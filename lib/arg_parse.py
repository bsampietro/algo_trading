from lib import core

class ArgParse:
    def __init__(self, args):
    	self.args = args + 10 * ['']

    def params_ids(self):
        if self.args[2] == '':
            return [0]
        else:
            return [int(id) for id in self.args[2].split(',')]

    def test_instances(self):
        return core.safe_execute(0, ValueError, int, self.args[3])

    def data_mode(self):
    	return 'data_mode' in self.args

    def output_chart(self):
    	return 'chart' in self.args