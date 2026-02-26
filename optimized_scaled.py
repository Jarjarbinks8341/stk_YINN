"""
Optimized Scaled Entry Strategies

Testing multiple approaches to get closer to all-in performance
"""
import pandas as pd
import numpy as np
from scaled_backtest import ScaledPositionTracker, calculate_time_weighted_levels

def scaled_v1_tight_around_support(data, initial_capital=10000, lookback=60, verbose=True):
    """
    VERSION 1: Tight Scaling Around Support

    Buy levels (much tighter):
    - 50% when AT support (within 2%)
    - 25% if drops 3% BELOW support (catching falling knife)
    - 25% if price BOUNCES 2% from support (confirmation)

    Sell levels:
    - 50% at resistance
    - 25% if rises 3% above
    - 25% on the way up (90% to resistance)
    """
    tracker = ScaledPositionTracker(initial_capital)
    start_idx = lookback

    buy_levels = {'at_support': False, 'below': False, 'bounce': False}
    sell_levels = {'at_resistance': False, 'above': False, 'partial': False}

    lowest_price = None

    if verbose:
        print("="*80)
        print("OPTIMIZED SCALED V1: Tight Around Support")
        print("="*80)
        print("Buy: 50% at support, 25% if drops 3% below, 25% on 2% bounce")
        print("="*80 + "\n")

    for i in range(start_idx, len(data)):
        historical_data = data.iloc[:i].copy()
        support, resistance, _, _ = calculate_time_weighted_levels(historical_data, lookback)

        if support is None or resistance is None:
            continue

        current_price = data.iloc[i]['close']
        current_date = data.index[i]

        # Track lowest price for bounce detection
        if tracker.position_shares == 0:
            lowest_price = None
            buy_levels = {'at_support': False, 'below': False, 'bounce': False}
        else:
            if lowest_price is None or current_price < lowest_price:
                lowest_price = current_price

        # BUY LOGIC
        # Level 1: At support (within 2%)
        if current_price <= support * 1.02 and not buy_levels['at_support']:
            shares = tracker.buy(current_date, current_price, 0.50)
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 50%  | ${current_price:6.2f} | At support (${support:.2f})")
            buy_levels['at_support'] = True
            lowest_price = current_price

        # Level 2: Below support (catching knife)
        elif current_price < support * 0.97 and not buy_levels['below']:
            shares = tracker.buy(current_date, current_price, 0.50)  # 50% of remaining (= 25% total)
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 25%  | ${current_price:6.2f} | 3% below support")
            buy_levels['below'] = True

        # Level 3: Bounce confirmation
        elif lowest_price and current_price > lowest_price * 1.02 and not buy_levels['bounce'] and buy_levels['at_support']:
            shares = tracker.buy(current_date, current_price, 1.0)  # Rest of cash
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 25%  | ${current_price:6.2f} | Bounce confirmation (+2% from low)")
            buy_levels['bounce'] = True

        # SELL LOGIC
        if tracker.position_shares > 0:
            # Level 1: At resistance
            if current_price >= resistance * 0.98 and not sell_levels['at_resistance']:
                shares = tracker.sell(current_date, current_price, 0.50)
                if shares > 0 and verbose:
                    trade = tracker.trades[-1]
                    print(f"{current_date.strftime('%Y-%m-%d')} | SELL 50% | ${current_price:6.2f} | At resistance (${resistance:.2f}) | P&L: ${trade['pnl']:+,.2f}")
                sell_levels['at_resistance'] = True

            # Level 2: Approaching resistance (90%)
            elif current_price >= resistance * 0.90 and current_price < resistance * 0.98 and not sell_levels['partial']:
                shares = tracker.sell(current_date, current_price, 0.30)
                if shares > 0 and verbose:
                    trade = tracker.trades[-1]
                    print(f"{current_date.strftime('%Y-%m-%d')} | SELL 25% | ${current_price:6.2f} | Approaching resistance | P&L: ${trade['pnl']:+,.2f}")
                sell_levels['partial'] = True

            # Level 3: Above resistance (momentum)
            elif current_price > resistance * 1.03 and not sell_levels['above']:
                shares = tracker.sell(current_date, current_price, 1.0)
                if shares > 0 and verbose:
                    trade = tracker.trades[-1]
                    print(f"{current_date.strftime('%Y-%m-%d')} | SELL 25% | ${current_price:6.2f} | Above resistance | P&L: ${trade['pnl']:+,.2f}")
                sell_levels['above'] = True
                sell_levels = {'at_resistance': False, 'above': False, 'partial': False}

    final_price = data.iloc[-1]['close']
    final_value = tracker.get_portfolio_value(final_price)

    return {
        'name': 'Tight Scaling',
        'final_value': final_value,
        'return_pct': ((final_value - initial_capital) / initial_capital) * 100,
        'trades': len(tracker.trades)
    }, tracker


