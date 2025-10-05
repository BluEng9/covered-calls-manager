# 🚀 מדריך התחלה מהירה - Covered Calls Manager

## 📍 הדשבורד נפתח ב: http://localhost:8501

---

## 🎯 שלב 1: התחברות ל-IBKR

### בסרגל הצדי (Sidebar):

1. **Host:** `127.0.0.1` (כבר מלא)
2. **Port:** `7497` (TWS Paper Trading)
3. **Client ID:** `1` (כבר מלא)
4. **Read-only mode:** ✅ סמן (מומלץ לבדיקות)

5. **לחץ:** 🔌 **Connect to IBKR**

### ✅ אם החיבור הצליח:
- תראה הודעה "Connected to IBKR"
- נתוני החשבון יופיעו בחלק העליון

### ❌ אם יש שגיאה:
- ✓ בדוק ש-TWS פועל
- ✓ בדוק ש-API מופעל (Configuration → API → Settings)
- ✓ וודא שהפורט נכון (7497 ל-Paper)

---

## 🛒 שלב 2: קניית מניות (אופציונלי)

**אם אין לך מניות בחשבון:**

### דרך 1: דרך TWS ישירות
1. פתח TWS
2. Mosaic → New Window → Order Entry
3. קנה 100 מניות (AAPL, MSFT, SPY...)

### דרך 2: דרך הסקריפט שלנו
```bash
cd ~/Projects/TradingBots/covered-calls-manager
source venv/bin/activate
python buy_stock_example.py
```

---

## 📊 שלב 3: שימוש בדשבורד

### 📈 Account Overview
- **Net Liquidation:** סך הנכסים שלך
- **Total Cash:** מזומן פנוי
- **Unrealized P&L:** רווח/הפסד לא ממומש
- **Realized P&L:** רווח/הפסד ממומש

### 💼 Portfolio Summary
- **Active Positions:** כמות פוזיציות Covered Call פעילות
- **Total Stock Value:** שווי כל המניות
- **Premium Collected:** פרמיה שנגבתה
- **Portfolio Return:** תשואה צפויה אם הכל יוקצה

### ⚠️ Alerts & Notifications
**סוגי התראות:**
- 🔴 **ASSIGNMENT_RISK** - המניה ITM, סיכון להקצאה
- 🟡 **EXPIRATION_SOON** - פוזיציה קרובה לתפוגה (7 ימים)
- 🟢 **LOW_LIQUIDITY** - נזילות נמוכה

### 📋 Active Positions
**טבלה עם כל הפוזיציות:**
- Symbol, Strike, Expiration
- Premium, Max Profit, Return
- Delta, IV, DTE
- 📥 כפתור להורדה כ-CSV

### 📅 Expiration Calendar
**פוזיציות לפי תאריך תפוגה:**
- מקובצות לפי יום
- סטטוס של כל פוזיציה
- 🔴/🟢 אינדיקטור סיכון

---

## 🎯 שלב 4: Strategy Finder - מציאת Strike אופטימלי

### בחלק "Strategy Finder":

1. **בחר מניה** מהרשימה (אם יש לך מניות)

2. **הגדר פרמטרים:**
   - **Target DTE:** 30 (30 ימים לתפוגה - מומלץ)
   - **Number of Results:** 5

3. **לחץ:** 🔍 **Find Best Strikes**

### 📊 מה תקבל:
המערכת תציג את 5 ה-Strikes הטובים ביותר עם:

- **Strike Price:** מחיר ההקצאה
- **Score:** ציון 0-100 (ככל שגבוה יותר - טוב יותר)
- **Premium:** הפרמיה שתקבל
- **Greeks:** Delta, Theta, IV
- **Returns:** תשואה רגילה ושנתית

### 💡 איך לבחור:
- **Conservative:** Strike גבוה, Delta נמוך (0.15-0.25), פרמיה קטנה
- **Moderate:** Strike בינוני, Delta 0.25-0.35, פרמיה סבירה ⭐ מומלץ
- **Aggressive:** Strike נמוך, Delta גבוה (0.35-0.50), פרמיה גבוהה

---

## 📈 שלב 5: Performance Analytics

### 🔷 Returns Distribution
- גרף עמודות של תשואות צפויות
- השוואה בין תשואה רגילה לשנתית

