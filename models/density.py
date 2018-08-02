import gvars
from lib import core

class Density:
    def __init__(self, monitor):
        self.mtr = monitor
        self.data = []
        self.current_dict_dps = {}
        self.current_list_dps = []

        self.current_dp = None
        self.close_dps = []
        self.density_direction = None
        self.action = None # "BUY" | "SELL" | or None
        

    def price_change(self):
        #self.update_all_data()
        self.update_current_data()
        self.get_state('up')
        # self.prepare()


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


    def update_current_data(self):
        self.current_dict_dps = {}
        if len(self.mtr.data) <= 2:
            return
        price_data = self.mtr.data_since(7200)
        if price_data[-1].time - price_data[0].time < 7000:
            return
        price_data = price_data[0:-1] # remove last element (doesn't have a duration)
        for cdp in price_data:
            if cdp.price not in self.current_dict_dps:
                self.current_dict_dps[cdp.price] = DensityPoint(cdp.price)
            self.current_dict_dps[cdp.price].duration += cdp.duration

        list_dps = list(self.current_dict_dps.values())
        list_dps.sort(key=lambda dp: dp.duration, reverse = True)

        # Set value
        for index, dp in enumerate(list_dps):
            dp.value = index

        list_dps.sort(key=lambda dp: dp.price)

        # Set height
        for i in range(len(list_dps)):
            if i < 2:
                continue
            if list_dps[i-2].value < list_dps[i-1].value < list_dps[i].value:
                list_dps[i-1].height = gvars.HEIGHT['mid']
            elif list_dps[i-2].value > list_dps[i-1].value > list_dps[i].value:
                list_dps[i-1].height = gvars.HEIGHT['mid']
            elif list_dps[i-2].value < list_dps[i-1].value > list_dps[i].value:
                list_dps[i-1].height = gvars.HEIGHT['max']
            elif list_dps[i-2].value > list_dps[i-1].value < list_dps[i].value:
                list_dps[i-1].height = gvars.HEIGHT['min']

        # Set kintile
        kintile_nr = self.current_max_value() / 5.0
        for dp in list_dps:
            for i in range(1, 6):
                if i * kintile_nr >= dp.value:
                    dp.kintile = i
                    break
            if dp.kintile == 0: # Never assigned
                dp.kintile = 5

        self.current_list_dps = list_dps

        # +++++++++++++ Print ++++++++++++++++
        # for key in sorted(self.current_dict_dps.keys(), reverse=True):
        #     gvars.datalog_buffer[self.mtr.ticker] += f"{self.current_dict_dps[key].state_str()}\n"
        for dp in reversed(self.current_list_dps):
            gvars.datalog_buffer[self.mtr.ticker] += f"{dp.state_str()}\n"
        gvars.datalog_buffer[self.mtr.ticker] += "\n"


    # Need to work on this one
    def get_state(self, price_direction):
        self.current_dp = None
        self.close_dps = []
        self.density_direction = None

        current_price_index = core.index(lambda dp: dp.price == self.mtr.last_price(), self.current_list_dps)
        if current_price_index is None:
            return # should NOT return. Is touching new ranges. NEED TO CONSIDER THIS CASE! working here!
            pass
        if price_direction == 'up':
            for i in range(current_price_index + 1, len(self.current_list_dps)): # up part
                if self.current_list_dps[i].height == gvars.HEIGHT['max']:
                    self.close_dps.append(self.current_list_dps[i])
                elif self.current_list_dps[i].height == gvars.HEIGHT['min']:
                    self.close_dps.append(self.current_list_dps[i])
            if len(self.close_dps) > 0:
                if self.close_dps[0].height == gvars.HEIGHT['max']:
                    self.density_direction = 'out'
                else:
                    self.density_direction = 'in'

            # for i in reversed(range(current_price_index)): # down part
            #     pass
        else:
            for i in reversed(range(current_price_index)): # down part
                pass
        

    # def prepare(self):
    #     cdp = self.mtr.data[-3:]
    #     if cdp[-3].price < cdp[-2].price < cdp[-1].price:
    #         # uptrend
    #         if self.current_value(cdp[-3].price) < self.current_value(cdp[-2].price) < self.current_value(cdp[-1].price):
    #             # going out of the range
    #             current_price_index = core.index(lambda dp: dp.price == cdp[-1].price, self.current_list_dps)
    #             for i in range(current_price_index, len(self.current_list_dps)):
    #                 # do up part
    #                 if self.current_list_dps[i].height == gvars.HEIGHT['max']:
    #                     #do something
    #                     pass
    #             for i in reversed(range(current_price_index+1)):
    #                 # do down part
    #                 pass

    #             # up_part = self.current_list_dps[current_price_index:]
    #             # down_part = self.current_list_dps[:current_price_index+1]

    #             pass
    #         elif self.current_value(cdp[-3].price) > self.current_value(cdp[-2].price) > self.current_value(cdp[-1].price):
    #             # going into the range
    #             pass
    #         # buy (or not)
    #     elif cdp[-1].price < cdp[-2].price < cdp[-3].price:
    #         # downtrend
    #         if self.current_value(cdp[-3].price) < self.current_value(cdp[-2].price) < self.current_value(cdp[-1].price):
    #             # going out of the range
    #             pass
    #         elif self.current_value(cdp[-3].price) > self.current_value(cdp[-2].price) > self.current_value(cdp[-1].price):
    #             # going into the range
    #             pass
    #         # sell (or not)
        

    def all_max_value(self):
        return len(self.data)

    def current_max_value(self):
        return len(self.current_dict_dps)

    def current_value(self, price):
        if price in self.current_dict_dps:
            return self.current_dict_dps[price].value
        else:
            return self.current_max_value() + 1


class DensityPoint:
    def __init__(self, price=0):
        self.price = price
        self.duration = 0
        self.value = 0
        self.height = gvars.HEIGHT['mid']
        self.kintile = 0

    def state_str(self):
        return f"'price': {self.price}, 'duration': {self.duration}, 'value': {self.value}, 'height': {self.height}, 'kintile': {self.kintile}"