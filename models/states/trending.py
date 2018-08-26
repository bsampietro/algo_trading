import gvars

class Trending:
    def __init__(self, monitor):
        self.m = monitor
        self.initialize_state()
        self.fantasy_pnl = []
        self.pnl = []


    def initialize_state(self):
        self.direction = 0
        self.transaction_price = 0
        self.transaction_time = 0
        self.trending_price = 0


    def price_change(self):
        position = self.m.position.position
        if position == 0:
            if self.direction != 0:
                self.append_pnls()
                self.initialize_state()
        else:
            if self.direction == 0:
                self.direction = position
                self.transaction_price = self.m.last_price()
                self.transaction_time = self.m.last_time()
                self.trending_price = self.m.last_price()
            elif self.direction == 1:
                if self.m.last_price() > self.trending_price:
                    self.trending_price = self.m.last_price()
            elif self.direction == -1:
                if self.m.last_price() < self.trending_price:
                    self.trending_price = self.m.last_price()

    
    def stopped(self):
        time_since_transaction = self.m.last_time() - self.transaction_time
        if time_since_transaction > self.m.prm.trending_break_time:
            min_max = self.m.min_max_since(self.m.prm.trending_break_time)
            gvars.datalog_buffer[self.m.ticker] += ("    1st: Inside trending.stopped:\n")
            gvars.datalog_buffer[self.m.ticker] += (f"      min_max_1: {min_max[1].price}\n")
            gvars.datalog_buffer[self.m.ticker] += (f"      min_max_0: {min_max[0].price}\n")
            gvars.datalog_buffer[self.m.ticker] += (f"      trending_break_value: {self.trending_break_value()}\n\n")
            if self.m.ticks(min_max[1].price - min_max[0].price) <= self.trending_break_value():
                return True
        if self.m.ticks(abs(self.m.last_price() - self.trending_price)) >= self.trending_break_value():
            return True
        return False


    def append_pnls(self):
        if self.direction == 1:
            self.fantasy_pnl.append(round(self.trending_price - self.transaction_price, self.m.prm.price_precision))
            self.pnl.append(round(self.m.last_price() - self.transaction_price, self.m.prm.price_precision))
        elif self.direction == -1:
            self.fantasy_pnl.append(round(self.transaction_price - self.trending_price, self.m.prm.price_precision))
            self.pnl.append(round(self.transaction_price - self.m.last_price(), self.m.prm.price_precision))


    def state_str(self):
        output = ""
        if self.direction != 0:
            output += (
                f"  TRENDING {self.direction}:\n"
                f"    transaction_price: {self.transaction_price}\n"
                f"    transaction_time: {self.transaction_time}\n"
                f"    trending_price: {self.trending_price}\n"
            )
            output += "    fantasy_pnl: "
            for pnl in self.fantasy_pnl:
                output += "{:+.2f}, ".format(pnl)
            output += "\n"
            output += "    pnl:         "
            for pnl in self.pnl:
                output += "{:+.2f}, ".format(pnl)
            output += "\n"
            output += "    fantasy_pnl_sum: {:+.2f}\n".format(sum(self.fantasy_pnl))
            output += "    ___real_pnl_sum: {:+.2f}\n".format(sum(self.pnl))
        return output

    # Private

    def trending_break_value(self):
        possible_trending_break_value = self.m.ticks(abs(self.trending_price - self.transaction_price)) / 3.0
        if possible_trending_break_value > self.m.prm.min_trending_break_value:
            return possible_trending_break_value
        else:
            return self.m.prm.min_trending_break_value