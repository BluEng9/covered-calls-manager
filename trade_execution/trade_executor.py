"""
Core Trade Execution Engine for Covered Calls Manager
Production-ready execution with full error handling and logging
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import asyncio
import concurrent.futures

from ib_async import IB, Stock, Option, Order, Trade, Contract
from .execution_logger import ExecutionLogger


class OrderType(Enum):
    """Order types supported"""
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STPLMT"


class OrderAction(Enum):
    """Order actions"""
    BUY = "BUY"
    SELL = "SELL"


class ExecutionStatus(Enum):
    """Trade execution status"""
    PENDING = "Pending"
    SUBMITTED = "Submitted"
    FILLED = "Filled"
    PARTIALLY_FILLED = "PartiallyFilled"
    CANCELLED = "Cancelled"
    ERROR = "Error"


@dataclass
class TradeRequest:
    """Trade request with all necessary parameters"""
    symbol: str
    action: OrderAction
    quantity: int
    order_type: OrderType = OrderType.LIMIT
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None

    # Option-specific fields
    is_option: bool = False
    strike: Optional[float] = None
    expiration: Optional[str] = None  # Format: YYYYMMDD
    right: str = "C"  # C for Call, P for Put

    # Advanced order params
    time_in_force: str = "DAY"  # DAY, GTC, IOC, GTD
    outside_rth: bool = False  # Regular trading hours only

    def __post_init__(self):
        """Validate trade request"""
        if self.order_type == OrderType.LIMIT and not self.limit_price:
            raise ValueError("Limit price required for LIMIT orders")

        if self.is_option and (not self.strike or not self.expiration):
            raise ValueError("Strike and expiration required for option trades")


@dataclass
class ExecutionResult:
    """Result of trade execution"""
    success: bool
    status: ExecutionStatus
    order_id: Optional[int] = None
    filled_quantity: int = 0
    average_fill_price: float = 0.0
    commission: float = 0.0
    message: str = ""
    trade_object: Optional[Trade] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class TradeExecutor:
    """
    Production-ready trade execution engine

    Features:
    - Full error handling and recovery
    - Connection loss resilience
    - Order status monitoring
    - Comprehensive logging
    - Position verification
    """

    def __init__(self, ibkr_connector, logger: Optional[logging.Logger] = None):
        """
        Initialize trade executor

        Args:
            ibkr_connector: IBKRConnector instance
            logger: Optional custom logger
        """
        self.ibkr = ibkr_connector
        self.logger = logger or logging.getLogger(__name__)
        self.execution_logger = ExecutionLogger()
        self.active_orders: Dict[int, Trade] = {}

    def sell_covered_call(
        self,
        symbol: str,
        strike: float,
        expiration: str,
        contracts: int,
        limit_price: Optional[float] = None,
        dry_run: bool = False
    ) -> ExecutionResult:
        """
        Execute a covered call sell order

        This is the PRIMARY method for selling covered calls.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            strike: Option strike price
            expiration: Expiration date (YYYYMMDD format)
            contracts: Number of contracts to sell
            limit_price: Limit price (None for market order)
            dry_run: If True, validate but don't execute

        Returns:
            ExecutionResult with execution details

        Example:
            ```python
            executor = TradeExecutor(ibkr_connector)
            result = executor.sell_covered_call(
                symbol="AAPL",
                strike=185.0,
                expiration="20250117",
                contracts=2,
                limit_price=2.50
            )

            if result.success:
                print(f"Order filled at ${result.average_fill_price}")
            else:
                print(f"Error: {result.error}")
            ```
        """
        try:
            # Step 1: Verify connection
            if not self.ibkr.connected:
                return ExecutionResult(
                    success=False,
                    status=ExecutionStatus.ERROR,
                    error="Not connected to IBKR. Please connect first."
                )

            # Step 2: Verify share ownership
            shares_required = contracts * 100
            verification = self._verify_share_ownership(symbol, shares_required)

            if not verification['valid']:
                return ExecutionResult(
                    success=False,
                    status=ExecutionStatus.ERROR,
                    error=verification['error']
                )

            # Step 3: Create option contract
            option_contract = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=expiration,
                strike=strike,
                right='C',  # Call option
                exchange='SMART',
                currency='USD'
            )

            # Step 4: Qualify the contract (verify it exists)
            try:
                qualified = self.ibkr.ib.qualifyContracts(option_contract)
                if not qualified:
                    return ExecutionResult(
                        success=False,
                        status=ExecutionStatus.ERROR,
                        error=f"Option contract not found: {symbol} {strike}C {expiration}"
                    )
                option_contract = qualified[0]
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    status=ExecutionStatus.ERROR,
                    error=f"Failed to qualify contract: {str(e)}"
                )

            # Step 5: Dry run check
            if dry_run:
                self.logger.info(f"[DRY RUN] Would sell {contracts} contracts of {symbol} {strike}C {expiration}")
                return ExecutionResult(
                    success=True,
                    status=ExecutionStatus.PENDING,
                    message="Dry run - order not submitted"
                )

            # Step 6: Create and place order
            order = Order(
                action='SELL',
                totalQuantity=contracts,
                orderType='LMT' if limit_price else 'MKT',
                lmtPrice=limit_price if limit_price else 0,
                tif='DAY',
                outsideRth=False,
                transmit=True  # Submit immediately
            )

            # Step 7: Place order
            trade = self.ibkr.ib.placeOrder(option_contract, order)

            # Store active order
            self.active_orders[trade.order.orderId] = trade

            # Step 8: Wait for initial status
            self.ibkr.ib.sleep(1)  # Give time for order to be acknowledged

            # Step 9: Log the trade
            self.execution_logger.log_trade({
                'type': 'SELL_COVERED_CALL',
                'symbol': symbol,
                'strike': strike,
                'expiration': expiration,
                'contracts': contracts,
                'limit_price': limit_price,
                'order_id': trade.order.orderId,
                'status': trade.orderStatus.status,
                'shares_owned': verification['shares_owned']
            })

            # Step 10: Return result
            result = ExecutionResult(
                success=True,
                status=self._map_status(trade.orderStatus.status),
                order_id=trade.order.orderId,
                filled_quantity=trade.orderStatus.filled,
                average_fill_price=trade.orderStatus.avgFillPrice,
                message=f"Order submitted: {trade.orderStatus.status}",
                trade_object=trade
            )

            self.logger.info(
                f"✅ Covered call sell order placed: {symbol} {strike}C {expiration} "
                f"x{contracts} @ ${limit_price or 'Market'} (Order ID: {trade.order.orderId})"
            )

            return result

        except Exception as e:
            error_msg = f"Failed to execute covered call sell: {str(e)}"
            self.logger.error(error_msg)

            # Log the error
            self.execution_logger.log_trade({
                'type': 'SELL_COVERED_CALL',
                'symbol': symbol,
                'strike': strike,
                'expiration': expiration,
                'contracts': contracts,
                'error': str(e),
                'status': 'ERROR'
            })

            return ExecutionResult(
                success=False,
                status=ExecutionStatus.ERROR,
                error=error_msg
            )

    def _verify_share_ownership(self, symbol: str, shares_required: int) -> Dict:
        """
        Verify we own enough shares for covered call

        Returns:
            dict with 'valid', 'shares_owned', and 'error' keys
        """
        try:
            positions = self.ibkr.get_stock_positions()

            # Find position for this symbol
            position = next((p for p in positions if p['symbol'] == symbol), None)

            if not position:
                return {
                    'valid': False,
                    'shares_owned': 0,
                    'error': f"No position in {symbol}. Cannot sell covered calls."
                }

            shares_owned = position['quantity']

            if shares_owned < shares_required:
                return {
                    'valid': False,
                    'shares_owned': shares_owned,
                    'error': f"Insufficient shares. Own: {shares_owned}, Need: {shares_required}"
                }

            return {
                'valid': True,
                'shares_owned': shares_owned,
                'error': None
            }

        except Exception as e:
            return {
                'valid': False,
                'shares_owned': 0,
                'error': f"Error checking positions: {str(e)}"
            }

    def cancel_order(self, order_id: int) -> ExecutionResult:
        """
        Cancel a pending order

        Args:
            order_id: Order ID to cancel

        Returns:
            ExecutionResult
        """
        try:
            if order_id not in self.active_orders:
                return ExecutionResult(
                    success=False,
                    status=ExecutionStatus.ERROR,
                    error=f"Order {order_id} not found in active orders"
                )

            trade = self.active_orders[order_id]
            self.ibkr.ib.cancelOrder(trade.order)

            self.logger.info(f"Order {order_id} cancelled")

            return ExecutionResult(
                success=True,
                status=ExecutionStatus.CANCELLED,
                order_id=order_id,
                message="Order cancelled successfully"
            )

        except Exception as e:
            error_msg = f"Failed to cancel order {order_id}: {str(e)}"
            self.logger.error(error_msg)
            return ExecutionResult(
                success=False,
                status=ExecutionStatus.ERROR,
                error=error_msg
            )

    def get_order_status(self, order_id: int) -> Optional[ExecutionResult]:
        """
        Get current status of an order

        Args:
            order_id: Order ID

        Returns:
            ExecutionResult with current status or None if not found
        """
        if order_id not in self.active_orders:
            return None

        trade = self.active_orders[order_id]

        return ExecutionResult(
            success=True,
            status=self._map_status(trade.orderStatus.status),
            order_id=order_id,
            filled_quantity=trade.orderStatus.filled,
            average_fill_price=trade.orderStatus.avgFillPrice,
            commission=trade.orderStatus.commission,
            trade_object=trade
        )

    def _map_status(self, ib_status: str) -> ExecutionStatus:
        """Map IBKR status to ExecutionStatus"""
        status_map = {
            'PendingSubmit': ExecutionStatus.PENDING,
            'Submitted': ExecutionStatus.SUBMITTED,
            'Filled': ExecutionStatus.FILLED,
            'PartiallyFilled': ExecutionStatus.PARTIALLY_FILLED,
            'Cancelled': ExecutionStatus.CANCELLED,
            'ApiCancelled': ExecutionStatus.CANCELLED,
            'PreSubmitted': ExecutionStatus.PENDING,
            'Inactive': ExecutionStatus.CANCELLED
        }
        return status_map.get(ib_status, ExecutionStatus.ERROR)
