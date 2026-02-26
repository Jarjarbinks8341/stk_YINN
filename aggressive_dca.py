"""
Aggressive DCA Strategy - Best Compromise

Buy: 50% at support (ensures major deployment)
Buy: 25% if drops 5% below (catching knife)
Buy: 25% if bounces 3% (confirmation)
Sell: 100% at resistance

This should get closer to all-in performance while keeping some DCA benefits
"""
import pandas as pd
import numpy as np
from scaled_backtest import ScaledPositionTracker, calculate_time_weighted_levels
from backtest import load_data, run_backtest
from production_strategy import YINNProductionStrategy

def aggressive_dca_backtest(data, initial_capital=10000, lookback=60, verbose=True):
    """
    Aggressive DCA: Deploy 50% immediately at support, scale the rest

    Buy levels:
    - 50% at support (within 2%)
    - 25% if drops 5% below support
    - 25% if price bounces 3% from entry (confirmation)

    Sell: All at once at resistance
    """
    tracker = ScaledPositionTracker(initial_capital)
    start_idx = lookback

    buy_levels = {'main': False, 'below': False, 'bounce': False}
    entry_price = None
    lowest_price = None

    if verbose:
        print("="*80)
        print("AGGRESSIVE DCA STRATEGY")
        print("="*80)
        print("Buy: 50% at support, 25% if drops 5%, 25% on bounce")
        print("Sell: 100% at resistance")
        print("="*80 + "\n")

    for i in range(start_idx, len(data)):
        historical_data = data.iloc[:i].copy()
        support, resistance, _, _ = calculate_time_weighted_levels(historical_data, lookback)

        if support is None or resistance is None:
            continue

        current_price = data.iloc[i]['close']
        current_date = data.index[i]

        # Reset when no position
        if tracker.position_shares == 0:
            buy_levels = {'main': False, 'below': False, 'bounce': False}
            entry_price = None
            lowest_price = None

        # Track lowest price since entry
        if tracker.position_shares > 0:
            if lowest_price is None or current_price < lowest_price:
                lowest_price = current_price

        # BUY LOGIC

        # Level 1: Main entry at support (50% - BIGGEST CHUNK)
        if current_price <= support * 1.02 and not buy_levels['main']:
            shares = tracker.buy(current_date, current_price, 0.50)  # 50% of capital
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 50%  | ${current_price:6.2f} | Main entry at support (${support:.2f})")
            buy_levels['main'] = True
            entry_price = current_price
            lowest_price = current_price

        # Level 2: Catch falling knife (25% more)
        elif current_price < support * 0.95 and buy_levels['main'] and not buy_levels['below']:
            shares = tracker.buy(current_date, current_price, 0.50)  # 50% of remaining = 25% total
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 25%  | ${current_price:6.2f} | 5% below support - catching knife")
            buy_levels['below'] = True

        # Level 3: Bounce confirmation (25% more)
        elif lowest_price and current_price > lowest_price * 1.03 and buy_levels['main'] and not buy_levels['bounce']:
            shares = tracker.buy(current_date, current_price, 1.0)  # Rest of cash
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 25%  | ${current_price:6.2f} | Bounce +3% - confirmation")
            buy_levels['bounce'] = True

        # SELL LOGIC - Simple, all at resistance
        if tracker.position_shares > 0 and current_price >= resistance * 0.98:
            shares = tracker.sell(current_date, current_price, 1.0)
            if shares > 0 and verbose:
                trade = tracker.trades[-1]
                print(f"{current_date.strftime('%Y-%m-%d')} | SELL ALL | ${current_price:6.2f} | At resistance (${resistance:.2f}) | P&L: ${trade['pnl']:+,.2f} ({trade['pnl_pct']:+.2f}%)")

    final_price = data.iloc[-1]['close']
    final_value = tracker.get_portfolio_value(final_price)

    # Calculate buy & hold
    buy_hold_shares = int(initial_capital / data.iloc[start_idx]['close'])
    buy_hold_final = buy_hold_shares * final_price
    buy_hold_return = ((buy_hold_final - initial_capital) / initial_capital) * 100

    results = {
        'name': 'Aggressive DCA',
        'initial_capital': initial_capital,
        'final_value': final_value,
        'total_return': final_value - initial_capital,
        'total_return_pct': ((final_value - initial_capital) / initial_capital) * 100,
        'buy_hold_return_pct': buy_hold_return,
        'alpha': ((final_value - initial_capital) / initial_capital) * 100 - buy_hold_return,
        'trades': len(tracker.trades),
        'buys': len([t for t in tracker.trades if t['action'] == 'BUY']),
        'sells': len([t for t in tracker.trades if t['action'] == 'SELL']),
    }

    if verbose:
        print("\n" + "="*80)
        print("AGGRESSIVE DCA RESULTS")
        print("="*80)
        print(f"Initial Capital:  ${results['initial_capital']:>12,.2f}")
        print(f"Final Value:      ${results['final_value']:>12,.2f}")
        print(f"Total Return:     ${results['total_return']:>12,.2f} ({results['total_return_pct']:>+6.2f}%)")
        print(f"Buy & Hold:       ${buy_hold_final:>12,.2f} ({results['buy_hold_return_pct']:>+6.2f}%)")
        print(f"Alpha:                                 ({results['alpha']:>+6.2f}%)")
        print(f"\nTotal Transactions: {results['trades']}")
        print(f"  Buys:  {results['buys']}")
        print(f"  Sells: {results['sells']}")
        print("="*80 + "\n")

    return results, tracker


