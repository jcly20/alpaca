
# notification.py
import requests
from config import DISCORD_WEBHOOK_URL

def send_discord_alert(message):
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Discord message: {e}")


#send_discord_alert("✅ Test alert: BIBO bot is connected!")
