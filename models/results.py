class Results:
    def __init__(self, monitor):
        self.m = monitor
        self.data = []
        self.show_results_history = False


    def append(self, pnl=0, fantasy_pnl=0, fluctuation=0, reversal=0):
    	self.show_results_history = True
    	self.data.append(Result(pnl, fantasy_pnl, fluctuation, reversal))


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
