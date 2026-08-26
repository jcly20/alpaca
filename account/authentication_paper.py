
import os
import sys

from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.data.historical.stock import StockHistoricalDataClient
import finnhub

def load_credentials():

    load_dotenv()

    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    paperAcc = os.getenv("PAPERACC")
    liveAcc = os.getenv("LIVEACC")
    paperAccUUID = os.getenv("PAPERACCUUID")
    accUUID = os.getenv("ACCUUID")
    api_key = os.getenv("API_KEY")
    secret_key = os.getenv("SECRET_KEY")
    webhook = os.getenv("DISCORD_WEBHOOK")
    finnhub_key = os.getenv("FINNHUB_KEY")

    if not email or not password or not paperAcc or not liveAcc or not paperAccUUID or not accUUID or not api_key or not secret_key or not webhook or not finnhub_key:
        raise ValueError("Missing credentials in .env")

    return email, password, paperAcc, liveAcc, paperAccUUID, accUUID, api_key, secret_key, webhook, finnhub_key


def load_client(email, api_key, secret_key, finnhub_key):

    print(f"logging in as {email} ...")

    client = TradingClient(api_key, secret_key, paper=True)
    historicalClient = StockHistoricalDataClient(api_key, secret_key)
    finnhubClient = finnhub.Client(api_key=finnhub_key)
    account = dict(client.get_account())
    cash = account["cash"]
    status = account["status"]

    print(f"\nlogin successful!\naccount status : {status}\ncash available : ${cash}\n\nhappy trading!\n\n")

    return client, historicalClient, finnhubClient


#load credentials
email, password, paperAcc, liveAcc, paperAccUUID, accUUID, api_key, secret_key, webhook, finnhub_key = load_credentials()

#create client and historical client
try:
    client, historicalClient, finnhubClient = load_client(email, api_key, secret_key, finnhub_key)
except Exception as error:
    print("error creating client ...\nexiting program ...\ngoodbye!")
    sys.exit(str(error))

