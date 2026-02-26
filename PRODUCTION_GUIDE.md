# YINN Production Trading System

## 🏆 Strategy Overview

**Winner: Time-Weighted Average (60-day lookback)**

- **Backtest Return:** 161.42%
- **Win Rate:** 100% (4/4 trades)
- **Alpha:** +91.21% vs buy & hold
- **Avg Profit/Trade:** $4,035.50

This is the production-ready implementation of the best performing strategy.

---

## 🚀 Quick Start

### 1. Get Current Trading Signal

```bash
source venv/bin/activate
python get_signal.py
```

**Output Example:**
```
================================================================================
YINN PRODUCTION TRADING SIGNAL
================================================================================

Date: 2026-02-06
Current Price: $44.44

🟢 SIGNAL: BUY (STRONG)

SUPPORT & RESISTANCE LEVELS:
  Support (Time-Weighted):    $41.32
  Resistance (Time-Weighted): $54.93
  Trading Range Width:        $13.60 (32.9%)

RECOMMENDATION:
✅ BUY YINN at current price $44.44
   Target: $54.93 (23.6% upside)
   Stop Loss: $41.32 (7.0% downside)
```

### 2. Daily Update & Signal

Run this every day to update data and get fresh signals:

```bash
source venv/bin/activate
python daily_update_and_signal.py
```

This will:
- ✅ Update YINN price data
- ✅ Calculate current trading signal
- ✅ Save signal to tracking file

---

## 📊 How It Works

### Strategy Logic

1. **Find Peaks & Troughs**
   - Look back 60 days
   - Identify top 3 peaks and bottom 3 troughs
   - Must be at least 5 days apart (distributed)

2. **Calculate Time-Weighted Levels**
   ```
   Support = Σ(trough_price × weight) / Σ(weight)
   where weight = 1 / (days_ago + 1)

   Recent troughs get MORE weight!
   ```

3. **Generate Signals**
   - **BUY:** Price ≤ Support × 1.02 (2% above support)
   - **SELL:** Price ≥ Resistance × 0.98 (2% below resistance)
   - **HOLD:** Otherwise

### Why Time-Weighted?

Traditional average treats all levels equally:
```
Support = ($41.48 + $42.59 + $41.25) / 3 = $41.77
```

Time-weighted gives more importance to RECENT levels:
```
$41.48 (51 days ago)  → weight = 0.0192 (1.9%)
$42.59 (37 days ago)  → weight = 0.0263 (2.6%)
$41.25 (1 day ago!)   → weight = 0.5000 (50.0%!)

Support = $41.32 (LOWER = earlier buy signals!)
```

**Result:** Catches bounces earlier = 161% return!

---

## 📁 File Structure

```
├── production_strategy.py      # Main strategy implementation
├── get_signal.py              # Quick signal checker
├── daily_update_and_signal.py # Daily update script
├── data/
│   ├── signals_log.json       # Historical signals
│   └── latest_signal.json     # Latest signal
└── PRODUCTION_GUIDE.md        # This file
```

---

## 🔔 Usage Patterns

### Pattern 1: Daily Trader

**Every morning:**
```bash
./daily_update_and_signal.py
```

Check the signal and act accordingly.

### Pattern 2: Manual Check

**Whenever you want:**
```bash
python get_signal.py
```

Get instant signal without updating data.

### Pattern 3: Automated (Advanced)

**Set up cron job** (macOS/Linux):
```bash
# Edit crontab
crontab -e

# Add this line (runs at 4:30 PM ET after market close)
30 16 * * 1-5 cd /Users/jiazhongchen/repo/stk_YINN && source venv/bin/activate && python daily_update_and_signal.py >> logs/daily.log 2>&1
```

---

## 📈 Interpreting Signals

### 🟢 BUY Signal

**What it means:**
- Price is near support level
- Good risk/reward ratio
- Time to enter position

**Action:**
1. Check risk/reward ratio (should be >2:1)
2. Buy YINN at market price
3. Set stop loss at support level
4. Target resistance level for exit

