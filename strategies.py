"""Collection of trading strategy implementations"""
import pandas as pd
import numpy as np
from strategy import Strategy, Signal

class MovingAverageCrossover(Strategy):
    """
    Simple Moving Average Crossover Strategy
    BUY when fast MA crosses above slow MA
    SELL when fast MA crosses below slow MA
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        super().__init__(f"MA_Crossover_{fast_period}_{slow_period}")
        self.fast_period = fast_period
        self.slow_period = slow_period

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate MA crossover signals"""
        # Calculate moving averages
        data['fast_ma'] = data['close'].rolling(window=self.fast_period).mean()
        data['slow_ma'] = data['close'].rolling(window=self.slow_period).mean()

        # Initialize signals
        signals = pd.Series(Signal.HOLD, index=data.index)

        # Generate signals
        for i in range(1, len(data)):
            if pd.notna(data['fast_ma'].iloc[i]) and pd.notna(data['slow_ma'].iloc[i]):
                # Bullish crossover
                if (data['fast_ma'].iloc[i] > data['slow_ma'].iloc[i] and
                    data['fast_ma'].iloc[i-1] <= data['slow_ma'].iloc[i-1]):
                    signals.iloc[i] = Signal.BUY

                # Bearish crossover
                elif (data['fast_ma'].iloc[i] < data['slow_ma'].iloc[i] and
                      data['fast_ma'].iloc[i-1] >= data['slow_ma'].iloc[i-1]):
                    signals.iloc[i] = Signal.SELL

        return signals


class RSIStrategy(Strategy):
    """
    RSI (Relative Strength Index) Strategy
    BUY when RSI crosses below oversold level
    SELL when RSI crosses above overbought level
    """

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__(f"RSI_{period}_{oversold}_{overbought}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate RSI indicator"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate RSI-based signals"""
        data['rsi'] = self.calculate_rsi(data)
        signals = pd.Series(Signal.HOLD, index=data.index)

        for i in range(1, len(data)):
            if pd.notna(data['rsi'].iloc[i]):
                # Buy signal: RSI crosses below oversold level
                if data['rsi'].iloc[i] < self.oversold and data['rsi'].iloc[i-1] >= self.oversold:
                    signals.iloc[i] = Signal.BUY

                # Sell signal: RSI crosses above overbought level
                elif data['rsi'].iloc[i] > self.overbought and data['rsi'].iloc[i-1] <= self.overbought:
                    signals.iloc[i] = Signal.SELL

        return signals


class MomentumStrategy(Strategy):
    """
    Momentum Strategy
    BUY when price increases by threshold% over lookback period
    SELL when price decreases by threshold% from recent high
    """

    def __init__(self, lookback_period: int = 20, buy_threshold: float = 5.0,
                 sell_threshold: float = -3.0):
        super().__init__(f"Momentum_{lookback_period}_{buy_threshold}_{sell_threshold}")
        self.lookback_period = lookback_period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate momentum-based signals"""
        # Calculate returns over lookback period
        data['returns'] = data['close'].pct_change(self.lookback_period) * 100

        # Calculate percentage from recent high
        data['recent_high'] = data['close'].rolling(window=self.lookback_period).max()
        data['pct_from_high'] = ((data['close'] - data['recent_high']) / data['recent_high']) * 100

        signals = pd.Series(Signal.HOLD, index=data.index)

        for i in range(self.lookback_period, len(data)):
            if pd.notna(data['returns'].iloc[i]):
                # Strong momentum - BUY
                if data['returns'].iloc[i] > self.buy_threshold:
                    signals.iloc[i] = Signal.BUY

                # Momentum breakdown - SELL
                elif data['pct_from_high'].iloc[i] < self.sell_threshold:
                    signals.iloc[i] = Signal.SELL

        return signals


class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands Mean Reversion Strategy
    BUY when price crosses below lower band
    SELL when price crosses above upper band
    """

    def __init__(self, period: int = 20, num_std: float = 2.0):
        super().__init__(f"BB_{period}_{num_std}")
        self.period = period
        self.num_std = num_std

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Bollinger Bands signals"""
        # Calculate Bollinger Bands
        data['sma'] = data['close'].rolling(window=self.period).mean()
        data['std'] = data['close'].rolling(window=self.period).std()
        data['upper_band'] = data['sma'] + (data['std'] * self.num_std)
        data['lower_band'] = data['sma'] - (data['std'] * self.num_std)

        signals = pd.Series(Signal.HOLD, index=data.index)

        for i in range(1, len(data)):
            if pd.notna(data['lower_band'].iloc[i]):
                # Price crosses below lower band - BUY (oversold)
                if (data['close'].iloc[i] < data['lower_band'].iloc[i] and
                    data['close'].iloc[i-1] >= data['lower_band'].iloc[i-1]):
                    signals.iloc[i] = Signal.BUY

                # Price crosses above upper band - SELL (overbought)
                elif (data['close'].iloc[i] > data['upper_band'].iloc[i] and
                      data['close'].iloc[i-1] <= data['upper_band'].iloc[i-1]):
                    signals.iloc[i] = Signal.SELL

        return signals
