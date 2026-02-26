import os
import requests
import sys

def send_to_telegram(message):
    """Sends notification via Telegram bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("INFO: Telegram bot token or chat ID not set. Skipping notification.")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': f"```\n{message}\n```", # Use code blocks for better formatting
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Telegram notification sent successfully.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to send Telegram notification: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = sys.argv[1]
        success = send_to_telegram(message)
        if not success:
            # Exit with 0 even if it fails to avoid breaking the GitHub Action job
            # unless you want the job to show as failed.
            sys.exit(0) 
    else:
        print("No message provided.")
