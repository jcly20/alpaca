import pandas as pd
import requests
from bs4 import BeautifulSoup
import concurrent.futures

from datetime import datetime
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from account.authentication_paper import historicalClient
import algorithm.tradingObjects.candle as candle
import csv
import pytz
import concurrent.futures

# Timezone setup
#mountain = pytz.timezone("America/Denver")

def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"id": "constituents"})
    symbols = [row.find_all("td")[0].text.strip().replace(".", "-") for row in table.find_all("tr")[1:]]
    #get first 100 symbols
    symbols = symbols[:100]

    return symbols

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
    position_size = risk / (entry_price - stop_loss) if (entry_price - stop_loss) > 0 else 0

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

def process(symbol, start, end, capital):
    try:
        df = fetch_data(symbol, start, end)
        df = add_indicators(df)
        signals = find_signals(df)
        trades = []
        for signal_index in signals:
            trade, pnl = simulate_trade(df, signal_index, capital)
            trade["Symbol"] = symbol
            if not trade["Outcome"] == "Expired":
                trades.append(trade)
                capital += pnl
        return trades, capital
    except Exception as e:
        print(f"Error with {symbol}: {e}")
        return [], capital

def run(start, end):
    symbols = get_sp500_symbols()
    all_trades = []
    capital = 100000

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process, symbol, start, end, capital) for symbol in symbols]
        for future in concurrent.futures.as_completed(futures):
            trades, capital = future.result()
            all_trades.extend(trades)

    return all_trades, capital

def save_to_csv(trades, final_capital, filename):
    if not trades:
        print("No trades to save.")
        return

    keys = list(trades[0].keys())
    with open(filename, "w", newline="") as f:
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

        print("Summary:")
        print(f"Total PnL: {round(total_pnl, 2)}")
        print(f"Number of Trades: {num_trades}")
        print(f"Win Rate: {round(win_rate, 2)}%")
        print(f"Average PnL: {round(avg_pnl, 2)}")
        print(f"Average Bars Held: {round(avg_bars_held, 2)}")
        print(f"Final Portfolio Value: {round(final_capital, 2)}")
        print(f"% Change: {round(pct_change, 2)}%")

if __name__ == "__main__":
    start_date = datetime(2024, 6, 1)
    end_date = datetime(2025, 6, 1)
    all_trades, final_capital = run(start_date, end_date)
    filename = input("Enter a name for the results file (without extension): ").strip() + ".csv"
    save_to_csv(all_trades, final_capital, filename)
    print(f"Saved {len(all_trades)} trades to {filename}")
