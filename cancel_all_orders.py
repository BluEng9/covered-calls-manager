#!/usr/bin/env python3
"""
❌ Cancel All Orders in IBKR Paper Trading
ביטול כל ההזמנות בחשבון Paper Trading
"""

from ibkr_connector import IBKRConnector, IBKRConfig
import time

def main():
    print("❌ Canceling All Orders in IBKR Paper Trading")
    print("=" * 60)

    # Connect to IBKR
    config = IBKRConfig(
        host="127.0.0.1",
        port=7497,
        client_id=3,
        readonly=False
    )

    connector = IBKRConnector(config)

    if not connector.connect():
        print("❌ Failed to connect to IBKR")
        return

    print("✅ Connected to IBKR Paper Trading")
    print()

    # Get all open orders
    trades = connector.ib.reqAllOpenOrders()
    connector.ib.sleep(2)

    open_orders = connector.ib.openTrades()

    if not open_orders:
        print("ℹ️  No open orders to cancel")
        connector.disconnect()
        return

    print(f"📋 Found {len(open_orders)} open orders")
    print()

    # Cancel each order
    for trade in open_orders:
        order_id = trade.order.orderId
        symbol = trade.contract.symbol
        action = trade.order.action
        quantity = trade.order.totalQuantity
        status = trade.orderStatus.status

        print(f"Canceling Order #{order_id}: {action} {quantity} {symbol} (Status: {status})")

        try:
            connector.ib.cancelOrder(trade.order)
            print(f"  ✅ Canceled")
        except Exception as e:
            print(f"  ❌ Error: {e}")

        time.sleep(0.5)

    print()
    print("=" * 60)
    print("✅ All orders canceled")

    # Verify
    time.sleep(2)
    remaining = connector.ib.openTrades()
    print(f"\n📊 Remaining open orders: {len(remaining)}")

    connector.disconnect()

if __name__ == "__main__":
    main()