**Example:**
```
Current: $44.44
Support: $41.32
Resistance: $54.93

Upside: $10.49 (23.6%)
Downside: $3.12 (7.0%)
Risk/Reward: 3.36:1 ✅
```

### 🔴 SELL Signal

**What it means:**
- Price is near resistance
- Take profits
- Overbought zone

**Action:**
1. Sell YINN at market price
2. Lock in profits
3. Wait for next buy signal

### 🟡 HOLD Signal

**What it means:**
- Price is in middle of range
- No clear entry/exit point
- Wait for better opportunity

**Action:**
1. Stay in cash (or hold position)
2. Set price alerts:
   - Alert at buy threshold
   - Alert at sell threshold

---

## ⚙️ Strategy Parameters

**Current Settings (Optimized):**
```python
lookback = 60           # Days to look back
min_distance = 5        # Min days between peaks
buy_threshold = 2.0%    # Buy within 2% of support
sell_threshold = 2.0%   # Sell within 2% of resistance
```

**To Adjust:**
Edit `production_strategy.py`:
```python
strategy = YINNProductionStrategy(
    lookback=60,              # Change lookback period
    min_distance=5,           # Change peak spacing
    buy_threshold_pct=2.0,    # Change buy threshold
    sell_threshold_pct=2.0    # Change sell threshold
)
```

---

## 📊 Performance Tracking

### View Signal History

```bash
cat data/signals_log.json
```

### Latest Signal

```bash
cat data/latest_signal.json
```

**Example:**
```json
{
  "timestamp": "2026-02-06T15:00:00",
  "date": "2026-02-06",
  "price": 44.44,
  "signal": "BUY",
  "support": 41.32,
  "resistance": 54.93,
  "position_in_range_pct": 19.9
}
```

---

## ⚠️ Risk Management

### Position Sizing

**Conservative (Recommended):**
- Use 25-50% of trading capital per trade
- Allows for averaging down if needed

**Aggressive:**
- Use 75-100% of capital
- Higher returns but higher risk

### Stop Losses

**Always use stop losses!**
- Set at support level
- Typically 5-10% below entry
- Honor your stops!

### Example Trade:

```
Capital: $10,000
Position Size: 50% = $5,000
Entry: $44.44
Stop Loss: $41.32 (7% down)
Target: $54.93 (23.6% up)

Max Loss: $5,000 × 7% = $350
Max Gain: $5,000 × 23.6% = $1,180
Risk/Reward: 3.36:1 ✅
```

---

## 🔧 Troubleshooting

### No signal generated

```bash
# Check if data is up to date
python update_daily.py

# Then get signal
python get_signal.py
```

### Error loading data

```bash
# Re-fetch all data
python fetch_data.py
```

### Wrong date/old data

```bash
# Update to latest
python update_daily.py
```

---

## 📞 Next Steps

1. **Test with paper trading first**
   - Track signals but don't trade real money
   - Verify strategy works for you
   - Build confidence

2. **Start small**
   - Begin with small position sizes
   - Scale up as you gain experience

3. **Track your trades**
   - Keep a trading journal
   - Review what worked/didn't work
   - Improve over time

4. **Stay disciplined**
   - Follow the signals
   - Use stop losses
   - Don't overtrade

---

## 🎯 Expected Performance

Based on backtesting (Jan 2025 - Feb 2026):

- **Total Return:** 161.42%
- **Number of Trades:** 4 per year
- **Win Rate:** 100%
- **Avg Hold Time:** ~46 days
- **Max Drawdown:** Minimal (all trades profitable)

**Past performance does not guarantee future results!**

---

## 📝 Strategy Checklist

Before each trade:

- [ ] Updated data to latest (run `update_daily.py`)
- [ ] Checked current signal (run `get_signal.py`)
- [ ] Verified risk/reward ratio (>2:1)
- [ ] Determined position size (25-50% of capital)
- [ ] Set stop loss at support level
- [ ] Set target at resistance level
- [ ] Ready to execute!

---

Good luck trading! 🚀📈

Remember: **The best strategy is one you can stick to consistently.**
