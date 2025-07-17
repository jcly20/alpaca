

from account.authentication_paper import client, historicalClient


def showAccountInfo():
    account = dict(client.get_account())

    print("\ncash available : $", account['cash'])

    assets = [asset for asset in client.get_all_positions()]
    positions = [(asset.symbol, asset.qty, asset.current_price) for asset in assets]
    print("\nPostions")
    print(f"{'Symbol':9}{'Qty':>4}{'Value':>15}")
    print('-' * 28)
    for position in positions:
        print(f"{position[0]:9}{int(position[1]):>4}{int(position[1]) * float(position[2]):>15.2f}")

    # Get our account information.
    account = client.get_account()

    # Check our current balance vs. our balance at the last market close
    balanceChange = round(float(account.equity) - float(account.last_equity), 2)
    print(f"\nToday\'s change: ${balanceChange}")



