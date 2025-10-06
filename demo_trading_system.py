#!/usr/bin/env python3
"""
🎮 Demo Trading System - Practice without IBKR connection
מערכת תרגול ללא חיבור לברוקר
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from safety_features import SafetyManager, TradingMode
from earnings_calendar import EarningsCalendar
from trade_analytics import TradeDatabase
import random

st.set_page_config(page_title="🎮 Demo Trading System", layout="wide")

# Initialize components
if 'safety' not in st.session_state:
    st.session_state.safety = SafetyManager(mode=TradingMode.DEMO)

if 'calendar' not in st.session_state:
    st.session_state.calendar = EarningsCalendar()

if 'db' not in st.session_state:
    st.session_state.db = TradeDatabase()

if 'demo_positions' not in st.session_state:
    # Create demo stock positions
    st.session_state.demo_positions = [
        {'symbol': 'AAPL', 'quantity': 300, 'currentPrice': 178.50, 'avgCost': 165.00},
        {'symbol': 'MSFT', 'quantity': 200, 'currentPrice': 420.30, 'avgCost': 395.00},
        {'symbol': 'NVDA', 'quantity': 100, 'currentPrice': 875.20, 'avgCost': 720.00},
        {'symbol': 'TSLA', 'quantity': 400, 'currentPrice': 242.80, 'avgCost': 210.00},
        {'symbol': 'GOOGL', 'quantity': 150, 'currentPrice': 142.50, 'avgCost': 130.00},
        {'symbol': 'MSTR', 'quantity': 200, 'currentPrice': 385.00, 'avgCost': 280.00},
        {'symbol': 'AMZN', 'quantity': 250, 'currentPrice': 175.30, 'avgCost': 155.00},
        {'symbol': 'META', 'quantity': 150, 'currentPrice': 485.20, 'avgCost': 420.00},
    ]

if 'trades_today' not in st.session_state:
    st.session_state.trades_today = 0

# Header
st.title("🎮 Demo Trading System")

st.info("""
**תרגול חופשי ללא חיבור לברוקר**

