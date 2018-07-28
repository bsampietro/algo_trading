import gvars

class Breaking:
    def __init__(self, direction, chart_data):
        self.direction = direction
        self.cd = chart_data

        self.breaking_price_changes = 0

        self.min_breaking_price = self.cd.last_price()
        self.max_breaking_price = self.cd.last_price()
        self.breaking_time = self.cd.last_time()

        self.duration_ok = False
        self.mid_price = 0


    def price_changed(self):
        self.duration_ok = False
        self.mid_price = 0

        self.breaking_price_changes += 1

        if self.direction == "up":

            ## Time up down system
            if self.cd.last_price() < self.min_breaking_price:
                self.min_breaking_price = self.cd.last_price()
                self.breaking_time = self.cd.last_time()
                self.breaking_price_changes = 0
            elif self.cd.last_price() > self.max_breaking_price:
                self.max_breaking_price = self.cd.last_price()
                self.breaking_time = self.cd.last_time()

            self.mid_price = round((self.max_breaking_price + self.min_breaking_price) / 2.0, 2)
            time_up_down = self.cd.time_up_down_since(self.breaking_time, self.mid_price)

            if time_up_down[2] == 0:
                self.duration_ok = True
            else:
                if (float(time_up_down[0] + time_up_down[1]) / time_up_down[2]) > self.cd.prm.up_down_ratio:
                    self.duration_ok = True

        else: # "down"

            ## Time up down system
            if self.cd.last_price() < self.min_breaking_price:
                self.min_breaking_price = self.cd.last_price()
                self.breaking_time = self.cd.last_time()
            elif self.cd.last_price() > self.max_breaking_price:
                self.max_breaking_price = self.cd.last_price()
                self.breaking_time = self.cd.last_time()
                self.breaking_price_changes = 0

            self.mid_price = round((self.max_breaking_price + self.min_breaking_price) / 2.0, 2)
            time_up_down = self.cd.time_up_down_since(self.breaking_time, self.mid_price)

            if time_up_down[0] == 0:
                self.duration_ok = True
            else:
                if (float(time_up_down[1] + time_up_down[2]) / time_up_down[0]) > self.cd.prm.up_down_ratio:
                    self.duration_ok = True

        
        gvars.datalog_buffer[self.cd.ticker] += ("1st: Inside decision methods:\n")
        gvars.datalog_buffer[self.cd.ticker] += (f"mid_price: {self.mid_price}\n")
        gvars.datalog_buffer[self.cd.ticker] += (f"time_up_down: {time_up_down}\n")
        gvars.datalog_buffer[self.cd.ticker] += (f"duration_ok: {self.duration_ok}\n\n")


    def state_str(self):
        output = (
            f"BREAKING {self.direction}:\n"
            f"breaking_price_changes: {self.breaking_price_changes}\n"
            f"min_breaking_price: {self.min_breaking_price}\n"
            f"max_breaking_price: {self.max_breaking_price}\n"
            f"breaking_time: {self.breaking_time}\n"
        )
        return output