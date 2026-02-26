"""
Run simulation from specific start date
"""
from backtest import load_data, run_backtest
from production_strategy import YINNProductionStrategy
import pandas as pd

def run_simulation_from_date(start_date, initial_capital=10000):
    """
    Run simulation starting from a specific date

    Args:
        start_date: Start date in YYYY-MM-DD format
        initial_capital: Starting capital
    """
    # Load all data
    all_data = load_data()

    # Convert start_date to date object for comparison
    start_date_obj = pd.to_datetime(start_date).date()

    # Filter data from start_date onwards
    data = all_data[all_data.index >= start_date_obj].copy()

    if data.empty:
        print(f"No data found from {start_date}")
        return

    print(f"\n{'='*80}")
    print(f"SIMULATION FROM {start_date}")
    print(f"{'='*80}")
    print(f"Period: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"Trading Days: {len(data)}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"{'='*80}\n")

    # Create production strategy
    strategy = YINNProductionStrategy(
        lookback=60,
        min_distance=5,
        buy_threshold_pct=2.0,
        sell_threshold_pct=2.0
    )

    # Run backtest
    results = run_backtest(
        strategy,
        data,
        initial_capital=initial_capital,
        position_size=1.0,
        verbose=True
    )

    # Show buy & hold comparison
    buy_hold_start = data.iloc[0]['close']
    buy_hold_end = data.iloc[-1]['close']
    buy_hold_shares = int(initial_capital / buy_hold_start)
    buy_hold_final = buy_hold_shares * buy_hold_end
    buy_hold_return = ((buy_hold_final - initial_capital) / initial_capital) * 100

    print(f"\n{'='*80}")
    print("BUY & HOLD COMPARISON")
    print(f"{'='*80}")
    print(f"Buy & Hold Strategy:")
    print(f"  Buy at:        ${buy_hold_start:.2f} on {data.index[0].strftime('%Y-%m-%d')}")
    print(f"  Shares:        {buy_hold_shares:,}")
    print(f"  Current Price: ${buy_hold_end:.2f} on {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"  Final Value:   ${buy_hold_final:,.2f}")
    print(f"  Return:        {buy_hold_return:+.2f}%")

    print(f"\nProduction Strategy:")
    print(f"  Final Value:   ${results['final_value']:,.2f}")
    print(f"  Return:        {results['total_return_pct']:+.2f}%")

    print(f"\nDifference:")
    print(f"  Alpha:         {results['alpha']:+.2f}%")
    print(f"  Extra Profit:  ${results['final_value'] - buy_hold_final:+,.2f}")

    if results['alpha'] > 0:
        print(f"\n✅ Strategy BEAT buy & hold by {results['alpha']:.2f}%!")
    else:
        print(f"\n⚠️  Strategy UNDERPERFORMED buy & hold by {abs(results['alpha']):.2f}%")

    print(f"{'='*80}\n")

    return results


if __name__ == "__main__":
    import sys

    # Get start date from command line or use default
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2025-07-01"
    initial_capital = float(sys.argv[2]) if len(sys.argv) > 2 else 10000

    run_simulation_from_date(start_date, initial_capital)
