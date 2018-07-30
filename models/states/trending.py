import gvars

class Trending:
    def __init__(self, direction, chart_data, speeding=False):
        self.direction = direction
        self.cd = chart_data
        self.speeding = speeding

        self.transaction_price = self.cd.last_price()
        self.transaction_time = self.cd.last_time()
        self.trending_price = self.cd.last_price()


    def price_changed(self):
        if self.direction == 'up':
            if self.cd.last_price() > self.trending_price:
                self.trending_price = self.cd.last_price()
        else:
            if self.cd.last_price() < self.trending_price:
                self.trending_price = self.cd.last_price()

    
    def trending_stop(self):
        time_since_transaction = self.cd.last_time() - self.transaction_time
        if time_since_transaction > self.cd.prm.trending_break_time:
            min_max = self.cd.min_max_since(self.cd.prm.trending_break_time)
            gvars.datalog_buffer[self.cd.ticker] += ("1st: Inside trending_stop:\n")
            gvars.datalog_buffer[self.cd.ticker] += (f"min_max_1: {min_max[1].price}\n")
            gvars.datalog_buffer[self.cd.ticker] += (f"min_max_0: {min_max[0].price}\n")
            gvars.datalog_buffer[self.cd.ticker] += (f"trending_break_value: {self.trending_break_value()}\n\n")
            if min_max[1].price - min_max[0].price <= self.trending_break_value():
                return True
        if abs(self.cd.last_price() - self.trending_price) >= self.trending_break_value():
            return True
        return False



    def state_str(self):
        output = (
            f"TRENDING {self.direction}:\n"
            f"transaction_price: {self.transaction_price}\n"
            f"transaction_time: {self.transaction_time}\n"
            f"trending_price: {self.trending_price}\n"
            f"speeding: {self.speeding}\n"
        )
        return output

    # Private

    def trending_break_value(self):
        possible_trending_break_value = (self.trending_price - self.transaction_price) / 3.0
        if possible_trending_break_value > self.cd.prm.min_trending_break_value:
            return possible_trending_break_value
        else:
            return self.cd.prm.min_trending_break_value