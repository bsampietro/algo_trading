# App Constants:
HEIGHT = {'max': 1, 'mid': 0, 'min': -1}
DENSITY_DIRECTION = {'in': 1, 'out': -1, 'out-in': -11, 'in-out': 11, 'out-edge': -12}
DENSITY_DIRECTION_INV = {v: k for k, v in DENSITY_DIRECTION.items()}
TREND_PATTERN = {'follow': 1, 'neutral': 0, 'reversal': -1}

# Variables:
params = None

# Config:
TEMP_DIR = "/media/ramd"
CONF = {
	'dynamic_parameter_change': 20, # None to disable
	'accepting_average_pnl': 6.0,
	'discarding_average_pnl': 3.0
}