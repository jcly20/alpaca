

# main.py

import sys
import os

# Add the root of your repo (2 levels up from main.py)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config import SCHEDULE_HOUR, SCHEDULE_MINUTE
from notification import send_discord_alert
from strategy import run_strategy
from trading import account_info

from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import logging



logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

scheduler = BlockingScheduler()

#@scheduler.scheduled_job('cron', day_of_week='mon-fri', hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE) #10 minutes before close
#@scheduler.scheduled_job('cron', day_of_week='mon-fri', hour=12, minute=38) #custom
def scheduled_run():

    openPositions, capital, portfolioValue = account_info()
    dailyUpdate = f"Total Capital: {capital}\n"
    dailyUpdate += f"Portfolio Value: {portfolioValue}\n"
    dailyUpdate += "".join(f"\t{symbol:<5} - {pnl:>7.2f}\n" for symbol, pnl in openPositions.items())
    send_discord_alert(dailyUpdate)

    logging.info("Running BIBO Strategy Scan...")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    send_discord_alert(f"🚀 BIBO started at {timestamp}")

    try:

        run_strategy()
        logging.info("BIBO Strategy Scan completed successfully.")
        timestamp = datetime.now().strftime("%H:%M")
        send_discord_alert(f"✅ BIBO completed at {timestamp}")

    except Exception as e:
        logging.error("BIBO failed to scan", exc_info=True)
        timestamp = datetime.now().strftime("%H:%M")
        send_discord_alert(f"❗ BIBO failed at {timestamp}")


if __name__ == "__main__":
    logging.info("Starting BIBO Scheduler...")

    #scheduler.start()

    scheduled_run()