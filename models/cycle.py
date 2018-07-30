# Represents a whole cycle from random walk to random walk
class Cycle:
    def __init__(self):
    	self.pnl = None
    	self.states = []

    def add_state(self, state):
    	self.states.append(state)

    def last_state(self):
    	return self.states[-1]

    def closed(self):
    	return self.pnl is not None

    def state_str(self):
        output = (
            f"CYCLE:\n"
            f"self.pnl: {self.pnl}\n"
        )
        return output