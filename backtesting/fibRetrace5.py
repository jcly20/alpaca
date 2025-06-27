from datetime import datetime
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from account.authentication import historicalClient
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


# Calculate Fibonacci retracement levels
def calculate_fibonacci_levels(swing_high, swing_low):
    diff = swing_high - swing_low
    return {
        '0.0': swing_high,
        '38.2': swing_high - 0.382 * diff,
        '50.0': swing_high - 0.5 * diff,
        '61.8': swing_high - 0.618 * diff
    }


# Identify swing highs and lows
def find_recent_swing(data, lookback=20):
    highs = [bar.high for bar in data[-lookback:]]
    lows = [bar.low for bar in data[-lookback:]]
    return max(highs), min(lows)


# Simulate entry based on Fib retracement

def simulate_trade_fib(bar, symbol, time, portfolio, portfolio_value, fib_levels, prev_bar, swing_low):
    price = bar.close
    buffer = 0.25  # Loosen condition slightly

    if symbol not in portfolio or portfolio[symbol]["status"] != "open":
        in_zone = fib_levels['50.0'] - buffer <= price <= fib_levels['61.8'] + buffer
        bounce = bar.close > bar.open and bar.close > prev_bar.close

        if in_zone and bounce:
            risk_amount = portfolio_value * 0.01
            quantity = round(risk_amount / price, 2)
            portfolio[symbol] = {
                "entry": price,
                "sl": round(swing_low, 2),
                "target": round(fib_levels['0.0'], 2),
                "status": "open",
                "time": time,
                "entry_signal": "Fibonacci Retracement",
                "trail_price": price,
                "quantity": quantity
            }

    return portfolio_value


# Check for target and trailing stop loss
def check_exit(bar, symbol, time, portfolio, trade_log, portfolio_value):
    if symbol in portfolio and portfolio[symbol]["status"] == "open":
        entry = portfolio[symbol]["entry"]
        trail_price = portfolio[symbol]["trail_price"]
        sl = portfolio[symbol]["sl"]
        target = portfolio[symbol]["target"]
        quantity = portfolio[symbol]["quantity"]

        # Trail SL upward
        if bar.close > trail_price:
            portfolio[symbol]["trail_price"] = bar.close
            portfolio[symbol]["sl"] = round(bar.close * 0.99, 2)

        # Take profit at 0% level (sell full position)
        if bar.close >= target:
            exit_price = round(bar.close, 2)
            pnl = round((exit_price - entry) * quantity, 2)
            portfolio_value += pnl
            trade_log.append([
                symbol,
                portfolio[symbol]["time"].astimezone(mountain),
                portfolio[symbol]["entry_signal"],
                entry,
                portfolio[symbol]["sl"],
                target,
                exit_price,
                "Target Hit",
                pnl,
                time.astimezone(mountain),
                round((target - entry) / (entry - sl), 2) if entry != sl else None  # R/R ratio
            ])
            portfolio[symbol]["status"] = "closed"
            return portfolio_value

        # Stop out if SL is hit
        if bar.close <= portfolio[symbol]["sl"]:
            exit_price = round(bar.close, 2)
            pnl = round((exit_price - entry) * quantity, 2)
            portfolio_value += pnl
            trade_log.append([
                symbol,
                portfolio[symbol]["time"].astimezone(mountain),
                portfolio[symbol]["entry_signal"],
                entry,
                portfolio[symbol]["sl"],
                target,
                exit_price,
                "Trailing SL",
                pnl,
                time.astimezone(mountain),
                round((target - entry) / (entry - sl), 2) if entry != sl else None  # R/R ratio here added
            ])
            portfolio[symbol]["status"] = "closed"
    return portfolio_value


# Signal scan for Fib retracement setup
def signalScan_fib(data, symbol, timestamps, portfolio, trade_log, portfolio_value):
    if len(data) < 61:
        return portfolio_value

    c = len(data) - 1
    bar = data[c]
    prev_bar = data[c - 1]
    bar_time = timestamps[c].astimezone(mountain)

    if not bar_time.hour > 8 or bar_time.hour >= 14:
        return portfolio_value

    swing_high, swing_low = find_recent_swing(data[:c])
    fib_levels = calculate_fibonacci_levels(swing_high, swing_low)

    portfolio_value = simulate_trade_fib(bar, symbol, timestamps[c], portfolio, portfolio_value, fib_levels, prev_bar,
                                         swing_low)
    portfolio_value = check_exit(bar, symbol, timestamps[c], portfolio, trade_log, portfolio_value)

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

    for i in range(61, len(simulated_data)):
        portfolio_value = signalScan_fib(simulated_data[:i + 1], symbol, timestamps[:i + 1], portfolio, trade_log,
                                         portfolio_value)

    return trade_log


