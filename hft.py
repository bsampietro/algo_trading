import sys
import logging
import time
import gvars

from ib.ib_hft import IBHft

from lib import util

# Main method
if __name__ == "__main__":
    logging.basicConfig(filename='./log/hft.log', level=logging.INFO)
    try:
        if ".txt" in sys.argv[1]:
            ib_hft = IBHft(tickers = util.read_symbol_list(sys.argv[1]))
        else:
            ib_hft = IBHft(input_file = sys.argv[1])
        print("Main program finished")
    except:
        print("Exceptions raised")
        raise
    finally:
        print("Done.")
