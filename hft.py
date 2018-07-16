import sys
import logging
import time
import gvars

from ib.ib_hft import IBHft
# from models.hft_monitor import HftMonitor

# Main method
if __name__ == "__main__":
    logging.basicConfig(filename='./log/hft.log', level=logging.INFO)
    
    try:
        if "data" in sys.argv[1]:
            ticker = sys.argv[1].replace("data/", "")
            gvars.datalog[ticker] = open(f"/media/ramd/{ticker}.log", "w")

            ib_hft = IBHft(input_file = sys.argv[1])
            
            gvars.datalog[ticker].close()
        else:
            for ticker in sys.argv[1:]:
                gvars.datalog[ticker] = open(f"/media/ramd/{ticker}.log", "w")
            
            ib_hft = IBHft(tickers = sys.argv[1:])
            
            for ticker in sys.argv[1:]:
                gvars.datalog[ticker].close()
        # Waiting indefinitely to catch the program termination exception
        # time.sleep(999999999)
        print("Main program finished")
    except (KeyboardInterrupt, SystemExit) as e:
        # ib_hft.clear_all()
        print("Program stopped")
    except:
        # ib_hft.clear_all()
        raise
