# logger.py

import logging
import os


import os
import logging

from config import LOG_DIR, LOG_FILE


os.makedirs(LOG_DIR, exist_ok=True)

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
