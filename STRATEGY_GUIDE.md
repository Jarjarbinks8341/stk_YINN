# Custom Strategy Development Guide

## Quick Start

1. **Use the Template**: Start with `custom_strategy_template.py`
2. **Implement Logic**: Fill in the `calculate_signals()` method
3. **Test**: Run backtest to evaluate performance

## Strategy Results Summary

### Simple Strategies (run_backtest.py)
| Strategy | Return | Win Rate | Trades | Best For |
|----------|--------|----------|--------|----------|
| Bollinger Bands (20,2) | +43.37% | 100% | 3 | Mean reversion |
| MA Crossover (10,30) | +20.37% | 66.7% | 3 | Trend following |
| MA Crossover (5,20) | -33.30% | 25% | 8 | ❌ Too many whipsaws |

### Advanced Strategies (test_custom_strategies.py)
| Strategy | Return | Win Rate | Trades | Best For |
|----------|--------|----------|--------|----------|
| Mean Reversion | +22.74% | 75% | 4 | Oversold bounces |
| Triple Indicator | 0% | - | 0 | ⚠️ Too strict entry |
| Breakout | -9.86% | 0% | 1 | ❌ False breakouts |
| Trend Following | -17.65% | 14.3% | 7 | ❌ Choppy market |

## How to Create Your Own Strategy

### Step 1: Define Your Hypothesis

Ask yourself:
- What market condition am I exploiting?
- When should I enter a trade?
- When should I exit?
- What's my edge?

### Step 2: Choose Your Indicators

Common indicators available:
- **Trend**: MA, EMA, MACD, ADX
- **Momentum**: RSI, Stochastic, Rate of Change
- **Volatility**: ATR, Bollinger Bands
- **Volume**: Volume MA, OBV, Volume Ratio

### Step 3: Code Your Logic

```python
from strategy import Strategy, Signal
import pandas as pd

class MyStrategy(Strategy):
    def __init__(self, param1=10):
        super().__init__(f"MyStrategy_{param1}")
        self.param1 = param1

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Add indicators
        data['indicator'] = data['close'].rolling(self.param1).mean()

        signals = pd.Series(Signal.HOLD, index=data.index)

        # Your logic here
        for i in range(1, len(data)):
            if YOUR_BUY_CONDITION:
                signals.iloc[i] = Signal.BUY
            elif YOUR_SELL_CONDITION:
                signals.iloc[i] = Signal.SELL

        return signals
```

### Step 4: Test Your Strategy

```python
from backtest import load_data, run_backtest

data = load_data()
strategy = MyStrategy(param1=20)
results = run_backtest(strategy, data, initial_capital=10000)
```

## Strategy Ideas for YINN

### Why Strategies Underperformed Buy & Hold:
- YINN had a strong uptrend (+70% in 1 year)
- Leveraged ETFs (3x) trend strongly
- Timing the market is hard with high volatility

### Better Approaches for YINN:

1. **Dip Buying Strategy**
   - Buy when RSI < 30 (oversold)
   - YINN tends to bounce quickly after drops
   - Mean Reversion worked well (22.74%)

2. **Volatility-Based Position Sizing**
   - Instead of 100% position size
   - Use ATR to adjust position size
   - Lower volatility = bigger positions

3. **Multi-Timeframe Strategy**
   - Use daily trend to guide trades
   - Use hourly/4H for entries/exits
   - Requires intraday data

4. **Pair Trading with FXI**
   - YINN is 3x FXI
   - Look for divergences
   - Requires FXI data

5. **Stop Loss + Trailing Stop**
   - Protect capital on downswings
   - Let winners run
   - Bollinger Bands had 100% win rate

## Best Practices

### DO:
✅ Test on historical data first
✅ Use proper position sizing (not always 100%)
✅ Include stop losses for risk management
✅ Keep strategies simple
✅ Understand why your edge exists
✅ Account for trading costs/slippage

### DON'T:
❌ Over-optimize on past data
❌ Use too many indicators
❌ Trade without backtesting
❌ Risk too much per trade
❌ Chase performance
❌ Ignore market regime changes

## Example: Building a Stop-Loss Strategy

```python
class StopLossStrategy(Strategy):
    def __init__(self, stop_pct=5.0):
        super().__init__(f"StopLoss_{stop_pct}")
        self.stop_pct = stop_pct
        self.entry_price = None

    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Your entry logic here (e.g., MA crossover)
        # Then add stop loss

        for i in range(1, len(data)):
            if entry_condition:
                signals.iloc[i] = Signal.BUY
                self.entry_price = data['close'].iloc[i]

            # Stop loss check
            if self.entry_price:
                loss = ((data['close'].iloc[i] - self.entry_price)
                       / self.entry_price) * 100
                if loss < -self.stop_pct:
                    signals.iloc[i] = Signal.SELL
                    self.entry_price = None

        return signals
```

## Next Steps

1. **Start Simple**: Modify an existing strategy
2. **Add One Feature**: e.g., stop loss to BB strategy
3. **Test Variations**: Try different parameters
4. **Compare Results**: Use `compare_strategies()`
5. **Iterate**: Refine based on results

## Resources

- `custom_strategy_template.py` - Blank template
- `strategies.py` - Simple strategy examples
- `advanced_strategies.py` - Complex strategy examples
- `backtest.py` - Backtesting engine documentation

Happy trading! 🚀
