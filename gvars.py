# Constants
TEMP_DIR = "/media/ramd"
HEIGHT = {'max': 1, 'mid': 0, 'min': -1}
DENSITY_DIRECTION = {'in': 1, 'out': -1, 'out-in': -11, 'in-out': 11, 'out-edge': -12}
DENSITY_DIRECTION_INV = {v: k for k, v in DENSITY_DIRECTION.items()}
TREND_PATTERN = {'follow': 1, 'neutral': 0, 'reversal': -1}

# Variables
datalog = {}
datalog_buffer = {}