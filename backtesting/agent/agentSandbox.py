
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pandas as pd
import yfinance as yf
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta
from account.authentication_paper import historicalClient


def get_vix(start_date, end_date) :
    vix = yf.download(
        tickers="^VIX",
        start=start_date,
        end=end_date,
        interval="5m",
        auto_adjust=False,
        multi_level_index=False
    )

    vix = vix.drop(columns=['Volume', 'Adj Close'])
    vix = vix.reset_index()
    vix.columns = ["date", "close", "high", "low", "open"]
    vix = vix[["date", "open", "high", "low", "close"]]

    return vix


def get_spy(start_date, end_date) :
    symbol = "SPY"

    req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame(5, TimeFrameUnit.Minute), start=start_date, end=end_date)
    bars = historicalClient.get_stock_bars(req)[symbol]
    data = [{
            "timestamp": bar.timestamp,
            "symbol": symbol,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
        } for bar in bars]

    df = pd.DataFrame(data)
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    df = df.rename(columns={"timestamp": "date"})

    return df


def merge_df(vix, spy) :
    spy["date"] = pd.to_datetime(spy["date"], utc=True).dt.tz_convert("America/New_York")
    vix["date"] = pd.to_datetime(vix["date"], utc=True).dt.tz_convert("America/New_York")

    df = pd.merge(
        spy,
        vix,
        on="date",
        suffixes=("_spy", "_vix")
    )

    df = df.sort_values("date").reset_index(drop=True)

    return df


start = datetime(2026, 7, 20)
end = datetime(2026, 9, 11)

#vix = get_vix(start, end)
spy = get_spy(start, end)

#print(vix)
print(spy)

#data = merge_df(vix, spy)

#print(data)



