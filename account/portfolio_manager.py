from alpaca.trading import GetOrdersRequest, QueryOrderStatus

from authentication_paper import client

#output all orders
account = client.get_account()


orders_resp = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, nested=True, limit=500))

# for order in orders_resp:
#     print(order)

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
print("Symbol, EntryDate, EntryPrice, StopLoss, TakeProfit, PositionSize, ExitPrice, Outcome, BarsHeld, PnL")

total_trades = 0
num_wins = 0
num_loss = 0
gross_profit = 0
gross_loss = 0
total_pnl = 0
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
    else:
        exit_price = order.legs[0].filled_avg_price
        outcome = "Target Hit"
        bars_held = (order.legs[0].filled_at - order.filled_at).days + 1
        pnl = round((float(order.legs[0].filled_avg_price) - float(order.filled_avg_price)) * float(order.filled_qty), 2)

        gross_profit += pnl
        num_wins += 1

    total_trades += 1
    total_pnl += pnl

    print(order.symbol,",",entry_date,",",entry_price,",",sl,",",tp,",",position_size,",",exit_price,",",outcome,",",bars_held,",",pnl)


initial_capital = 10000
final_capital = round(initial_capital + total_pnl, 2)

print(f"\n\ntotal pnl: {round(total_pnl, 2)}\n"
      f"total trades: {total_trades}\n"
      f"win rate: {round((num_wins/total_trades)*100, 2)}\n"
      f"final capital: {final_capital}\n"
      f"total wins: {num_wins}\n"
      f"gross profit: {round(gross_profit, 2)}\n"
      f"gross loss: {round(gross_loss, 2)}\n"
      f"theorhetical  R/R: {round(1/3, 2)}\n"
      f"actual R/R: {round(-1*gross_loss/gross_profit, 2)}\n"
      f"average pnl: {round(total_pnl/total_trades)}\n"
      f"average win: {round(gross_profit/num_wins)}\n"
      f"average loss: {round(gross_loss/num_loss)}\n"
      f"pnl %: {round(((final_capital-initial_capital)/initial_capital)*100, 2)}")








