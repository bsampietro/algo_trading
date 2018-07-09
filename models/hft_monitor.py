from datetime import datetime, date
import time
import logging
import statistics
from threading import Thread

from lib import util
from models.hft_chartdata import ChartData

class HftMonitor:
    SPEED_RATIO_THRESHOLD = 3


    def __init__(self, ticker, remote):
        # price variables to be substituted by:
        self.chart_data = ChartData()
        
        # Positions
        self.position = 0
        self.confirmed_position = 0
        self.order_price = 0
        self.confirmed_price = 0
        
        # general variables
        self.ticker = ticker.upper()
        self.contract = util.get_contract(self.ticker)

        self.remote = remote

        #self.req_id = remote.get_next_req_id()
        # remote.start_monitoring(self)


    def price_change(self, tickType, price):
        if price <= 0:
            print(f"Returned 0 or under 0 price: '{price}', for ticker {self.ticker}")
            return

        # bid price = 1
        # ask price = 2
        # last traded price = 4

        if tickType == 4:
            self.chart_data.add_price(price)

            if self.chart_data.do[0] == "notify":
                self.sound_notify()

            # price_line_str = f"{price}"
            # logging.info(price_line_str)
            # print(price_line_str)
            
            # All position querying should be done with self.confirmed_position once the system is executing orders

            # # Start position
            # if self.position == 0 and speed_ratio > HftMonitor.SPEED_RATIO_THRESHOLD:
            #     if v > 0:
            #         # buy at ask_price - tick
            #         # remote.place_order(self, "BUY", 1, price)
                    
            #         self.position = 1

            #         print(price_line_str)
            #         print(f"Bought at: {price}")
            #     else:
            #         # sell at bid price + tick
            #         # remote.place_order(self, "SELL", 1, price)

            #         self.position = -1

            #         print(price_line_str)
            #         print(f"Sold at: {price}")
            #     self.order_price = price

            # # Get out of position
            # if self.position == 1 and (self.order_price > price or speed_ratio < HftMonitor.SPEED_RATIO_THRESHOLD):
            #     # remote.place_order(self, "SELL", 1, price, self.active_order_id)
            #     print(price_line_str)
            #     print(f"Sold back at: {price}")
            #     print(f"Profit of {price - self.order_price}")
            #     self.position = 0

            # if self.position == -1 and (self.order_price < price or speed_ratio < HftMonitor.SPEED_RATIO_THRESHOLD):
            #     # remote.place_order(self, "BUY", 1, price, self.active_order_id)
            #     print(price_line_str)
            #     print(f"Bought back at: {price}")
            #     print(f"Profit of {self.order_price - price}")
            #     self.position = 0


    def order_change(self, order_id, status, remaining):
        if status == "Filled":
            self.active_order_id = None
            self.confirmed_position = remaining
            self.confirmed_price = self.order_price
            print(remaining)
        elif status == "Cancelled":
            self.active_order_id = None
        else:
            # get the order id after placing the order so
            # it is managed only on remote
            self.active_order_id = order_id


    def close(self):
        self.chart_data.close()


    def sound_notify(self):
        Thread(target = lambda: os.system("mpv --really-quiet /home/bruno/Downloads/Goat-sound-effect.mp3")).start()

    # Private

    def active_order(self):
        self.active_order_id is not None
