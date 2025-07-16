from datetime import datetime
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from account.authentication_paper import historicalClient
import algorithm.tradingObjects.candle as candle
import csv
import pytz
import concurrent.futures

# Timezone setup
mountain = pytz.timezone("America/Denver")

# Portfolio value and risk setup
initial_cash = 100000

# Load historical data for a symbol
def load_historical_data(symbol, start, end, timeframe=TimeFrame.Minute):
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start,
        end=end
    )
    return historicalClient.get_stock_bars(request)[symbol]

# Calculate EMA
def calculate_ema(data, period):
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
def simulate_trade(bar, symbol, time, portfolio, portfolio_value):
    price = bar.close
    if symbol not in portfolio or portfolio[symbol]["status"] != "open":
        risk_amount = portfolio_value * 0.01
        quantity = round(risk_amount / price, 2)
        portfolio[symbol] = {
            "entry": price,
            "sl": round(price * 0.99, 2),
            "status": "open",
            "time": time,
            "entry_signal": "3-bar momentum",
            "trail_price": price,
            "quantity": quantity
        }
    return portfolio_value

# Check for trailing stop loss
def check_exit(bar, symbol, time, portfolio, trade_log, portfolio_value):
    if symbol in portfolio and portfolio[symbol]["status"] == "open":
        entry = portfolio[symbol]["entry"]
        trail_price = portfolio[symbol]["trail_price"]
        quantity = portfolio[symbol]["quantity"]

        if bar.close > trail_price:
            portfolio[symbol]["trail_price"] = bar.close

        if bar.close <= portfolio[symbol]["trail_price"] * 0.99:
            exit_price = round(bar.close, 2)
            pnl = round((exit_price - entry) * quantity, 2)
            portfolio_value += pnl
            trade_log.append([
                symbol,
                portfolio[symbol]["time"].astimezone(mountain),
                portfolio[symbol]["entry_signal"],
                entry,
                None,
                None,
                exit_price,
                "Trailing SL",
                pnl,
                time.astimezone(mountain)
            ])
            portfolio[symbol]["status"] = "closed"
    return portfolio_value

# Signal logic based on 3-bar momentum and positive 9 EMA and above 50 EMA, during market hours
def signalScan(data, symbol, timestamps, ema_9, ema_50, portfolio, trade_log, portfolio_value):
    if len(data) < 51:
        return portfolio_value

    c = len(data) - 1
    b0, b1, b2 = data[c], data[c-1], data[c-2]
    bar_time = timestamps[c].astimezone(mountain)

    if not (bar_time.hour >= 7 and bar_time.hour < 14):
        return portfolio_value

    if (
        ema_9[c] is not None and
        ema_50[c] is not None and
        ema_9[c] > 0 and
        b0.close > ema_50[c] and
        b2.close < b1.close < b0.close and
        b2.close > b2.open and
        b1.close > b1.open and
        b0.close > b0.open
    ):
        portfolio_value = simulate_trade(b0, symbol, timestamps[c], portfolio, portfolio_value)

    portfolio_value = check_exit(b0, symbol, timestamps[c], portfolio, trade_log, portfolio_value)

    return portfolio_value

# Run backtest on a single symbol
def run_backtest(symbol, start, end):
    data = load_historical_data(symbol, start, end)
    portfolio = {}
    trade_log = []
    portfolio_value = initial_cash

    simulated_data = []
    timestamps = []
    for bar in data:
        simulated_data.append(candle.Candle(bar.open, bar.high, bar.low, bar.close, bar.close))
        timestamps.append(bar.timestamp)

    ema_9 = calculate_ema(simulated_data, 9)
    ema_50 = calculate_ema(simulated_data, 50)

    for i in range(50, len(simulated_data)):
        portfolio_value = signalScan(simulated_data[:i+1], symbol, timestamps[:i+1], ema_9[:i+1], ema_50[:i+1], portfolio, trade_log, portfolio_value)

    return trade_log

# Export results and calculate metrics
def export_results(all_trade_logs):
    flat_log = [entry for log in all_trade_logs for entry in log]
    total_pnl = sum([row[8] for row in flat_log])
    wins = sum(1 for row in flat_log if row[8] > 0)
    win_rate = round(wins / len(flat_log) * 100, 2) if flat_log else 0.0
    growth = round(total_pnl, 2)
    growth_pct = round((growth / initial_cash) * 100, 2)

    timestamp_str = datetime.now().astimezone(mountain).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backtest_results_parallel_{timestamp_str}.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Symbol", "Entry Time (MT)", "Entry Signal", "Entry Price", "Stop Loss", "Target", "Exit Price", "Exit Type", "P/L", "Exit Time (MT)"])
        writer.writerows(flat_log)
        writer.writerow([])
        writer.writerow(["Total P/L", total_pnl])
        writer.writerow(["Win Rate (%)", win_rate])
        writer.writerow(["Portfolio Growth ($)", growth])
        writer.writerow(["Portfolio Growth (%)", growth_pct])

    print(f"\nTotal P/L: {total_pnl}")
    print(f"Win Rate: {win_rate}%")
    print(f"Portfolio Growth: ${growth} ({growth_pct}%)")
    print(f"Results saved to {filename}")

# Main parallel backtest
if __name__ == "__main__":
    symbols = ["AMD",      # Tech
        "JNJ",      # Healthcare
        "KO",       # Consumer Staples
        "XOM",      # Energy
        "WMT",      # Retail
        "TSLA",     # Auto/Tech
        "JPM",      # Financial
        "MCD",      # Restaurants
        "BA",       # Aerospace
        "CVX"       # Energy
    ]
    start = datetime(2025, 5, 1)
    end = datetime(2025, 6, 1)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda sym: run_backtest(sym, start, end), symbols))

    export_results(results)
