class Speed:
    def __init__(self, monitor):
        self.mtr = monitor

        self.time_speed = []
        self.trend_speed = []
        self.time_speeding_ticks = 0
        self.trend_speeding_ticks = 0

        self._speed_min_time_passed = False
        self._last_time_speeding_time = 0


    def price_change(self):
        self.update_speeds()


    def find_criteria_speeding(self):
        pass
        # data = self.mtr.data_since(self.mtr.prm.speeding_time)
        # if len(data) <= 2:
        #     return None
        # if not (all(map(lambda cdp: cdp.trend > 0, data)) or all(map(lambda cdp: cdp.trend < 0, data))):
        #     return None
        # if self.mtr.ticks(abs(data[-1].price - data[0].price)) / abs(data[-1].time - data[0].time) < 1:
        #     return None

        # if data[-1].price > data[0].price:
        #     return 'up'
        # else:
        #     return 'down'


    def update_speeds(self):
        self.update_time_speed()
        # self.update_trend_speed()


    def update_time_speed(self):
        self.time_speeding_ticks = 0
        time_or_duration = self.mtr.prm.speeding_time
        if self.mtr.data[-1].time - self._last_time_speeding_time < self.mtr.prm.speeding_time:
            time_or_duration = self._last_time_speeding_time
        price_data = self.mtr.data_since(time_or_duration)
        if len(price_data) < 2:
            return
        max_ticks = 0
        for cdp in reversed(price_data):
            ticks = self.mtr.ticks((price_data[-1].price - cdp.price))
            if abs(ticks) > abs(max_ticks):
                max_ticks = ticks

        if max_ticks <= -5 or max_ticks >= 5:
            self.time_speed.append(SpeedPoint(max_ticks, price_data[-1].time))

        if len(self.time_speed) == 0:
            return

        if (price_data[-1].time - self.time_speed[0].time < self.mtr.prm.primary_look_back_time - 300 and
                not self._speed_min_time_passed):
            return
        self._speed_min_time_passed = True

        while price_data[-1].time - self.time_speed[0].time > self.mtr.prm.primary_look_back_time:
            self.time_speed.pop(0)

        if 5 <= max_ticks >= max(self.time_speed, key=lambda sp: sp.ticks).ticks * 0.75:
            self._last_time_speeding_time = price_data[-1].time
            self.time_speeding_ticks = max_ticks
        elif -5 >= ticks <= min(self.time_speed, key=lambda sp: sp.ticks).ticks * 0.75:
            self._last_time_speeding_time = price_data[-1].time
            self.time_speeding_ticks = max_ticks


    def update_trend_speed(self):
        self.trend_speeding_ticks = 0
        price_data = self.mtr.data_since(5)
        if len(price_data) < 2:
            return
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

        if ticks <= -5 or ticks >= 5:
            self.trend_speed.append(SpeedPoint(ticks, price_data[-1].time))
        
        if len(self.trend_speed) == 0:
            return

        if (price_data[-1].time - self.time_speed[0].time < self.mtr.prm.primary_look_back_time - 300 and
                not self._speed_min_time_passed):
            return
        self._speed_min_time_passed = True
            
        while price_data[-1].time - self.trend_speed[0].time > self.mtr.prm.primary_look_back_time:
            self.trend_speed.pop(0)

        if 5 <= ticks >= max(self.trend_speed, key=lambda sp: sp.ticks).ticks * 0.75:
            self.trend_speeding_ticks = ticks
        elif -5 >= ticks <= min(self.trend_speed, key=lambda sp: sp.ticks).ticks * 0.75:
            self.trend_speeding_ticks = ticks


    def state_str(self):
        output = ""
        # output += "time_speed:\n"
        # for sp in self.time_speed:
        #     output += f"{sp.state_str()}\n"

        # output += "trend_speed:\n"
        # for sp in self.trend_speed:
        #     output += f"{sp.state_str()}\n"

        if self.time_speeding_ticks != 0:
            output += "time_speeding_ticks: {:+d}\n".format(self.time_speeding_ticks)
        if self.trend_speeding_ticks != 0:
            output += "trend_speeding_ticks: {:+d}\n".format(self.trend_speeding_ticks)
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