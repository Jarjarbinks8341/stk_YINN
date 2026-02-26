"""Compare Scaled vs All-In strategies"""
from backtest import load_data, run_backtest
from production_strategy import YINNProductionStrategy
from scaled_backtest import run_scaled_backtest
import pandas as pd

def compare_scaled_vs_allin():
    """Compare both strategies side by side"""
    data = load_data()
    data_2025 = data[data.index >= pd.to_datetime("2025-01-01").date()].copy()

    initial_capital = 10000

    print("="*80)
    print("STRATEGY COMPARISON: Scaled Entry vs All-In")
    print("="*80 + "\n")

    # Run All-In Strategy
    print("STRATEGY 1: ALL-IN (Original Production Strategy)")
    print("-"*80)
    allin_strategy = YINNProductionStrategy(lookback=60, min_distance=5)
    allin_results = run_backtest(allin_strategy, data_2025.copy(), initial_capital, verbose=False)

    print(f"Return: {allin_results['total_return_pct']:.2f}%")
    print(f"Trades: {allin_results.get('total_trades', 0)}")
    print(f"Win Rate: {allin_results.get('win_rate', 0):.1f}%")
    print()

    # Run Scaled Strategy
    print("STRATEGY 2: SCALED ENTRY (30% + 30% + 40%)")
    print("-"*80)
    scaled_results, tracker = run_scaled_backtest(data_2025.copy(), initial_capital, verbose=False)

    print(f"Return: {scaled_results['total_return_pct']:.2f}%")
    print(f"Trades: {scaled_results['total_trades']}")
    print(f"Buys: {scaled_results['buys']}, Sells: {scaled_results['sells']}")
    print()

    # Comparison
    print("="*80)
    print("SIDE-BY-SIDE COMPARISON")
    print("="*80)

    comparison_data = {
        'Metric': [
            'Initial Capital',
            'Final Value',
            'Total Return',
            'Return %',
            'Alpha vs B&H',
            'Total Transactions',
            'Win Rate'
        ],
        'All-In Strategy': [
            f"${initial_capital:,.2f}",
            f"${allin_results['final_value']:,.2f}",
            f"${allin_results['total_return']:,.2f}",
            f"{allin_results['total_return_pct']:.2f}%",
            f"{allin_results['alpha']:.2f}%",
            f"{allin_results.get('total_trades', 0)}",
            f"{allin_results.get('win_rate', 0):.1f}%"
        ],
        'Scaled Entry': [
            f"${initial_capital:,.2f}",
            f"${scaled_results['final_value']:,.2f}",
            f"${scaled_results['total_return']:,.2f}",
            f"{scaled_results['total_return_pct']:.2f}%",
            f"{scaled_results['alpha']:.2f}%",
            f"{scaled_results['total_trades']}",
            "N/A"
        ]
    }

    df = pd.DataFrame(comparison_data)

    print(df.to_string(index=False))

    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    diff_return = allin_results['total_return_pct'] - scaled_results['total_return_pct']
    diff_value = allin_results['final_value'] - scaled_results['final_value']

    if diff_return > 0:
        print(f"\n✅ ALL-IN STRATEGY WINS!")
        print(f"   Better by: {diff_return:.2f}% ({diff_value:+,.2f} more profit)")
        print(f"\n   Why All-In Won:")
        print(f"   • Went ALL-IN at lowest prices (better avg cost)")
        print(f"   • Simpler: fewer transactions = lower potential slippage")
        print(f"   • Higher conviction trades")
    else:
        print(f"\n✅ SCALED STRATEGY WINS!")
        print(f"   Better by: {abs(diff_return):.2f}% ({abs(diff_value):+,.2f} more profit)")
        print(f"\n   Why Scaled Won:")
        print(f"   • Better average entry prices")
        print(f"   • More conservative = lower risk")
        print(f"   • Dollar cost averaging benefit")

    print(f"\n   Pros of Scaled Entry:")
    print(f"   ✅ Lower risk (staged entries)")
    print(f"   ✅ More transactions = more opportunities")
    print(f"   ✅ Better for larger accounts (less slippage)")
    print(f"   ✅ Psychological: easier to stomach gradual buys")

    print(f"\n   Pros of All-In:")
    print(f"   ✅ Higher returns in strong trends")
    print(f"   ✅ Simpler to execute")
    print(f"   ✅ Better when bottoms are clear")
    print(f"   ✅ Fewer transactions = lower costs")

    print("\n" + "="*80)

    return allin_results, scaled_results


if __name__ == "__main__":
    compare_scaled_vs_allin()
