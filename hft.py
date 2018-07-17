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
        if util.contract_type(sys.argv[1]) == "FUT":
            for ticker in sys.argv[1:]:
                gvars.datalog[ticker] = open(f"{gvars.TEMP_DIR}/{ticker}.log", "w")
            
            ib_hft = IBHft(tickers = sys.argv[1:])
        else:
            ticker = util.ticker_from_file(sys.argv[1])
            gvars.datalog[ticker] = open(f"{gvars.TEMP_DIR}/{ticker}.log", "w")

            ib_hft = IBHft(input_file = sys.argv[1])

        print("Main program finished")
    except:
        print("Exceptions raised")
        raise
    finally:
        for ticker, stream in gvars.datalog.items():
            print(f"Closing {ticker} stream...")
            stream.close()
        print("Done.")
