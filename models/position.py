import os, sys
import logging
import gvars
from models.active_position import ActivePosition

CONTRACT_NR = 1
POI = {'none': -2, 'local': -1} # 'none' is no order; 'local' is local order; >= 0 is server approved order

class Position:
    def __init__(self, monitor, remote):
        self.m = monitor
        self.remote = remote

        self.order_price = None # type: float
        self.order_time = None # type: int

        self.ap = None
        
        self.nr_of_trades = 0

        self.pending_position = 0
        self.position = 0 # set by IB
        self.pending_order_id = POI['none'] # set manually and by IB


    def price_change(self):
        if self.ap is not None:
            self.ap.price_change()
        

    def buy(self, price = None):
        assert self.position == 0
        if self.is_pending():
            return
        self.order_price = price
        self.order_time = self.m.last_time()

        self.pending_position = CONTRACT_NR
        self.pending_order_id = POI['local']

        self.remote.place_order(self.m, "BUY", CONTRACT_NR, price, test=self.m.test)

        self.m.datalog_buffer += (f"    Order to BUY at {price}\n")
        logging.info("+++++ Buy called ++++++")


    def sell(self, price = None):
        assert self.position == 0
        if self.is_pending():
            return
        self.order_price = price
        self.order_time = self.m.last_time()

        self.pending_position = -CONTRACT_NR
        self.pending_order_id = POI['local']

        self.remote.place_order(self.m, "SELL", CONTRACT_NR, price, test=self.m.test)

        self.m.datalog_buffer += (f"    Order to SELL at {price}\n")
        logging.info("+++++ Sell called ++++++")


    def close(self, price = None):
        assert self.position != 0
        if self.pending_order_id == POI['local']:
            logging.info("Called close multiple times without intermediate confirmation")
            return
        self.order_price = price
        self.order_time = self.m.last_time()

        if self.pending_order_id == POI['none']:
            self.pending_order_id = POI['local']
            order_id = None
        elif self.pending_order_id == POI['local']:
            assert False # should never get here
        else:
            order_id = self.pending_order_id

        if self.position == CONTRACT_NR:
            self.pending_position = -CONTRACT_NR
            self.remote.place_order(self.m, "SELL", CONTRACT_NR, price, order_id=order_id, test=self.m.test)
        elif self.position == -CONTRACT_NR:
            self.pending_position = CONTRACT_NR
            self.remote.place_order(self.m, "BUY", CONTRACT_NR, price, order_id=order_id, test=self.m.test)

        self.m.datalog_buffer += (f"    Order to close at {self.m.last_price()}\n")
        logging.info("+++++ Close Called ++++++")


    def cancel_pending(self):
        if self.pending_order_id in (POI['none'], POI['local']):
            return
        pending_order_id = self.pending_order_id
        self.pending_order_id = POI['local']
        self.remote.cancel_order(pending_order_id, test=self.m.test)


    def is_pending(self):
        return self.pending_order_id != POI['none']


    def is_active(self):
        return self.position != 0


    def direction(self):
        if self.position > 0:
            return 1
        elif self.position < 0:
            return -1
        else:
            return 0


    def order_change(self, order_id, status, remaining, fill_price, fill_time):
        self.m.datalog_buffer += (f"    position.order_change.order_id: {order_id}\n")
        self.m.datalog_buffer += (f"    position.order_change.status: {status}\n")
        self.m.datalog_buffer += (f"    position.order_change.remaining: {remaining}\n")
        
        if status == "Filled":
            self.pending_order_id = POI['none']
            self.nr_of_trades += 1
            self.position += self.pending_position
            self.pending_position = 0
            if self.position == 0:
                self.ap.append_results(fill_price, fill_time)
                self.ap = None
            else:
                self.ap = ActivePosition(self.m, self, fill_price, fill_time)
            self.order_price = None
            self.order_time = None
        elif status == "Cancelled":
            self.pending_order_id = POI['none']
            self.order_price = None
            self.order_time = None
        else:
            # status == "Submitted" or other
            # get the order id after placing the order so
            # it is managed only on remote
            self.pending_order_id = order_id
        # self.security_check(remaining)


    def state_str(self):
        output = ""
        if self.is_active() or self.is_pending():
            output += (
                f"  POSITION:\n"
                f"    nr_of_trades: {self.nr_of_trades}\n"
                f"    position: {self.position}\n"
                f"    pending_order_id: {self.pending_order_id}\n"
                f"    pending_position: {self.pending_position}\n"
            )
            if self.order_price is not None and self.order_time is not None:
                output += (
                    f"    order_price: {self.order_price:.{self.m.prm.price_precision}f}\n"
                    f"    order_time: {self.order_time:.4f}\n"
                )
        if self.ap is not None:
            output += self.ap.state_str()
        return output


    # Private

    def sound_notify(self):
        Thread(target = lambda: os.system("mpv --really-quiet /home/bruno/Downloads/Goat-sound-effect.mp3")).start()

    def security_check(self, remaining):
        if self.position != remaining or abs(self.position) > CONTRACT_NR:
            self.m.datalog_buffer += ("PROBLEM!! MORE THAN {CONTRACT_NR} CONTRACTS\n")
            print("PROBLEM!! MORE THAN {CONTRACT_NR} CONTRACTS ON {self.m.ticker}\n")
            # self.sound_notify()
            # os._exit(1)
            sys.exit(1)