#!/usr/bin/env python3
"""
Quick test script to verify IBKR connection and data retrieval
"""
import sys
from ibkr_connector import IBKRConnector, IBKRConfig

def test_connection():
    """Test IBKR connection outside of Streamlit"""
    print("=" * 60)
    print("Testing IBKR Connection")
    print("=" * 60)

    # Create config for paper trading
    config = IBKRConfig(
        host='127.0.0.1',
        port=7497,  # Paper trading port
        client_id=1,
        readonly=True
    )

    print(f"\n📡 Config: {config.host}:{config.port} (client_id={config.client_id})")

    # Create connector
    connector = IBKRConnector(config)
    print(f"📦 Created connector - id={id(connector)}")

    # Connect
    print("\n🔗 Connecting...")
    if not connector.connect():
        print("❌ Connection failed!")
        return False

    print(f"✅ Connected! connector.connected={connector.connected}")
    print(f"   Connector instance ID: {id(connector)}")

    # Test account summary
    print("\n📊 Fetching account summary...")
    try:
        summary = connector.get_account_summary()
        print(f"✅ Account summary retrieved:")
        for key, value in summary.items():
            print(f"   {key}: ${value:,.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    # Test positions
    print("\n📈 Fetching stock positions...")
    try:
        positions = connector.get_stock_positions()
        print(f"✅ Found {len(positions)} stock positions")
        for pos in positions:
            print(f"   {pos.symbol}: {pos.quantity} shares @ ${pos.current_price:.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Disconnect
    print("\n🔌 Disconnecting...")
    connector.disconnect()
    print("✅ Disconnected")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
