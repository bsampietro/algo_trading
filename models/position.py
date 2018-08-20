import gvars

CONTRACT_NR = 1

class Position:
    def __init__(self, chart_data, remote):
        self.cd = chart_data
        self.remote = remote

        self.last_order_price = 0
        self.last_order_time = 0
        
        self.pnl = 0
        self.nr_of_trades = 0

        # set by IB
        self.position = 0
        # set manually and by IB
        self.active_order_id = None


    def price_change(self):
        # check for more than allowed positions
        self.security_check()
        

    def buy(self, price):
        if self.is_active_order('local'):
            return # Means internally already called buy or sell
        self.last_order_price = price
        self.last_order_time = self.cd.last_time()
        self.active_order_id = -1

        self.remote.place_order(self.cd, "BUY", CONTRACT_NR, price)

        gvars.datalog_buffer[self.cd.ticker] += (f"3rd: Decision:\n")
        gvars.datalog_buffer[self.cd.ticker] += (f"Order to buy at {price}\n")


    def sell(self, price):
        if self.is_active_order('local'):
            return # Means internally already called buy or sell
        self.last_order_price = price
        self.last_order_time = self.cd.last_time()
        self.active_order_id = -1

        self.remote.place_order(self.cd, "SELL", CONTRACT_NR, price)

        gvars.datalog_buffer[self.cd.ticker] += (f"3rd: Decision:\n")
        gvars.datalog_buffer[self.cd.ticker] += (f"Order to sell at {price}\n")


    def close(self):
        if self.position == 0:
            return

        if self.position == CONTRACT_NR:
            self.remote.place_order(self.cd, "SELL", CONTRACT_NR)
            self.pnl = round(self.pnl + self.cd.last_price() - self.last_order_price, 2)
        elif self.position == -CONTRACT_NR:
            self.remote.place_order(self.cd, "BUY", CONTRACT_NR)
            self.pnl = round(self.pnl + self.last_order_price - self.cd.last_price(), 2)

        gvars.datalog_buffer[self.cd.ticker] += (f"3rd: Decision:\n")
        gvars.datalog_buffer[self.cd.ticker] += (f"Order to close at {self.cd.last_price()}\n")
        gvars.datalog_buffer[self.cd.ticker] += (self.cd.state_str())


    def cancel_active(self):
        if not self.is_active_order():
            return
        self.remote.cancel_order(self.active_order_id)
        self.active_order_id = None


    def is_active_order(self, where=""):
        if where == "":
            return self.active_order_id is not None
        else:
            # where == "local"
            return self.active_order_id == -1


    def is_running(self):
        return self.position != 0


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
        self.security_check()


    def state_str(self):
        output = (
            f"POSITION:\n"
            f"last_order_price: {self.last_order_price}\n"
            f"last_order_time: {self.last_order_time}\n"
            f"pnl: {self.pnl}\n"
            f"nr_of_trades: {self.nr_of_trades}\n"
            f"position: {self.position}\n"
            f"active_order_id: {self.active_order_id}\n"
        )
        return output


    # Private

    def sound_notify(self):
        Thread(target = lambda: os.system("mpv --really-quiet /home/bruno/Downloads/Goat-sound-effect.mp3")).start()

    def security_check(self):
        if abs(self.position) > CONTRACT_NR:
            gvars.datalog_buffer[self.cd.ticker] += ("PROBLEM!! MORE THAN {CONTRACT_NR} CONTRACTS\n")
            print("PROBLEM!! MORE THAN {CONTRACT_NR} CONTRACTS ON {self.cd.ticker}\n")
            # self.sound_notify()
            # assert False # Not yet...