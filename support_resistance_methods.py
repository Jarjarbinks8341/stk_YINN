"""
Different methods to calculate Support and Resistance levels

This file explains and implements various methods for calculating
support and resistance from price data.
"""
import pandas as pd
import numpy as np
from backtest import load_data
from peak_detector import find_distributed_peaks_troughs

def method1_simple_average(data, lookback=100, min_distance=5):
    """
    METHOD 1: Simple Average (CURRENT METHOD)

    How it works:
    1. Find all local peaks (points higher than neighbors)
    2. Filter peaks to be at least 'min_distance' days apart
    3. Take the TOP 3 highest peaks
    4. AVERAGE them to get resistance level

    Same process for troughs (bottoms) to get support

    Pros:
    - Simple and easy to understand
    - Gives equal weight to all top peaks
    - Works well for range-bound stocks

    Cons:
    - May miss important recent levels
    - Averages can be between actual price levels
    - Treats old and new peaks equally
    """
    peaks, troughs = find_distributed_peaks_troughs(
        data, lookback, min_distance, num_peaks=3, num_troughs=3
    )

    if not peaks or not troughs:
        return None, None, peaks, troughs

    # Simple average of top 3 peaks
    resistance = np.mean([p.price for p in peaks])

    # Simple average of bottom 3 troughs
    support = np.mean([t.price for t in troughs])

    print("="*80)
    print("METHOD 1: Simple Average")
    print("="*80)
    print(f"\nTop 3 Peaks:")
    for i, p in enumerate(peaks, 1):
        print(f"  {i}. ${p.price:.2f} on {p.date.strftime('%Y-%m-%d')}")

    print(f"\nResistance = (${peaks[0].price:.2f} + ${peaks[1].price:.2f} + ${peaks[2].price:.2f}) / 3")
    print(f"Resistance = ${resistance:.2f}")

    print(f"\nBottom 3 Troughs:")
    for i, t in enumerate(troughs, 1):
        print(f"  {i}. ${t.price:.2f} on {t.date.strftime('%Y-%m-%d')}")

    print(f"\nSupport = (${troughs[0].price:.2f} + ${troughs[1].price:.2f} + ${troughs[2].price:.2f}) / 3")
    print(f"Support = ${support:.2f}")
    print("="*80 + "\n")

    return support, resistance, peaks, troughs


def method2_weighted_average(data, lookback=100, min_distance=5):
    """
    METHOD 2: Time-Weighted Average

    How it works:
    1. Find top 3 peaks and bottom 3 troughs (same as method 1)
    2. Give MORE WEIGHT to RECENT peaks/troughs
    3. Give LESS WEIGHT to OLDER peaks/troughs

    Formula: weighted_avg = sum(price * weight) / sum(weight)
    Weight = 1 / (days_ago + 1)

    Example:
    Peak 1: $56.47, 142 days ago -> weight = 1/143 = 0.007
    Peak 2: $56.48, 127 days ago -> weight = 1/128 = 0.008
    Peak 3: $52.56, 102 days ago -> weight = 1/103 = 0.010

    Pros:
    - Recent levels are more relevant
    - Adapts to changing market conditions
    - Still uses historical context

    Cons:
    - More complex calculation
    - May ignore strong but old levels
    """
    peaks, troughs = find_distributed_peaks_troughs(
        data, lookback, min_distance, num_peaks=3, num_troughs=3
    )

    if not peaks or not troughs:
        return None, None

    last_date = data.index[-1]

    # Calculate weighted resistance
    peak_weights = []
    print("="*80)
    print("METHOD 2: Time-Weighted Average")
    print("="*80)
    print(f"\nTop 3 Peaks (weighted by recency):")

    for i, p in enumerate(peaks, 1):
        days_ago = (last_date - p.date).days
        weight = 1 / (days_ago + 1)  # More recent = higher weight
        peak_weights.append((p.price, weight))
        print(f"  {i}. ${p.price:.2f} ({days_ago} days ago) -> weight = {weight:.4f}")

    resistance = sum(p * w for p, w in peak_weights) / sum(w for _, w in peak_weights)
    print(f"\nWeighted Resistance = ${resistance:.2f}")

    # Calculate weighted support
    trough_weights = []
    print(f"\nBottom 3 Troughs (weighted by recency):")

    for i, t in enumerate(troughs, 1):
        days_ago = (last_date - t.date).days
        weight = 1 / (days_ago + 1)
        trough_weights.append((t.price, weight))
        print(f"  {i}. ${t.price:.2f} ({days_ago} days ago) -> weight = {weight:.4f}")

    support = sum(p * w for p, w in trough_weights) / sum(w for _, w in trough_weights)
    print(f"\nWeighted Support = ${support:.2f}")
    print("="*80 + "\n")

    return support, resistance


