import time
from threading import Thread
import logging
import json

import pygal

import gvars

STATE = {"random_walk": 0, "in_range": 1, "breaking_up": 2, "breaking_down": 3, "trending_up": 4, "trending_down": 5}
# ACTION = {"buy": 1, "sell": 2, "close": 3, "notify": 4}

class ChartData:
    def __init__(self, ticker):

        self.ticker = ticker
        self.prm = get_initial_parameters_for_ticker(ticker)
        
        # Data
        self.data = []

        self.state = STATE["random_walk"]
        self.min_range_price = 0
        self.max_range_price = 0
        
        # ----------Breaking data ----------------
        self.breaking_price_changes = 0
        
        # 5 second rule
        self.false_breaking_time = 0
        self.breaking_price = 0

        # up down
        self.min_breaking_price = 0
        self.max_breaking_price = 0
        self.breaking_time = 0
        # -----------------------------------------

        self.trending_price = 0
        self.transaction_price = 0 # bought price
        
        self.notification = ("", None)
        self.action = ("", None) # tuple with: (action, price)

        
        self.timed_prices = []

        # self.timer_active = True
        # self.timer = Thread(target = self.timed_work)
        # self.timer.start()


    def add_price(self, price, price_time):
        self.notification = ("", None)
        self.action = ("", None)
        cdp = ChartDataPoint()
        cdp.price = price
        cdp.time = price_time
        if len(self.data) > 0:
            if self.data[-1].price == price:
                return

            self.data[-1].duration = cdp.time - self.data[-1].time

        self.data.append(cdp)

        self.find_and_set_state()
    

    def find_and_set_state(self):

        if self.state_is("random_walk"):
            

            self.set_range()

        
        elif self.state_is("in_range"):


            self.set_range() # make the range thiner if needed

            
            if self.max_range_price < self.last_price() <= self.max_range_price + self.prm["BREAKING_RANGE_VALUE"]:
                self.breaking_price_changes = 0
                
                # self.false_breaking_time = 0
                # self.breaking_price = self.last_price()

                self.min_breaking_price = self.last_price()
                self.max_breaking_price = self.last_price()
                self.breaking_time = self.last_time()
                
                self.set_state("breaking_up")

            elif self.min_range_price - self.prm["BREAKING_RANGE_VALUE"] <= self.last_price() < self.min_range_price:
                self.breaking_price_changes = 0
                
                # self.false_breaking_time = 0
                # self.breaking_price = self.last_price()

                self.min_breaking_price = self.last_price()
                self.max_breaking_price = self.last_price()
                self.breaking_time = self.last_time()
                
                self.set_state("breaking_down")

            elif ((self.last_price() > self.max_range_price + self.prm["BREAKING_RANGE_VALUE"]) or 
                            (self.last_price() < self.min_range_price - self.prm["BREAKING_RANGE_VALUE"])):
                self.set_state("random_walk")


        elif self.state_is("breaking_up"):

            self.breaking_price_changes += 1

            # ## 5 seconds up rule
            # if self.breaking_price <= self.last_price():
            #     self.breaking_price = self.last_price()
            #     if self.false_breaking_time > 0: # Was down at least once
            #         if self.last_time() - self.false_breaking_time > MAX_FALSE_BREAKING_DURATION:
            #             self.breaking_price_changes = 0
            #             self.false_breaking_time = 0
            #             self.breaking_price = self.last_price()
            # else:
            #     if self.false_breaking_time == 0: # Was never down
            #         self.false_breaking_time = self.last_time() # Only assign if it was not set before
            # ## ------------------


            ## Time up down system
            if self.last_price() < self.min_breaking_price:
                self.min_breaking_price = self.last_price()
                self.breaking_time = self.last_time()
                self.breaking_price_changes = 0
            elif self.last_price() > self.max_breaking_price:
                self.max_breaking_price = self.last_price()
                self.breaking_time = self.last_time()

            mid_price = round((self.max_breaking_price + self.min_breaking_price) / 2.0, 2)
            time_up_down = self.time_up_down_since(self.breaking_time, mid_price)

            duration_ok = False
            if time_up_down[2] == 0:
                duration_ok = True
            else:
                if (float(time_up_down[0] + time_up_down[1]) / time_up_down[2]) > self.prm["UP_DOWN_RATIO"]:
                    duration_ok = True

            gvars.datalog[self.ticker].write("1st: Inside decision methods:\n")
            gvars.datalog[self.ticker].write(f"mid_price: {mid_price}\n")
            gvars.datalog[self.ticker].write(f"time_up_down: {time_up_down}\n")
            gvars.datalog[self.ticker].write(f"duration_ok: {duration_ok}\n\n")
            ## -------------------

            
            if ((self.last_price() > self.max_range_price + self.prm["BREAKING_RANGE_VALUE"]) or
                            (self.last_price() < self.min_range_price)):
              self.set_state("random_walk")

            elif self.min_range_price <= self.last_price() <= (self.max_range_price - self.prm["TICK_PRICE"]):
                self.set_state("in_range")

            elif (self.breaking_price_changes >= self.prm["MIN_BREAKING_PRICE_CHANGES"] and
                            self.last_price() > mid_price and duration_ok):
                self.trending_price = self.last_price()
                self.transaction_price = self.last_price()
                self.action = ("buy", self.last_price())
                self.set_state('trending_up')


        elif self.state_is("breaking_down"):


            self.breaking_price_changes += 1

            # ## 5 seconds up rule
            # if self.breaking_price <= self.last_price():
            #     self.breaking_price = self.last_price()
            #     if self.false_breaking_time > 0: # Was down at least once
            #         if self.last_time() - self.false_breaking_time > MAX_FALSE_BREAKING_DURATION:
            #             self.breaking_price_changes = 0
            #             self.false_breaking_time = 0
            #             self.breaking_price = self.last_price()
            # else:
            #     if self.false_breaking_time == 0: # Was never down
            #         self.false_breaking_time = self.last_time() # Only assign if it was not set before
            # ## ------------------


            ## Time up down system
            if self.last_price() < self.min_breaking_price:
                self.min_breaking_price = self.last_price()
                self.breaking_time = self.last_time()
            elif self.last_price() > self.max_breaking_price:
                self.max_breaking_price = self.last_price()
                self.breaking_time = self.last_time()
                self.breaking_price_changes = 0

            mid_price = round((self.max_breaking_price + self.min_breaking_price) / 2.0, 2)
            time_up_down = self.time_up_down_since(self.breaking_time, mid_price)

            duration_ok = False
            if time_up_down[0] == 0:
                duration_ok = True
            else:
                if (float(time_up_down[1] + time_up_down[2]) / time_up_down[0]) > self.prm["UP_DOWN_RATIO"]:
                    duration_ok = True

            gvars.datalog[self.ticker].write("1st: Inside decision methods:\n")
            gvars.datalog[self.ticker].write(f"mid_price: {mid_price}\n")
            gvars.datalog[self.ticker].write(f"time_up_down: {time_up_down}\n")
            gvars.datalog[self.ticker].write(f"duration_ok: {duration_ok}\n\n")
            ## -------------------

            
            if ((self.last_price() < self.min_range_price - self.prm["BREAKING_RANGE_VALUE"]) or
                            (self.last_price() > self.max_range_price)):
              self.set_state("random_walk")

            elif (self.min_range_price + self.prm["TICK_PRICE"]) <= self.last_price() <= self.max_range_price:
                self.set_state("in_range")

            elif (self.breaking_price_changes >= self.prm["MIN_BREAKING_PRICE_CHANGES"] and
                            self.last_price() < mid_price and duration_ok):
                self.trending_price = self.last_price()
                self.transaction_price = self.last_price()
                self.action = ("sell", self.last_price())
                self.set_state('trending_down')


        elif self.state_is("trending_up"):

            trending_break_value = self.prm["MIN_TRENDING_BREAK_VALUE"]
            new_trending_break_value = (self.trending_price - self.transaction_price) / 3.0
            if new_trending_break_value > trending_break_value:
                trending_break_value = new_trending_break_value

            if self.last_price() >= self.trending_price:
                self.trending_price = self.last_price()
            else:
                if self.trending_price - self.last_price() >= trending_break_value:
                    self.action = ("close", self.last_price()) # CLOSE POSITION SIGNAL (SELL) # last_price is added for backtesting purposes
                    self.set_state("random_walk")

        elif self.state_is("trending_down"):

            trending_break_value = self.prm["MIN_TRENDING_BREAK_VALUE"]
            new_trending_break_value = (self.transaction_price - self.trending_price) / 3.0
            if new_trending_break_value > trending_break_value:
                trending_break_value = new_trending_break_value

            if self.last_price() <= self.trending_price:
                self.trending_price = self.last_price()
            else:
                if self.last_price() - self.trending_price >= trending_break_value:
                    self.action = ("close", self.last_price()) # CLOSE POSITION SIGNAL (BUY) # last_price is added for backtesting purposes
                    self.set_state("random_walk")
        

    
    def set_range(self):
        min_price = self.last_price()
        max_price = self.last_price()
        for cdp in reversed(self.data):
            if cdp.price > max_price:
                max_price = cdp.price
            elif cdp.price < min_price:
                min_price = cdp.price
            
            range_value = max_price - min_price
            if range_value > self.prm["MAX_RANGE_VALUE"]:
                break
            
            if self.last_time() - cdp.time > self.prm["MIN_RANGE_TIME"]:
                self.min_range_price = min_price
                self.max_range_price = max_price
                self.set_state("in_range")
                # self.action = ("notify", None)


    def state_str(self):
        if len(self.data) < 2:
            return ""
        str = (
            f"Prev =>  P: {self.data[-2].price} - D: {self.data[-2].duration} | Current: P {self.data[-1].price}\n"
            f"state: {self.state}\n"
            f"min_range_price: {self.min_range_price}\n"
            f"max_range_price: {self.max_range_price}\n"

            f"breaking_price_changes: {self.breaking_price_changes}\n"
            f"min_breaking_price: {self.min_breaking_price}\n"
            f"max_breaking_price: {self.max_breaking_price}\n"
            f"breaking_time: {self.breaking_time}\n"

            f"trending_price: {self.trending_price}\n"
            f"transaction_price: {self.transaction_price}\n"
            f"action: {self.action}\n"
        )
        return str


    def set_state(self, state):
        if self.state != STATE[state]:
            self.notification = ("state_changed", f"state changed from {self.state} to {STATE[state]}")
            self.state = STATE[state]

    def state_is(self, state):
        return self.state == STATE[state]


    def last_cdp(self):
        if len(self.data) == 0:
            return ChartDataPoint()
        return self.data[-1]

    def last_price(self):
        return self.last_cdp().price

    def last_time(self):
        return self.last_cdp().time

    def data_since(self, the_time):
        data_since = []
        for cdp in reversed(self.data):
            data_since.append(cdp)
            if cdp.time == the_time:
                break
        data_since.reverse()
        assert len(data_since) < len(self.data)
        return data_since

    def time_up_down_since(self, the_time, price):
        time_up = 0
        time_equal = 0
        time_down = 0
        for cdp in self.data_since(the_time):
            if cdp.price > price:
                time_up += cdp.duration
            elif cdp.price == price:
                time_equal += cdp.duration
            else:
                time_down += cdp.duration
        return (time_up, time_equal, time_down)


    def timed_work(self):
        while self.timer_active:
            if len(self.data) > 0:
                self.timed_prices.append(self.data[-1].price)
                # if len(self.timed_prices) % 60 == 0:
                #     self.output_chart()
            time.sleep(1)

    
    def close(self):
        self.timer_active = False
        self.output_chart()
        self.save_data()


    def output_chart(self):
        # chart = pygal.Line()
        # # chart.x_labels = self.times
        # chart.add("Prices", self.timed_prices)
        initial_time = self.data[0].time

        chart = pygal.XY()
        chart.add('Prices',  list(map(lambda cdp: (cdp.time - initial_time, cdp.price), self.data)))

        chart.show_dots = False
        chart.render_to_file(f"{gvars.TEMP_DIR}/{self.ticker}_timed_prices.svg")


    def save_data(self):
        if self.test_mode():
            return
        mapped_data = list(map(lambda cdp: (cdp.time, cdp.price), self.data))
        file_name = f"{gvars.TEMP_DIR}/{self.ticker}_live_{time.strftime('%Y-%m-%d|%H-%M')}.json"
        with open(file_name, "w") as f:
            json.dump(mapped_data, f)


    def test_mode(self):
        return len(self.ticker) != 4




