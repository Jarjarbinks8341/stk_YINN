import pandas as pd
import numpy as np
from production_strategy import YINNProductionStrategy
from backtest import load_data
from datetime import datetime
import pytz

def calculate_technical_indicators(data):
    # MA200
    data['MA200'] = data['close'].rolling(window=200).mean()
    
    # RSI (14)
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    avg_gain = gain.copy()
    avg_loss = loss.copy()
    for i in range(14, len(data)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * 13 + gain.iloc[i]) / 14
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * 13 + loss.iloc[i]) / 14
    
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Price Drops
    data['1d_drop'] = data['close'].pct_change(1) * 100
    data['5d_drop'] = data['close'].pct_change(5) * 100
    
    return data

def generate_notification_report(panic_score, recommendation, details, current_price, rsi, d1_drop, support):
    """Formats the report for a notification service."""
    header = "🚨 YINN PANIC ALERT 🚨" if panic_score > 0 else "📊 YINN DAILY STATUS 📊"
    report = [
        header,
        f"Time: {datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M ET')}",
        f"Price: ${current_price:.2f} ({d1_drop:+.1f}%)",
        f"RSI: {rsi:.1f}",
        f"Panic Score: {panic_score}/100",
        "-" * 20,
        f"STRATEGY: {recommendation}",
        f"ADVICE: {details}",
        f"Target Support: ${support:.2f}",
        "-" * 20,
    ]
    if panic_score > 0:
        report.append("Check your account to execute.")
    else:
        report.append("No immediate action required.")
    return "\n".join(report)

def analyze_panic_levels(capital=15000, send_notif=False):
    data = load_data()
    data = calculate_technical_indicators(data)
    
    strategy = YINNProductionStrategy(lookback=60)
    prod_result = strategy.get_current_signal(data)
    
    curr = data.iloc[-1]
    current_price = curr['close']
    ma200 = curr['MA200']
    rsi = curr['RSI']
    d1_drop = curr['1d_drop']
    d5_drop = curr['5d_drop']
    support = prod_result['support']
    
    # Panic Score Calculation (0-100)
    panic_score = 0
    if rsi < 30: panic_score += 40
    if rsi < 20: panic_score += 20
    if d1_drop < -5: panic_score += 20
    if d5_drop < -10: panic_score += 20
    
    dist_to_ma200 = ((current_price - ma200) / ma200) * 100 if not pd.isna(ma200) else 0
    
    # Strategy Selection Logic
    if panic_score >= 60:
        recommendation = "EXTREME PANIC - AGGRESSIVE PUT SELL"
        strike = round(support)
        contracts = int(capital // (strike * 100))
        details = f"Sell {contracts} contracts at ${strike:.2f}. Support is holding, but fear is at peak. High premiums available."
    elif panic_score >= 40:
        recommendation = "MODERATE PANIC - CONSERVATIVE PUT SELL"
        strike = int(support * 0.95) # 5% below support
        contracts = int(capital // (strike * 100))
        details = f"Sell {contracts} contracts at ${strike:.2f}. Play it safe, wait for the floor to confirm."
    else:
        recommendation = "NO PANIC DETECTED - HOLD CASH"
        details = "Wait for better entry or a sharper drop to collect higher premiums."
        strike = None

    report = generate_notification_report(panic_score, recommendation, details, current_price, rsi, d1_drop, support)
    print(report)
    
    # Trigger Notification logic in GitHub Actions
    # This print will be caught by the grep in panic_monitor.yml

if __name__ == "__main__":
    analyze_panic_levels(15000, send_notif=True)
