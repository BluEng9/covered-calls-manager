#!/usr/bin/env python3
"""
📊 ניתוח מעמיק של אופציות TSLA
טווח: 14-90 ימים (2 שבועות - 3 חודשים)
"""

from ibkr_connector import IBKRConnector, IBKRConfig
from covered_calls_system import CoveredCallStrategy, RiskLevel
import sys
from datetime import datetime, timedelta
import pandas as pd

print("=" * 80)
print("📊 ניתוח אופציות TSLA - Covered Calls")
print("=" * 80)
print()

# הגדרות
SYMBOL = "TSLA"
STOCK_QUANTITY = 300  # יש לך 300 מניות
MIN_DTE = 14  # מינימום 2 שבועות
MAX_DTE = 90  # מקסימום 3 חודשים

print(f"🎯 מניה: {SYMBOL}")
print(f"📦 כמות: {STOCK_QUANTITY} מניות ({STOCK_QUANTITY // 100} חוזים)")
print(f"📅 טווח DTE: {MIN_DTE}-{MAX_DTE} ימים")
print()

# התחבר ל-IBKR
config = IBKRConfig(
    host="127.0.0.1",
    port=7497,
    client_id=3,  # Client ID שונה
    readonly=True  # קריאה בלבד לניתוח
)

try:
    print("🔌 מתחבר ל-Interactive Brokers...")
    ibkr = IBKRConnector(config)

    if not ibkr.connect():
        print("❌ החיבור נכשל")
        sys.exit(1)

    print("✅ מחובר ל-TWS\n")

    # קבל מחיר נוכחי
    print(f"📊 בודק מחיר {SYMBOL}...")

    try:
        current_price = ibkr.get_stock_price(SYMBOL)

        # בדוק אם המחיר תקין
        import math
        if not current_price or current_price == 0 or math.isnan(current_price):
            raise ValueError("Invalid price")

    except Exception as e:
        print(f"⚠️  לא ניתן לקבל מחיר (השוק סגור). משתמש במחיר לדוגמה: $400")
        current_price = 400.0

    print(f"💰 מחיר נוכחי: ${current_price:.2f}\n")

    # חשב אזורי Strike מעניינים
    print("🎯 אזורי Strike:")
    atm_strike = int(round(current_price))
    otm_5pct = round(current_price * 1.05)
    otm_10pct = round(current_price * 1.10)
    otm_15pct = round(current_price * 1.15)

    print(f"  ATM (At The Money): ${atm_strike}")
    print(f"  OTM 5%: ${otm_5pct}")
    print(f"  OTM 10%: ${otm_10pct}")
    print(f"  OTM 15%: ${otm_15pct}")
    print()

    # אסוף אופציות בטווח DTE הרצוי
    print("=" * 80)
    print("🔍 מחפש אופציות בטווח התפוגה...")
    print("=" * 80)
    print()

    all_options = []

    # נסה תפוגות שונות
    for days_ahead in [14, 21, 30, 45, 60, 75, 90]:
        if days_ahead < MIN_DTE or days_ahead > MAX_DTE:
            continue

        print(f"📅 בודק תפוגה ב-{days_ahead} ימים...")

        try:
            options = ibkr.get_otm_calls(
                SYMBOL,
                current_price,
                days_to_expiration=days_ahead
            )

            if options:
                print(f"   ✅ נמצאו {len(options)} אופציות")
                all_options.extend(options)
            else:
                print(f"   ⚠️  לא נמצאו אופציות")

        except Exception as e:
            print(f"   ❌ שגיאה: {e}")

    if not all_options:
        print("\n❌ לא נמצאו אופציות בטווח הזמן הזה")
        print("💡 טיפ: נסה שוב כשהשוק פתוח (9:30-16:00 EST)")
        ibkr.disconnect()
        sys.exit(1)

    print(f"\n✅ סה\"כ נמצאו {len(all_options)} אופציות")
    print()

    # ניתוח עם 3 רמות סיכון
    print("=" * 80)
    print("📊 ניתוח לפי רמות סיכון")
    print("=" * 80)
    print()

    results = {}

    for risk_name, risk_level in [
        ("שמרני (Conservative)", RiskLevel.CONSERVATIVE),
        ("מאוזן (Moderate)", RiskLevel.MODERATE),
        ("אגרסיבי (Aggressive)", RiskLevel.AGGRESSIVE)
    ]:
        print(f"\n{'='*80}")
        print(f"🎯 {risk_name}")
        print(f"{'='*80}\n")

        strategy = CoveredCallStrategy(risk_level)

        # מצא 5 הטובים ביותר
        best_strikes = strategy.find_best_strike(
            all_options,
            current_price,
            top_n=5
        )

        if not best_strikes:
            print("⚠️  לא נמצאו אופציות מתאימות לרמת סיכון זו")
            continue

        results[risk_name] = best_strikes

        # הצג תוצאות
        for i, (option, score) in enumerate(best_strikes, 1):
            print(f"#{i} - Strike ${option.strike:.2f} | תפוגה: {option.expiration} ({option.days_to_expiration} ימים)")
            print(f"{'─'*80}")

            # חישובי תשואה
            num_contracts = STOCK_QUANTITY // 100
            premium_per_contract = option.premium * 100
            total_premium = premium_per_contract * num_contracts

            # תשואה על ההשקעה הנוכחית
            investment = current_price * STOCK_QUANTITY
            premium_yield = (total_premium / investment) * 100

            # תשואה שנתית
            annualized = premium_yield * (365 / option.days_to_expiration)

            # רווח אם מוקצה
            if_assigned = ((option.strike - current_price) * STOCK_QUANTITY) + total_premium
            return_if_assigned = (if_assigned / investment) * 100
            annualized_if_assigned = return_if_assigned * (365 / option.days_to_expiration)

            # מחיר איזון
            breakeven = current_price - (total_premium / STOCK_QUANTITY)
            downside_protection = ((current_price - breakeven) / current_price) * 100

            # הצגה
            print(f"📊 פרמיה:")
            print(f"   ${option.premium:.2f}/מניה × 100 = ${premium_per_contract:,.0f}/חוזה")
            print(f"   {num_contracts} חוזים × ${premium_per_contract:,.0f} = ${total_premium:,.0f} סה\"כ")
            print()

            print(f"📈 תשואות:")
            print(f"   תשואת פרמיה: {premium_yield:.2f}% ({option.days_to_expiration} ימים)")
            print(f"   תשואה שנתית (פרמיה): {annualized:.2f}%")
            print(f"   תשואה אם מוקצה: {return_if_assigned:.2f}%")
            print(f"   תשואה שנתית (אם מוקצה): {annualized_if_assigned:.2f}%")
            print()

            print(f"🎯 Greeks & Stats:")
            print(f"   Delta: {option.delta:.3f} (סיכוי ~{option.delta*100:.0f}% ITM)")
            print(f"   Theta: ${option.theta:.2f}/יום (דעיכת זמן)")
            print(f"   IV: {option.implied_volatility:.1f}%")
            print()

            print(f"🛡️  הגנה:")
            print(f"   Breakeven: ${breakeven:.2f}")
            print(f"   Downside Protection: {downside_protection:.2f}%")
            print(f"   המניה יכולה לרדת ל-${breakeven:.2f} בלי להפסיד")
            print()

            print(f"💡 ציון איכות: {score:.0f}/100")
            print(f"   נזילות: {'✅ טובה' if option.is_liquid else '⚠️ נמוכה'}")

            # המלצה
            if option.delta < 0.25:
                risk_label = "🟢 סיכון נמוך"
            elif option.delta < 0.35:
                risk_label = "🟡 סיכון בינוני"
            else:
                risk_label = "🔴 סיכון גבוה"

            print(f"   רמת סיכון: {risk_label}")
            print()

    # סיכום והשוואה
    print("\n" + "=" * 80)
    print("📊 סיכום והמלצות")
    print("=" * 80)
    print()

    if results:
        print("🏆 ההמלצות הטובות ביותר לפי רמת סיכון:")
        print()

        for risk_name, strikes in results.items():
            if strikes:
                best_option, best_score = strikes[0]

                num_contracts = STOCK_QUANTITY // 100
                total_premium = best_option.premium * 100 * num_contracts
                investment = current_price * STOCK_QUANTITY
                premium_yield = (total_premium / investment) * 100
                annualized = premium_yield * (365 / best_option.days_to_expiration)

                print(f"▪️ {risk_name}:")
                print(f"  Strike: ${best_option.strike:.2f} | DTE: {best_option.days_to_expiration}")
                print(f"  פרמיה: ${total_premium:,.0f} | תשואה שנתית: {annualized:.2f}%")
                print(f"  Delta: {best_option.delta:.3f} | ציון: {best_score:.0f}/100")
                print()

    print("💡 איך לבחור:")
    print()
    print("🟢 שמרני (Conservative):")
    print("   ✓ Delta נמוך (0.15-0.25) = סיכוי נמוך להקצאה")
    print("   ✓ פרמיה קטנה אבל יציבה")
    print("   ✓ מתאים למי שרוצה להחזיק במניה")
    print()
    print("🟡 מאוזן (Moderate):")
    print("   ✓ Delta בינוני (0.25-0.35) = איזון טוב")
    print("   ✓ פרמיה סבירה")
    print("   ✓ מתאים לרוב המשקיעים ⭐ מומלץ")
    print()
    print("🔴 אגרסיבי (Aggressive):")
    print("   ✓ Delta גבוה (0.35-0.50) = פרמיה גבוהה")
    print("   ✓ סיכוי גבוה להקצאה")
    print("   ✓ מתאים למי שמוכן למכור במחיר טוב")
    print()

    print("🎯 הצעדים הבאים:")
    print()
    print("1. בחר את רמת הסיכון שמתאימה לך")
    print("2. בחר אחד מ-5 ה-Strikes המומלצים")
    print("3. פתח את הדשבורד: http://localhost:8501")
    print("4. או השתמש בפונקציה sell_covered_call:")
    print()
    print("   מאוזן לדוגמה:")
    if "מאוזן (Moderate)" in results and results["מאוזן (Moderate)"]:
        best_mod, _ = results["מאוזן (Moderate)"][0]
        print(f"   ibkr.sell_covered_call('{SYMBOL}', {STOCK_QUANTITY // 100}, {best_mod.strike:.0f}, '{best_mod.expiration}')")
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
