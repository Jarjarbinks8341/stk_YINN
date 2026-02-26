"""
Backtest all Support/Resistance calculation methods
to find which one performs best for YINN trading
"""
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from strategy import Strategy, Signal
from backtest import load_data, run_backtest, compare_strategies
from peak_detector import find_distributed_peaks_troughs

class Method1_SimpleAverage(Strategy):
    """Simple average of top 3 peaks/troughs"""

    def __init__(self, lookback=100, min_distance=5, threshold_pct=2.0):
        super().__init__(f"Method1_SimpleAvg_{lookback}_{threshold_pct}")
        self.lookback = lookback
        self.min_distance = min_distance
        self.threshold_pct = threshold_pct

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=data.index)
        start_idx = self.lookback

        for i in range(start_idx, len(data)):
            historical_data = data.iloc[:i].copy()
            peaks, troughs = find_distributed_peaks_troughs(
                historical_data, self.lookback, self.min_distance, 3, 3
            )

            if not peaks or not troughs:
                continue

            # Simple average
            avg_resistance = np.mean([p.price for p in peaks])
            avg_support = np.mean([t.price for t in troughs])

            current_price = data.iloc[i]['close']
            buy_threshold = avg_support * (1 + self.threshold_pct / 100)
            sell_threshold = avg_resistance * (1 - self.threshold_pct / 100)

            if current_price <= buy_threshold:
                signals.iloc[i] = Signal.BUY
            elif current_price >= sell_threshold:
                signals.iloc[i] = Signal.SELL

        return signals


class Method2_TimeWeighted(Strategy):
    """Time-weighted average - recent levels matter more"""

    def __init__(self, lookback=100, min_distance=5, threshold_pct=2.0):
        super().__init__(f"Method2_TimeWeighted_{lookback}_{threshold_pct}")
        self.lookback = lookback
        self.min_distance = min_distance
        self.threshold_pct = threshold_pct

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=data.index)
        start_idx = self.lookback

        for i in range(start_idx, len(data)):
            historical_data = data.iloc[:i].copy()
            peaks, troughs = find_distributed_peaks_troughs(
                historical_data, self.lookback, self.min_distance, 3, 3
            )

            if not peaks or not troughs:
                continue

            last_date = historical_data.index[-1]

            # Time-weighted average for resistance
            peak_weights = []
            for p in peaks:
                days_ago = (last_date - p.date).days
                weight = 1 / (days_ago + 1)
                peak_weights.append((p.price, weight))

            avg_resistance = sum(p * w for p, w in peak_weights) / sum(w for _, w in peak_weights)

            # Time-weighted average for support
            trough_weights = []
            for t in troughs:
                days_ago = (last_date - t.date).days
                weight = 1 / (days_ago + 1)
                trough_weights.append((t.price, weight))

            avg_support = sum(p * w for p, w in trough_weights) / sum(w for _, w in trough_weights)

            current_price = data.iloc[i]['close']
            buy_threshold = avg_support * (1 + self.threshold_pct / 100)
            sell_threshold = avg_resistance * (1 - self.threshold_pct / 100)

            if current_price <= buy_threshold:
                signals.iloc[i] = Signal.BUY
            elif current_price >= sell_threshold:
                signals.iloc[i] = Signal.SELL

        return signals


class Method3_NearestLevels(Strategy):
    """Use nearest peak/trough to current price"""

    def __init__(self, lookback=100, min_distance=5, threshold_pct=2.0):
        super().__init__(f"Method3_Nearest_{lookback}_{threshold_pct}")
        self.lookback = lookback
        self.min_distance = min_distance
        self.threshold_pct = threshold_pct

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=data.index)
        start_idx = self.lookback

        for i in range(start_idx, len(data)):
            historical_data = data.iloc[:i].copy()
            peaks, troughs = find_distributed_peaks_troughs(
                historical_data, self.lookback, self.min_distance, 3, 3
            )

            if not peaks or not troughs:
                continue

            current_price = data.iloc[i]['close']

            # Find nearest resistance (peak above current)
            peaks_above = [p for p in peaks if p.price > current_price]
            if peaks_above:
                resistance = min(peaks_above, key=lambda p: p.price).price
            else:
                resistance = max(peaks, key=lambda p: p.price).price

            # Find nearest support (trough below current)
            troughs_below = [t for t in troughs if t.price < current_price]
            if troughs_below:
                support = max(troughs_below, key=lambda t: t.price).price
            else:
                support = min(troughs, key=lambda t: t.price).price

            buy_threshold = support * (1 + self.threshold_pct / 100)
            sell_threshold = resistance * (1 - self.threshold_pct / 100)

            if current_price <= buy_threshold:
                signals.iloc[i] = Signal.BUY
            elif current_price >= sell_threshold:
                signals.iloc[i] = Signal.SELL

        return signals


