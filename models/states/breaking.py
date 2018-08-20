import gvars

class Breaking:
    def __init__(self, monitor):
        self.m = monitor
        self.initialize_state()


    def price_change(self):
        self.update()


    def initialize_state(self):
        self.direction = 0

        self.min_price = 0
        self.max_price = 0
        
        self.start_time = 0

        self.price_changes = 0
        self.duration_ok = False


    def update(self):
        density = self.m.density
        if self.direction == 0:
            if density.current_interval_max < self.m.last_price() < density.up_interval_min:
                self.direction = 1
                self.min_price = self.max_price = self.m.last_price()
                self.start_time = self.m.last_time()
            elif density.current_interval_min > self.m.last_price() > density.down_interval_max:
                self.direction = -1
                self.min_price = self.max_price = self.m.last_price()
                self.start_time = self.m.last_time()
            return

        self.duration_ok = False
        self.price_changes += 1
        
        current_interval_mid_price = round((density.current_interval_max + density.current_interval_min) / 2.0, 2)
        
        mid_price = round((self.max_price + self.min_price) / 2.0, 2)
        time_up_down = self.m.time_up_down_since(self.start_time, mid_price)

        if self.direction == 1:
            if current_interval_mid_price < self.m.last_price() < density.up_interval_min:
                if self.m.last_price() < self.min_price:
                    self.min_price = self.m.last_price()
                    self.start_time = self.m.last_time()
                    self.price_changes = 0
                elif self.m.last_price() > self.max_price:
                    self.max_price = self.m.last_price()
                    self.start_time = self.m.last_time()

                if time_up_down[2] == 0:
                    self.duration_ok = True
                else:
                    if (float(time_up_down[0] + time_up_down[1]) / time_up_down[2]) > self.m.prm.breaking_up_down_ratio:
                        self.duration_ok = True
            else:
                self.initialize_state()
        elif self.direction == -1:
            if current_interval_mid_price > self.m.last_price() > density.down_interval_max:
                if self.m.last_price() < self.min_price:
                    self.min_price = self.m.last_price()
                    self.start_time = self.m.last_time()
                elif self.m.last_price() > self.max_price:
                    self.max_price = self.m.last_price()
                    self.start_time = self.m.last_time()
                    self.price_changes = 0

                if time_up_down[0] == 0:
                    self.duration_ok = True
                else:
                    if (float(time_up_down[1] + time_up_down[2]) / time_up_down[0]) > self.m.prm.breaking_up_down_ratio:
                        self.duration_ok = True
            else:
                self.initialize_state()

        gvars.datalog_buffer[self.m.ticker] += (f"current_interval_mid_price: {current_interval_mid_price}\n")
        gvars.datalog_buffer[self.m.ticker] += (f"mid_price: {mid_price}\n")
        gvars.datalog_buffer[self.m.ticker] += (f"time_up_down: {time_up_down}\n")


    def state_str(self):
        output = ""
        if self.direction != 0:
            output += (
                f"BREAKING {self.direction}:\n"
                f"min_price: {self.min_price}\n"
                f"max_price: {self.max_price}\n"
                f"start_time: {self.start_time}\n"
                f"price_changes: {self.price_changes}\n"
                f"duration_ok: {self.duration_ok}\n"
            )
        return output