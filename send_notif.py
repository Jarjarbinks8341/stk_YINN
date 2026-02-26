import os
import requests
import sys

def send_to_telegram(message):
    """Example function for sending notification via Telegram bot."""
    # To use this, you'll need to set the environment variables
    # TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your GitHub Secrets.
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print("Telegram notification sent successfully.")
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")
    else:
        print("Telegram bot token or chat ID not set. Skipping notification.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = sys.argv[1]
        # send_to_telegram(message)
        # Add your preferred notification service here!
        print(f"SIMULATED NOTIFICATION:
{message}")
    else:
        print("No message provided.")
