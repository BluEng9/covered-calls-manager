#!/usr/bin/env python3
"""
📊 ניתוח אופציות TSLA - נתונים מיום שישי 03.10.2025
משתמש בנתונים היסטוריים כי השוק סגור
"""

from ibkr_connector import IBKRConnector, IBKRConfig
from covered_calls_system import CoveredCallStrategy, RiskLevel, OptionContract
from datetime import datetime, timedelta
import sys

print("=" * 80)
print("📊 ניתוח אופציות TSLA - נתונים מ-03.10.2025 (יום שישי)")
print("=" * 80)
print()

# הגדרות
SYMBOL = "TSLA"
STOCK_QUANTITY = 300
HISTORICAL_DATE = "20251003"  # יום שישי האחרון
MIN_DTE = 14
MAX_DTE = 90

print(f"🎯 מניה: {SYMBOL}")
print(f"📦 כמות: {STOCK_QUANTITY} מניות ({STOCK_QUANTITY // 100} חוזים)")
print(f"📅 נתונים מתאריך: 03.10.2025")
print(f"📅 טווח DTE: {MIN_DTE}-{MAX_DTE} ימים")
print()

# התחבר ל-IBKR
config = IBKRConfig(
    host="127.0.0.1",
    port=7497,
    client_id=4,
    readonly=True
)

