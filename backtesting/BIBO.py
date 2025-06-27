from datetime import datetime
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from account.authentication import historicalClient
import pandas as pd
import csv
import pytz
import concurrent.futures

mountain = pytz.timezone("America/Denver")

# Load S&P 500 tickers from Wikipedia
import requests
from bs4 import BeautifulSoup


def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"id": "constituents"})
    symbols = [row.find_all("td")[0].text.strip().replace(".", "-") for row in table.find_all("tr")[1:]]
    return symbols


# Load historical data using Alpaca API
def load_daily_data(symbol, start, end):
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end
    )
    bars = historicalClient.get_stock_bars(request)[symbol]
    data = [{
        "timestamp": bar.timestamp,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume
    } for bar in bars]
    df = pd.DataFrame(data)
    df.set_index("timestamp", inplace=True)
    return df


# Precompute SMAs
def compute_smas(df):
    df["SMA50"] = df["close"].rolling(50).mean()
    df["SMA100"] = df["close"].rolling(100).mean()
    df["SMA150"] = df["close"].rolling(150).mean()

    # ATR Calculation (14-day)
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR14"] = tr.rolling(14).mean()

    return df


# Check signal at each date
def scan_signals_over_time(symbol, df):
    signals = []

    if len(df) < 151:
        print(f"Skipping {symbol}: not enough data ({len(df)} rows)")
        return signals

    for i in range(151, len(df)):
        today = df.iloc[i]
        yesterday = df.iloc[i - 1]

        cond1 = today["SMA50"] > today["SMA100"] > today["SMA150"]
        cond2 = yesterday["low"] < yesterday["SMA50"] < yesterday["close"]
        cond3 = today["close"] > yesterday["close"]

        if cond1 and cond2 and cond3:
            entry_price = today["close"]
            atr = today["ATR14"]
            stop_price = entry_price - 1.5 * atr if pd.notna(atr) else None
            signals.append({
                "Symbol": symbol,
                "Date": today.name.strftime("%Y-%m-%d"),
                "Close": entry_price,
                "SMA50": today["SMA50"],
                "SMA100": today["SMA100"],
                "SMA150": today["SMA150"],
                "ATR14": atr,
                "StopLoss": stop_price,
                "TakeProfit": entry_price + 3 * atr if pd.notna(atr) else None
            })
    return signals


# Scan all S&P 500 symbols
def run_scan(start, end):
    symbols = get_sp500_symbols()
    all_signals = []

    def process(symbol):
        try:
            df = load_daily_data(symbol, start, end)
            df = compute_smas(df)
            signals = scan_signals_over_time(symbol, df)
            for sig in signals:
                i = df.index.get_loc(pd.to_datetime(sig["Date"]))
                entry = sig["Close"]
                stop = sig["StopLoss"]
                tp = sig["TakeProfit"]
                atr = sig["ATR14"]
                capital = 100000
                risk_per_trade = capital * 0.01
                position_size = round(risk_per_trade / (entry - stop), 2) if stop and entry != stop else 0

                exit_price = None
                outcome = None
                for j in range(i + 1, len(df)):
                    row = df.iloc[j]
                    bars_held = j - i
                    if row["low"] <= stop:
                        outcome = "Stopped Out"
                        sig["BarsHeld"] = bars_held
                        exit_price = stop
                        break
                    elif row["high"] >= tp:
                        outcome = "Target Hit"
                        sig["BarsHeld"] = bars_held
                        exit_price = tp
                        break

                pnl = round((exit_price - entry) * position_size, 2)
                sig.update({
                    "Outcome": outcome,
                    "ExitPrice": round(exit_price, 2),
                    "PnL": pnl,
                    "PositionSize": position_size
                })
            return signals
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(process, symbols))

    for signal_list in results:
        all_signals.extend(signal_list)

    return all_signals


# Save results
def save_signals(signals, filename):
    timestamp_str = datetime.now().astimezone(mountain).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{filename}_{timestamp_str}.csv"

    keys = ["Symbol", "Date", "Close", "SMA50", "SMA100", "SMA150", "ATR14", "StopLoss", "TakeProfit", "PositionSize",
            "ExitPrice", "Outcome", "PnL", "BarsHeld"]
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(signals)


# Main
if __name__ == "__main__":
    start = datetime(2024, 6, 1)
    end = datetime(2025, 6, 1)
    signals = run_scan(start, end)
    filename = input("Enter a name for the results file (without extension): ").strip()
    save_signals(signals, filename)
    print(f"Found {len(signals)} signals. Results saved to sma_bounce_signals.csv")
