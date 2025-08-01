# logger.py

import logging
import os

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Create a single logger instance
logger = logging.getLogger("alpaca_trader")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers if logger is imported multiple times
if not logger.handlers:
    file_handler = logging.FileHandler("logs/trading.log", mode='a')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
