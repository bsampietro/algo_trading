import gvars
from lib import core

class Density:
    def __init__(self, monitor):
        self.mtr = monitor
        self.data = []
        self.dict_dps = {}
        self.list_dps = []

        self.current_dp = None
        self.density_direction = ''

        self.initialize_interval_variables()


    def initialize_interval_variables(self):
        self.up_interval_max = 0
        self.up_interval_min = 0
        self.current_interval_max = 0
        self.current_interval_min = 0
        self.down_interval_max = 0
        self.down_interval_min = 0
        

    def price_change(self):
        #self.update_all_data()
        self.update_dps()
        self.get_state()


    def update_all_data(self):
        if len(self.mtr.data) <= 2:
            return
        stl_cdp = self.mtr.data[-2]
        dp = core.find(lambda dp: dp.price == stl_cdp.price, self.data)
        if dp is None:
            dp = DensityPoint(stl_cdp.price)
            self.data.append(dp)
        dp.duration += stl_cdp.duration
        self.data.sort(key=lambda dp: dp.duration, reverse = True)

        for index, dp in enumerate(self.data):
            dp.value = index
        
        # Print by duration
        # for dp in self.data:
        #     gvars.datalog_buffer[self.mtr.ticker] += f"{dp.state_str()}\n"
        # gvars.datalog_buffer[self.mtr.ticker] += "---\n"

        self.data.sort(key=lambda dp: dp.price)
        
        # Print by price
        # for dp in self.data:
        #     gvars.datalog_buffer[self.mtr.ticker] += f"{dp.state_str()}\n"


    def update_dps(self):
        self.dict_dps = {}
        if len(self.mtr.data) <= 2:
            return
        price_data = self.mtr.data_since(self.mtr.prm.primary_density_back_time)
        if price_data[-1].time - price_data[0].time < self.mtr.prm.primary_density_back_time - 200:
            return
        # price_data = price_data[0:-1] # remove last element (doesn't have a duration)
        for cdp in price_data:
            if cdp.price not in self.dict_dps:
                self.dict_dps[cdp.price] = DensityPoint(cdp.price)
            self.dict_dps[cdp.price].duration += cdp.duration

        list_dps = list(self.dict_dps.values())
        list_dps.sort(key=lambda dp: dp.duration, reverse = True)

        # Set value
        for index, dp in enumerate(list_dps):
            dp.value = index
        
        # Set percentile
        percentile_coefficient = 100.0 / (self.max_value() - 1)
        for dp in list_dps:
            dp.percentile = round(dp.value * percentile_coefficient)

        list_dps.sort(key=lambda dp: dp.price)
        
        self.list_dps = list_dps

        # +++++++++++++ Print ++++++++++++++++
        for dp in reversed(self.list_dps):
            gvars.datalog_buffer[self.mtr.ticker] += f"{dp.state_str()}\n"


    # Need to work on this one
    def get_state(self):
        self.current_dp = None

        current_dp_index = core.index(lambda dp: dp.price == self.mtr.last_price(), self.list_dps)
        if current_dp_index is None:
            print(self.mtr.last_price())
            # Should fix the minimum price data before working here
            return
        self.current_dp = self.list_dps[current_dp_index]

        if self.current_dp.percentile <= 20:
            self.density_direction = 'out'
        elif self.current_dp.percentile >= 80:
            self.density_direction = 'in'
        else:
            return

        # Set interval variables

        self.initialize_interval_variables()

        if self.density_direction == 'out':

            filled = 0
            # Up Part
            for i in range(current_dp_index + 1, len(self.list_dps)): # up part
                
                if self.list_dps[i].percentile > 20 and filled == 0:
                    self.current_interval_max = self.list_dps[i-1].price
                    filled = 1
                elif self.list_dps[i].percentile <= 20 and filled == 1:
                    # Not smooth case
                    self.initialize_interval_variables()
                    return
                elif self.list_dps[i].percentile >= 80 and filled == 1:
                    self.up_interval_min = self.list_dps[i].price
                    filled = 2
                elif self.list_dps[i].percentile < 80 and filled == 2:
                    self.up_interval_max = self.list_dps[i-1].price
                    filled = 3
                    break

            filled = 0
            # Down Part
            for i in reversed(range(current_dp_index)): # down part
            
                if self.list_dps[i].percentile > 20 and filled == 0:
                    self.current_interval_min = self.list_dps[i+1].price
                    filled = 1
                elif self.list_dps[i].percentile <= 20 and filled == 1:
                    # Not smooth case
                    self.initialize_interval_variables()
                    return
                elif self.list_dps[i].percentile >= 80 and filled == 1:
                    self.down_interval_max = self.list_dps[i].price
                    filled = 2
                elif self.list_dps[i].percentile < 80 and filled == 2:
                    self.down_interval_min = self.list_dps[i+1].price
                    filled = 3
                    break

        elif self.density_direction == 'in':

            filled = 0
            # Up Part
            for i in range(current_dp_index + 1, len(self.list_dps)): # up part
                
                if self.list_dps[i].percentile < 80 and filled == 0:
                    self.current_interval_max = self.list_dps[i-1].price
                    filled = 1
                elif self.list_dps[i].percentile >= 80 and filled == 1:
                    # Not smooth case
                    self.initialize_interval_variables()
                    return
                elif self.list_dps[i].percentile <= 20 and filled == 1:
                    self.up_interval_min = self.list_dps[i].price
                    filled = 2
                elif self.list_dps[i].percentile > 20 and filled == 2:
                    self.up_interval_max = self.list_dps[i-1].price
                    filled = 3
                    break

            filled = 0
            # Down Part
            for i in reversed(range(current_dp_index)): # down part
            
                if self.list_dps[i].percentile < 80 and filled == 0:
                    self.current_interval_min = self.list_dps[i+1].price
                    filled = 1
                elif self.list_dps[i].percentile >= 80 and filled == 1:
                    # Not smooth case
                    self.initialize_interval_variables()
                    return
                elif self.list_dps[i].percentile <= 20 and filled == 1:
                    self.down_interval_max = self.list_dps[i].price
                    filled = 2
                elif self.list_dps[i].percentile > 20 and filled == 2:
                    self.down_interval_min = self.list_dps[i+1].price
                    filled = 3
                    break

        if self.up_interval_max == 0:
            self.up_interval_max = self.list_dps[-1].price
        if self.up_interval_min == 0:
            self.up_interval_min = self.list_dps[-1].price
        if self.current_interval_max == 0:
            self.current_interval_max = self.list_dps[-1].price
        if self.current_interval_min == 0:
            self.current_interval_min = self.list_dps[0].price
        if self.down_interval_max == 0:
            self.down_interval_max = self.list_dps[0].price
        if self.down_interval_min == 0:
            self.down_interval_min = self.list_dps[0].price

        gvars.datalog_buffer[self.mtr.ticker] += f"{self.up_interval_max}\n"
        gvars.datalog_buffer[self.mtr.ticker] += f"{self.up_interval_min}\n"
        gvars.datalog_buffer[self.mtr.ticker] += f"{self.current_interval_max}\n"
        gvars.datalog_buffer[self.mtr.ticker] += f"current_dp: {self.current_dp.state_str()}\n"
        gvars.datalog_buffer[self.mtr.ticker] += f"{self.current_interval_min}\n"
        gvars.datalog_buffer[self.mtr.ticker] += f"{self.down_interval_max}\n"
        gvars.datalog_buffer[self.mtr.ticker] += f"{self.down_interval_min}\n"
        

    def all_max_value(self):
        return len(self.data)

    def max_value(self):
        return len(self.dict_dps)

    def current_value(self, price):
        if price in self.dict_dps:
            return self.dict_dps[price].value
        else:
            return self.max_value() + 1


class DensityPoint:
    def __init__(self, price=0):
        self.price = price
        self.duration = 0
        self.value = 0
        self.height = gvars.HEIGHT['mid']
        self.tritile = 0
        self.percentile = 0

    def state_str(self):
        output = (
            f"'price': {self.price}, "
            f"'duration': {self.duration}, "
            f"'value': {self.value}, "
            f"'percentile': {self.percentile}"
        )
        return output