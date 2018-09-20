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
        for file_or_ticker in sys.argv[1:]:
            ticker = util.file_from_path(file_or_ticker)
            gvars.datalog[ticker] = open(f"{gvars.TEMP_DIR}/{ticker}.log", "w")
            gvars.datalog_buffer[ticker] = ""
            gvars.datalog_final[ticker] = open(f"{gvars.TEMP_DIR}/{ticker}_final.log", "w")

        if util.contract_type(sys.argv[1]) == "FUT":
            ib_hft = IBHft(tickers = sys.argv[1:])
        else:
            ib_hft = IBHft(input_file = sys.argv[1])

        print("Main program finished")
    except:
        print("Exceptions raised")
        raise
    finally:
        for ticker, stream in gvars.datalog.items():
            print(f"Closing {ticker} stream...")
            stream.close()
        for ticker, stream in gvars.datalog_final.items():
            stream.close()
        print("Done.")
