
# trading.py
import csv
import os
from account.authentication_paper import client
from config import POSITION_CSV
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

def submit_limit_order(symbol, qty, limit_price):
    order = LimitOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        type="limit",
        limit_price=round(limit_price, 2),
        time_in_force=TimeInForce.DAY
    )
    client.submit_order(order)


def load_open_positions():
    positions = {}
    if os.path.exists(POSITION_CSV):
        with open(POSITION_CSV, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                positions[row['symbol']] = row
    return positions


def save_open_position(symbol, entry, sl, tp, qty):
    file_exists = os.path.isfile(POSITION_CSV)
    with open(POSITION_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['symbol', 'entry', 'sl', 'tp', 'qty'])
        writer.writerow([symbol, round(entry, 2), round(sl, 2), round(tp, 2), qty])