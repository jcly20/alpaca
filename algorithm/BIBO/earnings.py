import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import finnhub
import pandas as pd
from config import BASE_DIR
from datetime import datetime, timedelta, time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

spy_holdings = pd.read_excel(os.path.join(BASE_DIR, "spy_holdings.xlsx"), skiprows=4)
spy_symbols = spy_holdings["Ticker"].dropna().tolist()
print(spy_symbols)
print(len(spy_symbols))

from account.authentication_paper import finnhubClient, client

finnhubClient = finnhubClient

today = datetime.now().date()
earnings_date = datetime.now().date() + timedelta(days=4)

for symbol in spy_symbols:
    earnings = finnhubClient.earnings_calendar(_from=today, to=earnings_date, symbol=symbol, international=False)

    if earnings['earningsCalendar'] :
        print(earnings['earningsCalendar'][0]['symbol'] + " -- " + earnings['earningsCalendar'][0]['date'])
    else :
        print("no earnings")
