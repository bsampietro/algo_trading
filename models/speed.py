class Speed:
    def __init__(self, monitor):
        self.mtr = monitor

        self.max_time_speed = []
        self.min_time_speed = []
        self.max_trend_speed = []
        self.min_trend_speed = []
        self.is_time_speeding = 0
        self.is_trend_speeding = 0


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
        self.update_time_speed()
        self.update_trend_speed()


    def update_time_speed(self):
        price_data = self.mtr.data_since(5)
        if len(price_data) < 2:
            return
        max_ticks = 0
        min_ticks = 0
        for cdp in reversed(price_data):
            ticks = self.mtr.ticks((price_data[-1].price - cdp.price))
            if ticks > max_ticks:
                max_ticks = ticks
            elif ticks < min_ticks:
                min_ticks = ticks

        # Long
        if len(self.max_time_speed) >= 2:
            if self.max_time_speed[-1].time - self.max_time_speed[0].time > self.mtr.prm.primary_look_back_time - 200:
                if max_ticks > max(self.max_time_speed, key=lambda sp: sp.ticks).ticks * 1.20:
                    self.is_time_speeding = 1

            while self.max_time_speed[-1].time - self.max_time_speed[0].time > self.mtr.prm.primary_look_back_time:
                self.max_time_speed.pop(0)
        
        if max_ticks > 0:
            self.max_time_speed.append(SpeedPoint(max_ticks, price_data[-1].time))

        # Short
        if len(self.min_time_speed) >= 2:
            if self.min_time_speed[-1].time - self.min_time_speed[0].time > self.mtr.prm.primary_look_back_time - 200:
                if min_ticks < min(self.min_time_speed, key=lambda sp: sp.ticks).ticks * 1.20:
                    self.is_time_speeding = -1

            while self.min_time_speed[-1].time - self.min_time_speed[0].time > self.mtr.prm.primary_look_back_time:
                self.min_time_speed.pop(0)

        if min_ticks < 0:
            self.min_time_speed.append(SpeedPoint(min_ticks, price_data[-1].time))


    def update_trend_speed(self):
        price_data = self.mtr.data_since(5)
        if len(price_data) < 2:
            return
        self.is_trend_speeding = 0
        max_ticks = 0
        min_ticks = 0
        long_trend = price_data[-1].trend > 0
        complete_iteration = True
        for i in reversed(range(len(price_data) - 1)):
            if long_trend:
                if price_data[i].trend < 0:
                    max_ticks = price_data[-1].trend - price_data[i+1].trend
                    complete_iteration = False
                    break
            else:
                if price_data[i].trend > 0:
                    min_ticks = price_data[-1].trend - price_data[i+1].trend
                    complete_iteration = False
                    break
        if long_trend:
            if complete_iteration:
                max_ticks = price_data[-1].trend - price_data[0].trend

            if len(self.max_trend_speed) >= 2:
                if self.max_trend_speed[-1].time - self.max_trend_speed[0].time > self.mtr.prm.primary_look_back_time - 200:
                    if max_ticks > max(self.max_trend_speed, key=lambda sp: sp.ticks).ticks * 1.20:
                        self.is_trend_speeding = 1

                while self.max_trend_speed[-1].time - self.max_trend_speed[0].time > self.mtr.prm.primary_look_back_time:
                    self.max_trend_speed.pop(0)

            if max_ticks > 0:
                self.max_trend_speed.append(SpeedPoint(max_ticks, price_data[-1].time))
        else:
            if complete_iteration:
                min_ticks = price_data[-1].trend - price_data[0].trend

            if len(self.min_trend_speed) >= 2:
                if self.min_trend_speed[-1].time - self.min_trend_speed[0].time > self.mtr.prm.primary_look_back_time - 200:
                    if min_ticks < min(self.min_trend_speed, key=lambda sp: sp.ticks).ticks * 1.20:
                        self.is_trend_speeding = -1
                    
                while self.min_trend_speed[-1].time - self.min_trend_speed[0].time > self.mtr.prm.primary_look_back_time:
                    self.min_trend_speed.pop(0)

            if min_ticks < 0:
                self.min_trend_speed.append(SpeedPoint(min_ticks, price_data[-1].time))


    def state_str(self):
        output = ""
        output += "max_time_speed:\n"
        for sp in self.max_time_speed:
            output += f"{sp.state_str()}\n"

        output += "min_time_speed:\n"
        for sp in self.min_time_speed:
            output += f"{sp.state_str()}\n"

        output += "max_trend_speed:\n"
        for sp in self.max_trend_speed:
            output += f"{sp.state_str()}\n"

        output += "min_trend_speed:\n"
        for sp in self.min_trend_speed:
            output += f"{sp.state_str()}\n"

        output += f"is_time_speeding: {self.is_time_speeding}\n"
        output += f"is_trend_speeding: {self.is_trend_speeding}\n"
        return output


class SpeedPoint:
    def __init__(self, ticks, time):
        self.ticks = ticks
        self.time = time
        

    def state_str(self):
        output = (
            f"'ticks': {self.ticks}, "
            f"'time': {self.time}"
        )
        return output