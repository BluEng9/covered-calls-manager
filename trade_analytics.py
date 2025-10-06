#!/usr/bin/env python3
"""
📊 Trade History & Analytics Module
מערכת מסד נתונים וניתוח ביצועים למסחר
Phase 3 Implementation
"""

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ==================== Database Schema ====================

SCHEMA_SQL = """
-- Main trades table
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Trade details
    symbol VARCHAR(10) NOT NULL,
    trade_type VARCHAR(20) DEFAULT 'COVERED_CALL',
    action VARCHAR(10) NOT NULL,  -- SELL, BUY
    quantity INTEGER NOT NULL,
    strike DECIMAL(10,2),
    expiration DATE,
    
    -- Financials
    premium_received DECIMAL(10,2),
    commission DECIMAL(10,2) DEFAULT 0,
    total_credit DECIMAL(10,2),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'OPEN',  -- OPEN, CLOSED, ASSIGNED, EXPIRED, ROLLED
    close_date DATETIME,
    close_price DECIMAL(10,2),
    profit_loss DECIMAL(10,2),
    
    -- Greeks at entry
    entry_delta DECIMAL(5,4),
    entry_gamma DECIMAL(5,4),
    entry_theta DECIMAL(10,2),
    entry_vega DECIMAL(10,2),
    entry_iv DECIMAL(5,4),
    
    -- Strategy metadata
    risk_level VARCHAR(20),
    dte_at_open INTEGER,
    percent_otm DECIMAL(5,2),
    stock_price_at_open DECIMAL(10,2),
    annualized_return DECIMAL(5,2),
    
    -- Trading mode
    trading_mode VARCHAR(20) DEFAULT 'PAPER',  -- DEMO, PAPER, LIVE
    
    -- Links
    account_id VARCHAR(50),
    roll_from_id INTEGER,  -- If rolled from another position
    
    -- Notes
    notes TEXT,
    
    FOREIGN KEY (roll_from_id) REFERENCES trades(id)
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS daily_performance (
    date DATE PRIMARY KEY,
    
    -- Daily metrics
    trades_opened INTEGER DEFAULT 0,
    trades_closed INTEGER DEFAULT 0,
    premium_collected DECIMAL(12,2) DEFAULT 0,
    realized_pnl DECIMAL(12,2) DEFAULT 0,
    
    -- Cumulative metrics
    total_open_positions INTEGER DEFAULT 0,
    total_premium_collected DECIMAL(12,2) DEFAULT 0,
    total_realized_pnl DECIMAL(12,2) DEFAULT 0,
    
    -- Win rate
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    expired_worthless INTEGER DEFAULT 0,
    assigned_trades INTEGER DEFAULT 0,
    
    -- Risk metrics
    max_drawdown DECIMAL(10,2),
    portfolio_delta DECIMAL(10,4),
    portfolio_theta DECIMAL(12,2),
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_expiration ON trades(expiration);
CREATE INDEX IF NOT EXISTS idx_timestamp ON trades(timestamp);
"""

# ==================== Database Manager ====================

