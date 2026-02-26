#!/usr/bin/env python3
"""
Quick script to get current YINN trading signal

Usage:
    python get_signal.py
    or
    ./get_signal.py (if made executable)
"""
from production_strategy import get_trading_signal

if __name__ == "__main__":
    print(get_trading_signal())
