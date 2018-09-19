class Speed:
    def __init__(self, monitor):
        self.m = monitor

        self.time_speed = []
        self.time_speeding_points = []

        self._speed_min_time_passed = False
        self._last_time_speeding_time = 0
        self._show_full_list_in_state_str = True


    def price_change(self):
        self.update_time_speed()


    def find_criteria_speeding(self):
        pass
        # data = self.m.data_since(self.m.prm.speeding_time)
        # if len(data) <= 2:
        #     return None
        # if not (all(map(lambda cdp: cdp.trend > 0, data)) or all(map(lambda cdp: cdp.trend < 0, data))):
        #     return None
        # if self.m.ticks(abs(data[-1].price - data[0].price)) / abs(data[-1].time - data[0].time) < 1:
        #     return None

        # if data[-1].price > data[0].price:
        #     return 'up'
        # else:
        #     return 'down'


    def update_time_speed(self):
        # Get latest price data
        time_or_duration = self.m.prm.speeding_time
        if self._last_time_speeding_time > 0:
            if self.m.data[-1].time - self._last_time_speeding_time > self.m.prm.speeding_time / 2.0:
                time_or_duration = self._last_time_speeding_time
            else:
                return
        price_data = self.m.data_since(time_or_duration)

        if len(price_data) <= 1:
            self._last_time_speeding_time = 0
            self.time_speeding_points = []
            self._show_full_list_in_state_str = True
            return

        # Create Speed point
        speed_point = SpeedPoint(
            ticks = self.m.ticks(price_data[-1].price - price_data[0].price),
            max_ticks = self.m.ticks(max(price_data, key=lambda cdp: cdp.price).price - min(price_data, key=lambda cdp: cdp.price).price),
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
        if (price_data[-1].time - self.time_speed[0].time < self.m.prm.primary_look_back_time - 300 and
                not self._speed_min_time_passed):
            return
        self._speed_min_time_passed = True

        # Remove old data
        while len(self.time_speed) > 0 and price_data[-1].time - self.time_speed[0].time > self.m.prm.primary_look_back_time:
            self.time_speed.pop(0)

        # Current decision
        if len(self.time_speeding_points) == 0:
            if 4 <= speed_point.ticks >= max(self.time_speed, key=lambda sp: sp.ticks).ticks * 0.75:
                self._last_time_speeding_time = price_data[-1].time
                self.time_speeding_points = [speed_point]
            elif -4 >= speed_point.ticks <= min(self.time_speed, key=lambda sp: sp.ticks).ticks * 0.75:
                self._last_time_speeding_time = price_data[-1].time
                self.time_speeding_points = [speed_point]
        elif len(self.time_speeding_points) <= self.m.prm.time_speeding_points_length - 1: # <= X if want to have X + 1 max speeding points
            self._last_time_speeding_time = price_data[-1].time
            self.time_speeding_points.append(speed_point)
        else:
            self._last_time_speeding_time = 0
            self.time_speeding_points = []
            self._show_full_list_in_state_str = True


    def is_speeding(self):
        return len(self.time_speeding_points) > 0


    def state_str(self):
        output = ""
        if len(self.time_speeding_points) > 0:
            output += "  SPEED:\n"
            if self._show_full_list_in_state_str:
                self._show_full_list_in_state_str = False
                high_percentile = max(self.time_speed, key=lambda sp: sp.ticks).ticks * 0.75
                min_percentile = min(self.time_speed, key=lambda sp: sp.ticks).ticks * 0.75
                output += "    time_speed:\n"
                for sp in self.time_speed:
                    if sp.ticks <= min_percentile or sp.ticks >= high_percentile:
                        output += f"      {sp.state_str(self.m.prm.price_precision)}\n"
            output += "    time_speeding_points:\n"
            for sp in self.time_speeding_points:
                output += f"      {sp.state_str(self.m.prm.price_precision)}\n"
        return output


class SpeedPoint:
    def __init__(self, ticks, max_ticks, price, time, max_jump, changes):
        self.ticks = ticks
        self.max_ticks = max_ticks
        self.price = price
        self.time = time
        self.max_jump = max_jump
        self.changes = changes
        self.danger_index = ticks * changes # changes acts as volume
        

    def state_str(self, price_precision = 2):
        output = (
            "ticks: {:+d}, "
            "max_ticks: {}, "
            "price: {:.{price_precision}f}, "
            "time: {:.4f}, "
            "max_jump: {:+d}, "
            "changes: {}, "
            "danger_index: {:.2f}"
        )
        output = output.format(self.ticks, self.max_ticks, self.price, self.time,
            self.max_jump, self.changes, self.danger_index, price_precision = price_precision)
        return output