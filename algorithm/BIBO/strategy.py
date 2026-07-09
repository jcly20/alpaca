
#strategy.py

import sys
import os

from config import SPY_HARD, SPY_VOL_HARD, BASE_DIR, RISK_PER_TRADE, ATR_STOP_MULT, ATR_TP_MULT, MST
from trading import submit_order, load_open_positions, load_bto_orders
from notification import send_discord_alert
from logger import logger
from account.authentication_paper import client, historicalClient

import pandas as pd
from datetime import datetime, timedelta, time
import pytz
import math

from alpaca.data.requests import StockBarsRequest, StockSnapshotRequest
from alpaca.trading.requests import GetOrdersRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import OrderSide

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


def fetch_data(symbol):
    end = datetime.now(pytz.UTC) - timedelta(days=1)
    start = end - timedelta(days=230)
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )
    try:
        bars = historicalClient.get_stock_bars(request).df
    except Exception as e:
        logger.warning(f"Skipping {symbol}: {e}")
        return None
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


def generate_symbols():
    spy_holdings = pd.read_excel( os.path.join(BASE_DIR, "spy_holdings.xlsx"), skiprows=4)
    spy_symbols = spy_holdings["Ticker"].dropna().tolist()
    volume_rank = {}

    for symbol in spy_symbols:
        df = fetch_data(symbol)
        if df is None or len(df) < 20:
            continue
        avg_dollar_volume = (df["close"] * df["volume"]).tail(20).mean()
        volume_rank[symbol] = avg_dollar_volume

    spy = sorted(volume_rank, key=volume_rank.get, reverse=True)
    print(spy)
    return spy


def calculate_indicators(df):
    if df is None or df.empty:
        return None

    df['SMA50'] = df['close'].rolling(50).mean()
    df['SMA100'] = df['close'].rolling(100).mean()
    df['SMA150'] = df['close'].rolling(150).mean()
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['stock_return'] = df['close'].iloc[-1] / df['close'].iloc[-21] - 1

    return df.dropna()


def spy_data():

    spy_df = fetch_data("SPY")
    spy_df['SMA150'] = spy_df['close'].rolling(150).mean()
    spy_return = spy_df['close'].iloc[-1] / spy_df['close'].iloc[-21] - 1

    if spy_df is None or len(spy_df) < 1:
        send_discord_alert("❌ SPY data insufficient.")
        return False

    today = spy_df.iloc[-1]
    if today['close'] <= today['SMA150']:
        send_discord_alert("⚠️ No trades: SPY is below its 150SMA.")
        return False

    send_discord_alert("✅ Scanning: SPY is above its 150SMA.")
    logger.info("SPY trading above 150SMA")

    return True, spy_return


def check_signal(df, spy_return):
    today = df.iloc[-1]
    yesterday = df.iloc[-2]

    cond1 = today["SMA50"] > today["SMA100"] > today["SMA150"]
    cond2 = yesterday["low"] < yesterday["SMA50"] < yesterday["close"]
    cond3 = today["close"] > yesterday["close"]
    cond4 = today["close"] > today["open"]
    cond5 = today["stock_return"] - spy_return

    if cond1 and cond2 and cond3 and cond4 and cond5 > 0:
        return True, today

    return False, None


def time_check():

    timestamp = datetime.now(tz=MST).time()

    if not time(13, 45) <= timestamp < time(18, 58):
        print(datetime.now().time())
        send_discord_alert(f"❌ BIBO Timed Out - {timestamp}")
        logger.info(f"time_check: invalid - {timestamp}")
        return False

    logger.info(f"time_check: valid - {timestamp}")
    return True


def clear_bto_orders():
    open_orders = client.get_orders(GetOrdersRequest(status="open"))

    try:
        for order in open_orders:
            if order.side == OrderSide.BUY:
                print(f"Cancelling BUY order: {order.id} - {order.symbol}")
                client.cancel_order_by_id(order.id)
                logger.info(f"canceling bto order for {order.symbol}")
    except Exception as e:
        logger.error(f"error canceling orders: {e}")


def run_strategy():

    positions = list(load_open_positions().keys())
    bto_orders = load_bto_orders()
    account = client.get_account()
    capital = float(account.cash)

    if not time_check():
        return

    check_spy, spy_return = spy_data()

    if not check_spy:
        return

    spy = generate_symbols()

    clear_bto_orders()

    for symbol in spy:
        timestamp = datetime.now(tz=MST).strftime("%Y-%m-%d %H:%M")

        if symbol in positions:
            logger.info(f"position exists: {symbol}")
            continue
        if symbol in bto_orders:
            logger.info(f"bto order exists: {symbol}")
            continue

        df = fetch_data(symbol)
        if df is None or df.empty:
            logger.warning(f"No data returned for {symbol}")
            continue

        df = calculate_indicators(df)
        if df is None or len(df) < 2:
            continue

        signal, today = check_signal(df, spy_return)
        if not signal:
            continue

        risk = capital * RISK_PER_TRADE
        atr = today['ATR']
        entry = today['close']
        sl = entry - ATR_STOP_MULT * atr
        tp = entry + ATR_TP_MULT * atr
        qty = risk / (entry - sl)

        qty = math.floor(qty)
        entry = round(float(entry)*1.0025, 2)
        cost_basis = qty * entry
        sl = round(float(sl), 2)
        tp = round(float(tp), 2)

        if qty < 1 or cost_basis > capital:
            logger.info(f"out of bounds: {symbol} @ {timestamp} - cost_basis: {cost_basis}")
            continue

        try:
            submit_order(capital, symbol, qty, entry, sl, tp)
        except Exception as e:
            logger.error(f"Error submitting order in {symbol}: {e}")

