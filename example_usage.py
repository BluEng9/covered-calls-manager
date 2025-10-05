#!/usr/bin/env python3
"""
📈 Covered Calls Manager - דוגמאות שימוש
Examples demonstrating how to use the system
"""

from datetime import datetime, timedelta
from covered_calls_system import (
    Stock, OptionContract, CoveredCall, OptionType,
    PositionStatus, RiskLevel, CoveredCallStrategy,
    PortfolioManager, RollStrategy, AlertSystem
)

print("="*70)
print("📈 Covered Calls Manager - דוגמאות שימוש")
print("="*70)
print()

# ═══════════════════════════════════════════════════════════════════
# דוגמה 1: יצירת פוזיציית Covered Call
# ═══════════════════════════════════════════════════════════════════
print("1️⃣  יצירת פוזיציית Covered Call על AAPL")
print("-" * 70)

# המניה שלך
my_stock = Stock(
    symbol="AAPL",
    quantity=200,  # 200 מניות = 2 חוזים
    avg_cost=180.0,
    current_price=185.0
)

print(f"מניה: {my_stock.symbol}")
print(f"כמות: {my_stock.quantity} מניות")
print(f"מחיר קנייה ממוצע: ${my_stock.avg_cost:.2f}")
print(f"מחיר נוכחי: ${my_stock.current_price:.2f}")
print(f"רווח לא ממומש: ${my_stock.unrealized_pnl:.2f} ({my_stock.unrealized_pnl_pct:.2f}%)")
print()

# אופציית ה-Call
call_option = OptionContract(
    symbol="AAPL",
    strike=190.0,  # Strike 190 (2.7% OTM)
    expiration=datetime.now() + timedelta(days=30),
    option_type=OptionType.CALL,
    premium=3.50,  # $3.50 פרמיה
    implied_volatility=25.0,
    delta=0.30,
    gamma=0.015,
    theta=-0.05,
    vega=0.12,
    volume=5000,
    open_interest=10000,
    bid=3.45,
    ask=3.55
)

print(f"אופציה: {call_option.symbol} Call")
print(f"Strike: ${call_option.strike:.2f}")
print(f"תפוגה: {call_option.expiration.strftime('%Y-%m-%d')} ({call_option.days_to_expiration} ימים)")
print(f"פרמיה: ${call_option.premium:.2f}")
print(f"Delta: {call_option.delta:.3f}")
print(f"IV: {call_option.implied_volatility:.1f}%")
print(f"נזילות: {'✅ גבוהה' if call_option.is_liquid else '❌ נמוכה'}")
print()

# יצירת הפוזיציה
position = CoveredCall(
    id="CC_AAPL_001",
    stock=my_stock,
    option=call_option,
    quantity=2,  # 2 חוזים = 200 מניות
    entry_date=datetime.now(),
    status=PositionStatus.OPEN,
    premium_collected=700.0,  # $3.50 × 2 × 100 = $700
    commission=2.0
)

print("📊 ניתוח הפוזיציה:")
print(f"  • פרמיה נטו: ${position.net_premium:.2f}")
print(f"  • רווח מקסימלי (אם מוקצה): ${position.max_profit:.2f}")
print(f"  • תשואה אם מוקצה: {position.return_if_assigned:.2f}%")
print(f"  • תשואה שנתית: {position.annualized_return:.2f}%")
print(f"  • מחיר איזון: ${position.breakeven_price:.2f}")
print(f"  • הגנה כלפי מטה: {position.downside_protection:.2f}%")
print()

# ═══════════════════════════════════════════════════════════════════
# דוגמה 2: מציאת Strike אופטימלי
# ═══════════════════════════════════════════════════════════════════
print("\n2️⃣  מציאת Strike אופטימלי - אסטרטגיה Moderate")
print("-" * 70)

# יצירת אסטרטגיה
strategy = CoveredCallStrategy(RiskLevel.MODERATE)

# דמה מספר אופציות
test_options = [
    OptionContract("AAPL", 185.0, datetime.now() + timedelta(days=30), OptionType.CALL,
                   5.00, 30.0, 0.50, 0.02, -0.06, 0.14, 8000, 15000, 4.95, 5.05),
    OptionContract("AAPL", 190.0, datetime.now() + timedelta(days=30), OptionType.CALL,
                   3.50, 25.0, 0.30, 0.015, -0.05, 0.12, 5000, 10000, 3.45, 3.55),
    OptionContract("AAPL", 195.0, datetime.now() + timedelta(days=30), OptionType.CALL,
                   2.00, 22.0, 0.20, 0.012, -0.04, 0.10, 3000, 8000, 1.95, 2.05),
    OptionContract("AAPL", 200.0, datetime.now() + timedelta(days=30), OptionType.CALL,
                   1.00, 20.0, 0.10, 0.008, -0.03, 0.08, 2000, 5000, 0.95, 1.05),
]

# מצא את ה-Strikes הטובים ביותר
best_strikes = strategy.find_best_strike(test_options, my_stock.current_price, top_n=3)

print(f"נמצאו {len(best_strikes)} Strikes מומלצים:\n")
for i, (opt, score) in enumerate(best_strikes, 1):
    print(f"#{i} Strike ${opt.strike:.2f} - ציון: {score:.0f}/100")

    # חישוב תשואה פוטנציאלית
    contracts = my_stock.quantity // 100
    total_premium = opt.premium * contracts * 100
    premium_pct = (total_premium / my_stock.market_value) * 100
    annualized = premium_pct * (365 / opt.days_to_expiration)

    print(f"   📊 פרמיה: ${opt.premium:.2f} (סה\"כ ${total_premium:.0f})")
    print(f"   📈 תשואה: {premium_pct:.2f}% | שנתית: {annualized:.2f}%")
    print(f"   🎯 Delta: {opt.delta:.3f} | IV: {opt.implied_volatility:.1f}%")
    print(f"   🕐 DTE: {opt.days_to_expiration} ימים")
    print()

