import sys
import logging
import time

from ib.ib_hft import IBHft
# from models.hft_monitor import HftMonitor

# Main method
if __name__ == "__main__":
    logging.basicConfig(filename='./log/hft.log', level=logging.INFO)
    
    try:
        parameters = sys.argv + 5 * ['']
        ib_hft = IBHft(parameters[1])
        # Waiting indefinitely to catch the program termination exception
        # time.sleep(999999999)
        print("Main program finished")
    except (KeyboardInterrupt, SystemExit) as e:
        # ib_hft.clear_all()
        print("Program stopped")
    except:
        # ib_hft.clear_all()
        raise
