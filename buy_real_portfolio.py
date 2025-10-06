#!/usr/bin/env python3
"""
🛒 Buy Real Combined Portfolio in IBKR Paper Trading
קניית תיק האחזקות האמיתי מכל החשבונות
"""

from ibkr_connector import IBKRConnector, IBKRConfig
from ib_async import Stock, MarketOrder
import time
import csv

def load_portfolio_from_csv(csv_file: str):
    """Load and consolidate portfolio from CSV"""
    portfolio = {}

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row['Symbol']
            quantity = int(row['Quantity'])

            if symbol in portfolio:
                portfolio[symbol] += quantity
            else:
                portfolio[symbol] = quantity

    return portfolio

def main():
    print("🛒 Buying Real Combined Portfolio in IBKR Paper Trading")
    print("=" * 60)

    # Load portfolio from CSV
    csv_file = 'my_combined_portfolio.csv'
    portfolio = load_portfolio_from_csv(csv_file)

    print(f"\n📊 Portfolio from {csv_file}:")
    print("-" * 60)
    for symbol, quantity in portfolio.items():
        print(f"  {symbol}: {quantity} shares")
    print()

    # Connect to IBKR
    config = IBKRConfig(
        host="127.0.0.1",
        port=7497,
        client_id=4,
        readonly=False
    )

    connector = IBKRConnector(config)

    if not connector.connect():
        print("❌ Failed to connect to IBKR")
        return

    print("✅ Connected to IBKR Paper Trading")
    print()

    # Get current account info
    account = connector.get_account_summary()
    cash = account.get('TotalCashValue', 0)
    print(f"💰 Available Cash: ${cash:,.2f}")
    print()

    # Place orders for each position
    orders_placed = []
    total_estimated_cost = 0

    for symbol, quantity in portfolio.items():
        print(f"📊 Buying {quantity} shares of {symbol}...")

        try:
            # Create contract
            contract = Stock(symbol, 'SMART', 'USD')

            # Qualify the contract
            connector.ib.qualifyContracts(contract)

            # Get current market price
            ticker = connector.ib.reqMktData(contract)
            connector.ib.sleep(2)

            price = None
            if ticker.marketPrice():
                price = ticker.marketPrice()
                total_cost = price * quantity
                total_estimated_cost += total_cost
                print(f"  💵 Current Price: ${price:.2f}")
                print(f"  💰 Total Cost: ${total_cost:,.2f}")
            else:
                print(f"  ⚠️  Could not get market price for {symbol}")

            # Cancel market data subscription
            connector.ib.cancelMktData(contract)

            # Place market order
            order = MarketOrder('BUY', quantity)
            trade = connector.ib.placeOrder(contract, order)

            print(f"  ✅ Order placed: #{trade.order.orderId}")
            orders_placed.append({
                'symbol': symbol,
                'quantity': quantity,
                'order_id': trade.order.orderId,
                'estimated_price': price,
                'trade': trade
            })

            time.sleep(1)

        except Exception as e:
            print(f"  ❌ Error placing order for {symbol}: {e}")

        print()

    print("=" * 60)
    print(f"📋 Summary: {len(orders_placed)}/{len(portfolio)} orders placed")
    print(f"💰 Total Estimated Cost: ${total_estimated_cost:,.2f}")

    if total_estimated_cost > cash:
        print(f"⚠️  WARNING: Estimated cost (${total_estimated_cost:,.2f}) exceeds available cash (${cash:,.2f})")
        print(f"   Shortfall: ${total_estimated_cost - cash:,.2f}")
    else:
        print(f"✅ Sufficient cash available")
        print(f"   Remaining after purchase: ${cash - total_estimated_cost:,.2f}")

    print()

    # Wait for orders to process
    print("⏳ Waiting for orders to process...")
    time.sleep(5)

    # Check order status
    print("\n📊 Order Status:")
    print("-" * 60)

    for order_info in orders_placed:
        trade = order_info['trade']
        status = trade.orderStatus.status
        filled = trade.orderStatus.filled

        print(f"{order_info['symbol']:6} | Order #{order_info['order_id']:3} | Status: {status:12} | Filled: {filled:>4}/{order_info['quantity']:<4}")

    print()

    # Show final positions
    print("📦 Final Positions:")
    print("-" * 60)
    positions = connector.get_stock_positions()

    if positions:
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            qty = pos.get('quantity', 0)
            price = pos.get('current_price', 0)
            value = pos.get('market_value', 0)

            print(f"{symbol:6} | Qty: {qty:>4} | Price: ${price:>8.2f} | Value: ${value:>12,.2f}")
    else:
        print("  ⏳ No positions yet (orders may still be processing)")

    print()
    print("✅ Portfolio purchase process complete!")

    # Disconnect
    connector.disconnect()

if __name__ == "__main__":
    main()
