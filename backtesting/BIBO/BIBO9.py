import math
import random

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
    # url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    # resp = requests.get(url)
    # soup = BeautifulSoup(resp.text, "html.parser")
    # table = soup.find("table", {"id": "constituents"})
    # symbols = []
    # for row in table.find_all("tr")[1:]:
    #     cols = row.find_all("td")
    #     symbol = cols[0].text.strip().replace(".", "-")
    #     symbols.append(symbol)

    symbols = ['NVDA', 'TSLA', 'INTC', 'F', 'PLTR', 'AAPL', 'SMCI', 'AMZN', 'PFE', 'AMD', 'BAC', 'WBD', 'T', 'GOOGL', 'AVGO', 'CCL', 'MU', 'CMCSA', 'MSFT', 'UBER', 'AMCR', 'CSCO', 'VZ', 'WBA', 'HBAN', 'PCG', 'WMT', 'WFC', 'HPE', 'KO', 'KVUE', 'XOM', 'NKE', 'C', 'META', 'KMI', 'SLB', 'FCX', 'AES', 'MRK', 'CSX', 'KEY', 'NCLH', 'BMY', 'GM', 'CMG', 'OXY', 'HAL', 'NEE', 'VTRS', 'KDP', 'COIN', 'PYPL', 'SBUX', 'CVS', 'NEM', 'KHC', 'LUV', 'ORCL', 'DIS', 'DAL', 'SCHW', 'JPM', 'BA', 'LRCX', 'USB', 'MCHP', 'DVN', 'MRNA', 'PARA', 'HST', 'MO', 'DELL', 'QCOM', 'RF', 'CVX', 'ON', 'TFC', 'MDLZ', 'JNJ', 'EQT', 'HPQ', 'UAL', 'GILD', 'UNH', 'APH', 'COP', 'PG', 'DOW', 'APA', 'BKR', 'VST', 'AMAT', 'WMB', 'EXC', 'PEP', 'MDT', 'ANET', 'V', 'BSX', 'MS', 'WDC', 'CTRA', 'CRM', 'TXN', 'ABBV', 'TGT', 'ABT', 'MNST', 'CAG', 'VICI', 'IPG', 'KR', 'LVS', 'CNC', 'IP', 'PM', 'CNP', 'GE', 'GLW', 'DOC', 'RTX', 'EW', 'UPS', 'O', 'TJX', 'EBAY', 'ABNB', 'ENPH', 'DDOG', 'CZR', 'MGM', 'PPL', 'CPRT', 'FTNT', 'CL', 'CFG', 'MOS', 'MTCH', 'D', 'CRWD', 'SO', 'GIS', 'CARR', 'FITB', 'KIM', 'BEN', 'IVZ', 'DXCM', 'TPR', 'BAX', 'AIG', 'JCI', 'EL', 'IBM', 'PANW', 'KKR', 'DASH', 'DLTR', 'PLD', 'SW', 'BK', 'NI', 'DG', 'TMUS', 'FE', 'APO', 'BX', 'SRE', 'SYF', 'HON', 'WY', 'MMM', 'NFLX', 'GEN', 'LLY', 'CEG', 'COF', 'FOXA', 'ADI', 'XEL', 'CTSH', 'MCD', 'GEHC', 'DHR', 'ADM', 'OKE', 'DUK', 'TSCO', 'ADBE', 'HD', 'CTVA', 'EOG', 'INVH', 'FI', 'APTV', 'FAST', 'EIX', 'FIS', 'MET', 'BBY', 'GEV', 'FSLR', 'STX', 'SYY', 'AEP', 'CPB', 'DHI', 'PSX', 'EXE', 'VLO', 'NDAQ', 'SWKS', 'K', 'EMR', 'NRG', 'ICE', 'LYB', 'NWSA', 'CCI', 'ACN', 'VTR', 'WELL', 'CSGP', 'ALB', 'AXP', 'AMGN', 'ROST', 'EA', 'ETR', 'PGR', 'HWM', 'FTV', 'PEG', 'TER', 'NXPI', 'UNP', 'HRL', 'PCAR', 'MPC', 'LEN', 'ETN', 'OMC', 'MA', 'LW', 'WYNN', 'ZTS', 'IR', 'CAT', 'GPN', 'AMT', 'LOW', 'ES', 'WDAY', 'TSN', 'DD', 'ED', 'KMX', 'GS', 'HOLX', 'RCL', 'LYV', 'LULU', 'DECK', 'CMS', 'OTIS', 'LKQ', 'FANG', 'CF', 'NUE', 'CAH', 'BALL', 'KMB', 'CME', 'UDR', 'WEC', 'TAP', 'AFL', 'PNC', 'STT', 'EVRG', 'BDX', 'AKAM', 'MKC', 'COST', 'PHM', 'CDNS', 'SWK', 'DLR', 'YUM', 'TMO', 'PAYX', 'MMC', 'LIN', 'WSM', 'INCY', 'STZ', 'NTAP', 'EXPE', 'BRO', 'FDX', 'PPG', 'A', 'TRGP', 'HES', 'MAS', 'ZBH', 'CBRE', 'HUM', 'HSY', 'WRB', 'HLT', 'TTWO', 'IRM', 'EQR', 'CHD', 'ROL', 'DAY', 'HAS', 'COO', 'CI', 'ACGL', 'LNT', 'HSIC', 'BLDR', 'SHW', 'TEL', 'ADP', 'BG', 'ISRG', 'PRU', 'IQV', 'ODFL', 'CB', 'ALL', 'WM', 'ELV', 'INTU', 'HIG', 'MAR', 'AEE', 'SPG', 'TROW', 'IFF', 'STLD', 'COR', 'ADSK', 'NOW', 'TECH', 'CTAS', 'PNR', 'HCA', 'BIIB', 'NTRS', 'VRTX', 'XYL', 'JBL', 'CLX', 'TRMB', 'VLTO', 'GD', 'ARE', 'AJG', 'LMT', 'APD', 'SYK', 'BXP', 'DE', 'DRI', 'GDDY', 'TT', 'RJF', 'PFG', 'SJM', 'AME', 'GPC', 'AOS', 'DTE', 'CHRW', 'TRV', 'LDOS', 'TXT', 'CHTR', 'EXPD', 'EMN', 'AWK', 'NSC', 'CDW', 'SPGI', 'MTB', 'SNPS', 'ECL', 'PWR', 'AON', 'LHX', 'RSG', 'PNW', 'KLAC', 'FOX', 'TKO']

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