def method3_nearest_levels(data, lookback=100, min_distance=5):
    """
    METHOD 3: Nearest Strong Levels

    How it works:
    1. Find all peaks and troughs
    2. Use the CLOSEST peak above current price as resistance
    3. Use the CLOSEST trough below current price as support

    Pros:
    - Most relevant to current price action
    - Clear entry/exit points
    - Reacts quickly to breakouts

    Cons:
    - Only uses 2 data points (1 support, 1 resistance)
    - May miss broader range context
    - Can change frequently
    """
    peaks, troughs = find_distributed_peaks_troughs(
        data, lookback, min_distance, num_peaks=3, num_troughs=3
    )

    if not peaks or not troughs:
        return None, None

    current_price = data.iloc[-1]['close']

    # Find nearest resistance (peak above current price)
    peaks_above = [p for p in peaks if p.price > current_price]
    resistance = min(peaks_above, key=lambda p: p.price).price if peaks_above else max(peaks, key=lambda p: p.price).price

    # Find nearest support (trough below current price)
    troughs_below = [t for t in troughs if t.price < current_price]
    support = max(troughs_below, key=lambda t: t.price).price if troughs_below else min(troughs, key=lambda t: t.price).price

    print("="*80)
    print("METHOD 3: Nearest Strong Levels")
    print("="*80)
    print(f"\nCurrent Price: ${current_price:.2f}")
    print(f"\nNearest Resistance (peak above): ${resistance:.2f}")
    print(f"Nearest Support (trough below): ${support:.2f}")
    print(f"\nUpside Potential: ${resistance - current_price:.2f} ({((resistance/current_price - 1)*100):.1f}%)")
    print(f"Downside Risk: ${current_price - support:.2f} ({((current_price/support - 1)*100):.1f}%)")
    print("="*80 + "\n")

    return support, resistance


def method4_round_numbers(data, lookback=100):
    """
    METHOD 4: Psychological Round Numbers

    How it works:
    1. Find the trading range (high and low of period)
    2. Identify ROUND NUMBER levels in that range
    3. Round numbers act as natural support/resistance

    Examples: $40, $45, $50, $55, $60

    Traders tend to place orders at round numbers!

    Pros:
    - Based on real trader psychology
    - Simple to understand
    - Works across all markets

    Cons:
    - Doesn't use actual price history
    - May miss important non-round levels
    """
    window = data.tail(lookback)

    high = window['close'].max()
    low = window['close'].min()
    current = data.iloc[-1]['close']

    # Find round numbers in range (multiples of 5)
    round_levels = []
    for price in range(int(low), int(high) + 5, 5):
        if low <= price <= high:
            round_levels.append(price)

    # Find nearest round numbers
    resistance = min([p for p in round_levels if p > current], default=max(round_levels))
    support = max([p for p in round_levels if p < current], default=min(round_levels))

    print("="*80)
    print("METHOD 4: Psychological Round Numbers")
    print("="*80)
    print(f"\nTrading Range: ${low:.2f} - ${high:.2f}")
    print(f"Current Price: ${current:.2f}")
    print(f"\nRound number levels in range: {[f'${p}' for p in round_levels]}")
    print(f"\nNearest Resistance (round number above): ${resistance:.2f}")
    print(f"Nearest Support (round number below): ${support:.2f}")
    print("="*80 + "\n")

    return support, resistance


