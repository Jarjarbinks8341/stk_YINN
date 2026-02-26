#!/usr/bin/env python3
"""
Daily Update Script
===================

Run this script daily to:
1. Update YINN price data
2. Get current trading signal
3. Save signal to file for tracking

Usage:
    python daily_update_and_signal.py
"""
import sys
from datetime import datetime
from update_daily import update_latest
from production_strategy import get_trading_signal, YINNProductionStrategy
from backtest import load_data
import json

def main():
    print("=" * 80)
    print("DAILY YINN UPDATE")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Update data
    print("Step 1: Updating YINN price data...")
    print("-" * 80)
    try:
        update_latest()
        print("✅ Data updated successfully\n")
    except Exception as e:
        print(f"❌ Error updating data: {e}")
        print("Continuing with existing data...\n")

    # Step 2: Get trading signal
    print("\nStep 2: Generating trading signal...")
    print("-" * 80)
    signal_text = get_trading_signal()
    print(signal_text)

    # Step 3: Save signal to file for tracking
    print("\n" + "=" * 80)
    print("Step 3: Saving signal to file...")
    print("-" * 80)

    try:
        # Load data and get structured signal
        data = load_data()
        strategy = YINNProductionStrategy()
        signal_data = strategy.get_current_signal(data)

        if 'error' not in signal_data:
            # Create signal log entry
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'date': signal_data['date'].strftime('%Y-%m-%d'),
                'price': signal_data['current_price'],
                'signal': signal_data['signal'],
                'signal_strength': signal_data['signal_strength'],
                'support': signal_data['support'],
                'resistance': signal_data['resistance'],
                'position_in_range_pct': signal_data['position_in_range_pct'],
                'risk_reward_ratio': signal_data.get('risk_reward_ratio', 0)
            }

            # Append to signals log
            signals_file = 'data/signals_log.json'
            try:
                with open(signals_file, 'r') as f:
                    signals_log = json.load(f)
            except FileNotFoundError:
                signals_log = []

            signals_log.append(log_entry)

            with open(signals_file, 'w') as f:
                json.dump(signals_log, f, indent=2)

            print(f"✅ Signal saved to {signals_file}")

            # Also save latest signal separately
            latest_file = 'data/latest_signal.json'
            with open(latest_file, 'w') as f:
                json.dump(log_entry, f, indent=2)

            print(f"✅ Latest signal saved to {latest_file}")

        else:
            print(f"⚠️  Could not save signal: {signal_data['error']}")

    except Exception as e:
        print(f"❌ Error saving signal: {e}")

    print("\n" + "=" * 80)
    print("DAILY UPDATE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
