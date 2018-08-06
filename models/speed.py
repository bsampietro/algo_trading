class Speed:
    def __init__(self, monitor):
        self.mtr = monitor

        self.time_speed = []
        self.trend_speed = []
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


    def update_speeds(self):
        self.update_time_speed()
        self.update_trend_speed()


    def update_time_speed(self):
        price_data = self.mtr.data_since(5)
        if len(price_data) < 2:
            return
        self.is_time_speeding = 0
        ticks = 0
        max_ticks = 0
        for cdp in reversed(price_data):
            ticks = self.mtr.ticks((price_data[-1].price - cdp.price))
            if abs(ticks) > abs(max_ticks):
                max_ticks = ticks

        if len(self.time_speed) >= 2:
            if self.time_speed[-1].time - self.time_speed[0].time > self.mtr.prm.primary_look_back_time - 200:
                if ticks > 0:
                    if 5 < ticks > max(self.time_speed, key=lambda sp: sp.ticks).ticks * 0.75:
                        self.is_time_speeding = ticks
                elif ticks < 0:
                    if -5 > ticks < min(self.time_speed, key=lambda sp: sp.ticks).ticks * 0.75:
                        self.is_time_speeding = ticks

            while self.time_speed[-1].time - self.time_speed[0].time > self.mtr.prm.primary_look_back_time:
                self.time_speed.pop(0)
        
        if ticks < -2 or ticks > 2:
            self.time_speed.append(SpeedPoint(ticks, price_data[-1].time))


    def update_trend_speed(self):
        price_data = self.mtr.data_since(5)
        if len(price_data) < 2:
            return
        self.is_trend_speeding = 0
        ticks = 0
        complete_iteration = True
        for i in reversed(range(len(price_data) - 1)):
            if (price_data[-1].trend > 0 and price_data[i].trend < 0 or 
                    price_data[-1].trend < 0 and price_data[i].trend > 0):
                ticks = price_data[-1].trend - price_data[i+1].trend
                complete_iteration = False
                break
        if complete_iteration:
            ticks = price_data[-1].trend - price_data[0].trend

        if len(self.trend_speed) >= 2:
            if self.trend_speed[-1].time - self.trend_speed[0].time > self.mtr.prm.primary_look_back_time - 200:
                if ticks > 0:
                    if 5 < ticks > max(self.trend_speed, key=lambda sp: sp.ticks).ticks * 0.75:
                        self.is_trend_speeding = ticks
                elif ticks < 0:
                    if -5 > ticks < min(self.trend_speed, key=lambda sp: sp.ticks).ticks * 0.75:
                        self.is_trend_speeding = ticks

            while self.trend_speed[-1].time - self.trend_speed[0].time > self.mtr.prm.primary_look_back_time:
                self.trend_speed.pop(0)

        if ticks < -2 or ticks > 2:
            self.trend_speed.append(SpeedPoint(ticks, price_data[-1].time))


    def state_str(self):
        output = ""
        # output += "time_speed:\n"
        # for sp in self.time_speed:
        #     output += f"{sp.state_str()}\n"

        # output += "trend_speed:\n"
        # for sp in self.trend_speed:
        #     output += f"{sp.state_str()}\n"

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