class Method4_RoundNumbers(Strategy):
    """Use psychological round number levels"""

    def __init__(self, lookback=100, round_to=5):
        super().__init__(f"Method4_RoundNum_{lookback}_{round_to}")
        self.lookback = lookback
        self.round_to = round_to

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=data.index)
        start_idx = self.lookback

        for i in range(start_idx, len(data)):
            window = data.iloc[i-self.lookback:i]

            high = window['close'].max()
            low = window['close'].min()
            current = data.iloc[i]['close']

            # Find round numbers in range
            round_levels = []
            for price in range(int(low), int(high) + self.round_to, self.round_to):
                if low <= price <= high:
                    round_levels.append(price)

            if not round_levels:
                continue

            # Find nearest round numbers
            levels_above = [p for p in round_levels if p > current]
            levels_below = [p for p in round_levels if p < current]

            resistance = min(levels_above) if levels_above else max(round_levels)
            support = max(levels_below) if levels_below else min(round_levels)

            # Buy within 3% of support, sell within 3% of resistance
            if current <= support * 1.03:
                signals.iloc[i] = Signal.BUY
            elif current >= resistance * 0.97:
                signals.iloc[i] = Signal.SELL

        return signals


class Method5_Clustering(Strategy):
    """Use price clustering to find strongest levels"""

    def __init__(self, lookback=100, min_distance=5, cluster_range=2.0, threshold_pct=2.0):
        super().__init__(f"Method5_Cluster_{lookback}_{cluster_range}")
        self.lookback = lookback
        self.min_distance = min_distance
        self.cluster_range = cluster_range
        self.threshold_pct = threshold_pct

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=data.index)
        start_idx = self.lookback

        for i in range(start_idx, len(data)):
            window = data.iloc[i-self.lookback:i]
            prices = window['close'].values

            # Find all peaks and troughs
            peak_indices, _ = find_peaks(prices, distance=self.min_distance, prominence=0.5)
            trough_indices, _ = find_peaks(-prices, distance=self.min_distance, prominence=0.5)

            if len(peak_indices) == 0 or len(trough_indices) == 0:
                continue

            peak_prices = [prices[idx] for idx in peak_indices]
            trough_prices = [prices[idx] for idx in trough_indices]

            # Cluster peaks
            peak_clusters = {}
            for price in peak_prices:
                found = False
                for center in list(peak_clusters.keys()):
                    if abs(price - center) <= self.cluster_range:
                        peak_clusters[center].append(price)
                        found = True
                        break
                if not found:
                    peak_clusters[price] = [price]

            # Cluster troughs
            trough_clusters = {}
            for price in trough_prices:
                found = False
                for center in list(trough_clusters.keys()):
                    if abs(price - center) <= self.cluster_range:
                        trough_clusters[center].append(price)
                        found = True
                        break
                if not found:
                    trough_clusters[price] = [price]

            # Get strongest clusters
            if peak_clusters:
                strongest_peak = max(peak_clusters.items(), key=lambda x: len(x[1]))
                resistance = np.mean(strongest_peak[1])
            else:
                continue

            if trough_clusters:
                strongest_trough = max(trough_clusters.items(), key=lambda x: len(x[1]))
                support = np.mean(strongest_trough[1])
            else:
                continue

            current_price = data.iloc[i]['close']
            buy_threshold = support * (1 + self.threshold_pct / 100)
            sell_threshold = resistance * (1 - self.threshold_pct / 100)

            if current_price <= buy_threshold:
                signals.iloc[i] = Signal.BUY
            elif current_price >= sell_threshold:
                signals.iloc[i] = Signal.SELL

        return signals


