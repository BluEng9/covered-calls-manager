#!/usr/bin/env python3
"""
🛒 Buy Demo Portfolio in IBKR Paper Trading
קניית תיק הדמו בחשבון Paper Trading
"""

from ibkr_connector import IBKRConnector, IBKRConfig
from ib_async import Stock, MarketOrder
import time

# Portfolio from demo system
PORTFOLIO = [
    {'symbol': 'AAPL', 'quantity': 300},
    {'symbol': 'MSFT', 'quantity': 200},
    {'symbol': 'NVDA', 'quantity': 100},
    {'symbol': 'TSLA', 'quantity': 400},
    {'symbol': 'GOOGL', 'quantity': 150},
    {'symbol': 'MSTR', 'quantity': 200},
    {'symbol': 'AMZN', 'quantity': 250},
    {'symbol': 'META', 'quantity': 150},
]

def main():
    print("🛒 Buying Demo Portfolio in IBKR Paper Trading")
    print("=" * 60)

    # Connect to IBKR
    config = IBKRConfig(
        host="127.0.0.1",
        port=7497,
        client_id=2,  # Different client ID to avoid conflicts
        readonly=False  # Need to place orders
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

    for position in PORTFOLIO:
        symbol = position['symbol']
        quantity = position['quantity']

        print(f"📊 Buying {quantity} shares of {symbol}...")

        try:
            # Create contract
            contract = Stock(symbol, 'SMART', 'USD')

            # Qualify the contract
            connector.ib.qualifyContracts(contract)

            # Get current market price
            ticker = connector.ib.reqMktData(contract)
            connector.ib.sleep(2)  # Wait for market data

            if ticker.marketPrice():
                price = ticker.marketPrice()
                total_cost = price * quantity
                print(f"  💵 Current Price: ${price:.2f}")
                print(f"  💰 Total Cost: ${total_cost:,.2f}")
            else:
                print(f"  ⚠️  Could not get market price for {symbol}")

            # Cancel market data subscription
            connector.ib.cancelMktData(contract)

            # Place market order
            order = MarketOrder('BUY', quantity)
            trade = connector.ib.placeOrder(contract, order)

            print(f"  ✅ Order placed: {trade.order.orderId}")
            orders_placed.append({
                'symbol': symbol,
                'quantity': quantity,
                'order_id': trade.order.orderId,
                'trade': trade
            })

            # Wait a bit between orders
            time.sleep(1)

        except Exception as e:
            print(f"  ❌ Error placing order for {symbol}: {e}")

        print()

    print("=" * 60)
    print(f"📋 Summary: {len(orders_placed)}/{len(PORTFOLIO)} orders placed")
    print()

    # Wait for orders to fill
    print("⏳ Waiting for orders to fill...")
    time.sleep(5)

    # Check order status
    print("\n📊 Order Status:")
    print("-" * 60)

    for order_info in orders_placed:
        trade = order_info['trade']
        status = trade.orderStatus.status
        filled = trade.orderStatus.filled

        print(f"{order_info['symbol']:6} | Status: {status:10} | Filled: {filled}/{order_info['quantity']}")

    print()

    # Show final positions
    print("📦 Final Positions:")
    print("-" * 60)
    positions = connector.get_stock_positions()

    for pos in positions:
        symbol = pos.get('symbol', 'N/A')
        qty = pos.get('quantity', 0)
        price = pos.get('current_price', 0)
        value = pos.get('market_value', 0)

        print(f"{symbol:6} | Qty: {qty:>4} | Price: ${price:>8.2f} | Value: ${value:>12,.2f}")

    print()
    print("✅ Portfolio purchase complete!")

    # Disconnect
    connector.disconnect()

if __name__ == "__main__":
    main()
