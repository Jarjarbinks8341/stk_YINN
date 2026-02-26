"""
Peak and Trough Detection for YINN Trading Strategy

Finds the top 3 peaks and bottom 3 troughs over a lookback period,
ensuring they are well-distributed (not clustered together).
"""
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Tuple, List
from dataclasses import dataclass

@dataclass
class PeakTrough:
    """Represents a peak or trough"""
    date: pd.Timestamp
    price: float
    index: int

def find_distributed_peaks_troughs(data: pd.DataFrame,
                                   lookback: int = 100,
                                   min_distance: int = 5,
                                   num_peaks: int = 3,
                                   num_troughs: int = 3) -> Tuple[List[PeakTrough], List[PeakTrough]]:
    """
    Find distributed peaks and troughs in price data

    Args:
        data: DataFrame with 'close' column and date index
        lookback: Number of days to look back
        min_distance: Minimum days between peaks/troughs to ensure distribution
        num_peaks: Number of top peaks to return
        num_troughs: Number of bottom troughs to return

    Returns:
        Tuple of (peaks, troughs) where each is a list of PeakTrough objects
    """
    if len(data) < lookback:
        lookback = len(data)

    # Get the lookback window
    window = data.tail(lookback).copy()
    prices = window['close'].values
    dates = window.index

    # Find all local peaks
    peak_indices, peak_properties = find_peaks(
        prices,
        distance=min_distance,
        prominence=0.5  # Require some prominence to avoid noise
    )

    # Find all local troughs (peaks in inverted data)
    trough_indices, trough_properties = find_peaks(
        -prices,
        distance=min_distance,
        prominence=0.5
    )

    # Create PeakTrough objects for peaks
    peaks = []
    for idx in peak_indices:
        peaks.append(PeakTrough(
            date=dates[idx],
            price=prices[idx],
            index=idx
        ))

    # Create PeakTrough objects for troughs
    troughs = []
    for idx in trough_indices:
        troughs.append(PeakTrough(
            date=dates[idx],
            price=prices[idx],
            index=idx
        ))

    # Sort peaks by price (highest first)
    peaks.sort(key=lambda x: x.price, reverse=True)

    # Sort troughs by price (lowest first)
    troughs.sort(key=lambda x: x.price)

    # Filter peaks to ensure distribution
    distributed_peaks = _filter_distributed(peaks, min_distance, num_peaks)

    # Filter troughs to ensure distribution
    distributed_troughs = _filter_distributed(troughs, min_distance, num_troughs)

    # Sort by date for easier visualization
    distributed_peaks.sort(key=lambda x: x.date)
    distributed_troughs.sort(key=lambda x: x.date)

    return distributed_peaks, distributed_troughs


def _filter_distributed(points: List[PeakTrough],
                        min_distance: int,
                        num_points: int) -> List[PeakTrough]:
    """
    Filter points to ensure they are well-distributed

    Greedily selects the highest/lowest points while maintaining minimum distance
    """
    if len(points) <= num_points:
        return points

    selected = []

    for point in points:
        # Check if this point is far enough from all selected points
        is_far_enough = True
        for selected_point in selected:
            distance = abs(point.index - selected_point.index)
            if distance < min_distance:
                is_far_enough = False
                break

        if is_far_enough:
            selected.append(point)

        if len(selected) >= num_points:
            break

    return selected


def get_support_resistance_levels(data: pd.DataFrame,
                                  lookback: int = 100,
                                  min_distance: int = 5) -> dict:
    """
    Get support and resistance levels from peaks and troughs

    Args:
        data: DataFrame with price data
        lookback: Lookback period in days
        min_distance: Minimum distance between peaks/troughs

    Returns:
        Dictionary with support and resistance levels
    """
    peaks, troughs = find_distributed_peaks_troughs(
        data, lookback, min_distance
    )

    # Calculate average resistance (from peaks)
    resistance_levels = [p.price for p in peaks]
    avg_resistance = np.mean(resistance_levels) if resistance_levels else None

    # Calculate average support (from troughs)
    support_levels = [t.price for t in troughs]
    avg_support = np.mean(support_levels) if support_levels else None

    return {
        'peaks': peaks,
        'troughs': troughs,
        'resistance_levels': resistance_levels,
        'support_levels': support_levels,
        'avg_resistance': avg_resistance,
        'avg_support': avg_support,
        'range': avg_resistance - avg_support if avg_resistance and avg_support else None
    }


def print_peaks_troughs(data: pd.DataFrame,
                       lookback: int = 100,
                       min_distance: int = 5):
    """
    Print peaks and troughs in a formatted way
    """
    levels = get_support_resistance_levels(data, lookback, min_distance)

    print(f"\n{'='*80}")
    print(f"PEAKS & TROUGHS ANALYSIS (Last {lookback} days)")
    print(f"{'='*80}\n")

    print("TOP 3 PEAKS (Resistance Levels):")
    print("-" * 80)
    if levels['peaks']:
        for i, peak in enumerate(levels['peaks'], 1):
            date_str = peak.date.strftime('%Y-%m-%d') if hasattr(peak.date, 'strftime') else str(peak.date)
            print(f"  {i}. {date_str} | Price: ${peak.price:>6.2f}")
        print(f"\n  Average Resistance: ${levels['avg_resistance']:>6.2f}")
    else:
        print("  No peaks found")

    print(f"\n{'='*80}\n")

    print("BOTTOM 3 TROUGHS (Support Levels):")
    print("-" * 80)
    if levels['troughs']:
        for i, trough in enumerate(levels['troughs'], 1):
            date_str = trough.date.strftime('%Y-%m-%d') if hasattr(trough.date, 'strftime') else str(trough.date)
            print(f"  {i}. {date_str} | Price: ${trough.price:>6.2f}")
        print(f"\n  Average Support: ${levels['avg_support']:>6.2f}")
    else:
        print("  No troughs found")

    print(f"\n{'='*80}")
    if levels['range']:
        print(f"Trading Range: ${levels['avg_support']:.2f} - ${levels['avg_resistance']:.2f}")
        print(f"Range Width: ${levels['range']:.2f} ({(levels['range']/levels['avg_support'])*100:.1f}%)")
    print(f"{'='*80}\n")

    return levels


# Example usage and testing
if __name__ == "__main__":
    from backtest import load_data

    # Load YINN data
    print("Loading YINN data...")
    data = load_data()

    if data.empty:
        print("No data found. Please run fetch_data.py first.")
        exit()

    print(f"Loaded {len(data)} days of data\n")

    # Test different lookback periods
    for lookback in [100, 60, 30]:
        print_peaks_troughs(data, lookback=lookback, min_distance=5)
