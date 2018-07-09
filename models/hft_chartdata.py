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
        self.do = ("", 0) # tuple with: (action, price)

        self.timed_prices = []

        self.timer_active = True
        self.timer = Thread(target = self.timed_work)
        self.timer.start()

        # Class constants
        self.initial_time = time.time()

    def add_price(self, price):
        cdt = ChartDataPoint()
        cdt.price = price
        cdt.time = time.time() - self.initial_time
        if len(self.data) > 0:
            self.data[-1].duration = cdt.time - self.data[-1].time
        self.data.append(cdt)

        self.set_state()

        print(self.state_str())

    
    def last_cdt(self):
        if len(self.data) == 0:
            return ChartDataPoint()
        return self.data[-1]

    def last_price(self):
        return self.last_cdt().price

    def last_time(self):
        return self.last_cdt().time


    def set_state(self):
        self.do = ("", 0)

        if self.state == STATE["random_walk"]:
            

            self.set_range()

        
        elif self.state == STATE["in_range"]:


            # self.set_range() # make the range thiner if needed

            
            if self.max_range_price < self.last_price() <= self.max_range_price + BREAKING_RANGE_VALUE:
                self.state = STATE["breaking_up"]

            elif self.min_range_price - BREAKING_RANGE_VALUE <= self.last_price() < self.min_range_price:
                self.state = STATE["breaking_down"]

            elif ((self.last_price() > self.max_range_price + BREAKING_RANGE_VALUE) or 
                            (self.last_price() < self.min_range_price - BREAKING_RANGE_VALUE)):
                self.state = STATE["random_walk"]


        elif self.state == STATE["breaking_up"]:
            

            # # check if trending up:
            # self.state = STATE['trending_up']
            # self.trending_price = self.last_price()
            # self.do = ("buy", self.last_price()) # ??

            if ((self.last_price() > self.max_range_price + BREAKING_RANGE_VALUE) or
                            (self.last_price() < self.min_range_price)):
              self.state = STATE["random_walk"]

            elif self.min_range_price <= self.last_price() <= (self.max_range_price - MAX_RANGE_VALUE / 2.0):
                self.state = STATE["in_range"]


        elif self.state == STATE["breaking_down"]:


            # # check if trending down:
            # self.state = STATE['trending_down']
            # self.trending_price = self.last_price()
            # self.do = ("sell", self.last_price()) # ??

            if ((self.last_price() < self.min_range_price - BREAKING_RANGE_VALUE) or
                            (self.last_price() > self.max_range_price)):
              self.state = STATE["random_walk"]

            elif (self.min_range_price + MAX_RANGE_VALUE / 2.0) <= self.last_price() <= self.max_range_prince:
                self.state = STATE["in_range"]


        elif self.state == STATE["trending_up"]:


            if self.last_price() >= self.trending_price:
                self.trending_price = self.last_price()
            else:
                if self.trending_price - self.last_price() >= TRENDING_BREAK_VALUE:
                    self.state = STATE["random_walk"]
                    self.do = ("close", 0) # CLOSE POSITION SIGNAL (SELL)

        elif self.state == STATE["trending_down"]:


            if self.last_price() <= self.trending_price:
                self.trending_price = self.last_price()
            else:
                if self.last_price() - self.trending_price >= TRENDING_BREAK_VALUE:
                    self.state = STATE["random_walk"]
                    self.do = ("close", 0) # CLOSE POSITION SIGNAL (BUY)
        

    
    def state_str(self):
        if len(self.data) < 2:
            return ""
        str = (
            f"{time.strftime('%H:%M:%S')}\n"
            f"Prev =>  P: {self.data[-2].price} - D: {self.data[-2].duration} | Current: P {self.data[-1].price}\n"
            f"state: {self.state}\n"
            f"min_range_price: {self.min_range_price}\n"
            f"max_range_price: {self.max_range_price}\n"
            f"trending_price: {self.trending_price}\n"
            f"do: {self.do}\n"
        )
        return str


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
                self.state = STATE["in_range"]
                self.min_range_price = min_price
                self.max_range_price = max_price
                self.do = ("notify", 0)


    def random_walk(self):
        return self.state == STATE["random_walk"]

    def in_range(self):
        return self.state == STATE["in_range"]

    def breaking_up(self):
        return self.state == STATE["breaking_up"]

    def breaking_down(self):
        return self.state == STATE["breaking_down"]

    def trending_up(self):
        return self.state == STATE["trending_up"]

    def trending_down(self):
        return self.state == STATE["trending_down"]


    def timed_work(self):
        while self.timer_active:
            if len(self.data) > 0:
                # self.timed_prices.append(self.data[-1].price)
                if int(time.time()) % 10 == 0:
                    self.output_chart()
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
