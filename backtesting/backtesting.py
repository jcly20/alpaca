from datetime import datetime
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from account.authentication import historicalClient
import algorithm.tradingObjects.candle as candle
import csv
import pytz

# Timezone setup
mountain = pytz.timezone("America/Denver")

# Simulated portfolio and trade log
portfolio = {}
trade_log = []

# Load historical data for a symbol
def load_historical_data(symbol, start, end, timeframe=TimeFrame.Minute):
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start,
        end=end
    )
    return historicalClient.get_stock_bars(request)[symbol]

# Calculate 9-period EMA
def calculate_ema(data, period=9):
    ema = []
    k = 2 / (period + 1)
    for i in range(len(data)):
        close = data[i].close
        if i < period - 1:
            ema.append(None)
        elif i == period - 1:
            sma = sum([data[j].close for j in range(i - period + 1, i + 1)]) / period
            ema.append(sma)
        else:
            ema.append(close * k + ema[-1] * (1 - k))
    return ema

# Simulate entry logic
def simulate_trade(bar, symbol, time):
    global portfolio
    price = bar.close
    if symbol not in portfolio or portfolio[symbol]["status"] != "open":
        portfolio[symbol] = {
            "entry": price,
            "sl": round(price * 0.9975, 2),
            "trail": round(price * 0.0025, 2),
            "highest": price,
            "status": "open",
            "time": time,
            "entry_signal": "3-bar momentum"
        }
        print(f"[BUY] {symbol} at {price}")

# Check for trailing stop loss
def check_exit(bar, symbol, time):
    global portfolio, trade_log
    if symbol in portfolio and portfolio[symbol]["status"] == "open":
        price = bar.close
        if price > portfolio[symbol]["highest"]:
            portfolio[symbol]["highest"] = price

        trail_sl = portfolio[symbol]["highest"] - portfolio[symbol]["trail"]
        entry = portfolio[symbol]["entry"]

        if price <= trail_sl:
            pnl = round(price - entry, 2)
            trade_log.append([
                symbol,
                portfolio[symbol]["time"].astimezone(mountain),
                portfolio[symbol]["entry_signal"],
                entry,
                trail_sl,
                "-",
                price,
                "Trailing SL",
                pnl,
                time.astimezone(mountain)
            ])
            print(f"[SELL - Trailing SL] {symbol} at {price}, P/L: {pnl}")
            portfolio[symbol]["status"] = "closed"

# Signal logic based on updated rule
def signalScan(data, symbols, timestamps):
    emas = [calculate_ema(symbol_data) for symbol_data in data]
    for i in range(len(symbols)):
        if len(data[i]) < 3:
            continue
        c = len(data[i]) - 1
        b0, b1, b2 = data[i][c], data[i][c-1], data[i][c-2]
        ema_value = emas[i][c]
        if (
            ema_value is not None and
            ema_value > 0 and
            b2.close < b1.close < b0.close and
            b2.close > b2.open and
            b1.close > b1.open and
            b0.close > b0.open
        ):
            simulate_trade(b0, symbols[i], timestamps[c])
        check_exit(b0, symbols[i], timestamps[c])

# Backtest loop
def backtest(symbols, start, end):
    data = {symbol: load_historical_data(symbol, start, end) for symbol in symbols}
    simulated_data = [[] for _ in symbols]
    timestamps = [bar.timestamp for bar in next(iter(data.values()))]
    num_bars = len(timestamps)

    for i in range(num_bars):
        for idx, symbol in enumerate(symbols):
            bar = data[symbol][i]
            simulated_data[idx].append(
                candle.Candle(bar.open, bar.high, bar.low, bar.close, bar.close)
            )
        signalScan(simulated_data, symbols, timestamps)

    export_results()

# Export results and calculate metrics
def export_results():
    total_pnl = sum([row[8] for row in trade_log])
    wins = sum(1 for row in trade_log if row[8] > 0)
    win_rate = round(wins / len(trade_log) * 100, 2) if trade_log else 0.0

    timestamp_str = datetime.now().astimezone(mountain).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backtest_results_{timestamp_str}(trailingSL-3bar-9ema.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Symbol", "Entry Time (MT)", "Entry Signal", "Entry Price", "Stop Loss", "Target", "Exit Price", "Exit Type", "P/L", "Exit Time (MT)"])
        writer.writerows(trade_log)
        writer.writerow([])
        writer.writerow(["Total P/L", total_pnl])
        writer.writerow(["Win Rate (%)", win_rate])

    print(f"\nTotal P/L: {total_pnl}")
    print(f"Win Rate: {win_rate}%")
    print(f"Results saved to {filename}")

# Example usage
if __name__ == "__main__":
    symbols = ["AMD"]
    start = datetime(2025, 5, 1)
    end = datetime(2025, 5, 6)
    backtest(symbols, start, end)
