# 🚀 פרויקטים מומלצים מ-GitHub לשילוב במערכת

## 📊 סקירה כללית

מצאתי **10 פרויקטים מעולים** שיכולים לשפר את מערכת ה-Covered Calls שלך. להלן רשימה מסודרת לפי עדיפות.

---

## 🏆 שילובים מומלצים - עדיפות גבוהה

### 1️⃣ ib_async - IBKR API משופר ⭐⭐⭐⭐⭐

**Repository:** https://github.com/ib-api-reloaded/ib_async
**Stars:** 1,047 ⭐
**Last Updated:** October 2025

**מה זה עושה:**
- Successor ל-ib_insync (שאתה משתמש בו עכשיו)
- תמיכה מודרנית ב-async/await
- תיקוני באגים ועדכונים שוטפים
- תמיכה בכל פיצ'רים החדשים של IBKR

**למה להשתמש בזה:**
✅ יותר יציב ומתוחזק
✅ API זהה - שינוי קל
✅ ביצועים טובים יותר
✅ קהילה פעילה

**איך להתקין:**
```bash
cd ~/Projects/TradingBots/covered-calls-manager
source venv/bin/activate
pip uninstall ib-insync
pip install ib-async
```

**שינויים נדרשים בקוד:**
```python
# Before
from ib_insync import *

# After
from ib_async import *
```

**קושי:** 🟢 קל (5 דקות)

---

### 2️⃣ blackscholes - Greeks Calculator מתקדם ⭐⭐⭐⭐⭐

**Repository:** https://github.com/CarloLepelaars/blackscholes
**Stars:** 54 ⭐
**Last Updated:** September 2025

**מה זה עושה:**
- חישוב Greeks מדויק (Delta, Gamma, Vega, Theta, Rho)
- Greeks מסדר גבוה (Vanna, Charm, Speed, Zomma, Color)
- Black-Scholes מדויק יותר מהמימוש שלך

**למה להשתמש בזה:**
✅ Greeks יותר מדויקים
✅ ניהול סיכונים טוב יותר
✅ תמיכה ב-Greeks מתקדמים
✅ ביצועים מהירים

**איך להתקין:**
```bash
pip install blackscholes
```

**דוגמת שימוש:**
```python
from blackscholes import BlackScholes

# חישוב Greeks
bs = BlackScholes(
    S=430,      # Stock price
    K=450,      # Strike
    T=30/365,   # Time to expiration (years)
    r=0.05,     # Risk-free rate
    sigma=0.40  # IV
)

print(f"Delta: {bs.delta():.3f}")
print(f"Gamma: {bs.gamma():.4f}")
print(f"Theta: {bs.theta():.2f}")
print(f"Vega: {bs.vega():.2f}")
print(f"Rho: {bs.rho():.2f}")

# Higher-order Greeks
print(f"Vanna: {bs.vanna():.4f}")
print(f"Charm: {bs.charm():.4f}")
```

**קושי:** 🟢 קל (10 דקות)

---

### 3️⃣ Python_Option_Pricing - IV & Pricing Models ⭐⭐⭐⭐

**Repository:** https://github.com/dedwards25/Python_Option_Pricing
**Stars:** 791 ⭐
**Last Updated:** October 2025

**מה זה עושה:**
- חישוב Implied Volatility מדויק
- מודלים מרובים: Black-Scholes, Black 76, Binomial
- תמיכה באופציות American ו-European
- תמיכה ב-Spreads

**למה להשתמש בזה:**
✅ בחירת Strike חכמה יותר על סמך IV
✅ השוואת מחירים תיאורטיים למחירי שוק
✅ זיהוי אופציות מתומחרות לא נכון
✅ אופטימיזציה של אסטרטגיה

**איך להתקין:**
```bash
pip install py_vollib
```

**דוגמת שימוש:**
```python
from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes.implied_volatility import implied_volatility

# חישוב IV מהשוק
market_price = 8.50
iv = implied_volatility(
    price=market_price,
    S=430,      # Stock price
    K=450,      # Strike
    t=30/365,   # Time
    r=0.05,     # Risk-free rate
    flag='c'    # 'c' for call
)

print(f"Implied Volatility: {iv*100:.1f}%")

# חישוב מחיר תיאורטי
theoretical_price = black_scholes(
    flag='c',
    S=430,
    K=450,
    t=30/365,
    r=0.05,
    sigma=iv
)

print(f"Theoretical Price: ${theoretical_price:.2f}")
print(f"Market Price: ${market_price:.2f}")
print(f"Difference: ${theoretical_price - market_price:.2f}")
```

**קושי:** 🟡 בינוני (30 דקות)

---

## 🎯 שילובים נוספים - עדיפות בינונית

### 4️⃣ optopsy - Backtesting Library ⭐⭐⭐⭐

**Repository:** https://github.com/michaelchu/optopsy
**Stars:** 1,191 ⭐

**מה זה עושה:**
- Backtesting של אסטרטגיות Covered Calls
- בדיקת ביצועים היסטוריים
- אופטימיזציה של פרמטרים

**למה להשתמש בזה:**
✅ בדוק אסטרטגיה לפני מסחר אמיתי
✅ מצא DTE ו-Strike אופטימליים
✅ השווה אסטרטגיות שונות

