class Results:
    def __init__(self, monitor):
        self.m = monitor
        self.data = []
        self.show_results_history = False


    def append(self, pnl, fantasy_pnl, fluctuation, reversal):
    	self.show_results_history = True
    	self.data.append(Result(pnl, fantasy_pnl, fluctuation, reversal, self.m.last_decision))


    def state_str(self):
        output = ""
        if self.show_results_history:
            self.show_results_history = False
            output += "  RESULTS:\n"
            for result in self.data:
                output += f"    {result.state_str()}\n"
            output += "    ___real_pnl: {:+.2f}\n".format(sum(map(lambda r: r.pnl, self.data)))
            output += "    fantasy_pnl: {:+.2f}\n".format(sum(map(lambda r: r.fantasy_pnl, self.data)))
        return output



class Result:
    def __init__(self, pnl, fantasy_pnl, fluctuation, reversal, decision):
        self.pnl = pnl
        self.fantasy_pnl = fantasy_pnl
        self.fluctuation = fluctuation
        self.reversal = reversal
        self.decision = decision


    def state_str(self):
        output = (
            "pnl: {:+.2f}, "
            "fantasy_pnl: {:+.2f}, "
            "fluctuation: {:.2f}, "
            "reversal: {:.2f}, "
            "decision: '{}'"
        )
        output = output.format(self.pnl, self.fantasy_pnl, self.fluctuation, self.reversal,
            self.decision.state_str())
        return output
