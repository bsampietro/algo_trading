class Closing:
    def __init__(self, monitor):
    	self.m = monitor
    	self.close_limit_orders = 0
    	self.close_limit_price = self.m.last_price()

    def order_type(self):
    	if self.m.ticks(abs(self.close_limit_price - self.m.last_price())) >= 2:
    		if self.close_limit_orders < 2:
    			self.close_limit_orders += 1
    			self.close_limit_price = self.m.last_price()
    			return "LMT"
    		else:
    			return "MKT"
    	else:
    		return ''