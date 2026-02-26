"""Advanced multi-indicator trading strategies"""
import pandas as pd
import numpy as np
from strategy import Strategy, Signal

class TripleIndicatorStrategy(Strategy):
    """
    Combines RSI, MACD, and Volume for entry/exit signals

    Entry (BUY):
    - RSI < oversold (momentum oversold)
    - MACD histogram turning positive (trend reversal)
    - Volume > average volume (confirmation)

    Exit (SELL):
    - RSI > overbought OR
    - MACD histogram turning negative OR
    - Stop loss triggered
    """

    def __init__(self, rsi_period: int = 14, oversold: int = 30,
                 overbought: int = 70, volume_ma: int = 20):
        super().__init__(f"TripleIndicator_{rsi_period}_{oversold}_{overbought}")
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.volume_ma = volume_ma

    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate RSI indicator"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, data: pd.DataFrame, fast: int = 12,
                       slow: int = 26, signal: int = 9):
        """Calculate MACD indicator"""
        ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate signals using multiple indicators"""
        # Calculate indicators
        data['rsi'] = self.calculate_rsi(data)
        data['macd'], data['macd_signal'], data['macd_hist'] = self.calculate_macd(data)
        data['volume_ma'] = data['volume'].rolling(window=self.volume_ma).mean()

        signals = pd.Series(Signal.HOLD, index=data.index)

        for i in range(1, len(data)):
            if pd.isna(data['rsi'].iloc[i]) or pd.isna(data['macd_hist'].iloc[i]):
                continue

            # BUY signal: RSI oversold + MACD turning positive + high volume
            if (data['rsi'].iloc[i] < self.oversold and
                data['macd_hist'].iloc[i] > 0 and
                data['macd_hist'].iloc[i-1] <= 0 and
                data['volume'].iloc[i] > data['volume_ma'].iloc[i]):
                signals.iloc[i] = Signal.BUY

            # SELL signal: RSI overbought OR MACD turning negative
            elif (data['rsi'].iloc[i] > self.overbought or
                  (data['macd_hist'].iloc[i] < 0 and data['macd_hist'].iloc[i-1] >= 0)):
                signals.iloc[i] = Signal.SELL

        return signals


class TrendFollowingStrategy(Strategy):
    """
    Trend following strategy using EMA, ADX, and ATR

    Entry (BUY):
    - Price above 50 EMA (uptrend)
    - ADX > 25 (strong trend)
    - Price pullback to support level

    Exit (SELL):
    - Price crosses below 50 EMA
    - ATR-based trailing stop loss
    """

    def __init__(self, ema_period: int = 50, adx_period: int = 14,
                 atr_period: int = 14, atr_multiplier: float = 2.0):
        super().__init__(f"TrendFollow_{ema_period}_{adx_period}_{atr_multiplier}")
        self.ema_period = ema_period
        self.adx_period = adx_period
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.trailing_stop = None

    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=self.atr_period).mean()

    def calculate_adx(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average Directional Index"""
        high_diff = data['high'].diff()
        low_diff = -data['low'].diff()

        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

        atr = self.calculate_atr(data)
        plus_di = 100 * (plus_dm.rolling(window=self.adx_period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=self.adx_period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=self.adx_period).mean()

        return adx

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate trend following signals"""
        data['ema'] = data['close'].ewm(span=self.ema_period, adjust=False).mean()
        data['atr'] = self.calculate_atr(data)
        data['adx'] = self.calculate_adx(data)

        signals = pd.Series(Signal.HOLD, index=data.index)

        for i in range(self.ema_period, len(data)):
            if pd.isna(data['adx'].iloc[i]):
                continue

            # BUY: Price above EMA and strong trend
            if (data['close'].iloc[i] > data['ema'].iloc[i] and
                data['adx'].iloc[i] > 25 and
                data['close'].iloc[i-1] <= data['ema'].iloc[i-1]):
                signals.iloc[i] = Signal.BUY
                # Set initial stop loss
                self.trailing_stop = data['close'].iloc[i] - (data['atr'].iloc[i] * self.atr_multiplier)

            # SELL: Price crosses below EMA or hits trailing stop
            elif signals.iloc[:i].isin([Signal.BUY]).any():
                # Update trailing stop
                new_stop = data['close'].iloc[i] - (data['atr'].iloc[i] * self.atr_multiplier)
                if self.trailing_stop is None or new_stop > self.trailing_stop:
                    self.trailing_stop = new_stop

                # Check exit conditions
                if (data['close'].iloc[i] < data['ema'].iloc[i] or
                    data['low'].iloc[i] < self.trailing_stop):
                    signals.iloc[i] = Signal.SELL
                    self.trailing_stop = None

        return signals


class MeanReversionStrategy(Strategy):
    """
    Mean reversion strategy using Z-Score

    Entry (BUY):
    - Z-score < -2 (price significantly below mean)
    - Volume spike (>1.5x average)

    Exit (SELL):
    - Z-score > 0 (price returns to mean)
    - OR maximum hold period reached
    """

    def __init__(self, lookback: int = 20, z_threshold: float = 2.0,
                 max_hold_days: int = 10):
        super().__init__(f"MeanReversion_{lookback}_{z_threshold}")
        self.lookback = lookback
        self.z_threshold = z_threshold
        self.max_hold_days = max_hold_days
        self.entry_date = None

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate mean reversion signals"""
        # Calculate rolling mean and std
        data['rolling_mean'] = data['close'].rolling(window=self.lookback).mean()
        data['rolling_std'] = data['close'].rolling(window=self.lookback).std()
        data['z_score'] = (data['close'] - data['rolling_mean']) / data['rolling_std']
        data['volume_ma'] = data['volume'].rolling(window=self.lookback).mean()

        signals = pd.Series(Signal.HOLD, index=data.index)

        for i in range(self.lookback, len(data)):
            if pd.isna(data['z_score'].iloc[i]):
                continue

            # BUY: Oversold with volume spike
            if (data['z_score'].iloc[i] < -self.z_threshold and
                data['volume'].iloc[i] > 1.5 * data['volume_ma'].iloc[i]):
                signals.iloc[i] = Signal.BUY
                self.entry_date = data.index[i]

            # SELL: Return to mean or max hold period
            elif self.entry_date is not None:
                days_held = (data.index[i] - self.entry_date).days
                if (data['z_score'].iloc[i] > 0 or days_held >= self.max_hold_days):
                    signals.iloc[i] = Signal.SELL
                    self.entry_date = None

        return signals


class BreakoutStrategy(Strategy):
    """
    Breakout strategy using volume-confirmed price breakouts

    Entry (BUY):
    - Price breaks above recent high
    - Volume > 2x average (confirmation)
    - RSI < 70 (not overbought)

    Exit (SELL):
    - Price breaks below recent low
    - OR profit target reached (5%)
    """

    def __init__(self, lookback: int = 20, volume_multiplier: float = 2.0,
                 profit_target: float = 5.0):
        super().__init__(f"Breakout_{lookback}_{volume_multiplier}_{profit_target}")
        self.lookback = lookback
        self.volume_multiplier = volume_multiplier
        self.profit_target = profit_target
        self.entry_price = None

    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate breakout signals"""
        data['high_breakout'] = data['high'].rolling(window=self.lookback).max().shift(1)
        data['low_breakdown'] = data['low'].rolling(window=self.lookback).min().shift(1)
        data['volume_ma'] = data['volume'].rolling(window=self.lookback).mean()
        data['rsi'] = self.calculate_rsi(data)

        signals = pd.Series(Signal.HOLD, index=data.index)

        for i in range(self.lookback, len(data)):
            if pd.isna(data['high_breakout'].iloc[i]):
                continue

            # BUY: Volume-confirmed breakout
            if (data['close'].iloc[i] > data['high_breakout'].iloc[i] and
                data['volume'].iloc[i] > self.volume_multiplier * data['volume_ma'].iloc[i] and
                data['rsi'].iloc[i] < 70):
                signals.iloc[i] = Signal.BUY
                self.entry_price = data['close'].iloc[i]

            # SELL: Breakdown or profit target
            elif self.entry_price is not None:
                profit_pct = ((data['close'].iloc[i] - self.entry_price) / self.entry_price) * 100

                if (data['close'].iloc[i] < data['low_breakdown'].iloc[i] or
                    profit_pct >= self.profit_target):
                    signals.iloc[i] = Signal.SELL
                    self.entry_price = None

        return signals
