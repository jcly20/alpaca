
import config
from alpaca.trading.client import TradingClient
from alpaca.trading.stream import TradingStream
from alpaca.trading.requests import GetAssetsRequest

client = TradingClient(config.API_KEY, config.SECRET_KEY, paper=True)
account = dict(client.get_account())
# for k,v in account.items() :
#     print(f"{k:30}{v}")

print("\ncash available : ", account['cash'])






