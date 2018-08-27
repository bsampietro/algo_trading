import gvars
class ActivePosition:
    def __init__(self, position, monitor):
        self.m = monitor
        self.p = position
        self.results = []
        self.show_results_history = False
        self.initialize_state()


    def initialize_state(self):
        self.direction = 0
        self.up_trending_price = 0
        self.down_trending_price = 0
        self.transaction_time = 0


    def price_change(self):
        if self.p.position == 0:
            if self.direction != 0:
                # Just got out of position
                self.append_pnls()
                self.initialize_state()
                self.show_results_history = True
        else:
            if self.direction == 0:
                # Just got into new position
                self.direction = self.p.position
                self.up_trending_price = self.down_trending_price = self.m.last_price()
                self.transaction_time = self.m.last_time()
            else:
                # There is an active position
                if self.m.last_price() > self.up_trending_price:
                    self.up_trending_price = self.m.last_price()
                elif self.m.last_price() < self.down_trending_price:
                    self.down_trending_price = self.m.last_price()

    
    def trending_stopped(self):
        time_since_transaction = self.m.last_time() - self.transaction_time
        if time_since_transaction > self.m.prm.trending_break_time:
            min_max = self.m.min_max_since(self.m.prm.trending_break_time)
            gvars.datalog_buffer[self.m.ticker] += ("    1st: Inside trending.stopped:\n")
            gvars.datalog_buffer[self.m.ticker] += (f"      min_max_1: {min_max[1].price}\n")
            gvars.datalog_buffer[self.m.ticker] += (f"      min_max_0: {min_max[0].price}\n")
            gvars.datalog_buffer[self.m.ticker] += (f"      trending_break_value: {self.trending_break_value()}\n\n")
            if self.m.ticks(min_max[1].price - min_max[0].price) <= self.trending_break_value():
                return True
        if self.m.ticks(abs(self.m.last_price() - self.trending_price())) >= self.trending_break_value():
            return True
        return False


    def append_pnls(self):
        assert self.direction != 0
        self.results.append(
            Result(
                pnl = round(self.direction * (self.m.data[-2].price - self.transaction_price),
                    self.m.prm.price_precision),
                fantasy_pnl = round(self.direction * (self.trending_price() - self.transaction_price),
                    self.m.prm.price_precision),
                fluctuation = round(self.up_trending_price - self.down_trending_price,
                    self.m.prm.price_precision),
                reversal = round(abs(self.transaction_price - self.trending_price(False)),
                    self.m.prm.price_precision)
            )
        )


    def trending_price(self, straight=True):
        assert self.direction != 0
        if straight:
            return self.up_trending_price if self.direction == 1 else self.down_trending_price
        else:
            return self.down_trending_price if self.direction == 1 else self.up_trending_price


    @property
    def transaction_price(self):
        return self.p.order_price


    def state_str(self):
        output = ""
        if self.p.is_active():
            output += (
                f"  ACTIVE_POSITION {self.direction}:\n"
                f"    transaction_time: {self.transaction_time}\n"
                f"    up_trending_price: {self.up_trending_price}\n"
                f"    down_trending_price: {self.down_trending_price}\n"
            )
        if self.show_results_history:
            self.show_results_history = False
            output += "  RESULTS (ACTIVE_POSITION):\n"
            for result in self.results:
                output += f"    {result.state_str()}\n"
            output += "    ___real_pnl: {:+.2f}\n".format(sum(map(lambda r: r.pnl, self.results)))
            output += "    fantasy_pnl: {:+.2f}\n".format(sum(map(lambda r: r.fantasy_pnl, self.results)))
        return output

    # Private

    def trending_break_value(self):
        possible_trending_break_value = self.m.ticks(abs(self.trending_price() - self.transaction_price)) / 3.0
        if possible_trending_break_value > self.m.prm.min_trending_break_value:
            return possible_trending_break_value
        else:
            return self.m.prm.min_trending_break_value



class Result:
    def __init__(self, pnl=0, fantasy_pnl=0, fluctuation=0, reversal=0):
        self.pnl = pnl
        self.fantasy_pnl = fantasy_pnl
        self.fluctuation = fluctuation
        self.reversal = reversal


    def state_str(self):
        output = (
            "pnl: {:+.2f}, "
            "fantasy_pnl: {:+.2f}, "
            "fluctuation: {:.2f}, "
            "reversal: {:.2f}"
        )
        output = output.format(self.pnl, self.fantasy_pnl, self.fluctuation, self.reversal)
        return output
