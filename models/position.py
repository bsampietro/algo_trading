import gvars

CONTRACT_NR = 1

class Position:
    def __init__(self, monitor, remote):
        self.m = monitor
        self.remote = remote

        self.last_order_price = 0
        self.last_order_time = 0
        
        self.pnl = 0
        self.nr_of_trades = 0

        # set by IB
        self.position = 0
        # set manually and by IB
        self.pending_order_id = None


    def price_change(self):
        # check for more than allowed positions
        self.security_check()
        

    def buy(self, price):
        if self.is_pending('local'):
            return # Means internally already called buy or sell
        self.last_order_price = price
        self.last_order_time = self.m.last_time()
        self.pending_order_id = -1

        self.remote.place_order(self.m, "BUY", CONTRACT_NR, price)

        gvars.datalog_buffer[self.m.ticker] += ("    3rd: Decision:\n")
        gvars.datalog_buffer[self.m.ticker] += (f"      Order to buy at {price}\n")


    def sell(self, price):
        if self.is_pending('local'):
            return # Means internally already called buy or sell
        self.last_order_price = price
        self.last_order_time = self.m.last_time()
        self.pending_order_id = -1

        self.remote.place_order(self.m, "SELL", CONTRACT_NR, price)

        gvars.datalog_buffer[self.m.ticker] += (f"    3rd: Decision:\n")
        gvars.datalog_buffer[self.m.ticker] += (f"      Order to sell at {price}\n")


    def close(self):
        if self.position == 0:
            return

        if self.position == CONTRACT_NR:
            self.remote.place_order(self.m, "SELL", CONTRACT_NR)
            self.pnl = round(self.pnl + self.m.last_price() - self.last_order_price, 2)
        elif self.position == -CONTRACT_NR:
            self.remote.place_order(self.m, "BUY", CONTRACT_NR)
            self.pnl = round(self.pnl + self.last_order_price - self.m.last_price(), 2)

        gvars.datalog_buffer[self.m.ticker] += (f"    3rd: Decision:\n")
        gvars.datalog_buffer[self.m.ticker] += (f"      Order to close at {self.m.last_price()}\n")


    def cancel_pending(self):
        if not self.is_pending():
            return
        self.remote.cancel_order(self.pending_order_id)
        self.pending_order_id = None


    def is_pending(self, where=""):
        if where == "":
            return self.pending_order_id is not None
        else:
            # where == "local"
            return self.pending_order_id == -1


    def is_active(self):
        return self.position != 0


    def order_change(self, order_id, status, remaining):
        gvars.datalog_buffer[self.m.ticker] += ("    position.order_change params:\n")
        gvars.datalog_buffer[self.m.ticker] += (f"      order_id: {order_id}\n")
        gvars.datalog_buffer[self.m.ticker] += (f"      status: {status}\n")
        gvars.datalog_buffer[self.m.ticker] += (f"      remaining: {remaining}\n")
        
        if status == "Filled":
            self.pending_order_id = None
            self.nr_of_trades += 1
        elif status == "Cancelled":
            self.pending_order_id = None
        else:
            # get the order id after placing the order so
            # it is managed only on remote
            self.pending_order_id = order_id
        self.position = remaining


    def state_str(self):
        output = ""
        if self.is_active() or self.is_pending():
            output += (
                f"  POSITION:\n"
                f"    last_order_price: {self.last_order_price}\n"
                f"    last_order_time: {self.last_order_time}\n"
                f"    pnl: {self.pnl}\n"
                f"    nr_of_trades: {self.nr_of_trades}\n"
                f"    position: {self.position}\n"
                f"    pending_order_id: {self.pending_order_id}\n"
            )
        return output


    # Private

    def sound_notify(self):
        Thread(target = lambda: os.system("mpv --really-quiet /home/bruno/Downloads/Goat-sound-effect.mp3")).start()

    def security_check(self):
        if abs(self.position) > CONTRACT_NR:
            gvars.datalog_buffer[self.m.ticker] += ("PROBLEM!! MORE THAN {CONTRACT_NR} CONTRACTS\n")
            print("PROBLEM!! MORE THAN {CONTRACT_NR} CONTRACTS ON {self.m.ticker}\n")
            # self.sound_notify()
            # assert False # Not yet...