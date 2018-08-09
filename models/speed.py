class Speed:
    def __init__(self, monitor):
        self.mtr = monitor

        self.time_speed = []
        self.time_speeding_points = []

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


    def update_time_speed(self):
        # Get latest price data
        time_or_duration = self.mtr.prm.speeding_time
        if self._last_time_speeding_time > 0:
            if self.mtr.data[-1].time - self._last_time_speeding_time > self.mtr.prm.speeding_time / 2.0:
                time_or_duration = self._last_time_speeding_time
            else:
                return
        price_data = self.mtr.data_since(time_or_duration)

        if len(price_data) <= 1:
            self._last_time_speeding_time = 0
            self.time_speeding_points = []
            return

        # Process latest price data
        max_ticks = 0
        for cdp in reversed(price_data):
            ticks = self.mtr.ticks((price_data[-1].price - cdp.price))
            if abs(ticks) > abs(max_ticks):
                max_ticks = ticks

        # Create Speed point
        speed_point = SpeedPoint(
            ticks = max_ticks,
            price = price_data[-1].price,
            time = price_data[-1].time,
            changes = len(price_data) - 1, # -1 because it includes the change already counted before
            max_jump = max(price_data, key=lambda cdp: abs(cdp.jump)).jump
        )

        # Add to time speed
        if speed_point.ticks <= -4 or speed_point.ticks >= 4:
            self.time_speed.append(speed_point)

        # Return if not enough info
        if len(self.time_speed) == 0:
            return
        if (price_data[-1].time - self.time_speed[0].time < self.mtr.prm.primary_look_back_time - 300 and
                not self._speed_min_time_passed):
            return
        self._speed_min_time_passed = True

        # Remove old data
        while price_data[-1].time - self.time_speed[0].time > self.mtr.prm.primary_look_back_time:
            self.time_speed.pop(0)

        # Current decision
        if len(self.time_speeding_points) == 0:
            if 4 <= speed_point.ticks >= max(self.time_speed, key=lambda sp: sp.ticks).ticks * 0.75:
                self._last_time_speeding_time = price_data[-1].time
                self.time_speeding_points = [speed_point]
            elif -4 >= speed_point.ticks <= min(self.time_speed, key=lambda sp: sp.ticks).ticks * 0.75:
                self._last_time_speeding_time = price_data[-1].time
                self.time_speeding_points = [speed_point]
        elif len(self.time_speeding_points) <= 4:
            self._last_time_speeding_time = price_data[-1].time
            self.time_speeding_points.append(speed_point)
        else:
            self._last_time_speeding_time = 0
            self.time_speeding_points = []




    # def update_trend_speed(self):
    #     self.trend_speeding_ticks = 0
    #     price_data = self.mtr.data_since(5)
    #     if len(price_data) < 2:
    #         return
    #     ticks = 0
    #     complete_iteration = True
    #     for i in reversed(range(len(price_data) - 1)):
    #         if (price_data[-1].trend > 0 and price_data[i].trend < 0 or 
    #                 price_data[-1].trend < 0 and price_data[i].trend > 0):
    #             ticks = price_data[-1].trend - price_data[i+1].trend
    #             complete_iteration = False
    #             break
    #     if complete_iteration:
    #         ticks = price_data[-1].trend - price_data[0].trend

    #     if ticks <= -5 or ticks >= 5:
    #         self.trend_speed.append(SpeedPoint(ticks, price_data[-1].time))
        
    #     if len(self.trend_speed) == 0:
    #         return

    #     if (price_data[-1].time - self.time_speed[0].time < self.mtr.prm.primary_look_back_time - 300 and
    #             not self._speed_min_time_passed):
    #         return
    #     self._speed_min_time_passed = True
            
    #     while price_data[-1].time - self.trend_speed[0].time > self.mtr.prm.primary_look_back_time:
    #         self.trend_speed.pop(0)

    #     if 5 <= ticks >= max(self.trend_speed, key=lambda sp: sp.ticks).ticks * 0.75:
    #         self.trend_speeding_ticks = ticks
    #     elif -5 >= ticks <= min(self.trend_speed, key=lambda sp: sp.ticks).ticks * 0.75:
    #         self.trend_speeding_ticks = ticks


    def state_str(self):
        output = ""
        if len(self.time_speeding_points) > 0:
            output += "time_speed:\n"
            for sp in self.time_speed:
                output += f"{sp.state_str()}\n"

            output += "time_speeding_points:\n"
            for sp in self.time_speeding_points:
                output += f"{sp.state_str()}\n"
        return output


class SpeedPoint:
    def __init__(self, ticks, price, time, max_jump, changes):
        self.ticks = ticks
        self.price = price
        self.time = time
        self.max_jump = max_jump
        self.changes = changes
        self.danger_index = ticks * changes # changes acts as volume
        

    def state_str(self):
        output = (
            "'ticks': {:+d}, "
            "'price': {:.2f}, "
            "'time': {:.4f}, "
            "'max_jump': {:+d}, "
            "'changes': {}, "
            "'danger_index': {:.2f}"
        )
        output = output.format(self.ticks, self.price, self.time, self.max_jump, self.changes, self.danger_index)
        return output