class Speed:
    def __init__(self, monitor):
        self.mtr = monitor

        self.speeds = {}


    def price_change(self):
        # pass
        self.update_speeds()


    def find_criteria_speeding(self):
        data = self.mtr.data_since(self.mtr.prm.speeding_time_considered)
        if len(data) <= 2:
            return None
        if not (all(map(lambda cdp: cdp.trend > 0, data)) or all(map(lambda cdp: cdp.trend < 0, data))):
            return None
        if self.mtr.ticks(abs(data[-1].price - data[0].price)) / abs(data[-1].time - data[0].time) < 1:
            return None

        if data[-1].price > data[0].price:
            return 'up'
        else:
            return 'down'


    def find_time_speeding(self, last, ticks):
        if len(self.speeds) == 0:
            return 0
        price_data = self.mtr.data[-last:]
        last_cdp = price_data[-1]
        for cdp in reversed(price_data):
            ticks_move = self.mtr.ticks((last_cdp.price - cdp.price))
            if ticks_move == ticks:
                time = last_cdp.time - cdp.time
                if ticks not in self.speeds:
                    continue
                if time < self.speeds[ticks] * 1.20:
                    return 1 if ticks > 0 else -1
        return 0


    def update_speeds(self):
        price_data = self.mtr.data_since(self.mtr.prm.primary_density_back_time)
        if price_data[-1].time - price_data[0].time < self.mtr.prm.primary_density_back_time - 200:
            return

        self.speeds = {}
        for i in range(len(price_data)):
            for j in range(i, i + 15):
                if j > len(price_data) - 1:
                    break
                ticks = self.mtr.ticks((price_data[j].price - price_data[i].price))
                if ticks < -5 or ticks == 0 or ticks > 5:
                    continue
                time = price_data[j].time - price_data[i].time
                if ticks not in self.speeds:
                    self.speeds[ticks] = time
                else:
                    if time < self.speeds[ticks]:
                        self.speeds[ticks] = time


    def state_str(self):
        output = ""
        for ticks, time in sorted(self.speeds.items(), key=lambda k_v_set: k_v_set[0]):
            output += f"{ticks}: {time}\n"
        return output