#!/usr/bin/env python3
"""
🛒 קניית מניות לדוגמה ב-Paper Trading
הסקריפט הזה מראה איך לקנות מניות דרך IBKR
"""

from ibkr_connector import IBKRConnector, IBKRConfig
from ib_async import Stock, MarketOrder, LimitOrder
import sys

print("="*70)
print("🛒 קניית מניות לדוגמה - Paper Trading")
print("="*70)
print()

# הגדרות
SYMBOL = "AAPL"  # שנה למניה אחרת אם תרצה
QUANTITY = 100   # 100 מניות = 1 חוזה Covered Call
BUY_TYPE = "MARKET"  # או "LIMIT"

print(f"📝 הפרמטרים:")
print(f"  מניה: {SYMBOL}")
print(f"  כמות: {QUANTITY}")
print(f"  סוג פקודה: {BUY_TYPE}")
print()

# התחבר
config = IBKRConfig(
    host="127.0.0.1",
    port=7497,
    client_id=1,
    readonly=False  # ⚠️ חשוב: readonly=False כדי לאפשר מסחר!
)

try:
    ibkr = IBKRConnector(config)

    if not ibkr.connect():
        print("❌ החיבור נכשל")
        sys.exit(1)

    print("✅ מחובר ל-TWS\n")

    # קבל מחיר נוכחי
    print(f"📊 בודק מחיר {SYMBOL}...")
    current_price = ibkr.get_stock_price(SYMBOL)

    if current_price:
        print(f"✅ מחיר נוכחי: ${current_price:.2f}\n")

        total_cost = current_price * QUANTITY
        print(f"💰 עלות משוערת: ${total_cost:,.2f}\n")

        # אישור משתמש
        print("⚠️  זוהי פקודה ב-Paper Trading (לא כסף אמיתי)")
        confirm = input(f"\n❓ האם לבצע קניה של {QUANTITY} מניות {SYMBOL}? (yes/no): ")

        if confirm.lower() in ['yes', 'y']:
            print("\n📤 שולח פקודה...")

            # יצירת חוזה
            contract = Stock(SYMBOL, 'SMART', 'USD')
            ibkr.ib.qualifyContracts(contract)

            # יצירת פקודה
            if BUY_TYPE == "MARKET":
                order = MarketOrder('BUY', QUANTITY)
            else:
                # פקודת Limit ב-1% מעל המחיר הנוכחי
                limit_price = current_price * 1.01
                order = LimitOrder('BUY', QUANTITY, limit_price)

            # שליחת פקודה
            trade = ibkr.ib.placeOrder(contract, order)

            print("✅ הפקודה נשלחה!")
            print(f"📋 Order ID: {trade.order.orderId}")
            print()

            # המתן למילוי
            print("⏳ ממתין למילוי הפקודה...")
            import time
            for i in range(10):
                ibkr.ib.sleep(1)

                if trade.orderStatus.status == 'Filled':
                    print("\n🎉 הפקודה מולאה!")
                    print(f"✅ קנית {QUANTITY} מניות {SYMBOL}")
                    print(f"💵 מחיר ממוצע: ${trade.orderStatus.avgFillPrice:.2f}")
                    break

                elif trade.orderStatus.status in ['Cancelled', 'ApiCancelled']:
                    print(f"\n❌ הפקודה בוטלה: {trade.orderStatus.status}")
                    break

                print(f"  סטטוס: {trade.orderStatus.status}...")

            else:
                print("\n⚠️  הפקודה עדיין לא מולאה")
                print(f"   סטטוס: {trade.orderStatus.status}")

            print()
            print("📊 כעת תוכל:")
            print("  1. לבדוק את הפוזיציה: python connect_ibkr.py")
            print("  2. לפתוח את הדשבורד ולמכור Covered Call")
            print("  3. לחפש Strike אופטימלי")

        else:
            print("\n⏭️  הפקודה בוטלה")

    else:
        print(f"❌ לא ניתן לקבל מחיר עבור {SYMBOL}")

    ibkr.disconnect()

except KeyboardInterrupt:
    print("\n\n⚠️  בוטל על ידי המשתמש")

except Exception as e:
    print(f"\n❌ שגיאה: {e}")
    import traceback
    traceback.print_exc()

print("\n👋 סיום\n")
