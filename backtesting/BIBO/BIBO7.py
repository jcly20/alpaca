import pandas as pd
import requests
from bs4 import BeautifulSoup
import concurrent.futures

from datetime import datetime, timedelta
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from account.authentication_paper import historicalClient
import algorithm.tradingObjects.candle as candle
import csv
import pytz


def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"id": "constituents"})
    symbols = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        symbol = cols[0].text.strip().replace(".", "-")
        symbols.append(symbol)

    return symbols


def fetch_data(symbol, start, end):
    req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start, end=end)
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


def find_signal_today(df, current_date):

    if current_date not in df.index:
        return None

    idx = df.index.get_loc(current_date)
    if idx < 151:
        return None

    today = df.iloc[idx]
    yesterday = df.iloc[idx - 1]

    #indicators = ["SMA50", "SMA100", "SMA150", "ATR14"]
    #if any(pd.isna(today[ind]) or pd.isna(yesterday.get(ind)) for ind in indicators):
    #    return None

    cond1 = today["SMA50"] > today["SMA100"] > today["SMA150"]
    cond2 = yesterday["low"] < yesterday["SMA50"] < yesterday["close"]
    cond3 = today["close"] > yesterday["close"]
    cond4 = today["close"] > today["open"]

    if cond1 and cond2 and cond3 and cond4:
        return today

    return None


def simulate_market(start, end):
    symbols = get_sp500_symbols()
    market_data = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(fetch_data, symbol, start, end): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(futures):
            symbol = futures[future]
            try:
                df = future.result()
                df = add_indicators(df)
                market_data[symbol] = df
            except Exception as e:
                print(f"Error loading {symbol}: {e}")

    capital = 10000
    available_capital = capital
    signals_total = 0
    signals_taken = 0
    open_positions = []
    trade_log = []
    peak = capital
    max_drawdown = 0

    all_dates = pd.date_range(start=start, end=end, freq='B', tz="UTC")

    for current_date in all_dates:
        # Close trades
        still_open = []
        for trade in open_positions:
            symbol = trade["Symbol"]
            df = market_data[symbol]
            if current_date not in df.index:
                still_open.append(trade)
                continue

            row = df.loc[current_date]
            if row["low"] <= trade["StopLoss"]:
                exit_price = trade["StopLoss"]
                outcome = "Stopped Out"
            elif row["high"] >= trade["TakeProfit"]:
                exit_price = trade["TakeProfit"]
                outcome = "Target Hit"
            else:
                still_open.append(trade)
                continue

            pnl = round((exit_price - trade["EntryPrice"]) * trade["PositionSize"], 2)
            bars_held = (current_date - trade["EntryDate"]).days
            capital += pnl
            available_capital += ((trade["PositionSize"] * trade["EntryPrice"]) + pnl)

            trade_log.append({
                **trade,
                "ExitPrice": round(exit_price, 2),
                "Outcome": outcome,
                "PnL": pnl,
                "BarsHeld": bars_held
            })

        open_positions = still_open

        # Open new trades
        for symbol, df in market_data.items():

            print(f"checking {symbol}")
            signal = find_signal_today(df, current_date)
            if signal is None:
                continue

            print(f"signal found in {symbol}")
            signals_total += 1

            entry_price = signal["close"]
            atr = signal["ATR14"]
            stop_loss = entry_price - 0.5 * atr
            take_profit = entry_price + 1 * atr
            risk = 0.005 * capital
            diff = entry_price - stop_loss
            position_size = risk / diff if diff > 0 else 0
            required_capital = position_size * entry_price

            if required_capital <= available_capital and position_size > 0:
                print(f"opening a position in {symbol} @ {entry_price} -- portfolio = {capital}")
                available_capital -= required_capital
                signals_taken += 1
                open_positions.append({
                    "Symbol": symbol,
                    "EntryDate": current_date,
                    "EntryPrice": round(entry_price, 2),
                    "StopLoss": round(stop_loss, 2),
                    "TakeProfit": round(take_profit, 2),
                    "PositionSize": round(position_size, 2)
                })

        if capital > peak:
            peak = capital
        drawdown = (peak - capital) / peak
        max_drawdown = max(max_drawdown, drawdown)

    max_drawdown_pct = max_drawdown * 100
    return trade_log, capital, max_drawdown_pct, signals_total, signals_taken


def save_trades_to_csv(trades, final_capital, max_drawdown_pct, signals_total, signals_taken, filename):
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
        pct_change = ((final_capital - 10000) / 10000) * 100

        f.write("\nSummary:\n")
        f.write(f"Total PnL: {round(total_pnl, 2)}\n")
        f.write(f"Number of Trades: {num_trades}\n")
        f.write(f"Win Rate: {round(win_rate, 2)}%\n")
        f.write(f"Average PnL: {round(avg_pnl, 2)}\n")
        f.write(f"Average Bars Held: {round(avg_bars_held, 2)}\n")
        f.write(f"Final Portfolio Value: {round(final_capital, 2)}\n")
        f.write(f"% Change: {round(pct_change, 2)}%\n")
        f.write(f"Max Drawdown (%): {round(max_drawdown_pct, 2)}%\n")
        f.write(f"Signals Total: {signals_total}\n")
        f.write(f"Signals Taken: {signals_taken}\n")
        f.write(f"Signals Taken (%): {(signals_taken/signals_total)*100}\n")


if __name__ == "__main__":
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2025, 6, 30)
    trades, final_capital, max_dd, signals_total, signals_taken = simulate_market(start_date, end_date)
    print(f"Final Capital: {final_capital:.2f}, Max Drawdown: {max_dd:.2f}%, Trades: {len(trades)}")
    filename = input("Enter a name for the results file (without extension): ").strip() + ".csv"
    save_trades_to_csv(trades, final_capital, max_dd, signals_total, signals_taken, filename)
    print(f"Saved {len(trades)} trades to {filename}")

