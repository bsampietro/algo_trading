class Stats:
    def __init__(self, monitor):
        self.m = monitor


    def find_rallies(self):
        rallies = []
        max_trend = 0
        for cdp in reversed(self.m.data_since(7200)):
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