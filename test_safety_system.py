#!/usr/bin/env python3
"""
Test script for safety features
Demonstrates pre-trade validation
"""

from safety_features import SafetyManager, TradingMode
from earnings_calendar import EarningsCalendar

print("=" * 60)
print("🛡️  SAFETY FEATURES TEST")
print("=" * 60)

# Test 1: SafetyManager validation
print("\n1️⃣  Testing SafetyManager...")
manager = SafetyManager(mode=TradingMode.PAPER)

# Good trade
print("\n✅ Testing VALID trade:")
good_trade = {
    'symbol': 'AAPL',
    'contracts': 2,
    'delta': 0.30,
    'dte': 30,
    'premium': 2.50,
    'strike': 185.0
}

approved, messages = manager.pre_trade_validation(good_trade)
for msg in messages:
    print(f"  {msg}")
print(f"\n  Result: {'✅ APPROVED' if approved else '❌ REJECTED'}")

# Bad trade - too many contracts
print("\n❌ Testing INVALID trade (too many contracts):")
bad_trade = {
    'symbol': 'AAPL',
    'contracts': 15,  # Exceeds limit of 10
    'delta': 0.30,
    'dte': 30,
    'premium': 2.50,
    'strike': 185.0
}

approved, messages = manager.pre_trade_validation(bad_trade)
for msg in messages:
    print(f"  {msg}")
print(f"\n  Result: {'✅ APPROVED' if approved else '❌ REJECTED'}")

# Test 2: Earnings Calendar
print("\n\n2️⃣  Testing Earnings Calendar...")
calendar = EarningsCalendar()

test_symbols = ['AAPL', 'TSLA', 'MSFT']
for symbol in test_symbols:
    print(f"\n📅 {symbol}:")
    result = calendar.check_before_trade(symbol, dte=30)
    print(f"  Safe: {result['safe']}")
    print(f"  Reason: {result['reason']}")
    if result['earnings_date']:
        print(f"  Earnings: {result['earnings_date']}")

# Test 3: Safety Summary
print("\n\n3️⃣  Safety System Summary:")
summary = manager.get_safety_summary()
print(f"\n  Mode: {summary['mode']}")
print(f"  Trades today: {summary['todays_trades']}/{summary['max_daily_trades']}")
print(f"  Trades remaining: {summary['trades_remaining']}")
print("\n  Limits:")
for key, value in summary['limits'].items():
    print(f"    {key}: {value}")

print("\n" + "=" * 60)
print("✅ All tests completed!")
print("=" * 60)
