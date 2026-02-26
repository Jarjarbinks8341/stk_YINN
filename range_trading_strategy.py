"""
Range Trading Strategy for YINN

Uses distributed peaks and troughs to identify support/resistance levels.
Buys near support, sells near resistance.
"""
import pandas as pd
import numpy as np
from strategy import Strategy, Signal
from peak_detector import find_distributed_peaks_troughs

class RangeTradingStrategy(Strategy):
    """
    Range trading strategy using dynamic support/resistance levels

    Strategy:
    1. Find top 3 distributed peaks (resistance) and bottom 3 troughs (support)
    2. BUY when price approaches support (within threshold)
    3. SELL when price approaches resistance (within threshold)

    Args:
        lookback: Days to look back for peak/trough detection
        min_distance: Minimum days between peaks/troughs
        buy_threshold_pct: % above support level to trigger buy (default: 2%)
        sell_threshold_pct: % below resistance level to trigger sell (default: 2%)
    """

    def __init__(self,
                 lookback: int = 100,
                 min_distance: int = 5,
                 buy_threshold_pct: float = 2.0,
                 sell_threshold_pct: float = 2.0):
        super().__init__(f"RangeTrading_{lookback}_{min_distance}_{buy_threshold_pct}_{sell_threshold_pct}")
        self.lookback = lookback
        self.min_distance = min_distance
        self.buy_threshold_pct = buy_threshold_pct
        self.sell_threshold_pct = sell_threshold_pct

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate trading signals based on support/resistance levels"""
        signals = pd.Series(Signal.HOLD, index=data.index)

        # Need at least lookback + min_distance days
        start_idx = max(self.lookback, self.min_distance * 6)

        for i in range(start_idx, len(data)):
            # Get historical data up to current point
            historical_data = data.iloc[:i].copy()

            # Find peaks and troughs
            peaks, troughs = find_distributed_peaks_troughs(
                historical_data,
                lookback=self.lookback,
                min_distance=self.min_distance,
                num_peaks=3,
                num_troughs=3
            )

            if not peaks or not troughs:
                continue

            # Calculate average support and resistance
            avg_support = np.mean([t.price for t in troughs])
            avg_resistance = np.mean([p.price for p in peaks])

            current_price = data.iloc[i]['close']

            # Calculate thresholds
            buy_threshold = avg_support * (1 + self.buy_threshold_pct / 100)
            sell_threshold = avg_resistance * (1 - self.sell_threshold_pct / 100)

            # BUY signal: Price near support
            if current_price <= buy_threshold:
                signals.iloc[i] = Signal.BUY

            # SELL signal: Price near resistance
            elif current_price >= sell_threshold:
                signals.iloc[i] = Signal.SELL

        return signals


class ImprovedRangeTradingStrategy(Strategy):
    """
    Improved range trading with additional filters

    Enhancements:
    1. Only trade if range is wide enough (min_range_pct)
    2. Use volume confirmation for entries
    3. Dynamic threshold based on volatility
    4. RSI filter to avoid overbought/oversold extremes
    """

    def __init__(self,
                 lookback: int = 100,
                 min_distance: int = 5,
                 min_range_pct: float = 10.0,
                 volume_threshold: float = 1.2):
        super().__init__(f"ImprovedRange_{lookback}_{min_distance}_{min_range_pct}")
        self.lookback = lookback
        self.min_distance = min_distance
        self.min_range_pct = min_range_pct
        self.volume_threshold = volume_threshold

    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate signals with enhanced filters"""
        # Calculate indicators
        data = data.copy()
        data['rsi'] = self.calculate_rsi(data)
        data['volume_ma'] = data['volume'].rolling(window=20).mean()

        signals = pd.Series(Signal.HOLD, index=data.index)

        start_idx = max(self.lookback, 20)

        for i in range(start_idx, len(data)):
            historical_data = data.iloc[:i].copy()

            # Find peaks and troughs
            peaks, troughs = find_distributed_peaks_troughs(
                historical_data,
                lookback=self.lookback,
                min_distance=self.min_distance,
                num_peaks=3,
                num_troughs=3
            )

            if not peaks or not troughs:
                continue

            avg_support = np.mean([t.price for t in troughs])
            avg_resistance = np.mean([p.price for p in peaks])

            # Check if range is wide enough
            range_pct = ((avg_resistance - avg_support) / avg_support) * 100
            if range_pct < self.min_range_pct:
                continue

            current_price = data.iloc[i]['close']
            current_rsi = data.iloc[i]['rsi']
            current_volume = data.iloc[i]['volume']
            avg_volume = data.iloc[i]['volume_ma']

            # Dynamic thresholds based on range
            support_threshold = avg_support * 1.03  # 3% above support
            resistance_threshold = avg_resistance * 0.97  # 3% below resistance

            # BUY: Near support + RSI not oversold + volume confirmation
            if (current_price <= support_threshold and
                current_rsi > 25 and  # Not extremely oversold
                current_volume > avg_volume * self.volume_threshold):
                signals.iloc[i] = Signal.BUY

            # SELL: Near resistance + RSI not overbought
            elif (current_price >= resistance_threshold and
                  current_rsi < 75):  # Not extremely overbought
                signals.iloc[i] = Signal.SELL

        return signals


# Test the strategy
if __name__ == "__main__":
    from backtest import load_data, run_backtest, compare_strategies

    print("Loading YINN data...")
    data = load_data()

    if data.empty:
        print("No data found.")
        exit()

    print(f"Loaded {len(data)} days of data\n")

    # Test different variations
    strategies = [
        RangeTradingStrategy(lookback=100, min_distance=5, buy_threshold_pct=2.0, sell_threshold_pct=2.0),
        RangeTradingStrategy(lookback=100, min_distance=10, buy_threshold_pct=3.0, sell_threshold_pct=3.0),
        RangeTradingStrategy(lookback=60, min_distance=5, buy_threshold_pct=2.0, sell_threshold_pct=2.0),
        ImprovedRangeTradingStrategy(lookback=100, min_distance=5, min_range_pct=10.0),
    ]

    print("="*80)
    print("TESTING RANGE TRADING STRATEGIES")
    print("="*80 + "\n")

    for strategy in strategies:
        run_backtest(strategy, data.copy(), initial_capital=10000, verbose=True)

    # Compare
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)

    comparison = compare_strategies(strategies, data, initial_capital=10000)

    print("\nRanked by Total Return:")
    print("-" * 80)
    for idx, row in comparison.iterrows():
        print(f"\n{row['strategy_name']}")
        print(f"  Return: {row['total_return_pct']:>6.2f}% | Alpha: {row['alpha']:>+6.2f}% | Trades: {row.get('total_trades', 0):>3} | Win Rate: {row.get('win_rate', 0):>5.1f}%")

    print("\n" + "="*80)