def main():
    print("Loading YINN data...")
    data = load_data()

    if data.empty:
        print("No data found.")
        return

    print(f"Loaded {len(data)} days of data\n")

    # Test all methods with same parameters
    strategies = [
        Method1_SimpleAverage(lookback=100, min_distance=5, threshold_pct=2.0),
        Method2_TimeWeighted(lookback=100, min_distance=5, threshold_pct=2.0),
        Method3_NearestLevels(lookback=100, min_distance=5, threshold_pct=2.0),
        Method4_RoundNumbers(lookback=100, round_to=5),
        Method5_Clustering(lookback=100, min_distance=5, cluster_range=2.0, threshold_pct=2.0),
    ]

    # Also test with 60-day lookback (which performed well before)
    strategies.extend([
        Method1_SimpleAverage(lookback=60, min_distance=5, threshold_pct=2.0),
        Method2_TimeWeighted(lookback=60, min_distance=5, threshold_pct=2.0),
        Method3_NearestLevels(lookback=60, min_distance=5, threshold_pct=2.0),
    ])

    print("="*80)
    print("BACKTESTING ALL SUPPORT/RESISTANCE METHODS")
    print("="*80 + "\n")

    # Run backtests
    for strategy in strategies:
        run_backtest(strategy, data.copy(), initial_capital=10000, verbose=False)

    # Compare
    comparison = compare_strategies(strategies, data, initial_capital=10000)

    print("\n" + "="*80)
    print("RESULTS - RANKED BY TOTAL RETURN")
    print("="*80)
    print(f"\n{'Rank':<6} {'Method':<35} {'Return':<10} {'Alpha':<10} {'Trades':<8} {'Win Rate':<10}")
    print("-"*80)

    for idx, row in comparison.iterrows():
        rank = comparison.index.get_loc(idx) + 1
        trades = row.get('total_trades', 0)
        win_rate = row.get('win_rate', 0)

        # Add medal emojis for top 3
        medal = ""
        if rank == 1:
            medal = "🥇"
        elif rank == 2:
            medal = "🥈"
        elif rank == 3:
            medal = "🥉"

        print(f"{medal:<6} {row['strategy_name']:<35} {row['total_return_pct']:>6.2f}%   {row['alpha']:>+6.2f}%   {trades:>5.0f}    {win_rate:>6.1f}%")

    print("\n" + "="*80)
    print("DETAILED COMPARISON")
    print("="*80)

    # Show top 3 in detail
    for idx, row in comparison.head(3).iterrows():
        rank = comparison.index.get_loc(idx) + 1
        print(f"\n{rank}. {row['strategy_name']}")
        print(f"   Return: {row['total_return_pct']:>6.2f}% (${row['final_value']:,.2f})")
        print(f"   Alpha:  {row['alpha']:>+6.2f}%")

        if 'total_trades' in row and pd.notna(row['total_trades']):
            print(f"   Trades: {row['total_trades']:.0f} ({row['win_rate']:.1f}% win rate)")
            print(f"   Avg P&L: ${row.get('avg_pnl', 0):.2f}")

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)

    winner = comparison.iloc[0]
    print(f"\n🏆 WINNER: {winner['strategy_name']}")
    print(f"   Total Return: {winner['total_return_pct']:.2f}%")
    print(f"   Beat Buy & Hold by: {winner['alpha']:.2f}%")

    # Buy & Hold comparison
    buy_hold = comparison.iloc[0]['buy_hold_return_pct']
    print(f"\n📊 Buy & Hold Benchmark: {buy_hold:.2f}%")

    methods_beat_benchmark = comparison[comparison['alpha'] > 0]
    print(f"   Methods that beat buy & hold: {len(methods_beat_benchmark)}/{len(comparison)}")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