def scaled_v2_support_only(data, initial_capital=10000, lookback=60, verbose=True):
    """
    VERSION 2: Support Zone Only (Most Conservative)

    Buy ONLY when at/near support:
    - 40% when price touches support
    - 30% if it drops to 3% below support
    - 30% if it bounces 5% from support

    This mimics all-in but with small scaling for safety
    """
    tracker = ScaledPositionTracker(initial_capital)
    start_idx = lookback

    buy_levels = {'first': False, 'drop': False, 'bounce': False}
    entry_price = None

    if verbose:
        print("="*80)
        print("OPTIMIZED SCALED V2: Support Zone Only")
        print("="*80)
        print("Buy: Only when AT support zone (no early entries)")
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
            buy_levels = {'first': False, 'drop': False, 'bounce': False}
            entry_price = None

        # BUY LOGIC - only in support zone
        if current_price <= support * 1.01 and not buy_levels['first']:
            shares = tracker.buy(current_date, current_price, 0.40)
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 40%  | ${current_price:6.2f} | Support touch")
            buy_levels['first'] = True
            entry_price = current_price

        elif current_price < support * 0.97 and buy_levels['first'] and not buy_levels['drop']:
            shares = tracker.buy(current_date, current_price, 0.50)  # 50% of remaining = 30% total
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 30%  | ${current_price:6.2f} | Below support")
            buy_levels['drop'] = True

        elif entry_price and current_price > entry_price * 1.05 and buy_levels['first'] and not buy_levels['bounce']:
            shares = tracker.buy(current_date, current_price, 1.0)  # Rest
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 30%  | ${current_price:6.2f} | Bounce +5%")
            buy_levels['bounce'] = True

        # SELL LOGIC - simple, at resistance
        if tracker.position_shares > 0 and current_price >= resistance * 0.98:
            shares = tracker.sell(current_date, current_price, 1.0)  # Sell all at once
            if shares > 0 and verbose:
                trade = tracker.trades[-1]
                print(f"{current_date.strftime('%Y-%m-%d')} | SELL ALL | ${current_price:6.2f} | At resistance | P&L: ${trade['pnl']:+,.2f}")

    final_price = data.iloc[-1]['close']
    final_value = tracker.get_portfolio_value(final_price)

    return {
        'name': 'Support Only',
        'final_value': final_value,
        'return_pct': ((final_value - initial_capital) / initial_capital) * 100,
        'trades': len(tracker.trades)
    }, tracker


def scaled_v3_smart_dca(data, initial_capital=10000, lookback=60, verbose=True):
    """
    VERSION 3: Smart DCA (Dollar Cost Average)

    Buy in equal chunks as price approaches support:
    - 33% at 5% above support (early bird)
    - 33% at support
    - 34% at 5% below support (greedy)

    Sell all at resistance (no scaling out)
    """
    tracker = ScaledPositionTracker(initial_capital)
    start_idx = lookback

    buy_levels = {'early': False, 'support': False, 'below': False}

    if verbose:
        print("="*80)
        print("OPTIMIZED SCALED V3: Smart DCA")
        print("="*80)
        print("Buy: 33% at +5%, 33% at support, 34% at -5%")
        print("="*80 + "\n")

    for i in range(start_idx, len(data)):
        historical_data = data.iloc[:i].copy()
        support, resistance, _, _ = calculate_time_weighted_levels(historical_data, lookback)

        if support is None or resistance is None:
            continue

        current_price = data.iloc[i]['close']
        current_date = data.index[i]

        if tracker.position_shares == 0:
            buy_levels = {'early': False, 'support': False, 'below': False}

        # BUY LOGIC
        if current_price <= support * 1.05 and current_price > support * 1.01 and not buy_levels['early']:
            shares = tracker.buy(current_date, current_price, 0.33)
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 33%  | ${current_price:6.2f} | 5% above support")
            buy_levels['early'] = True

        elif current_price <= support * 1.01 and current_price >= support * 0.97 and not buy_levels['support']:
            shares = tracker.buy(current_date, current_price, 0.50)  # 50% of remaining = 33% total
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 33%  | ${current_price:6.2f} | At support")
            buy_levels['support'] = True

        elif current_price < support * 0.95 and not buy_levels['below']:
            shares = tracker.buy(current_date, current_price, 1.0)  # Rest
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 34%  | ${current_price:6.2f} | 5% below support")
            buy_levels['below'] = True

        # SELL - all at once at resistance
        if tracker.position_shares > 0 and current_price >= resistance * 0.98:
            shares = tracker.sell(current_date, current_price, 1.0)
            if shares > 0 and verbose:
                trade = tracker.trades[-1]
                print(f"{current_date.strftime('%Y-%m-%d')} | SELL ALL | ${current_price:6.2f} | At resistance | P&L: ${trade['pnl']:+,.2f}")

    final_price = data.iloc[-1]['close']
    final_value = tracker.get_portfolio_value(final_price)

    return {
        'name': 'Smart DCA',
        'final_value': final_value,
        'return_pct': ((final_value - initial_capital) / initial_capital) * 100,
        'trades': len(tracker.trades)
    }, tracker


