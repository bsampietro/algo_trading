import sys
import logging
import time
import os, os.path

import gvars
from lib import util, core
from ib.ib_hft import IBHft
from lib.arg_parse import ArgParse

# Main method
if __name__ == "__main__":
    try:
        gvars.args = ArgParse(sys.argv)
        if ".txt" in sys.argv[1]:
            # Live
            logging.basicConfig(filename='./log/hft_live.log', level=logging.INFO)
            IBHft(tickers = util.read_symbol_list(sys.argv[1]))
        else:
            # Load
            if os.path.isdir(sys.argv[1]):
                filenames = os.listdir(sys.argv[1])
                filenames = [f"{sys.argv[1]}/{filename}" for filename in filenames]
            else:
                filenames = [sys.argv[1]]
            for filename in filenames:
                logging.basicConfig(filename='./log/hft_load.log', level=logging.ERROR)
                IBHft(input_file = filename)
    except:
        print("Reraising exceptions in main file.")
        raise
    finally:
        print("Program finished.")
