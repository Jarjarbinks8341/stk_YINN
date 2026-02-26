"""
Scaled Entry/Exit Backtesting with Position Management

Implements gradual buying and selling:
- Buy in 3 stages: 30% + 30% + 40%
- Sell in 3 stages: 30% + 30% + 40%
"""
import pandas as pd
import numpy as np
from datetime import datetime
from backtest import load_data
from peak_detector import find_distributed_peaks_troughs

class ScaledPositionTracker:
    """Track scaled positions with multiple entry/exit levels"""

    def __init__(self, initial_capital):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position_shares = 0
        self.position_cost = 0
        self.trades = []

    def buy(self, date, price, pct_of_cash):
        """Buy shares with percentage of available cash"""
        if self.cash <= 0:
            return 0

        cash_to_use = self.cash * pct_of_cash
        shares = int(cash_to_use / price)

        if shares > 0:
            cost = shares * price
            self.cash -= cost
            self.position_shares += shares
            self.position_cost += cost

            self.trades.append({
                'date': date,
                'action': 'BUY',
                'price': price,
                'shares': shares,
                'cost': cost,
                'pct_used': pct_of_cash * 100,
                'total_shares': self.position_shares,
                'cash_remaining': self.cash
            })

            return shares
        return 0

    def sell(self, date, price, pct_of_position):
        """Sell percentage of current position"""
        if self.position_shares <= 0:
            return 0

        shares_to_sell = int(self.position_shares * pct_of_position)

        if shares_to_sell > 0:
            proceeds = shares_to_sell * price

            # Calculate P&L for this partial sale
            avg_cost_per_share = self.position_cost / self.position_shares if self.position_shares > 0 else 0
            cost_of_shares_sold = shares_to_sell * avg_cost_per_share
            pnl = proceeds - cost_of_shares_sold
            pnl_pct = (pnl / cost_of_shares_sold * 100) if cost_of_shares_sold > 0 else 0

            self.cash += proceeds
            self.position_shares -= shares_to_sell
            self.position_cost -= cost_of_shares_sold

            self.trades.append({
                'date': date,
                'action': 'SELL',
                'price': price,
                'shares': shares_to_sell,
                'proceeds': proceeds,
                'pct_sold': pct_of_position * 100,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'total_shares': self.position_shares,
                'cash': self.cash
            })

            return shares_to_sell
        return 0

    def get_portfolio_value(self, current_price):
        """Get total portfolio value"""
        position_value = self.position_shares * current_price if self.position_shares > 0 else 0
        return self.cash + position_value

    def get_position_pct(self):
        """Get current position as % of capital"""
        if self.position_shares == 0:
            return 0
        return (self.position_cost / self.initial_capital) * 100


def calculate_time_weighted_levels(data, lookback=60, min_distance=5):
    """Calculate time-weighted support and resistance"""
    peaks, troughs = find_distributed_peaks_troughs(
        data, lookback, min_distance, num_peaks=3, num_troughs=3
    )

    if not peaks or not troughs:
        return None, None, None, None

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

    return support, resistance, peaks, troughs