def compare_all_optimized():
    """Compare all optimized versions + original"""
    from backtest import load_data, run_backtest
    from production_strategy import YINNProductionStrategy
    import pandas as pd

    data = load_data()
    data_2025 = data[data.index >= pd.to_datetime("2025-01-01").date()].copy()
    initial_capital = 10000

    print("\n" + "="*80)
    print("TESTING ALL OPTIMIZED SCALED STRATEGIES")
    print("="*80 + "\n")

    # Test all versions
    results = []

    # Baseline: All-In
    print("BASELINE: ALL-IN STRATEGY")
    print("-"*80)
    allin = YINNProductionStrategy(lookback=60)
    allin_result = run_backtest(allin, data_2025.copy(), initial_capital, verbose=False)
    results.append({
        'name': 'All-In (Baseline)',
        'final_value': allin_result['final_value'],
        'return_pct': allin_result['total_return_pct'],
        'trades': allin_result.get('total_trades', 0)
    })
    print(f"Return: {allin_result['total_return_pct']:.2f}%\n")

    # V1: Tight Scaling
    result1, _ = scaled_v1_tight_around_support(data_2025.copy(), initial_capital, verbose=False)
    results.append(result1)
    print(f"\nV1 - {result1['name']}: {result1['return_pct']:.2f}%")

    # V2: Support Only
    result2, _ = scaled_v2_support_only(data_2025.copy(), initial_capital, verbose=False)
    results.append(result2)
    print(f"V2 - {result2['name']}: {result2['return_pct']:.2f}%")

    # V3: Smart DCA
    result3, _ = scaled_v3_smart_dca(data_2025.copy(), initial_capital, verbose=False)
    results.append(result3)
    print(f"V3 - {result3['name']}: {result3['return_pct']:.2f}%")

    # Summary
    print("\n" + "="*80)
    print("FINAL COMPARISON")
    print("="*80)

    df = pd.DataFrame(results)
    df = df.sort_values('return_pct', ascending=False)

    print(f"\n{'Rank':<6} {'Strategy':<25} {'Return':<12} {'Final Value':<15} {'Trades':<8}")
    print("-"*80)

    for idx, row in df.iterrows():
        rank = df.index.get_loc(idx) + 1
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        print(f"{medal:<6} {row['name']:<25} {row['return_pct']:>6.2f}%     ${row['final_value']:>10,.2f}    {row['trades']:>5}")

    # Best scaled vs all-in
    best_scaled = df[df['name'] != 'All-In (Baseline)'].iloc[0]
    baseline = df[df['name'] == 'All-In (Baseline)'].iloc[0]

    diff = best_scaled['return_pct'] - baseline['return_pct']

    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    if abs(diff) < 10:
        print(f"\n✅ SUCCESS! Best scaled strategy is CLOSE to all-in!")
        print(f"   Gap: only {abs(diff):.2f}%")
    elif diff > 0:
        print(f"\n🎉 WINNER! {best_scaled['name']} BEAT all-in by {diff:.2f}%!")
    else:
        print(f"\n📊 Best scaled: {best_scaled['name']}")
        print(f"   Still {abs(diff):.2f}% behind all-in")
        print(f"   But offers: lower risk, gradual entries, psychological comfort")

    print("\n" + "="*80)

    return results


if __name__ == "__main__":
    compare_all_optimized()
