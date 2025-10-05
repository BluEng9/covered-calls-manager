# Project Memory - Covered Calls Manager

## Last Session Summary
**Date:** 2025-10-06
**Last Commit:** 7ef31fa - Fix dict/object compatibility and add comprehensive status report

## Active Context

### Recent Work Completed
1. ✅ Fixed `get_otm_calls()` missing from PortfolioDataStore (csv_portfolio_loader.py:199-204)
2. ✅ Fixed `get_otm_calls()` missing from DemoIBKRConnector (demo_mode.py:199-212)
3. ✅ Fixed dict/object compatibility with `get_stock_attr()` helper (dashboard.py:32-37)
4. ✅ Created comprehensive STATUS_REPORT.md for Claude Max handoff
5. ✅ Created my_combined_portfolio.csv with 3 accounts (IB, Leumi, Ziko)
6. ✅ Fixed CSV column naming ("Price" not "Current Price")

### Known Issues
1. ⚠️ IBKR Connection fails - TWS/Gateway not running on port 7497
2. ⚠️ Paper Trading account empty (0 positions)
3. ⚠️ AsyncIO event loop conflicts on reconnection
4. ⚠️ 11+ remaining pos.stock.* references need conversion to get_stock_attr()

### Current Portfolio Data
- **Interactive Brokers:** $110,127 (TSLA 194@$230, MSTR 30@$100, IBIT 100@$35, MSTY 450@$14.70)
- **Bank Leumi:** ~$40,000 (MSTR 50@$70, IBIT 35@$35)
- **Ziko Bank:** $32,625 (MSTR 50@$70, TSLA 35@$165)
- **Total Portfolio Value:** ~$182,752

### Working Modes
- ✅ Demo Mode - Fully functional with mock data
- ✅ CSV Upload Mode - Functional with user's portfolio
- ❌ Live IBKR Mode - Requires TWS/Gateway running

## Pending Tasks

### High Priority
1. Test CSV upload with my_combined_portfolio.csv after all fixes
2. Fix remaining 11 pos.stock.* direct attribute references in dashboard.py
3. Resolve AsyncIO event loop cleanup in ibkr_connector.py

### Medium Priority
4. Implement covered call position tracking in CSV mode
5. Add multi-account view/filtering in dashboard
6. Complete backtesting integration (currently 60% done)

### Low Priority
7. Add options chain visualization
8. Implement alert system for expiring positions
9. Add portfolio rebalancing recommendations

## Key Decisions & Context

### Architecture Choices
- **Multi-mode support:** Live IBKR, CSV Upload, Demo Mode for flexibility
- **Dict/Object flexibility:** Use helper functions to support both data formats
- **Streamlit UI:** 5-tab dashboard (Overview, Positions, Strategy Finder, Backtesting, Settings)
- **Risk Management:** Built-in portfolio risk scoring and warnings

### File Organization
- `dashboard.py` - Main UI (3,400+ lines)
- `ibkr_connector.py` - Live IBKR integration
- `csv_portfolio_loader.py` - CSV import functionality
- `demo_mode.py` - Mock data for testing
- `covered_call_strategy.py` - Strategy logic
- `backtesting.py` - Historical analysis

### Dependencies
- ib_async - IBKR API client
- streamlit - Web UI framework
- pandas - Data manipulation
- yfinance - Historical data

## Quick Commands

```bash
# Run dashboard
streamlit run dashboard.py

# Git backup
git add . && git commit -m "Your message"

# Check project status
git status
git log --oneline -5
```

## Notes for Next Session
- User requested memory system (זיכרון) - THIS FILE IS THE ANSWER
- STATUS_REPORT.md has full technical documentation for Claude Max
- CSV mode is recommended until IBKR connection is established
- All recent fixes are in commit 7ef31fa

## Important File References
- Bug fixes: dashboard.py:32-37, csv_portfolio_loader.py:199-211, demo_mode.py:199-212
- Portfolio data: my_combined_portfolio.csv (excluded from git)
- Full status: STATUS_REPORT.md
- Strategy logic: covered_call_strategy.py:30-150
