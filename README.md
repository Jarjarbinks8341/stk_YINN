# YINN Trading System

A production-ready trading system for YINN (Direxion Daily FTSE China Bull 3X Shares).

**🏆 Production Strategy Performance:**
- **Return:** 161.42% (backtested)
- **Win Rate:** 100% (4/4 trades)
- **Alpha:** +91.21% vs buy & hold
- **Method:** Time-Weighted Support/Resistance (60-day)

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize database and fetch historical data:
```bash
python fetch_data.py
```

## 🚀 Production Usage

### Get Current Trading Signal

```bash
source venv/bin/activate
python get_signal.py
```

### Daily Update & Signal

```bash
python daily_update_and_signal.py
```

This will:
- Update YINN price data
- Calculate current trading signal
- Save signal to tracking file

### 🤖 Automated Daily Monitor (GitHub Actions)

The system is configured to run automatically every weekday at **10:00 AM ET** (30 minutes after NYSE opens).

- **Location**: `.github/workflows/panic_monitor.yml`
- **Function**: Automatically updates data and runs the `panic_put_seller.py` logic.
- **Manual Trigger**: You can also trigger this manually from the "Actions" tab in your GitHub repository.

**📖 See [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md) for complete production guide**

## Database

- **Location**: `data/yinn.db` (SQLite)
- **Table**: `daily_prices`
- **Columns**: ticker, date, open, high, low, close, volume, adj_close

## Trading Strategies

### Run Backtests

Test simple strategies:
```bash
python run_backtest.py
```

Test advanced multi-indicator strategies:
```bash
python test_custom_strategies.py
```

### Available Strategies

**Simple Strategies** (strategies.py):
- Moving Average Crossover
- RSI Strategy
- Momentum Strategy
- Bollinger Bands ⭐ Best performer (43% return, 100% win rate)

**Advanced Strategies** (advanced_strategies.py):
- Triple Indicator (RSI + MACD + Volume)
- Trend Following (EMA + ADX + ATR trailing stop)
- Mean Reversion (Z-Score based) ⭐ 22% return, 75% win rate
- Breakout (Volume-confirmed breakouts)

### Creating Your Own Strategies

See **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)** for detailed guide on building custom strategies.

Quick start:
1. Copy `custom_strategy_template.py`
2. Implement your `calculate_signals()` logic
3. Test with `run_backtest()`

## Files

**Data & Database:**
- `config.py` - Configuration settings
- `database.py` - Database models and setup
- `fetch_data.py` - Initial data fetch script
- `update_daily.py` - Daily update script

**Strategy Framework:**
- `strategy.py` - Base strategy class and position tracking
- `backtest.py` - Backtesting engine

**Pre-built Strategies:**
- `strategies.py` - Simple strategy implementations
- `advanced_strategies.py` - Multi-indicator strategies

**Example Scripts:**
- `run_backtest.py` - Test simple strategies
- `test_custom_strategies.py` - Test advanced strategies
- `custom_strategy_template.py` - Template for creating your own

**Production System:**
- `production_strategy.py` - Production trading strategy (161% return)
- `get_signal.py` - Get current trading signal
- `daily_update_and_signal.py` - Daily update + signal script
- `peak_detector.py` - Peak/trough detection algorithm
- `visualize_peaks.py` - Chart generation
- `support_resistance_methods.py` - S/R calculation methods
- `test_sr_methods.py` - Backtest all S/R methods

**Documentation:**
- `README.md` - This file
- `PRODUCTION_GUIDE.md` - Production trading guide ⭐
- `STRATEGY_GUIDE.md` - Custom strategy development guide
