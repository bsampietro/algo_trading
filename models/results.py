import statistics

class Results:
    def __init__(self, monitor):
        self.m = monitor
        self.data = []
        self.show_results_history = False


    def append(self, pnl, fantasy_pnl, fluctuation, reversal):
    	self.show_results_history = True
    	self.data.append(Result(pnl, fantasy_pnl, fluctuation, reversal, self.m.action_decision))


    def state_str(self):
        output = ""
        if self.show_results_history:
            self.show_results_history = False
            output += "  RESULTS:\n"
            for result in self.data:
                output += f"    {result.state_str()}\n"
            output += "    ___real_pnl: {:+.2f}\n".format(self.pnl())
            output += "    fantasy_pnl: {:+.2f}\n".format(self.fantasy_pnl())
            output += "            w/l: {} / {}\n".format(self.nr_of_wl('winners'), self.nr_of_wl('loosers'))
            output += "    average_win: {:+.2f}\n".format(self.average_wl('winners'))
            output += "   average_loss: {:+.2f}\n".format(self.average_wl('loosers'))
        return output


    def pnl(self):
        return sum(map(lambda r: r.pnl, self.data))

    def fantasy_pnl(self):
        return sum(map(lambda r: r.fantasy_pnl, self.data))

    def nr_of_wl(self, x):
        assert x in ('winners', 'loosers')
        multi = 1 if x == 'winners' else -1
        return len([r.pnl for r in self.data if multi * r.pnl > 0])

    def average_wl(self, x):
        assert x in ('winners', 'loosers')
        multi = 1 if x == 'winners' else -1
        results = [r.pnl for r in self.data if multi * r.pnl > 0]
        return statistics.mean(results) if len(results) > 0 else 0


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
