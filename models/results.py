import statistics

class Results:
    def __init__(self, monitor):
        self.m = monitor
        self.data = []
        self.show_results_history = False


    def append(self, pnl, fantasy_pnl, fluctuation, reversal, order_time, start_time, end_time):
    	self.show_results_history = True
    	self.data.append(Result(pnl, fantasy_pnl, fluctuation, reversal, order_time,
            start_time, end_time, self.m.action_decision))


    def state_str(self):
        output = ""
        if self.show_results_history:
            self.show_results_history = False
            output += "  RESULTS:\n"
            for result in self.data:
                output += f"    {result.state_str(self.m.prm.price_precision)}\n"
            output += (
                "    ___real_pnl: {:+.{price_precision}f}\n"
                "    fantasy_pnl: {:+.{price_precision}f}\n"
                "            w/l: {} / {}\n"
                "    average_win: {:+.{price_precision}f}\n"
                "   average_loss: {:+.{price_precision}f}\n"
            ).format(self.pnl(), self.fantasy_pnl(),
                self.nr_of_wl('winners'), self.nr_of_wl('loosers'),
                self.average_wl('winners'), self.average_wl('loosers'),
                price_precision = self.m.prm.price_precision)
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
    def __init__(self, pnl, fantasy_pnl, fluctuation, reversal, order_time, start_time, end_time, decision):
        self.pnl = pnl
        self.fantasy_pnl = fantasy_pnl
        self.fluctuation = fluctuation
        self.reversal = reversal
        self.order_time = order_time
        self.start_time = start_time
        self.end_time = end_time
        self.decision = decision


    def canceled(self):
        return self.start_time == 0


    def state_str(self, price_precision = 2):
        output = (
            "pnl: {:+.{price_precision}f}, "
            "f_pnl: {:+.{price_precision}f}, "
            "fluct: {:.{price_precision}f}, "
            "rev: {:.{price_precision}f}, "
            "o_time: {:>15.2f}, "
            "s_time: {:>15.2f}, "
            "e_time: {:>15.2f}, "
            "decision: '{}'"
        ).format(self.pnl, self.fantasy_pnl, self.fluctuation, self.reversal, self.order_time,
            self.start_time, self.end_time, self.decision.state_str(), price_precision = price_precision)
        return output
