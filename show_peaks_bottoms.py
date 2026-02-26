"""Show peaks and bottoms for the last 100 days"""
from backtest import load_data
from peak_detector import find_distributed_peaks_troughs

# Load data
data = load_data()
print(f'Analyzing YINN data from {data.index[0]} to {data.index[-1]}')
print(f'Total days: {len(data)}\n')

# Get peaks and troughs for last 100 days
peaks, troughs = find_distributed_peaks_troughs(
    data,
    lookback=100,
    min_distance=5,
    num_peaks=3,
    num_troughs=3
)

print('='*80)
print('PEAKS (HIGHS) - Last 100 Days')
print('='*80)
print(f"{'Rank':<8} {'Date':<15} {'Price':<12} {'Days Ago':<10}")
print('-'*80)

last_date = data.index[-1]
for i, peak in enumerate(peaks, 1):
    date_str = peak.date.strftime('%Y-%m-%d') if hasattr(peak.date, 'strftime') else str(peak.date)
    days_ago = (last_date - peak.date).days
    print(f"{i:<8} {date_str:<15} ${peak.price:<11.2f} {days_ago:<10}")

print('\n' + '='*80)
print('TROUGHS (LOWS) - Last 100 Days')
print('='*80)
print(f"{'Rank':<8} {'Date':<15} {'Price':<12} {'Days Ago':<10}")
print('-'*80)

for i, trough in enumerate(troughs, 1):
    date_str = trough.date.strftime('%Y-%m-%d') if hasattr(trough.date, 'strftime') else str(trough.date)
    days_ago = (last_date - trough.date).days
    print(f"{i:<8} {date_str:<15} ${trough.price:<11.2f} {days_ago:<10}")

# Calculate stats
if peaks and troughs:
    avg_resistance = sum(p.price for p in peaks) / len(peaks)
    avg_support = sum(t.price for t in troughs) / len(troughs)
    range_width = avg_resistance - avg_support
    range_pct = (range_width / avg_support) * 100

    print('\n' + '='*80)
    print('SUMMARY STATISTICS')
    print('='*80)
    print(f'Average Resistance: ${avg_resistance:.2f}')
    print(f'Average Support:    ${avg_support:.2f}')
    print(f'Range Width:        ${range_width:.2f} ({range_pct:.1f}%)')

    current = data.iloc[-1]['close']
    current_date = data.index[-1].strftime('%Y-%m-%d')
    print(f'Current Price:      ${current:.2f} ({current_date})')

    # Show where current price is in the range
    pct_in_range = ((current - avg_support) / range_width) * 100
    print(f'Position in Range:  {pct_in_range:.1f}%')

    if pct_in_range < 25:
        print('  → Near SUPPORT - Potential BUY zone')
    elif pct_in_range > 75:
        print('  → Near RESISTANCE - Potential SELL zone')
    else:
        print('  → In MIDDLE of range')

    print('='*80)
