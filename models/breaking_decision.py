from functools import lru_cache

from models.decision import Decision
import gvars
from lib import util

class BreakingDecision(Decision):
    def __init__(self, monitor, density_data):
        Decision.__init__(self, monitor)
        self.density_data = density_data

        self.breaking_duration_ok = False
        self.breaking_price_changes = 0
        self.in_line = 0
        self.trend_two = 0
        self.adjusting_ticks = None # type: int


    @lru_cache(maxsize=None)
    def should(self):
        decision = ''
        self.set_breaking_data()
        total_score = sum(self.all_scores())
        if total_score >= 6:
            self.adjusting_ticks = self.m.prm.trade_initiation_ticks
            if self.direction == 1:
                decision = 'buy'
            elif self.direction == -1:
                decision = 'sell'
        return decision


    # ++++++++ SCORES +++++++++++++
    
    def breaking_price_changes_score(self):
        score = 0
        if self.breaking_price_changes > self.m.prm.min_breaking_price_changes:
            score += self.m.prm.breaking_price_changes_score
            if self.breaking_duration_ok:
                score += self.m.prm.duration_score
        return score


    def in_line_score(self):
        return self.m.prm.in_line_score if self.in_line >= 3 else 0


    def trend_two_score(self):
        return self.m.prm.trend_two_score if self.trend_two > 0 else 0


    def density_direction_score(self):
        if not self.is_breaking_in_range():
            return 0
        score = 0
        if self.density_data.trend_density_direction in (gvars.DENSITY_DIRECTION['in'], gvars.DENSITY_DIRECTION['out-in']):
            score += self.m.prm.in_density_direction_score
            if self.density_data.anti_trend_density_direction in (gvars.DENSITY_DIRECTION['out'], gvars.DENSITY_DIRECTION['out-edge']):
                score += self.m.prm.out_density_direction_score
        return score


    def advantage_score(self):
        if not self.is_breaking_in_range():
            return 0
        score = 0
        if self.to_win_ticks() <= 1:
            score += -1000 # Big number so it doesn't place the trade
        if self.to_win_ticks() - self.to_loose_ticks() >= 1:
            score += self.m.prm.advantage_score
        return score

    # +++++++++++++++++++++++++++++


    def set_breaking_data(self):
        if (self.density_data.trend_density_direction in (gvars.DENSITY_DIRECTION['in'], gvars.DENSITY_DIRECTION['out-in']) and
                self.density_data.anti_trend_density_direction in (gvars.DENSITY_DIRECTION['out'], gvars.DENSITY_DIRECTION['out-edge'])):
            self.trend_pattern = gvars.TREND_PATTERN['reversal']
        elif (self.density_data.trend_density_direction in (gvars.DENSITY_DIRECTION['out'], gvars.DENSITY_DIRECTION['out-edge']) and
                self.density_data.anti_trend_density_direction in (gvars.DENSITY_DIRECTION['in'], gvars.DENSITY_DIRECTION['out-in'])):
            self.trend_pattern = gvars.TREND_PATTERN['follow']


    def trending_break_ticks(self):
        break_ticks = None
        trend_ticks = self.m.ticks(abs(self.density_data.trend_tuple[1] - self.ap.trending_price()))
        anti_trend_ticks = self.m.ticks(abs(self.ap.transaction_price - self.density_data.anti_trend_tuple[0]))

        # break_ticks = min(trend_ticks, anti_trend_ticks)
        if self.direction * self.m.ticks(self.ap.trending_price() - self.density_data.trend_tuple[1]) >= 0:
            break_ticks = self.m.prm.reached_first_target_break
        elif self.direction * self.m.ticks(self.ap.trending_price() - self.ap.transaction_price) >= 2:
            break_ticks = self.m.prm.made_two_break
        else:
            break_ticks = util.value_or_min_max(anti_trend_ticks, self.m.prm.min_max_loose_ticks)
        break_ticks += self.m.prm.reversal_addition_break if self.trend_pattern == gvars.TREND_PATTERN['reversal'] else 0
        return break_ticks


    def reached_maximum(self, ticks_to_maximum):
        if self.m.prm.max_winning_ticks is not None:
            if self.direction * (self.m.last_price() - self.ap.transaction_price) >= self.m.prm.max_winning_ticks - ticks_to_maximum:
                return True
        if self.direction * (self.m.last_price() - self.m.mid_price(self.density_data.trend_tuple[1:3])) >= 0 - ticks_to_maximum:
            return True
        else:
            return False


    @lru_cache(maxsize=None)
    def to_win_ticks(self):
        return self.m.ticks(abs(self.density_data.trend_tuple[1] - self.creation_price))


    @lru_cache(maxsize=None)
    def to_loose_ticks(self):
        return self.m.ticks(abs(self.density_data.anti_trend_tuple[0] - self.creation_price))
        

    @lru_cache(maxsize=None)
    def break_time(self):
        return self.m.prm.breaking_stop_time


    def state_str(self):
        output = "Breaking - "
        output += f"trend_pattern: {self.trend_pattern:+d}, "
        output += self._scores_output
        output += (
            f"breaking_price_changes: {self.breaking_price_changes:>3}, "
            f"breaking_duration_ok: {str(self.breaking_duration_ok):>5}, "
            f"in_line: {self.in_line}, "
            f"trend_two: {self.trend_two}, "
            f"adjusting_ticks: {self.adjusting_ticks}, "
        )
        return output