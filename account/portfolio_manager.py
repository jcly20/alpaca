from alpaca.trading import GetOrdersRequest, QueryOrderStatus

from authentication_paper import client
from collections import defaultdict


#output all orders
account = client.get_account()

orders_resp = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, nested=True, limit=500))

orders = [order for order in orders_resp if order.filled_qty != '0' and order.legs is not None]
open_positions = [order for order in orders if order.legs[0].filled_at is None and order.legs[1].filled_at is None]
closed_positions = [order for order in orders if order not in open_positions and order.filled_qty != '0' and order.legs]

print(" -- open positions -- ")
for order in open_positions:
    print(f"\n{order.symbol}\n"
          f"\tentry: {order.filled_qty} shares @ {order.filled_avg_price}\n"
          f"\t tp: {order.legs[0].limit_price}\n"
          f"\t sl: {order.legs[1].stop_price}\n")


print(" -- closed positions -- \n")
print("Symbol, EntryDate, EntryPrice, StopLoss, TakeProfit, Position_RR, PositionSize, ExitPrice, Outcome, BarsHeld, PnL")

total_trades = 0
num_wins = 0
num_loss = 0
gross_profit = 0
gross_loss = 0
total_pnl = 0
barsHeld_avg = 0
barsHeld_win = 0
barsHeld_loss = 0
average_rr = 0

symbol_stats = defaultdict(lambda: {
    "trades": 0,
    "wins": 0,
    "losses": 0,
    "pnl": 0.0
})

for order in closed_positions:
    entry_date = order.filled_at
    entry_price = order.filled_avg_price
    sl = order.legs[1].stop_price
    tp = order.legs[0].limit_price
    position_size = order.filled_qty
    if order.legs[1].filled_at is not None:
        exit_price = order.legs[1].filled_avg_price
        outcome = "Stopped Out"
        bars_held = (order.legs[1].filled_at - order.filled_at).days + 1
        pnl = round((float(order.legs[1].filled_avg_price) - float(order.filled_avg_price)) * float(order.filled_qty), 2)

        gross_loss += pnl
        num_loss += 1
        barsHeld_loss += bars_held
    else:
        exit_price = order.legs[0].filled_avg_price
        outcome = "Target Hit"
        bars_held = (order.legs[0].filled_at - order.filled_at).days + 1
        pnl = round((float(order.legs[0].filled_avg_price) - float(order.filled_avg_price)) * float(order.filled_qty), 2)

        gross_profit += pnl
        num_wins += 1
        barsHeld_win += bars_held

    position_rr = round((float(order.filled_avg_price) - float(order.legs[1].stop_price)) / (float(order.legs[0].limit_price) - float(order.filled_avg_price)), 2)
    average_rr += position_rr
    barsHeld_avg += bars_held
    total_trades += 1
    total_pnl += pnl

    stats = symbol_stats[order.symbol]
    stats["trades"] += 1
    stats["pnl"] += pnl

    if pnl > 0:
        stats["wins"] += 1
    else:
        stats["losses"] += 1

    print(order.symbol,",",entry_date,",",entry_price,",",sl,",",tp,",",position_rr,",",position_size,",",exit_price,",",outcome,",",bars_held,",",pnl)


initial_capital = 10000
final_capital = round(initial_capital + total_pnl, 2)

print("\n--- Total Statistics ---")
print(f"\n\ntotal pnl: {round(total_pnl, 2)}\n"
      f"total trades: {total_trades}\n"
      f"win rate: {round((num_wins/total_trades)*100, 2)}\n"
      f"final capital: {final_capital}\n"
      f"total wins: {num_wins}\n"
      f"total loss: {num_loss}\n"
      f"gross profit: {round(gross_profit, 2)}\n"
      f"gross loss: {round(gross_loss, 2)}\n"
      f"theorhetical  R/R: {round(1/3, 2)}\n"
      f"actual R/R: {round(average_rr/total_trades, 2)}\n"
      f"average pnl: {round(total_pnl/total_trades)}\n"
      f"average win: {round(gross_profit/num_wins)}\n"
      f"average loss: {round(gross_loss/num_loss)}\n"
      f"average days held: {round(barsHeld_avg/total_trades)}\n"
      f"average days (wins): {round(barsHeld_win/num_wins)}\n"
      f"average days (loss): {round(barsHeld_loss/num_loss)}\n"
      f"pnl %: {round(((final_capital-initial_capital)/initial_capital)*100, 2)}")


print("\n--- Symbol Statistics ---")
for symbol, s in sorted(symbol_stats.items(), key=lambda x: x[1]["pnl"], reverse=True):

    win_rate = s["wins"] / s["trades"] * 100

    print(
        f"{symbol:6}"
        f" Trades:{s['trades']:3}"
        f" Wins:{s['wins']:3}"
        f" Losses:{s['losses']:3}"
        f" Win%:{win_rate:6.1f}"
        f" PnL:${s['pnl']:8.2f}"
    )








