import gvars
from lib import core

class Density:
    def __init__(self, monitor):
        self.mtr = monitor
        self.data = []
        self.current_dps = None
        

    def price_change(self):
        self.update_all_data()
        self.update_current_data()


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
        self.current_dps = {}
        if len(self.mtr.data) <= 2:
            return
        price_data = self.mtr.data_since(2100)
        if price_data[-1].time - price_data[0].time < 1800:
            return
        price_data = price_data[0:-1] # remove last element (doesn't have a duration)
        for cdp in price_data:
            if cdp.price not in self.current_dps:
                self.current_dps[cdp.price] = DensityPoint(cdp.price)
            self.current_dps[cdp.price].duration += cdp.duration

        list_dps = list(self.current_dps.values())
        list_dps.sort(key=lambda dp: dp.duration, reverse = True)

        for index, dp in enumerate(list_dps):
            dp.value = index

        # Print
        for key in sorted(self.current_dps.keys(), reverse=True):
            gvars.datalog_buffer[self.mtr.ticker] += f"{self.current_dps[key].state_str()}\n"
        gvars.datalog_buffer[self.mtr.ticker] += "\n"
        

    def is_a_transaction(self):
        last_cdps = self.mtr.data[-3:]
        if last_cdps[0].price < last_cdps[1].price < last_cdps[2].price:
            # uptrend
            if self.current_value(last_cdps[0].price) < self.current_value(last_cdps[1].price) < self.current_value(last_cdps[2].price):
                # going out of the range
                pass
            elif self.current_value(last_cdps[0].price) > self.current_value(last_cdps[1].price) > self.current_value(last_cdps[2].price):
                # going into the range
                pass
            # buy (or not)
        elif last_cdps[2].price < last_cdps[1].price < last_cdps[0].price:
            # downtrend
            if self.current_value(last_cdps[0].price) < self.current_value(last_cdps[1].price) < self.current_value(last_cdps[2].price):
                # going out of the range
                pass
            elif self.current_value(last_cdps[0].price) > self.current_value(last_cdps[1].price) > self.current_value(last_cdps[2].price):
                # going into the range
                pass
            # sell (or not)
        

    def all_max_value(self):
        return len(self.data)

    def current_max_value(self):
        return len(self.current_data)

    def current_value(self, price):
        if price in self.current_dps:
            return self.current_dps[price].value
        else:
            return self.current_max_value()


class DensityPoint:
    def __init__(self, price=0):
        self.price = price
        self.duration = 0
        self.value = 0

    def state_str(self):
        return f"'price': {self.price}, 'duration': {self.duration}, 'value': {self.value}"