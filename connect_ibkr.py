#!/usr/bin/env python3
"""
🔌 התחברות ל-IBKR TWS והצגת נתונים בסיסיים
"""

from ibkr_connector import IBKRConnector, IBKRConfig
from covered_calls_system import CoveredCallStrategy, RiskLevel
import sys

print("="*70)
print("🔌 מתחבר ל-Interactive Brokers TWS...")
print("="*70)
print()

# הגדרות חיבור
config = IBKRConfig(
    host="127.0.0.1",
    port=7497,  # TWS Paper Trading
    client_id=1,
    readonly=True  # מצב קריאה בלבד - בטוח לבדיקות
)

try:
    # התחבר
    print("📡 מנסה להתחבר...")
    ibkr = IBKRConnector(config)

    if not ibkr.connect():
        print("❌ החיבור נכשל. וודא ש-TWS פעיל ו-API מופעל")
        sys.exit(1)

    print("✅ התחברות הצליחה!\n")

    # ═══════════════════════════════════════════════════════════════════
    # 1. נתוני חשבון
    # ═══════════════════════════════════════════════════════════════════
    print("📊 נתוני חשבון:")
    print("-" * 70)

    account = ibkr.get_account_summary()

    if account:
        print(f"  💰 נכסים נטו: ${account.get('NetLiquidation', 0):,.2f}")
        print(f"  💵 מזומן: ${account.get('TotalCashValue', 0):,.2f}")
        print(f"  📈 רווח/הפסד לא ממומש: ${account.get('UnrealizedPnL', 0):,.2f}")
        print(f"  💹 רווח/הפסד ממומש: ${account.get('RealizedPnL', 0):,.2f}")
        print(f"  🛡️  כוח קנייה: ${account.get('BuyingPower', 0):,.2f}")
    else:
        print("  ⚠️  לא התקבלו נתוני חשבון")

    print()

    # ═══════════════════════════════════════════════════════════════════
    # 2. פוזיציות מניות
    # ═══════════════════════════════════════════════════════════════════
    print("📈 פוזיציות מניות:")
    print("-" * 70)

    stocks = ibkr.get_stock_positions()

    if stocks:
        print(f"נמצאו {len(stocks)} פוזיציות:\n")

        total_value = 0
        total_pnl = 0

        for stock in stocks:
            print(f"  🏢 {stock.symbol}")
            print(f"     כמות: {stock.quantity} מניות")
            print(f"     מחיר ממוצע: ${stock.avg_cost:.2f}")
            print(f"     מחיר נוכחי: ${stock.current_price:.2f}")
            print(f"     שווי: ${stock.market_value:,.2f}")

            pnl_emoji = "🟢" if stock.unrealized_pnl >= 0 else "🔴"
            print(f"     {pnl_emoji} P&L: ${stock.unrealized_pnl:,.2f} ({stock.unrealized_pnl_pct:.2f}%)")

            total_value += stock.market_value
            total_pnl += stock.unrealized_pnl

            # בדוק אם אפשר למכור Covered Calls
            contracts_available = stock.quantity // 100
            if contracts_available > 0:
                print(f"     ✅ ניתן למכור {contracts_available} חוזי Call")
            else:
                print(f"     ⚠️  צריך לפחות 100 מניות למכירת Call")

            print()

        print(f"סה\"כ שווי מניות: ${total_value:,.2f}")
        print(f"סה\"כ P&L: ${total_pnl:,.2f}")

    else:
        print("  📭 אין פוזיציות מניות")
        print("  💡 טיפ: קנה לפחות 100 מניות כדי למכור Covered Call")

    print()

    # ═══════════════════════════════════════════════════════════════════
    # 3. פוזיציות אופציות
    # ═══════════════════════════════════════════════════════════════════
    print("🎯 פוזיציות אופציות:")
    print("-" * 70)

    options = ibkr.get_option_positions()

    if options:
        print(f"נמצאו {len(options)} פוזיציות אופציות:\n")

        for opt in options:
            contract = opt['contract']
            print(f"  📝 {contract.symbol} {contract.strike} {contract.right}")
            print(f"     תפוגה: {contract.lastTradeDateOrContractMonth}")
            print(f"     כמות: {opt['position']}")
            print(f"     מחיר ממוצע: ${opt['avg_cost']:.2f}")
            print(f"     שווי שוק: ${opt['market_value']:,.2f}")
            print(f"     P&L: ${opt['unrealized_pnl']:,.2f}")
            print()
    else:
        print("  📭 אין פוזיציות אופציות")

    print()

    # ═══════════════════════════════════════════════════════════════════
    # 4. אם יש מניות - מצא Covered Calls אפשריים
    # ═══════════════════════════════════════════════════════════════════
    if stocks and len(stocks) > 0:
        stock = stocks[0]  # קח את המניה הראשונה

        if stock.quantity >= 100:
            print(f"🎯 מציאת Covered Calls אופטימליים עבור {stock.symbol}:")
            print("-" * 70)

            try:
                print(f"מחפש אופציות OTM ל-{stock.symbol} במחיר ${stock.current_price:.2f}...")

                # מצא OTM Calls
                otm_calls = ibkr.get_otm_calls(
                    stock.symbol,
                    stock.current_price,
                    days_to_expiration=30
                )

                if otm_calls:
                    print(f"✅ נמצאו {len(otm_calls)} אופציות\n")

                    # דרג את האופציות
                    strategy = CoveredCallStrategy(RiskLevel.MODERATE)
                    best_strikes = strategy.find_best_strike(
                        otm_calls,
                        stock.current_price,
                        top_n=3
                    )

                    print("🏆 3 ה-Strikes הטובים ביותר:\n")

                    for i, (option, score) in enumerate(best_strikes, 1):
                        print(f"#{i} - Strike ${option.strike:.2f} (ציון: {score:.0f}/100)")

                        # חישוב תשואה
                        contracts = stock.quantity // 100
                        total_premium = option.premium * contracts * 100
                        premium_pct = (total_premium / stock.market_value) * 100
                        annualized = premium_pct * (365 / option.days_to_expiration)

                        print(f"    📊 פרמיה: ${option.premium:.2f}/חוזה (סה\"כ ${total_premium:.0f})")
                        print(f"    📈 תשואה: {premium_pct:.2f}% ({option.days_to_expiration} ימים)")
                        print(f"    📅 תשואה שנתית: {annualized:.2f}%")
                        print(f"    🎯 Delta: {option.delta:.3f}")
                        print(f"    📊 IV: {option.implied_volatility:.1f}%")
                        print(f"    💧 נזילות: {'✅ טובה' if option.is_liquid else '⚠️ נמוכה'}")
                        print()

                    print("💡 כדי למכור Covered Call, השתמש ב:")
                    print(f"   ibkr.sell_covered_call('{stock.symbol}', 1, {best_strikes[0][0].strike:.2f}, ...)")

                else:
                    print("⚠️  לא נמצאו אופציות מתאימות")

            except Exception as e:
                print(f"⚠️  שגיאה בחיפוש אופציות: {e}")
                print("   (ייתכן שאין אופציות זמינות למניה זו)")

    print()
    print("="*70)
    print("✅ הבדיקה הושלמה בהצלחה!")
    print("="*70)
    print()
    print("📝 הצעדים הבאים:")
    print("  1. פתח את הדשבורד: http://localhost:8501")
    print("  2. התחבר ל-IBKR דרך הדשבורד")
    print("  3. השתמש ב-Strategy Finder למציאת Strikes")
    print("  4. מכור Covered Calls ישירות מהדשבורד")
    print()

    # נתק
    ibkr.disconnect()
    print("👋 התנתקות מ-IBKR")

except KeyboardInterrupt:
    print("\n\n⚠️  החיבור בוטל על ידי המשתמש")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ שגיאה: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