def find_signal_today(df, spy, current_date):

    if current_date not in df.index:
        return None

    idx = df.index.get_loc(current_date)
    if idx < 151:
        return None

    today = df.iloc[idx]
    yesterday = df.iloc[idx - 1]

    spy_today = spy.iloc[idx]

    cond1 = today["SMA50"] > today["SMA100"] > today["SMA150"]
    cond2 = yesterday["low"] < yesterday["SMA50"] < yesterday["close"]
    cond3 = today["close"] > yesterday["close"]
    cond4 = today["close"] > today["open"]
    cond5 = spy_today["close"] > spy_today["SMA150"]

    if cond1 and cond2 and cond3 and cond4 and cond5:
        return today

    return None


def simulate_market(start, end, market_data, spy_data, initial_capital, sl_multiple, tp_multiple, risk_perc):

    available_capital = capital = initial_capital
    signals_total = 0
    signals_taken = 0
    open_positions = []
    trade_log = []
    peak = capital
    max_drawdown = 0

    all_dates = pd.date_range(start=start, end=end, freq='B', tz="UTC")

    for current_date in all_dates:
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

        # Convert the items to a list and shuffle it
        items = list(market_data.items())
        random.shuffle(items)

        # Loop through randomized symbol-data pairs
        for symbol, df in items:

        #for symbol, df in market_data.items():

            #print(f"checking {symbol}")
            signal = find_signal_today(df, spy_data, current_date)

            if signal is None:
                continue

            if any(position.get("symbol") == symbol for position in open_positions):
                continue

            #print(f"signal found in {symbol}")
            signals_total += 1

            entry_price = signal["close"]
            atr = signal["ATR14"]
            stop_loss = entry_price - sl_multiple * atr
            take_profit = entry_price + tp_multiple * atr
            risk = risk_perc * capital
            diff = entry_price - stop_loss
            position_size = risk / diff if diff > 0 else 0
            required_capital = position_size * entry_price

            if required_capital <= available_capital and position_size > 0:
                #print(f"opening a position in {symbol} @ {entry_price} -- portfolio = {capital}")
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


