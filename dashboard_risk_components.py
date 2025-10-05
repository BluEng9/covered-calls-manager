"""
Risk Management UI Components for Streamlit Dashboard
======================================================
קומפוננטים לממשק ניהול סיכונים

Author: Alon Platt Chance
Date: 2025-10-05
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from risk_manager import RiskManager, RiskLevel, format_risk_report
from typing import Dict, List
import pandas as pd


def render_risk_dashboard(risk_analysis: Dict):
    """רנדור לוח בקרת סיכונים מלא"""
    
    st.markdown("## 🛡️ ניהול סיכונים")
    
    # Overall Risk Level - גדול ובולט
    _render_overall_risk(risk_analysis['overall_risk'])
    
    st.markdown("---")
    
    # 4 מדדים מרכזיים
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        _render_concentration_card(risk_analysis['concentration'])
    
    with col2:
        _render_cash_reserve_card(risk_analysis['cash_reserve'])
    
    with col3:
        _render_cc_exposure_card(risk_analysis['cc_exposure'])
    
    with col4:
        _render_assignment_risk_card(risk_analysis['assignment_risk'])
    
    st.markdown("---")
    
    # Alerts
    if risk_analysis['alerts']:
        _render_alerts_panel(risk_analysis['alerts'])
        st.markdown("---")
    
    # Recommendations
    _render_recommendations(risk_analysis['recommendations'])
    
    # Detailed Analysis - Expandable
    with st.expander("📊 ניתוח מפורט", expanded=False):
        _render_detailed_analysis(risk_analysis)


def _render_overall_risk(risk_level: RiskLevel):
    """כרטיס רמת סיכון כללית - גדול ובולט"""
    
    colors = {
        RiskLevel.LOW: "#28a745",
        RiskLevel.MEDIUM: "#ffc107",
        RiskLevel.HIGH: "#fd7e14",
        RiskLevel.CRITICAL: "#dc3545"
    }
    
    emojis = {
        RiskLevel.LOW: "🟢",
        RiskLevel.MEDIUM: "🟡",
        RiskLevel.HIGH: "🟠",
        RiskLevel.CRITICAL: "🔴"
    }
    
    color = colors.get(risk_level, "#6c757d")
    emoji = emojis.get(risk_level, "⚪")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}22 0%, {color}11 100%);
        border-right: 5px solid {color};
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
    ">
        <h1 style="margin: 0; color: {color}; font-size: 3em;">
            {emoji}
        </h1>
        <h2 style="margin: 10px 0; color: {color};">
            רמת סיכון: {risk_level.value}
        </h2>
    </div>
    """, unsafe_allow_html=True)


def _render_concentration_card(concentration: Dict):
    """כרטיס ריכוזיות תיק"""
    
    status = concentration.get('status', 'OK')
    largest = concentration.get('largest_position', 'N/A')
    pct = concentration.get('largest_pct', 0)
    
    color = "#dc3545" if status == "WARNING" else "#28a745"
    
    st.markdown(f"""
    <div style="
        background: {color}11;
        border: 2px solid {color};
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    ">
        <h3 style="margin: 0;">🎯 ריכוזיות</h3>
        <h2 style="color: {color}; margin: 10px 0;">{pct:.1f}%</h2>
        <p style="margin: 0; font-size: 0.9em;">{largest}</p>
    </div>
    """, unsafe_allow_html=True)


def _render_cash_reserve_card(cash_reserve: Dict):
    """כרטיס רזרבת מזומן"""
    
    status = cash_reserve.get('status', 'OK')
    pct = cash_reserve.get('cash_pct', 0)
    required = cash_reserve.get('required_pct', 10)
    
    color = "#dc3545" if status == "LOW" else "#28a745"
    
    st.markdown(f"""
    <div style="
        background: {color}11;
        border: 2px solid {color};
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    ">
        <h3 style="margin: 0;">💰 מזומן</h3>
        <h2 style="color: {color}; margin: 10px 0;">{pct:.1f}%</h2>
        <p style="margin: 0; font-size: 0.9em;">נדרש: {required:.0f}%</p>
    </div>
    """, unsafe_allow_html=True)


