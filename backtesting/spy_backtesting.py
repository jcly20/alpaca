

import pandas as pd
import requests
from bs4 import BeautifulSoup
import concurrent.futures

from datetime import datetime, timedelta
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from account.authentication import historicalClient
import algorithm.tradingObjects.candle as candle
import math
import csv
import pytz

start_date = datetime(2021, 1, 1)
end_date = datetime(2025, 6, 30)

symbol = "SPY"

req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start_date, end=end_date)
bars = historicalClient.get_stock_bars(req)[symbol]
data = [{
        "timestamp": pd.to_datetime(bar.timestamp).normalize(),
        "symbol": symbol,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume
    } for bar in bars]

spy_initial = data[0]
spy_final = data[-1]

print(spy_initial)
print(spy_final)

spyPrice_initial = spy_initial["close"]
spyPrice_final = spy_final["close"]

#print(spyPrice_initial)

position_size = math.floor(10000/spyPrice_initial)
#print(position_size)
position_initial = position_size * spyPrice_initial
#print(position_initial)
position_final = position_size * spyPrice_final
#print(position_final)

pnl = round(((position_final - position_initial) / 10000) * 100, 1)

print(f"\n\nSPY change since 1/1/21: {pnl}%")

