
import os
import sys

from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.data.historical.stock import StockHistoricalDataClient

def load_credentials():

    load_dotenv()

    email = os.getenv("email")
    password = os.getenv("pw")
    paperAcc = os.getenv("paperAcc")
    liveAcc = os.getenv("liveAcc")
    paperAccUUID = os.getenv("paperAccUUID")
    accUUID = os.getenv("accUUID")
    api_key = os.getenv("API_KEY")
    secret_key = os.getenv("SECRET_KEY")
    webhook = os.getenv("DISCORD_WEBHOOK")

    if not email or not password or not paperAcc or not liveAcc or not paperAccUUID or not accUUID or not api_key or not secret_key:
        raise ValueError("Missing credentials in .env")

    return email, password, paperAcc, liveAcc, paperAccUUID, accUUID, api_key, secret_key, webhook


def load_client(email, api_key, secret_key):

    print(f"logging in as {email} ...")

    client = TradingClient(api_key, secret_key, paper=True)
    historicalClient = StockHistoricalDataClient(api_key, secret_key)
    account = dict(client.get_account())
    cash = account["cash"]
    status = account["status"]

    print(f"\nlogin successful!\naccount status : {status}\ncash available : ${cash}\n\nhappy trading!\n\n")

    return client, historicalClient


#load credentials
email, password, paperAcc, liveAcc, paperAccUUID, accUUID, api_key, secret_key, webhook = load_credentials()

#create client and historical client
try:
    client, historicalClient = load_client(email, api_key, secret_key)
except Exception as error:
    print("error creating client ...\nexiting program ...\ngoodbye!")
    sys.exit(str(error))

