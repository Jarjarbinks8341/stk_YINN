"""
Visualize YINN price with peaks and troughs marked
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
import numpy as np
from backtest import load_data
from peak_detector import find_distributed_peaks_troughs

def plot_peaks_troughs(lookback=100, min_distance=5, save_path='yinn_chart.png'):
    """
    Create a chart showing YINN price with peaks and troughs marked

    Args:
        lookback: Number of days to look back
        min_distance: Minimum distance between peaks/troughs
        save_path: Path to save the chart image
    """
    # Load data
    data = load_data()

    # Get the lookback window
    window = data.tail(lookback).copy()

    # Find peaks and troughs
    peaks, troughs = find_distributed_peaks_troughs(
        data,
        lookback=lookback,
        min_distance=min_distance,
        num_peaks=3,
        num_troughs=3
    )

    # Calculate support and resistance levels
    avg_resistance = np.mean([p.price for p in peaks]) if peaks else None
    avg_support = np.mean([t.price for t in troughs]) if troughs else None

    # Create the plot
    fig, ax = plt.subplots(figsize=(16, 9))

    # Plot the price line
    ax.plot(window.index, window['close'],
            color='#2E86AB', linewidth=2, label='YINN Close Price', zorder=1)

    # Fill area between support and resistance
    if avg_support and avg_resistance:
        ax.axhspan(avg_support, avg_resistance, alpha=0.1, color='gray',
                   label=f'Trading Range: ${avg_support:.2f} - ${avg_resistance:.2f}')

    # Plot resistance level
    if avg_resistance:
        ax.axhline(y=avg_resistance, color='#A23B72', linestyle='--',
                   linewidth=2, alpha=0.7, label=f'Avg Resistance: ${avg_resistance:.2f}')

    # Plot support level
    if avg_support:
        ax.axhline(y=avg_support, color='#F18F01', linestyle='--',
                   linewidth=2, alpha=0.7, label=f'Avg Support: ${avg_support:.2f}')

    # Mark the peaks
    for i, peak in enumerate(peaks, 1):
        ax.scatter(peak.date, peak.price, color='red', s=200,
                   marker='^', zorder=5, edgecolors='darkred', linewidth=2)
        ax.annotate(f'Peak {i}\n${peak.price:.2f}',
                    xy=(peak.date, peak.price),
                    xytext=(0, 15), textcoords='offset points',
                    ha='center', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', fc='red', alpha=0.7),
                    color='white')

    # Mark the troughs
    for i, trough in enumerate(troughs, 1):
        ax.scatter(trough.date, trough.price, color='green', s=200,
                   marker='v', zorder=5, edgecolors='darkgreen', linewidth=2)
        ax.annotate(f'Bottom {i}\n${trough.price:.2f}',
                    xy=(trough.date, trough.price),
                    xytext=(0, -25), textcoords='offset points',
                    ha='center', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', fc='green', alpha=0.7),
                    color='white')

    # Mark current price
    current_price = window.iloc[-1]['close']
    current_date = window.index[-1]
    ax.scatter(current_date, current_price, color='blue', s=300,
               marker='o', zorder=6, edgecolors='darkblue', linewidth=3)
    ax.annotate(f'Current\n${current_price:.2f}',
                xy=(current_date, current_price),
                xytext=(20, 0), textcoords='offset points',
                ha='left', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', fc='blue', alpha=0.8),
                color='white',
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))

    # Formatting
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
    ax.set_title(f'YINN Trading Range Analysis - Last {lookback} Days\n'
                 f'Peaks & Troughs with Support/Resistance Levels',
                 fontsize=16, fontweight='bold', pad=20)

    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=45, ha='right')

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Legend
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)

    # Add statistics box
    if avg_support and avg_resistance:
        range_width = avg_resistance - avg_support
        range_pct = (range_width / avg_support) * 100
        pct_in_range = ((current_price - avg_support) / range_width) * 100

        stats_text = (
            f'Trading Statistics:\n'
            f'Range Width: ${range_width:.2f} ({range_pct:.1f}%)\n'
            f'Current Position: {pct_in_range:.1f}% in range\n'
        )

        if pct_in_range < 25:
            stats_text += 'Signal: 🟢 BUY ZONE (Near Support)'
            box_color = 'lightgreen'
        elif pct_in_range > 75:
            stats_text += 'Signal: 🔴 SELL ZONE (Near Resistance)'
            box_color = 'lightcoral'
        else:
            stats_text += 'Signal: 🟡 NEUTRAL (Mid Range)'
            box_color = 'lightyellow'

        ax.text(0.02, 0.98, stats_text,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor=box_color, alpha=0.8))

    # Tight layout
    plt.tight_layout()

    # Save the figure
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f'\n✅ Chart saved to: {save_path}')

    # Close the plot to free memory
    plt.close()

    return save_path


if __name__ == "__main__":
    print("Creating YINN chart with peaks and troughs...\n")

    # Create chart for last 100 days
    plot_peaks_troughs(lookback=100, min_distance=5, save_path='yinn_100days.png')

    # Create chart for last 60 days (the best performing strategy)
    plot_peaks_troughs(lookback=60, min_distance=5, save_path='yinn_60days.png')

    print("\n✅ Charts created successfully!")
    print("  - yinn_100days.png (100-day analysis)")
    print("  - yinn_60days.png (60-day analysis - best strategy)")
