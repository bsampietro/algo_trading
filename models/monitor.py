import time
from threading import Thread, Lock
import logging
import json
import os
from functools import lru_cache

import gvars
from lib import util, core
from lib.secondary import DummyStream

# State objects can be used to return data and decide in this class whether to change state
# or just return direct information and get this class to ask if should change or not
from models.breaking import Breaking
from models.params import Params
from models.position import Position
from models.density import Density
from models.speed import Speed
from models.results import Results
from models.breaking_decision import BreakingDecision
from models.speeding_decision import SpeedingDecision
from models.params_db import ParamsDb
from models.closing import Closing

class Monitor:
    def __init__(self, ticker, remote, prm_id):

        self.ticker = ticker
        self.remote = remote
        self.data = []
        
        self.test = False
        if prm_id == None:
            self.test = True
            self.assign_params(Params(), randomize=True)
        elif prm_id == 0:
            self.assign_params(Params())
        else:
            self.assign_params(ParamsDb.gi().get_params(prm_id))
        self.position = Position(self, remote)
        self.density = Density(self)
        self.breaking = Breaking(self)
        self.speed = Speed(self)
        self.results = Results(self)
        
        self.action_decision = None
        self.initial_time = None # type: int
        self.max_average_pnl = None
        self.processed_params = {}

        # Lock variables
        self.price_change_lock = Lock()
        self.order_change_lock = Lock()

        self.child_test_monitors = []

        if self.test:
            base_file_name = f"{ticker}_{hash(self)}"
            self.datalog = DummyStream()
        else:
            base_file_name = f"{ticker}"
            self.datalog = open(f"{self.create_and_return_output_dir()}/{base_file_name}.log", "w")
        self.datalog_buffer = ""
        self.datalog_final = open(f"{self.create_and_return_output_dir()}/{base_file_name}_final.log", "w")


    def price_change(self, tickType, price, price_time):
        with self.price_change_lock:
            if tickType != 4:
                return
            for monitor in self.child_test_monitors:
                monitor.price_change(tickType, price, price_time)
            cdp = ChartDataPoint(price, price_time)
            if len(self.data) > 0:
                if self.data[-1].price == price:
                    return
                self.data[-1].duration = cdp.time - self.data[-1].time
                cdp.jump = self.ticks(cdp.price - self.data[-1].price)

            # Stats
            cdp.price_data_length = len(self.data_since(900))
            cdp.density_points_length = len(self.density.list_dps)
            cdp.acc_pnl = self.results.acc_pnl()
            cdp.nr_of_trades = self.position.nr_of_trades
            cdp.action = ''

            self.data.append(cdp)

            if len(self.data) == 1:
                self.initial_time = int(self.data[0].time)

            if not self.test and (self.remote.live_mode or len(self.data) % 50 == 0):
                output = (
                    f"{self.ticker} => {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_time()))}"
                    f"({self.last_time():.2f} - {int(self.last_time()) - self.initial_time:>6}): "
                    f"{self.last_price():.{self.prm.price_precision}f}   "
                    f"plen: {self.data[-1].price_data_length:>4} - "
                    f"dlen: {self.data[-1].density_points_length:>3} - "
                    f"acc_pnl: {self.data[-1].acc_pnl:>5.2f} - "
                    f"nr_of_trades: {self.data[-1].nr_of_trades:>3} - "
                    f"prm_id: {self.prm.id:>3} - "
                )
                print(output)
                self.datalog_final.write(f"{output}\n")
            
            if gvars.args.data_mode():
                return

            self.set_last_height_and_trend()

            self.density.price_change()

            self.speed.price_change()

            self.breaking.price_change()

            self.position.price_change()

            self.process_params()

            self.query_and_decision()

            self.log_data()


    def set_last_height_and_trend(self):
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

            if self.closing is None:
                self.closing = Closing(self)

            if self.action_decision.should_stop():
                order_type = self.closing.order_type()
                if order_type == 'LMT':
                    self.position.close(self.last_price())
                    self.data[-1].action += f"-- Stop LMT {self.last_price()} "
                elif order_type == 'MKT':
                    self.position.close()
                    self.data[-1].action += f"-- Stop MKT {self.last_price()} "
            elif self.action_decision.reached_maximum(1):
                self.position.close(self.price_plus_ticks(self.position.direction() * 1))
                self.data[-1].action += f"-- Max LMT {self.price_plus_ticks(self.position.direction() * 1)} "

            # Before doing this, we need to make sure the price filled
            # if self.action_decision.is_breaking_in_range():
            #     # self.breaking.initialize_state()
            #     pass
            # elif self.action_decision.is_speeding():
            #     self.speed.reset()
            # return

        elif self.position.is_pending():
            # pending to open position

            if self.action_decision.is_breaking_in_range():
                if not self.breaking.in_range():
                    self.position.cancel_pending()
                    self.data[-1].action += "-- Cancel: Out of range "
                    #self.results.append(0, 0, 0, 0, self.position.order_time, 0, self.last_time())
            elif self.action_decision.is_speeding():
                if not self.speed.is_speeding():
                    self.position.cancel_pending()
                    self.data[-1].action += "-- Cancel: Stopped speeding "
                    #self.results.append(0, 0, 0, 0, self.position.order_time, 0, self.last_time())

        else:
            self.closing = None
            decision = None
            
            if self.speed.is_speeding() and gvars.CONF['speeding_enabled']:

                decision = SpeedingDecision(self, time_speeding_points = self.speed.time_speeding_points)

            elif self.breaking.in_range() and gvars.CONF['breaking_enabled']:
                
                decision = BreakingDecision(self, density_data = self.breaking.density_data)
                decision.direction = self.breaking.direction
                decision.creation_price = self.last_price()

                decision.breaking_price_changes = self.breaking.price_changes
                decision.breaking_duration_ok = self.breaking.duration_ok()
                decision.in_line = abs(self.data[-1].trend)

                if self.breaking.direction * (self.last_price() - self.breaking.density_data.trend_tuple[0]) >= 2:
                    decision.trend_two = abs(self.last_price() - self.breaking.density_data.trend_tuple[0])

            if decision is None:
                return

            if decision.should() == 'buy':
                self.action_decision = decision
                self.position.buy(self.price_plus_ticks(-decision.adjusting_ticks))
                self.data[-1].action += f"-- BUY LMT {self.price_plus_ticks(-decision.adjusting_ticks)} "
                self.datalog_buffer += f"    monitor.query_and_decision.decision: {decision.state_str()}\n"
            elif decision.should() == 'sell':
                self.action_decision = decision
                self.position.sell(self.price_plus_ticks(+decision.adjusting_ticks))
                self.data[-1].action += f"-- SELL LMT {self.price_plus_ticks(+decision.adjusting_ticks)} "
                self.datalog_buffer += f"    monitor.query_and_decision.decision: {decision.state_str()}\n"


    def last_price(self):
        return self.data[-1].price

    
    def last_time(self):
        return self.data[-1].time


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


    def dollars(self, price_difference):
        return price_difference * self.prm.dollar_multiplier


    def price_plus_ticks(self, ticks, price=None):
        price = price or self.last_price()
        return round(price + ticks * self.prm.tick_price, self.prm.price_precision)


    def mid_price(self, price1, price2 = 0):
        if price2 == 0: # price1 is iterable with 2 elements
            price1, price2 = price1
        return round((price1 + price2) / 2.0, self.prm.price_precision)


    def ticker_code(self):
        return self.ticker[0:2]

    
    def close(self):
        for monitor in self.child_test_monitors:
            monitor.close()
        self.save_params()
        if not self.test:
            if gvars.args.output_chart():
                self.output_chart('timed')
                self.output_chart('all')
                self.output_chart_pnl_against('price_data_length', 'density_points_length')
            if self.remote.live_mode:
                self.save_data()
        self.log_final_data(should_print = not self.remote.live_mode)
        self.datalog.close()
        self.datalog_final.close()


    def output_chart(self, kind):
        # Importing at the function level because method is not always used
        # import pygal
        import bokeh.plotting
        import bokeh.models
        from bokeh.models.ranges import Range1d
        from bokeh.models.axes import LinearAxis

        # Bokeh
        
        price_source = None
        if kind == 'timed':
            timed_prices = self.timed_prices(interval=15)
            price_source = bokeh.plotting.ColumnDataSource(data=dict(
                x=list(map(lambda cdp: cdp.time, timed_prices)),
                y=list(map(lambda cdp: cdp.price, timed_prices))
            ))
        else:
            price_source = bokeh.plotting.ColumnDataSource(data=dict(
                x=[cdp.time - self.initial_time for cdp in self.data],
                y=[cdp.price for cdp in self.data],
                price_data_length=[cdp.price_data_length for cdp in self.data],
                density_points_length=[cdp.density_points_length for cdp in self.data],
                acc_pnl=[cdp.acc_pnl for cdp in self.data],
                nr_of_trades=[cdp.nr_of_trades for cdp in self.data],
                action=[cdp.action for cdp in self.data]
            ))

        min_price = min([cdp.price for cdp in self.data])
        action_source = bokeh.plotting.ColumnDataSource(data=dict(
            x=[cdp.time - self.initial_time for cdp in self.data],
            y=[cdp.price if cdp.action != "" else min_price for cdp in self.data]
        ))
        
        TOOLTIPS = [
            ("index", "$index"),
            ("time", "@x{0.00}"),
            ("price", "@y{0.00}"),
            # ("hover (price,time)", "($y{0.00}, $x{0.00})"),
            ("price_data_length", "@price_data_length"),
            ("density_points_length", "@density_points_length"),
            ("acc_pnl", "@acc_pnl{0.00}"),
            ("nr_of_trades", "@nr_of_trades"),
            ("action", "@action")
        ]
        hover_tool = bokeh.models.HoverTool(
            tooltips=TOOLTIPS,
            # display a tooltip whenever the cursor is vertically in line with a glyph
            mode='mouse' # "mouse" (default) | "vline" | "hline"
        )
        bokeh.plotting.output_file(f"{self.create_and_return_output_dir()}/{self.ticker}_{kind}_chart.html", title=self.ticker)
        p = bokeh.plotting.figure(
           title=self.ticker,
           width=1200,
           tools=[hover_tool,"crosshair,pan,wheel_zoom,box_zoom,reset,box_select"]
        )
        p.circle(x = 'x', y = 'y', size=4, color='blue', source=price_source)
        p.circle(x = 'x', y = 'y', size=8, color='red', source=action_source)
        p.line(x = 'x', y = 'y', color='blue', source=price_source)
        bokeh.plotting.save(p)

        # # Pygal
        # dir_path = f"{self.create_and_return_output_dir()}/{self.ticker}_chart"
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


    def output_chart_pnl_against(self, *stats):
        import bokeh.plotting
        import bokeh.models
        from bokeh.models.ranges import Range1d
        from bokeh.models.axes import LinearAxis

        time = [cdp.time - self.initial_time for cdp in self.data]
        price = [cdp.price for cdp in self.data]
        price_data_length = [cdp.price_data_length for cdp in self.data]
        density_points_length = [cdp.density_points_length for cdp in self.data]
        acc_pnl = [cdp.acc_pnl for cdp in self.data]
        nr_of_trades = [cdp.nr_of_trades for cdp in self.data]

        pnl_source = bokeh.plotting.ColumnDataSource(data=dict(
            x=time,
            y=acc_pnl,
            price=price,
            price_data_length=price_data_length,
            density_points_length=density_points_length,
            nr_of_trades=nr_of_trades
        ))
        
        TOOLTIPS = [
            ("index", "$index"),
            ("time", "@x{0.00}"),
            ("acc_pnl", "@y{0.00}"),
            ("price", "@price"),
            ("price_data_length", "@price_data_length"),
            ("density_points_length", "@density_points_length"),
            ("nr_of_trades", "@nr_of_trades"),
        ]
        hover_tool = bokeh.models.HoverTool(
            tooltips=TOOLTIPS,
            mode='mouse' # "mouse" (default) | "vline" | "hline"
        )
        bokeh.plotting.output_file(f"{self.create_and_return_output_dir()}/{self.ticker}_comparison_chart.html", title=self.ticker)
        p = bokeh.plotting.figure(
            title=self.ticker,
            width=1200,
            tools=[hover_tool,"crosshair,pan,wheel_zoom,box_zoom,reset,box_select"],
            x_range=(min(time), max(time)),
            y_range=(min(acc_pnl), max(acc_pnl))
        )
        p.circle(x = 'x', y = 'y', size=2, color='blue', source=pnl_source)
        p.line(x = 'x', y = 'y', color='blue', source=pnl_source)

        # Against data
        colors = ['green', 'red', 'brown', 'yellow', 'pink', 'grey']
        extra_y_ranges = {}
        for stat in stats:
            var_stat = locals()[stat]
            extra_y_ranges[stat] = Range1d(start=min(var_stat), end=max(var_stat))
        p.extra_y_ranges = extra_y_ranges
        for stat in stats:
            var_stat = locals()[stat]
            color = colors.pop(0)
            p.add_layout(LinearAxis(y_range_name=stat), 'right')
            p.circle(x = time, y = var_stat, size=2, color=color, y_range_name=stat, legend=stat)
            p.line(x = time, y = var_stat, color=color, y_range_name=stat, legend=stat)

        bokeh.plotting.save(p)


    def save_data(self):
        file_name = f"{self.create_and_return_output_dir()}/{self.ticker}_live_{time.strftime('%Y-%m-%d|%H-%M')}.json"
        if os.path.isfile(file_name):
            return
        mapped_data = list(map(lambda cdp: (cdp.time, cdp.price), self.data))
        with open(file_name, "w") as f:
            json.dump(mapped_data, f)


    def log_data(self):
        if self.test:
            self.datalog_buffer = ""
            return
        self.datalog.write(
            f"\n=>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_time()))}"
            f"({self.last_time():.2f} - {int(self.last_time()) - self.initial_time}): {self.last_price():.{self.prm.price_precision}f}\n"
        )
        self.datalog.write(self.density.state_str())
        self.datalog.write(self.speed.state_str())
        self.datalog.write(self.breaking.state_str())
        self.datalog.write(self.position.state_str())
        self.datalog.write(self.results.state_str())
        
        if self.datalog_buffer != "":
            self.datalog.write("  DATALOG_BUFFER:\n")
            self.datalog.write(self.datalog_buffer)
            self.datalog_buffer = ""


    def log_final_data(self, should_print):
        output = "\nFINAL DATA\n"
        output += self.results.state_str('stats')
        print(output) if should_print else None
        min_max = self.min_max_since(86400*7)
        output += f"  Max ticks: {self.ticks(min_max[1].price - min_max[0].price)}\n"
        output += f"  Data points: {len(self.data)}\n"
        output += self.prm.state_str()
        output += self.results.state_str('all')
        self.datalog.write(output)
        self.datalog_final.write(output)


    def save_params(self):
        if gvars.CONF['dynamic_parameter_change']:
            return
        if not self.test:
            return
        self.prm.attach_last_result()
        if ((gvars.CONF['accepting_average_pnl'] is None or self.prm.last_result['average_pnl'] >= gvars.CONF['accepting_average_pnl'])
                    and
                (gvars.CONF['accepting_trade_number'] is None or (self.prm.last_result['nr_of_winners'] + self.prm.last_result['nr_of_loosers']) >= gvars.CONF['accepting_trade_number'])
                    and
                self.data[-1].time - self.data[0].time > 3600 * 4):
            ParamsDb.gi().add_or_modify(self.prm)


    def process_params(self):
        if not gvars.CONF['dynamic_parameter_change']:
            return
        
        current_average_pnl = None
        children_prm_pnl = []
        for monitor in self.child_test_monitors:
            if len(monitor.results.data) >= gvars.CONF['dynamic_parameter_change']:
                # Assigning data
                monitor_average_pnl = self.dollars(monitor.results.average_pnl(gvars.CONF['dynamic_parameter_change']))
                if current_average_pnl is None:
                    current_average_pnl = self.dollars(self.results.average_pnl(gvars.CONF['dynamic_parameter_change']))
                if self.max_average_pnl is None or current_average_pnl > self.max_average_pnl:
                    self.max_average_pnl = current_average_pnl

                if monitor_average_pnl < gvars.CONF['discarding_average_pnl']:
                    print(f"Changing params on child monitors with avg_pnl of {monitor_average_pnl}")
                    monitor.assign_params(Params(), randomize=True)
                    monitor.density = Density(monitor)
                    monitor.breaking = Breaking(monitor)
                    monitor.speed = Speed(monitor)
                elif monitor_average_pnl > gvars.CONF['accepting_average_pnl']:
                    print(f"Saving params on child monitors with avg_pnl of {monitor_average_pnl}")
                    monitor.prm.attach_last_result(gvars.CONF['dynamic_parameter_change'])
                    ParamsDb.gi().add_or_modify(monitor.prm)
                # # In case we don't want to reset results.
                # # Identical to above block but without reseting results
                # if (len(monitor.results.data) >= 30 and
                #         len(monitor.results.data) % 30 == 0 and
                #         not self.processed_params.get(monitor, False)):
                #     average_pnl = self.dollars(monitor.results.average_pnl(30))
                #     if average_pnl < 4.0:
                #         monitor.prm.randomize()
                #         monitor.density = Density(monitor)
                #         monitor.breaking = Breaking(monitor)
                #         monitor.speed = Speed(monitor)
                #     elif average_pnl > 6.0:
                #         monitor.prm.attach_last_result()
                #         ParamsDb.gi().add_or_modify(monitor.prm)
                #     self.processed_params[monitor] = True
                # elif len(monitor.results.data) % 30 == 1:
                #     self.processed_params[monitor] = False
                if monitor_average_pnl > self.max_average_pnl + gvars.CONF['discarding_average_pnl']:
                    children_prm_pnl.append((monitor.prm, monitor_average_pnl))

                monitor.results = Results(monitor)
                monitor.position = Position(monitor, self.remote)
        try:
            best_prm, prm_avg_pnl = max(children_prm_pnl, key=lambda t: t[1])
        except ValueError:
            return # there is no max so it can't assign anything
        if self.prm == best_prm:
            return
        print(f"Changing params on main (live) trading monitor, groing from avg_pnls of: {current_average_pnl} to {prm_avg_pnl}")
        self.max_average_pnl = prm_avg_pnl
        self.assign_params(best_prm)
        self.density = Density(self)
        self.breaking = Breaking(self)
        self.speed = Speed(self)


    def order_change(self, order_id, status, remaining, fill_price, fill_time):
        with self.order_change_lock:
            self.position.order_change(order_id, status, remaining, fill_price, fill_time)


    def create_children(self, number):
        for i in range(number):
            self.child_test_monitors.append(Monitor(self.ticker, self.remote, None))


    def assign_params(self, params, randomize=False):
        self.prm = params
        self.prm.assign_monitor(self)
        self.prm.randomize() if randomize else None


    @lru_cache(maxsize=None)
    def create_and_return_output_dir(self):
        new_dir_name = f"{gvars.TEMP_DIR}/{self.ticker[0:2]}"
        try:
            os.mkdir(new_dir_name)
        except FileExistsError:
            pass
        return new_dir_name


class ChartDataPoint:
    def __init__(self, price, time):
        self.price = price
        self.time = time
        self.duration = 0
        self.jump = 0 # distance (in ticks) from previous price
        self.height = gvars.HEIGHT['mid'] # min - mid - max
        self.trend = None # type: int # distance (in ticks) from min or max
        # self.slope = 0
        
        # Stats fields (should they be in different class?)
        self.price_data_length = None # type: int
        self.density_points_length = None # type: int
        self.acc_pnl = None # type: int
        self.nr_of_trades = None # type: int
        self.action = None # type: string