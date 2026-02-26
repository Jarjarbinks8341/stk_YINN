"""Base strategy class and common strategy implementations"""
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

class Signal(Enum):
    """Trading signals"""
    BUY = 1
    SELL = -1
    HOLD = 0

@dataclass
class Position:
    """Represents a trading position"""
    entry_date: datetime
    entry_price: float
    shares: int
    position_type: str  # 'long' or 'short'

    @property
    def cost_basis(self):
        return self.entry_price * self.shares

    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L"""
        if self.position_type == 'long':
            return (current_price - self.entry_price) * self.shares
        else:  # short
            return (self.entry_price - current_price) * self.shares

    def unrealized_pnl_pct(self, current_price: float) -> float:
        """Calculate unrealized P&L as percentage"""
        pnl = self.unrealized_pnl(current_price)
        return (pnl / self.cost_basis) * 100

class Strategy(ABC):
    """Base class for trading strategies"""

    def __init__(self, name: str):
        self.name = name
        self.position = None
        self.trades = []
        self.cash = 0
        self.initial_capital = 0

    @abstractmethod
    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate trading signals for the entire dataset

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with Signal values (BUY, SELL, HOLD) for each date
        """
        pass

    def initialize(self, initial_capital: float):
        """Initialize strategy with starting capital"""
        self.cash = initial_capital
        self.initial_capital = initial_capital
        self.position = None
        self.trades = []

    def execute_signal(self, date: datetime, signal: Signal, price: float,
                       position_size: float = 1.0):
        """
        Execute a trading signal

        Args:
            date: Trade date
            signal: BUY, SELL, or HOLD
            price: Current price
            position_size: Fraction of available capital to use (0-1)
        """
        if signal == Signal.BUY and self.position is None:
            # Enter long position
            shares = int((self.cash * position_size) / price)
            if shares > 0:
                cost = shares * price
                self.cash -= cost
                self.position = Position(
                    entry_date=date,
                    entry_price=price,
                    shares=shares,
                    position_type='long'
                )
                self.trades.append({
                    'date': date,
                    'action': 'BUY',
                    'price': price,
                    'shares': shares,
                    'value': cost
                })

        elif signal == Signal.SELL and self.position is not None:
            # Exit position
            proceeds = self.position.shares * price
            pnl = self.position.unrealized_pnl(price)
            pnl_pct = self.position.unrealized_pnl_pct(price)

            self.cash += proceeds
            self.trades.append({
                'date': date,
                'action': 'SELL',
                'price': price,
                'shares': self.position.shares,
                'value': proceeds,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'hold_days': (date - self.position.entry_date).days
            })
            self.position = None

    def get_portfolio_value(self, current_price: float) -> float:
        """Get total portfolio value (cash + position value)"""
        if self.position:
            return self.cash + (self.position.shares * current_price)
        return self.cash

    def get_performance_summary(self) -> dict:
        """Get summary of strategy performance"""
        if not self.trades:
            return {'error': 'No trades executed'}

        completed_trades = [t for t in self.trades if 'pnl' in t]

        if not completed_trades:
            return {'error': 'No completed trades'}

        total_pnl = sum(t['pnl'] for t in completed_trades)
        winning_trades = [t for t in completed_trades if t['pnl'] > 0]
        losing_trades = [t for t in completed_trades if t['pnl'] < 0]

        return {
            'total_trades': len(completed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(completed_trades) * 100,
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / len(completed_trades),
            'avg_win': sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            'avg_loss': sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0,
            'avg_hold_days': sum(t['hold_days'] for t in completed_trades) / len(completed_trades),
            'total_return_pct': (total_pnl / self.initial_capital) * 100
        }
