from functools import lru_cache

class Decision:
    def __init__(self, monitor):
        self.m = monitor
        self.breaking = 0
        self.in_line = 0
        self.density_direction = None


    @lru_cache(maxsize=None)
    def should(self):
        decision = ''
        total_score = sum((self.breaking, self.in_line))
        # all(map(lambda nr: nr > 0, self.tupleize_scores())) and total_points >= 5
        if total_score >= 5 and self.breaking >= 0 and self.in_line >= 0:
            decision = 'buy'
        elif total_score <= -5 and self.breaking <= 0 and self.in_line <= 0:
            decision = 'sell'
        return decision


    def breaking_reason(self):
        return self.breaking != 0


    def state_str(self):
        output = (
            "breaking: {}, "
            "in_line: {}"
        )
        output = output.format(self.breaking, self.in_line)
        return output