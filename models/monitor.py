import time
from threading import Thread
import logging
import json
import os

import pygal
import bokeh.plotting
import bokeh.models

import gvars
from lib import util

# State objects can be used to return data and decide in this class whether to change state
# or just return direct information and get this class to ask if should change or not
from models.states.breaking import Breaking
from models.states.range import Range
from models.states.trending import Trending
from models.cycle import Cycle
from models.params import Params
from models.position import Position
from models.density import Density
from models.speed import Speed

STATE = {"random_walk": 0, "in_range": 1, "breaking_up": 2, "breaking_down": 3,
        "trending_up": 4, "trending_down": 5}

class Monitor:
    def __init__(self, ticker, remote):

        self.ticker = ticker
        self.remote = remote
        self.prm = Params(self)
        self.position = Position(self, remote)
        self.density = Density(self)
        self.speed = Speed(self)
        
        # Data
        self.data = []
        self.state = STATE["random_walk"]

        self.cycles = []
        self.pending_exec = None
        self.initial_time = 0
        
        # self.timed_prices = []
        # self.timer_active = True
        # self.timer = Thread(target = self.timed_work)
        # self.timer.start()


    def price_change(self, tickType, price, price_time):
        if tickType != 4:
            return
        cdp = ChartDataPoint(price, price_time)
        if len(self.data) > 0:
            if self.data[-1].price == price:
                return
            self.data[-1].duration = cdp.time - self.data[-1].time
            cdp.jump = self.ticks(cdp.price - self.data[-1].price)

        self.data.append(cdp)

        if len(self.data) == 1:
            self.initial_time = int(self.data[0].time)

        self.set_last_height_and_trend()

        self.density.price_change()

        self.speed.price_change()

        self.prm.adjust()

        self.position.price_change()

        # self.find_and_set_state()

        self.find_and_set_state2()

        self.log_data()


    def set_last_height_and_trend(self):
        if len(self.data) == 0:
            return
        if len(self.data) == 1:
            self.data[-1].trend = 1 # Arbitrary, could be -1
            return

        if self.data[-1].price > self.data[-2].price:
            new_trend = self.ticks(self.data[-1].price - self.data[-2].price)
            if self.data[-2].trend > 0:
                self.data[-1].trend = self.data[-2].trend + new_trend
                self.data[-2].height = gvars.HEIGHT["mid"]
            else:
                self.data[-1].trend = new_trend
                self.data[-2].height = gvars.HEIGHT["min"]
        else: # They can not be equal
            new_trend = self.ticks(self.data[-2].price - self.data[-1].price)
            if self.data[-2].trend < 0:
                self.data[-1].trend = self.data[-2].trend - new_trend
                self.data[-2].height = gvars.HEIGHT["mid"]
            else:
                self.data[-1].trend = -new_trend
                self.data[-2].height = gvars.HEIGHT["max"]

    
    def find_and_set_state(self):

        if self.state_is("random_walk"):
            
            self.find_and_set_range()
        
        elif self.state_is("in_range"):

            self.last_range.price_changed()
            rng = self.last_range
            
            if rng.max_price < self.last_price() <= rng.max_price + self.prm.breaking_range_value:
                self.ls = Breaking("up", self)
                self.set_state("breaking_up")

            elif rng.min_price - self.prm.breaking_range_value <= self.last_price() < rng.min_price:
                self.ls = Breaking("down", self)
                self.set_state("breaking_down")

            elif ((self.last_price() > rng.max_price + self.prm.breaking_range_value) or 
                            (self.last_price() < rng.min_price - self.prm.breaking_range_value)):
                self.set_state("random_walk")


        elif self.state_is("breaking_up"):

            rng = self.last_range

            if self.position.active_order():
                if (self.last_price() > self.position.last_order_price + self.prm.breaking_range_value):
                    self.position.cancel_active()
                    self.execute_pending("")
                    self.set_state("random_walk")
                    return
            else:
                if self.execute_pending():
                    return

            if ((self.last_price() > rng.max_price + self.prm.breaking_range_value) or
                            (self.last_price() < rng.min_price)):
                self.set_state("random_walk")
                return

            if rng.min_price <= self.last_price() <= (rng.max_price - self.prm.tick_price):
                self.set_state("in_range")
                return

            self.ls.price_changed()

            if (self.ls.breaking_price_changes >= self.prm.min_breaking_price_changes and
                            self.last_price() > self.ls.mid_price and self.ls.duration_ok):
                self.position.buy(round(self.last_price() - 2 * self.prm.tick_price, 2))
                code = (
                    "self.ls = Trending('up', self);"
                    "self.set_state('trending_up')"
                )
                self.execute_pending(code)


        elif self.state_is("breaking_down"):

            rng = self.last_range

            if self.position.active_order():
                if (self.last_price() < self.position.last_order_price - self.prm.breaking_range_value):
                    self.position.cancel_active()
                    self.execute_pending("")
                    self.set_state("random_walk")
                    return
            else:
                if self.execute_pending():
                    return

            if ((self.last_price() < rng.min_price - self.prm.breaking_range_value) or
                            (self.last_price() > rng.max_price)):
                self.set_state("random_walk")
                return

            elif (rng.min_price + self.prm.tick_price) <= self.last_price() <= rng.max_price:
                self.set_state("in_range")
                return

            self.ls.price_changed()

            if (self.ls.breaking_price_changes >= self.prm.min_breaking_price_changes and
                            self.last_price() < self.ls.mid_price and self.ls.duration_ok):
                self.position.sell(round(self.last_price() + 2 * self.prm.tick_price, 2))
                code = (
                    "self.ls = Trending('down', self);"
                    "self.set_state('trending_down')"
                )
                self.execute_pending(code)


        elif self.state_is("trending_up"):

            self.ls.price_changed()

            if self.ls.trending_stop():
                self.position.close()
                self.cycles[-1].pnl = round(self.last_price() - self.ls.transaction_price, 2)
                self.set_state("random_walk")

        elif self.state_is("trending_down"):

            self.ls.price_changed()

            if self.ls.trending_stop():
                self.position.close()
                self.cycles[-1].pnl = round(self.ls.transaction_price - self.last_price(), 2)
                self.set_state("random_walk")
        

    def find_and_set_range(self):
        min_price = self.last_price()
        max_price = self.last_price()
        max_range_value = self.prm.max_range_value
        outside_duration = 0
        start_time = 0
        for cdp in reversed(self.data):
            if cdp.price > max_price:

                if cdp.price - min_price <= max_range_value:
                    max_price = cdp.price
                    outside_duration = 0
                else:
                    outside_duration += cdp.duration
                    if outside_duration > self.prm.min_range_time / 20.0:
                        break

            elif cdp.price < min_price:

                if max_price - cdp.price <= max_range_value:
                    min_price = cdp.price
                    outside_duration = 0
                else:
                    outside_duration += cdp.duration
                    if outside_duration > self.prm.min_range_time / 20.0:
                        break

            else: # Inside max and min
                outside_duration = 0
            
            if self.last_time() - cdp.time > self.prm.min_range_time:
                start_time = cdp.time
                # max_range_value = max_price - min_price # in the case we want to consider thiner ranges

        if start_time > 0:
            self.ls = Range(self, min_price, max_price, start_time)
            self.set_state("in_range")


    def find_and_set_state2(self):
        # Speeding
        if self.state_is("random_walk") or self.state_is("in_range"):
            is_speeding = self.speed.find_criteria_speeding()
            if is_speeding == 'up':
                self.position.buy(self.last_price())
                self.ls = Trending('up', self, speeding = True)
                self.set_state('trending_up')
                return
            elif is_speeding == 'down':
                self.position.sell(self.last_price())
                self.ls = Trending('down', self, speeding = True)
                self.set_state('trending_down')
                return

        # Density
        # ...


    def set_state(self, state):
        if self.state != STATE[state]:
            gvars.datalog_buffer[self.ticker] += (f"State changed from {self.state} to {STATE[state]}\n")
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

    # ------ Cycles ------------
    @property
    def last_range(self):
        for state in reversed(self.cycles[-1].states):
            if type(state) is Range:
                return state

    # Last State
    @property
    def ls(self):
        return self.cycles[-1].last_state()
    
    # add_state(self, state)
    @ls.setter
    def ls(self, value):
        if len(self.cycles) == 0 or self.cycles[-1].closed():
            self.cycles.append(Cycle())
        self.cycles[-1].add_state(value)
    # --------------------------


    def execute_pending(self, code=None):
        if code is None:
            if self.pending_exec is not None:
                exec(self.pending_exec)
                self.pending_exec = None
                return True
        elif code == "":
            self.pending_exec = None
        else:
            self.pending_exec = code
        return False

    # the_time could be a specific time or an amount of time since now
    def data_since(self, time_or_duration):
        data_since = []
        for cdp in reversed(self.data):
            data_since.append(cdp)
            if cdp.time == time_or_duration:
                break
            elif self.last_time() - cdp.time > time_or_duration:
                data_since.pop() # patch because of adding the element first
                break
        data_since.reverse()
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


    def min_max_since(self, time_ago):
        data_portion = self.data_since(time_ago)
        return (min(data_portion, key=lambda cdp: cdp.price),
                max(data_portion, key=lambda cdp: cdp.price))


    def timed_prices(self, time_ago=0, interval=60):
        data = self.data if time_ago == 0 else self.data_since(time_ago)
        timed_prices = []
        initial_time = data[0].time
        current_interval = 0
        i = 1
        while i < len(data):
            if data[i].time - initial_time >= current_interval:
                timed_prices.append(ChartDataPoint(data[i-1].price, current_interval))
                current_interval += interval
            else:
                i += 1
        return timed_prices


    def ticks(self, price_difference):
        return round(price_difference / self.prm.tick_price)

    
    def close(self):
        self.timer_active = False
        self.output_chart('timed')
        self.output_chart('all')
        self.save_data()
        self.log_cycles()


    def state_str(self):
        if len(self.data) < 2:
            return ""
        output = (
            f"Prev =>  P: {self.data[-2].price} - D: {self.data[-2].duration} | Current: P {self.data[-1].price}\n"
            f"state: {self.state}\n"
            f"pending_exec: {self.pending_exec}\n"
            f"{self.position.state_str()}\n"
        )
        if self.ls == self.last_range:
            output += self.ls.state_str()
        else:
            output += self.last_range.state_str()
            output += self.ls.state_str()
        return output


    def output_chart(self, kind):
        # Bokeh
        x = None
        y = None
        if kind == 'timed':
            timed_prices = self.timed_prices(interval=15)
            x = list(map(lambda cdp: cdp.time, timed_prices))
            y = list(map(lambda cdp: cdp.price, timed_prices))
        else:
            x = list(map(lambda cdp: cdp.time - self.initial_time, self.data))
            y = list(map(lambda cdp: cdp.price, self.data))

        bokeh.plotting.output_file(f"{gvars.TEMP_DIR}/{self.ticker}_{kind}_chart.html", title=self.ticker)
        
        TOOLTIPS = [
            ("index", "$index"),
            ("price", "@y{0.00}"),
            ("time", "@x{0.00}"),
            ("hover (price,time)", "($y{0.00}, $x{0.00})")
        ]
        hover_tool = bokeh.models.HoverTool(
            tooltips=TOOLTIPS,

            # display a tooltip whenever the cursor is vertically in line with a glyph
            mode='mouse' # "mouse" (default) | "vline" | "hline"
        )
        p = bokeh.plotting.figure(
           #tools="crosshair,pan,wheel_zoom,box_zoom,reset,box_select,hover",
           # tooltips=TOOLTIPS,
           title=self.ticker,
           width=1200,
           tools=[hover_tool,"crosshair,pan,wheel_zoom,box_zoom,reset,box_select"]
        )
        p.circle(x, y, size=4, color='blue')
        p.line(x, y, color='blue')

        bokeh.plotting.save(p)

        # # Pygal
        # dir_path = f"{gvars.TEMP_DIR}/{self.ticker}_chart"
        # os.makedirs(dir_path, exist_ok=True)
        # chunks = []
        # chunk = []
        # chunk_nr = 1
        # for cdp in self.data:
        #     if (int(cdp.time) - self.initial_time) > (3600 * chunk_nr):
        #         chunks.append(chunk)
        #         chunk = []
        #         chunk_nr += 1
        #     chunk.append(cdp)
        # chunks.append(chunk)

        # for chunk in chunks:
        #     chart = pygal.XY(width=1200)
            
        #     mapped_data = list(map(lambda cdp: (int(cdp.time) - self.initial_time, cdp.price), chunk))
        #     chart.add('',  mapped_data)

        #     initial_time = mapped_data[0][0]
        #     final_time = mapped_data[-1][0]
        #     chart.x_labels = range(initial_time, final_time, 200)
        #     chart.y_labels = set(map(lambda cdp: cdp.price, chunk))
        #     chart.show_dots = True
        #     chart.dots_size = 2
        #     chart.render_to_file(f"{dir_path}/{initial_time}_{final_time}.svg")


    def save_data(self):
        if not self.remote.live_mode:
            return
        mapped_data = list(map(lambda cdp: (cdp.time, cdp.price), self.data))
        file_name = f"{gvars.TEMP_DIR}/{self.ticker}_live_{time.strftime('%Y-%m-%d|%H-%M')}.json"
        with open(file_name, "w") as f:
            json.dump(mapped_data, f)


    def log_data(self):
        print(f"{self.ticker} => {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_time()))}: {self.last_price()}")
        gvars.datalog[self.ticker].write(
            f"\n=>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_time()))}"
            f"({self.last_time()} - {int(self.last_time()) - self.initial_time}): {self.last_price()}\n"
        )
        if self.state in (1, 2, 3, 4, 5):
            gvars.datalog[self.ticker].write("2nd: MONITOR:\n")
            gvars.datalog[self.ticker].write(self.state_str())
        gvars.datalog[self.ticker].write(self.density.state_str())
        gvars.datalog[self.ticker].write(self.speed.state_str())
        gvars.datalog[self.ticker].write(gvars.datalog_buffer[self.ticker])
        gvars.datalog_buffer[self.ticker] = ""


    def log_cycles(self):
        output = ""
        for cycle in self.cycles:
            output += cycle.state_str()
            for state in cycle.states:
                output += state.state_str()
        gvars.datalog[self.ticker].write("\nCYCLES:\n")
        gvars.datalog[self.ticker].write(output)


    def order_change(self, order_id, status, remaining):
        self.position.order_change(order_id, status, remaining)


    # def timed_work(self):
    #     sec = 0
    #     while self.timer_active:
    #         if len(self.data) > 0 and sec % 60 == 0:
    #             if len(self.timed_prices) > 120:
    #                 self.timed_prices.pop(0)
    #             self.timed_prices.append(self.last_price())
    #         sec += 1
    #         time.sleep(1)


class ChartDataPoint:
    def __init__(self, price=0, time=0):
        self.price = price
        self.time = time
        self.duration = 0
        self.height = 0 # min - mid - max
        self.trend = 0 # distance (in ticks) from min or max
        self.jump = 0 # distance (in ticks) from previous price
        # self.slope = 0