
import os
import alpaca

from alpaca.trading.client import TradingClient

from dotenv import load_dotenv


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

    if not email or not password or not paperAcc or not liveAcc or not paperAccUUID or not accUUID or not api_key or not secret_key:
        raise ValueError("Missing credentials in .env")

    return email, password, paperAcc, liveAcc, paperAccUUID, accUUID, api_key, secret_key


def load_client(email, api_key, secret_key):

    print(f"logging in as {email} ...")

    client = TradingClient(api_key, secret_key, paper=True)
    account = dict(client.get_account())
    cash = account["cash"]
    status = account["status"]

    print(f"\nlogin successful!\naccount status : {status}\ncash available : ${cash}\n\nhappy trading!\n\n")

    return client