### 🔷 Greeks Exposure
- סך Delta של הפורטפוליו
- סך Theta (רווח יומי מדעיכת זמן)

### 🔷 Expiration Timeline
- ציר זמן של תפוגות
- גודל הבועה = DTE
- צבע = מניה שונה

---

## 🎓 טיפים למתחילים

### ✅ עשה:
1. **התחל ב-Paper Trading** - תרגל ללא סיכון
2. **Strike 3-5% OTM** - מעל המחיר הנוכחי
3. **30-45 DTE** - sweet spot לתשואה
4. **Delta 0.25-0.35** - סיכון מאוזן
5. **מניות יציבות** - AAPL, MSFT, SPY
6. **בדוק נזילות** - Volume > 1,000, OI > 5,000
7. **הגדר התראות** - עקוב אחר פוזיציות

### ❌ אל תעשה:
1. **אל תמכור ITM** - Strike מתחת למחיר
2. **אל תתעלם מדיבידנדים** - בדוק ex-dividend date
3. **אל תמכור לפני ארועים** - Earnings, FDA approvals
4. **אל תרדוף פרמיה** - IV גבוה = סיכון
5. **אל תשכח לגלגל** - עקוב בשבוע לפני תפוגה

---

## 🔄 Rolling (גלגול פוזיציה)

### מתי לגלגל:
- ✅ המניה קרובה ל-Strike (< 5%)
- ✅ 7-14 ימים לפני תפוגה
- ✅ אתה רוצה להמשיך להחזיק במניה

### איך לגלגל:
1. **Buy to Close** - קנה בחזרה את ה-Call הישן
2. **Sell to Open** - מכור Call חדש (תפוגה מאוחרת יותר)
3. **נטו:** רוצים קרדיט (לקבל כסף), לא דביט

### בדשבורד:
- המערכת תתריע אם צריך לגלגל
- תראה חישוב של net credit

---

## 🧮 הבנת המדדים

### Return if Assigned (תשואה אם מוקצה)
```
= (Strike - Avg Cost) × 100 + Premium
  ------------------------------------ × 100%
        Avg Cost × 100
```

### Annualized Return (תשואה שנתית)
```
= Return if Assigned × (365 / DTE)
```

### Breakeven Price (מחיר איזון)
```
= Avg Cost - (Premium / 100)
```

### Downside Protection (הגנה מפני ירידה)
```
= (Premium / Current Price) × 100%
```

---

## 🆘 פתרון בעיות

### לא מצליח להתחבר ל-IBKR?
1. ✓ TWS פועל?
2. ✓ API מופעל? (Configuration → API → Settings)
3. ✓ "Enable ActiveX and Socket Clients" מסומן?
4. ✓ הפורט נכון? (7497 Paper, 7496 Live)
5. ✓ לא סומן "Read-Only API"?

### לא רואה מניות?
1. ✓ יש לך מניות בחשבון?
2. ✓ התחברת בהצלחה?
3. ✓ נסה לרענן (F5)

### לא מוצא אופציות?
1. ✓ יש לך לפחות 100 מניות?
2. ✓ המניה תומכת באופציות?
3. ✓ Market Data מחובר? (ב-TWS)

### הפקודה לא עוברת?
1. ✓ Read-only mode מכובה?
2. ✓ יש מספיק מניות?
3. ✓ Market Hours? (9:30-16:00 EST)

---

## 📞 עזרה נוספת

### תיעוד מלא:
```bash
cat README.md  # מדריך מלא באנגלית
```

### דוגמאות קוד:
```bash
python example_usage.py  # 7 דוגמאות מקיפות
```

### בדיקת חיבור:
```bash
python connect_ibkr.py  # בדיקה מהירה של חיבור
```

### לוגים:
- TWS Logs: Help → Log Viewer
- Python Errors: טרמינל שבו הדשבורד רץ

---

## 🎉 מוכן להתחיל!

1. ✅ התחבר ל-TWS (אם עדיין לא)
2. ✅ פתח http://localhost:8501
3. ✅ התחבר בדשבורד
4. ✅ קנה מניות (אם צריך)
5. ✅ מצא Strike אופטימלי
6. ✅ מכור Covered Call!

**בהצלחה! 📈💰**

---

*⚠️ אזהרה: זהו כלי לימודי. לא ייעוץ פינסי. סחר כרוך בסיכון.*