class TradeDatabase:
    """SQLite database manager for trade history"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path.home() / "Projects" / "TradingBots" / "covered-calls-manager" / "trades.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database with schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
    
    def record_trade(self, trade_data: Dict) -> int:
        """Record a new trade and return its ID"""
        
        # Prepare trade data
        columns = [
            'symbol', 'trade_type', 'action', 'quantity', 'strike', 'expiration',
            'premium_received', 'commission', 'total_credit', 'status',
            'entry_delta', 'entry_gamma', 'entry_theta', 'entry_vega', 'entry_iv',
            'risk_level', 'dte_at_open', 'percent_otm', 'stock_price_at_open',
            'annualized_return', 'trading_mode', 'account_id', 'notes'
        ]
        
        # Filter only existing keys
        filtered_data = {k: v for k, v in trade_data.items() if k in columns}
        
        # Build SQL
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?' for _ in filtered_data])
        sql = f"INSERT INTO trades ({cols}) VALUES ({placeholders})"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, list(filtered_data.values()))
            trade_id = cursor.lastrowid
            
            # Update daily performance
            self._update_daily_performance(conn, trade_data.get('symbol'))
            
            conn.commit()
            return trade_id
    
    def update_trade_status(
        self, 
        trade_id: int, 
        status: str, 
        close_price: float = None, 
        profit_loss: float = None
    ):
        """Update trade when closed/expired/assigned"""
        
        sql = """
        UPDATE trades 
        SET status = ?, 
            close_date = ?,
            close_price = ?,
            profit_loss = ?
        WHERE id = ?
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, [
                status, 
                datetime.now().isoformat(),
                close_price,
                profit_loss,
                trade_id
            ])
            
            # Update daily performance
            self._update_daily_performance(conn)
            conn.commit()
    
    def get_open_positions(self) -> pd.DataFrame:
        """Get all open covered call positions"""
        
        sql = """
        SELECT * FROM trades 
        WHERE status = 'OPEN' 
        ORDER BY expiration ASC
        """
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(sql, conn)
            return df
    
    def get_trade_history(
        self, 
        symbol: str = None, 
        days: int = 30,
        status: str = None
    ) -> pd.DataFrame:
        """Get historical trades with filters"""
        
        conditions = ["timestamp > datetime('now', ?"]
        params = [f'-{days} days']
        
        if symbol:
            conditions.append("symbol = ?")
            params.append(symbol)
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        # Fix SQL syntax
        where_clause = " AND ".join(conditions)
        where_clause = where_clause.replace("datetime('now', ?", "datetime('now', ?)")
        
        sql = f"""
        SELECT * FROM trades 
        WHERE {where_clause}
        ORDER BY timestamp DESC
        """
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(sql, conn, params=params)
            return df
    
    def get_performance_summary(self, days: int = 30) -> Dict:
        """Get comprehensive performance metrics"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Get recent trades
            trades_sql = f"""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_trades,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(premium_received) as total_premium,
                SUM(profit_loss) as total_pnl,
                AVG(profit_loss) as avg_pnl,
                AVG(annualized_return) as avg_annual_return
            FROM trades
            WHERE timestamp > datetime('now', '-{days} days')
            """
            
            cursor = conn.cursor()
            result = cursor.execute(trades_sql).fetchone()
            
            # Calculate win rate
            total_closed = (result[2] or 0) + (result[3] or 0)
            win_rate = (result[2] / total_closed * 100) if total_closed > 0 else 0
            
            return {
                'total_trades': result[0] or 0,
                'open_trades': result[1] or 0,
                'winning_trades': result[2] or 0,
                'losing_trades': result[3] or 0,
                'win_rate': round(win_rate, 1),
                'total_premium': result[4] or 0,
                'total_pnl': result[5] or 0,
                'avg_pnl': result[6] or 0,
                'avg_annual_return': result[7] or 0
            }
    
    def _update_daily_performance(self, conn, symbol: str = None):
        """Update daily performance metrics"""
        
        today = datetime.now().date()
        
        # Calculate today's metrics
        sql = """
        INSERT OR REPLACE INTO daily_performance (date, trades_opened, premium_collected)
        SELECT 
            DATE('now') as date,
            COUNT(*) as trades_opened,
            SUM(premium_received) as premium_collected
        FROM trades
        WHERE DATE(timestamp) = DATE('now')
        """
        
        conn.execute(sql)

# ==================== Performance Analytics ====================

class PerformanceAnalyzer:
    """Analyze trading performance and generate insights"""
    
    def __init__(self, db: TradeDatabase):
        self.db = db
    
    def calculate_returns(self, start_date=None, end_date=None) -> pd.DataFrame:
        """Calculate period returns with various metrics"""
        
        # Get trades
        trades_df = self.db.get_trade_history(days=365)
        
        if trades_df.empty:
            return pd.DataFrame()
        
        # Filter by dates if provided
        if start_date:
            trades_df = trades_df[trades_df['timestamp'] >= start_date]
        if end_date:
            trades_df = trades_df[trades_df['timestamp'] <= end_date]
        
        # Calculate daily returns
        daily_returns = trades_df.groupby(pd.to_datetime(trades_df['timestamp']).dt.date).agg({
            'premium_received': 'sum',
            'profit_loss': 'sum'
        }).fillna(0)
        
        # Calculate cumulative returns
        daily_returns['cumulative_premium'] = daily_returns['premium_received'].cumsum()
        daily_returns['cumulative_pnl'] = daily_returns['profit_loss'].cumsum()
        
        return daily_returns
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio of the strategy"""
        
        returns_df = self.calculate_returns()
        
        if returns_df.empty:
            return 0
        
        # Calculate daily returns percentage
        returns_df['daily_return_pct'] = returns_df['profit_loss'].pct_change()
        
        # Calculate Sharpe
        excess_returns = returns_df['daily_return_pct'] - (risk_free_rate / 252)
        sharpe = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
        
        return round(sharpe, 2) if not np.isnan(sharpe) else 0
    
    def calculate_max_drawdown(self) -> Tuple[float, str, str]:
        """Calculate maximum drawdown and dates"""
        
        returns_df = self.calculate_returns()
        
        if returns_df.empty:
            return 0, None, None
        
        # Calculate running maximum
        cumulative = returns_df['cumulative_pnl']
        running_max = cumulative.expanding().max()
        
        # Calculate drawdown
        drawdown = (cumulative - running_max) / running_max
        
        # Find max drawdown
        max_dd = drawdown.min()
        max_dd_date = drawdown.idxmin()
        
        # Find recovery date (if any)
        recovery_date = None
        if max_dd_date in cumulative.index:
            peak_value = running_max[max_dd_date]
            future_values = cumulative[cumulative.index > max_dd_date]
            recovery_mask = future_values >= peak_value
            if recovery_mask.any():
                recovery_date = recovery_mask.idxmax()
        
        return round(max_dd * 100, 2), max_dd_date, recovery_date
    
    def analyze_by_strategy(self) -> pd.DataFrame:
        """Analyze performance by risk level/strategy"""
        
        trades_df = self.db.get_trade_history(days=365)
        
        if trades_df.empty:
            return pd.DataFrame()
        
        # Group by risk level
        strategy_stats = trades_df.groupby('risk_level').agg({
            'id': 'count',
            'profit_loss': ['sum', 'mean'],
            'premium_received': 'sum',
            'annualized_return': 'mean'
        })
        
        strategy_stats.columns = ['trades', 'total_pnl', 'avg_pnl', 'total_premium', 'avg_annual_return']
        
        # Calculate win rate per strategy
        for risk_level in strategy_stats.index:
            level_trades = trades_df[trades_df['risk_level'] == risk_level]
            wins = (level_trades['profit_loss'] > 0).sum()
            total = len(level_trades)
            strategy_stats.loc[risk_level, 'win_rate'] = (wins / total * 100) if total > 0 else 0
        
        return strategy_stats.round(2)
    
    def get_best_worst_trades(self, n: int = 5) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get best and worst performing trades"""
        
        trades_df = self.db.get_trade_history(days=365)
        
        if trades_df.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Filter closed trades only
        closed_trades = trades_df[trades_df['status'].isin(['CLOSED', 'EXPIRED', 'ASSIGNED'])]
        
        if closed_trades.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Best trades
        best = closed_trades.nlargest(n, 'profit_loss')[
            ['symbol', 'strike', 'expiration', 'profit_loss', 'annualized_return', 'status']
        ]
        
        # Worst trades
        worst = closed_trades.nsmallest(n, 'profit_loss')[
            ['symbol', 'strike', 'expiration', 'profit_loss', 'annualized_return', 'status']
        ]
        
        return best, worst

# ==================== Visualization ====================

class TradeCharts:
    """Create visualizations for trade analytics"""
    
    @staticmethod
    def create_pnl_curve(returns_df: pd.DataFrame) -> go.Figure:
        """Create cumulative P&L curve"""
        
        fig = go.Figure()
        
        # Add P&L line
        fig.add_trace(go.Scatter(
            x=returns_df.index,
            y=returns_df['cumulative_pnl'],
            mode='lines',
            name='Cumulative P&L',
            line=dict(color='green', width=2)
        ))
        
        # Add premium collected
        fig.add_trace(go.Scatter(
            x=returns_df.index,
            y=returns_df['cumulative_premium'],
            mode='lines',
            name='Premium Collected',
            line=dict(color='blue', width=2, dash='dash')
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        fig.update_layout(
            title="P&L Performance Over Time",
            xaxis_title="Date",
            yaxis_title="USD ($)",
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_win_rate_chart(performance_summary: Dict) -> go.Figure:
        """Create win rate donut chart"""
        
        labels = ['Winning', 'Losing', 'Open']
        values = [
            performance_summary['winning_trades'],
            performance_summary['losing_trades'],
            performance_summary['open_trades']
        ]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=['green', 'red', 'gray']
        )])
        
        fig.update_layout(
            title="Trade Outcomes",
            annotations=[dict(
                text=f"{performance_summary['win_rate']:.0f}%",
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )],
            height=300
        )
        
        return fig
    
    @staticmethod
    def create_monthly_returns_heatmap(trades_df: pd.DataFrame) -> go.Figure:
        """Create monthly returns heatmap"""
        
        if trades_df.empty:
            return go.Figure()
        
        # Convert to monthly returns
        trades_df['month'] = pd.to_datetime(trades_df['timestamp']).dt.to_period('M')
        monthly = trades_df.groupby('month')['profit_loss'].sum().reset_index()
        monthly['month_str'] = monthly['month'].astype(str)
        
        # Pivot for heatmap
        monthly['year'] = pd.to_datetime(monthly['month_str']).dt.year
        monthly['month_num'] = pd.to_datetime(monthly['month_str']).dt.month
        
        pivot = monthly.pivot(index='month_num', columns='year', values='profit_loss').fillna(0)
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][:len(pivot.index)],
            colorscale='RdYlGn',
            zmid=0
        ))
        
        fig.update_layout(
            title="Monthly Returns Heatmap",
            xaxis_title="Year",
            yaxis_title="Month",
            height=400
        )
        
        return fig

# ==================== Streamlit Dashboard Integration ====================

def add_analytics_to_dashboard():
    """Add analytics tab to main dashboard"""
    
    st.markdown("## 📊 Trade History & Analytics")
    
    # Initialize database
    db = TradeDatabase()
    analyzer = PerformanceAnalyzer(db)
    
    # Performance summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    summary = db.get_performance_summary(days=30)
    
    with col1:
        st.metric(
            "Total Trades",
            summary['total_trades'],
            delta=f"{summary['open_trades']} open"
        )
    
    with col2:
        st.metric(
            "Win Rate",
            f"{summary['win_rate']:.0f}%",
            delta=f"{summary['winning_trades']}W/{summary['losing_trades']}L"
        )
    
    with col3:
        st.metric(
            "Total P&L",
            f"${summary['total_pnl']:,.0f}",
            delta=f"Avg: ${summary['avg_pnl']:.0f}"
        )
    
    with col4:
        st.metric(
            "Premium Collected",
            f"${summary['total_premium']:,.0f}",
            delta=f"{summary['avg_annual_return']:.1f}% annual"
        )
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Performance", "📜 Trade History", "📊 Analytics", "📋 Reports"
    ])
    
    with tab1:
        st.markdown("### Performance Charts")
        
        # P&L curve
        returns_df = analyzer.calculate_returns()
        if not returns_df.empty:
            fig_pnl = TradeCharts.create_pnl_curve(returns_df)
            st.plotly_chart(fig_pnl, use_container_width=True)
        
        # Win rate donut
        col1, col2 = st.columns(2)
        with col1:
            fig_winrate = TradeCharts.create_win_rate_chart(summary)
            st.plotly_chart(fig_winrate, use_container_width=True)
        
        with col2:
            # Sharpe ratio and max drawdown
            sharpe = analyzer.calculate_sharpe_ratio()
            max_dd, dd_date, recovery = analyzer.calculate_max_drawdown()
            
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")
            st.metric("Max Drawdown", f"{max_dd:.1f}%")
            if dd_date:
                st.caption(f"Occurred on {dd_date}")
    
    with tab2:
        st.markdown("### Trade History")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_symbol = st.text_input("Symbol Filter", "")
        with col2:
            filter_days = st.slider("Days Back", 7, 365, 30)
        with col3:
            filter_status = st.selectbox(
                "Status",
                ["All", "OPEN", "CLOSED", "EXPIRED", "ASSIGNED"]
            )
        
        # Get filtered trades
        status_filter = None if filter_status == "All" else filter_status
        trades_df = db.get_trade_history(
            symbol=filter_symbol if filter_symbol else None,
            days=filter_days,
            status=status_filter
        )
        
        if not trades_df.empty:
            # Format for display
            display_df = trades_df[[
                'timestamp', 'symbol', 'strike', 'expiration', 
                'premium_received', 'status', 'profit_loss'
            ]].copy()
            
            display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No trades found for selected filters")
    
    with tab3:
        st.markdown("### Strategy Analytics")
        
        # Strategy performance comparison
        strategy_stats = analyzer.analyze_by_strategy()
        if not strategy_stats.empty:
            st.dataframe(strategy_stats, use_container_width=True)
        
        # Best and worst trades
        col1, col2 = st.columns(2)
        
        best, worst = analyzer.get_best_worst_trades(5)
        
        with col1:
            st.markdown("#### 🏆 Best Trades")
            if not best.empty:
                st.dataframe(best, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### 📉 Worst Trades")
            if not worst.empty:
                st.dataframe(worst, use_container_width=True, hide_index=True)
        
        # Monthly returns heatmap
        if not trades_df.empty:
            fig_heatmap = TradeCharts.create_monthly_returns_heatmap(trades_df)
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with tab4:
        st.markdown("### Generate Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generate Monthly Report"):
                st.info("Report generation coming soon...")
        
        with col2:
            if st.button("💾 Export to CSV"):
                trades_df = db.get_trade_history(days=365)
                csv = trades_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

# ==================== Test Functions ====================

def test_database():
    """Test database functionality"""
    
    print("🧪 Testing Trade Database...")
    
    # Initialize
    db = TradeDatabase("test_trades.db")
    
    # Test trade
    test_trade = {
        'symbol': 'AAPL',
        'action': 'SELL',
        'quantity': 1,
        'strike': 150.0,
        'expiration': '2024-01-19',
        'premium_received': 250.0,
        'total_credit': 250.0,
        'entry_delta': 0.25,
        'entry_theta': -5.0,
        'dte_at_open': 30,
        'percent_otm': 3.5,
        'stock_price_at_open': 145.0,
        'annualized_return': 25.5,
        'trading_mode': 'PAPER'
    }
    
    # Record trade
    trade_id = db.record_trade(test_trade)
    print(f"✅ Trade recorded with ID: {trade_id}")
    
    # Get open positions
    open_pos = db.get_open_positions()
    print(f"✅ Open positions: {len(open_pos)}")
    
    # Get performance
    perf = db.get_performance_summary()
    print(f"✅ Performance summary: {perf}")
    
    # Clean up
    Path("test_trades.db").unlink(missing_ok=True)
    
    print("✅ All database tests passed!")

if __name__ == "__main__":
    # Run tests
    test_database()

    # If running as streamlit
    try:
        # Check if running in streamlit by looking for runtime
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is not None:
            st.set_page_config(page_title="Trade Analytics", layout="wide")
            add_analytics_to_dashboard()
        else:
            print("\n📊 Trade Analytics Module Ready!")
    except:
        print("\n📊 Trade Analytics Module Ready!")
        print("Add to dashboard with: add_analytics_to_dashboard()")
