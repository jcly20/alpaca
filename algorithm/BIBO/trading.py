
# trading.py

import sys
import os

# Add the root of your repo (2 levels up from main.py)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from notification import send_discord_alert
from config import POSITION_CSV
from account.authentication_paper import client

import csv
from _datetime import datetime


def submit_order(capital, symbol, qty, entry, sl, tp):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    order = client.submit_order(
        symbol=symbol,
        qty=qty,
        side="buy",
        type="limit",
        limit_price=entry,
        time_in_force="gtc",
        order_class="bracket",
        take_profit={"limit_price": tp},
        stop_loss={"stop_price": sl}
    )
    client.submit_order(order)

    total_risk = qty * (entry - sl)
    save_position(capital, symbol, timestamp, entry, sl, tp, qty, total_risk)

    message = (
        f"📈 Limit Order Placed for {symbol} @ ${entry:.2f} | SL: ${sl:.2f} | TP: ${tp:.2f}\n"
        f"💰 Account Balance: ${capital:.2f} | Risked: ${total_risk:.2f} | Qty: {qty}\n"
        f"🕒 {timestamp}"
    )
    send_discord_alert(message)


def load_open_positions():
    positions = {}

    try:
        alpaca_positions = client.get_all_positions()
        for pos in alpaca_positions:
            symbol = pos.symbol
            positions[symbol] = {
                'symbol': symbol,
                'qty': pos.qty,
                'avg_entry_price': pos.avg_entry_price,
                'current_price': pos.current_price,
                'unrealized_pl': pos.unrealized_pl,
                'market_value': pos.market_value
            }
    except Exception as e:
        print(f"Error fetching positions from Alpaca: {e}")

    return positions


def save_position(capital, symbol, timestamp, entry, sl, tp, qty, total_risk):
    file_exists = os.path.isfile(POSITION_CSV)
    with open(POSITION_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['capital', 'symbol', 'time_stamp', 'entry', 'sl', 'tp', 'qty', 'total_risk'])
        writer.writerow([round(capital, 2), symbol, timestamp, round(entry, 2), round(sl, 2), round(tp, 2), qty, round(total_risk, 2)])


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