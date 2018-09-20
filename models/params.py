class Params:
    def __init__(self, chart_data):
        self.cd = chart_data
        self.set_initial_parameters()


    def adjust(self):
        pass
        # self.find_rallies()
        # explore results and get statistics...


    def find_rallies(self):
        rallies = []
        max_trend = 0
        for cdp in reversed(self.cd.data_since(7200)):
            if max_trend == 0:
                if cdp.trend > 5 or cdp.trend < -5:
                    # Set begining of trend
                    last_trend_time = cdp.time
                    max_trend = cdp.trend
            else:
                if (cdp.trend < -1 and max_trend > 0) or (cdp.trend > 1 and max_trend < 0):
                    # Set end of trend
                    initial_trend_time = cdp.time
                    rallies.append((last_trend_time, initial_trend_time, max_trend)) # temp code. need to see how to return data accordingly
                    max_trend = 0
        return rallies


    def set_initial_parameters(self):
        if self.cd.ticker[0:2] == "GC":
            self.tick_price = 0.10
            self.price_precision = 2
        elif self.cd.ticker[0:2] == "CL":
            self.tick_price = 0.01
            self.price_precision = 2
        elif self.cd.ticker[0:2] == "NG":
            self.tick_price = 0.001
            self.price_precision = 3
        elif self.cd.ticker[0:2] == "ES":
            self.tick_price = 0.25
            self.price_precision = 2
        elif self.cd.ticker[0:3] == "EUR":
            self.tick_price = 0.00005
            self.price_precision = 5

        self.breaking_stop_time = 60 # secs
        self.speeding_stop_time = 10 # secs

        self.min_breaking_price_changes = 5 # times
        self.breaking_up_down_ratio = 1.0
        self.max_breaking_price_changes_list = 50 # times
        
        self.primary_look_back_time = 900 # secs # ideal for ES, 600-900 for all others

        self.speeding_time = 5 # secs
        self.time_speeding_points_length = 4
        self.speed_min_max_win_loose_ticks = (2, 6)