def calculate_spy(start_date, end_date):
    symbol = "SPY"

    req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start_date, end=end_date)
    bars = historicalClient.get_stock_bars(req)[symbol]
    data = [{
        "timestamp": pd.to_datetime(bar.timestamp).normalize(),
        "symbol": symbol,
        "close": bar.close,
    } for bar in bars]

    df = pd.DataFrame(data).set_index("timestamp")

    # Performance
    spy_initial = df.iloc[0]["close"]
    spy_final = df.iloc[-1]["close"]
    position_size = math.floor(10000 / spy_initial)
    position_initial = position_size * spy_initial
    position_final = position_size * spy_final
    pnl = round(((position_final - position_initial) / 10000) * 100, 1)

    # Max drawdown
    cumulative = df["close"]
    peak = cumulative.cummax()
    drawdown = (peak - cumulative) / peak
    max_drawdown = round(drawdown.max() * 100, 2)

    return pnl, max_drawdown


def save_trades_to_csv(trades, initial_capital, final_capital, max_drawdown_pct, signals_total, signals_taken, spy_performance, spy_drawdown,
                       filename):
    if not trades:
        print("No trades to save.")
        return

    keys = list(trades[0].keys())
    risk_amount = input("% of portfolio risked: ").strip()
    strategy_description = input("short strategy description: ").strip()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        f.write(f"Strategy Description: {strategy_description}\n")
        f.write(f"Risk Amount per Trade: {risk_amount}\n")

        writer = csv.DictWriter(f, keys)
        writer.writeheader()
        writer.writerows(trades)

        total_pnl = sum(t["PnL"] for t in trades)
        num_trades = len(trades)
        wins = [t for t in trades if t["PnL"] > 0]
        win_rate = len(wins) / num_trades * 100 if num_trades > 0 else 0
        avg_pnl = total_pnl / num_trades if num_trades > 0 else 0
        avg_bars_held = sum(t["BarsHeld"] for t in trades) / num_trades if num_trades > 0 else 0
        pct_change = ((final_capital - initial_capital) / initial_capital) * 100

        f.write(f"Strategy Description:\n")
        f.write(f"Risk Amount per Trade: {risk_amount}\n")

        f.write("\nSummary:\n")
        f.write(f"Total PnL: {round(total_pnl, 2)}\n")
        f.write(f"Win Rate: {round(win_rate, 2)}%\n")
        f.write(f"Average PnL: {round(avg_pnl, 2)}\n")
        f.write(f"Average Bars Held: {round(avg_bars_held, 2)}\n")
        f.write(f"% Change: {round(pct_change, 2)}%\n")
        f.write(f"Max Drawdown (%): {round(max_drawdown_pct, 2)}%\n")
        f.write(f"Signals Total: {signals_total}\n")
        f.write(f"Signals Taken: {signals_taken}\n")
        f.write(f"Signals Taken (%): {round((signals_taken / signals_total) * 100, 2)}\n")
        f.write(f"SPY Performance: {spy_performance}%\n")
        f.write(f"SPY Drawdown: {spy_drawdown}%\n")
        f.write(f"Alpha: {round(pct_change - spy_performance, 2)}\n")


