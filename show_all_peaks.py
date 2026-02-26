"""Show ALL peaks and bottoms detected in the last 100 days"""
from backtest import load_data
from scipy.signal import find_peaks
import pandas as pd

# Load data
data = load_data()
print(f'Analyzing YINN data from {data.index[0]} to {data.index[-1]}')
print(f'Total days: {len(data)}\n')

# Get the last 100 days
lookback = 100
min_distance = 5

window = data.tail(lookback).copy()
prices = window['close'].values
dates = window.index

# Find ALL local peaks
peak_indices, peak_properties = find_peaks(
    prices,
    distance=min_distance,
    prominence=0.5
)

# Find ALL local troughs
trough_indices, trough_properties = find_peaks(
    -prices,
    distance=min_distance,
    prominence=0.5
)

print('='*80)
print(f'ALL PEAKS DETECTED - Last {lookback} Days (min distance: {min_distance} days)')
print('='*80)
print(f"{'#':<5} {'Date':<15} {'Price':<12} {'Days Ago':<12} {'Rank by Price':<15}")
print('-'*80)

# Create list of peaks with prices
all_peaks = [(dates[i], prices[i], i) for i in peak_indices]
all_peaks_sorted = sorted(all_peaks, key=lambda x: x[1], reverse=True)

last_date = data.index[-1]
for idx, (date, price, i) in enumerate(all_peaks_sorted, 1):
    date_str = date.strftime('%Y-%m-%d')
    days_ago = (last_date - date).days
    rank = '⭐ TOP 3' if idx <= 3 else ''
    print(f"{idx:<5} {date_str:<15} ${price:<11.2f} {days_ago:<12} {rank:<15}")

print(f'\nTotal peaks found: {len(all_peaks)}')

print('\n' + '='*80)
print(f'ALL TROUGHS DETECTED - Last {lookback} Days (min distance: {min_distance} days)')
print('='*80)
print(f"{'#':<5} {'Date':<15} {'Price':<12} {'Days Ago':<12} {'Rank by Price':<15}")
print('-'*80)

# Create list of troughs with prices
all_troughs = [(dates[i], prices[i], i) for i in trough_indices]
all_troughs_sorted = sorted(all_troughs, key=lambda x: x[1])

for idx, (date, price, i) in enumerate(all_troughs_sorted, 1):
    date_str = date.strftime('%Y-%m-%d')
    days_ago = (last_date - date).days
    rank = '⭐ BOTTOM 3' if idx <= 3 else ''
    print(f"{idx:<5} {date_str:<15} ${price:<11.2f} {days_ago:<12} {rank:<15}")

print(f'\nTotal troughs found: {len(all_troughs)}')
print('='*80)

# Show the filtering effect
if all_peaks and all_troughs:
    print('\nFILTERING SUMMARY:')
    print(f'  Raw peaks detected:     {len(all_peaks)}')
    print(f'  Filtered to top:        3 peaks')
    print(f'  Raw troughs detected:   {len(all_troughs)}')
    print(f'  Filtered to bottom:     3 troughs')
    print(f'  Min distance enforced:  {min_distance} days')
    print('='*80)
