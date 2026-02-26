"""
Scaled Entry/Exit Strategy for YINN
=====================================

Instead of buying 100% at once, scale into position:
- 30% when 80% close to support
- 30% when 90% close to support
- 40% when at/below support

Similar for selling when approaching resistance.

Benefits:
- Better average entry/exit prices
- More trades = more opportunities
- Lower risk per entry
- Dollar cost averaging
"""
import pandas as pd
import numpy as np
from strategy import Strategy, Signal
from peak_detector import find_distributed_peaks_troughs

class ScaledEntryStrategy(Strategy):
    """
    Scaled entry/exit strategy using time-weighted support/resistance

    Entry levels (from top to bottom):
    - Level 1: 80% to support (30% position)
    - Level 2: 90% to support (30% position)
    - Level 3: At support (40% position)

    Exit levels (from bottom to top):
    - Level 1: 80% to resistance (30% position)
    - Level 2: 90% to resistance (30% position)
    - Level 3: At resistance (40% position)
    """

    def __init__(self, lookback=60, min_distance=5):
        super().__init__(f"ScaledEntry_{lookback}")
        self.lookback = lookback
        self.min_distance = min_distance

        # Position tracking
        self.current_position_pct = 0  # 0-100%
        self.position_cost_basis = 0
        self.position_shares = 0

    def calculate_time_weighted_levels(self, data: pd.DataFrame):
        """Calculate time-weighted support and resistance levels"""
        peaks, troughs = find_distributed_peaks_troughs(
            data, self.lookback, self.min_distance, num_peaks=3, num_troughs=3
        )

        if not peaks or not troughs:
            return None, None

        last_date = data.index[-1]

        # Time-weighted resistance
        peak_weights = []
        for p in peaks:
            days_ago = (last_date - p.date).days
            weight = 1 / (days_ago + 1)
            peak_weights.append((p.price, weight))
        resistance = sum(p * w for p, w in peak_weights) / sum(w for _, w in peak_weights)

        # Time-weighted support
        trough_weights = []
        for t in troughs:
            days_ago = (last_date - t.date).days
            weight = 1 / (days_ago + 1)
            trough_weights.append((t.price, weight))
        support = sum(p * w for p, w in trough_weights) / sum(w for _, w in trough_weights)

        return support, resistance

    def calculate_position_in_range(self, current_price, support, resistance):
        """
        Calculate where current price is in the range (0-100%)
        0% = at support, 100% = at resistance
        """
        if resistance == support:
            return 50

        position_pct = ((current_price - support) / (resistance - support)) * 100
        return max(0, min(100, position_pct))  # Clamp between 0-100

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate scaled entry/exit signals"""
        signals = pd.Series(Signal.HOLD, index=data.index)
        start_idx = self.lookback

        for i in range(start_idx, len(data)):
            historical_data = data.iloc[:i].copy()
            support, resistance = self.calculate_time_weighted_levels(historical_data)

            if support is None or resistance is None:
                continue

            current_price = data.iloc[i]['close']
            position_pct = self.calculate_position_in_range(current_price, support, resistance)

            # BUY SIGNALS (scaling in as price falls to support)
            if position_pct <= 20:  # 80% to support (20% from support in range)
                signals.iloc[i] = Signal.BUY
            elif position_pct <= 10:  # 90% to support
                signals.iloc[i] = Signal.BUY
            elif position_pct <= 0:  # At/below support
                signals.iloc[i] = Signal.BUY

            # SELL SIGNALS (scaling out as price rises to resistance)
            elif position_pct >= 80:  # 80% to resistance
                signals.iloc[i] = Signal.SELL
            elif position_pct >= 90:  # 90% to resistance
                signals.iloc[i] = Signal.SELL
            elif position_pct >= 100:  # At/above resistance
                signals.iloc[i] = Signal.SELL

        return signals


class ImprovedScaledStrategy(Strategy):
    """
    Improved scaled entry with explicit position management

    Tracks position size and only buys if <100% invested
    Only sells if >0% invested
    """

    def __init__(self, lookback=60, min_distance=5):
        super().__init__(f"ImprovedScaled_{lookback}")
        self.lookback = lookback
        self.min_distance = min_distance

    def calculate_time_weighted_levels(self, data: pd.DataFrame):
        """Calculate time-weighted support and resistance"""
        peaks, troughs = find_distributed_peaks_troughs(
            data, self.lookback, self.min_distance, num_peaks=3, num_troughs=3
        )

        if not peaks or not troughs:
            return None, None

        last_date = data.index[-1]

        peak_weights = [(p.price, 1/(last_date - p.date).days + 1) for p in peaks]
        resistance = sum(p * w for p, w in peak_weights) / sum(w for _, w in peak_weights)

        trough_weights = [(t.price, 1/(last_date - t.date).days + 1) for t in troughs]
        support = sum(p * w for p, w in trough_weights) / sum(w for _, w in trough_weights)

        return support, resistance

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate scaled signals with position tracking

        BUY levels (% distance from resistance to support):
        - 80% to support (20% in range) -> BUY 30%
        - 90% to support (10% in range) -> BUY 30%
        - At support (0% in range) -> BUY 40%

        SELL levels:
        - 80% to resistance (80% in range) -> SELL 30%
        - 90% to resistance (90% in range) -> SELL 30%
        - At resistance (100% in range) -> SELL 40%
        """
        signals = pd.Series(Signal.HOLD, index=data.index)

        # Track position (will be managed by backtest engine)
        in_position = False

        start_idx = self.lookback

        for i in range(start_idx, len(data)):
            historical_data = data.iloc[:i].copy()
            support, resistance = self.calculate_time_weighted_levels(historical_data)

            if support is None or resistance is None:
                continue

            current_price = data.iloc[i]['close']
            range_width = resistance - support

            # Calculate position in range (0 = support, 100 = resistance)
            if range_width > 0:
                position_pct = ((current_price - support) / range_width) * 100
            else:
                position_pct = 50

            # BUY signals when approaching support
            if not in_position:
                if position_pct <= 20:  # 80% to support
                    signals.iloc[i] = Signal.BUY
                    in_position = True

            # SELL signals when approaching resistance
            elif in_position:
                if position_pct >= 80:  # 80% to resistance
                    signals.iloc[i] = Signal.SELL
                    in_position = False

        return signals


def test_scaled_strategies():
    """Test both scaled strategies"""
    from backtest import load_data, run_backtest, compare_strategies

    print("Loading data...")
    data = load_data()

    strategies = [
        ScaledEntryStrategy(lookback=60, min_distance=5),
        ImprovedScaledStrategy(lookback=60, min_distance=5),
    ]

    print("\n" + "="*80)
    print("TESTING SCALED ENTRY STRATEGIES")
    print("="*80 + "\n")

    for strategy in strategies:
        print(f"\nTesting {strategy.name}...")
        run_backtest(strategy, data.copy(), initial_capital=10000, verbose=True)

    # Compare
    comparison = compare_strategies(strategies, data, initial_capital=10000)

    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)

    for idx, row in comparison.iterrows():
        print(f"\n{row['strategy_name']}")
        print(f"  Return: {row['total_return_pct']:>6.2f}%")
        print(f"  Alpha:  {row['alpha']:>+6.2f}%")
        print(f"  Trades: {row.get('total_trades', 0):.0f}")
        print(f"  Win Rate: {row.get('win_rate', 0):.1f}%")


if __name__ == "__main__":
    test_scaled_strategies()
