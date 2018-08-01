class Speeding:
    def __init__(self, monitor):
        self.mtr = monitor


    def find(self):
        if not (self.mtr.state_is("random_walk") or self.mtr.state_is("in_range")):
        	return None

        data = self.mtr.data_since(self.mtr.prm.speeding_time_considered)
        if len(data) <= 2:
            return None
        if not (all(map(lambda cdp: cdp.trend > 0, data)) or all(map(lambda cdp: cdp.trend < 0, data))):
            return None
        if self.mtr.ticks(abs(data[-1].price - data[0].price)) / abs(data[-1].time - data[0].time) < 1:
            return None

        if data[-1].price > data[0].price:
            return 'up'
        else:
            return 'down'