"""Backtesting engine for trading strategies"""
import pandas as pd
from datetime import datetime
from database import get_session, DailyPrice
from strategy import Strategy, Signal
import config

def load_data(ticker: str = config.TICKER, start_date: str = None,
              end_date: str = None) -> pd.DataFrame:
    """
    Load historical data from database

    Args:
        ticker: Stock ticker
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame with OHLCV data
    """
    session = get_session()

    try:
        query = session.query(DailyPrice).filter_by(ticker=ticker)

        if start_date:
            query = query.filter(DailyPrice.date >= start_date)
        if end_date:
            query = query.filter(DailyPrice.date <= end_date)

        query = query.order_by(DailyPrice.date.asc())

        results = query.all()

        if not results:
            return pd.DataFrame()

        # Convert to DataFrame
        data = pd.DataFrame([{
            'date': r.date,
            'open': r.open,
            'high': r.high,
            'low': r.low,
            'close': r.close,
            'volume': r.volume,
            'adj_close': r.adj_close
        } for r in results])

        data.set_index('date', inplace=True)
        return data

    finally:
        session.close()


def run_backtest(strategy: Strategy, data: pd.DataFrame,
                initial_capital: float = 10000, position_size: float = 1.0,
                verbose: bool = True) -> dict:
    """
    Run backtest for a strategy

    Args:
        strategy: Strategy instance to test
        data: Historical price data
        initial_capital: Starting capital
        position_size: Fraction of capital to use per trade (0-1)
        verbose: Print trade details

    Returns:
        Dictionary with backtest results
    """
    if data.empty:
        return {'error': 'No data provided'}

    # Initialize strategy
    strategy.initialize(initial_capital)

    # Calculate signals
    signals = strategy.calculate_signals(data.copy())

    if verbose:
        print(f"\n{'='*80}")
        print(f"Backtesting: {strategy.name}")
        print(f"Period: {data.index[0]} to {data.index[-1]}")
        print(f"Initial Capital: ${initial_capital:,.2f}")
        print(f"Position Size: {position_size*100:.0f}%")
        print(f"{'='*80}\n")

    # Execute trades based on signals
    for date, signal in signals.items():
        if signal != Signal.HOLD:
            price = data.loc[date, 'close']
            strategy.execute_signal(date, signal, price, position_size)

            if verbose and strategy.trades:
                last_trade = strategy.trades[-1]
                action = last_trade['action']
                print(f"{date} | {action:4s} | Price: ${price:6.2f} | Shares: {last_trade['shares']:4d} | Value: ${last_trade['value']:9,.2f}", end='')
                if 'pnl' in last_trade:
                    print(f" | P&L: ${last_trade['pnl']:8,.2f} ({last_trade['pnl_pct']:+.2f}%) | Hold: {last_trade['hold_days']} days")
                else:
                    print()

    # Close any open position at the end
    if strategy.position:
        final_date = data.index[-1]
        final_price = data.loc[final_date, 'close']
        strategy.execute_signal(final_date, Signal.SELL, final_price, position_size)

        if verbose:
            last_trade = strategy.trades[-1]
            print(f"{final_date} | SELL | Price: ${final_price:6.2f} | Shares: {last_trade['shares']:4d} | Value: ${last_trade['value']:9,.2f} | P&L: ${last_trade['pnl']:8,.2f} ({last_trade['pnl_pct']:+.2f}%) | Hold: {last_trade['hold_days']} days [FINAL]")

    # Get performance summary
    performance = strategy.get_performance_summary()
    final_value = strategy.get_portfolio_value(data.iloc[-1]['close'])

    # Calculate buy & hold benchmark
    buy_hold_shares = int(initial_capital / data.iloc[0]['close'])
    buy_hold_value = buy_hold_shares * data.iloc[-1]['close']
    buy_hold_return = ((buy_hold_value - initial_capital) / initial_capital) * 100

    results = {
        'strategy_name': strategy.name,
        'initial_capital': initial_capital,
        'final_value': final_value,
        'total_return': final_value - initial_capital,
        'total_return_pct': ((final_value - initial_capital) / initial_capital) * 100,
        'buy_hold_return_pct': buy_hold_return,
        'alpha': ((final_value - initial_capital) / initial_capital) * 100 - buy_hold_return,
        **performance
    }

    if verbose:
        print(f"\n{'='*80}")
        print(f"BACKTEST RESULTS")
        print(f"{'='*80}")
        print(f"Strategy: {results['strategy_name']}")
        print(f"\nPerformance:")
        print(f"  Initial Capital:    ${results['initial_capital']:>12,.2f}")
        print(f"  Final Value:        ${results['final_value']:>12,.2f}")
        print(f"  Total Return:       ${results['total_return']:>12,.2f} ({results['total_return_pct']:>+6.2f}%)")
        print(f"  Buy & Hold Return:                   ({results['buy_hold_return_pct']:>+6.2f}%)")
        print(f"  Alpha (vs B&H):                      ({results['alpha']:>+6.2f}%)")

        if 'total_trades' in results:
            print(f"\nTrade Statistics:")
            print(f"  Total Trades:       {results['total_trades']:>12}")
            print(f"  Winning Trades:     {results['winning_trades']:>12} ({results['win_rate']:.1f}%)")
            print(f"  Losing Trades:      {results['losing_trades']:>12}")
            print(f"  Average P&L:        ${results['avg_pnl']:>12,.2f}")
            print(f"  Average Win:        ${results['avg_win']:>12,.2f}")
            print(f"  Average Loss:       ${results['avg_loss']:>12,.2f}")
            print(f"  Avg Hold Period:    {results['avg_hold_days']:>12.1f} days")
        print(f"{'='*80}\n")

    return results


def compare_strategies(strategies: list, data: pd.DataFrame,
                      initial_capital: float = 10000,
                      position_size: float = 1.0) -> pd.DataFrame:
    """
    Compare multiple strategies

    Args:
        strategies: List of Strategy instances
        data: Historical price data
        initial_capital: Starting capital
        position_size: Position size fraction

    Returns:
        DataFrame comparing strategy performance
    """
    results = []

    for strategy in strategies:
        result = run_backtest(strategy, data.copy(), initial_capital, position_size, verbose=False)
        results.append(result)

    comparison = pd.DataFrame(results)

    # Sort by total return percentage
    comparison = comparison.sort_values('total_return_pct', ascending=False)

    return comparison
