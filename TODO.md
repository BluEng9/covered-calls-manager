# 📋 TODO - Covered Calls Manager

**Last Updated:** 2025-10-05
**Quick Access:** `cc-todo`

---

## 🔥 Priority 1: Critical Features (Missing Functionality)

### 1. Sell Covered Call from Dashboard
**Status:** ✅ COMPLETED (2025-10-06)
**Effort:** Medium (2-3 hours)
**Impact:** HIGH - Core functionality

**Tasks:**
- [ ] Add "Sell" button to each strike in Strategy Finder results
- [ ] Create confirmation dialog with trade preview
  - Show: Symbol, Strike, Expiration, Contracts, Premium, Total Value
  - Calculate: Max profit, Max loss, Breakeven
- [ ] Connect to `ibkr.sell_covered_call()` method
- [ ] Handle success/error responses
- [ ] Refresh positions table after execution
- [ ] Add safety checks (readonly mode, sufficient shares, etc.)

**Files to modify:**
- `dashboard.py:358-472` (Strategy Finder section)

**Code example:**
```python
if st.button("🚀 Sell Covered Call", key=f"sell_{strike}"):
    with st.expander("⚠️ Confirm Trade"):
        st.write(f"Symbol: {symbol}")
        st.write(f"Strike: ${strike}")
        # ... show details
        if st.button("✅ Confirm"):
            result = ibkr.sell_covered_call(...)
            if result.success:
                st.success("✅ Trade executed!")
```

---

### 2. Active Positions Management Table
**Status:** ✅ COMPLETED (2025-10-06)
**Effort:** Medium (3-4 hours)
**Impact:** HIGH - Position tracking

**Tasks:**
- [ ] Create new section "Active Covered Calls"
- [ ] Fetch all open option positions from IBKR
- [ ] Filter for short calls matching long stock positions
- [ ] Display table with columns:
  - Symbol, Strike, Expiration, DTE
  - Premium received, Current value, P&L
  - Greeks (Delta, Theta, Gamma, Vega)
  - Probability of assignment
- [ ] Add action buttons per row:
  - "Close" - Buy back the call
  - "Roll" - Close and open new position
  - "Details" - Expanded view

**Files to modify:**
- `dashboard.py` - New function `active_positions_table()`
- `ibkr_connector.py` - Add `get_option_positions()` method

---

### 3. Rolling Strategy (Roll Out / Roll Up)
**Status:** ❌ Not Started
**Effort:** High (4-6 hours)
**Impact:** MEDIUM-HIGH - Advanced management

**Tasks:**
- [ ] Implement Roll Out logic (same strike, later expiration)
- [ ] Implement Roll Up logic (higher strike, same/later expiration)
- [ ] Implement Roll Out & Up (both)
- [ ] Calculate net credit/debit for roll
- [ ] Show roll recommendations in Active Positions table
- [ ] Execute roll as atomic transaction (close + open)

**Algorithm:**
```python
def should_roll(position):
    if position.dte < 7:  # Expiring soon
        return True
    if position.delta > 0.70:  # High assignment risk
        return True
    return False

def find_best_roll(current_position):
    # Find new strike/expiration with:
    # 1. Net credit (or minimal debit)
    # 2. Lower Delta
    # 3. Good premium
    ...
```

---

## 🎨 Priority 2: UI/UX Improvements

### 4. Hebrew Support (RTL)
**Status:** ❌ Not Started
**Effort:** Medium (2-3 hours)
**Impact:** MEDIUM - Better UX for Hebrew speakers

**Tasks:**
- [ ] Add RTL CSS to Streamlit
- [ ] Translate all UI text to Hebrew
- [ ] Adjust table/chart layouts for RTL
- [ ] Test on mobile devices

**Code:**
```python
st.markdown("""
<style>
.main { direction: rtl; }
.stDataFrame { direction: ltr; }  /* Keep numbers LTR */
</style>
""", unsafe_allow_html=True)
```

---

### 5. Modern Dashboard Layout
**Status:** ❌ Not Started
**Effort:** Medium (3-4 hours)
**Impact:** MEDIUM - Better visual appeal

