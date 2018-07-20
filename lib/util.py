import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from datetime import datetime, timedelta
import math
import statistics

from ibapi.contract import *

from lib.errors import *

def get_contract(symbol):
    ctype = contract_type(symbol)
    if ctype == "FUT":
        return get_futures_contract(symbol)
    elif ctype == "OPT":
        return get_options_contract(symbol)
    else:
        return get_stock_contract(symbol)

def contract_type(symbol):
    if len(symbol) in (4, 5) and symbol[-1].isdigit():
        return "FUT"
    elif len(symbol) <= 5:
        return "STK"
    else:
        return "" # is nothing

def today_in_string():
    return datetime.today().strftime("%Y%m%d")

def date_in_string(date):
    if type(date) is str:
        return date
    elif type(date) is datetime:
        return date.strftime("%Y%m%d")
    else:
        raise RuntimeError("Bruno: the_day argument is of wrong type")

def read_symbol_list(path):
    symbol_list = []
    with open(path) as symbols:
        for symbol in symbols:
            symbol = symbol.strip()
            if symbol != '' and symbol[0] != '#':
                symbol_list.append(symbol)
    return symbol_list

def covariance(data1, data2):
    if len(data1) != len(data2):
        raise RuntimeError("Covariance lists should have the same lenghts")

    data1_mean = statistics.mean(data1)
    data2_mean = statistics.mean(data2)

    sum = 0
    for i in range(len(data1)):
        sum += ((data1[i] - data1_mean) * (data2[i] - data2_mean))

    return sum / (len(data1) - 1)

def calculate_hv(closes):
    # return (statistics.stdev(closes) / closes[-1]) * 100 * math.sqrt(252/len(closes))
    return (statistics.stdev(closes) / statistics.mean(closes)) * 100 * math.sqrt(252/len(closes))

def calculate_percentage_hv(percentage_changes):
    return statistics.stdev(percentage_changes) * math.sqrt(252/len(percentage_changes))

def ticker_from_file(file_):
    return file_.replace("data/", "")


# ------ Private ------

def get_basic_contract():
    contract = Contract()
    contract.currency = "USD"
    contract.exchange = "SMART"
    return contract

# Not working method
def get_options_contract(symbol):
    contract = get_basic_contract()
    contract.symbol = symbol
    contract.secType = "OPT"
    contract.multiplier = "100"
    # contract.lastTradeDateOrContractMonth = date_str
    # contract.strike = strike
    # contract.right = right
    return contract

def get_stock_contract(symbol):
    contract = get_basic_contract()
    contract.symbol = symbol
    contract.secType = "STK"
    if symbol in ("GLD", "GDX", "GDXJ", "SOYB", "CORN", "WEAT"):
        contract.exchange = "ARCA"
    elif symbol in ("MSFT", "INTC", "CSCO"):
        contract.exchange = "ISLAND"
        # contract.primaryExchange = "ISLAND"
    return contract

def get_futures_contract(symbol):
    contract = get_basic_contract()
    contract.secType = "FUT"
    if symbol[0:2] in ("GC", "SI", "NG", "CL", "HG"):
        contract.exchange = "NYMEX"
    elif symbol[0:2] in ("ES", "GE", "6E", "6J"):
        contract.exchange = "GLOBEX"
    elif symbol[0:2] in ("UB" ,"ZB", "ZN", "ZF", "ZT", "ZS", "ZC", "ZW", "YM"):
        contract.exchange = "ECBOT"
    elif symbol[0:2] in ("VX"):
        contract.exchange = "CFE"
    elif symbol[0:3] in ("EUR", "JPY"):
        contract.exchange = "GLOBEX"
    elif symbol[0:3] in ("VIX"):
        contract.exchange = "CFE"
        contract.localSymbol = "VX" + symbol[-2:]
    
    ticker_length = len(symbol) - 2 # 2 is the lengh of month and year. eg. U8
    contract.symbol = symbol[0:ticker_length]
    contract.lastTradeDateOrContractMonth = get_futures_date(symbol[-2:]) # eg. "201612"

    return contract

# fd code is something like U8
def get_futures_date(fdcode):
    month = None
    year = None

    if fdcode[0] == "F":
        month = "01"
    elif fdcode[0] == "G":
        month = "02"
    elif fdcode[0] == "H":
        month = "03"
    elif fdcode[0] == "J":
        month = "04"
    elif fdcode[0] == "K":
        month = "05"
    elif fdcode[0] == "M":
        month = "06"
    elif fdcode[0] == "N":
        month = "07"
    elif fdcode[0] == "Q":
        month = "08"
    elif fdcode[0] == "U":
        month = "09"
    elif fdcode[0] == "V":
        month = "10"
    elif fdcode[0] == "X":
        month = "11"
    elif fdcode[0] == "Z":
        month = "12"
    else:
        raise InputError("Unknown futures month")

    if fdcode[1] == "8":
        year = "2018"
    elif fdcode[1] == "9":
        year = "2019"
    # more elifs...
    else:
        raise InputError("Unknown futures year")

    return year + month


# ----------- to implement ---------------

def get_option_expiration(date):
    day = 21 - (calendar.weekday(date.year, date.month, 1) + 2) % 7
    return datetime(date.year, date.month, day)

