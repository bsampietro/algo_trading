import gvars

class Breaking:
    def __init__(self, monitor):
        self.m = monitor

        self.direction = 0
        self.min_breaking_price = 0
        self.max_breaking_price = 0
        self.breaking_time = 0

        self.breaking_price_changes = 0
        self.duration_ok = False
        self.mid_price = 0


    def price_change(self):
        if self.m.density.in_position:
            self.reset_state()
        self.update()


    def reset_state(self):
        self.direction = 0
        self.min_breaking_price = 0
        self.max_breaking_price = 0
        self.breaking_time = 0

        self.breaking_price_changes = 0
        self.duration_ok = False
        self.mid_price = 0


    def update(self):
        density = self.m.density
        if self.direction == 0:
            if density.current_interval_max < self.m.last_price() < density.up_interval_min:
                self.direction = 1
                self.min_breaking_price = self.max_breaking_price = self.m.last_price()
                self.breaking_time = self.m.last_time()
            elif density.current_interval_min > self.m.last_price() > density.down_interval_max:
                self.direction = -1
                self.min_breaking_price = self.max_breaking_price = self.m.last_price()
                self.breaking_time = self.m.last_time()
            return
        mid_price = round((density.current_interval_max + density.current_interval_min) / 2.0, 2)
        if self.direction == 1:
            if self.m.last_price() < mid_price or self.m.last_price() > density.up_interval_min:
                self.reset_state()
            else:
                self.get_state()
        elif self.direction == -1:
            if self.m.last_price() > mid_price or self.m.last_price() < density.down_interval_max:
                self.reset_state()
            else:
                self.get_state()


    def get_state(self):
        self.duration_ok = False
        self.mid_price = 0

        self.breaking_price_changes += 1

        if self.direction == 1: # Up

            ## Time up down system
            if self.m.last_price() < self.min_breaking_price:
                self.min_breaking_price = self.m.last_price()
                self.breaking_time = self.m.last_time()
                self.breaking_price_changes = 0
            elif self.m.last_price() > self.max_breaking_price:
                self.max_breaking_price = self.m.last_price()
                self.breaking_time = self.m.last_time()

            self.mid_price = round((self.max_breaking_price + self.min_breaking_price) / 2.0, 2)
            time_up_down = self.m.time_up_down_since(self.breaking_time, self.mid_price)

            if time_up_down[2] == 0:
                self.duration_ok = True
            else:
                if (float(time_up_down[0] + time_up_down[1]) / time_up_down[2]) > self.m.prm.breaking_up_down_ratio:
                    self.duration_ok = True

        else: # Down

            ## Time up down system
            if self.m.last_price() < self.min_breaking_price:
                self.min_breaking_price = self.m.last_price()
                self.breaking_time = self.m.last_time()
            elif self.m.last_price() > self.max_breaking_price:
                self.max_breaking_price = self.m.last_price()
                self.breaking_time = self.m.last_time()
                self.breaking_price_changes = 0

            self.mid_price = round((self.max_breaking_price + self.min_breaking_price) / 2.0, 2)
            time_up_down = self.m.time_up_down_since(self.breaking_time, self.mid_price)

            if time_up_down[0] == 0:
                self.duration_ok = True
            else:
                if (float(time_up_down[1] + time_up_down[2]) / time_up_down[0]) > self.m.prm.breaking_up_down_ratio:
                    self.duration_ok = True

        
        gvars.datalog_buffer[self.m.ticker] += ("1st: Inside breaking and price changed:\n")
        gvars.datalog_buffer[self.m.ticker] += (f"mid_price: {self.mid_price}\n")
        gvars.datalog_buffer[self.m.ticker] += (f"time_up_down: {time_up_down}\n")
        gvars.datalog_buffer[self.m.ticker] += (f"duration_ok: {self.duration_ok}\n\n")


    def state_str(self):
        output = (
            f"BREAKING {self.direction}:\n"
            f"breaking_price_changes: {self.breaking_price_changes}\n"
            f"min_breaking_price: {self.min_breaking_price}\n"
            f"max_breaking_price: {self.max_breaking_price}\n"
            f"breaking_time: {self.breaking_time}\n"
        )
        return output