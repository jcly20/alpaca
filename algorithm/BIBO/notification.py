
# notification.py

import sys
import os

# Add the root of your repo (2 levels up from main.py)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from account.authentication_paper import webhook as discord_webhook

import requests


def send_discord_alert(message):
    payload = {"content": message}
    try:
        response = requests.post(discord_webhook, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Discord message: {e}")


#send_discord_alert("✅ Test alert: BIBO bot is connected!")
