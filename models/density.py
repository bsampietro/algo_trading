import gvars
from lib import core

class Density:
    def __init__(self, monitor):
        self.mtr = monitor
        
        self.data = []

        self.list_dps = []

        self.current_dp = None
        self.density_direction = ''

        self.up_interval_max = 0
        self.up_interval_min = 0
        self.current_interval_max = 0
        self.current_interval_min = 0
        self.down_interval_max = 0
        self.down_interval_min = 0

        self.in_position = False

        # Private
        self._previous_price_data = []
        

    def price_change(self):
        self.update_state()


    def update_state(self):
        self.update_dps()
        self.update_intervals()


    def update_dps(self):
        data = self.mtr.data_since(self.mtr.prm.primary_density_back_time)
        if len(data) < 2:
            return

        # Add 2 newest prices
        for cdp in data[-2:]:
            dp = core.find(lambda dp: dp.price == cdp.price, self.list_dps)
            if dp is None:
                dp = DensityPoint(cdp.price)
                self.list_dps.append(dp)
            dp.duration += cdp.duration

        if (data[-1].time - data[0].time < self.mtr.prm.primary_density_back_time - 300 and 
                len(self._previous_price_data) == 0):
            return

        # Remove old elements
        for cdp in self._previous_price_data:
            if cdp == data[0]: # Pointer comparison
                break
            dp_index = core.index(lambda dp: dp.price == cdp.price, self.list_dps)
            self.list_dps[dp_index].duration -= cdp.duration
            if self.list_dps[dp_index].duration < 0.001: # because of floating point errors
                self.list_dps.pop(dp_index)
        self._previous_price_data = data

        # Set value
        self.list_dps.sort(key=lambda dp: dp.duration, reverse = True)
        for index, dp in enumerate(self.list_dps):
            dp.value = index
        
        # Set percentile
        percentile_coefficient = 100.0 / (self.max_value() - 1)
        for dp in self.list_dps:
            dp.percentile = round(dp.value * percentile_coefficient)

        self.list_dps.sort(key=lambda dp: dp.price)


    def update_intervals(self):
        if len(self.list_dps) == 0:
            return

        self.in_position = False

        current_dp_index = core.index(lambda dp: dp.price == self.mtr.last_price(), self.list_dps)
        self.current_dp = self.list_dps[current_dp_index]

        if self.current_dp.percentile <= 20:
            self.density_direction = 'out'
        elif self.current_dp.percentile >= 80:
            self.density_direction = 'in'
        else:
            return

        # Set interval variables

        up_interval_max = 0
        up_interval_min = 0
        current_interval_max = 0
        current_interval_min = 0
        down_interval_max = 0
        down_interval_min = 0

        if self.density_direction == 'out':

            wrong_consecutives = 0
            filled_position = 0
            # Up Part
            for i in range(current_dp_index + 1, len(self.list_dps)): # up part

                if filled_position != 1:
                    j = i
                elif self.list_dps[i].percentile - self.list_dps[j].percentile < -30:
                    return
                elif self.list_dps[i].percentile - self.list_dps[j].percentile < -10:
                    wrong_consecutives += 1
                    if wrong_consecutives == 3:
                        return
                else:
                    j = i

                if self.list_dps[i].percentile <= 20 and filled_position == 1:
                    return
                
                if self.list_dps[i].percentile > 20 and filled_position == 0:
                    current_interval_max = self.list_dps[i-1].price
                    filled_position = 1
                elif self.list_dps[i].percentile >= 80 and filled_position == 1:
                    up_interval_min = self.list_dps[i].price
                    filled_position = 2
                elif self.list_dps[i].percentile < 80 and filled_position == 2:
                    up_interval_max = self.list_dps[i-1].price
                    filled_position = 3
                    break

            wrong_consecutives = 0
            filled_position = 0
            # Down Part
            for i in reversed(range(current_dp_index)): # down part

                if filled_position != 1:
                    j = i
                elif self.list_dps[i].percentile - self.list_dps[j].percentile < -30:
                    return
                elif self.list_dps[i].percentile - self.list_dps[j].percentile < -10:
                    wrong_consecutives += 1
                    if wrong_consecutives == 3:
                        return
                else:
                    j = i
                
                if self.list_dps[i].percentile <= 20 and filled_position == 1:
                    return
            
                if self.list_dps[i].percentile > 20 and filled_position == 0:
                    current_interval_min = self.list_dps[i+1].price
                    filled_position = 1
                elif self.list_dps[i].percentile >= 80 and filled_position == 1:
                    down_interval_max = self.list_dps[i].price
                    filled_position = 2
                elif self.list_dps[i].percentile < 80 and filled_position == 2:
                    down_interval_min = self.list_dps[i+1].price
                    filled_position = 3
                    break

        elif self.density_direction == 'in':

            wrong_consecutives = 0
            filled_position = 0
            # Up Part
            for i in range(current_dp_index + 1, len(self.list_dps)): # up part

                if filled_position != 1:
                    j = i
                elif self.list_dps[i].percentile - self.list_dps[j].percentile > 30:
                    return
                elif self.list_dps[i].percentile - self.list_dps[j].percentile > 10:
                    wrong_consecutives += 1
                    if wrong_consecutives == 3:
                        return
                else:
                    j = i

                if self.list_dps[i].percentile >= 80 and filled_position == 1:
                    return
                
                if self.list_dps[i].percentile < 80 and filled_position == 0:
                    current_interval_max = self.list_dps[i-1].price
                    filled_position = 1
                elif self.list_dps[i].percentile <= 20 and filled_position == 1:
                    up_interval_min = self.list_dps[i].price
                    filled_position = 2
                elif self.list_dps[i].percentile > 20 and filled_position == 2:
                    up_interval_max = self.list_dps[i-1].price
                    filled_position = 3
                    break

            wrong_consecutives = 0
            filled_position = 0
            # Down Part
            for i in reversed(range(current_dp_index)): # down part

                if filled_position != 1:
                    j = i
                elif self.list_dps[i].percentile - self.list_dps[j].percentile > 30:
                    return
                elif self.list_dps[i].percentile - self.list_dps[j].percentile > 10:
                    wrong_consecutives += 1
                    if wrong_consecutives == 3:
                        return
                else:
                    j = i

                if self.list_dps[i].percentile >= 80 and filled_position == 1:
                    return
            
                if self.list_dps[i].percentile < 80 and filled_position == 0:
                    current_interval_min = self.list_dps[i+1].price
                    filled_position = 1
                elif self.list_dps[i].percentile <= 20 and filled_position == 1:
                    down_interval_max = self.list_dps[i].price
                    filled_position = 2
                elif self.list_dps[i].percentile > 20 and filled_position == 2:
                    down_interval_min = self.list_dps[i+1].price
                    filled_position = 3
                    break

        if up_interval_max == 0:
            self.up_interval_max = self.list_dps[-1].price
        else:
            self.up_interval_max = up_interval_max

        if up_interval_min == 0:
            self.up_interval_min = self.list_dps[-1].price
        else:
            self.up_interval_min = up_interval_min

        if current_interval_max == 0:
            self.current_interval_max = self.list_dps[-1].price
        else:
            self.current_interval_max = current_interval_max

        if current_interval_min == 0:
            self.current_interval_min = self.list_dps[0].price
        else:
            self.current_interval_min = current_interval_min

        if down_interval_max == 0:
            self.down_interval_max = self.list_dps[0].price
        else:
            self.down_interval_max = down_interval_max

        if down_interval_min == 0:
            self.down_interval_min = self.list_dps[0].price
        else:
            self.down_interval_min = down_interval_min

        self.in_position = True
        

    def all_max_value(self):
        return len(self.data)

    
    def max_value(self):
        return len(self.list_dps)


    def state_str(self):
        output = ""
        for dp in reversed(self.list_dps):
            output += f"{dp.state_str()}\n"
        if self.current_dp is not None:
            output += (
                f"in_position: {self.in_position}\n"
                f"density_direction: {self.density_direction}\n"
                f"{self.up_interval_max}\n"
                f"{self.up_interval_min}\n"
                f"{self.current_interval_max}\n"
                f"current_dp: {self.current_dp.state_str()}\n"
                f"{self.current_interval_min}\n"
                f"{self.down_interval_max}\n"
                f"{self.down_interval_min}\n"
            )
        return output


class DensityPoint:
    def __init__(self, price):
        self.price = price
        self.duration = 0
        self.value = 0
        self.percentile = 0

    def state_str(self):
        output = (
            f"'price': {self.price}, "
            f"'duration': {self.duration}, "
            f"'value': {self.value}, "
            f"'percentile': {self.percentile}"
        )
        return output