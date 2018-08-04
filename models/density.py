import gvars
from lib import core

class Density:
    def __init__(self, monitor):
        self.mtr = monitor
        self.data = []
        self.dict_dps = {}
        self.list_dps = []

        self.current_dp = None
        self.up_dps = []
        self.down_dps = []
        self.density_direction = None
        self.action = None # "BUY" | "SELL" | or None
        

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
        price_data = price_data[0:-1] # remove last element (doesn't have a duration)
        for cdp in price_data:
            if cdp.price not in self.dict_dps:
                self.dict_dps[cdp.price] = DensityPoint(cdp.price)
            self.dict_dps[cdp.price].duration += cdp.duration

        list_dps = list(self.dict_dps.values())
        list_dps.sort(key=lambda dp: dp.duration, reverse = True)

        # Set value
        for index, dp in enumerate(list_dps):
            dp.value = index
        
        # Set "iles"
        tritile_coefficient = 3.0 / (self.max_value() - 1)
        percentile_coefficient = 100.0 / (self.max_value() - 1)
        for dp in list_dps:
            dp.tritile = round(dp.value * tritile_coefficient)
            dp.percentile = round(dp.value * percentile_coefficient)

        list_dps.sort(key=lambda dp: dp.price)

        # Set height
        trend = 1
        for i in range(len(list_dps)):
            if i == 0:
                list_dps[0].height = gvars.HEIGHT['mid']
            else:
                if list_dps[i-1].tritile < list_dps[i].tritile:
                    if trend == -1:
                        list_dps[i-1].height = gvars.HEIGHT['min']
                        for j in range(2, i):
                            if list_dps[i-j].tritile == list_dps[i-1].tritile:
                                list_dps[i-j].height = gvars.HEIGHT['min']
                            else:
                                break
                        trend = 1
                elif list_dps[i-1].tritile > list_dps[i].tritile:
                    if trend == 1:
                        list_dps[i-1].height = gvars.HEIGHT['max']
                        for j in range(2, i):
                            if list_dps[i-j].tritile == list_dps[i-1].tritile:
                                list_dps[i-j].height = gvars.HEIGHT['max']
                            else:
                                break
                        trend = -1
        
        self.list_dps = list_dps

        # +++++++++++++ Print ++++++++++++++++
        for dp in reversed(self.list_dps):
            gvars.datalog_buffer[self.mtr.ticker] += f"{dp.state_str()}\n"


    # Need to work on this one
    def get_state(self):
        self.current_dp = None
        self.up_dps = []
        self.down_dps = []
        self.density_direction = None

        current_dp_index = core.index(lambda dp: dp.price == self.mtr.last_price(), self.list_dps)
        if current_dp_index is None:
            return # should NOT return. Is touching new ranges. NEED TO CONSIDER THIS CASE! working here!
            pass
        else:
            self.current_dp = self.list_dps[current_dp_index]

        # Up Part
        for i in range(current_dp_index + 1, len(self.list_dps)): # up part
            if self.list_dps[i].height == gvars.HEIGHT['mid']:
                continue
            if len(self.up_dps) > 0:
                if ((self.list_dps[i].height == gvars.HEIGHT['max'] and 
                        self.up_dps[-1].height == gvars.HEIGHT['max']) or
                            (self.list_dps[i].height == gvars.HEIGHT['min'] and 
                                self.up_dps[-1].height == gvars.HEIGHT['min'])):
                    self.up_dps[-1] = self.list_dps[i]
                    continue
            self.up_dps.append(self.list_dps[i])

        if len(self.up_dps) > 0:
            if self.up_dps[0].height == gvars.HEIGHT['max']:
                self.density_direction = 'out'
            else:
                self.density_direction = 'in'

        # Down Part
        for i in reversed(range(current_dp_index)): # down part
            if self.list_dps[i].height == gvars.HEIGHT['mid']:
                continue
            if len(self.down_dps) > 0:
                if ((self.list_dps[i].height == gvars.HEIGHT['max'] and 
                        self.down_dps[-1].height == gvars.HEIGHT['max']) or
                            (self.list_dps[i].height == gvars.HEIGHT['min'] and 
                                self.down_dps[-1].height == gvars.HEIGHT['min'])):
                    self.down_dps[-1] = self.list_dps[i]
                    continue
            self.down_dps.append(self.list_dps[i])

        if len(self.down_dps) > 0:
            if self.down_dps[0].height == gvars.HEIGHT['max']:
                self.density_direction = 'out'
            else:
                self.density_direction = 'in'

        # +++++++++++++ Print ++++++++++++++++
        gvars.datalog_buffer[self.mtr.ticker] += f"Up dps\n"
        for dp in reversed(self.up_dps):
            gvars.datalog_buffer[self.mtr.ticker] += f"{dp.state_str()}\n"

        gvars.datalog_buffer[self.mtr.ticker] += f"Down dps\n"
        for dp in self.down_dps:
            gvars.datalog_buffer[self.mtr.ticker] += f"{dp.state_str()}\n"
        

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
            f"'height': {self.height}, "
            f"'tritile': {self.tritile}, "
            f"'percentile': {self.percentile}"
        )
        return output