def compare_aggressive_vs_allin():
    """Compare Aggressive DCA vs All-In from Jan 1, 2025"""
    data = load_data()
    data_2025 = data[data.index >= pd.to_datetime("2025-01-01").date()].copy()

    initial_capital = 10000

    print("\n" + "="*80)
    print("COMPARISON: AGGRESSIVE DCA vs ALL-IN")
    print("Starting: January 1, 2025 | Capital: $10,000")
    print("="*80 + "\n")

    # Test All-In
    print("1️⃣  ALL-IN STRATEGY (Baseline)")
    print("="*80)
    allin_strategy = YINNProductionStrategy(lookback=60, min_distance=5)
    allin_results = run_backtest(allin_strategy, data_2025.copy(), initial_capital, verbose=True)

    print("\n" + "="*80)
    print("="*80 + "\n")

    # Test Aggressive DCA
    print("2️⃣  AGGRESSIVE DCA STRATEGY")
    print("="*80)
    dca_results, tracker = aggressive_dca_backtest(data_2025.copy(), initial_capital, verbose=True)

    # Side by side comparison
    print("\n" + "="*80)
    print("FINAL COMPARISON")
    print("="*80)

    comparison = pd.DataFrame({
        'Metric': [
            'Initial Capital',
            'Final Value',
            'Total Profit',
            'Return %',
            'Alpha vs B&H',
            'Transactions',
            'Win Rate',
            'Avg Hold Days'
        ],
        'All-In': [
            f"${initial_capital:,.2f}",
            f"${allin_results['final_value']:,.2f}",
            f"${allin_results['total_return']:,.2f}",
            f"{allin_results['total_return_pct']:.2f}%",
            f"{allin_results['alpha']:.2f}%",
            f"{allin_results.get('total_trades', 0)}",
            f"{allin_results.get('win_rate', 0):.1f}%",
            f"{allin_results.get('avg_hold_days', 0):.1f}"
        ],
        'Aggressive DCA': [
            f"${initial_capital:,.2f}",
            f"${dca_results['final_value']:,.2f}",
            f"${dca_results['total_return']:,.2f}",
            f"{dca_results['total_return_pct']:.2f}%",
            f"{dca_results['alpha']:.2f}%",
            f"{dca_results['trades']}",
            "N/A",
            "N/A"
        ]
    })

    print("\n" + comparison.to_string(index=False))

    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    diff_return = allin_results['total_return_pct'] - dca_results['total_return_pct']
    diff_value = allin_results['final_value'] - dca_results['final_value']

    print(f"\nPerformance Gap: {abs(diff_return):.2f}%")
    print(f"Profit Difference: ${abs(diff_value):,.2f}")

    if abs(diff_return) < 15:
        print(f"\n✅ VERY CLOSE! Gap is only {abs(diff_return):.2f}%")
        print("   Both strategies are excellent choices!")
    elif diff_return > 0:
        print(f"\n🏆 All-In wins by {diff_return:.2f}%")
    else:
        print(f"\n🏆 Aggressive DCA wins by {abs(diff_return):.2f}%!")

    # Pros/Cons
    print(f"\n{'='*80}")
    print("TRADE-OFFS")
    print(f"{'='*80}")

    print(f"\n📊 All-In Strategy:")
    print(f"   Return: {allin_results['total_return_pct']:.2f}%")
    print(f"   Pros: ✅ Maximum returns ✅ Simpler ✅ Fewer trades")
    print(f"   Cons: ❌ All-or-nothing ❌ Higher psychological stress")

    print(f"\n📊 Aggressive DCA:")
    print(f"   Return: {dca_results['total_return_pct']:.2f}%")
    print(f"   Pros: ✅ 50% deployed immediately ✅ Lower risk ✅ Easier to execute")
    print(f"   Cons: ❌ Slightly lower returns ❌ More transactions")

    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")

    if abs(diff_return) < 10:
        print("\n💡 Use Aggressive DCA if:")
        print("   • You want peace of mind")
        print("   • You're new to trading")
        print("   • You have a larger account ($50k+)")
        print("   • You prefer gradual entries")
        print("\n💡 Use All-In if:")
        print("   • You want maximum returns")
        print("   • You're comfortable with volatility")
        print("   • You have high conviction")
        print("   • You prefer simplicity")
    else:
        print(f"\n💡 Stick with All-In Strategy")
        print(f"   The {diff_return:.2f}% performance gap is significant")

    print(f"\n{'='*80}\n")

    return allin_results, dca_results


if __name__ == "__main__":
    compare_aggressive_vs_allin()
