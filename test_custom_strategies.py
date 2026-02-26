"""Test advanced custom strategies"""
from backtest import load_data, run_backtest, compare_strategies
from advanced_strategies import (
    TripleIndicatorStrategy,
    TrendFollowingStrategy,
    MeanReversionStrategy,
    BreakoutStrategy
)

def main():
    print("Loading YINN data...")
    data = load_data()

    if data.empty:
        print("No data found. Please run fetch_data.py first.")
        return

    print(f"Loaded {len(data)} days of data from {data.index[0]} to {data.index[-1]}\n")

    # Define advanced strategies
    strategies = [
        TripleIndicatorStrategy(rsi_period=14, oversold=30, overbought=70),
        TrendFollowingStrategy(ema_period=50, adx_period=14, atr_multiplier=2.0),
        MeanReversionStrategy(lookback=20, z_threshold=2.0, max_hold_days=10),
        BreakoutStrategy(lookback=20, volume_multiplier=2.0, profit_target=5.0)
    ]

    initial_capital = 10000
    position_size = 1.0

    # Run individual backtests
    print("="*80)
    print("TESTING ADVANCED STRATEGIES")
    print("="*80 + "\n")

    for strategy in strategies:
        run_backtest(strategy, data.copy(), initial_capital, position_size, verbose=True)

    # Compare all strategies
    print("\n" + "="*80)
    print("ADVANCED STRATEGY COMPARISON")
    print("="*80)

    comparison = compare_strategies(strategies, data, initial_capital, position_size)

    print("\nRanked by Total Return:")
    print("-" * 80)

    for idx, row in comparison.iterrows():
        print(f"\n{row['strategy_name']}")
        print(f"  Return: {row['total_return_pct']:>6.2f}% | Alpha: {row['alpha']:>+6.2f}% | Trades: {row.get('total_trades', 0):>3} | Win Rate: {row.get('win_rate', 0):>5.1f}%")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
