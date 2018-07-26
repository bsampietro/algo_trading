import gvars

CONTRACT_NR = 1

class Position:
    def __init__(self, chart_data, remote):
        self.cd = chart_data
        self.remote = remote

        # Positions
        self.position = 0
        self.confirmed_position = 0 # set by IB

        # for internal count or backtesting
        self.order_price = 0
        # self.confirmed_price = 0
        self.pnl = 0
        self.nr_of_trades = 0

        # Orders
        self.active_order_id = None


    def buy(self, price):
        self.position = CONTRACT_NR
        self.order_price = price
        self.nr_of_trades += 1

        if self.confirmed_position == 0 and not self.active_order(): # be sure!
            # remote.place_order(self, "BUY", CONTRACT_NR, price)
            pass

        gvars.datalog[self.cd.ticker].write(f"3rd: Decision:\n")
        gvars.datalog[self.cd.ticker].write(f"Order to buy at {price}\n")
        gvars.datalog[self.cd.ticker].write("\n\n\n")
        print(f"Order to buy {self.cd.ticker} at {price}")


    def sell(self, price):
        self.position = -CONTRACT_NR
        self.order_price = price
        self.nr_of_trades += 1

        if self.confirmed_position == 0 and not self.active_order(): # be sure!
            # remote.place_order(self, "SELL", CONTRACT_NR, price)
            pass

        gvars.datalog[self.cd.ticker].write(f"3rd: Decision:\n")
        gvars.datalog[self.cd.ticker].write(f"Order to sell at {price}\n")
        gvars.datalog[self.cd.ticker].write("\n\n\n")
        print(f"Order to sell {self.cd.ticker} at {price}")


    def close(self, price):
        if self.position == CONTRACT_NR:
            self.pnl += price - self.order_price
        elif self.position == -CONTRACT_NR:
            self.pnl += self.order_price - price
        self.nr_of_trades += 1
        
        if self.confirmed_position == CONTRACT_NR and not self.active_order(): # be sure!
            # remote.place_order(self, "SELL", CONTRACT_NR)
            pass
        elif self.confirmed_position == -CONTRACT_NR and not self.active_order(): # be sure!
            # remote.place_order(self, "BUY", CONTRACT_NR)
            pass

        gvars.datalog[self.cd.ticker].write(f"3rd: Decision:\n")
        gvars.datalog[self.cd.ticker].write(f"Order to close at {price}\n")
        gvars.datalog[self.cd.ticker].write(self.cd.state_str())
        gvars.datalog[self.cd.ticker].write(f"P&L: {self.pnl}\n")
        gvars.datalog[self.cd.ticker].write(f"Nr of trades {self.nr_of_trades}\n")
        gvars.datalog[self.cd.ticker].write("\n\n\n")
        print(f"Order to close {self.cd.ticker} at {price}")
        print(f"P&L: {self.pnl}")
        print(f"Nr of trades {self.nr_of_trades}")


    # All position querying should be done with self.confirmed_position once the system is executing orders

    def order_change(self, order_id, status, remaining):
        if status == "Filled":
            self.active_order_id = None
            # self.confirmed_price = self.order_price
        elif status == "Cancelled":
            self.active_order_id = None
        else:
            # get the order id after placing the order so
            # it is managed only on remote
            self.active_order_id = order_id
        self.confirmed_position = remaining

        gvars.datalog[self.cd.ticker].write(f"Remaining (current positions): {self.confirmed_position}\n")
        if abs(self.confirmed_position) > CONTRACT_NR:
            gvars.datalog[self.cd.ticker].write("PROBLEM!! MORE THAN {CONTRACT_NR} CONTRACTS\n")
            self.sound_notify()


    # Private

    def sound_notify(self):
        Thread(target = lambda: os.system("mpv --really-quiet /home/bruno/Downloads/Goat-sound-effect.mp3")).start()

    # Worth??
    def active_order(self):
        self.active_order_id is not None