def save_parameter_stats_to_csv(stats, spy_performance, spy_drawdown, filename):

    if not stats:
        print("No trades to save.")
        return

    with open(filename, "w", newline="", encoding="utf-8") as f:

        for i in stats:

            trades = i["Trades"]
            initial_capital = i["InitialCapital"]
            final_capital = i["FinalCapital"]
            drawdown = i["Drawdown"]
            signals_total = i["SigTotal"]
            signals_taken = i["SigTaken"]
            sl_multiple = i["SLMult"]
            tp_multiple = i["TPMult"]
            risk = i["Risk"]

            f.write(f"\n\nStrategy Description:\n")
            f.write(f"Initial Capital: {initial_capital}\n")
            f.write(f"Risk Amount: {risk}\n")
            f.write(f"SL Multiple: {sl_multiple}\n")
            f.write(f"TP Multiple: {tp_multiple}\n")

            total_pnl = sum(t["PnL"] for t in trades)
            num_trades = len(trades)
            wins = [t for t in trades if t["PnL"] > 0]
            win_rate = len(wins) / num_trades * 100 if num_trades > 0 else 0
            avg_pnl = total_pnl / num_trades if num_trades > 0 else 0
            avg_bars_held = sum(t["BarsHeld"] for t in trades) / num_trades if num_trades > 0 else 0
            pct_change = ((final_capital - initial_capital) / initial_capital) * 100

            f.write("\nSummary:\n")
            f.write(f"Total PnL: {round(total_pnl, 2)}\n")
            f.write(f"Win Rate: {round(win_rate, 2)}%\n")
            f.write(f"Average PnL: {round(avg_pnl, 2)}\n")
            f.write(f"Average Bars Held: {round(avg_bars_held, 2)}\n")
            f.write(f"% Change: {round(pct_change, 2)}%\n")
            f.write(f"Max Drawdown (%): {round(drawdown, 2)}%\n")
            f.write(f"Signals Total: {signals_total}\n")
            f.write(f"Signals Taken: {signals_taken}\n")
            f.write(f"Signals Taken (%): {round((signals_taken / signals_total) * 100, 2)}\n")
            f.write(f"SPY Performance: {spy_performance}%\n")
            f.write(f"SPY Drawdown: {spy_drawdown}%\n")
            f.write(f"Alpha: {round(pct_change - spy_performance, 2)}\n")

if __name__ == "__main__":

    start_date = datetime(2021, 1, 1)
    end_date = datetime(2025, 6, 30)

    parameter_stats = []
    num_tests = 0

    symbols = get_sp500_symbols()
    market_data = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(fetch_data, symbol, start_date, end_date): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(futures):
            symbol = futures[future]
            try:
                df = future.result()
                df = add_indicators(df)
                market_data[symbol] = df
            except Exception as e:
                print(f"Error loading {symbol}: {e}")

    spy_data = fetch_data("SPY", start_date, end_date)
    spy_data = add_indicators(spy_data)

    initial_capital = [10000]
    for i in initial_capital:
        sl_multiple = [0.2, 0.4, 0.5]
        for s in sl_multiple:
            tp_multiple = [0.8, 1, 1.2]
            for t in tp_multiple:
                risk_perc = [0.005, 1]
                for r in risk_perc:

                    trades, final_capital, max_dd, signals_total, signals_taken = simulate_market(start_date, end_date, market_data, spy_data, i, s, t, r)
                    print(f"Test {num_tests}: Final Capital: {final_capital:.2f}, Max Drawdown: {max_dd:.2f}%, Trades: {len(trades)}")
                    stats = {"Trades":trades, "FinalCapital":final_capital, "Drawdown":max_dd, "SigTotal":signals_total, "SigTaken":signals_taken, "InitialCapital": i, "SLMult":s, "TPMult":t, "Risk":r}
                    parameter_stats.append(stats)
                    num_tests += 1

    spy_performance, spy_drawdown = calculate_spy(start_date, end_date)
    filename = input("Enter a name for the results file (without extension): ").strip() + ".csv"
    save_parameter_stats_to_csv(parameter_stats, spy_performance, spy_drawdown, filename)
    print(f"Saved stats to {filename}")
