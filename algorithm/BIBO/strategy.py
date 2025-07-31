
#strategy.py

import sys
import os

# Add the root of your repo (2 levels up from main.py)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config import SPY, SPY_VOL, RISK_PER_TRADE, ATR_STOP_MULT, ATR_TP_MULT
from trading import submit_order, load_open_positions
from notification import send_discord_alert
from account.authentication_paper import client, historicalClient

import pandas as pd
from datetime import datetime, timedelta, time
import pytz

from alpaca.data.requests import StockBarsRequest, StockSnapshotRequest
from alpaca.data.timeframe import TimeFrame


def fetch_data(symbol):
    end = datetime.now(pytz.UTC) - timedelta(days=1)
    start = end - timedelta(days=230)
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )
    bars = historicalClient.get_stock_bars(request).df
    if bars.empty or symbol not in bars.index.get_level_values(0):
        return None

    df = bars.xs(symbol, level=0).copy()
    df.index = df.index.tz_convert('US/Eastern')

    df = df.drop(columns=["vwap", "trade_count"])

    latest_bar_resp = historicalClient.get_stock_snapshot(StockSnapshotRequest(symbol_or_symbols=symbol))
    latest_bar = latest_bar_resp[symbol].daily_bar

    latest_df = pd.DataFrame([{
        "open": latest_bar.open,
        "high": latest_bar.high,
        "low": latest_bar.low,
        "close": latest_bar.close,
        "volume": latest_bar.volume
    }], index=[latest_bar.timestamp.astimezone(pytz.timezone('US/Eastern'))])

    df = pd.concat([df, latest_df])

    return df


def calculate_indicators(df):

    df['SMA50'] = df['close'].rolling(50).mean()
    df['SMA100'] = df['close'].rolling(100).mean()
    df['SMA150'] = df['close'].rolling(150).mean()
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(14).mean()

    return df.dropna()


def check_spy():

    print("spy")
    spy_df = fetch_data("SPY")
    spy_df['SMA150'] = spy_df['close'].rolling(150).mean()

    if spy_df is None or len(spy_df) < 1:
        send_discord_alert("❌ SPY data insufficient.")
        return False

    today = spy_df.iloc[-1]
    if today['close'] <= today['SMA150']:
        send_discord_alert("⚠️ No trades: SPY is below its 150SMA.")
        return False

    send_discord_alert("✅ Scanning: SPY is above its 150SMA.")

    return True


def check_signal(df):
    today = df.iloc[-1]
    yesterday = df.iloc[-2]

    cond1 = today["SMA50"] > today["SMA100"] > today["SMA150"]
    cond2 = yesterday["low"] < yesterday["SMA50"] < yesterday["close"]
    cond3 = today["close"] > yesterday["close"]
    cond4 = today["close"] > today["open"]

    if cond1 and cond2 and cond3 and cond4:
        return True, today

    return False, None


def time_check():

    if not time(15, 50) <= datetime.now().time() < time(16, 0):
        send_discord_alert("❌ BIBO Timed Out")
        return False

    return True


def run_strategy():

    positions = list(load_open_positions().keys())
    account = client.get_account()
    capital = float(account.cash)

    if not time_check():
        return

    if not check_spy():
        return

    for symbol in SPY_VOL:
        print(f"scanning: {symbol}")
        if symbol in positions:
            print(f"{symbol} already in portfolio")
            continue
        df = fetch_data(symbol)
        df = calculate_indicators(df)
        if df is None or len(df) < 1:
            continue
        signal, today = check_signal(df)
        if not signal:
            continue

        risk = capital * RISK_PER_TRADE
        atr = today['ATR']
        entry = today['close']
        sl = entry - ATR_STOP_MULT * atr
        tp = entry + ATR_TP_MULT * atr
        qty = risk / (entry - sl)

        if qty < 1:
            continue

        submit_order(capital, symbol, qty, entry, sl, tp)

