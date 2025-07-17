
#strategy.py
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from config import SYMBOLS, RISK_PER_TRADE, ATR_STOP_MULT, ATR_TP_MULT
from trading import submit_limit_order, load_open_positions, save_open_position
from notification import send_discord_alert
import pytz
from account.authentication_paper import client, historicalClient

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

def fetch_data(symbol):
    end = datetime.now(pytz.UTC) - timedelta(days=1)
    start = end - timedelta(days=365)
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
    return calculate_indicators(df)

def check_signal(df):
    today = df.iloc[-1]
    prev = df.iloc[-2]

    if (
        prev['low'] < prev['SMA50'] and prev['close'] > prev['SMA50'] and
        today['close'] > prev['close'] and today['close'] > today['open'] and
        today['SMA50'] > today['SMA100'] > today['SMA150']
    ):
        return True, today
    return False, None

def run_strategy():
    positions = load_open_positions()
    account = client.get_account()
    capital = float(account.cash)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for symbol in SYMBOLS:
        if symbol in positions:
            continue
        df = fetch_data(symbol)
        if df is None or len(df) < 150:
            continue
        signal, today = check_signal(df)
        if not signal:
            continue

        risk = capital * RISK_PER_TRADE
        atr = today['ATR']
        entry = today['close']
        sl = entry - ATR_STOP_MULT * atr
        tp = entry + ATR_TP_MULT * atr
        qty = int(risk / (entry - sl))

        if qty < 1:
            continue

        submit_limit_order(symbol, qty, entry)
        save_open_position(symbol, entry, sl, tp, qty)
        total_risk = qty * (entry - sl)
        message = (
            f"📈 Limit Order Placed for {symbol} @ ${entry:.2f} | SL: ${sl:.2f} | TP: ${tp:.2f}\n"
            f"💰 Account Balance: ${capital:.2f} | Risked: ${total_risk:.2f} | Qty: {qty}\n"
            f"🕒 {timestamp}"
        )
        send_discord_alert(message)


def account_info():

    account = client.get_account()
    capital = float(account.cash)
    portfolioValue = float(account.portfolio_value)
    positions = client.get_all_positions()

    openPositions = {}
    for pos in positions:
        symbol = pos.symbol
        pnl = float(pos.unrealized_pl)
        openPositions[symbol] = pnl

    return openPositions, capital, portfolioValue