**קושי:** 🟡 בינוני (דורש נתונים היסטוריים)

---

### 5️⃣ ibkr-options-volatility-trading - Alert System ⭐⭐⭐

**Repository:** https://github.com/mcf-long-short/ibkr-options-volatility-trading
**Stars:** 319 ⭐

**מה זה עושה:**
- בוט שסורק הזדמנויות מסחר
- התראות Email/Slack
- ניטור תנודתיות

**למה להשתמש בזה:**
✅ קבל התראות אוטומטיות על הזדמנויות
✅ ניטור פוזיציות 24/7
✅ אל תפספס הזדמנויות

**קושי:** 🟡 בינוני

---

### 6️⃣ Harvest - Multi-Broker Framework ⭐⭐⭐

**Repository:** https://github.com/tfukaza/harvest
**Stars:** 143 ⭐

**מה זה עושה:**
- תמיכה במספר ברוקרים (IBKR, Robinhood, Alpaca)
- Paper Trading מובנה
- Framework לפיתוח אלגו

**למה להשתמש בזה:**
✅ גיוון בין ברוקרים
✅ Paper Trading קל יותר
✅ Framework מסודר

**קושי:** 🟢 קל

---

## 📚 משאבים נוספים

### 7️⃣ awesome-systematic-trading - Resource List ⭐⭐⭐⭐⭐

**Repository:** https://github.com/wangzhe3224/awesome-systematic-trading
**Stars:** 3,112 ⭐

**מה זה עושה:**
- רשימה אדירה של משאבים למסחר
- ספריות, כלים, APIs
- מדריכים ומאמרים

**למה להשתמש בזה:**
✅ גלה כלים חדשים
✅ למד אסטרטגיות מתקדמות
✅ התחבר לקהילה

---

## 🛠️ תוכנית שילוב מומלצת

### שלב 1: שיפורים מיידיים (היום/מחר)

```bash
# 1. התקן blackscholes
pip install blackscholes

# 2. התקן py_vollib
pip install py_vollib

# 3. שפר את covered_calls_system.py
# הוסף Greeks מדויקים יותר
```

### שלב 2: שדרוג IBKR (השבוע)

```bash
# Upgrade ל-ib_async
pip uninstall ib-insync
pip install ib-async

# עדכן את ibkr_connector.py
# שנה imports
```

### שלב 3: Backtesting (חודש הבא)

```bash
# התקן optopsy
pip install optopsy

# צור סקריפט backtesting
# הורד נתונים היסטוריים
# בדוק אסטרטגיות
```

---

## 💡 המלצות שימוש

### ל-TSLA Covered Calls:

1. **השתמש ב-blackscholes** לחישוב Greeks מדויק:
   - Delta אמיתי לבחירת Strike
   - Theta לחישוב רווח יומי
   - Vega למניעת הפתעות IV

2. **השתמש ב-py_vollib** לזיהוי הזדמנויות:
   - IV גבוה = פרמיה טובה
   - השווה IV בין Strikes שונים
   - מצא אופציות מתומחרות יתר

3. **שקול Backtesting**:
   - בדוק ביצועי 30 vs 45 DTE
   - בדוק ביצועי OTM 5% vs 10%
   - מצא את ה-sweet spot

---

## 📦 קובץ requirements.txt מעודכן

```text
# Current dependencies
numpy>=1.24.0
scipy>=1.10.0
pandas>=2.0.0
streamlit>=1.28.0
plotly>=5.17.0
pytest>=7.4.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0

# IBKR Integration (choose one)
# ib-insync>=0.9.86  # Current (legacy)
ib-async>=1.0.0      # Recommended upgrade

# NEW: Advanced Greeks
blackscholes>=1.0.0

# NEW: IV Calculations
py-vollib>=1.0.1

# OPTIONAL: Backtesting
# optopsy>=1.0.0

# OPTIONAL: Multi-broker
# harvest-python>=0.1.0

# Helper libraries
nest-asyncio>=1.5.0  # For Python 3.13 compatibility
```

---

## 🎯 סיכום

**התקן עכשיו:**
1. ✅ `blackscholes` - Greeks טובים יותר
2. ✅ `py_vollib` - IV analysis
3. ✅ `ib_async` - IBKR משודרג

**שקול בעתיד:**
4. 📊 `optopsy` - Backtesting
5. 🔔 `ibkr-options-volatility-trading` - Alerts
6. 🌐 `Harvest` - Multi-broker

**לקריאה:**
7. 📚 `awesome-systematic-trading` - Resources

---

## 📞 צעדים הבאים

1. **התקן את 3 הראשונים:**
   ```bash
   cd ~/Projects/TradingBots/covered-calls-manager
   source venv/bin/activate
   pip install blackscholes py-vollib ib-async
   ```

2. **שפר את covered_calls_system.py:**
   - החלף Greeks Calculator ב-blackscholes
   - הוסף IV analysis עם py_vollib

3. **שדרג IBKR connector:**
   - החלף ib_insync ב-ib_async

4. **בדוק במחיר אמיתי מחר:**
   - הרץ את analyze_tsla_options.py
   - השווה תוצאות

---

**בהצלחה! 🚀📈**
