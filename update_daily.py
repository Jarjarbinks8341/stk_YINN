"""Daily update script to fetch latest YINN data"""
from datetime import datetime, timedelta
from database import get_session, DailyPrice
import config
from fetch_data import fetch_and_store_data

def update_latest():
    """Fetch data from the last stored date to today"""
    session = get_session()

    try:
        # Get the latest date in database
        latest = session.query(DailyPrice).filter_by(ticker=config.TICKER).order_by(DailyPrice.date.desc()).first()

        if latest:
            # Start from the day after latest date
            start_date = (latest.date + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"Updating from {start_date} to today...")
        else:
            # No data exists, start from config start date
            start_date = config.START_DATE
            print(f"No existing data found. Fetching from {start_date}...")

        fetch_and_store_data(start_date=start_date)

    finally:
        session.close()

if __name__ == "__main__":
    update_latest()
