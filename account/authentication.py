
import os
import alpaca

from alpaca.trading.client import TradingClient
from alpaca.trading.stream import TradingStream
from alpaca.trading.requests import GetAssetsRequest

from dotenv import load_dotenv



load_dotenv()

email = os.getenv("email")
password = os.getenv("pw")

api_key = os.getenv("API_KEY")
secret_key = os.getenv("SECRET_KEY")

if not email or not password:
    raise ValueError("Missing BROKER_USERNAME or BROKER_PASSWORD in .env")

print(f"Logging in as {email}...")

client = TradingClient(api_key, secret_key, paper=True)

account = dict(client.get_account())
# for k,v in account.items() :
#     print(f"{k:30}{v}")

print("\ncash available : ", account['cash'])