class ChartDataPoint:
    def __init__(self):
        
        self.price = 0
        self.time = 0
        self.duration = 0
        # self.slope = 0


def get_initial_parameters_for_ticker(ticker):
    prms = {}
    if ticker[0:2] == "GC":
        prms["TICK_PRICE"] = 0.10
    elif ticker[0:2] == "CL":
        prms["TICK_PRICE"] = 0.01
    elif ticker[0:2] == "NG":
        prms["TICK_PRICE"] = 0.001
    elif ticker[0:2] == "ES":
        prms["TICK_PRICE"] = 0.25
    elif ticker[0:2] == "6E":
        prms["TICK_PRICE"] = 0.00005

    prms["MAX_RANGE_VALUE"] = 4 * prms["TICK_PRICE"] # 0.4
    prms["MIN_RANGE_TIME"] = 300 # seconds
    
    prms["BREAKING_RANGE_VALUE"] = 3 * prms["TICK_PRICE"]
    prms["MIN_BREAKING_PRICE_CHANGES"] = 4 # times

    prms["MIN_TRENDING_BREAK_VALUE"] = 2 * prms["TICK_PRICE"] # 0.3
    # MAX_FALSE_BREAKING_DURATION = 5 # secs
    prms["UP_DOWN_RATIO"] = 1.0

    return prms