import streamlit as st
from risk_manager import RiskManager, RiskLevel
from dashboard_risk_components import render_risk_dashboard, render_position_validator

st.set_page_config(page_title="🛡️ Risk Management Demo", layout="wide")

# RTL Support
st.markdown("""
<style>
    .main { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ דמו - מערכת ניהול סיכונים")

# נתוני דמו
rm = RiskManager(
    max_position_pct=0.25,
    max_cc_pct=0.70,
    min_cash_reserve=0.10
)

positions = [
    {
        'symbol': 'TSLA',
        'quantity': 300,
        'price': 430.00,
        'has_covered_call': True,
        'option_delta': 0.68,
        'days_to_expiry': 12
    },
    {
        'symbol': 'AAPL', 
        'quantity': 500,
        'price': 180.00,
        'has_covered_call': True,
        'option_delta': 0.45,
        'days_to_expiry': 28
    },
    {
        'symbol': 'NVDA',
        'quantity': 200,
        'price': 450.00,
        'has_covered_call': False,
        'option_delta': 0,
        'days_to_expiry': 999
    }
]

account_value = 266296.0
cash_balance = 50000.0

# ניתוח
st.info("📊 מנתח תיק עם 3 פוזיציות...")

risk_analysis = rm.analyze_portfolio(
    account_value=account_value,
    cash_balance=cash_balance,
    positions=positions
)

# הצג
render_risk_dashboard(risk_analysis)

st.markdown("---")
st.markdown("## 🔍 בדיקת פוזיציה חדשה")

render_position_validator(
    risk_manager=rm,
    account_value=account_value,
    existing_positions=positions
)

st.markdown("---")
st.success("✅ המערכת פועלת תקין! עכשיו תוכל לראות את זה עם נתונים אמיתיים ב-Dashboard הראשי")
