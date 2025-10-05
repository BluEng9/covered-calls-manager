#!/usr/bin/env python3
"""
📊 יצירת תיק השקעות מותאם אישית
Portfolio: TSLA, MSTR, IBIT, MSTY
"""

from ibkr_connector import IBKRConnector, IBKRConfig
from ib_async import Stock as IBStock, MarketOrder
import sys
import time

print("=" * 70)
print("📊 בניית תיק השקעות")
print("=" * 70)
print()

# הגדרת תיק
PORTFOLIO = {
    "TSLA": 300,   # Tesla
    "MSTR": 100,   # MicroStrategy
    "IBIT": 1000,  # iShares Bitcoin Trust
    "MSTY": 660    # YieldMax MSTR Option Income Strategy
}

print("📝 תיק ההשקעות:")
for symbol, qty in PORTFOLIO.items():
    print(f"  • {symbol}: {qty:,} מניות")
print()

# התחבר ל-IBKR
config = IBKRConfig(
    host="127.0.0.1",
    port=7497,  # Paper Trading
    client_id=2,  # Client ID 2 (הדשבורד משתמש ב-1)
    readonly=False  # נדרש למסחר
)

try:
    print("🔌 מתחבר ל-Interactive Brokers...")
    ibkr = IBKRConnector(config)

    if not ibkr.connect():
        print("❌ החיבור נכשל. וודא ש-TWS פועל עם API מופעל")
        sys.exit(1)

    print("✅ מחובר ל-TWS\n")

    # הצג נתוני חשבון נוכחיים
    account = ibkr.get_account_summary()
    if account:
        cash = account.get('TotalCashValue', 0)
        print(f"💰 מזומן זמין: ${cash:,.2f}\n")

    # חישוב עלות משוערת
    print("📊 בודק מחירים נוכחיים...\n")

    total_cost = 0
    prices = {}

    for symbol, quantity in PORTFOLIO.items():
        print(f"🔍 {symbol}...")
        price = ibkr.get_stock_price(symbol)

        if price:
            prices[symbol] = price
            cost = price * quantity
            total_cost += cost
            print(f"   מחיר: ${price:.2f}")
            print(f"   כמות: {quantity:,} מניות")
            print(f"   עלות: ${cost:,.2f}\n")
        else:
            print(f"   ⚠️  לא ניתן לקבל מחיר\n")

    print("=" * 70)
    print(f"💵 סה\"כ עלות משוערת: ${total_cost:,.2f}")
    print("=" * 70)
    print()

    if account and total_cost > cash:
        print(f"⚠️  אזהרה: העלות (${total_cost:,.2f}) גבוהה מהמזומן הזמין (${cash:,.2f})")
        print("   זה בסדר ב-Paper Trading, אבל במסחר אמיתי הפקודות עלולות להידחות")
        print()

    # אישור
    print("⚠️  זוהי פקודה ב-Paper Trading (לא כסף אמיתי)")
    confirm = input("\n❓ האם לבצע את כל הקניות? (yes/no): ")

    if confirm.lower() not in ['yes', 'y']:
        print("\n⏭️  הפעולה בוטלה")
        ibkr.disconnect()
        sys.exit(0)

    print("\n" + "=" * 70)
    print("🛒 מבצע קניות...")
    print("=" * 70)
    print()

    # ביצוע קניות
    trades = []

    for symbol, quantity in PORTFOLIO.items():
        print(f"📤 קונה {quantity:,} מניות {symbol}...")

        try:
            # יצירת חוזה
            contract = IBStock(symbol, 'SMART', 'USD')
            ibkr.ib.qualifyContracts(contract)

            # פקודת שוק
            order = MarketOrder('BUY', quantity)

            # שליחה
            trade = ibkr.ib.placeOrder(contract, order)
            trades.append((symbol, trade))

            print(f"   ✅ פקודה נשלחה (Order ID: {trade.order.orderId})")

        except Exception as e:
            print(f"   ❌ שגיאה: {e}")

        print()

    # המתן למילוי
    if trades:
        print("⏳ ממתין למילוי הפקודות...\n")

        for _ in range(15):  # נסה עד 15 שניות
            ibkr.ib.sleep(1)

            all_filled = True
            for symbol, trade in trades:
                if trade.orderStatus.status not in ['Filled', 'Cancelled', 'ApiCancelled']:
                    all_filled = False
                    break

            if all_filled:
                break

        # סיכום
        print("=" * 70)
        print("📋 סיכום פקודות:")
        print("=" * 70)
        print()

        filled_count = 0
        total_spent = 0

        for symbol, trade in trades:
            status = trade.orderStatus.status

            if status == 'Filled':
                filled_count += 1
                avg_price = trade.orderStatus.avgFillPrice
                quantity = trade.order.totalQuantity
                cost = avg_price * quantity
                total_spent += cost

                print(f"✅ {symbol}")
                print(f"   כמות: {quantity:,} מניות")
                print(f"   מחיר ממוצע: ${avg_price:.2f}")
                print(f"   עלות: ${cost:,.2f}")

            elif status in ['Cancelled', 'ApiCancelled']:
                print(f"❌ {symbol}")
                print(f"   סטטוס: {status}")

            else:
                print(f"⏳ {symbol}")
                print(f"   סטטוס: {status}")

            print()

        print("=" * 70)
        print(f"✅ {filled_count}/{len(trades)} פקודות מולאו")
        print(f"💵 סה\"כ הוצאה: ${total_spent:,.2f}")
        print("=" * 70)
        print()

    # הצג פוזיציות חדשות
    print("📊 פוזיציות נוכחיות בחשבון:\n")

    stocks = ibkr.get_stock_positions()

    if stocks:
        for stock in stocks:
            print(f"🏢 {stock.symbol}")
            print(f"   כמות: {stock.quantity:,} מניות")
            print(f"   מחיר ממוצע: ${stock.avg_cost:.2f}")
            print(f"   שווי: ${stock.market_value:,.2f}")

            # בדוק אפשרות Covered Calls
            contracts_available = stock.quantity // 100
            if contracts_available > 0:
                print(f"   ✅ ניתן למכור {contracts_available} חוזי Covered Call")
            else:
                print(f"   ⚠️  צריך {100 - stock.quantity} מניות נוספות לחוזה ראשון")

            print()

    print("🎯 צעדים הבאים:")
    print("  1. פתח את הדשבורד: http://localhost:8501")
    print("  2. התחבר ל-IBKR")
    print("  3. השתמש ב-Strategy Finder למציאת Strikes אופטימליים")
    print("  4. מכור Covered Calls על המניות")
    print()

    ibkr.disconnect()
    print("👋 התנתקות מ-IBKR")

except KeyboardInterrupt:
    print("\n\n⚠️  הפעולה בוטלה על ידי המשתמש")

except Exception as e:
    print(f"\n❌ שגיאה: {e}")
    import traceback
    traceback.print_exc()

print()
