# 🤖 Claude Context - Covered Calls Manager

**Last Updated:** 2025-10-05
**Project Status:** Active Development
**Quick Access:** `cc-context` or `~/Workspace/Scripts/covered-calls-manager.sh context`

---

## 📋 Quick Reference

### What is this project?
Automated Covered Calls trading system with IBKR integration, Greek calculations, and real-time dashboard.

### How to run?
```bash
cc-run              # Start dashboard
cc-status           # Check status
cc-test             # Test IBKR connection
```

### Where is everything?
- **Main Dashboard:** `dashboard.py` (605 lines)
- **Core System:** `covered_calls_system.py` (Greek calculations, strategy)
- **IBKR Connector:** `ibkr_connector.py` (TWS integration)
- **Scripts:** `my_portfolio.py`, `buy_stock_example.py`

---

## 🎯 Project Purpose

Create and manage Covered Calls positions automatically:
1. Connect to Interactive Brokers TWS (Paper/Live)
2. Analyze stock positions
3. Find optimal strike prices (Greeks-based scoring)
4. Execute Covered Call sales
5. Monitor and manage positions

---

## 🔧 Technical Stack

### Core Libraries
```python
streamlit>=1.28.0       # Dashboard UI
plotly>=5.17.0          # Charts/graphs
pandas>=2.0.0           # Data analysis
ib-async>=2.0.0         # IBKR API (upgraded Oct 2025)
blackscholes>=0.2.0     # Advanced Greeks (NEW)
py-vollib>=1.0.1        # IV calculations (NEW)
```

### Python Version
- **Required:** Python 3.13
- **Virtual env:** `venv/` in project root
- **Activate:** `source venv/bin/activate` or `venv-activate`

---

## 📁 File Structure

```
~/Projects/TradingBots/covered-calls-manager/
├── dashboard.py                 # Streamlit dashboard (main UI)
├── covered_calls_system.py      # Greeks, scoring, strategy logic
├── ibkr_connector.py            # IBKR TWS connection
├── my_portfolio.py              # Portfolio builder script
├── buy_stock_example.py         # Buy stocks demo
├── requirements.txt             # Dependencies
├── venv/                        # Python virtual environment
├── UPGRADE_SUMMARY.md          # Oct 2025 upgrades
├── QUICK_START_HE.md           # Hebrew quick start
├── GITHUB_INTEGRATIONS.md      # Integration ideas
├── TSLA_ANALYSIS_REPORT.md     # Sample analysis
├── CLAUDE_CONTEXT.md           # This file
└── TODO.md                     # Task list
```

---

## 🚀 Recent Upgrades (Oct 2025)

### 1. ib-async Migration
**From:** `ib-insync` (deprecated)
**To:** `ib-async>=2.0.0` (modern, Python 3.13 compatible)

**Why:** Better performance, active maintenance, Python 3.13 support

### 2. Enhanced Greeks Calculations
**Library:** `blackscholes>=0.2.0`

```python
from covered_calls_system import GreeksCalculator, OptionType

# More accurate Greeks
delta = GreeksCalculator.calculate_delta(430, 450, 30/365, 0.05, 0.40, OptionType.CALL)
# Result: 0.381 (vs ~0.35 with old method)
```

### 3. Implied Volatility Calculator
**Library:** `py-vollib>=1.0.1`

```python
# Calculate IV from market price
iv = GreeksCalculator.calculate_implied_volatility(
    market_price=8.50,
    S=430, K=450, T=30/365, r=0.05,
    option_type=OptionType.CALL
)
# Result: 31.8%
```

---

## 🔌 IBKR Connection

### Configuration
```python
IBKRConfig(
    host="127.0.0.1",
    port=7497,           # Paper Trading (7496 for Live)
    client_id=1,         # Unique per connection
    readonly=False       # True for read-only
)
```

### Quick Test
```bash
cc-test              # Full connection test
cc-quick-test        # Fast connection check
```

### Common Issues
- **Port 7497 refused:** TWS not running or API not enabled
- **Already connected:** Change `client_id` or disconnect other clients
- **Timeout:** Check TWS settings → API → Socket Port

---

## 📊 Dashboard Features

### Current Features (dashboard.py)

1. **IBKR Connection** (Line 82)
   - Port, Client ID configuration
   - Connect/Disconnect buttons
   - Status indicator

2. **Account Overview** (Line 140)
   - Total cash
   - Portfolio value
   - P&L today/total

3. **Portfolio Summary** (Line 186)
   - All stock positions
   - Current prices, P&L
   - Quantity available for Covered Calls

4. **Strategy Finder** (Line 358) ⭐ MAIN FEATURE
   - Select stock from portfolio
   - Set DTE (7-60 days)
   - Find 3-10 best strikes
   - Score 0-100 per strike
   - Display Greeks, returns, probabilities

5. **Positions Table** (Line 229)
   - All active positions
   - Real-time P&L

6. **Expiration Calendar** (Line 276)
   - Upcoming option expirations
   - Days until expiry

7. **Alerts Panel** (Line 310)
   - Assignment risk
   - Expiring soon warnings
   - IV changes
   - Rolling opportunities

