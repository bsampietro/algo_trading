import gvars
class ActivePosition:
    def __init__(self, monitor, position, fill_price, fill_time):
        self.m = monitor
        self.p = position
        
        self.direction = self.p.direction()
        assert self.direction != 0
        self.transaction_price = self.up_trending_price = self.down_trending_price = fill_price
        self.transaction_time = fill_time
        self.density_data = self.m.action_density_data


    def price_change(self):
        if self.m.last_price() > self.up_trending_price:
            self.up_trending_price = self.m.last_price()
        elif self.m.last_price() < self.down_trending_price:
            self.down_trending_price = self.m.last_price()


    def reached_minimum(self):
        if self.direction * (self.m.last_price() - self.density_data.anti_trend_tuple[0]) < 0:
            return True
        else:
            return False


    def reached_maximum(self):
        if self.direction * (self.m.last_price() - self.density_data.trend_tuple[1]) >= 0:
            return True
        else:
            return False

    
    def trending_stopped(self):
        trending_break_ticks = self.trending_break_ticks()
        gvars.datalog_buffer[self.m.ticker] += (f"    trending_break_ticks: {trending_break_ticks}\n\n")

        # Time stop
        time_since_transaction = self.m.last_time() - self.transaction_time
        if time_since_transaction > self.m.prm.trending_break_time:
            min_max = self.m.min_max_since(self.m.prm.trending_break_time)
            gvars.datalog_buffer[self.m.ticker] += (f"    t_stopped: min_max_1: {min_max[1].price}\n")
            gvars.datalog_buffer[self.m.ticker] += (f"    t_stopped: min_max_0: {min_max[0].price}\n")
            if self.m.ticks(min_max[1].price - min_max[0].price) <= trending_break_ticks:
                return True
        
        # Price stop
        if self.m.ticks(abs(self.m.last_price() - self.trending_price())) >= trending_break_ticks:
            return True

        return False


    def append_results(self, fill_price, fill_time):
        self.m.results.append(
            pnl = round(self.direction * (fill_price - self.transaction_price),
                self.m.prm.price_precision),
            fantasy_pnl = round(self.direction * (self.trending_price() - self.transaction_price),
                self.m.prm.price_precision),
            fluctuation = round(self.up_trending_price - self.down_trending_price,
                self.m.prm.price_precision),
            reversal = round(abs(self.transaction_price - self.trending_price(False)),
                self.m.prm.price_precision),
            order_time = self.p.order_time,
            start_time = self.transaction_time,
            end_time = fill_time
        )


    def trending_price(self, straight=True):
        if straight:
            return self.up_trending_price if self.direction == 1 else self.down_trending_price
        else:
            return self.down_trending_price if self.direction == 1 else self.up_trending_price


    def state_str(self):
        output = (
            f"  Active Position {self.direction}:\n"
            f"    transaction_price: {self.transaction_price:.{self.m.prm.price_precision}f}\n"
            f"    transaction_time: {self.transaction_time:.4f}\n"
            f"    up_trending_price: {self.up_trending_price:.{self.m.prm.price_precision}f}\n"
            f"    down_trending_price: {self.down_trending_price:.{self.m.prm.price_precision}f}\n"
        )
        return output


    def trending_break_ticks(self):
        # possible_trending_break_ticks = self.m.ticks(abs(self.trending_price() - self.transaction_price)) / 3.0
        # if possible_trending_break_ticks > self.m.prm.min_trending_break_ticks:
        #     return possible_trending_break_ticks
        # else:
        #     return self.m.prm.min_trending_break_ticks

        trend_ticks = self.m.ticks(abs(self.density_data.trend_tuple[1] - self.trending_price()))
        anti_trend_ticks = self.m.ticks(abs(self.transaction_price - self.density_data.anti_trend_tuple[0]))

        # break_ticks = min(trend_ticks, anti_trend_ticks)
        # if break_ticks < self.m.prm.min_trending_break_ticks:
        #     return self.m.prm.min_trending_break_ticks
        # elif break_ticks > self.m.prm.max_trending_break_ticks:
        #     return self.m.prm.max_trending_break_ticks
        # else:
        #     return break_ticks

        break_ticks = 0
        if self.direction * (self.trending_price() - self.transaction_price) >= 2:
            break_ticks = 3
        elif self.direction * (self.trending_price() - self.density_data.trend_tuple[1]) >= 0:
            break_ticks = 1
        elif anti_trend_ticks <= 3:
            break_ticks = 3
        elif anti_trend_ticks >= 6:
            break_ticks = 6
        else:
            break_ticks = anti_trend_ticks
        return break_ticks
        
        # return 3

