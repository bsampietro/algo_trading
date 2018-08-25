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
        self.min_price = 0
        self.max_price = 0
        self.start_time = 0
        self.price_changes = 0


    def update(self):
        # Direction
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

        self.price_changes += 1
        
        density_interval_mid_price = round((density.current_interval_max + density.current_interval_min) / 2.0, 2)
        if self.direction == 1:
            if density_interval_mid_price <= self.m.last_price() < density.up_interval_min:
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
            if density_interval_mid_price >= self.m.last_price() > density.down_interval_max:
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

        gvars.datalog_buffer[self.m.ticker] += (f"    density_interval_mid_price: {density_interval_mid_price}\n")


    def duration_ok(self):
        duration_ok = False
        mid_price = round((self.max_price + self.min_price) / 2.0, 2)
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

        gvars.datalog_buffer[self.m.ticker] += (f"    mid_price: {mid_price}\n")
        gvars.datalog_buffer[self.m.ticker] += (f"    time_up_down: {time_up_down}\n")
        gvars.datalog_buffer[self.m.ticker] += (f"    duration_ok: {duration_ok}\n")

        return duration_ok


    def price_changes_ok(self):
        price_changes_ok = False
        
        threshold = self.m.prm.min_breaking_price_changes
        # Uncomment this to start using the past breaking price changes
        # if len(self.price_changes_list) > self.m.prm.max_breaking_price_changes_list - 5:
        #     threshold = round(max(self.price_changes_list) * 0.75)
        # if threshold > self.m.prm.min_breaking_price_changes:
        #     threshold = self.m.prm.min_breaking_price_changes
        
        if self.price_changes >= threshold:
            price_changes_ok = True
        
        gvars.datalog_buffer[self.m.ticker] += (f"    threshold: {threshold}\n")
        gvars.datalog_buffer[self.m.ticker] += (f"    price_changes_ok: {price_changes_ok}\n")
        
        return price_changes_ok


    def add_to_price_changes_list(self, price_changes):
        while len(self.price_changes_list) > self.m.prm.max_breaking_price_changes_list:
            self.price_changes_list.pop(0)
        self.price_changes_list.append(price_changes)


    def state_str(self):
        output = ""
        if self.direction != 0:
            output += (
                f"  BREAKING {self.direction}:\n"
                f"    min_price: {self.min_price}\n"
                f"    max_price: {self.max_price}\n"
                f"    start_time: {self.start_time}\n"
                f"    price_changes: {self.price_changes}\n"
            )
            if len(self.price_changes_list) > 0:
                output += f"    price_changes_list: {str(self.price_changes_list)}\n"
        return output