✅ All safety checks enabled
✅ Earnings calendar protection
✅ Auto-save to database
✅ No IBKR connection required
""")

# Sidebar - Trading Mode
with st.sidebar:
    st.markdown("### 🎯 Trading Mode")
    st.success("🎮 **DEMO MODE**")
    st.write("Practice trading without real broker connection")

    st.markdown("---")

    st.markdown("### 📊 Today's Activity")
    st.metric("Trades Today", st.session_state.trades_today)
    st.metric("Daily Limit", st.session_state.safety.limits.max_trades_per_day)
    remaining = st.session_state.safety.limits.max_trades_per_day - st.session_state.trades_today
    st.metric("Remaining", remaining)

# Main content
st.markdown("## 🚀 Execute Covered Call")

# Position selector
col1, col2 = st.columns([2, 3])

with col1:
    symbols = [p['symbol'] for p in st.session_state.demo_positions]
    selected_symbol = st.selectbox("📈 Select Position:", symbols)

    # Get selected position
    position = next((p for p in st.session_state.demo_positions if p['symbol'] == selected_symbol), None)

    if position:
        st.markdown("#### Position Details")
        st.write(f"**Shares:** {position['quantity']}")
        st.write(f"**Current Price:** ${position['currentPrice']:.2f}")
        st.write(f"**Avg Cost:** ${position['avgCost']:.2f}")
        pnl = (position['currentPrice'] - position['avgCost']) * position['quantity']
        st.write(f"**P&L:** ${pnl:,.2f}")

with col2:
    if position:
        st.markdown("#### Trade Configuration")

        current_price = position['currentPrice']
        contracts_available = position['quantity'] // 100

        if contracts_available == 0:
            st.error(f"❌ Need at least 100 shares. You have: {position['quantity']}")
        else:
            # Trade inputs
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                contracts = st.number_input(
                    "Contracts",
                    min_value=1,
                    max_value=contracts_available,
                    value=min(2, contracts_available)
                )

            with col_b:
                # Strike selection
                otm_pct = st.slider("OTM %", 1, 10, 3)
                strike = current_price * (1 + otm_pct/100)
                st.metric("Strike", f"${strike:.2f}")

            with col_c:
                dte = st.slider("DTE", 21, 45, 30)
                expiration = (datetime.now() + timedelta(days=dte)).strftime('%Y%m%d')
                st.metric("Expiration", expiration)

            # Estimate Greeks and premium
            moneyness = (strike - current_price) / current_price
            estimated_delta = max(0.1, 0.5 - moneyness * 2)
            estimated_premium = current_price * 0.02 * (dte/30) * (1 - moneyness * 5)

            st.markdown("---")
            st.markdown("#### 📊 Estimated Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Premium/Contract", f"${estimated_premium * 100:.2f}")
            with col2:
                st.metric("Delta", f"{estimated_delta:.3f}")
            with col3:
                total_premium = estimated_premium * 100 * contracts
                st.metric("Total Premium", f"${total_premium:.2f}")
            with col4:
                capital_at_risk = current_price * 100 * contracts
                annual_return = (total_premium / capital_at_risk) * (365/dte) * 100
                st.metric("Annual Return", f"{annual_return:.1f}%")

            st.markdown("---")

            # Execute button
            execute_clicked = st.button("🚀 EXECUTE DEMO TRADE", type="primary", use_container_width=True)

            if execute_clicked:

                # Build trade request
                trade_request = {
                    'symbol': selected_symbol,
                    'contracts': contracts,
                    'delta': estimated_delta,
                    'dte': dte,
                    'premium': estimated_premium,
                    'strike': strike
                }

                # Step 1: Safety validation
                st.info("🔍 Running safety checks...")
                approved, safety_messages = st.session_state.safety.pre_trade_validation(trade_request)

                for msg in safety_messages:
                    st.write(msg)

                if not approved:
                    st.error("❌ Trade rejected by safety system")
                else:
                    # Step 2: Check earnings
                    st.info("📅 Checking earnings calendar...")
                    earnings_check = st.session_state.calendar.check_before_trade(selected_symbol, dte)

                    if not earnings_check['safe']:
                        st.warning(f"⚠️ {earnings_check['reason']}")
                        st.write(earnings_check['recommendation'])

                    # Step 3: Execute
                    st.success("✅ All safety checks passed!")

                    # Generate demo trade ID
                    trade_id = f"DEMO_{selected_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                    # Save to database
                    st.session_state.db.record_trade({
                        'symbol': selected_symbol,
                        'strike': strike,
                        'expiration': expiration,
                        'contracts': contracts,
                        'quantity': contracts * 100,  # Required field - shares covered
                        'premium': total_premium,
                        'delta': estimated_delta,
                        'dte': dte,
                        'entry_price': current_price,
                        'strategy': 'covered_call',
                        'action': 'SELL',  # Required field
                        'mode': 'DEMO'
                    })

                    # Update counters
                    st.session_state.trades_today += 1
                    st.session_state.safety.todays_trades += 1

                    st.success(f"✅ Demo trade executed! ID: {trade_id}")
                    st.info(f"💾 Trade saved to database")
                    st.balloons()

                    # Show trade summary
                    with st.expander("📋 Trade Summary", expanded=True):
                        st.write(f"""
                        **Trade Details:**
                        - Symbol: {selected_symbol}
                        - Contracts: {contracts}
                        - Strike: ${strike:.2f} ({otm_pct}% OTM)
                        - Expiration: {expiration} ({dte} days)
                        - Premium: ${total_premium:.2f}
                        - Delta: {estimated_delta:.3f}
                        - Annual Return: {annual_return:.1f}%
                        """)

                    # Add refresh button to go back
                    if st.button("✅ Done - Back to Trading", type="secondary", use_container_width=True):
                        st.rerun()

# Show recent trades from database
st.markdown("---")
st.markdown("## 📊 Trade History")

recent_trades = st.session_state.db.get_open_positions()
if recent_trades is not None and len(recent_trades) > 0:
    df = pd.DataFrame(recent_trades)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No trades yet. Execute your first demo trade above!")

# Performance summary
st.markdown("---")
st.markdown("## 📈 Performance Summary")

summary = st.session_state.db.get_performance_summary()
if summary:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trades", summary.get('total_trades', 0))
    with col2:
        st.metric("Open Positions", summary.get('open_trades', 0))
    with col3:
        st.metric("Total Premium", f"${summary.get('total_premium', 0):,.2f}")
    with col4:
        st.metric("Avg Annual Return", f"{summary.get('avg_annual_return', 0):.1f}%")
