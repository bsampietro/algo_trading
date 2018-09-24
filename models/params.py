import random

class Params:
    def __init__(self, monitor):
        self.m = monitor
        self.set_initial_parameters()
        self.set_options()


    def set_initial_parameters(self):
        if self.m.ticker[0:2] == "GC":
            self.tick_price = 0.10
            self.price_precision = 2
        elif self.m.ticker[0:2] == "CL":
            self.tick_price = 0.01
            self.price_precision = 2
        elif self.m.ticker[0:2] == "NG":
            self.tick_price = 0.001
            self.price_precision = 3
        elif self.m.ticker[0:2] == "ES":
            self.tick_price = 0.25
            self.price_precision = 2
        elif self.m.ticker[0:3] == "EUR":
            self.tick_price = 0.00005
            self.price_precision = 5
        self.max_breaking_price_changes_list = 50 # times

        self.breaking_stop_time = 60 # secs
        self.speeding_stop_time = 10 # secs

        self.min_breaking_price_changes = 5 # times
        self.breaking_up_down_ratio = 1.0
        
        self.primary_look_back_time = 900 # secs # ideal for ES, 600-900 for all others

        self.speeding_time = 5 # secs
        self.time_speeding_points_length = 4
        self.speed_min_max_win_loose_ticks = (2, 6)


    def set_options(self):
        self.breaking_stop_time_options = (20, 40, 60, 80, 120) # secs
        self.speeding_stop_time_options = (5, 10, 20, 30) # secs

        self.min_breaking_price_changes_options = (3, 5, 10, 15) # times
        self.breaking_up_down_ratio_options = (1.0, 1.5, 2.0)
        
        self.primary_look_back_time_options = (900, 1800, 3600, 7200) # secs # ideal for ES, 600-900 for all others

        self.speeding_time_options = (5, 10, 20) # secs
        self.time_speeding_points_length_options = (4, 6)
        self.speed_min_max_win_loose_ticks_options = ((2, 6), (3, 6), (4, 8))


    def randomize(self):
        for variable, value in vars(self).items():
            if variable[-8:] == '_options':
                setattr(self, variable.replace('_options', ''), random.choice(value))


    def state_str(self):
        output = "  PARAMETERS:\n"
        for variable, value in vars(self).items():
            if variable[-8:] == '_options':
                output += f"    {variable.replace('_options', '')}: {getattr(self, variable.replace('_options', ''))}\n"
        return output