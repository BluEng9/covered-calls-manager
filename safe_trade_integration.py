#!/usr/bin/env python3
"""
🔗 Integration Layer - Combining Safety + Trade Execution
שילוב מערכת ההגנות עם מודול הביצוע
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd

# Add project to path
project_dir = Path.home() / "Projects" / "TradingBots" / "covered-calls-manager"
sys.path.insert(0, str(project_dir))

from trade_execution import TradeExecutor, ExecutionLogger
from safety_features import SafetyManager, TradingMode
from earnings_calendar import EarningsCalendar
from covered_calls_system import CoveredCallStrategy, RiskLevel
from ibkr_connector import IBKRConnector
from trade_analytics import TradeDatabase
from typing import Dict, Optional

class SafeTradeExecutor:
    """
    Combined Safe Trade Execution System
    Integrates safety checks with trade execution
    """
    
    def __init__(self, ib_connector: IBKRConnector, mode: TradingMode = TradingMode.PAPER):
        # Core components
        self.ib = ib_connector
        self.executor = TradeExecutor(ib_connector)
        self.safety = SafetyManager(mode)
        self.calendar = EarningsCalendar()
        self.logger = ExecutionLogger()

        # Analytics & Database
        self.db = TradeDatabase()
        self.analytics = TradeAnalytics(self.db)

        # Trading state
        self.mode = mode
        self.active_trades_today = 0
        
    def execute_covered_call(
        self,
        symbol: str,
        strike: float,
        expiration: str,
        contracts: int,
        current_price: float,
        delta: float,
        premium: float,
        dte: int
    ) -> Dict:
        """
        Execute covered call with full safety checks
        
        Returns: {
            'success': bool,
            'trade_id': str or None,
            'messages': list,
            'trade_details': dict or None
        }
        """
        
        result = {
            'success': False,
            'trade_id': None,
            'messages': [],
            'trade_details': None
        }
        
        # Step 1: Build trade request for validation
        trade_request = {
            'symbol': symbol,
            'contracts': contracts,
            'delta': delta,
            'dte': dte,
            'premium': premium,
            'strike': strike
        }
        
        # Step 2: Safety validation
        st.info("🔍 Running safety checks...")
        approved, safety_messages = self.safety.pre_trade_validation(trade_request)
        result['messages'].extend(safety_messages)
        
        if not approved:
            st.error("❌ Trade rejected by safety system")
            for msg in safety_messages:
                st.write(msg)
            result['success'] = False
            return result
        
        # Step 3: Check earnings
        st.info("📅 Checking earnings calendar...")
        earnings_check = self.calendar.check_before_trade(symbol, dte)
        
        if not earnings_check['safe']:
            st.error(f"❌ Earnings risk: {earnings_check['reason']}")
            result['messages'].append(earnings_check['recommendation'])
            
            # Allow override with confirmation
            if not st.checkbox("⚠️ Override earnings warning (NOT RECOMMENDED)"):
                result['success'] = False
                return result
        
        # Step 4: Final confirmation
        st.success("✅ All safety checks passed!")
        
        # Show trade summary
        with st.expander("📋 Trade Summary", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Symbol", symbol)
                st.metric("Strike", f"${strike}")
                st.metric("Contracts", contracts)
                st.metric("DTE", f"{dte} days")
            with col2:
                st.metric("Premium", f"${premium * 100 * contracts:,.2f}")
                st.metric("Delta", f"{delta:.3f}")
                st.metric("Mode", self.mode.value)
                annual_return = (premium * 100 * contracts / (current_price * 100 * contracts)) * (365/dte) * 100
                st.metric("Annual Return", f"{annual_return:.1f}%")
        
        # Step 5: Get final confirmation
        col1, col2, col3 = st.columns(3)
        
        with col2:
            if self.mode == TradingMode.LIVE:
                confirm = st.button("💰 EXECUTE LIVE TRADE", type="primary", use_container_width=True)
                st.error("⚠️ REAL MONEY - This will execute immediately!")
            elif self.mode == TradingMode.PAPER:
                confirm = st.button("📝 EXECUTE PAPER TRADE", use_container_width=True)
                st.warning("Paper trading mode - simulated execution")
            else:
                confirm = st.button("🎮 EXECUTE DEMO TRADE", use_container_width=True)
                st.info("Demo mode - no real execution")
        
        if not confirm:
            result['messages'].append("Trade cancelled by user")
            return result
        
        # Step 6: Execute trade
        try:
            st.info(f"🚀 Executing {self.mode.value} trade...")
            
            if self.mode == TradingMode.DEMO:
                # Demo mode - just log
                trade_id = f"DEMO_{symbol}_{strike}_{expiration}"
                st.success(f"✅ Demo trade executed: {trade_id}")
                
            else:
                # Paper or Live mode - use real executor
                dry_run = (self.mode == TradingMode.PAPER)
                
                trade = self.executor.sell_covered_call(
                    symbol=symbol,
                    strike=strike,
                    expiration=expiration,
                    contracts=contracts,
                    limit_price=premium if premium > 0 else None,
                    dry_run=dry_run
                )
                
                trade_id = trade.order.orderId if trade else None
                
                # Log the trade (JSONL backup)
                self.logger.log_trade({
                    'trade_id': trade_id,
                    'symbol': symbol,
                    'strike': strike,
                    'expiration': expiration,
                    'contracts': contracts,
                    'premium': premium * 100 * contracts,
                    'delta': delta,
                    'dte': dte,
                    'mode': self.mode.value,
                    'status': 'EXECUTED'
                })

                # Save to database for analytics
                self.db.record_trade({
                    'symbol': symbol,
                    'strike': strike,
                    'expiration': expiration,
                    'contracts': contracts,
                    'premium': premium * 100 * contracts,
                    'delta': delta,
                    'dte': dte,
                    'entry_price': current_price,
                    'strategy': 'covered_call',
                    'mode': self.mode.value
                })

                st.success(f"✅ Trade executed successfully! ID: {trade_id}")
                st.info(f"💾 Trade saved to database for analytics")
                st.balloons()

            # Update daily counter
            self.active_trades_today += 1
            self.safety.todays_trades += 1

            result['success'] = True
            result['trade_id'] = trade_id
            result['trade_details'] = trade_request
            
        except Exception as e:
            st.error(f"❌ Trade execution failed: {e}")
            result['messages'].append(str(e))
            result['success'] = False
        
        return result
    
    def display_execution_panel(self, position: Dict):
        """Display trade execution panel for a position"""
        
        st.markdown(f"### 🎯 Execute Covered Call for {position['symbol']}")
        
        # Get current price
        current_price = position.get('currentPrice', 100)
        shares = position.get('quantity', 0)
        contracts_available = shares // 100
        
        if contracts_available == 0:
            st.error(f"❌ Insufficient shares. Have: {shares}, Need: 100+")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            contracts = st.number_input(
                "Contracts",
                min_value=1,
                max_value=contracts_available,
                value=1
            )
        
        with col2:
            # Strike selection
            strikes = [
                current_price * 1.01,  # 1% OTM
                current_price * 1.02,  # 2% OTM
                current_price * 1.03,  # 3% OTM
                current_price * 1.05,  # 5% OTM
            ]
            strike = st.selectbox(
                "Strike Price",
                options=strikes,
                format_func=lambda x: f"${x:.2f} ({((x/current_price - 1) * 100):.1f}% OTM)"
            )
        
        with col3:
            dte = st.slider("Days to Expiration", 21, 45, 30)
            expiration = (pd.Timestamp.now() + pd.Timedelta(days=dte)).strftime('%Y%m%d')
        
        # Estimate Greeks (simplified)
        moneyness = (strike - current_price) / current_price
        estimated_delta = max(0.1, 0.5 - moneyness * 2)
        estimated_premium = current_price * 0.02 * (dte/30) * (1 - moneyness * 5)
        
        # Display estimated metrics
        st.markdown("#### 📊 Estimated Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Est. Premium", f"${estimated_premium * 100:.2f}")
        with col2:
            st.metric("Est. Delta", f"{estimated_delta:.3f}")
        with col3:
            total_premium = estimated_premium * 100 * contracts
            st.metric("Total Premium", f"${total_premium:.2f}")
        with col4:
            annual_return = (total_premium / (current_price * 100 * contracts)) * (365/dte) * 100
            st.metric("Annual Return", f"{annual_return:.1f}%")
        
        # Execute button
        if st.button(f"Execute {self.mode.value} Trade", type="primary", use_container_width=True):
            result = self.execute_covered_call(
                symbol=position['symbol'],
                strike=strike,
                expiration=expiration,
                contracts=contracts,
                current_price=current_price,
                delta=estimated_delta,
                premium=estimated_premium,
                dte=dte
            )
            
            if result['success']:
                st.experimental_rerun()

def add_to_dashboard():
    """Add safe execution to main dashboard"""
    
    # In the Strategy Finder tab
    st.markdown("## 🚀 Safe Trade Execution")
    
    # Initialize components
    if 'safe_executor' not in st.session_state:
        # Get connector from session
        connector = st.session_state.get('connector')
        if not connector:
            st.error("No connector available. Please connect first.")
            return
        
        # Determine mode
        mode = TradingMode.PAPER  # Default to paper for safety
        
        st.session_state.safe_executor = SafeTradeExecutor(connector, mode)
    
    executor = st.session_state.safe_executor
    
    # Mode selector in sidebar
    with st.sidebar:
        st.markdown("### 🎯 Trading Mode")
        
        mode_options = {
            "🎮 Demo": TradingMode.DEMO,
            "📝 Paper": TradingMode.PAPER,
            "💰 Live": TradingMode.LIVE
        }
        
        selected_mode = st.radio(
            "Select Mode:",
            options=list(mode_options.keys()),
            index=1  # Default to Paper
        )
        
        if mode_options[selected_mode] == TradingMode.LIVE:
            st.error("⚠️ LIVE TRADING MODE")
            confirm_live = st.checkbox("I understand the risks")
            if confirm_live:
                executor.mode = TradingMode.LIVE
                executor.safety.mode = TradingMode.LIVE
        else:
            executor.mode = mode_options[selected_mode]
            executor.safety.mode = mode_options[selected_mode]
    
    # Get positions
    positions = st.session_state.connector.get_stock_positions()
    
    if positions:
        # Position selector
        symbols = [p['symbol'] for p in positions]
        selected_symbol = st.selectbox("Select position:", symbols)
        
        # Get selected position
        position = next((p for p in positions if p['symbol'] == selected_symbol), None)
        
        if position:
            # Display execution panel
            executor.display_execution_panel(position)
    else:
        st.info("No positions available for covered calls")
    
    # Display today's trades
    st.markdown("### 📈 Today's Trades")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Trades Today", executor.active_trades_today)
    with col2:
        st.metric("Daily Limit", executor.safety.limits.max_trades_per_day)
    with col3:
        remaining = executor.safety.limits.max_trades_per_day - executor.active_trades_today
        st.metric("Remaining", remaining)

if __name__ == "__main__":
    st.set_page_config(page_title="Safe Trade Executor", layout="wide")
    st.title("🚀 Safe Trade Execution System")
    
    # Test the integration
    st.info("""
    This module integrates:
    - ✅ Trade Execution (from Claude Code)
    - ✅ Safety Features (pre-trade validation)
    - ✅ Earnings Calendar (avoid risky trades)
    - ✅ Mode Selection (Demo/Paper/Live)
    - ✅ Execution Logging
    """)
    
    add_to_dashboard()
