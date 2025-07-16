
#config.py
BASE_URL = "https://paper-api.alpaca.markets"

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1395151086612123799/djv1NNY5tMxHQ03vYBZnyXfR-OqoXmcTu5rES1pgFMlIRWVBkO8H6v2tnyRGbDHiBidm"

POSITION_CSV = "open_positions.csv"
TRADE_LOG_CSV = "trade_log.csv"

SYMBOLS = ["AAPL", "MSFT", "NVDA", "SPY"]  # Replace with full SP500 list if needed

RISK_PER_TRADE = 0.01
ATR_STOP_MULT = 0.4
ATR_TP_MULT = 1.2

SCHEDULE_HOUR = 13
SCHEDULE_MINUTE = 50  # 10 mins before market close





