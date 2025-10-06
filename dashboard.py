"""
Covered Calls Dashboard - Streamlit Web Interface
Interactive dashboard for monitoring and managing covered call positions
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import asyncio
import nest_asyncio

# Fix for Python 3.13 event loop issue
nest_asyncio.apply()

from covered_calls_system import (
    Stock, OptionContract, CoveredCall, PortfolioManager,
    CoveredCallStrategy, RiskLevel, OptionType, PositionStatus,
    RollStrategy, AlertSystem
)
from ibkr_connector import IBKRConnector, IBKRConfig
from dashboard_risk_components import render_risk_dashboard, render_position_validator
from trade_analytics import TradeDatabase, add_analytics_to_dashboard
from risk_manager import RiskManager
from demo_mode import DemoIBKRConnector
from csv_portfolio_loader import CSVPortfolioLoader, PortfolioDataStore
from covered_calls_backtester import CoveredCallBacktester


# Helper function to handle both dict and object stock data
def get_stock_attr(stock, attr_name, default=None):
    """Get attribute from stock (dict or object)"""
    if isinstance(stock, dict):
        return stock.get(attr_name, default)
    return getattr(stock, attr_name, default)


# Page configuration
st.set_page_config(
    page_title="Covered Calls Manager",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .profit-positive {
        color: #00cc00;
        font-weight: bold;
    }
    .profit-negative {
        color: #cc0000;
        font-weight: bold;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
    }
    .danger-box {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


class DashboardState:
    """Manage dashboard state"""

    def __init__(self):
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = PortfolioManager()
        if 'ibkr' not in st.session_state:
            st.session_state.ibkr = None
        if 'connected' not in st.session_state:
            st.session_state.connected = False
        if 'risk_level' not in st.session_state:
            st.session_state.risk_level = RiskLevel.MODERATE
        if 'portfolio_data' not in st.session_state:
            st.session_state.portfolio_data = None
        if 'csv_mode' not in st.session_state:
            st.session_state.csv_mode = False


def sidebar_config():
    """Sidebar configuration and connection settings"""
    st.sidebar.title("🎯 Covered Calls Manager")
    st.sidebar.markdown("---")

    st.sidebar.subheader("IBKR Connection")

    # Demo mode toggle
    demo_mode = st.sidebar.checkbox("🎮 Demo Mode (Sample Data)", value=False,
                                     help="Use demo mode to explore features without connecting to IBKR")

    if demo_mode:
        # Demo mode - use mock data
        if not st.session_state.connected:
            if st.sidebar.button("🎮 Start Demo"):
                st.session_state.ibkr = DemoIBKRConnector()
                st.session_state.connected = True
                st.session_state.demo_mode = True
                st.sidebar.success("✅ Demo Mode Active!")
                st.rerun()
        else:
            st.sidebar.success("🎮 Demo Mode Active")
            if st.sidebar.button("Stop Demo"):
                st.session_state.connected = False
                st.session_state.demo_mode = False
                st.sidebar.info("Demo stopped")
                st.rerun()
    else:
        # Live mode - real IBKR connection
        # Connection settings
        host = st.sidebar.text_input("Host", value="127.0.0.1")
        port = st.sidebar.number_input("Port", value=7497, step=1)
        client_id = st.sidebar.number_input("Client ID", value=1, step=1)
        readonly = st.sidebar.checkbox("Read-only mode", value=True)

        # Connect/Disconnect button
        if not st.session_state.connected:
            if st.sidebar.button("🔌 Connect to IBKR"):
                config = IBKRConfig(
                    host=host,
                    port=int(port),
                    client_id=int(client_id),
                    readonly=readonly
                )
                ibkr = IBKRConnector(config)
                if ibkr.connect():
                    st.session_state.ibkr = ibkr
                    st.session_state.connected = True
                    st.session_state.demo_mode = False
                    st.sidebar.success("✅ Connected!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Connection failed")
        else:
            st.sidebar.success("✅ Connected to IBKR")
            if st.sidebar.button("🔌 Disconnect"):
                if st.session_state.ibkr:
                    st.session_state.ibkr.disconnect()
                st.session_state.connected = False
                st.session_state.demo_mode = False
                st.sidebar.info("Disconnected")
                st.rerun()

    # CSV Upload Mode
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 CSV Portfolio Upload")

    uploaded_file = st.sidebar.file_uploader(
        "Upload Portfolio CSV",
        type=['csv'],
        help="Upload IBKR portfolio export or simple format (Symbol,Quantity,AvgCost,CurrentPrice)"
    )

    if uploaded_file is not None:
        try:
            # Read CSV content
            csv_content = uploaded_file.getvalue().decode('utf-8')

            # Load portfolio data
            if st.session_state.portfolio_data is None:
                st.session_state.portfolio_data = PortfolioDataStore()

            st.session_state.portfolio_data.load_from_csv(csv_content)
            st.session_state.csv_mode = True
            st.session_state.connected = True
            st.session_state.ibkr = st.session_state.portfolio_data

            st.sidebar.success(f"✅ Loaded {len(st.session_state.portfolio_data.stocks)} positions")
            st.sidebar.info(f"Last updated: {st.session_state.portfolio_data.timestamp}")

        except Exception as e:
            st.sidebar.error(f"❌ Error loading CSV: {str(e)}")
            st.session_state.csv_mode = False

    st.sidebar.markdown("---")

    # Strategy settings
    st.sidebar.subheader("⚙️ Strategy Settings")
    risk_level = st.sidebar.selectbox(
        "Risk Level",
        options=[level.value for level in RiskLevel],
        index=1
    )
    st.session_state.risk_level = RiskLevel[risk_level]

    # Auto-refresh
    st.sidebar.markdown("---")
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        st.sidebar.info("Dashboard will refresh every 30 seconds")
        # This would need to be implemented with st.experimental_rerun


def account_overview():
    """Display account overview and key metrics"""
    st.header("📊 Account Overview")

    if not st.session_state.connected:
        st.warning("⚠️ Not connected to IBKR. Please connect in the sidebar.")
        return

    try:
        ibkr = st.session_state.ibkr
        account = ibkr.get_account_summary()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Net Liquidation",
                f"${account.get('NetLiquidation', 0):,.2f}"
            )

        with col2:
            st.metric(
                "Total Cash",
                f"${account.get('TotalCashValue', 0):,.2f}"
            )

        with col3:
            unrealized = account.get('UnrealizedPnL', 0)
            st.metric(
                "Unrealized P&L",
                f"${unrealized:,.2f}",
                delta=f"{unrealized:,.2f}"
            )

        with col4:
            realized = account.get('RealizedPnL', 0)
            st.metric(
                "Realized P&L",
                f"${realized:,.2f}",
                delta=f"{realized:,.2f}"
            )

    except Exception as e:
        st.error(f"Error fetching account data: {e}")


def active_positions_table():
    """Display active covered call positions with P&L and Greeks"""
    st.header("📊 Active Covered Call Positions")

    if not st.session_state.connected:
        st.warning("⚠️ Not connected to IBKR. Please connect in the sidebar.")
        return

    try:
        ibkr = st.session_state.ibkr
        positions = ibkr.get_covered_call_positions()

        if not positions:
            st.info("ℹ️ No active covered call positions found")
            return

        # Convert to DataFrame
        df = pd.DataFrame(positions)

        # Format columns
        df['option_expiry'] = pd.to_datetime(df['option_expiry']).dt.strftime('%Y-%m-%d')
        df['stock_price'] = df['stock_price'].apply(lambda x: f"${x:.2f}")
        df['option_strike'] = df['option_strike'].apply(lambda x: f"${x:.2f}")
        df['premium_received'] = df['premium_received'].apply(lambda x: f"${x:.2f}")
        df['current_option_value'] = df['current_option_value'].apply(lambda x: f"${x:.2f}")
        df['unrealized_pnl'] = df['unrealized_pnl'].apply(lambda x: f"${x:.2f}")
        df['delta'] = df['delta'].apply(lambda x: f"{x:.3f}" if x is not None else "N/A")
        df['theta'] = df['theta'].apply(lambda x: f"{x:.3f}" if x is not None else "N/A")

        # Rename columns for display
        df = df.rename(columns={
            'symbol': 'Symbol',
            'stock_qty': 'Shares',
            'stock_price': 'Stock Price',
            'option_strike': 'Strike',
            'option_expiry': 'Expiry',
            'option_dte': 'DTE',
            'contracts': 'Contracts',
            'premium_received': 'Premium',
            'current_option_value': 'Current Value',
            'unrealized_pnl': 'P&L',
            'delta': 'Delta',
            'theta': 'Theta'
        })

        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        # Action buttons for each position
        st.markdown("### Position Actions")
        for idx, pos in enumerate(positions):
            with st.expander(f"📌 {pos['symbol']} - ${pos['option_strike']:.2f} ({pos['option_dte']} DTE)"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button(f"📊 Details", key=f"details_{idx}"):
                        st.info("Details view coming soon...")

                with col2:
                    if st.button(f"🔄 Roll", key=f"roll_{idx}"):
                        st.info("Roll functionality coming soon...")

                with col3:
                    if st.button(f"❌ Close", key=f"close_{idx}"):
                        st.warning("Close functionality coming soon...")

    except Exception as e:
        st.error(f"Error fetching positions: {e}")


def portfolio_summary():
    """Display portfolio summary"""
    st.header("💼 Portfolio Summary")

    portfolio = st.session_state.portfolio

    if not portfolio.positions:
        st.info("📭 No active covered call positions")
        return

    metrics = portfolio.get_portfolio_metrics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Positions", metrics['total_positions'])

    with col2:
        st.metric("Total Stock Value", f"${metrics['total_stock_value']:,.2f}")

    with col3:
        st.metric("Premium Collected", f"${metrics['total_premium_collected']:,.2f}")

    with col4:
        st.metric(
            "Portfolio Return",
            f"{metrics['portfolio_return_if_assigned']:.2f}%"
        )

    # Additional metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Avg Days to Expiration", f"{metrics['avg_days_to_expiration']:.0f}")

    with col2:
        st.metric("Avg Delta", f"{metrics['avg_delta']:.3f}")

    with col3:
        total_theta = portfolio.calculate_total_theta()
        st.metric("Total Daily Theta", f"${total_theta:.2f}")


def positions_table():
    """Display detailed positions table"""
    st.header("📋 Active Positions")

    portfolio = st.session_state.portfolio

    if not portfolio.positions:
        return

    # Create DataFrame from positions
    data = []
    for pos in portfolio.positions:
        data.append({
            'Symbol': pos.stock.symbol,
            'Quantity': pos.quantity,
            'Stock Price': f"${pos.stock.current_price:.2f}",
            'Strike': f"${pos.option.strike:.2f}",
            'Expiration': pos.option.expiration.strftime('%Y-%m-%d'),
            'DTE': pos.option.days_to_expiration,
            'Premium': f"${pos.net_premium:.2f}",
            'Max Profit': f"${pos.max_profit:.2f}",
            'Return': f"{pos.return_if_assigned:.2f}%",
            'Ann. Return': f"{pos.annualized_return:.2f}%",
            'Delta': f"{pos.option.delta:.3f}",
            'IV': f"{pos.option.implied_volatility:.1f}%",
            'Status': pos.status.value
        })

    df = pd.DataFrame(data)

    # Style the DataFrame
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"covered_calls_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


def expiration_calendar():
    """Display expiration calendar"""
    st.header("📅 Expiration Calendar")

    portfolio = st.session_state.portfolio
    calendar = portfolio.get_expiration_calendar()

    if not calendar:
        st.info("No positions to display")
        return

    # Create visualization
    for exp_date, positions in sorted(calendar.items()):
        with st.expander(f"**{exp_date}** - {len(positions)} position(s)"):
            for pos in positions:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.write(f"**{pos.stock.symbol}**")

                with col2:
                    st.write(f"Strike: ${pos.option.strike:.2f}")

                with col3:
                    st.write(f"Premium: ${pos.net_premium:.2f}")

                with col4:
                    # Check if at risk
                    if pos.stock.current_price >= pos.option.strike:
                        st.markdown("🔴 **AT RISK**")
                    else:
                        st.markdown("🟢 Safe")


def alerts_panel():
    """Display alerts and warnings"""
    st.header("⚠️ Alerts & Notifications")

    portfolio = st.session_state.portfolio
    alert_system = AlertSystem()
    alerts = alert_system.check_alerts(portfolio)

    if not alerts:
        st.success("✅ No alerts at this time")
        return

    # Group alerts by severity
    high_alerts = [a for a in alerts if a['severity'] == 'HIGH']
    medium_alerts = [a for a in alerts if a['severity'] == 'MEDIUM']
    low_alerts = [a for a in alerts if a['severity'] == 'LOW']

    # Display high severity alerts
    if high_alerts:
        st.markdown("### 🔴 High Priority")
        for alert in high_alerts:
            st.markdown(f"""
            <div class="danger-box">
                <strong>{alert['type']}</strong><br>
                {alert['message']}<br>
                <em>Action: {alert['action']}</em>
            </div>
            """, unsafe_allow_html=True)

    # Display medium severity alerts
    if medium_alerts:
        st.markdown("### 🟡 Medium Priority")
        for alert in medium_alerts:
            st.markdown(f"""
            <div class="warning-box">
                <strong>{alert['type']}</strong><br>
                {alert['message']}<br>
                <em>Action: {alert['action']}</em>
            </div>
            """, unsafe_allow_html=True)

    # Display low severity alerts
    if low_alerts:
        with st.expander("🟢 Low Priority Alerts"):
            for alert in low_alerts:
                st.info(f"**{alert['type']}**: {alert['message']}")


def strategy_finder():
    """Find and suggest covered call strategies"""
    st.header("🎯 Strategy Finder")

    if not st.session_state.connected:
        st.warning("Please connect to IBKR first")
        return

    ibkr = st.session_state.ibkr

    # Get stock positions
    stocks = ibkr.get_stock_positions()

    if not stocks:
        st.info("No stock positions found")
        return

    # Select stock - handle both dict and object format
    stock_symbols = []
    for stock in stocks:
        if isinstance(stock, dict):
            stock_symbols.append(stock['symbol'])
        else:
            stock_symbols.append(stock.symbol)

    selected_symbol = st.selectbox(
        "Select Stock",
        options=stock_symbols
    )

    # Find selected stock
    selected_stock = None
    for s in stocks:
        if isinstance(s, dict):
            if s['symbol'] == selected_symbol:
                selected_stock = s
                break
        else:
            if s.symbol == selected_symbol:
                selected_stock = s
                break

    if not selected_stock:
        return

    # Display stock info - handle both dict and object format
    def get_attr(obj, attr, default=0):
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    current_price = get_attr(selected_stock, 'current_price')
    quantity = get_attr(selected_stock, 'quantity')
    avg_cost = get_attr(selected_stock, 'avg_cost')

    # Calculate P&L if not in dict
    if isinstance(selected_stock, dict):
        unrealized_pnl = (current_price - avg_cost) * quantity
        unrealized_pnl_pct = ((current_price - avg_cost) / avg_cost) * 100 if avg_cost > 0 else 0
    else:
        unrealized_pnl = get_attr(selected_stock, 'unrealized_pnl', 0)
        unrealized_pnl_pct = get_attr(selected_stock, 'unrealized_pnl_pct', 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${current_price:.2f}")
    with col2:
        st.metric("Quantity", int(quantity))
    with col3:
        st.metric("Avg Cost", f"${avg_cost:.2f}")
    with col4:
        pnl_color = "profit-positive" if unrealized_pnl >= 0 else "profit-negative"
        st.markdown(
            f"<div class='{pnl_color}'>P&L: ${unrealized_pnl:.2f} "
            f"({unrealized_pnl_pct:.2f}%)</div>",
            unsafe_allow_html=True
        )

    # Strategy parameters
    st.subheader("Strategy Parameters")
    col1, col2 = st.columns(2)

    with col1:
        target_dte = st.slider("Target Days to Expiration", 7, 60, 30)

    with col2:
        max_results = st.slider("Number of Results", 3, 10, 5)

    if st.button("🔍 Find Best Strikes"):
        with st.spinner("Analyzing options..."):
            try:
                # Get current price (handle both dict and object)
                current_price = get_stock_attr(selected_stock, 'current_price')

                # Get OTM calls
                options = ibkr.get_otm_calls(
                    selected_symbol,
                    current_price,
                    days_to_expiration=target_dte
                )

                if not options:
                    st.warning("No suitable options found")
                    return

                # Score options
                strategy = CoveredCallStrategy(st.session_state.risk_level)
                scored_options = strategy.find_best_strike(
                    options,
                    current_price,
                    top_n=max_results
                )

                # Display results
                st.success(f"Found {len(scored_options)} suitable options")

                for i, (option, score) in enumerate(scored_options, 1):
                    with st.expander(f"#{i} - Strike ${option.strike:.2f} (Score: {score:.0f}/100)"):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write("**Contract Details**")
                            st.write(f"Strike: ${option.strike:.2f}")
                            st.write(f"Premium: ${option.premium:.2f}")
                            st.write(f"Expiration: {option.expiration.strftime('%Y-%m-%d')}")
                            st.write(f"DTE: {option.days_to_expiration}")

                        with col2:
                            st.write("**Greeks**")
                            st.write(f"Delta: {option.delta:.3f}")
                            st.write(f"Theta: {option.theta:.4f}")
                            st.write(f"IV: {option.implied_volatility:.1f}%")

                        with col3:
                            st.write("**Returns**")
                            # Calculate potential returns
                            contracts = selected_stock.quantity // 100
                            total_premium = option.premium * contracts * 100
                            premium_pct = (total_premium / selected_stock.market_value) * 100
                            annualized = premium_pct * (365 / option.days_to_expiration)

                            st.write(f"Premium: ${total_premium:.2f}")
                            st.write(f"Return: {premium_pct:.2f}%")
                            st.write(f"Annualized: {annualized:.2f}%")

                        # Action button with confirmation
                        if f'confirm_sell_{i}' not in st.session_state:
                            st.session_state[f'confirm_sell_{i}'] = False

                        col_btn1, col_btn2 = st.columns([1, 3])

                        with col_btn1:
                            if st.button(f"🚀 Sell Covered Call", key=f"sell_{i}", type="primary"):
                                st.session_state[f'confirm_sell_{i}'] = True

                        # Confirmation dialog
                        if st.session_state.get(f'confirm_sell_{i}', False):
                            st.warning("⚠️ **Confirm Trade**")

                            # Display trade summary
                            st.write(f"**Symbol:** {selected_symbol}")
                            st.write(f"**Strike:** ${option.strike:.2f}")
                            st.write(f"**Expiration:** {option.expiration.strftime('%Y-%m-%d')}")
                            st.write(f"**Premium:** ${total_premium:.2f}")
                            st.write(f"**Contracts:** {contracts}")

                            # Risk validation
                            try:
                                from risk_manager import RiskManager
                                risk_manager = RiskManager()

                                # Get account value from session state or estimate
                                account_value = st.session_state.get('account_value',
                                                                    sum(pos.stock.market_value for pos in portfolio.positions) if portfolio.positions else 100000)

                                # Convert existing positions for risk check
                                existing_positions = []
                                for pos in portfolio.positions:
                                    existing_positions.append({
                                        'symbol': get_stock_attr(pos.stock, 'symbol'),
                                        'quantity': get_stock_attr(pos.stock, 'quantity'),
                                        'price': get_stock_attr(pos.stock, 'current_price'),
                                        'has_covered_call': True,
                                        'option_delta': get_stock_attr(pos.option, 'delta', 0.5),
                                        'days_to_expiry': get_stock_attr(pos.option, 'days_to_expiration', 30)
                                    })

                                approved, reason = risk_manager.validate_new_position(
                                    symbol=selected_symbol,
                                    contracts=contracts,
                                    strike=option.strike,
                                    current_price=selected_stock.current_price,
                                    account_value=account_value,
                                    existing_positions=existing_positions
                                )

                                if approved:
                                    st.success(reason)
                                else:
                                    st.error(reason)

                            except Exception as e:
                                st.warning(f"Risk validation unavailable: {str(e)}")
                                approved = True  # Allow trade if risk check fails

                            col_confirm1, col_confirm2 = st.columns(2)

                            with col_confirm1:
                                if st.button("✅ Execute Trade", key=f"execute_{i}", disabled=not approved):
                                    try:
                                        # Get IBKR connector from session state
                                        ibkr = st.session_state.get('ibkr')
                                        if not ibkr or not ibkr.connected:
                                            st.error("❌ Not connected to IBKR. Please connect first.")
                                        else:
                                            # Execute the trade
                                            expiration_str = option.expiration.strftime('%Y%m%d')
                                            trade = ibkr.sell_covered_call(
                                                symbol=selected_symbol,
                                                quantity=contracts,
                                                strike=option.strike,
                                                expiration=expiration_str,
                                                limit_price=option.premium  # Use current premium as limit
                                            )

                                            if trade:
                                                st.success(f"✅ Trade executed successfully!")
                                                st.session_state[f'confirm_sell_{i}'] = False
                                                st.rerun()
                                            else:
                                                st.error("❌ Trade failed. Check logs or read-only mode.")

                                    except Exception as e:
                                        st.error(f"❌ Error: {str(e)}")

                            with col_confirm2:
                                if st.button("❌ Cancel", key=f"cancel_{i}"):
                                    st.session_state[f'confirm_sell_{i}'] = False
                                    st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")


def performance_charts():
    """Display performance charts and analytics"""
    st.header("📈 Performance Analytics")

    portfolio = st.session_state.portfolio

    if not portfolio.positions and not portfolio.closed_positions:
        st.info("No data available for charts")
        return

    # Create tabs for different charts
    tab1, tab2, tab3, tab4 = st.tabs(["Returns Distribution", "Greeks Exposure", "Expiration Timeline", "🛡️ Risk Management"])

    with tab1:
        # Returns distribution
        if portfolio.positions:
            returns_data = [
                {
                    'Symbol': pos.stock.symbol,
                    'Return if Assigned': pos.return_if_assigned,
                    'Annualized Return': pos.annualized_return
                }
                for pos in portfolio.positions
            ]
            df = pd.DataFrame(returns_data)

            fig = px.bar(
                df,
                x='Symbol',
                y=['Return if Assigned', 'Annualized Return'],
                title="Expected Returns by Position",
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Greeks exposure
        if portfolio.positions:
            greeks_data = {
                'Delta': portfolio.calculate_total_delta(),
                'Theta': portfolio.calculate_total_theta(),
            }

            fig = go.Figure(data=[
                go.Bar(
                    x=list(greeks_data.keys()),
                    y=list(greeks_data.values()),
                    marker_color=['blue', 'green']
                )
            ])
            fig.update_layout(title="Portfolio Greeks Exposure")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Expiration timeline
        if portfolio.positions:
            timeline_data = [
                {
                    'Symbol': pos.stock.symbol,
                    'Expiration': pos.option.expiration,
                    'DTE': pos.option.days_to_expiration,
                    'Premium': pos.net_premium
                }
                for pos in portfolio.positions
            ]
            df = pd.DataFrame(timeline_data)

            fig = px.scatter(
                df,
                x='Expiration',
                y='Premium',
                size='DTE',
                color='Symbol',
                title="Expiration Timeline",
                hover_data=['DTE']
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        # Risk Management Dashboard
        try:
            # Initialize Risk Manager
            risk_manager = RiskManager(
                max_position_pct=0.25,
                max_cc_pct=0.70,
                min_cash_reserve=0.10
            )

            # Convert portfolio positions to risk manager format
            positions_for_risk = []
            for pos in portfolio.positions:
                positions_for_risk.append({
                    'symbol': pos.stock.symbol,
                    'quantity': pos.stock.quantity,
                    'price': pos.stock.current_price,
                    'has_covered_call': True,
                    'option_delta': pos.option.delta if hasattr(pos.option, 'delta') else 0.5,
                    'days_to_expiry': pos.option.days_to_expiration
                })

            # Calculate account value and cash
            account_value = sum(pos.stock.quantity * pos.stock.current_price for pos in portfolio.positions)
            cash_balance = account_value * 0.15  # Placeholder - should come from IBKR

            # Analyze portfolio
            risk_analysis = risk_manager.analyze_portfolio(
                account_value=account_value,
                cash_balance=cash_balance,
                positions=positions_for_risk
            )

            # Render risk dashboard
            render_risk_dashboard(risk_analysis)

            st.markdown("---")

            # Position validator tool
            render_position_validator(
                risk_manager=risk_manager,
                account_value=account_value,
                existing_positions=positions_for_risk
            )

        except Exception as e:
            st.error(f"Error loading risk management: {str(e)}")
            st.info("Risk management features require active portfolio positions")


def backtesting_tab():
    """Historical backtesting of covered calls strategies"""
    st.header("📊 Strategy Backtesting")

    st.markdown("""
    Test different covered calls strategies on historical data to see what would have worked best.
    """)

    # Get available stocks
    if not st.session_state.connected:
        st.warning("⚠️ Connect to IBKR or upload CSV to see your positions")
        return

    ibkr = st.session_state.ibkr
    stocks = ibkr.get_stock_positions()

    if not stocks:
        st.info("No stock positions found")
        return

    # Extract symbols
    stock_symbols = []
    for stock in stocks:
        if isinstance(stock, dict):
            stock_symbols.append(stock['symbol'])
        else:
            stock_symbols.append(stock.symbol)

    # Backtester settings
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_symbol = st.selectbox("📈 Symbol", options=stock_symbols)

    with col2:
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime('2024-04-01'),
            max_value=datetime.now().date()
        )

    with col3:
        end_date = st.date_input(
            "End Date",
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )

    # Get quantity for selected symbol
    selected_stock = None
    for s in stocks:
        symbol = s['symbol'] if isinstance(s, dict) else s.symbol
        if symbol == selected_symbol:
            selected_stock = s
            break

    if selected_stock:
        quantity = selected_stock['quantity'] if isinstance(selected_stock, dict) else selected_stock.quantity
        st.info(f"📊 Your position: {int(quantity)} shares of {selected_symbol}")
    else:
        quantity = 100

    # Run backtest button
    if st.button("🚀 Run Backtest", type="primary"):
        try:
            with st.spinner(f"Running backtest on {selected_symbol}..."):
                # Create backtester
                backtester = CoveredCallBacktester(
                    symbol=selected_symbol,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    quantity=int(quantity)
                )

                # Compare strategies
                comparison = backtester.compare_strategies()

                st.success("✅ Backtest Complete!")

                # Display results table
                st.subheader("📊 Strategy Comparison")
                st.dataframe(comparison, use_container_width=True)

                # Create visualization
                st.subheader("📈 Returns Comparison")

                # Extract numeric values for plotting
                comparison_plot = comparison.copy()
                comparison_plot['Total Return $'] = comparison['Total Return'].str.replace('$', '').str.replace(',', '').astype(float)
                comparison_plot['Annualized %'] = comparison['Annualized %'].str.replace('%', '').astype(float)

                col1, col2 = st.columns(2)

                with col1:
                    fig1 = px.bar(
                        comparison_plot,
                        x='Strategy',
                        y='Total Return $',
                        title="Total Return by Strategy",
                        labels={'Total Return $': 'Total Return ($)'}
                    )
                    fig1.update_xaxes(tickangle=-45)
                    st.plotly_chart(fig1, use_container_width=True)

                with col2:
                    fig2 = px.bar(
                        comparison_plot,
                        x='Strategy',
                        y='Annualized %',
                        title="Annualized Return by Strategy",
                        labels={'Annualized %': 'Annualized Return (%)'},
                        color='Annualized %',
                        color_continuous_scale='RdYlGn'
                    )
                    fig2.update_xaxes(tickangle=-45)
                    st.plotly_chart(fig2, use_container_width=True)

                # Insights
                st.subheader("💡 Key Insights")

                # Best performing strategy
                best_idx = comparison_plot['Total Return $'].idxmax()
                best_strategy = comparison.iloc[best_idx]

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "🏆 Best Strategy",
                        best_strategy['Strategy'].split('(')[0].strip(),
                        delta=best_strategy['Total Return']
                    )

                with col2:
                    st.metric(
                        "📊 Annualized Return",
                        best_strategy['Annualized %']
                    )

                with col3:
                    st.metric(
                        "✅ Win Rate",
                        best_strategy['Win Rate']
                    )

                # Export option
                csv = comparison.to_csv(index=False)
                st.download_button(
                    label="💾 Download Results (CSV)",
                    data=csv,
                    file_name=f"backtest_{selected_symbol}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"❌ Error running backtest: {str(e)}")
            import traceback
            st.code(traceback.format_exc())


def main():
    """Main dashboard function"""
    # Initialize state
    DashboardState()

    # Sidebar
    sidebar_config()

    # Main content
    st.title("📈 Covered Calls Management Dashboard")

    # Create tabs for organized navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🔍 Strategy Finder",
        "📈 Active Positions",
        "📉 Backtesting",
        "⚙️ Analytics"
    ])

    with tab1:
        # Overview Tab - Account summary and portfolio
        st.header("Portfolio Overview")
        account_overview()
        st.markdown("---")
        portfolio_summary()
        st.markdown("---")
        alerts_panel()
        st.markdown("---")
        positions_table()

    with tab2:
        # Strategy Finder Tab
        strategy_finder()

    with tab3:
        # Active Positions Tab
        active_positions_table()
        st.markdown("---")
        expiration_calendar()

    with tab4:
        # Backtesting Tab
        backtesting_tab()

    with tab5:
        # Analytics Tab - Trade Performance & Database Analytics
        st.header("📊 Trade Analytics & Performance")

        # Add the full analytics dashboard from trade_analytics.py
        add_analytics_to_dashboard()

        st.markdown("---")

        # Original performance charts (portfolio-level)
        st.subheader("📈 Portfolio Performance Charts")
        performance_charts()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p>Covered Calls Manager v1.0 | Built with Streamlit</p>
        <p><em>⚠️ For educational purposes only. Not financial advice.</em></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
