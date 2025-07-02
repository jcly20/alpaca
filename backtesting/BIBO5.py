import pandas as pd
import requests
from bs4 import BeautifulSoup
import concurrent.futures

from datetime import datetime
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from account.authentication import historicalClient
import algorithm.tradingObjects.candle as candle
import csv
import pytz
import threading

# Global lock for thread-safe capital updates
capital_lock = threading.Lock()


def get_sp500_symbols():
    return ['AFL', 'MO', 'AMZN', 'AXP', 'AIG', 'AMP', 'AMGN', 'APH', 'APO', 'ACGL', 'ANET', 'AIZ', 'ATO', 'AVB', 'BKNG', 'BSX', 'BRO', 'CPT', 'CAH', 'CNP', 'CI', 'CTAS', 'CSCO', 'CFG', 'CME', 'KO', 'CTSH', 'ED', 'CEG', 'CTVA', 'COST', 'CMI', 'DRI', 'DVA', 'DELL', 'FANG', 'ETN', 'ELV', 'EQT', 'EQR', 'EG', 'FITB', 'FSLR', 'GRMN', 'GE', 'GD', 'HIG', 'HPE', 'HLT', 'HD', 'HWM', 'IBM', 'IR', 'PODD', 'ICE', 'IP', 'INTU', 'IRM', 'JCI', 'JPM', 'K', 'KEY', 'KIM', 'KMI', 'KKR', 'LHX', 'LII', 'LLY', 'LIN', 'LKQ', 'L', 'LULU', 'LYB', 'MTB', 'MAR', 'MCK', 'MET', 'MOH', 'TAP', 'MCO', 'MSI', 'NDAQ', 'NWSA', 'NWS', 'NI', 'NTRS', 'NOC', 'NRG', 'ORLY', 'OXY', 'OMC', 'OKE', 'PKG', 'PANW', 'PAYX', 'PCG', 'PNW', 'PFG', 'PG', 'PGR', 'PRU', 'PWR', 'DGX', 'RSG', 'ROL', 'SLB', 'STX', 'NOW', 'SPG', 'SBUX', 'TRGP', 'TDY', 'TPL', 'TXT', 'TKO', 'TT', 'TFC', 'TYL', 'UDR', 'URI', 'VRSK', 'VRTX', 'GWW', 'WAT', 'WEC', 'WELL', 'XEL', 'ZBRA']


def fetch_data(symbol, start, end):
    req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start, end=end)
    bars = historicalClient.get_stock_bars(req)[symbol]
    data = [{
        "timestamp": pd.to_datetime(bar.timestamp).normalize(),
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume
    } for bar in bars]
    df = pd.DataFrame(data).set_index("timestamp")
    return df

def add_indicators(df):
    df["SMA50"] = df["close"].rolling(50).mean()
    df["SMA100"] = df["close"].rolling(100).mean()
    df["SMA150"] = df["close"].rolling(150).mean()

    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR14"] = tr.rolling(14).mean()
    return df

def find_signals(df):
    signals = []
    for i in range(151, len(df)):
        today = df.iloc[i]
        yesterday = df.iloc[i - 1]

        cond1 = today["SMA50"] > today["SMA100"] > today["SMA150"]
        cond2 = yesterday["low"] < yesterday["SMA50"] < yesterday["close"]
        cond3 = today["close"] > yesterday["close"]
        cond4 = today["close"] > today["open"]

        if cond1 and cond2 and cond3 and cond4:
            signals.append(i)
    return signals

def simulate_trade(df, signal_index, capital):
    entry_price = df.iloc[signal_index]["close"]
    atr = df.iloc[signal_index]["ATR14"]
    stop_loss = entry_price - 0.5 * atr
    take_profit = entry_price + 1 * atr
    risk = 0.01 * capital
    diff = entry_price - stop_loss
    position_size = risk / diff if diff > 0 else 0

    outcome = "Expired"
    exit_price = df.iloc[-1]["close"]
    bars_held = 0

    for j in range(signal_index + 1, len(df)):
        low = df.iloc[j]["low"]
        high = df.iloc[j]["high"]
        bars_held = j - signal_index

        if low <= stop_loss:
            outcome = "Stopped Out"
            exit_price = stop_loss
            break
        if high >= take_profit:
            outcome = "Target Hit"
            exit_price = take_profit
            break

    pnl = round((exit_price - entry_price) * position_size, 2)

    return {
        "Symbol": "",
        "Date": df.index[signal_index].strftime("%Y-%m-%d"),
        "EntryPrice": round(entry_price, 2),
        "StopLoss": round(stop_loss, 2),
        "TakeProfit": round(take_profit, 2),
        "PositionSize": round(position_size, 2),
        "ExitPrice": round(exit_price, 2),
        "Outcome": outcome,
        "PnL": pnl,
        "BarsHeld": bars_held
    }, pnl

