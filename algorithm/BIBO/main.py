

# main.py

import sys
import os

from config import SCHEDULE_HOUR, SCHEDULE_MINUTE, MST
from notification import send_discord_alert
from strategy import run_strategy
from trading import account_info
from logger import logger

from datetime import datetime, time
import time as t

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

#reconfigure captial allocation


def scheduled_run():

    openPositions, capital, portfolioValue = account_info()
    dailyUpdate = f"Total Capital: {capital}\n"
    dailyUpdate += f"Portfolio Value: {portfolioValue}\n"
    dailyUpdate += "".join(f"\t{symbol:<5} - {pnl:>7.2f}\n" for symbol, pnl in openPositions.items())
    send_discord_alert(dailyUpdate)
    logger.info(dailyUpdate)

    try:
        timestamp = datetime.now(tz=MST).strftime("%Y-%m-%d %H:%M")
        logger.info(f"Running BIBO Strategy Scan: {timestamp} -- ")
        send_discord_alert(f"🚀 BIBO started at {timestamp}")

        run_strategy()

        logger.info("BIBO Strategy Scan completed successfully.")
        timestamp = datetime.now(tz=MST).strftime("%H:%M")
        send_discord_alert(f"✅ BIBO completed at {timestamp}")

    except Exception as e:
        logger.error("BIBO failed to scan", exc_info=True)
        timestamp = datetime.now(tz=MST).strftime("%H:%M")
        send_discord_alert(f"❗ BIBO failed at {timestamp}")


if __name__ == "__main__":
    timestamp = datetime.now(tz=MST).strftime("%Y-%m-%d %H:%M")
    logger.info(f"\n\n\n -- booting application: {timestamp} -- ")
    send_discord_alert(f" -- booting application: {timestamp} -- ")

    timecheck = datetime.now(tz=MST).time()
    while not time(13, 48) <= timecheck < time(13, 58):
        logger.info(f"-- delay BIBO: {timecheck.strftime('%H:%M')} -- ")
        t.sleep(120)
        timecheck = datetime.now(tz=MST).time()

    scheduled_run()

