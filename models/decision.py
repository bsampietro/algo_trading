from functools import lru_cache

import gvars

class Decision:
    def __init__(self, monitor):
        self.m = monitor

        self.density_data = None
        self.direction = 0
        self.breaking_in_range = False
        self.speeding = False
        
        self.breaking_duration_ok = False
        self.breaking_price_changes = 0
        self.in_line = 0
        self.trend_two = 0


    @lru_cache(maxsize=None)
    def should(self):
        decision = ''
        total_score = sum(self.tupleized_scores())
        if total_score >= 6:
            if self.direction == 1:
                decision = 'buy'
            elif self.direction == -1:
                decision = 'sell'
        return decision


    def should_close(self):
        ap = self.m.position.ap
        trending_break_ticks = self.trending_break_ticks()
        gvars.datalog_buffer[self.m.ticker] += (f"    trending_break_ticks: {trending_break_ticks}\n\n")

        # Time stop
        time_since_transaction = self.m.last_time() - ap.transaction_time
        if time_since_transaction > self.m.prm.trending_break_time:
            min_max = self.m.min_max_since(self.m.prm.trending_break_time)
            gvars.datalog_buffer[self.m.ticker] += (f"    t_stopped: min_max_1: {min_max[1].price}\n")
            gvars.datalog_buffer[self.m.ticker] += (f"    t_stopped: min_max_0: {min_max[0].price}\n")
            if self.m.ticks(min_max[1].price - min_max[0].price) <= trending_break_ticks:
                return True
        
        # Price stop
        if self.m.ticks(abs(self.m.last_price() - ap.trending_price())) >= trending_break_ticks:
            return True

        return False


    def tupleized_scores(self):
        return (self.breaking_price_changes_score(), self.in_line_score(), self.trend_two_score(), 
            self.density_direction_score(), self.breaking_duration_ok_score())


    # ++++++++ Scores +++++++++++++

    def breaking_price_changes_score(self):
        return 6 if self.breaking_price_changes > self.m.prm.min_breaking_price_changes else 0


    def in_line_score(self):
        return self.in_line if self.in_line >= 4 else 0


    def trend_two_score(self):
        return 3 if self.trend_two > 0 else 0


    def density_direction_score(self):
        if self.density_data and self.density_data.trend_density_direction in (gvars.DENSITY_DIRECTION['in'], gvars.DENSITY_DIRECTION['out-in']):
            return 3
        else:
            return 0


    def breaking_duration_ok_score(self):
        if self.breaking_duration_ok:
            return 0 # 2
        else:
            return 0

    # +++++++++++++++++++++++++++++

    
    def trending_break_ticks(self):
        assert self.breaking_in_range or self.speeding
        ap = self.m.position.ap
        if self.breaking_in_range:
            trend_ticks = self.m.ticks(abs(self.density_data.trend_tuple[1] - ap.trending_price()))
            anti_trend_ticks = self.m.ticks(abs(ap.transaction_price - self.density_data.anti_trend_tuple[0]))

            # break_ticks = min(trend_ticks, anti_trend_ticks)
            # if break_ticks < self.m.prm.min_trending_break_ticks:
            #     return self.m.prm.min_trending_break_ticks
            # elif break_ticks > self.m.prm.max_trending_break_ticks:
            #     return self.m.prm.max_trending_break_ticks
            # else:
            #     return break_ticks

            break_ticks = 0
            if self.direction * self.m.ticks(ap.trending_price() - ap.transaction_price) >= 2:
                break_ticks = 3
            elif self.direction * self.m.ticks(ap.trending_price() - self.density_data.trend_tuple[1]) >= 0:
                break_ticks = 1
            elif anti_trend_ticks <= 3:
                break_ticks = 3
            elif anti_trend_ticks >= 6:
                break_ticks = 6
            else:
                break_ticks = anti_trend_ticks
            return break_ticks
            # return 3
        else:
            return 4


    def reached_maximum(self):
        if self.direction * (self.m.last_price() - self.m.mid_price(self.density_data.trend_tuple[1:3])) >= 0 and self.breaking_in_range:
            return True
        else:
            return False


    def state_str(self):
        output = (
            "breaking_price_changes: {}, "
            "breaking_duration_ok: {}, "
            "breaking_in_range: {}, "
            "in_line: {}, "
            "trend_two: {}, "
        ).format(self.breaking_price_changes, self.breaking_duration_ok, self.breaking_in_range,
            self.in_line, self.trend_two)
        if self.density_data:
            output += "density_direction: {}".format(gvars.DENSITY_DIRECTION_INV.get(self.density_data.trend_density_direction))
        return output