try:
    print("🔌 מתחבר ל-Interactive Brokers...")
    ibkr = IBKRConnector(config)

    if not ibkr.connect():
        print("❌ החיבור נכשל")
        sys.exit(1)

    print("✅ מחובר ל-TWS\n")

    # קבל מחיר סגירה מיום שישי
    print(f"📊 מושך נתונים היסטוריים ל-{SYMBOL}...")

    try:
        # קבל נתון אחד - סגירה של יום שישי
        historical_data = ibkr.get_historical_data(
            SYMBOL,
            duration="1 D",  # יום אחד
            bar_size="1 day",
            what_to_show="TRADES"
        )

        if not historical_data.empty:
            # קח את המחיר האחרון (סגירה של יום שישי)
            last_close = historical_data.iloc[-1]['close']
            last_date = historical_data.iloc[-1]['date']

            # המרה לתאריך
            if hasattr(last_date, 'date'):
                date_str = last_date.date()
            else:
                date_str = str(last_date)[:10]

            print(f"✅ מחיר סגירה ב-{date_str}: ${last_close:.2f}")
            current_price = last_close
        else:
            print("⚠️  לא התקבלו נתונים. משתמש במחיר לדוגמה: $400")
            current_price = 400.0

    except Exception as e:
        print(f"⚠️  שגיאה בקבלת היסטוריה: {e}")
        print("משתמש במחיר לדוגמה: $400")
        current_price = 400.0

    print(f"💰 מחיר עבודה: ${current_price:.2f}\n")

    # חשב אזורי Strike
    print("🎯 אזורי Strike מומלצים:")
    atm_strike = int(round(current_price))
    otm_5pct = int(round(current_price * 1.05))
    otm_10pct = int(round(current_price * 1.10))
    otm_15pct = int(round(current_price * 1.15))

    print(f"  ATM: ${atm_strike}")
    print(f"  OTM +5%: ${otm_5pct}")
    print(f"  OTM +10%: ${otm_10pct}")
    print(f"  OTM +15%: ${otm_15pct}")
    print()

    # קבל Option Chain
    print("=" * 80)
    print("📋 Option Chain - תפוגות זמינות")
    print("=" * 80)
    print()

    chain = ibkr.get_option_chain(SYMBOL)

    if chain.empty:
        print("❌ לא התקבל Option Chain")
        ibkr.disconnect()
        sys.exit(1)

    # הצג תפוגות זמינות
    if 'expiration' in chain.columns:
        expirations = sorted(chain['expiration'].unique())

        print(f"✅ נמצאו {len(expirations)} תפוגות:\n")

        today = datetime.now()
        valid_expirations = []

        for i, exp in enumerate(expirations[:15], 1):  # הצג רק 15 הראשונות
            exp_date = datetime.strptime(exp, "%Y%m%d")
            dte = (exp_date - today).days

            if MIN_DTE <= dte <= MAX_DTE:
                valid_expirations.append((exp, dte))
                print(f"  ✅ {i}. {exp} ({dte} ימים) ⭐")
            else:
                status = "📅" if dte < MIN_DTE else "📆"
                print(f"  {status} {i}. {exp} ({dte} ימים)")

        print()
        print(f"✅ {len(valid_expirations)} תפוגות בטווח {MIN_DTE}-{MAX_DTE} ימים")
        print()

        if not valid_expirations:
            print("⚠️  אין תפוגות בטווח הרצוי")
            print("💡 טיפ: שנה את MIN_DTE או MAX_DTE")
            ibkr.disconnect()
            sys.exit(0)

        # בחר 3 תפוגות מייצגות
        selected_expirations = []

        # קצר (14-21 ימים)
        short_term = [e for e in valid_expirations if 14 <= e[1] <= 21]
        if short_term:
            selected_expirations.append(short_term[0])

        # בינוני (30-45 ימים)
        mid_term = [e for e in valid_expirations if 30 <= e[1] <= 45]
        if mid_term:
            selected_expirations.append(mid_term[0])

        # ארוך (60-90 ימים)
        long_term = [e for e in valid_expirations if 60 <= e[1] <= 90]
        if long_term:
            selected_expirations.append(long_term[0])

        if not selected_expirations:
            # אם אין תפוגות מייצגות, קח את 3 הראשונות
            selected_expirations = valid_expirations[:3]

        print(f"🎯 תפוגות לניתוח מעמיק:")
        for exp, dte in selected_expirations:
            if dte <= 21:
                term = "קצר טווח"
            elif dte <= 45:
                term = "בינוני טווח"
            else:
                term = "ארוך טווח"
            print(f"  • {exp} ({dte} ימים) - {term}")
        print()

        # ניתוח Strikes מתאימים
        print("=" * 80)
        print("📊 המלצות Covered Call לפי רמת סיכון")
        print("=" * 80)
        print()

        # הצע Strikes ספציפיים בהתבסס על המחיר
        strike_suggestions = {
            "שמרני (Conservative)": [
                (otm_10pct, f"OTM +10% (${otm_10pct})"),
                (otm_15pct, f"OTM +15% (${otm_15pct})")
            ],
            "מאוזן (Moderate)": [
                (otm_5pct, f"OTM +5% (${otm_5pct})"),
                (otm_10pct, f"OTM +10% (${otm_10pct})")
            ],
            "אגרסיבי (Aggressive)": [
                (atm_strike, f"ATM (${atm_strike})"),
                (otm_5pct, f"OTM +5% (${otm_5pct})")
            ]
        }

        for risk_name, strikes in strike_suggestions.items():
            print(f"\n{'='*80}")
            print(f"🎯 {risk_name}")
            print(f"{'='*80}\n")

            for strike, strike_desc in strikes:
                print(f"Strike: {strike_desc}")
                print(f"{'─'*80}")

                # חישובים לכל תפוגה
                for exp, dte in selected_expirations:
                    # חישוב משוער של פרמיה (בהתבסס על IV ו-DTE)
                    # פרמיה משוערת: ככל שיותר OTM ויותר DTE, יותר פרמיה

                    distance_pct = ((strike - current_price) / current_price) * 100

                    # פרמיה בסיסית (1-3% מהמחיר)
                    if distance_pct <= 0:  # ATM or ITM
                        base_premium_pct = 0.03
                    elif distance_pct <= 5:  # OTM 0-5%
                        base_premium_pct = 0.02
                    elif distance_pct <= 10:  # OTM 5-10%
                        base_premium_pct = 0.015
                    else:  # OTM 10%+
                        base_premium_pct = 0.01

                    # התאמה לפי DTE
                    dte_factor = (dte / 30) ** 0.5  # שורש ריבועי של יחס DTE ל-30 ימים

                    estimated_premium_per_share = current_price * base_premium_pct * dte_factor

                    # חישוב תשואות
                    num_contracts = STOCK_QUANTITY // 100
                    premium_per_contract = estimated_premium_per_share * 100
                    total_premium = premium_per_contract * num_contracts

                    investment = current_price * STOCK_QUANTITY
                    premium_yield = (total_premium / investment) * 100
                    annualized = premium_yield * (365 / dte)

                    if_assigned = ((strike - current_price) * STOCK_QUANTITY) + total_premium
                    return_if_assigned = (if_assigned / investment) * 100
                    annualized_if_assigned = return_if_assigned * (365 / dte)

                    breakeven = current_price - (total_premium / STOCK_QUANTITY)
                    downside_protection = ((current_price - breakeven) / current_price) * 100

                    # הצגה
                    exp_date = datetime.strptime(exp, "%Y%m%d")
                    print(f"\n  📅 תפוגה: {exp_date.strftime('%d.%m.%Y')} ({dte} ימים)")
                    print(f"  ─────────────────────────────────────")
                    print(f"  💰 פרמיה משוערת:")
                    print(f"     ${estimated_premium_per_share:.2f}/מניה × 100 = ${premium_per_contract:,.0f}/חוזה")
                    print(f"     {num_contracts} חוזים × ${premium_per_contract:,.0f} = ${total_premium:,.0f} סה\"כ")
                    print()
                    print(f"  📈 תשואות:")
                    print(f"     תשואת פרמיה: {premium_yield:.2f}% ({dte} ימים)")
                    print(f"     תשואה שנתית (פרמיה): {annualized:.2f}%")
                    print(f"     תשואה אם מוקצה: {return_if_assigned:.2f}%")
                    print(f"     תשואה שנתית (אם מוקצה): {annualized_if_assigned:.2f}%")
                    print()
                    print(f"  🛡️  הגנה:")
                    print(f"     Breakeven: ${breakeven:.2f}")
                    print(f"     Downside Protection: {downside_protection:.2f}%")

                print()

        # סיכום
        print("\n" + "=" * 80)
        print("📊 סיכום והמלצות")
        print("=" * 80)
        print()

        print("⚠️  שים לב: הנתונים לעיל הם אומדנים משוערים!")
        print("הפרמיות האמיתיות ישתנו בהתאם ל:")
        print("  • IV (Implied Volatility) בפועל")
        print("  • ביקוש והיצע בשוק")
        print("  • אירועים (Earnings, חדשות)")
        print()

        print("💡 המלצות כלליות ל-TSLA:")
        print()
        print("🟢 שמרני:")
        print(f"   Strike: ${otm_10pct}-${otm_15pct} (OTM +10-15%)")
        print("   DTE: 30-45 ימים")
        print("   יעד: פרמיה יציבה, סיכוי נמוך להקצאה")
        print()
        print("🟡 מאוזן: ⭐ מומלץ")
        print(f"   Strike: ${otm_5pct}-${otm_10pct} (OTM +5-10%)")
        print("   DTE: 30-45 ימים")
        print("   יעד: איזון טוב בין פרמיה לסיכון")
        print()
        print("🔴 אגרסיבי:")
        print(f"   Strike: ${atm_strike}-${otm_5pct} (ATM עד OTM +5%)")
        print("   DTE: 14-30 ימים")
        print("   יעד: פרמיה גבוהה, מוכן למכור")
        print()

        print("🎯 הצעדים הבאים:")
        print()
        print("1. כשהשוק יפתח (מחר בבוקר):")
        print("   python analyze_tsla_options.py")
        print()
        print("2. או השתמש בדשבורד:")
        print("   http://localhost:8501")
        print()
        print("3. בדוק את המחירים האמיתיים והשווה לאומדנים")
        print()

    ibkr.disconnect()
    print("👋 התנתקות מ-IBKR")

except KeyboardInterrupt:
    print("\n\n⚠️  בוטל על ידי המשתמש")

except Exception as e:
    print(f"\n❌ שגיאה: {e}")
    import traceback
    traceback.print_exc()

print()
