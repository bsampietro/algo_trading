import sys, os 
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import unittest

from models.hft_chartdata import *

class TestChartData(unittest.TestCase):

    def setUp(self):
        self.chart_data = create_chart_data()

    def test_height_and_trend(self):
        data = self.chart_data.data
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
        self.assertEqual(self.chart_data.data_since(1000100), self.chart_data.data[-2:])
        self.assertEqual(self.chart_data.data_since(145), self.chart_data.data[-4:])


def create_chart_data():
    chart_data = ChartData("GCQ8")
    initial_time = 1000000
    chart_data.add_price(1220.40, initial_time + 0)   #0
    chart_data.add_price(1220.60, initial_time + 10)  #1
    chart_data.add_price(1220.70, initial_time + 15)  #2
    chart_data.add_price(1220.80, initial_time + 25)  #3
    chart_data.add_price(1220.70, initial_time + 50)  #4
    chart_data.add_price(1220.60, initial_time + 60)  #5
    chart_data.add_price(1220.80, initial_time + 90)  #6
    chart_data.add_price(1221.00, initial_time + 100) #7
    chart_data.add_price(1220.90, initial_time + 200) #8
    return chart_data

def print_data_with_cdps(data):
    for cdp in data:
        print(f"Price: {cdp.price}")
        print(f"Time: {cdp.time}")
        print(f"Trend: {cdp.trend}")
        print(f"Height: {cdp.height}")
        print("")


if __name__ == '__main__':
    unittest.main()