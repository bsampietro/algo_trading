import sys
import logging
import time
import gvars

from ib.ib_hft import IBHft

from lib import util, core

# Main method
if __name__ == "__main__":
    try:
        params = sys.argv + 5 * ['']
        if ".txt" in sys.argv[1]:
            # Live
            logging.basicConfig(filename='./log/hft_live.log', level=logging.INFO)
            IBHft(tickers = util.read_symbol_list(sys.argv[1]), data_mode = params[2] == 'data_mode')
        else:
            # Load
            logging.basicConfig(filename='./log/hft_load.log', level=logging.ERROR)
            monitor_children = core.safe_execute(1, ValueError, int, params[2])
            IBHft(input_file = sys.argv[1], monitor_children = monitor_children)
    except:
        print("Reraising exceptions in main file.")
        raise
    finally:
        print("Program finished.")
