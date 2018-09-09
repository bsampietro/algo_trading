from functools import lru_cache

import gvars

class Decision:
    def __init__(self, monitor):
        self.m = monitor
        self.direction = 0
        self.breaking_in_range = False
        
        self.breaking_duration_ok = False
        self.density_direction = 0
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


    def tupleized_scores(self):
        return (self.breaking_price_changes_score(), self.in_line_score(), self.trend_two_score(), 
            self.density_direction_score(), self.breaking_duration_ok_score())


    def breaking_price_changes_score(self):
        return 6 if self.breaking_price_changes > 0 else 0

    def in_line_score(self):
        return self.in_line

    def trend_two_score(self):
        return 3 if self.trend_two > 0 else 0

    def density_direction_score(self):
        if self.density_direction in (gvars.DENSITY_DIRECTION['in'], gvars.DENSITY_DIRECTION['out-in']):
            return 3
        else:
            return 0

    def breaking_duration_ok_score(self):
        if self.breaking_duration_ok:
            return 2
        else:
            return 0


    def state_str(self):
        output = (
            "breaking_price_changes: {}, "
            "breaking_duration_ok: {}, "
            "breaking_in_range: {}, "
            "in_line: {}, "
            "trend_two: {}, "
            "density_direction: {}"
        )
        output = output.format(self.breaking_price_changes, self.breaking_duration_ok, self.breaking_in_range,
            self.in_line, self.trend_two, gvars.DENSITY_DIRECTION_INV.get(self.density_direction),
            )
        return output