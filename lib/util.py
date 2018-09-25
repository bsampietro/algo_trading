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

def read_symbol_list(path):
    symbol_list = []
    with open(path) as symbols:
        for symbol in symbols:
            symbol = symbol.strip()
            if symbol != '' and symbol[0] != '#':
                symbol_list.append(symbol)
    return symbol_list

def file_from_path(file_):
    return file_.split("/")[-1]

def value_or_min_max(value, min_max):
    if value < min_max[0]:
        return min_max[0]
    elif value > min_max[1]:
        return min_max[1]
    else:
        return value

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
    elif symbol[0:2] in ("ES", "NQ", "GE"):
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