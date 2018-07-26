import sys, os 
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import unittest
from unittest.mock import MagicMock

from models.monitor import *

class TestMonitor(unittest.TestCase):

    def setUp(self):
        self.monitor = create_monitor()

    def test_height_and_trend(self):
        data = self.monitor.data
        self.assertEqual(data[2].height, HEIGHT["mid"])
        self.assertEqual(data[2].trend, 4)
        self.assertEqual(data[3].height, HEIGHT["max"])
        self.assertEqual(data[3].trend, 5)
        self.assertEqual(data[5].height, HEIGHT["min"])
        self.assertEqual(data[5].trend, -2)
        self.assertEqual(data[7].height, HEIGHT["max"])
        self.assertEqual(data[7].trend, 4)
        self.assertEqual(data[8].trend, -1)

    def test_data_since(self):
        self.assertEqual(self.monitor.data_since(1000100), self.monitor.data[-2:])
        self.assertEqual(self.monitor.data_since(145), self.monitor.data[-4:])


def create_monitor():
    monitor = Monitor("GCQ8", None)
    monitor.log_data = MagicMock() # Disable loggin
    initial_time = 1000000
    monitor.price_change(4, 1220.40, initial_time + 0)   #0
    monitor.price_change(4, 1220.60, initial_time + 10)  #1
    monitor.price_change(4, 1220.70, initial_time + 15)  #2
    monitor.price_change(4, 1220.80, initial_time + 25)  #3
    monitor.price_change(4, 1220.70, initial_time + 50)  #4
    monitor.price_change(4, 1220.60, initial_time + 60)  #5
    monitor.price_change(4, 1220.80, initial_time + 90)  #6
    monitor.price_change(4, 1221.00, initial_time + 100) #7
    monitor.price_change(4, 1220.90, initial_time + 200) #8
    return monitor

def print_data_with_cdps(data):
    for cdp in data:
        print(f"Price: {cdp.price}")
        print(f"Time: {cdp.time}")
        print(f"Trend: {cdp.trend}")
        print(f"Height: {cdp.height}")
        print("")


if __name__ == '__main__':
    unittest.main()