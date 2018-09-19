import time
from threading import Thread, Lock
import logging
import json
import os

# import pygal
# import bokeh.plotting
# import bokeh.models

import gvars
from lib import util

# State objects can be used to return data and decide in this class whether to change state
# or just return direct information and get this class to ask if should change or not
from models.breaking import Breaking
from models.params import Params
from models.position import Position
from models.density import Density
from models.speed import Speed
from models.results import Results
from models.decision import Decision

class Monitor:
    def __init__(self, ticker, remote):

        self.ticker = ticker
        self.remote = remote
        self.data = []
        
        self.prm = Params(self)
        self.position = Position(self, remote)
        self.density = Density(self)
        self.speed = Speed(self)
        self.results = Results(self)
        self.breaking = Breaking(self)
        
        self.action_decision = None

        self.initial_time = 0

        # Lock variables
        self.price_change_lock = Lock()
        self.order_change_lock = Lock()


    def price_change(self, tickType, price, price_time):
        with self.price_change_lock:
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

            self.breaking.price_change()

            self.position.price_change()

            # self.prm.adjust()

            self.query_and_decision()

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


    def query_and_decision(self):
        # Query (if not active position):
        # -4 in line
        # -speed
        # -breaking
        # -Density percentile movement (to start or stop a trade)
        
        if self.position.is_active():

            if self.action_decision.should_close():
                self.position.close()
                # self.breaking.initialize_state()
                return

        elif self.position.is_pending():

            if self.action_decision.breaking_in_range():
                if not self.breaking.in_range():
                    self.position.cancel_pending()
                    #self.results.append(0, 0, 0, 0, self.position.order_time, 0, self.last_time())
            elif self.action_decision.speeding():
                if not self.speed.is_speeding():
                    self.position.cancel_pending()
                    #self.results.append(0, 0, 0, 0, self.position.order_time, 0, self.last_time())

        else:
            decision = Decision(self)
            
            if self.speed.is_speeding():

                decision.time_speeding_points = self.speed.time_speeding_points

            elif self.breaking.in_range():
                
                decision.density_data = self.breaking.density_data
                decision.direction = self.breaking.direction
                decision.last_price = self.last_price()

                decision.breaking_price_changes = self.breaking.price_changes
                decision.breaking_duration_ok = self.breaking.duration_ok()
                decision.in_line = abs(self.data[-1].trend)

                if self.breaking.direction * (self.last_price() - self.breaking.density_data.trend_tuple[0]) >= 2:
                    decision.trend_two = abs(self.last_price() - self.breaking.density_data.trend_tuple[0])

            if decision.should() == 'buy':
                self.action_decision = decision
                self.position.buy(self.price_plus_ticks(-decision.adjusting_ticks))
                gvars.datalog_buffer[self.ticker] += f"    monitor.query_and_decision.decision:\n{decision.state_str()}"
            elif decision.should() == 'sell':
                self.action_decision = decision
                self.position.sell(self.price_plus_ticks(+decision.adjusting_ticks))
                gvars.datalog_buffer[self.ticker] += f"    monitor.query_and_decision.decision:\n{decision.state_str()}"


    def last_cdp(self):
        if len(self.data) == 0:
            return ChartDataPoint()
        return self.data[-1]

    
    def last_price(self):
        return self.last_cdp().price

    
    def last_time(self):
        return self.last_cdp().time


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


    def price_plus_ticks(self, ticks):
        return round(self.last_price() + ticks * self.prm.tick_price, self.prm.price_precision)


    def mid_price(self, price1, price2 = 0):
        if price2 == 0: # price1 is iterable with 2 elements
            price1, price2 = price1
        return round((price1 + price2) / 2.0, self.prm.price_precision)

    
    def close(self):
        #self.output_chart('timed')
        #self.output_chart('all')
        self.log_final_data()
        self.save_data()


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
        print(f"{self.ticker} => {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_time()))}: {self.last_price():.{self.prm.price_precision}f}")
        gvars.datalog[self.ticker].write(
            f"\n=>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_time()))}"
            f"({self.last_time()} - {int(self.last_time()) - self.initial_time}): {self.last_price():.{self.prm.price_precision}f}\n"
        )
        gvars.datalog[self.ticker].write(self.density.state_str())
        gvars.datalog[self.ticker].write(self.speed.state_str())
        gvars.datalog[self.ticker].write(self.breaking.state_str())
        gvars.datalog[self.ticker].write(self.position.state_str())
        gvars.datalog[self.ticker].write(self.results.state_str())
        
        if gvars.datalog_buffer[self.ticker] != "":
            gvars.datalog[self.ticker].write("  DATALOG_BUFFER:\n")
            gvars.datalog[self.ticker].write(gvars.datalog_buffer[self.ticker])
            gvars.datalog_buffer[self.ticker] = ""


    def log_final_data(self):
        output = "\nFINAL DATA\n"
        output += self.results.state_str(True)
        min_max = self.min_max_since(86400*7)
        output += f"  Max ticks: {self.ticks(min_max[1].price - min_max[0].price)}\n"
        output += f"  Data points: {len(self.data)}\n"
        print(output)
        gvars.datalog[self.ticker].write(output)


    def order_change(self, order_id, status, remaining, fill_price, fill_time):
        with self.order_change_lock:
            self.position.order_change(order_id, status, remaining, fill_price, fill_time)


class ChartDataPoint:
    def __init__(self, price=0, time=0):
        self.price = price
        self.time = time
        self.duration = 0
        self.height = 0 # min - mid - max
        self.trend = 0 # distance (in ticks) from min or max
        self.jump = 0 # distance (in ticks) from previous price
        # self.slope = 0