"""Example script to run backtests on YINN strategies"""
from backtest import load_data, run_backtest, compare_strategies
from strategies import (
    MovingAverageCrossover,
    RSIStrategy,
    MomentumStrategy,
    BollingerBandsStrategy
)

def main():
    # Load YINN data
    print("Loading YINN data...")
    data = load_data()

    if data.empty:
        print("No data found. Please run fetch_data.py first.")
        return

    print(f"Loaded {len(data)} days of data from {data.index[0]} to {data.index[-1]}\n")

    # Define strategies to test
    strategies = [
        MovingAverageCrossover(fast_period=10, slow_period=30),
        MovingAverageCrossover(fast_period=5, slow_period=20),
        RSIStrategy(period=14, oversold=30, overbought=70),
        MomentumStrategy(lookback_period=20, buy_threshold=5.0, sell_threshold=-3.0),
        BollingerBandsStrategy(period=20, num_std=2.0)
    ]

    # Run individual backtests
    initial_capital = 10000
    position_size = 1.0  # Use 100% of capital per trade

    for strategy in strategies:
        run_backtest(strategy, data.copy(), initial_capital, position_size, verbose=True)

    # Compare all strategies
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)

    comparison = compare_strategies(strategies, data, initial_capital, position_size)

    # Display comparison table
    print("\nRanked by Total Return:")
    print("-" * 80)

    for idx, row in comparison.iterrows():
        print(f"\n{row['strategy_name']}")
        print(f"  Return: {row['total_return_pct']:>6.2f}% | Alpha: {row['alpha']:>+6.2f}% | Trades: {row.get('total_trades', 0):>3} | Win Rate: {row.get('win_rate', 0):>5.1f}%")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
