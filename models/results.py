import statistics

class Results:
    def __init__(self, monitor):
        self.m = monitor
        self.data = []
        self.show_results_history = False


    def append(self, pnl, fantasy_pnl, fluctuation, reversal, order_time, start_time, end_time):
    	self.show_results_history = True
    	self.data.append(Result(pnl, fantasy_pnl, fluctuation, reversal, self.m.action_decision, self.pnl(),
            order_time, start_time, end_time, self.m.initial_time))


    def pnl(self, last=None):
        data = self.data if last is None else self.data[-last:]
        return sum(map(lambda r: r.pnl, data))

    def nr_of_wl(self, x, last=None):
        data = self.data if last is None else self.data[-last:]
        assert x in ('winners', 'loosers')
        multi = 1 if x == 'winners' else -1
        return len([r.pnl for r in data if multi * r.pnl > 0])

    def average_pnl(self, last=None):
        data = self.data if last is None else self.data[-last:]
        return (sum(map(lambda r: r.pnl, data)) / len(data)) if len(data) > 0 else 0

    def average_wl(self, x):
        assert x in ('winners', 'loosers')
        multi = 1 if x == 'winners' else -1
        results = [r.pnl for r in self.data if multi * r.pnl > 0]
        return statistics.mean(results) if len(results) > 0 else 0
    
    def fantasy_pnl(self):
        return sum(map(lambda r: r.fantasy_pnl, self.data))

    def total_trades(self):
        return len(self.data)

    def acc_pnl(self):
        return self.data[-1].acc_pnl if len(self.data) > 0 else 0


    def state_str(self, *pshow):
        show = ('last', 'stats') if len(pshow) == 0 else pshow
        output = ""
        if self.show_results_history or len(pshow) > 0:
            self.show_results_history = False
            output += f"  RESULTS (live: {not self.m.test}):\n"
            if 'all' in show:
                for result in self.data:
                    output += f"    {result.state_str(self.m.prm.price_precision)}\n"
            if 'last' in show:
                output += f"    {self.data[-1].state_str(self.m.prm.price_precision)}\n"
            if 'stats' in show:
                output += (
                    "    ___real_pnl: {:+.{price_precision}f}\n"
                    "    fantasy_pnl: {:+.{price_precision}f}\n"
                    "            w/l: {} / {}\n"
                    "    average_win: {:+.{price_precision}f}\n"
                    "   average_loss: {:+.{price_precision}f}\n"
                    "    average_pnl: {:+.5f}\n"
                    "   total_trades: {}\n"
                ).format(self.pnl(), self.fantasy_pnl(),
                    self.nr_of_wl('winners'), self.nr_of_wl('loosers'),
                    self.average_wl('winners'), self.average_wl('loosers'),
                    self.average_pnl(), self.total_trades(),
                    price_precision = self.m.prm.price_precision)
        return output


class Result:
    def __init__(self, pnl, fantasy_pnl, fluctuation, reversal, decision, acc_pnl, order_time, start_time, end_time, initial_time):
        self.pnl = pnl
        self.fantasy_pnl = fantasy_pnl
        self.fluctuation = fluctuation
        self.reversal = reversal
        self.decision = decision
        self.acc_pnl = acc_pnl
        self.order_time = order_time
        self.start_time = start_time
        self.end_time = end_time
        self.initial_time = initial_time


    def canceled(self):
        return self.start_time == 0


    def state_str(self, price_precision = 2):
        output = (
            f"pnl: {self.pnl:+.{price_precision}f}, "
            f"f_pnl: {self.fantasy_pnl:+.{price_precision}f}, "
            f"fluct: {self.fluctuation:.{price_precision}f}, "
            f"rev: {self.reversal:.{price_precision}f}, "
            f"acc_pnl: {self.acc_pnl:>+6.{price_precision}f}, "
            f"o_time: {self.order_time - self.initial_time:>8.1f}, "
            f"s_time: {self.start_time - self.initial_time:>8.1f}, "
            f"e_time: {self.end_time - self.initial_time:>8.1f}, "
            f"decision: ({self.decision.state_str()}), "
        )
        return output
