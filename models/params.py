import random
import statistics
import time

class Params:
    def __init__(self):
        self.m = None
        self.set_options_and_defaults()

        self.id = -2 # negative ids for maintaining code default versions
        self.results = []
        self.last_result = None # temp variable to store last result, will be appended to results when stored


    def assign_monitor(self, monitor):
        self.m = monitor
        self.set_basic_parameters()


    def set_basic_parameters(self):
        if self.m.ticker_code() == "ES":
            self.tick_price = 0.25
            self.price_precision = 2
            self.dollar_multiplier = 50
        
        elif self.m.ticker_code() == "NQ":
            self.tick_price = 0.25
            self.price_precision = 2
            self.dollar_multiplier = 20
        
        elif self.m.ticker_code() == "YM":
            self.tick_price = 1
            self.price_precision = 2
            self.dollar_multiplier = 20
        
        elif self.m.ticker_code() == "CL":
            self.tick_price = 0.01
            self.price_precision = 2
            self.dollar_multiplier = 1000
        
        elif self.m.ticker_code() == "NG":
            self.tick_price = 0.001
            self.price_precision = 3
            self.dollar_multiplier = 10000
        
        elif self.m.ticker_code() == "GC":
            self.tick_price = 0.10
            self.price_precision = 2
            self.dollar_multiplier = 100
        
        elif self.m.ticker_code() == "HG":
            self.tick_price = 0.0005
            self.price_precision = 4
            self.dollar_multiplier = 5000
        
        elif self.m.ticker_code() == "SI":
            self.tick_price = 0.005
            self.price_precision = 3
            self.dollar_multiplier = 5000
        
        elif self.m.ticker_code() == "EU":
            self.tick_price = 0.00005
            self.price_precision = 5
            self.dollar_multiplier = 125000
        
        elif self.m.ticker_code() == "JP":
            self.tick_price = 0.0000005
            self.price_precision = 7
            self.dollar_multiplier = 12500000
        
        elif self.m.ticker_code() == "ZB":
            self.tick_price = 0.03125
            self.price_precision = 5
            self.dollar_multiplier = 1000
        
        elif self.m.ticker_code() == "ZN":
            self.tick_price = 0.015625
            self.price_precision = 6
            self.dollar_multiplier = 1000
        
        elif self.m.ticker_code() == "ZC":
            self.tick_price = 0.25
            self.price_precision = 2
            self.dollar_multiplier = 50
        
        elif self.m.ticker_code() == "ZS":
            self.tick_price = 0.25
            self.price_precision = 2
            self.dollar_multiplier = 50

        self.max_breaking_price_changes_list = 50
        self.min_breaking_price_changes_list = 20


    # performance parameters with options
    # if parameter is set None, means that should be resolved in the specific part of the code, probably in Decision class.
    # if parameter is set 'calc', it is calculated in the property part
    # first value of tuple is default value
    def set_options_and_defaults(self):
        self.primary_look_back_time_options = (3600, 7200, 1800, 900) # secs # ideal for ES, 600-900 for all others
        self.density_division_options = (10, 5)
        
        # Stop time
        self.breaking_stop_time_options = (60, 20, 40, 80, 120) # secs
        self.speeding_stop_time_options = (10, 5, 20, 30) # secs

        # Breaking
        self._min_breaking_price_changes_options = (7, 3, 15, 'calc') # times
        self.breaking_up_down_ratio_options = (1.0, 1.5, 2.0)
        self.min_breaking_range_options = (4, 2, 6)

        # Speeding
        self.speeding_time_options = (5, 10, 20) # secs
        self.time_speeding_points_length_options = (4, 3, 6)
        self.speed_min_max_win_loose_ticks_options = ((2, 6), (3, 6), (4, 10))

        # Stop values
        self.reached_first_target_break_options = (1, 2)
        self.made_two_break_options = (1, 2)
        self.min_max_loose_ticks_options = ((1, 3), (2, 5)) # could replace speed_min_max_win_loose_ticks_options
        self.reversal_addition_break_options = (1, 2, 0)

        # Variety
        self._max_winning_ticks_options = (4, 1, 2) # With 1 it is mostly a market maker
        self.reduce_score_rate_on_price_data_length_options = ((150, 350, 0.75), (150, 300, 0.50), None, None)
        self.trade_initiation_ticks_options = (1, 0)

        # Scores
        self.breaking_price_changes_score_options = (3, 1, 0)
        self.duration_score_options = (1, 2, 0)
        self.in_line_score_options = (1, 2, 0)
        self.trend_two_score_options = (1, 2, 0)
        self.in_out_density_direction_score_options = (1, 2, 0)
        self.advantage_score_options = (3, 1, 0)

        # Set defaults (default value is the first of the options)
        current_vars = dict(vars(self))
        for variable, value in current_vars.items():
            if variable[-8:] == '_options':
                setattr(self, variable.replace('_options', ''), value[0])


    def randomize(self):
        for variable, value in vars(self).items():
            if variable[-8:] == '_options':
                setattr(self, variable.replace('_options', ''), random.choice(value))
        self.id = None # without any id, ParamsDb will assign a new one and save it as new


    @property
    def min_breaking_price_changes(self):
        if self._min_breaking_price_changes == 'calc':
            if len(self.m.breaking.price_changes_list) < self.min_breaking_price_changes_list:
                return self.default('_min_breaking_price_changes')
            else:
                try:
                    return round(statistics.median(self.m.breaking.price_changes_list) * 1.5)
                except statistics.StatisticsError:
                    return self.default('_min_breaking_price_changes')
        else:
            return self._min_breaking_price_changes


    @property
    def max_winning_ticks(self):
        if self._max_winning_ticks == 'calc':
            if len(self.m.results.data) < 20:
                return self.default('_max_winning_ticks')
            else:
                try:
                    return statistics.mode(r.fantasy_pnl for r in self.m.results.data)
                except statistics.StatisticsError:
                    return self.default('_max_winning_ticks')
        else:
            return self._max_winning_ticks


    def default(self, attr):
        return getattr(self, attr + '_options')[0]


    def attach_last_result(self, last=None):
        self.last_result = {}
        self.last_result['average_pnl'] = self.m.dollars(self.m.results.average_pnl(last))
        self.last_result['nr_of_winners'] = self.m.results.nr_of_wl('winners', last)
        self.last_result['nr_of_loosers'] = self.m.results.nr_of_wl('loosers', last)
        self.last_result['underlying'] = f"{self.m.ticker_code()}_{time.strftime('%Y-%m-%d--%H-%M', time.localtime(self.m.last_time()))}"


    def state_str(self):
        output = "  PARAMETERS:\n"
        output += f"    id: {self.id}\n"
        for variable, value in vars(self).items():
            if variable[-8:] == '_options':
                output += f"    {variable.replace('_options', '')}: {getattr(self, variable.replace('_options', ''))}\n"
        return output