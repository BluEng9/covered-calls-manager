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
from risk_manager import RiskManager


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


def sidebar_config():
    """Sidebar configuration and connection settings"""
    st.sidebar.title("🎯 Covered Calls Manager")
    st.sidebar.markdown("---")

    st.sidebar.subheader("IBKR Connection")

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
            st.sidebar.info("Disconnected")
            st.rerun()

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

    # Select stock
    selected_symbol = st.selectbox(
        "Select Stock",
        options=[stock.symbol for stock in stocks]
    )

    selected_stock = next((s for s in stocks if s.symbol == selected_symbol), None)

    if not selected_stock:
        return

    # Display stock info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${selected_stock.current_price:.2f}")
    with col2:
        st.metric("Quantity", selected_stock.quantity)
    with col3:
        st.metric("Avg Cost", f"${selected_stock.avg_cost:.2f}")
    with col4:
        pnl_color = "profit-positive" if selected_stock.unrealized_pnl >= 0 else "profit-negative"
        st.markdown(
            f"<div class='{pnl_color}'>P&L: ${selected_stock.unrealized_pnl:.2f} "
            f"({selected_stock.unrealized_pnl_pct:.2f}%)</div>",
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
                # Get OTM calls
                options = ibkr.get_otm_calls(
                    selected_symbol,
                    selected_stock.current_price,
                    days_to_expiration=target_dte
                )

                if not options:
                    st.warning("No suitable options found")
                    return

                # Score options
                strategy = CoveredCallStrategy(st.session_state.risk_level)
                scored_options = strategy.find_best_strike(
                    options,
                    selected_stock.current_price,
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

                        # Action button
                        if st.button(f"📝 Create Position #{i}", key=f"create_{i}"):
                            st.info("Position creation feature coming soon!")

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


def main():
    """Main dashboard function"""
    # Initialize state
    DashboardState()

    # Sidebar
    sidebar_config()

    # Main content
    st.title("📈 Covered Calls Management Dashboard")

    # Account overview
    account_overview()

    st.markdown("---")

    # Portfolio summary
    portfolio_summary()

    st.markdown("---")

    # Alerts
    alerts_panel()

    st.markdown("---")

    # Positions table
    positions_table()

    st.markdown("---")

    # Expiration calendar
    col1, col2 = st.columns([1, 1])

    with col1:
        expiration_calendar()

    with col2:
        # Strategy finder
        strategy_finder()

    st.markdown("---")

    # Performance charts
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
