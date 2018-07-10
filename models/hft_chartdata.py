import time
from threading import Thread

import pygal

TICK_PRICE = 0.10
MAX_RANGE_VALUE = 4 * TICK_PRICE # 0.4
MIN_RANGE_TIME = 300 # seconds
TRENDING_BREAK_VALUE = 3 * TICK_PRICE # 0.3
BREAKING_RANGE_VALUE = 2 * TICK_PRICE
STATE = {"random_walk": 0, "in_range": 1, "breaking_up": 2, "breaking_down": 3, "trending_up": 4, "trending_down": 5}
ACTION = {"buy": 1, "sell": 2, "close": 3, "notify": 4}

class ChartData:
    def __init__(self):
        
        # Data
        self.data = []

        self.state = STATE["random_walk"]
        self.min_range_price = 0
        self.max_range_price = 0
        self.trending_price = 0
        self.action = ("", None) # tuple with: (action, price)

        self.timed_prices = []

        # self.timer_active = True
        # self.timer = Thread(target = self.timed_work)
        # self.timer.start()

        # Class constants
        self.initial_time = time.time()

    def add_price(self, price, price_time):
        cdt = ChartDataPoint()
        cdt.price = price
        if price_time == 0:
            cdt.time = time.time() # - self.initial_time
        else:
            cdt.time = price_time
        if len(self.data) > 0:
            self.data[-1].duration = cdt.time - self.data[-1].time

            if len(self.data) % 10 == 0:
                self.output_chart()

        self.data.append(cdt)

        self.find_and_set_state()
    

    def find_and_set_state(self):
        self.action = ("", None)

        if self.state_is("random_walk"):
            

            self.set_range()

        
        elif self.state_is("in_range"):


            self.set_range() # make the range thiner if needed

            
            if self.max_range_price < self.last_price() <= self.max_range_price + BREAKING_RANGE_VALUE:
                self.set_state("breaking_up")

            elif self.min_range_price - BREAKING_RANGE_VALUE <= self.last_price() < self.min_range_price:
                self.set_state("breaking_down")

            elif ((self.last_price() > self.max_range_price + BREAKING_RANGE_VALUE) or 
                            (self.last_price() < self.min_range_price - BREAKING_RANGE_VALUE)):
                self.set_state("random_walk")


        elif self.state_is("breaking_up"):
            

            # # check if trending up:
            # self.state = STATE['trending_up']
            # self.trending_price = self.last_price()
            # self.action = ("buy", self.last_price()) # ??

            if ((self.last_price() > self.max_range_price + BREAKING_RANGE_VALUE) or
                            (self.last_price() < self.min_range_price)):
              self.set_state("random_walk")

            elif self.min_range_price <= self.last_price() <= (self.max_range_price - MAX_RANGE_VALUE / 2.0):
                self.set_state("in_range")


        elif self.state_is("breaking_down"):


            # # check if trending down:
            # self.state = STATE['trending_down']
            # self.trending_price = self.last_price()
            # self.action = ("sell", self.last_price()) # ??

            if ((self.last_price() < self.min_range_price - BREAKING_RANGE_VALUE) or
                            (self.last_price() > self.max_range_price)):
              self.set_state("random_walk")

            elif (self.min_range_price + MAX_RANGE_VALUE / 2.0) <= self.last_price() <= self.max_range_price:
                self.set_state("in_range")


        elif self.state_is("trending_up"):


            if self.last_price() >= self.trending_price:
                self.trending_price = self.last_price()
            else:
                if self.trending_price - self.last_price() >= TRENDING_BREAK_VALUE:
                    self.set_state("random_walk")
                    self.action = ("close", self.last_price) # CLOSE POSITION SIGNAL (SELL) # last_price is added for backtesting purposes

        elif self.state_is("trending_down"):


            if self.last_price() <= self.trending_price:
                self.trending_price = self.last_price()
            else:
                if self.last_price() - self.trending_price >= TRENDING_BREAK_VALUE:
                    self.set_state("random_walk")
                    self.action = ("close", self.last_price) # CLOSE POSITION SIGNAL (BUY) # last_price is added for backtesting purposes
        

    
    def set_range(self):
        min_price = self.last_price()
        max_price = self.last_price()
        for cdt in reversed(self.data):
            if cdt.price > max_price:
                max_price = cdt.price
            elif cdt.price < min_price:
                min_price = cdt.price
            
            range_value = max_price - min_price
            if range_value > MAX_RANGE_VALUE:
                break
            
            if self.last_time() - cdt.time > MIN_RANGE_TIME:
                self.min_range_price = min_price
                self.max_range_price = max_price
                self.set_state("in_range")
                # self.action = ("notify", None)


    def state_str(self):
        if len(self.data) < 2:
            return ""
        str = (
            f"\n{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.data[-1].time))}\n"
            f"Prev =>  P: {self.data[-2].price} - D: {self.data[-2].duration} | Current: P {self.data[-1].price}\n"
            f"state: {self.state}\n"
            f"min_range_price: {self.min_range_price}\n"
            f"max_range_price: {self.max_range_price}\n"
            f"trending_price: {self.trending_price}\n"
            f"action: {self.action}\n"
        )
        return str


    def set_state(self, state):
        if self.state != STATE[state]:
            self.action = ("state_changed", f"state changed from {self.state} to {STATE[state]}")
            self.state = STATE[state]

    def state_is(self, state):
        return self.state == STATE[state]


    def last_cdt(self):
        if len(self.data) == 0:
            return ChartDataPoint()
        return self.data[-1]

    def last_price(self):
        return self.last_cdt().price

    def last_time(self):
        return self.last_cdt().time


    def timed_work(self):
        while self.timer_active:
            if len(self.data) > 0:
                self.timed_prices.append(self.data[-1].price)
                # if len(self.timed_prices) % 60 == 0:
                #     self.output_chart()
            time.sleep(1)

    
    def close(self):
        self.timer_active = False


    def output_chart(self):
        # chart = pygal.Line()
        # # chart.x_labels = self.times
        # chart.add("Prices", self.timed_prices)

        chart = pygal.XY()
        chart.add('Prices',  list(map(lambda cdt: (cdt.time, cdt.price), self.data)))

        chart.show_dots = False
        chart.render_to_file(f"/media/ramd/timed_prices.svg")




class ChartDataPoint:
    def __init__(self):
        
        self.price = 0
        self.time = 0
        self.duration = 0
        # self.slope = 0