def _render_cc_exposure_card(cc_exposure: Dict):
    """כרטיס חשיפת Covered Calls"""
    
    status = cc_exposure.get('status', 'OK')
    pct = cc_exposure.get('exposure_pct', 0)
    num_positions = cc_exposure.get('num_positions', 0)
    
    color_map = {
        'OK': '#28a745',
        'MEDIUM': '#ffc107',
        'HIGH': '#dc3545'
    }
    color = color_map.get(status, '#6c757d')
    
    st.markdown(f"""
    <div style="
        background: {color}11;
        border: 2px solid {color};
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    ">
        <h3 style="margin: 0;">📊 חשיפת CC</h3>
        <h2 style="color: {color}; margin: 10px 0;">{pct:.1f}%</h2>
        <p style="margin: 0; font-size: 0.9em;">{num_positions} פוזיציות</p>
    </div>
    """, unsafe_allow_html=True)


def _render_assignment_risk_card(assignment_risk: Dict):
    """כרטיס סיכון הקצאה"""
    
    high_risk = assignment_risk.get('high_risk_count', 0)
    
    color = "#dc3545" if high_risk > 0 else "#28a745"
    
    st.markdown(f"""
    <div style="
        background: {color}11;
        border: 2px solid {color};
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    ">
        <h3 style="margin: 0;">⚠️ סיכון הקצאה</h3>
        <h2 style="color: {color}; margin: 10px 0;">{high_risk}</h2>
        <p style="margin: 0; font-size: 0.9em;">פוזיציות בסיכון</p>
    </div>
    """, unsafe_allow_html=True)


def _render_alerts_panel(alerts: List):
    """פאנל התראות"""
    
    st.markdown("### ⚠️ התראות")
    
    for alert in alerts:
        color_map = {
            RiskLevel.LOW: "info",
            RiskLevel.MEDIUM: "warning",
            RiskLevel.HIGH: "error",
            RiskLevel.CRITICAL: "error"
        }
        
        alert_type = color_map.get(alert.level, "info")
        
        with st.container():
            if alert_type == "error":
                st.error(f"**{alert.title}**\n\n{alert.message}")
            elif alert_type == "warning":
                st.warning(f"**{alert.title}**\n\n{alert.message}")
            else:
                st.info(f"**{alert.title}**\n\n{alert.message}")


def _render_recommendations(recommendations: List[str]):
    """פאנל המלצות"""
    
    st.markdown("### 💡 המלצות")
    
    if not recommendations:
        st.success("✅ אין המלצות מיוחדות - התיק נראה מאוזן!")
        return
    
    for rec in recommendations:
        st.markdown(f"- {rec}")


def _render_detailed_analysis(risk_analysis: Dict):
    """ניתוח מפורט"""
    
    # טבלת ריכוזיות
    if 'positions_breakdown' in risk_analysis['concentration']:
        st.markdown("#### התפלגות פוזיציות")
        
        breakdown = risk_analysis['concentration']['positions_breakdown']
        df = pd.DataFrame([
            {'סימול': symbol, 'ערך ($)': f"${value:,.0f}"}
            for symbol, value in breakdown.items()
        ])
        
        st.dataframe(df, use_container_width=True)
    
    # גרף ריכוזיות
    if 'positions_breakdown' in risk_analysis['concentration']:
        breakdown = risk_analysis['concentration']['positions_breakdown']
        
        fig = go.Figure(data=[go.Pie(
            labels=list(breakdown.keys()),
            values=list(breakdown.values()),
            hole=0.3
        )])
        
        fig.update_layout(
            title="התפלגות תיק",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_position_validator(risk_manager: RiskManager,
                             account_value: float,
                             existing_positions: List[Dict]):
    """כלי לבדיקת פוזיציה חדשה לפני פתיחה"""
    
    st.markdown("### 🔍 בדיקת פוזיציה חדשה")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbol = st.text_input("סימול מניה", value="AAPL")
    
    with col2:
        current_price = st.number_input("מחיר נוכחי", value=180.0, step=1.0)
    
    with col3:
        contracts = st.number_input("מספר חוזים", value=1, min_value=1, step=1)
    
    strike = st.number_input("Strike", value=185.0, step=1.0)
    
    if st.button("🔍 בדוק פוזיציה", type="primary"):
        approved, reason = risk_manager.validate_new_position(
            symbol=symbol,
            contracts=contracts,
            strike=strike,
            current_price=current_price,
            account_value=account_value,
            existing_positions=existing_positions
        )
        
        if approved:
            st.success(reason)
            
            # חשב גודל פוזיציה מומלץ
            recommended = risk_manager.calculate_position_size(
                account_value=account_value,
                stock_price=current_price
            )
            
            st.info(f"💡 גודל פוזיציה מומלץ: {recommended} חוזים")
        else:
            st.error(reason)


