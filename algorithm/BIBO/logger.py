# logger.py

import logging
import os


import os
import logging

# Get absolute path to 'logs/trading.log' relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "trading.log")

# Create a single logger instance
logger = logging.getLogger("alpaca_trader")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers if logger is imported multiple times
if not logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE, mode='a')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
