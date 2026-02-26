"""Fetch YINN data and store in database"""
import yfinance as yf
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import config
from database import init_db, get_session, DailyPrice

def fetch_and_store_data(ticker=config.TICKER, start_date=config.START_DATE, end_date=None):
    """
    Fetch historical data for ticker and store in database

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (default: today)
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    print(f"Fetching {ticker} data from {start_date} to {end_date}...")

    # Initialize database
    init_db()
    session = get_session()

    try:
        # Fetch data from yfinance
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)

        if df.empty:
            print(f"No data found for {ticker}")
            return

        print(f"Retrieved {len(df)} rows of data")

        # Store each row in database
        new_records = 0
        updated_records = 0

        for date, row in df.iterrows():
            try:
                # Check if record already exists
                existing = session.query(DailyPrice).filter_by(
                    ticker=ticker,
                    date=date.date()
                ).first()

                if existing:
                    # Update existing record
                    existing.open = float(row['Open'])
                    existing.high = float(row['High'])
                    existing.low = float(row['Low'])
                    existing.close = float(row['Close'])
                    existing.volume = int(row['Volume'])
                    existing.adj_close = float(row['Close'])  # yfinance returns adjusted prices by default
                    updated_records += 1
                else:
                    # Create new record
                    price_record = DailyPrice(
                        ticker=ticker,
                        date=date.date(),
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(row['Volume']),
                        adj_close=float(row['Close'])
                    )
                    session.add(price_record)
                    new_records += 1

            except Exception as e:
                print(f"Error processing row for {date}: {e}")
                continue

        session.commit()
        print(f"Successfully stored data: {new_records} new records, {updated_records} updated")

        # Display summary
        total_records = session.query(DailyPrice).filter_by(ticker=ticker).count()
        latest = session.query(DailyPrice).filter_by(ticker=ticker).order_by(DailyPrice.date.desc()).first()
        earliest = session.query(DailyPrice).filter_by(ticker=ticker).order_by(DailyPrice.date.asc()).first()

        print(f"\nDatabase summary for {ticker}:")
        print(f"Total records: {total_records}")
        if earliest and latest:
            print(f"Date range: {earliest.date} to {latest.date}")
            print(f"Latest close: ${latest.close:.2f}")

    except Exception as e:
        print(f"Error fetching data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fetch_and_store_data()
