import pandas as pd
from pandas.tseries.holiday import (
    AbstractHolidayCalendar, Holiday, nearest_workday,
    USMartinLutherKingJr, USPresidentsDay, USMemorialDay, 
    USLaborDay, USThanksgivingDay, GoodFriday
)
from datetime import datetime, time
import pytz
import sys

class NYSEHolidayCalendar(AbstractHolidayCalendar):
    rules = [
        Holiday('New Years Day', month=1, day=1, observance=nearest_workday),
        USMartinLutherKingJr,
        USPresidentsDay,
        GoodFriday,
        USMemorialDay,
        Holiday('Juneteenth', month=6, day=19, observance=nearest_workday),
        Holiday('US Independence Day', month=7, day=4, observance=nearest_workday),
        USLaborDay,
        USThanksgivingDay,
        Holiday('Christmas', month=12, day=25, observance=nearest_workday)
    ]

def is_market_open():
    # Convert UTC to US Eastern Time
    eastern = pytz.timezone('US/Eastern')
    now_et = datetime.now(pytz.utc).astimezone(eastern)
    today_et = now_et.date()
    time_et = now_et.time()
    
    # 1. Check if weekend
    if today_et.weekday() >= 5:
        print(f"DEBUG: Weekend ({today_et.strftime('%A')})")
        return False
        
    # 2. Check if NYSE Holiday
    cal = NYSEHolidayCalendar()
    holidays = cal.holidays(start=f"{today_et.year}-01-01", end=f"{today_et.year}-12-31")
    if today_et in holidays.date:
        print(f"DEBUG: NYSE Holiday ({today_et})")
        return False
        
    # 3. Check if Market Hours (9:30 AM - 4:00 PM ET)
    market_open = time(9, 30)
    market_close = time(16, 0)
    
    if not (market_open <= time_et <= market_close):
        print(f"DEBUG: Outside Market Hours ({time_et.strftime('%H:%M')} ET)")
        return False
        
    return True

if __name__ == "__main__":
    if is_market_open():
        print("Market is currently open and trading.")
        sys.exit(0)
    else:
        print("Market is currently closed.")
        sys.exit(1)
