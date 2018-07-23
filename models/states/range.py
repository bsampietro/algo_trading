class Range:
    def __init__(self, chart_data, min_price, max_price, start_time):
        self.cd = chart_data

        self.min_price = min_price
        self.max_price = max_price
        self.start_time = start_time
        self.last_time = self.cd.last_time()


    def price_changed(self):
    	self.last_time = self.cd.last_time()


    def duration(self):
    	return self.last_time - self.start_time


    def state_str(self):
        output = (
            f"RANGE:\n"
            f"min_range_price: {self.min_price}\n"
            f"max_range_price: {self.max_price}\n"
            f"start_range_time: {self.start_time}\n"
            f"last_range_time: {self.last_time}\n"
            f"range_duration: {self.duration()}\n"
        )
        return output