
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pandas as pd
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from account.authentication_paper import historicalClient

# Define the time range: last 2 years
end_date = datetime.now()
start_date = end_date - timedelta(days=730)

# Create request for VIX data using the ^VIX symbol
symbol = "VIX"
request_params = StockBarsRequest(
    symbol_or_symbols=symbol,
    timeframe=TimeFrame.Day,
    start=start_date,
    end=end_date,
)

# Fetch the data
bars = historicalClient.get_stock_bars(request_params)

# Convert to DataFrame - bars is a dict-like object keyed by symbol
bars_data = bars[symbol]
vix_df = pd.DataFrame([{
    "timestamp": pd.to_datetime(bar.timestamp).normalize(),
    "open": bar.open,
    "high": bar.high,
    "low": bar.low,
    "close": bar.close,
    "volume": bar.volume
} for bar in bars_data]).set_index("timestamp")

print(f"VIX data fetched: {len(vix_df)} rows")
print(f"Date range: {vix_df.index.min()} to {vix_df.index.max()}")
print("\nFirst few rows:")
print(vix_df.head())
print("\nDataFrame info:")
print(vix_df.info())







