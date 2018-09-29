import sys
import logging
import time
import os, os.path

import gvars
from lib import util, core
from ib.ib_hft import IBHft

# Main method
if __name__ == "__main__":
    try:
        gvars.params = sys.argv + 5 * ['']
        if ".txt" in gvars.params[1]:
            # Live
            logging.basicConfig(filename='./log/hft_live.log', level=logging.INFO)
            IBHft(tickers = util.read_symbol_list(gvars.params[1]), data_mode = gvars.params[2] == 'data_mode')
        else:
            # Load
            if os.path.isdir(gvars.params[1]):
                filenames = os.listdir(gvars.params[1])
                filenames = [f"{gvars.params[1]}/{filename}" for filename in filenames]
            else:
                filenames = [gvars.params[1]]
            for filename in filenames:
                logging.basicConfig(filename='./log/hft_load.log', level=logging.ERROR)
                IBHft(input_file = filename)
    except:
        print("Reraising exceptions in main file.")
        raise
    finally:
        print("Program finished.")
