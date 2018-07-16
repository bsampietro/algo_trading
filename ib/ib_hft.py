import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from threading import Thread
import logging
import time
import json

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import *
from ibapi.common import *
from ibapi.order import *

from lib import util

from models.hft_monitor import HftMonitor


class IBHft(EClient, EWrapper):

    def __init__(self, input_file=""):
        EClient.__init__(self, wrapper = self)

        self.monitors = []

        # state variables
        self.req_id_to_monitor_map = {}
        self.order_id_to_monitor_map = {}

        # tws variables
        self.current_req_id = 0
        self.current_order_id = None

        # test variables
        self.test_mode = "data" in input_file
        self.input_file = input_file

        if self.test_mode:
            self.test_thread = Thread(target = self.connectAck)
            self.test_thread.start()
            self.test_thread.join()
        else:
            self.connect("127.0.0.1", 7496, 2)

            # Try without calling self.run() ??
            # thread = Thread(target = self.run)
            # thread.start()
            self.run()

            self.wait_for_readiness()


    def connectAck(self):
        """ callback signifying completion of successful connection """
        # self.logAnswer(current_fn_name(), vars())

        # tickers = [sys.argv[1]] # can be taken from list in the future
        tickers = ["GCQ8"]
        for ticker in tickers:
            monitor = HftMonitor(ticker, self)
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
        self.request_market_data(next_req_id, monitor.contract)


    def request_market_data(self, req_id, contract):
        if self.test_mode:
            with open(self.input_file, "r") as f:
                data = json.load(f)

            for time, price in data:
                self.tickPrice(self.current_req_id, 4, price, {"time": time})
            
            for req_id, monitor in self.req_id_to_monitor_map.items():
                monitor.close()
        else:
            self.reqMktData(req_id, contract, "", False, False, [])


    def tickPrice(self, reqId, tickType, price:float, attrib):
        super().tickPrice(reqId, tickType, price, attrib)

        if self.test_mode:
            self.req_id_to_monitor_map[reqId].price_change(tickType, price, attrib["time"])
        else:
            self.req_id_to_monitor_map[reqId].price_change(tickType, price, 0)


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

        self.placeOrder(order_id, monitor.contract, order)


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


    # # Overload methods for test mode
    # def reqMktData(self, reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions):
    #     if self.test_mode:
    #         # manually call tickPrice
    #         pass
    #     else:
    #         super().reqMktData(reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions)

