import math
import random
import pandas as pd
import concurrent.futures
from datetime import datetime, timedelta
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from account.authentication_paper import historicalClient
import csv
import pytz

MST = pytz.timezone("America/Denver")
EST = pytz.timezone("America/New_York")


def get_sp500_symbols():
    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', "F", "MMM", "AMD", "WM", "SLM", "SEIC", "KO", "IDXX", "PG"]  # Reduced list for speed


def fetch_intraday_data(symbol, start, end):
    req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Minute, start=start, end=end)
    bars = historicalClient.get_stock_bars(req)[symbol]
    data = [{
        "timestamp": pd.to_datetime(bar.timestamp).tz_convert(EST).tz_convert(MST),
        "symbol": symbol,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
    } for bar in bars]
    df = pd.DataFrame(data).set_index("timestamp")
    df = df.between_time("07:30", "14:00")  # NYSE 9:30-16:00 in MST
    return df


def find_orb_signal_and_execute(df, current_date, capital):

    day_data = df[df.index.date == current_date.date()]
    if len(day_data) < 16:
        return None, capital

    opening_range = day_data.iloc[:15]
    high = opening_range["high"].max()
    low = opening_range["low"].min()

    trade_data = day_data.iloc[15:]
    entry = stop = target = entry_time = range = None
    for t, row in trade_data.iterrows():
        if entry is None and row["high"] > high:
            entry = high
            range = round(high - low, 2)
            stop = high - (range / 4)
            target = high + (range)
            entry_time = t
            break

    if entry is None:
        return None, capital

    position_size = (0.005 * capital) / (entry - stop) if (entry - stop) > 0 else 0
    qty = math.floor(position_size)
    cost_basis = round(qty * entry, 2)

    for t, row in trade_data[trade_data.index > entry_time].iterrows():
        if row["low"] <= stop:
            exit_price = stop
            pnl = (exit_price - entry) * qty
            capital += pnl
            return {
                "EntryTime": entry_time.strftime("%Y-%m-%d %H:%M"),
                "Symbol": df["symbol"].iloc[0],
                "Entry": round(entry, 2),
                "Stop": round(stop, 2),
                "Target": round(target, 2),
                "Qty": qty,
                "Range": range,
                "PositionSize": round(position_size, 2),
                "CostBasis": cost_basis,
                "Outcome": "Stop",
                "ExitTime": t.strftime("%Y-%m-%d %H:%M"),
                "Exit": round(exit_price, 2),
                "PnL": round(pnl, 2)
            }, capital
        elif row["high"] >= target:
            exit_price = target
            pnl = (exit_price - entry) * qty
            capital += pnl
            return {
                "EntryTime": entry_time.strftime("%Y-%m-%d %H:%M"),
                "Symbol": df["symbol"].iloc[0],
                "Entry": round(entry, 2),
                "Stop": round(stop, 2),
                "Target": round(target, 2),
                "Qty": qty,
                "Range": range,
                "PositionSize": round(position_size, 2),
                "CostBasis": cost_basis,
                "Outcome": "Target",
                "ExitTime": t.strftime("%Y-%m-%d %H:%M"),
                "Exit": round(exit_price, 2),
                "PnL": round(pnl, 2)
            }, capital

    return None, capital


def simulate_orb(start, end):
    symbols = get_sp500_symbols()
    market_data = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(fetch_intraday_data, symbol, start, end): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(futures):
            symbol = futures[future]
            try:
                market_data[symbol] = future.result()
            except Exception as e:
                print(f"Error loading {symbol}: {e}")

    initial_capital = 10000
    capital = initial_capital
    trade_log = []
    win_count = 0

    all_dates = pd.date_range(start=start, end=end, freq='B', tz=MST)

    for current_date in all_dates:
        for symbol, df in market_data.items():
            trade, capital = find_orb_signal_and_execute(df, current_date, capital)
            if trade:
                trade_log.append(trade)
                if trade["PnL"] > 0:
                    win_count += 1

    return trade_log, capital, initial_capital, win_count


def save_trades_to_csv(trades, initial_capital, final_capital, win_count, filename, strategy_description):
    with open(filename, "w", newline="", encoding="utf-8") as f:

        f.write(f"Strategy Description: {strategy_description}\n\n")

        header = f"{'EntryTime':<18} {'Symbol':<6} {'Entry':>7} {'Stop':>7} {'Target':>7} {'Qty':>4} {'Range':>6} {'PosSize':>9} {'CostBasis':>10} {'Outcome':<8} {'ExitTime':<18} {'Exit':>7} {'PnL':>7}"
        f.write(header + "\n")
        f.write("-" * len(header) + "\n")

        for trade in trades:
            f.write(
                f"{trade['EntryTime']:<18} {trade['Symbol']:<6} {trade['Entry']:>7.2f} {trade['Stop']:>7.2f} {trade['Target']:>7.2f} "
                f"{trade['Qty']:>4} {trade['Range']:>6} {trade['PositionSize']:>9.2f} {trade['CostBasis']:>10.2f} {trade['Outcome']:<8} "
                f"{trade['ExitTime']:<18} {trade['Exit']:>7.2f} {trade['PnL']:>7.2f}\n"
            )

        total_pnl = final_capital - initial_capital
        f.write("\nSummary:\n")
        f.write(f"Strategy Description: {strategy_description}\n\n")
        f.write(f"Initial Capital: {initial_capital}\n")
        f.write(f"Final Capital: {round(final_capital, 2)}\n")
        f.write(f"Total PnL: {round(total_pnl, 2)}\n")
        f.write(f"PnL %: {round(((final_capital-initial_capital)/initial_capital)*100, 2)}%\n")
        f.write(f"Number of Trades: {len(trades)}\n")
        f.write(f"Winning Trades: {win_count}\n")
        f.write(f"Win Rate: {round((win_count/len(trades)*100), 2)}%\n")


if __name__ == "__main__":
    start_date = datetime(2025, 7, 14, tzinfo=MST)
    end_date = datetime(2025, 8, 1, tzinfo=MST)
    trades, final_capital, initial_capital, win_count = simulate_orb(start_date, end_date)
    filename = input("Enter a name for the results file (without extension): ").strip() + ".csv"
    strategy_description = input("short strategy description: ").strip()
    save_trades_to_csv(trades, initial_capital, final_capital, win_count, filename, strategy_description)
    print(f"Saved {len(trades)} trades to {filename}")