def method5_clustering(data, lookback=100, min_distance=5, cluster_range=2.0):
    """
    METHOD 5: Price Clustering

    How it works:
    1. Find ALL peaks and troughs
    2. Group (cluster) peaks that are within $X of each other
    3. The STRONGEST cluster = resistance (most times price tested it)
    4. Same for troughs = support

    Example:
    Peaks at $56.47, $56.48, $55.20 -> cluster around $56
    More tests = stronger level

    Pros:
    - Identifies the STRONGEST levels (most tested)
    - Accounts for multiple tests of same level
    - Very reliable levels

    Cons:
    - More complex
    - May miss single strong levels
    """
    from scipy.signal import find_peaks as scipy_find_peaks

    window = data.tail(lookback).copy()
    prices = window['close'].values

    # Find ALL peaks (not just top 3)
    peak_indices, _ = scipy_find_peaks(prices, distance=min_distance, prominence=0.5)
    trough_indices, _ = scipy_find_peaks(-prices, distance=min_distance, prominence=0.5)

    peak_prices = [prices[i] for i in peak_indices]
    trough_prices = [prices[i] for i in trough_indices]

    # Cluster peaks
    peak_clusters = {}
    for price in peak_prices:
        # Find existing cluster within range
        found_cluster = False
        for cluster_center in list(peak_clusters.keys()):
            if abs(price - cluster_center) <= cluster_range:
                peak_clusters[cluster_center].append(price)
                found_cluster = True
                break

        if not found_cluster:
            peak_clusters[price] = [price]

    # Find strongest cluster (most peaks)
    if peak_clusters:
        strongest_peak_cluster = max(peak_clusters.items(), key=lambda x: len(x[1]))
        resistance = np.mean(strongest_peak_cluster[1])
        resistance_strength = len(strongest_peak_cluster[1])
    else:
        resistance, resistance_strength = None, 0

    # Cluster troughs
    trough_clusters = {}
    for price in trough_prices:
        found_cluster = False
        for cluster_center in list(trough_clusters.keys()):
            if abs(price - cluster_center) <= cluster_range:
                trough_clusters[cluster_center].append(price)
                found_cluster = True
                break

        if not found_cluster:
            trough_clusters[price] = [price]

    # Find strongest cluster
    if trough_clusters:
        strongest_trough_cluster = max(trough_clusters.items(), key=lambda x: len(x[1]))
        support = np.mean(strongest_trough_cluster[1])
        support_strength = len(strongest_trough_cluster[1])
    else:
        support, support_strength = None, 0

    print("="*80)
    print("METHOD 5: Price Clustering")
    print("="*80)
    print(f"\nClustering range: ${cluster_range:.2f}")
    print(f"\nResistance Cluster: ${resistance:.2f} (tested {resistance_strength} times)")
    print(f"Support Cluster: ${support:.2f} (tested {support_strength} times)")
    print(f"\nStronger level = more reliable!")
    print("="*80 + "\n")

    return support, resistance


def compare_all_methods(data, lookback=100):
    """Compare all methods side by side"""
    print("\n" + "="*80)
    print("COMPARING ALL SUPPORT/RESISTANCE CALCULATION METHODS")
    print("="*80 + "\n")

    # Run all methods
    support1, resistance1, peaks, troughs = method1_simple_average(data, lookback)
    support2, resistance2 = method2_weighted_average(data, lookback)
    support3, resistance3 = method3_nearest_levels(data, lookback)
    support4, resistance4 = method4_round_numbers(data, lookback)
    support5, resistance5 = method5_clustering(data, lookback)

    # Summary table
    print("\n" + "="*80)
    print("SUMMARY COMPARISON")
    print("="*80)
    print(f"{'Method':<30} {'Support':<12} {'Resistance':<12} {'Range Width':<12}")
    print("-"*80)

    current = data.iloc[-1]['close']

    methods = [
        ("1. Simple Average", support1, resistance1),
        ("2. Time-Weighted Average", support2, resistance2),
        ("3. Nearest Levels", support3, resistance3),
        ("4. Round Numbers", support4, resistance4),
        ("5. Price Clustering", support5, resistance5),
    ]

    for method_name, sup, res in methods:
        if sup and res:
            width = res - sup
            print(f"{method_name:<30} ${sup:<11.2f} ${res:<11.2f} ${width:.2f}")

    print(f"\nCurrent Price: ${current:.2f}")
    print("="*80 + "\n")

    # Recommendation
    print("RECOMMENDATION:")
    print("-"*80)
    print("• Method 1 (Simple Average): Best for stable range-bound trading")
    print("• Method 2 (Weighted): Best when market is changing/trending")
    print("• Method 3 (Nearest): Best for quick day-trading decisions")
    print("• Method 4 (Round Numbers): Best for psychological levels")
    print("• Method 5 (Clustering): Best for finding strongest levels")
    print("\nFor YINN range trading: Use Method 1 or Method 2")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Load YINN data
    data = load_data()

    # Compare all methods
    compare_all_methods(data, lookback=100)
