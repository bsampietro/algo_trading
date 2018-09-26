import sys
import logging
import time
import gvars

from ib.ib_hft import IBHft

from lib import util

# Main method
if __name__ == "__main__":
    try:
        if ".txt" in sys.argv[1]:
            # Live
            logging.basicConfig(filename='./log/hft_live.log', level=logging.INFO)
            IBHft(tickers = util.read_symbol_list(sys.argv[1]), data_mode = sys.argv[2] == 'data_mode')
        else:
            # Load
            logging.basicConfig(filename='./log/hft_load.log', level=logging.ERROR)
            IBHft(input_file = sys.argv[1])
    except:
        print("Reraising exceptions in main file.")
        raise
    finally:
        print("Program finished.")
