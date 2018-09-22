from functools import lru_cache

from models.decision import Decision
import gvars
from lib import util

class SpeedingDecision(Decision):
    def __init__(self, monitor, time_speeding_points):
        Decision.__init__(self, monitor)
        self.time_speeding_points = time_speeding_points


    @lru_cache(maxsize=None)
    def should(self):
        decision = ''
        self.set_speeding_data()
        self.adjusting_ticks = 0
        if self.direction == 1:
            decision = 'buy'
        elif self.direction == -1:
            decision = 'sell'
        return decision


    def set_speeding_data(self):
        if len(self.time_speeding_points) == 1:
            return
        if -1 <= self.time_speeding_points[-1].ticks <= 1:
            sum_ticks = sum(tsp.ticks for tsp in self.time_speeding_points)
            ini_ticks = self.time_speeding_points[0].ticks
            if ini_ticks > 0:
                if sum_ticks >= ini_ticks * 0.75:
                    self.direction = -1
                    self.trend_pattern = gvars.TREND_PATTERN['reversal']
            elif ini_ticks < 0:
                if sum_ticks <= ini_ticks * 0.75:
                    self.direction = 1
                    self.trend_pattern = gvars.TREND_PATTERN['reversal']
        elif len(self.time_speeding_points) == self.m.prm.time_speeding_points_length:
            if all(tsp.ticks >= 2 for tsp in self.time_speeding_points):
                self.direction = 1
                self.trend_pattern = gvars.TREND_PATTERN['follow']
            elif all(tsp.ticks <= -2 for tsp in self.time_speeding_points):
                self.direction = -1
                self.trend_pattern = gvars.TREND_PATTERN['follow']


    def trending_break_ticks(self):
        break_ticks = self.to_loose_ticks()
        break_ticks += 1 if self.trend_pattern == gvars.TREND_PATTERN['reversal'] else 0
        return break_ticks


    def reached_maximum(self):
        if (self.trend_pattern == gvars.TREND_PATTERN['reversal'] and
                self.direction * self.m.ticks(self.ap.trending_price() - self.ap.transaction_price) >= self.to_win_ticks()):
            return True
        else:
            return False


    @lru_cache(maxsize=None)
    def to_win_ticks(self):
        return util.value_or_min_max(
                abs(round(sum(tsp.ticks for tsp in self.time_speeding_points) * 0.75)),
                self.m.prm.speed_min_max_win_loose_ticks)


    @lru_cache(maxsize=None)
    def to_loose_ticks(self):
        return util.value_or_min_max(
                round(self.to_win_ticks() * 0.75),
                self.m.prm.speed_min_max_win_loose_ticks)


    @lru_cache(maxsize=None)
    def break_time(self):
        return self.m.prm.speeding_stop_time


    def state_str(self):
        output = "Speeding - "
        output += f"trend_pattern: {self.trend_pattern:+d}, "
        output += self._scores_output
        output += f"time_speeding_points: {str([tsp.ticks for tsp in self.time_speeding_points])}"
        return output