from lib import core

class ArgParse:
    def __init__(self, args):
    	self.args = args + 10 * ['']

    def params_id(self):
    	return core.safe_execute(None, ValueError, int, self.args[3])

    def instances(self):
    	return core.safe_execute(0, ValueError, int, self.args[2])

    def data_mode(self):
    	return 'data_mode' in self.args

    def output_chart(self):
    	return 'chart' in self.args