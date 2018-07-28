import gvars

CONTRACT_NR = 1

class Position:
    def __init__(self, chart_data, remote):
        self.cd = chart_data
        self.remote = remote

        self.last_order_price = 0
        self.last_order_time = 0
        self.last_action = "" # "BUY", "SELL", "CLOSE", "CANCEL" # Only used in load mode
        
        self.pnl = 0
        self.nr_of_trades = 0

        # set by IB
        self.position = 0
        # set manually and by IB
        self.active_order_id = None
        


    def price_change(self):
        # check for more than allowed positions
        self.security_check()
        if not self.remote.live_mode:
            if self.last_action == "BUY":
                if self.cd.last_price() <= self.last_order_price:
                    self.order_change(self.active_order_id, "Filled", CONTRACT_NR)
            elif self.last_action == "SELL":
                if self.cd.last_price() >= self.last_order_price:
                    self.order_change(self.active_order_id, "Filled", -CONTRACT_NR)

    def buy(self, price):
        if self.active_order('local'):
            return # Means internally already called buy or sell
        self.last_order_price = price
        self.last_order_time = self.cd.last_time()
        self.active_order_id = -1
        self.last_action = "BUY"

        # if self.remote.live_mode:
        #     self.remote.place_order(self, "BUY", CONTRACT_NR, price, self.active_order_id)

        gvars.datalog_buffer[self.cd.ticker] += (f"3rd: Decision:\n")
        gvars.datalog_buffer[self.cd.ticker] += (f"Order to buy at {price}\n")
        gvars.datalog_buffer[self.cd.ticker] += ("\n\n\n")


    def sell(self, price):
        if self.active_order('local'):
            return # Means internally already called buy or sell
        self.last_order_price = price
        self.last_order_time = self.cd.last_time()
        self.active_order_id = -1
        self.last_action = "SELL"

        # if self.remote.live_mode:
        #     self.remote.place_order(self, "SELL", CONTRACT_NR, price, self.active_order_id)

        gvars.datalog_buffer[self.cd.ticker] += (f"3rd: Decision:\n")
        gvars.datalog_buffer[self.cd.ticker] += (f"Order to sell at {price}\n")
        gvars.datalog_buffer[self.cd.ticker] += ("\n\n\n")


    def close(self):
        if self.active_order():
            return

        if self.position == 0:
            return

        self.last_action = "CLOSE"
        if self.position == CONTRACT_NR:
            # self.remote.place_order(self, "SELL", CONTRACT_NR)
            self.pnl += self.cd.last_price() - self.last_order_price
        elif self.position == -CONTRACT_NR:
            # self.remote.place_order(self, "BUY", CONTRACT_NR)
            self.pnl += self.last_order_price - self.cd.last_price()

        gvars.datalog_buffer[self.cd.ticker] += (f"3rd: Decision:\n")
        gvars.datalog_buffer[self.cd.ticker] += (f"Order to close at {self.cd.last_price()}\n")
        gvars.datalog_buffer[self.cd.ticker] += (self.cd.state_str())
        gvars.datalog_buffer[self.cd.ticker] += (f"P&L: {self.pnl}\n")
        gvars.datalog_buffer[self.cd.ticker] += (f"Nr of trades {self.nr_of_trades}\n")
        gvars.datalog_buffer[self.cd.ticker] += ("\n\n\n")


    def cancel_active(self):
        if not self.active_order():
            return
        self.last_action = "CANCEL"
        # self.remote.cancel_order(self.active_order_id)


    def active_order(self, where=""):
        if where == "":
            return self.active_order_id is not None
        else:
            # where == "local"
            return self.active_order_id == -1



    def order_change(self, order_id, status, remaining):
        if status == "Filled":
            self.active_order_id = None
            self.nr_of_trades += 1
        elif status == "Cancelled":
            self.active_order_id = None
        else:
            # get the order id after placing the order so
            # it is managed only on remote
            self.active_order_id = order_id
        self.position = remaining

        gvars.datalog_buffer[self.cd.ticker] += (f"Remaining (current positions): {self.position}\n")
        self.security_check()


    # Private

    def sound_notify(self):
        Thread(target = lambda: os.system("mpv --really-quiet /home/bruno/Downloads/Goat-sound-effect.mp3")).start()

    def security_check(self):
        if abs(self.position) > CONTRACT_NR:
            gvars.datalog_buffer[self.cd.ticker] += ("PROBLEM!! MORE THAN {CONTRACT_NR} CONTRACTS\n")
            print("PROBLEM!! MORE THAN {CONTRACT_NR} CONTRACTS ON {self.cd.ticker}\n")
            # self.sound_notify()
            assert False