def run_scaled_backtest(data, initial_capital=10000, lookback=60, verbose=True):
    """
    Run backtest with scaled entry/exit

    BUY levels:
    - 30% when 80% to support (20% in range)
    - 30% when 90% to support (10% in range)
    - 40% when at support (0% in range)

    SELL levels:
    - 30% when 80% to resistance (80% in range)
    - 30% when 90% to resistance (90% in range)
    - 40% when at resistance (100% in range)
    """
    tracker = ScaledPositionTracker(initial_capital)

    # Track which levels we've already traded at
    buy_levels_hit = {80: False, 90: False, 100: False}
    sell_levels_hit = {80: False, 90: False, 100: False}

    start_idx = lookback

    if verbose:
        print("="*80)
        print("SCALED ENTRY/EXIT BACKTEST")
        print("="*80)
        print(f"Period: {data.index[start_idx]} to {data.index[-1]}")
        print(f"Initial Capital: ${initial_capital:,.2f}")
        print(f"Lookback: {lookback} days")
        print("="*80 + "\n")

    for i in range(start_idx, len(data)):
        historical_data = data.iloc[:i].copy()
        support, resistance, peaks, troughs = calculate_time_weighted_levels(
            historical_data, lookback
        )

        if support is None or resistance is None:
            continue

        current_price = data.iloc[i]['close']
        current_date = data.index[i]

        # Calculate position in range
        range_width = resistance - support
        if range_width > 0:
            position_pct = ((current_price - support) / range_width) * 100
        else:
            continue

        # BUYING LOGIC (when moving toward support)
        if tracker.position_shares == 0:
            # Reset buy levels when no position
            buy_levels_hit = {80: False, 90: False, 100: False}

        # Buy Level 1: 80% to support (20% in range)
        if position_pct <= 20 and not buy_levels_hit[80]:
            shares = tracker.buy(current_date, current_price, 0.30)  # 30% of cash
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 30%  | ${current_price:6.2f} | Level 1 (80% to support) | Shares: {shares} | Cash: ${tracker.cash:,.2f}")
                buy_levels_hit[80] = True

        # Buy Level 2: 90% to support (10% in range)
        elif position_pct <= 10 and not buy_levels_hit[90]:
            shares = tracker.buy(current_date, current_price, 0.30)  # 30% of remaining cash
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 30%  | ${current_price:6.2f} | Level 2 (90% to support) | Shares: {shares} | Cash: ${tracker.cash:,.2f}")
                buy_levels_hit[90] = True

        # Buy Level 3: At support (0% in range)
        elif position_pct <= 2 and not buy_levels_hit[100]:  # 2% buffer
            shares = tracker.buy(current_date, current_price, 1.0)  # All remaining cash (40%)
            if shares > 0 and verbose:
                print(f"{current_date.strftime('%Y-%m-%d')} | BUY 40%  | ${current_price:6.2f} | Level 3 (at support)     | Shares: {shares} | Cash: ${tracker.cash:,.2f}")
                buy_levels_hit[100] = True

        # SELLING LOGIC (when moving toward resistance)
        if tracker.position_shares > 0:
            # Reset sell levels when we have a position
            if not any(sell_levels_hit.values()):
                sell_levels_hit = {80: False, 90: False, 100: False}

            # Sell Level 1: 80% to resistance
            if position_pct >= 80 and not sell_levels_hit[80]:
                shares = tracker.sell(current_date, current_price, 0.30)  # 30% of position
                if shares > 0 and verbose:
                    trade = tracker.trades[-1]
                    print(f"{current_date.strftime('%Y-%m-%d')} | SELL 30% | ${current_price:6.2f} | Level 1 (80% to resist)  | Shares: {shares} | P&L: ${trade['pnl']:+.2f} ({trade['pnl_pct']:+.2f}%)")
                    sell_levels_hit[80] = True

            # Sell Level 2: 90% to resistance
            elif position_pct >= 90 and not sell_levels_hit[90]:
                shares = tracker.sell(current_date, current_price, 0.30)  # 30% of remaining
                if shares > 0 and verbose:
                    trade = tracker.trades[-1]
                    print(f"{current_date.strftime('%Y-%m-%d')} | SELL 30% | ${current_price:6.2f} | Level 2 (90% to resist)  | Shares: {shares} | P&L: ${trade['pnl']:+.2f} ({trade['pnl_pct']:+.2f}%)")
                    sell_levels_hit[90] = True

            # Sell Level 3: At resistance
            elif position_pct >= 98 and not sell_levels_hit[100]:  # 2% buffer
                shares = tracker.sell(current_date, current_price, 1.0)  # All remaining (40%)
                if shares > 0 and verbose:
                    trade = tracker.trades[-1]
                    print(f"{current_date.strftime('%Y-%m-%d')} | SELL 40% | ${current_price:6.2f} | Level 3 (at resist)      | Shares: {shares} | P&L: ${trade['pnl']:+.2f} ({trade['pnl_pct']:+.2f}%)")
                    sell_levels_hit[100] = True
                    # Reset for next cycle
                    sell_levels_hit = {80: False, 90: False, 100: False}

    # Final portfolio value
    final_price = data.iloc[-1]['close']
    final_value = tracker.get_portfolio_value(final_price)

    # Calculate buy & hold
    buy_hold_shares = int(initial_capital / data.iloc[start_idx]['close'])
    buy_hold_final = buy_hold_shares * final_price
    buy_hold_return = ((buy_hold_final - initial_capital) / initial_capital) * 100

    # Results
    results = {
        'initial_capital': initial_capital,
        'final_value': final_value,
        'total_return': final_value - initial_capital,
        'total_return_pct': ((final_value - initial_capital) / initial_capital) * 100,
        'buy_hold_return_pct': buy_hold_return,
        'alpha': ((final_value - initial_capital) / initial_capital) * 100 - buy_hold_return,
        'total_trades': len(tracker.trades),
        'buys': len([t for t in tracker.trades if t['action'] == 'BUY']),
        'sells': len([t for t in tracker.trades if t['action'] == 'SELL']),
    }

    if verbose:
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"Initial Capital:  ${results['initial_capital']:>12,.2f}")
        print(f"Final Value:      ${results['final_value']:>12,.2f}")
        print(f"Total Return:     ${results['total_return']:>12,.2f} ({results['total_return_pct']:>+6.2f}%)")
        print(f"Buy & Hold:       ${buy_hold_final:>12,.2f} ({results['buy_hold_return_pct']:>+6.2f}%)")
        print(f"Alpha:                                 ({results['alpha']:>+6.2f}%)")
        print(f"\nTotal Transactions: {results['total_trades']}")
        print(f"  Buys:  {results['buys']}")
        print(f"  Sells: {results['sells']}")
        print("="*80 + "\n")

    return results, tracker


if __name__ == "__main__":
    data = load_data()

    print("Testing Scaled Entry/Exit Strategy\n")

    # Run from Jan 1, 2025
    data_2025 = data[data.index >= pd.to_datetime("2025-01-01").date()].copy()

    results, tracker = run_scaled_backtest(
        data_2025,
        initial_capital=10000,
        lookback=60,
        verbose=True
    )
