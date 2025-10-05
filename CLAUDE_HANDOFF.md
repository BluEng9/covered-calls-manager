# 🤖 Claude Session Handoff Document
**Last Updated:** $(date +"%Y-%m-%d %H:%M")
**Project:** Covered Calls Manager v2.1

## 🎯 Quick Start for Next Claude Session

### 1. Load Project Context
```bash
cd ~/Projects/TradingBots/covered-calls-manager
cat PROJECT_MEMORY.md  # Read this first!
cat STATUS_REPORT.md   # Detailed status
```

### 2. Current State
- **Working Features:** Demo Mode ✅, CSV Upload ✅
- **Issues:** IBKR Paper Trading account empty
- **Last Session:** Fixed CSV/Demo bugs, added Hebrew support
- **Next Priority:** Add real trading capabilities

### 3. Run Dashboard
```bash
source venv/bin/activate
streamlit run dashboard.py --server.port 8508
```

### 4. Continue Development
**High Priority Tasks:**
1. Implement sell_covered_call() execution
2. Add position rolling functionality
3. Create alert system

**Medium Priority:**
1. IV Analysis charts
2. Performance tracking database
3. Email notifications

### 5. Test Modes
- **Demo:** Use demo button in sidebar
- **CSV:** Upload my_combined_portfolio.csv
- **IBKR:** TWS on port 7497 (empty account)

## 📁 Key Files to Review
1. `covered_calls_system.py` - Core strategy engine
2. `dashboard.py` - Main UI (1072 lines)
3. `PROJECT_MEMORY.md` - Recent work & issues
4. `fix_immediate_issues.py` - Bug fixes to apply

## 🔧 Pending Fixes
```bash
# If bugs reappear, run:
python3 fix_immediate_issues.py
```

## 📊 Portfolio Summary
- Total: $182,752
- Accounts: 3 (IBKR, Leumi, Ziko)
- Positions: TSLA (229), MSTR (130), IBIT (135), MSTY (450)

## 🚀 Git Commands
```bash
git pull origin main  # Get latest
git add -A           # Stage changes
git commit -m "msg"  # Commit
git push            # Upload
```

**Remember:** This project uses ib_async (not ib_insync) and Python 3.13.7
