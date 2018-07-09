import sys
import logging
from datetime import datetime, date
import time

from ib.ib_test_data import IBTestData
# from models.hft_monitor import HftMonitor

# Main method
if __name__ == "__main__":
    logging.basicConfig(filename='./log/test_data.log', level=logging.INFO)
    
    try:
        parameters = sys.argv + 5 * ['']
        parameters[1] = "GCQ8"
        ib_hft = IBTestData(parameters[1])
        # Waiting indefinitely to catch the program termination exception
        # time.sleep(999999999)
        print("Main program finished")
    except (KeyboardInterrupt, SystemExit) as e:
        # ib_hft.clear_all()
        print("Program stopped")
    except:
        # ib_hft.clear_all()
        raise