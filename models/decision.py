from functools import lru_cache

import gvars

class Decision:
    def __init__(self, monitor):
        self.m = monitor
        self.breaking_in_range = False
        self.density_direction = None

        # Score
        self.breaking_price_changes_and_duration = 0
        self.in_line = 0
        self.trend_two = 0


    @lru_cache(maxsize=None)
    def should(self):
        decision = ''
        total_score = 0
        if self.density_direction in (gvars.DENSITY_DIRECTION['in'], gvars.DENSITY_DIRECTION['out-in']):
            total_score += 3
        total_score += sum(self.tupleized_scores())
        if total_score >= 6 and all(map(lambda nr: nr >= 0, self.tupleized_scores())):
            decision = 'buy'
        elif total_score <= -6 and all(map(lambda nr: nr <= 0, self.tupleized_scores())):
            decision = 'sell'
        return decision


    def tupleized_scores(self):
        return (self.breaking_price_changes_and_duration, self.in_line, self.trend_two)


    def state_str(self):
        output = (
            "bkr_pr_ch_and_drt: {}, "
            "in_line: {}, "
            "density_direction: {}"
        )
        output = output.format(self.breaking_price_changes_and_duration, self.in_line,
            gvars.DENSITY_DIRECTION_INV.get(self.density_direction))
        return output