# ═══════════════════════════════════════════════════════════════════
# דוגמה 3: השוואת רמות סיכון
# ═══════════════════════════════════════════════════════════════════
print("\n3️⃣  השוואת אסטרטגיות לפי רמת סיכון")
print("-" * 70)

risk_levels = [RiskLevel.CONSERVATIVE, RiskLevel.MODERATE, RiskLevel.AGGRESSIVE]

for risk in risk_levels:
    strat = CoveredCallStrategy(risk)
    print(f"\n{risk.value}:")
    print(f"  • טווח Delta: {strat.target_delta[0]:.2f} - {strat.target_delta[1]:.2f}")
    print(f"  • מינימום פרמיה: {strat.min_premium_pct:.1f}%")
    print(f"  • מקס ימים לתפוגה: {strat.max_dte}")

# ═══════════════════════════════════════════════════════════════════
# דוגמה 4: ניהול פורטפוליו
# ═══════════════════════════════════════════════════════════════════
print("\n\n4️⃣  ניהול פורטפוליו")
print("-" * 70)

portfolio = PortfolioManager()

# הוסף פוזיציות
portfolio.add_position(position)

# הוסף עוד פוזיציה
msft_stock = Stock("MSFT", 100, 380.0, 385.0)
msft_option = OptionContract(
    "MSFT", 395.0, datetime.now() + timedelta(days=25),
    OptionType.CALL, 6.00, 28.0, 0.32, 0.014, -0.055, 0.13,
    4500, 9000, 5.90, 6.10
)
msft_position = CoveredCall(
    "CC_MSFT_001", msft_stock, msft_option, 1,
    datetime.now(), PositionStatus.OPEN, 600.0, 1.0
)
portfolio.add_position(msft_position)

# נתוני פורטפוליו
metrics = portfolio.get_portfolio_metrics()

print("\n📊 סיכום פורטפוליו:")
print(f"  • סה\"כ פוזיציות: {metrics['total_positions']}")
print(f"  • שווי מניות: ${metrics['total_stock_value']:,.2f}")
print(f"  • פרמיה שנגבתה: ${metrics['total_premium_collected']:,.2f}")
print(f"  • רווח מקסימלי: ${metrics['total_max_profit']:,.2f}")
print(f"  • תשואה אם מוקצה: {metrics['portfolio_return_if_assigned']:.2f}%")
print(f"  • ממוצע Delta: {metrics['avg_delta']:.3f}")
print(f"  • ממוצע DTE: {metrics['avg_days_to_expiration']:.0f} ימים")

# Delta ו-Theta של הפורטפוליו
total_delta = portfolio.calculate_total_delta()
total_theta = portfolio.calculate_total_theta()

print(f"\n📈 חשיפת Greeks:")
print(f"  • סה\"כ Delta: {total_delta:.2f}")
print(f"  • סה\"כ Theta: ${total_theta:.2f}/יום")

# ═══════════════════════════════════════════════════════════════════
# דוגמה 5: אסטרטגיית Rolling
# ═══════════════════════════════════════════════════════════════════
print("\n\n5️⃣  האם לגלגל (Roll) את הפוזיציה?")
print("-" * 70)

# בדוק אם צריך לגלגל
should_roll = RollStrategy.should_roll(position, my_stock.current_price)

print(f"מחיר נוכחי: ${my_stock.current_price:.2f}")
print(f"Strike: ${position.option.strike:.2f}")
print(f"DTE: {position.option.days_to_expiration} ימים")
print(f"\n{'✅ כדאי לגלגל' if should_roll else '❌ אין צורך לגלגל'}")

if should_roll:
    print("\nסיבות:")
    if position.option.days_to_expiration <= 7:
        print("  • קרוב לתפוגה")
    if my_stock.current_price >= position.option.strike:
        print("  • ITM - סיכון להקצאה")

# ═══════════════════════════════════════════════════════════════════
# דוגמה 6: מערכת התראות
# ═══════════════════════════════════════════════════════════════════
print("\n\n6️⃣  התראות ואזהרות")
print("-" * 70)

alert_system = AlertSystem()
alerts = alert_system.check_alerts(portfolio)

if alerts:
    print(f"נמצאו {len(alerts)} התראות:\n")
    for alert in alerts:
        severity_emoji = {
            'HIGH': '🔴',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }[alert['severity']]

        print(f"{severity_emoji} {alert['type']}")
        print(f"   {alert['message']}")
        print(f"   פעולה מומלצת: {alert['action']}")
        print()
else:
    print("✅ אין התראות - הכל תקין!")

# ═══════════════════════════════════════════════════════════════════
# דוגמה 7: יצוא נתונים
# ═══════════════════════════════════════════════════════════════════
print("\n7️⃣  יצוא נתונים")
print("-" * 70)

output_file = "portfolio_example.json"
portfolio.export_to_json(output_file)
print(f"✅ הפורטפוליו יוצא ל: {output_file}")

print("\n" + "="*70)
print("✅ הדוגמאות הושלמו!")
print("="*70)
print("\n💡 טיפים:")
print("  1. השתמש בדשבורד לניהול ויזואלי")
print("  2. התחבר ל-IBKR לנתונים בזמן אמת")
print("  3. התחל עם אסטרטגיה MODERATE")
print("  4. בדוק Delta לפני מכירה")
print("  5. הגדר התראות ב-TradingView")
print()
