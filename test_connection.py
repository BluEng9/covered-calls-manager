#!/usr/bin/env python3
"""Test IBKR connection"""

from ibkr_connector import IBKRConnector, IBKRConfig
import time

config = IBKRConfig(host='127.0.0.1', port=7497, client_id=10, readonly=False)
conn = IBKRConnector(config)

print('מנסה להתחבר ל-IBKR...')
if conn.connect():
    print('✅ מחובר בהצלחה!')
    print(f'מצב חיבור: {conn.connected}')

    # Get positions
    try:
        positions = conn.ib.positions()
        print(f'\n📊 נמצאו {len(positions)} פוזיציות:')
        for pos in positions:
            print(f'  {pos.contract.symbol}: {pos.position} @ ${pos.avgCost:.2f}')
    except Exception as e:
        print(f'❌ שגיאה בקבלת פוזיציות: {e}')

    conn.disconnect()
else:
    print('❌ החיבור נכשל')
