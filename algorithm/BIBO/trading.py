
# trading.py

import sys
import os

from notification import send_discord_alert
from config import POSITION_CSV
from logger import logger
from account.authentication_paper import client

import csv
from _datetime import datetime

from alpaca.trading.requests import OrderRequest, TakeProfitRequest, StopLossRequest, LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce, OrderClass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


def submit_order(capital, symbol, qty, entry, sl, tp):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    order_request = LimitOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
        limit_price=entry,
        order_class=OrderClass.BRACKET,
        take_profit=TakeProfitRequest(limit_price=tp),
        stop_loss=StopLossRequest(stop_price=sl)
    )
    order = client.submit_order(order_request)

    total_risk = qty * (entry - sl)

    print(f"placing an order: {symbol}")
    logger.info(f"order placed for {symbol} @ {timestamp}: {qty} @ {entry} per share ")
    message = (
        f"\t Order Placed for {symbol} @ ${entry:.2f} | SL: ${sl:.2f} | TP: ${tp:.2f}\n"
        f"\t\t Account Balance: ${capital:.2f} | Risked: ${total_risk:.2f} | Qty: {qty}\n"
        f"\t\t {timestamp}"
    )
    send_discord_alert(message)

    save_position(capital, symbol, timestamp, entry, sl, tp, qty, total_risk)


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
        logger.error(f"Error fetching positions from Alpaca: {e}")

    return positions


def load_bto_orders():
    orders = []

    try:
        open_orders = client.get_orders(GetOrdersRequest(status="open", side=OrderSide.BUY))
        for order in open_orders:
            symbol = order.symbol
            orders.append(symbol)
    except Exception as e:
        logger.error(f"Error fetching positions from Alpaca: {e}")

    return orders


def save_position(capital, symbol, timestamp, entry, sl, tp, qty, total_risk):
    file_exists = os.path.isfile(POSITION_CSV)
    with open(POSITION_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['time_stamp', 'capital', 'symbol', 'entry', 'sl', 'tp', 'qty', 'total_risk'])
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