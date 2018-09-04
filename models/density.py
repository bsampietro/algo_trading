import gvars
from lib import core

class Density:
    def __init__(self, monitor):
        self.m = monitor

        self.list_dps = []

        self.current_dp = None
        self.up_density_direction = None
        self.down_density_direction = None

        self.up_interval_max = 0
        self.up_interval_min = 0
        self.current_interval_max = 0
        self.current_interval_min = 0
        self.down_interval_max = 0
        self.down_interval_min = 0

        self.in_position = False

        # Private
        self._previous_price_data = []
        self.min_higher_area = 0
        self.max_lower_area = 0
        

    def price_change(self):
        self.update_state()


    def update_state(self):
        self.update_dps()
        self.update_intervals()


    def update_dps(self):
        data = self.m.data_since(self.m.prm.primary_look_back_time)
        if len(data) < 2:
            return

        # Add 2 newest prices
        for cdp in data[-2:]:
            dp = core.find(lambda dp: dp.price == cdp.price, self.list_dps)
            if dp is None:
                dp = DensityPoint(cdp.price)
                self.list_dps.append(dp)
            dp.duration += cdp.duration

        if (data[-1].time - data[0].time < self.m.prm.primary_look_back_time - 300 and 
                len(self._previous_price_data) == 0):
            return

        # Remove old elements
        for cdp in self._previous_price_data:
            if cdp == data[0]: # Pointer comparison
                break
            dp_index = core.index(lambda dp: dp.price == cdp.price, self.list_dps)
            dp = self.list_dps[dp_index]
            dp.duration -= cdp.duration
            if dp.price != self.m.last_price() and dp.duration < 0.001: # not last and duration close to zero (floating point errors)
                self.list_dps.pop(dp_index)
        self._previous_price_data = data

        self.list_dps.sort(key=lambda dp: dp.duration)

        # Set index, percentile and dpercentage
        total_duration = sum(map(lambda dp: dp.duration, self.list_dps))
        ipercentile_coefficient = 100.0 / (len(self.list_dps) - 1)
        for index, dp in enumerate(self.list_dps):
            dp.index = index
            dp.ipercentile = round(dp.index * ipercentile_coefficient)
            dp.dpercentage = (dp.duration / total_duration) * 100

        # set dpercentile 
        dpercentile_coefficient = 100.0 / max(self.list_dps, key=lambda dp: dp.dpercentage).dpercentage
        for dp in self.list_dps:
            dp.dpercentile = round(dp.dpercentage * dpercentile_coefficient)

        # set first_quarter and last_quarter dpercentiles
        quarter = round((len(self.list_dps) - 1) / 4)
        self.min_higher_area = self.list_dps[quarter * 3].dpercentile
        self.max_lower_area = self.list_dps[quarter].dpercentile

        self.list_dps.sort(key=lambda dp: dp.price)

        # Set height
        for i in range(len(self.list_dps)):
            self.list_dps[i].height = gvars.HEIGHT['mid']
        unreal_consecutives = 0
        trend = 1
        for i in range(len(self.list_dps)):
            if i == 0:
                j = i
            else:
                if self.list_dps[j].dpercentile < self.list_dps[i].dpercentile:
                    if trend == -1:
                        if (0 < self.list_dps[i].dpercentile - self.list_dps[j].dpercentile < 10) and unreal_consecutives < 3:
                            # Unreal change
                            unreal_consecutives += 1
                        else:
                            # Real change
                            self.list_dps[i-1].height = gvars.HEIGHT['min']
                            for k in range(j, i-1):
                                self.list_dps[k].height = gvars.HEIGHT['min']
                            unreal_consecutives = 0
                            j = i
                            trend = 1
                    else:
                        unreal_consecutives = 0
                        j = i
                elif self.list_dps[j].dpercentile > self.list_dps[i].dpercentile:
                    if trend == 1:
                        if (0 < self.list_dps[j].dpercentile - self.list_dps[i].dpercentile < 10) and unreal_consecutives < 3:
                            # Unreal change
                            unreal_consecutives += 1
                        else:
                            # Real change
                            self.list_dps[i-1].height = gvars.HEIGHT['max']
                            for k in range(j, i-1):
                                self.list_dps[k].height = gvars.HEIGHT['max']
                            unreal_consecutives = 0
                            j = i
                            trend = -1
                    else:
                        unreal_consecutives = 0
                        j = i


    def update_intervals(self):
        if len(self._previous_price_data) == 0:
            return

        self.in_position = False

        current_dp_index = core.index(lambda dp: dp.price == self.m.last_price(), self.list_dps)
        self.current_dp = self.list_dps[current_dp_index]

        if self.current_dp.dpercentile <= self.max_lower_area:
            self.up_density_direction = self.down_density_direction = gvars.DENSITY_DIRECTION['in']
        elif self.current_dp.dpercentile >= self.min_higher_area:
            self.up_density_direction = self.down_density_direction = gvars.DENSITY_DIRECTION['out']
        else:
            return

        # Set interval variables

        self.up_interval_max = 0
        self.up_interval_min = 0
        self.current_interval_max = 0
        self.current_interval_min = 0
        self.down_interval_max = 0
        self.down_interval_min = 0

        if self.up_density_direction == gvars.DENSITY_DIRECTION['out']:

            filled_position = 0
            for i in range(current_dp_index + 1, len(self.list_dps)): # up part
                
                if self.list_dps[i].dpercentile < self.min_higher_area and filled_position == 0:
                    self.current_interval_max = self.list_dps[i-1].price
                    filled_position = 1
                if self.list_dps[i].dpercentile >= self.min_higher_area and filled_position == 1:
                    self.up_interval_min = self.up_interval_max = self.list_dps[i].price
                    self.up_density_direction = gvars.DENSITY_DIRECTION['out-in']
                    break
                if self.list_dps[i].dpercentile <= self.max_lower_area and filled_position == 1:
                    self.up_interval_min = self.list_dps[i].price
                    filled_position = 2
                if self.list_dps[i].dpercentile > self.max_lower_area and filled_position == 2:
                    self.up_interval_max = self.list_dps[i-1].price
                    filled_position = 3
                    break

            filled_position = 0
            for i in reversed(range(current_dp_index)): # down part
            
                if self.list_dps[i].dpercentile < self.min_higher_area and filled_position == 0:
                    self.current_interval_min = self.list_dps[i+1].price
                    filled_position = 1
                if self.list_dps[i].dpercentile >= self.min_higher_area and filled_position == 1:
                    self.down_interval_max = self.down_interval_min = self.list_dps[i].price
                    self.down_density_direction = gvars.DENSITY_DIRECTION['out-in']
                    break
                if self.list_dps[i].dpercentile <= self.max_lower_area and filled_position == 1:
                    self.down_interval_max = self.list_dps[i].price
                    filled_position = 2
                if self.list_dps[i].dpercentile > self.max_lower_area and filled_position == 2:
                    self.down_interval_min = self.list_dps[i+1].price
                    filled_position = 3
                    break

        elif self.up_density_direction == gvars.DENSITY_DIRECTION['in']:

            filled_position = 0
            for i in range(current_dp_index + 1, len(self.list_dps)): # up part

                if self.list_dps[i].dpercentile > self.max_lower_area and filled_position == 0:
                    self.current_interval_max = self.list_dps[i-1].price
                    filled_position = 1
                if self.list_dps[i].dpercentile <= self.max_lower_area and filled_position == 1:
                    self.up_interval_min = self.up_interval_max = self.list_dps[i].price
                    self.up_density_direction = gvars.DENSITY_DIRECTION['in-out']
                    break
                if self.list_dps[i].dpercentile >= self.min_higher_area and filled_position == 1:
                    self.up_interval_min = self.list_dps[i].price
                    filled_position = 2
                if self.list_dps[i].dpercentile < self.min_higher_area and filled_position == 2:
                    self.up_interval_max = self.list_dps[i-1].price
                    filled_position = 3
                    break

            filled_position = 0
            for i in reversed(range(current_dp_index)): # down part

                if self.list_dps[i].dpercentile > self.max_lower_area and filled_position == 0:
                    self.current_interval_min = self.list_dps[i+1].price
                    filled_position = 1
                if self.list_dps[i].dpercentile <= self.max_lower_area and filled_position == 1:
                    self.down_interval_max = self.down_interval_min = self.list_dps[i].price
                    self.down_density_direction = gvars.DENSITY_DIRECTION['in-out']
                    break
                if self.list_dps[i].dpercentile >= self.min_higher_area and filled_position == 1:
                    self.down_interval_max = self.list_dps[i].price
                    filled_position = 2
                if self.list_dps[i].dpercentile < self.min_higher_area and filled_position == 2:
                    self.down_interval_min = self.list_dps[i+1].price
                    filled_position = 3
                    break

        if self.up_interval_max == 0:
            self.up_interval_max = self.list_dps[-1].price
        if self.up_interval_min == 0:
            self.up_interval_min = self.list_dps[-1].price
            self.up_density_direction = gvars.DENSITY_DIRECTION['out-edge']
        if self.current_interval_max == 0:
            self.current_interval_max = self.list_dps[-1].price
        if self.current_interval_min == 0:
            self.current_interval_min = self.list_dps[0].price
        if self.down_interval_max == 0:
            self.down_interval_max = self.list_dps[0].price
            self.down_density_direction = gvars.DENSITY_DIRECTION['out-edge']
        if self.down_interval_min == 0:
            self.down_interval_min = self.list_dps[0].price

        self.in_position = True


    def up_down_ratio(self, direction):
        mid_part = self.current_interval_max - self.current_interval_min
        if mid_part == 0:
            mid_part = self.m.prm.tick_price
        if direction == 1:
            up_part = self.up_interval_min - self.current_interval_max
            return up_part / mid_part
        else:
            down_part = self.current_interval_min - self.down_interval_max
            return down_part / mid_part


    def interval_tuples(self, direction):
        assert direction in (1, -1)
        up_tuple = (self.current_interval_max, self.up_interval_min, self.up_interval_max)
        down_tuple = (self.current_interval_min, self.down_interval_max, self.down_interval_min)
        if direction == 1:
            return (up_tuple, down_tuple)
        else:
            return (down_tuple, up_tuple)


    def density_direction(self, direction):
        assert direction in (1, -1)
        if direction == 1:
            return self.up_density_direction
        else:
            return self.down_density_direction


    def is_ready(self):
        return len(self._previous_price_data) > 0


    def copy_data(self):
        new_density = Density(None)
        new_density.up_density_direction = self.up_density_direction
        new_density.down_density_direction = self.down_density_direction
        new_density.up_interval_max = self.up_interval_max
        new_density.up_interval_min = self.up_interval_min
        new_density.current_interval_max = self.current_interval_max
        new_density.current_interval_min = self.current_interval_min
        new_density.down_interval_max = self.down_interval_max
        new_density.down_interval_min = self.down_interval_min
        return new_density


    def state_str(self):
        if self.current_dp is None:
            return ""
        output = "  DENSITY:\n"
        if self.in_position:
            for dp in reversed(self.list_dps):
                if self.down_interval_min <= dp.price <= self.up_interval_max:
                    output += f"    {dp.state_str()}\n"
        output += (
            f"    in_position: {self.in_position}\n"
            f"    up_density_direction: {gvars.DENSITY_DIRECTION_INV.get(self.up_density_direction)}\n"
            f"    down_density_direction: {gvars.DENSITY_DIRECTION_INV.get(self.down_density_direction)}\n"
            f"    min_higher_area: {self.min_higher_area}\n"
            f"    max_lower_area: {self.max_lower_area}\n"
            f"    {self.up_interval_max}\n"
            f"    {self.up_interval_min}\n"
            f"    {self.current_interval_max}\n"
            f"    current_dp: {self.current_dp.state_str()}\n"
            f"    {self.current_interval_min}\n"
            f"    {self.down_interval_max}\n"
            f"    {self.down_interval_min}\n"
        )
        return output


class DensityPoint:
    def __init__(self, price):
        self.price = price
        self.duration = 0
        self.index = 0
        self.ipercentile = 0
        self.dpercentage = 0
        self.dpercentile = 0
        self.height = gvars.HEIGHT['mid']

    def state_str(self):
        output = (
            "price: {:.2f}, "
            "duration: {:.2f}, "
            "index: {}, "
            "ipercentile: {}, "
            "dpercentage: {:.2f}, "
            "dpercentile: {}, "
            "height: {}"
        )
        output = output.format(self.price, self.duration, self.index, 
            self.ipercentile, self.dpercentage, self.dpercentile, self.height)
        return output