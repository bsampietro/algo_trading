import gvars

class Breaking:
    def __init__(self, monitor):
        self.m = monitor
        self.price_changes_list = []
        self.initialize_state()


    def price_change(self):
        self.update()


    def initialize_state(self):
        self.direction = 0
        self.min_price = None # type: float
        self.max_price = None # type: float
        self.start_time = None # type: int
        self.price_changes = 0
        self.density_data = None


    def update(self):
        if not self.m.density.values_set():
            return
        if self.direction == 0:
            if self.m.density.current_interval_max < self.m.last_price() < self.m.density.up_interval_min:
                self.direction = 1
                self.min_price = self.max_price = self.m.last_price()
                self.start_time = self.m.last_time()
                self.density_data = self.m.density.get_data(self.direction)
            elif self.m.density.current_interval_min > self.m.last_price() > self.m.density.down_interval_max:
                self.direction = -1
                self.min_price = self.max_price = self.m.last_price()
                self.start_time = self.m.last_time()
                self.density_data = self.m.density.get_data(self.direction)
        else:
            self.price_changes += 1
            
            density_interval_mid_price = self.m.mid_price(
                self.density_data.current_interval_max, self.density_data.current_interval_min)
            
            if self.direction == 1:
                if density_interval_mid_price <= self.m.last_price() < self.density_data.up_interval_min:
                    if self.m.last_price() < self.min_price:
                        self.min_price = self.m.last_price()
                        self.start_time = self.m.last_time()
                        self.price_changes = 0
                    elif self.m.last_price() > self.max_price:
                        self.max_price = self.m.last_price()
                        self.start_time = self.m.last_time()
                else:
                    self.add_to_price_changes_list(self.price_changes)
                    self.initialize_state()
            elif self.direction == -1:
                if density_interval_mid_price >= self.m.last_price() > self.density_data.down_interval_max:
                    if self.m.last_price() < self.min_price:
                        self.min_price = self.m.last_price()
                        self.start_time = self.m.last_time()
                    elif self.m.last_price() > self.max_price:
                        self.max_price = self.m.last_price()
                        self.start_time = self.m.last_time()
                        self.price_changes = 0
                else:
                    self.add_to_price_changes_list(self.price_changes)
                    self.initialize_state()

            self.m.datalog_buffer += (f"    breaking.update.density_interval_mid_price: {density_interval_mid_price}\n")


    def duration_ok(self):
        duration_ok = False
        mid_price = self.m.mid_price(self.max_price, self.min_price)
        time_up_down = self.m.time_up_down_since(self.start_time, mid_price)

        if self.direction == 1:
            if time_up_down[2] == 0:
                duration_ok = True
            else:
                if (float(time_up_down[0] + time_up_down[1]) / time_up_down[2]) > self.m.prm.breaking_up_down_ratio:
                    duration_ok = True
        elif self.direction == -1:
            if time_up_down[0] == 0:
                duration_ok = True
            else:
                if (float(time_up_down[1] + time_up_down[2]) / time_up_down[0]) > self.m.prm.breaking_up_down_ratio:
                    duration_ok = True

        self.m.datalog_buffer += (f"    breaking.duration_ok.mid_price: {mid_price}\n")
        self.m.datalog_buffer += (f"    breaking.duration_ok.time_up_down: {time_up_down}\n")
        self.m.datalog_buffer += (f"    breaking.duration_ok.duration_ok: {duration_ok}\n")

        return duration_ok


    def add_to_price_changes_list(self, price_changes):
        while len(self.price_changes_list) > self.m.prm.max_breaking_price_changes_list:
            self.price_changes_list.pop(0)
        self.price_changes_list.append(price_changes)
        self.price_changes_list.sort()


    def in_range(self):
        return self.direction != 0


    def state_str(self):
        output = ""
        if self.direction != 0:
            output += (
                "  BREAKING {}:\n"
                "    min_price: {:.{price_precision}f}\n"
                "    max_price: {:.{price_precision}f}\n"
                "    start_time: {:.4f}\n"
                "    price_changes: {}\n"
            ).format(self.direction, self.min_price, self.max_price, self.start_time, 
                self.price_changes, price_precision = self.m.prm.price_precision)
            if len(self.price_changes_list) > 0:
                output += f"    price_changes_list: {str(self.price_changes_list)}\n"
            output += self.density_data.state_str(self.m.prm.price_precision)
        return output