import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from threading import Thread, Lock
import logging
import time
import json

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import *
from ibapi.common import *
from ibapi.order import *

from lib import util
from models.monitor import Monitor


class IBHft(EClient, EWrapper):

    def __init__(self, tickers=[], input_file=""):
        EClient.__init__(self, wrapper = self)

        self.monitors = []
        self.tickers = tickers

        # state variables
        self.req_id_to_monitor_map = {}
        self.order_id_to_monitor_map = {}

        # tws variables
        self.current_req_id = 0
        self.current_order_id = None

        # threading variables
        self.lock = Lock()

        # test variables
        self.live_mode = True if input_file == "" else False

        if self.live_mode:
            self.connect("127.0.0.1", 7497, 0)
            self.run()
            self.wait_for_readiness()
        else:
            self.input_file = input_file
            self.tickers = [util.ticker_from_file(input_file)]

            self.test_thread = Thread(target = self.connectAck)
            self.test_thread.start()
            self.test_thread.join()


    def connectAck(self):
        """ callback signifying completion of successful connection """
        # tickers = ["GCQ8"]
        for ticker in self.tickers:
            monitor = Monitor(ticker, self)
            self.start_monitoring(monitor)
            self.monitors.append(monitor)


    def keyboardInterrupt(self):
        self.clear_all()


    def clear_all(self):
        print("Clearing all...")
        
        for req_id, monitor in self.req_id_to_monitor_map.items():
            self.cancelMktData(req_id)
            monitor.close()
            time.sleep(3)
        self.disconnect()

        print("Finished clearing.")


    def start_monitoring(self, monitor):
        next_req_id = self.get_next_req_id()
        self.req_id_to_monitor_map[next_req_id] = monitor
        self.request_market_data(next_req_id, monitor.ticker)


    def request_market_data(self, req_id, ticker):
        if self.live_mode:
            self.reqMktData(req_id, util.get_contract(ticker), "", False, False, [])
        else:
            with open(self.input_file, "r") as f:
                data = json.load(f)

            for time, price in data:
                self.tickPrice(self.current_req_id, 4, price, {"time": time})
            
            for req_id, monitor in self.req_id_to_monitor_map.items():
                monitor.close()


    def tickPrice(self, reqId, tickType, price:float, attrib):
        super().tickPrice(reqId, tickType, price, attrib)

        if price <= 0:
            logging.info(f"Returned 0 or under 0 price: '{price}', for ticker {self.ticker}")
            return

        # tickType:
        # bid price = 1
        # ask price = 2
        # last traded price = 4

        if self.live_mode:
            self.req_id_to_monitor_map[reqId].price_change(tickType, price, time.time())
        else:
            self.req_id_to_monitor_map[reqId].price_change(tickType, price, attrib["time"])


    def is_ready(self):
        return self.current_order_id is not None


    def wait_for_readiness(self):
        for i in range(120):
            if self.is_ready():
                break
            else:
                time.sleep(1)
        if self.is_ready():
            print("IB Ready")
        else:
            # raise exception ?
            print("IB was not reported ready after 120 seconds")


    # callback to client.reqIds(-1)
    def nextValidId(self, orderId:int):
        super().nextValidId(orderId)
        self.current_order_id = orderId

    # App functions
    def get_next_order_id(self):
        self.current_order_id += 1
        return self.current_order_id

    def get_next_req_id(self):
        self.current_req_id += 1
        return self.current_req_id


    # Orders
    def place_order(self, monitor, action, quantity, price=0, orderId=None):
        if not self.live_mode:
            return

        with self.lock:
            order = Order()
            if price == 0:
                order.orderType = "MKT"
            else:    
                order.orderType = "LMT"
            order.totalQuantity = quantity
            order.action = action # "BUY"|"SELL"
            order.lmtPrice = price

            if orderId is None:
                order_id = self.get_next_order_id()
                self.order_id_to_monitor_map[next_order_id] = monitor
            else:
                order_id = orderId

            self.placeOrder(order_id, util.get_contract(monitor.ticker), order)


    def cancel_order(self, order_id):
        self.cancelOrder(order_id)


    def orderStatus(self, orderId, status, filled,
                    remaining, avgFillPrice, permId,
                    parentId, lastFillPrice, clientId,
                    whyHeld):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, 
                lastFillPrice, clientId, whyHeld)

        self.order_id_to_monitor_map[orderId].order_change(orderId, status, remaining)

    def openOrder(self, orderId, contract, order,
                  orderState):
        super().openOrder(orderId, contract, order, orderState)

        # self.order_id_to_monitor_map[orderId].order_change()