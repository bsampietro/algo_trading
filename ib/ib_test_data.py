import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from threading import Thread
import logging
import time
from datetime import datetime
import json

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import *
from ibapi.common import *

from lib import util


class IBTestData(EClient, EWrapper):
    def __init__(self, ticker):
        EClient.__init__(self, wrapper = self)

        # variables
        self.next_req_id = 0
        self.req_id_to_stock_ticker_map = {}
        self.req_id_to_requested_historical_data = {}
        self.session_requested_data = set()
        self.api_ready = False

        self.ticker = ticker

        self.test_data = []

        self.connect("127.0.0.1", 7496, 3)
        self.run()
        self.wait_for_api_ready()


    def connectAck(self):
        """ callback signifying completion of successful connection """

        self.request_historical_data(self.ticker)


    def request_historical_data(self, ticker):
        # Remember queries in this session
        if ticker in self.session_requested_data:
            logging.info(f"{ticker} already requested")
            return
        else:
            self.session_requested_data.add(ticker)

        # Setting query variables
        duration_string = "14400 S"
        bar_size = "10 secs" # "1 secs" # "1 min" # "1 hour"
        what_to_show = "MIDPOINT"
        
        # Class level mappings
        next_req_id = self.get_next_req_id()
        self.req_id_to_stock_ticker_map[next_req_id] = ticker

        # Query
        self.reqHistoricalData(next_req_id, util.get_contract(ticker), '', duration_string, bar_size, what_to_show, 1, 2, [])

        print("Requesting historical data")


    def historicalData(self, reqId:TickerId , date:str, open:float, high:float,
                       low:float, close:float, volume:int, barCount:int,
                        WAP:float, hasGaps:int):
        super().historicalData(reqId, date, open, high, low, close, volume, barCount, WAP, hasGaps)

        self.req_id_to_stock_ticker_map[reqId] # good to keep it

        self.test_data.append((date, close))


    def historicalDataEnd(self, reqId:int, start:str, end:str):
        self.req_id_to_stock_ticker_map.pop(reqId, None)
        print("Historical data fetched")

        self.test_data.sort(key=lambda s: s[0])
        self.test_data = list(map(lambda s: (int(s[0]), s[1]), self.test_data))
        print(f"Got {len(self.test_data)} data points")

        test_data_sanitized = []
        for i in range(len(self.test_data)):
            if i == 0:
                test_data_sanitized.append(self.test_data[i])
            else:
                if self.test_data[i][1] != self.test_data[i-1][1]:
                    test_data_sanitized.append(self.test_data[i])
        self.test_data = test_data_sanitized
        print(f"Cleaned to {len(self.test_data)} data points")

        print("Saving...")
        with open(f"./data/{self.ticker}.json", "w") as f:
            json.dump(self.test_data, f)
        
        print("Disconnecting...")
        self.disconnect()



    # Async

    def wait_for_async_request(self):
        for i in range(120):
            if len(self.req_id_to_stock_ticker_map) == 0:
                break
            else:
                time.sleep(1)


    def wait_for_api_ready(self):
        for i in range(120):
            if self.api_ready:
                break
            else:
                time.sleep(1)


    # Private
    
    def get_next_req_id(self, next = True):
        if next:
            self.next_req_id += 1
        return self.next_req_id


    def reset_session_requested_data(self):
        self.session_requested_data = set()


    def error(self, reqId:TickerId, errorCode:int, errorString:str):
        super().error(reqId, errorCode, errorString)
        
        self.req_id_to_stock_ticker_map.pop(reqId, None)
        logging.info(f"Bruno says: Error logged with reqId: {reqId}")

    
    # Overwritten

    def keyboardInterrupt(self):
        self.disconnect()


    def nextValidId(self, orderId:int):
        super().nextValidId(orderId)
        logging.info(f"Bruno says: App ready with orderId: {orderId}")
        self.api_ready = True