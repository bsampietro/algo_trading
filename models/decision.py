import gvars

class Decision:
    def __init__(self, monitor):
        self.m = monitor

        self.direction = None # type: int
        self.last_price = None # type: float
        
        self.adjusting_ticks = None # type: int

        self.trend_pattern = gvars.TREND_PATTERN['neutral']

        self._scores_output = ""


    def is_breaking_in_range(self):
        # return isinstance(self, BreakingDecision)
        return 'density_data' in vars(self) # sounds hackisk but avoids importing BreakingDecision type


    def is_speeding(self):
        # return isinstance(self, SpeedingDecision)
        return 'time_speeding_points' in vars(self) # sounds hackisk but avoids importing SpeedingDecision type


    def should_close(self):
        trending_break_ticks = self.trending_break_ticks()
        gvars.datalog_buffer[self.m.ticker] += (f"    decision.should_close.trending_break_ticks: {trending_break_ticks}\n")

        # Time stop
        time_since_transaction = self.m.last_time() - self.ap.transaction_time
        if time_since_transaction > self.break_time():
            min_max = self.m.min_max_since(self.break_time())
            gvars.datalog_buffer[self.m.ticker] += (f"    decision.should_close.min_max[1].price: {min_max[1].price}\n")
            gvars.datalog_buffer[self.m.ticker] += (f"    decision.should_close.min_max[0].price: {min_max[0].price}\n")
            if self.m.ticks(min_max[1].price - min_max[0].price) <= trending_break_ticks:
                return True
        
        # Price stop
        if self.m.ticks(abs(self.m.last_price() - self.ap.trending_price())) >= trending_break_ticks:
            return True

        if self.reached_maximum():
            return True

        return False


    def all_scores(self):
        scores = []
        for funct_name, funct_obj in vars(type(self)).items():
            if funct_name[-6:] == '_score':
                score = funct_obj(self)
                self._scores_output += (f"{funct_name}: {score}, ")
                scores.append(score)
        return scores


    @property
    def ap(self):
        return self.m.position.ap



    # +++++ To be overwritten in child classes ++++

    def trending_break_ticks(self):
        pass

    def break_time(self):
        pass

    def reached_maximum(self):
        pass