def process(symbol, start, end, capital_ref):
    try:
        df = fetch_data(symbol, start, end)
        df = add_indicators(df)
        signals = find_signals(df)
        trades = []

        for signal_index in signals:
            with capital_lock:
                current_capital = capital_ref[0]
            trade, pnl = simulate_trade(df, signal_index, current_capital)
            trade["Symbol"] = symbol
            if trade["Outcome"] != "Expired":
                trades.append(trade)
                with capital_lock:
                    capital_ref[0] += pnl

        return trades
    except Exception as e:
        print(f"Error with {symbol}: {e}")
        return []

def run(start, end):
    symbols = get_sp500_symbols()
    all_trades = []
    capital_ref = [100000]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process, symbol, start, end, capital_ref) for symbol in symbols]
        for future in concurrent.futures.as_completed(futures):
            trades = future.result()
            all_trades.extend(trades)

    return all_trades, capital_ref[0]

def save_to_csv(trades, final_capital, filename):
    if not trades:
        print("No trades to save.")
        return

    keys = list(trades[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, keys)
        writer.writeheader()
        writer.writerows(trades)

        total_pnl = sum(t["PnL"] for t in trades)
        num_trades = len(trades)
        wins = [t for t in trades if t["PnL"] > 0]
        win_rate = len(wins) / num_trades * 100 if num_trades > 0 else 0
        avg_pnl = total_pnl / num_trades if num_trades > 0 else 0
        avg_bars_held = sum(t["BarsHeld"] for t in trades) / num_trades if num_trades > 0 else 0
        pct_change = ((final_capital - 100000) / 100000) * 100

        f.write("\n")
        f.write("Summary:\n")
        f.write(f"Total PnL: {round(total_pnl, 2)}\n")
        f.write(f"Number of Trades: {num_trades}\n")
        f.write(f"Win Rate: {round(win_rate, 2)}%\n")
        f.write(f"Average PnL: {round(avg_pnl, 2)}\n")
        f.write(f"Average Bars Held: {round(avg_bars_held, 2)}\n")
        f.write(f"Final Portfolio Value: {round(final_capital, 2)}\n")
        f.write(f"% Change: {round(pct_change, 2)}%\n")

        f.write("\nSymbol Statistics:\n")
        symbol_stats = {}
        for t in trades:
            symbol = t["Symbol"]
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {"wins": 0, "total": 0}
            symbol_stats[symbol]["total"] += 1
            if t["PnL"] > 0:
                symbol_stats[symbol]["wins"] += 1

        f.write("Symbol,Total Trades,Win Rate (%)\n")
        for symbol, stats in sorted(symbol_stats.items()):
            total = stats["total"]
            win_rate_symbol = (stats["wins"] / total) * 100 if total > 0 else 0
            f.write(f"{symbol},{total},{round(win_rate_symbol, 2)}\n")

        winners = [s for s, stats in symbol_stats.items() if (stats["wins"] / stats["total"] * 100) >= 33]
        losers = [s for s in symbol_stats if s not in winners]

        f.write("Analysis:")

        def parse_market_cap(cap_str):
            try:
                if cap_str.endswith('B'):
                    return float(cap_str[:-1]) * 1e9
                elif cap_str.endswith('M'):
                    return float(cap_str[:-1]) * 1e6
                return float(cap_str.replace(',', ''))
            except:
                return 0

        f.write(f"Winners (>=33% win rate): {len(winners)} symbols\n")
        f.write(f"Losers (<33% win rate): {len(losers)} symbols\n")

        print("Summary:")
        print(f"Total PnL: {round(total_pnl, 2)}")
        print(f"Number of Trades: {num_trades}")
        print(f"Win Rate: {round(win_rate, 2)}%")
        print(f"Average PnL: {round(avg_pnl, 2)}")
        print(f"Average Bars Held: {round(avg_bars_held, 2)}")
        print(f"Final Portfolio Value: {round(final_capital, 2)}")
        print(f"% Change: {round(pct_change, 2)}%")

if __name__ == "__main__":
    start_date = datetime(2024, 11, 5)
    end_date = datetime(2025, 6, 30)
    all_trades, final_capital = run(start_date, end_date)
    filename = input("Enter a name for the results file (without extension): ").strip() + ".csv"
    save_to_csv(all_trades, final_capital, filename)
    print(f"Saved {len(all_trades)} trades to {filename}")

