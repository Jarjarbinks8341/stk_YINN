"""
Template for creating custom trading strategies

Copy this template and implement your own strategy logic in calculate_signals()
"""
import pandas as pd
import numpy as np
from strategy import Strategy, Signal

class MyCustomStrategy(Strategy):
    """
    Custom Strategy Template

    TODO: Describe your strategy here
    - Entry conditions:
    - Exit conditions:
    - Timeframe:
    """

    def __init__(self, param1: int = 10, param2: float = 2.0):
        """
        Initialize your strategy with parameters

        Args:
            param1: Description of parameter 1
            param2: Description of parameter 2
        """
        super().__init__(f"MyCustomStrategy_{param1}_{param2}")
        self.param1 = param1
        self.param2 = param2

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate trading signals based on your strategy logic

        Args:
            data: DataFrame with columns: open, high, low, close, volume

        Returns:
            Series with Signal.BUY, Signal.SELL, or Signal.HOLD for each date
        """
        # Initialize signals to HOLD
        signals = pd.Series(Signal.HOLD, index=data.index)

        # TODO: Add your indicators
        # Example: Calculate a simple moving average
        # data['sma'] = data['close'].rolling(window=self.param1).mean()

        # TODO: Implement your entry/exit logic
        # Loop through data and generate signals
        for i in range(1, len(data)):
            # Skip if we don't have enough data yet
            # if i < self.param1:
            #     continue

            # TODO: Your BUY logic
            # Example: if some_condition:
            #     signals.iloc[i] = Signal.BUY

            # TODO: Your SELL logic
            # Example: if some_other_condition:
            #     signals.iloc[i] = Signal.SELL

            pass

        return signals


# Example: Run backtest with your custom strategy
if __name__ == "__main__":
    from backtest import load_data, run_backtest

    # Load data
    data = load_data()

    # Create and test your strategy
    strategy = MyCustomStrategy(param1=20, param2=2.0)
    results = run_backtest(strategy, data, initial_capital=10000)