8. **Performance Charts** (Line 474)
   - P&L over time
   - Returns distribution
   - Greeks analysis

---

## 🎯 Strategy Finder Deep Dive

**Location:** `dashboard.py:358-472`

### How it works:
```python
1. User selects stock from portfolio
2. Sets target DTE (e.g., 30 days)
3. System fetches OTM calls from IBKR
4. Scores each option (0-100)
5. Displays top N strikes with full details
```

### Scoring Algorithm:
```python
CoveredCallStrategy.score_option():
  - Premium amount (higher = better)
  - Distance from current price (sweet spot ~5-10%)
  - Days to expiration (30-45 optimal)
  - Greeks (Delta 0.20-0.40 ideal)
  - IV rank (higher = better premium)

  Output: Score 0-100
```

### Example Output:
```
Strike: $450
Premium: $8.50 ($2,550 total for 3 contracts)
Annual Return: 24.31%
Greeks:
  Delta: 0.381
  Theta: -$0.33/day
  IV: 31.8%
Probability OTM: 61.9%
Score: 85/100
```

---

## ⚠️ Known Issues & Limitations

### Current Limitations:
1. **No execution from dashboard** - Only shows recommendations
2. **No Hebrew support** - UI is English only, not RTL
3. **No position management** - Can't Roll/Close existing positions
4. **Slow options chain loading** - Takes 5-8 seconds for large chains
5. **No IV charts** - Not using new `calculate_implied_volatility` in UI yet

### Planned Fixes:
See `TODO.md` for detailed task list

---

## 🛠️ Development Workflow

### Making Changes
```bash
1. cd ~/Projects/TradingBots/covered-calls-manager
2. source venv/bin/activate
3. # Edit files
4. streamlit run dashboard.py  # Test
5. # Commit when satisfied
```

### Testing
```bash
# Test IBKR connection
python -c "from ibkr_connector import IBKRConnector, IBKRConfig; ..."

# Run portfolio script
python my_portfolio.py

# Test Greeks calculations
python -c "from covered_calls_system import GreeksCalculator; ..."
```

### Debugging
- Dashboard logs: `~/.streamlit/logs/`
- Print statements show in terminal where `streamlit run` was executed
- IBKR errors: Check TWS message window

---

## 📝 Common Tasks

### Add a new feature to dashboard:
1. Read `dashboard.py` to understand structure
2. Find appropriate section (or create new)
3. Add Streamlit widgets (st.button, st.selectbox, etc.)
4. Connect to `ibkr_connector` or `covered_calls_system` APIs
5. Test with `streamlit run dashboard.py`

### Improve Greeks calculations:
1. Edit `covered_calls_system.py`
2. Modify `GreeksCalculator` class methods
3. Use `blackscholes` library for accuracy
4. Test with sample data

### Add new IBKR functionality:
1. Edit `ibkr_connector.py`
2. Add method to `IBKRConnector` class
3. Use `ib_async` API (see docs)
4. Test connection and data retrieval

---

## 🔐 Security Notes

- **Paper Trading recommended** for testing
- **Never commit API keys** or credentials
- **readonly=True** for safe browsing
- **readonly=False** required for actual trading

---

## 📚 Additional Resources

### Documentation
- **UPGRADE_SUMMARY.md** - What was upgraded and why
- **QUICK_START_HE.md** - Hebrew quick start guide
- **GITHUB_INTEGRATIONS.md** - Suggested integrations
- **PROJECT_CONTEXT.md** - Dashboard upgrade context (in ~/Desktop/dashboard-upgrade/)

### External Docs
- ib_async: https://github.com/ib-api-reloaded/ib_async
- blackscholes: https://github.com/CarloLepelaars/blackscholes
- py_vollib: https://github.com/vollib/py_vollib
- Streamlit: https://docs.streamlit.io

---

## 🎯 Next Steps / Priorities

1. **Add "Sell Covered Call" button** to Strategy Finder
2. **Hebrew support (RTL)** for dashboard
3. **Position management table** for active Covered Calls
4. **Rolling recommendations** and execution
5. **IV analysis charts** using new calculate_implied_volatility

See `TODO.md` for complete list.

---

## 💬 Tips for Working with Claude

### What to tell Claude:
- "I want to add [feature] to the dashboard at line [X]"
- "Fix [issue] in [file] around line [Y]"
- "Show me how to use [API/function]"
- "Test if [component] is working"

### What Claude needs to know:
- **Files involved** (dashboard.py, covered_calls_system.py, etc.)
- **Line numbers** if possible
- **Desired outcome** (what should happen)
- **Constraints** (don't break existing features, must use Hebrew, etc.)

### Example Good Request:
```
Add a "Sell Covered Call" button to Strategy Finder (dashboard.py:358-472).
When clicked:
1. Show confirmation dialog with trade details
2. Call ibkr.sell_covered_call(symbol, contracts, strike, expiration)
3. Display success/error message
4. Refresh positions table

Use Streamlit widgets. Connect to existing ibkr instance from session_state.
```

---

**End of Context Document**

*For dashboard upgrade work, see: ~/Desktop/dashboard-upgrade/PROJECT_CONTEXT.md*