**Tasks:**
- [ ] Use Streamlit columns for better layout
- [ ] Add color-coded metrics (green profit, red loss)
- [ ] Implement tabs instead of long scrolling page
- [ ] Add icons and emojis for visual hierarchy
- [ ] Improve spacing and padding

**Structure:**
```
Tab 1: Overview (Account + Portfolio Summary)
Tab 2: Strategy Finder
Tab 3: Active Positions
Tab 4: Performance & Analytics
Tab 5: Settings
```

---

### 6. Mobile Responsive Design
**Status:** ❌ Not Started
**Effort:** Low (1-2 hours)
**Impact:** LOW-MEDIUM - Mobile access

**Tasks:**
- [ ] Test on mobile browser
- [ ] Adjust column widths for small screens
- [ ] Make tables scrollable horizontally
- [ ] Increase button sizes for touch

---

## 📊 Priority 3: Analytics & Insights

### 7. IV Analysis & Charts
**Status:** ❌ Not Started
**Effort:** Medium (2-3 hours)
**Impact:** MEDIUM - Better decision making

**Tasks:**
- [ ] Use new `calculate_implied_volatility()` in Strategy Finder
- [ ] Show IV percentile (current vs historical)
- [ ] Add IV chart over time
- [ ] Highlight high IV opportunities
- [ ] Compare IV across different strikes

**Integration:**
```python
from covered_calls_system import GreeksCalculator

# For each option in results:
market_iv = GreeksCalculator.calculate_implied_volatility(
    option.last_price, stock_price, strike, dte/365, 0.05, OptionType.CALL
)

# Compare to historical
if market_iv > historical_iv * 1.2:
    st.success("🔥 High IV - Great premium!")
```

---

### 8. Probability Calculator
**Status:** ❌ Not Started
**Effort:** Low (1 hour)
**Impact:** LOW-MEDIUM - Better insights

**Tasks:**
- [ ] Calculate probability of expiring OTM (1 - Delta)
- [ ] Show visual probability bar
- [ ] Estimate expected return based on probability

**Display:**
```
Probability OTM: 61.9% ████████░░░░░░░░░░
Expected Return: $1,580 (61.9% of $2,550)
Risk of Assignment: 38.1%
```

---

### 9. Historical Performance Tracking
**Status:** ❌ Not Started
**Effort:** High (5-7 hours)
**Impact:** MEDIUM - Long-term value

**Tasks:**
- [ ] Create database/CSV to store closed positions
- [ ] Track: Entry date, Exit date, P&L, Win rate
- [ ] Show statistics:
  - Total trades, Win rate, Average return
  - Best/worst trades
  - Return by month
- [ ] Generate performance charts

**Schema:**
```python
{
    'date_opened': '2025-01-15',
    'date_closed': '2025-02-14',
    'symbol': 'TSLA',
    'strike': 450,
    'premium_received': 850,
    'premium_paid': 50,  # if bought back
    'net_profit': 800,
    'outcome': 'expired_otm'  # or 'assigned', 'closed_early'
}
```

---

## ⚡ Priority 4: Performance & Optimization

### 10. Faster Options Chain Loading
**Status:** ❌ Not Started
**Effort:** Medium (2-3 hours)
**Impact:** MEDIUM - Better UX

**Tasks:**
- [ ] Implement caching for options data (TTL: 60 seconds)
- [ ] Fetch only OTM calls (not entire chain)
- [ ] Use async/parallel requests for multiple expirations
- [ ] Add loading spinner with progress indicator

**Optimization:**
```python
@st.cache_data(ttl=60)
def get_otm_calls_cached(symbol, price, dte):
    return ibkr.get_otm_calls(symbol, price, dte)
```

---

### 11. Background Data Refresh
**Status:** ❌ Not Started
**Effort:** High (4-5 hours)
**Impact:** LOW-MEDIUM - Real-time data

**Tasks:**
- [ ] Implement WebSocket for real-time price updates
- [ ] Auto-refresh positions every 30 seconds
- [ ] Update Greeks in real-time
- [ ] Show "Last updated" timestamp

---

## 🔧 Priority 5: Code Quality & Maintenance