# Export results and calculate metrics
def export_results(all_trade_logs, custom_filename=None):
    flat_log = [entry for log in all_trade_logs for entry in log]
    total_pnl = sum([row[8] for row in flat_log])
    wins = sum(1 for row in flat_log if row[8] > 0)
    win_rate = round(wins / len(flat_log) * 100, 2) if flat_log else 0.0
    growth = round(total_pnl, 2)
    growth_pct = round((growth / initial_cash) * 100, 2)

    # R/R performance analysis
    rr_buckets = {"<1": [], "1-2": [], "2-3": [], ">=3": []}
    for row in flat_log:
        rr = row[10] if len(row) > 10 else None
        if rr is not None:
            if rr < 1:
                rr_buckets["<1"].append(row[8])
            elif rr < 2:
                rr_buckets["1-2"].append(row[8])
            elif rr < 3:
                rr_buckets["2-3"].append(row[8])
            else:
                rr_buckets[">=3"].append(row[8])

    timestamp_str = datetime.now().astimezone(mountain).strftime("%Y-%m-%d_%H-%M-%S")
    if custom_filename:
        filename = f"{custom_filename}_{timestamp_str}.csv"
    else:
        filename = f"backtest_fibonacci_{timestamp_str}.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Symbol", "Entry Time (MT)", "Entry Signal", "Entry Price", "Stop Loss", "Target", "Exit Price",
             "Exit Type", "P/L", "Exit Time (MT)", "R/R Ratio"])
        writer.writerows(flat_log)
        writer.writerow([])
        writer.writerow(["Total P/L", total_pnl])
        writer.writerow(["Win Rate (%)", win_rate])
        writer.writerow(["Portfolio Growth ($)", growth])
        writer.writerow([])
        writer.writerow(["P/L by R/R Bucket"])
        for bucket, values in rr_buckets.items():
            avg_bucket = round(sum(values) / len(values), 2) if values else 0.0
            total_bucket = round(sum(values), 2)
            writer.writerow(
                [f"{bucket} R/R", f"Avg P/L: {avg_bucket}", f"Total P/L: {total_bucket}", f"Count: {len(values)}"])
        writer.writerow(["Portfolio Growth (%)", growth_pct])

        # P/L by symbol and time of day (written inside the same CSV)
        from collections import defaultdict
        symbol_pnl = defaultdict(list)
        time_of_day_pnl = defaultdict(list)

        for row in flat_log:
            symbol = row[0]
            pnl = row[8]
            time = row[9].astimezone(mountain)
            hour_bin = f"{time.hour:02d}:00 - {time.hour + 1:02d}:00"

            symbol_pnl[symbol].append(pnl)
            time_of_day_pnl[hour_bin].append(pnl)

        writer.writerow([])
        writer.writerow(["P/L by Symbol"])
        for symbol, pnl_list in symbol_pnl.items():
            total = round(sum(pnl_list), 2)
            avg = round(sum(pnl_list) / len(pnl_list), 2)
            count = len(pnl_list)
            writer.writerow([symbol, f"Total P/L: {total}", f"Avg P/L: {avg}", f"Trades: {count}"])

        writer.writerow([])
        writer.writerow(["P/L by Time of Day"])
        for hour, pnl_list in sorted(time_of_day_pnl.items()):
            total = round(sum(pnl_list), 2)
            avg = round(sum(pnl_list) / len(pnl_list), 2)
            count = len(pnl_list)
            writer.writerow([hour, f"Total P/L: {total}", f"Avg P/L: {avg}", f"Trades: {count}"])

        writer.writerow([])
        writer.writerow(["P/L by Symbol by Hour"])
        symbol_hour_pnl = defaultdict(lambda: defaultdict(list))
        for row in flat_log:
            symbol = row[0]
            hour = row[9].astimezone(mountain).hour
            symbol_hour_pnl[symbol][hour].append(row[8])

        writer.writerow(["Symbol", "Hour", "Total P/L", "Avg P/L", "Trades"])
        for symbol in sorted(symbol_hour_pnl):
            for hour in sorted(symbol_hour_pnl[symbol]):
                pnl_list = symbol_hour_pnl[symbol][hour]
                total = round(sum(pnl_list), 2)
                avg = round(sum(pnl_list) / len(pnl_list), 2)
                count = len(pnl_list)
                writer.writerow([symbol, f"{hour:02d}:00 - {hour + 1:02d}:00", total, avg, count])

    import matplotlib.pyplot as plt

    # Visualization: R/R Ratio vs P/L Scatter Plot
    rr_values = [row[10] for row in flat_log if row[10] is not None]
    pnl_values = [row[8] for row in flat_log if row[10] is not None]

    plt.figure(figsize=(10, 6))
    plt.scatter(rr_values, pnl_values, alpha=0.4, edgecolors='k')
    plt.title('R/R Ratio vs Profit/Loss per Trade')
    plt.xlabel('R/R Ratio')
    plt.ylabel('Profit / Loss')
    plt.grid(True)
    plt.axhline(0, color='red', linestyle='--')
    plt.show()  # Show interactive plot instead of saving
    # plt.close()  # Do not close to allow manipulation

    print("Scatter plot displayed interactively")
    # Save PnL and R/R values to CSV for analysis
    rr_export_file = f"rr_pnl_data_{timestamp_str}.csv"
    with open(rr_export_file, "w", newline="") as rr_file:
        rr_writer = csv.writer(rr_file)
        rr_writer.writerow(["R/R Ratio", "P/L"])
        for rr, pnl in zip(rr_values, pnl_values):
            rr_writer.writerow([rr, pnl])

    print(f"Saved R/R vs P/L data to {rr_export_file}")

    print(f"Total P/L: {total_pnl}")
    print(f"Win Rate: {win_rate}%")
    print(f"Portfolio Growth: ${growth} ({growth_pct}%)")
    # Collect daily stats and SPY returns
    from collections import defaultdict
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    spy_data = load_historical_data("SPY", start, end, timeframe=TimeFrame.Day)
    spy_returns = {bar.timestamp.date(): (bar.close - bar.open) / bar.open for bar in spy_data}

    daily_stats = defaultdict(lambda: {"count": 0, "wins": 0, "losses": 0, "pnl": 0.0})

    for row in flat_log:
        trade_date = row[9].date()
        daily_stats[trade_date]["count"] += 1
        daily_stats[trade_date]["pnl"] += row[8]
        if row[8] > 0:
            daily_stats[trade_date]["wins"] += 1
        else:
            daily_stats[trade_date]["losses"] += 1

    trade_stats_filename = f"daily_trade_stats_{timestamp_str}.csv"
    with open(trade_stats_filename, "w", newline="") as stats_file:
        stats_writer = csv.writer(stats_file)
        stats_writer.writerow(["Date", "Trades", "Wins", "Losses", "Total P/L", "SPY Return"])
        for day, stats in sorted(daily_stats.items()):
            spy_return = round(spy_returns.get(day, 0.0) * 100, 2)
            stats_writer.writerow(
                [day, stats["count"], stats["wins"], stats["losses"], round(stats["pnl"], 2), spy_return])

    # Histogram: Daily trade count and profitability
    import matplotlib.dates as mdates
    dates = list(daily_stats.keys())
    trade_counts = [daily_stats[day]["count"] for day in dates]
    daily_pnl = [daily_stats[day]["pnl"] for day in dates]

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(dates, trade_counts, color='skyblue', label='Trade Count')
    ax1.set_ylabel('Number of Trades', color='skyblue')
    ax1.tick_params(axis='y', labelcolor='skyblue')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.tick_params(axis='x', rotation=45)

    ax2 = ax1.twinx()
    ax2.plot(dates, daily_pnl, color='green', marker='o', label='P/L')
    ax2.set_ylabel('Daily P/L', color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    spy_series = [spy_returns.get(day, 0.0) * 100 for day in dates]
    ax3 = ax1.twinx()
    ax3.plot(dates, spy_series, color='orange', linestyle='--', label='SPY Return (%)')
    ax3.spines["right"].set_position(("outward", 60))
    ax3.set_ylabel("SPY Return (%)", color='orange')
    ax3.tick_params(axis='y', labelcolor='orange')

    plt.title("Daily Trade Count, Profitability, and SPY Return")
    fig.tight_layout()
    plt.show()

    print(f"Saved daily trade stats to {trade_stats_filename}")

    print(f"Results saved to {filename}")


# Main parallel backtest
if __name__ == "__main__":
    symbols = ["AMD", "JNJ", "KO", "XOM", "WMT", "TSLA", "JPM", "MCD", "BA", "CVX"]
    start = datetime(2025, 1, 1)
    end = datetime(2025, 6, 1)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda sym: run_backtest(sym, start, end), symbols))

        filename = input("Enter a name for the results file (without extension): ").strip()
    export_results(results, custom_filename=filename)
