# Trade Execution Module

Production-ready trade execution engine for covered calls trading through Interactive Brokers.

## Quick Start

```python
from trade_execution import TradeExecutor
from ibkr_connector import IBKRConnector, IBKRConfig

# Initialize
config = IBKRConfig()
ibkr = IBKRConnector(config)
ibkr.connect()

executor = TradeExecutor(ibkr)

# Sell a covered call
result = executor.sell_covered_call(
    symbol="AAPL",
    strike=185.0,
    expiration="20250117",  # YYYYMMDD format
    contracts=2,
    limit_price=2.50
)

if result.success:
    print(f"✅ Order placed! ID: {result.order_id}")
    print(f"   Status: {result.status}")
else:
    print(f"❌ Error: {result.error}")
```

## Features

- ✅ **Share Ownership Verification** - Prevents naked calls
- ✅ **Contract Qualification** - Validates option exists
- ✅ **Dry Run Mode** - Test without executing
- ✅ **Comprehensive Logging** - Full audit trail
- ✅ **Order Lifecycle Management** - Track, cancel, monitor
- ✅ **Error Handling** - Detailed error messages

## API Reference

### TradeExecutor.sell_covered_call()

Primary method for selling covered calls.

**Parameters:**
- `symbol` (str): Stock symbol (e.g., "AAPL")
- `strike` (float): Option strike price
- `expiration` (str): Expiration date in YYYYMMDD format
- `contracts` (int): Number of contracts to sell
- `limit_price` (float, optional): Limit price (None for market order)
- `dry_run` (bool, optional): If True, validate but don't execute

**Returns:** `ExecutionResult`

**Example:**
```python
result = executor.sell_covered_call(
    symbol="TSLA",
    strike=250.0,
    expiration="20250214",
    contracts=1,
    limit_price=5.00,
    dry_run=True  # Test first
)
```

### ExecutionResult

**Attributes:**
- `success` (bool): Whether execution succeeded
- `status` (ExecutionStatus): Current order status
- `order_id` (int): IBKR order ID
- `filled_quantity` (int): Contracts filled
- `average_fill_price` (float): Average fill price
- `commission` (float): Commission paid
- `message` (str): Status message
- `error` (str): Error message if failed
- `trade_object` (Trade): Raw IBKR trade object

### ExecutionLogger

Logs all trades to JSONL files (one per day).

```python
from trade_execution import ExecutionLogger

logger = ExecutionLogger()

# Get today's trades
trades = logger.get_trades()

# Get summary
summary = logger.get_summary()
print(f"Total trades: {summary['total_trades']}")
print(f"Covered calls sold: {summary['covered_calls_sold']}")
```

## Testing

Run integration tests:

```bash
python tests/trade_execution/test_trade_executor_integration.py
```

## Log Files

Trade logs are stored in `execution_logs/`:
- Format: `trades_YYYY-MM-DD.jsonl`
- One JSON object per line
- Includes all trade details and timestamps

## Error Handling

The module handles:
- Connection failures
- Insufficient shares
- Invalid contracts
- Market closed
- Order rejections

All errors return `ExecutionResult` with `success=False` and detailed `error` message.

## Requirements

- IBKR TWS or Gateway running
- ib_async library
- Active IBKR account with trading permissions

## Next Steps

See `PROJECT_MEMORY.md` for:
- Additional modules to implement (order_manager, position_tracker, risk_checks)
- Integration with dashboard
- Live trading setup