### 12. Add Unit Tests
**Status:** ❌ Not Started
**Effort:** High (6-8 hours)
**Impact:** MEDIUM - Long-term stability

**Tasks:**
- [ ] Set up pytest
- [ ] Test GreeksCalculator methods
- [ ] Test CoveredCallStrategy scoring
- [ ] Mock IBKR API responses
- [ ] Test edge cases

---

### 13. Error Handling & Logging
**Status:** 🟡 Partial
**Effort:** Medium (2-3 hours)
**Impact:** MEDIUM - Debugging

**Tasks:**
- [ ] Add comprehensive try/except blocks
- [ ] Log all IBKR API calls
- [ ] Show user-friendly error messages
- [ ] Add debug mode toggle in UI

---

### 14. Configuration File
**Status:** ❌ Not Started
**Effort:** Low (1 hour)
**Impact:** LOW - Easier setup

**Tasks:**
- [ ] Create `config.yaml` for user settings
- [ ] Store: IBKR port, client_id, risk_level, default_dte
- [ ] Load config on startup
- [ ] Add settings page in dashboard

---

## 📦 Priority 6: Integrations & Extensions

### 15. Alert System (Email/SMS)
**Status:** ❌ Not Started
**Effort:** Medium (3-4 hours)
**Impact:** LOW-MEDIUM - Notifications

**Tasks:**
- [ ] Set up email notifications (Gmail API or SendGrid)
- [ ] Alert conditions:
  - Position expiring in 3 days
  - Delta > 0.70 (assignment risk)
  - IV spike > 20%
  - Good rolling opportunity
- [ ] User preferences for alerts

---

### 16. Backtesting Module
**Status:** ❌ Not Started
**Effort:** Very High (10+ hours)
**Impact:** HIGH - Strategy validation

**Tasks:**
- [ ] Install `optopsy` library
- [ ] Historical options data source
- [ ] Backtest Covered Calls strategy
- [ ] Compare different Strike selection methods
- [ ] Generate backtest report with metrics

---

### 17. Multi-Broker Support
**Status:** ❌ Not Started
**Effort:** Very High (15+ hours)
**Impact:** LOW - Most users use IBKR only

**Tasks:**
- [ ] Abstract broker interface
- [ ] Add Alpaca connector
- [ ] Add TD Ameritrade connector
- [ ] Unified position/order API

---

## 🐛 Known Bugs & Issues

### 18. Fix: Streamlit reruns losing connection
**Status:** ✅ FIXED (2025-10-06)
**Effort:** Low (30 min)

**Issue:** When Streamlit reruns (e.g., button click), IBKR connection is lost
**Workaround:** Store `ibkr` in `st.session_state`
**Fix:** Already implemented - verify it works consistently

---

### 19. Fix: Greeks not displaying for some options
**Status:** ❌ Not Started
**Effort:** Low (1 hour)

**Issue:** Some options show "N/A" for Greeks
**Cause:** Missing data from IBKR or calculation error
**Fix:** Add better error handling and fallback calculations

---

## 📝 Nice-to-Have (Backlog)

- [ ] Dark mode toggle
- [ ] Export positions to CSV/Excel
- [ ] Portfolio optimizer (how many contracts per stock)
- [ ] Tax reporting (realized gains, wash sales)
- [ ] Social features (share strategies)
- [ ] AI-powered strike recommendations
- [ ] Volatility smile visualization
- [ ] Multi-leg strategies (spreads, strangles)

---

## 📊 Progress Summary

**Total Tasks:** 19 major features + many sub-tasks
**Completed:** 3 (Sell button, Positions table, Connection fix)
**In Progress:** 0
**Not Started:** 16

**Estimated Total Effort:** ~80-100 hours

**Suggested Order:**
1. Sell Covered Call button (Priority 1.1)
2. Active Positions table (Priority 1.2)
3. Hebrew support (Priority 2.4)
4. IV Analysis (Priority 3.7)
5. Rolling strategy (Priority 1.3)

---

**Quick Access:**
```bash
cc-todo       # Show this file
cc-context    # Show Claude context
cc-run        # Start dashboard
```

**For Claude:**
When working on a task, mark it in this file and track progress with TodoWrite tool.
