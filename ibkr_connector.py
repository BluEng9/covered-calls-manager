"""
Interactive Brokers Connector for Covered Calls System
Handles connection, data retrieval, and order execution with IBKR TWS/Gateway
"""

import asyncio
import nest_asyncio

# Fix for Python 3.13 event loop issue
nest_asyncio.apply()

from ib_async import *
from ib_async import Stock as IBStock  # Rename to avoid conflict
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import logging
from covered_calls_system import (
    Stock, OptionContract, OptionType, CoveredCall,
    PositionStatus, GreeksCalculator
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IBKRConfig:
    """IBKR connection configuration"""
    host: str = "127.0.0.1"
    port: int = 7497  # 7497 for TWS paper, 7496 for TWS live, 4002 for Gateway paper, 4001 for Gateway live
    client_id: int = 1
    readonly: bool = False  # Set True for read-only mode (no order execution)


class IBKRConnector:
    """Main connector class for Interactive Brokers"""

    def __init__(self, config: IBKRConfig = None):
        self.config = config or IBKRConfig()
        self.ib = IB()
        self.connected = False
        self._positions_cache = {}
        self._options_cache = {}

    def connect(self) -> bool:
        """Connect to IBKR TWS or Gateway"""
        # Check if already connected
        if self.ib.isConnected():
            logger.info("Already connected to IBKR")
            self.connected = True
            return True

        try:
            # Advanced fix for Streamlit asyncio event loop conflict
            # Streamlit runs in its own event loop, but ib_async needs its own
            import threading

            # Try to disconnect any existing connection first
            try:
                if hasattr(self.ib, '_loop') and self.ib._loop:
                    self.ib.disconnect()
            except:
                pass

            # Get or create event loop for this thread
            try:
                loop = asyncio.get_running_loop()
                # If we're in a running loop (Streamlit), we need to use run_in_executor
                # to avoid "loop already running" error
                logger.info("Detected running event loop (Streamlit)")

                # Create a new IB instance with fresh event loop
                self.ib = IB()

                # Use the synchronous connect with timeout
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self.ib.connect,
                        self.config.host,
                        self.config.port,
                        clientId=self.config.client_id,
                        readonly=self.config.readonly,
                        timeout=10
                    )
                    future.result(timeout=15)

            except RuntimeError:
                # No running loop, we can use connect normally
                logger.info("No running event loop, using direct connect")
                self.ib.connect(
                    self.config.host,
                    self.config.port,
                    clientId=self.config.client_id,
                    readonly=self.config.readonly,
                    timeout=10
                )

            self.connected = True
            logger.info(f"Connected to IBKR on {self.config.host}:{self.config.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    # ==================== Account & Portfolio ====================

    def get_account_summary(self) -> Dict:
        """Get account summary information"""
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        account_values = self.ib.accountSummary()
        summary = {}

        for av in account_values:
            if av.tag in ['NetLiquidation', 'TotalCashValue', 'BuyingPower',
                         'GrossPositionValue', 'UnrealizedPnL', 'RealizedPnL']:
                summary[av.tag] = float(av.value)

        return summary

    def get_stock_positions(self) -> List[Stock]:
        """Get all stock positions in account"""
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        positions = self.ib.positions()
        stocks = []

        for pos in positions:
            if isinstance(pos.contract, IBStock):
                # Get current market price
                ticker = self.ib.reqMktData(pos.contract)
                self.ib.sleep(1)  # Wait for data

                stock = Stock(
                    symbol=pos.contract.symbol,
                    quantity=int(pos.position),
                    avg_cost=pos.avgCost,
                    current_price=ticker.marketPrice() or ticker.close
                )
                stocks.append(stock)

        logger.info(f"Retrieved {len(stocks)} stock positions")
        return stocks

    def get_option_positions(self) -> List[Dict]:
        """Get all option positions"""
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        positions = self.ib.positions()
        options = []

        for pos in positions:
            if isinstance(pos.contract, Option):
                options.append({
                    'contract': pos.contract,
                    'position': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_value': pos.marketValue,
                    'unrealized_pnl': pos.unrealizedPNL
                })

        logger.info(f"Retrieved {len(options)} option positions")
        return options

    def get_covered_call_positions(self) -> List[Dict]:
        """
        Get covered call positions (matched stock holdings + short call options)

        Returns: List of dicts with:
            - symbol: Stock symbol
            - stock_qty: Number of shares held
            - stock_price: Current stock price
            - option_strike: Call option strike price
            - option_expiry: Expiration date
            - option_dte: Days to expiration
            - contracts: Number of option contracts (negative for short)
            - premium_received: Premium from selling the call
            - current_option_value: Current market value of option
            - unrealized_pnl: Unrealized P&L on the option
            - delta: Option delta
            - theta: Option theta
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        # Get all positions
        positions = self.ib.positions()

        # Separate stocks and options
        stocks = {}
        short_calls = []

        for pos in positions:
            if isinstance(pos.contract, IBStock):
                stocks[pos.contract.symbol] = {
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost,
                    'current_price': pos.marketPrice
                }
            elif isinstance(pos.contract, Option):
                if pos.contract.right == 'C' and pos.position < 0:  # Short call
                    short_calls.append({
                        'symbol': pos.contract.symbol,
                        'strike': pos.contract.strike,
                        'expiry': pos.contract.lastTradeDateOrContractMonth,
                        'contracts': pos.position,
                        'avg_cost': pos.avgCost,
                        'market_value': pos.marketValue,
                        'unrealized_pnl': pos.unrealizedPNL,
                        'contract': pos.contract
                    })

        # Match short calls with stock holdings (covered calls)
        covered_positions = []

        for call in short_calls:
            symbol = call['symbol']
            if symbol in stocks and stocks[symbol]['quantity'] >= abs(call['contracts']) * 100:
                # Calculate days to expiration
                from datetime import datetime
                expiry_str = call['expiry']
                expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
                dte = (expiry_date - datetime.now()).days

                # Get Greeks
                ticker = self.ib.reqMktData(call['contract'], '', False, False)
                self.ib.sleep(0.5)

                delta = getattr(ticker, 'modelGreeks', None)
                theta = getattr(ticker, 'modelGreeks', None)

                covered_positions.append({
                    'symbol': symbol,
                    'stock_qty': stocks[symbol]['quantity'],
                    'stock_price': stocks[symbol]['current_price'],
                    'option_strike': call['strike'],
                    'option_expiry': expiry_date,
                    'option_dte': dte,
                    'contracts': call['contracts'],
                    'premium_received': -call['avg_cost'] * abs(call['contracts']) * 100,
                    'current_option_value': call['market_value'],
                    'unrealized_pnl': call['unrealized_pnl'],
                    'delta': delta.delta if delta else None,
                    'theta': delta.theta if delta else None
                })

        logger.info(f"Retrieved {len(covered_positions)} covered call positions")
        return covered_positions

    # ==================== Market Data ====================

    def get_stock_price(self, symbol: str, exchange: str = "SMART") -> float:
        """Get current stock price"""
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        contract = IBStock(symbol, exchange, 'USD')
        ticker = self.ib.reqMktData(contract, '', False, False)
        self.ib.sleep(1)

        price = ticker.marketPrice() or ticker.last or ticker.close
        return price

    def get_option_chain(self, symbol: str, exchange: str = "SMART") -> pd.DataFrame:
        """
        Get full option chain for a symbol

        Returns: DataFrame with all available strikes and expirations
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        stock = IBStock(symbol, exchange, 'USD')
        self.ib.qualifyContracts(stock)

        # Get option chain
        chains = self.ib.reqSecDefOptParams(stock.symbol, '', stock.secType, stock.conId)

        if not chains:
            logger.warning(f"No option chain found for {symbol}")
            return pd.DataFrame()

        chain = chains[0]
        expirations = sorted(chain.expirations)
        strikes = sorted(chain.strikes)

        logger.info(f"Retrieved option chain for {symbol}: "
                   f"{len(expirations)} expirations, {len(strikes)} strikes")

        return pd.DataFrame({
            'symbol': symbol,
            'expirations': [expirations],
            'strikes': [strikes],
            'exchange': chain.exchange
        })

    def get_options_for_expiration(
        self,
        symbol: str,
        expiration: str,
        option_type: OptionType = OptionType.CALL,
        exchange: str = "SMART"
    ) -> List[OptionContract]:
        """
        Get all options for specific expiration

        Args:
            symbol: Stock symbol
            expiration: Expiration date in format 'YYYYMMDD'
            option_type: CALL or PUT
            exchange: Exchange (default SMART)

        Returns: List of OptionContract objects with Greeks
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        # Get available strikes
        chain_df = self.get_option_chain(symbol, exchange)
        if chain_df.empty:
            return []

        strikes = chain_df.iloc[0]['strikes']

        # Create option contracts
        right = 'C' if option_type == OptionType.CALL else 'P'
        contracts = [
            Option(symbol, expiration, strike, right, exchange)
            for strike in strikes
        ]

        # Qualify contracts (get full contract details)
        qualified = self.ib.qualifyContracts(*contracts)

        # Request market data and Greeks
        options_list = []
        for contract in qualified:
            try:
                # Request market data with Greeks
                ticker = self.ib.reqMktData(
                    contract,
                    genericTickList='',
                    snapshot=False,
                    regulatorySnapshot=False
                )
                self.ib.sleep(0.5)  # Brief pause for data

                # Get Greeks from model calculation if not available from IBKR
                greeks = ticker.modelGreeks
                if not greeks:
                    greeks = ticker.lastGreeks

                option = OptionContract(
                    symbol=symbol,
                    strike=contract.strike,
                    expiration=datetime.strptime(contract.lastTradeDateOrContractMonth, '%Y%m%d'),
                    option_type=option_type,
                    premium=ticker.marketPrice() or ticker.last or 0,
                    implied_volatility=greeks.impliedVol * 100 if greeks else 0,
                    delta=greeks.delta if greeks else 0,
                    gamma=greeks.gamma if greeks else 0,
                    theta=greeks.theta if greeks else 0,
                    vega=greeks.vega if greeks else 0,
                    volume=ticker.volume or 0,
                    open_interest=ticker.openInterest or 0,
                    bid=ticker.bid or 0,
                    ask=ticker.ask or 0
                )
                options_list.append(option)

            except Exception as e:
                logger.warning(f"Failed to get data for strike {contract.strike}: {e}")
                continue

        logger.info(f"Retrieved {len(options_list)} options for {symbol} {expiration}")
        return options_list

    def get_otm_calls(
        self,
        symbol: str,
        current_price: float,
        days_to_expiration: int = 30,
        min_dte: int = 7,
        max_dte: int = 60
    ) -> List[OptionContract]:
        """
        Get out-of-the-money call options

        Args:
            symbol: Stock symbol
            current_price: Current stock price
            days_to_expiration: Target days to expiration
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration

        Returns: List of OTM call options
        """
        # Get option chain
        chain_df = self.get_option_chain(symbol)
        if chain_df.empty:
            return []

        expirations = chain_df.iloc[0]['expirations']

        # Filter expirations by DTE
        target_date = datetime.now() + timedelta(days=days_to_expiration)
        min_date = datetime.now() + timedelta(days=min_dte)
        max_date = datetime.now() + timedelta(days=max_dte)

        valid_expirations = [
            exp for exp in expirations
            if min_date <= datetime.strptime(exp, '%Y%m%d') <= max_date
        ]

        if not valid_expirations:
            logger.warning(f"No expirations found in range {min_dte}-{max_dte} days")
            return []

        # Get closest expiration to target
        target_exp = min(
            valid_expirations,
            key=lambda x: abs((datetime.strptime(x, '%Y%m%d') - target_date).days)
        )

        # Get all options for that expiration
        all_options = self.get_options_for_expiration(symbol, target_exp, OptionType.CALL)

        # Filter OTM options (strike > current price)
        otm_options = [opt for opt in all_options if opt.strike > current_price]

        logger.info(f"Found {len(otm_options)} OTM calls for {symbol} expiring {target_exp}")
        return otm_options

    # ==================== Order Execution ====================

    def sell_covered_call(
        self,
        symbol: str,
        quantity: int,
        strike: float,
        expiration: str,
        limit_price: Optional[float] = None,
        exchange: str = "SMART"
    ) -> Optional[Trade]:
        """
        Sell covered call (open position)

        Args:
            symbol: Stock symbol
            quantity: Number of contracts
            strike: Strike price
            expiration: Expiration date 'YYYYMMDD'
            limit_price: Limit price (optional, use None for market order)
            exchange: Exchange

        Returns: Trade object or None if failed
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        if self.config.readonly:
            logger.warning("Read-only mode - order not submitted")
            return None

        # Create option contract
        contract = Option(symbol, expiration, strike, 'C', exchange)
        self.ib.qualifyContracts(contract)

        # Create sell order
        if limit_price:
            order = LimitOrder('SELL', quantity, limit_price)
        else:
            order = MarketOrder('SELL', quantity)

        # Submit order
        try:
            trade = self.ib.placeOrder(contract, order)
            logger.info(f"Submitted covered call sell order: {symbol} {strike}C @ {limit_price or 'market'}")
            return trade
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            return None

    def buy_to_close(
        self,
        symbol: str,
        quantity: int,
        strike: float,
        expiration: str,
        limit_price: Optional[float] = None,
        exchange: str = "SMART"
    ) -> Optional[Trade]:
        """
        Buy to close option position

        Args:
            symbol: Stock symbol
            quantity: Number of contracts
            strike: Strike price
            expiration: Expiration date 'YYYYMMDD'
            limit_price: Limit price (optional)
            exchange: Exchange

        Returns: Trade object or None
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        if self.config.readonly:
            logger.warning("Read-only mode - order not submitted")
            return None

        contract = Option(symbol, expiration, strike, 'C', exchange)
        self.ib.qualifyContracts(contract)

        if limit_price:
            order = LimitOrder('BUY', quantity, limit_price)
        else:
            order = MarketOrder('BUY', quantity)

        try:
            trade = self.ib.placeOrder(contract, order)
            logger.info(f"Submitted buy-to-close order: {symbol} {strike}C @ {limit_price or 'market'}")
            return trade
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            return None

    def roll_call(
        self,
        symbol: str,
        quantity: int,
        old_strike: float,
        old_expiration: str,
        new_strike: float,
        new_expiration: str,
        net_credit_limit: float,
        exchange: str = "SMART"
    ) -> Optional[List[Trade]]:
        """
        Roll covered call (close old, open new)

        Args:
            symbol: Stock symbol
            quantity: Number of contracts
            old_strike: Current strike
            old_expiration: Current expiration
            new_strike: New strike
            new_expiration: New expiration
            net_credit_limit: Minimum net credit required
            exchange: Exchange

        Returns: List of [buy_trade, sell_trade] or None
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        if self.config.readonly:
            logger.warning("Read-only mode - orders not submitted")
            return None

        # Get current prices
        old_contract = Option(symbol, old_expiration, old_strike, 'C', exchange)
        new_contract = Option(symbol, new_expiration, new_strike, 'C', exchange)

        self.ib.qualifyContracts(old_contract, new_contract)

        old_ticker = self.ib.reqMktData(old_contract)
        new_ticker = self.ib.reqMktData(new_contract)
        self.ib.sleep(1)

        # Calculate net credit
        buyback_cost = old_ticker.ask
        new_premium = new_ticker.bid
        net_credit = new_premium - buyback_cost

        if net_credit < net_credit_limit:
            logger.warning(
                f"Net credit {net_credit:.2f} below limit {net_credit_limit:.2f} - roll not executed"
            )
            return None

        # Execute roll
        try:
            buy_order = MarketOrder('BUY', quantity)
            buy_trade = self.ib.placeOrder(old_contract, buy_order)

            sell_order = MarketOrder('SELL', quantity)
            sell_trade = self.ib.placeOrder(new_contract, sell_order)

            logger.info(
                f"Rolled {symbol}: {old_strike}C {old_expiration} -> {new_strike}C {new_expiration} "
                f"for net credit ${net_credit:.2f}"
            )

            return [buy_trade, sell_trade]

        except Exception as e:
            logger.error(f"Failed to roll position: {e}")
            return None

    # ==================== Historical Data ====================

    def get_historical_data(
        self,
        symbol: str,
        duration: str = "1 Y",
        bar_size: str = "1 day",
        what_to_show: str = "TRADES"
    ) -> pd.DataFrame:
        """
        Get historical price data

        Args:
            symbol: Stock symbol
            duration: Duration string (e.g., "1 Y", "6 M", "30 D")
            bar_size: Bar size (e.g., "1 day", "1 hour", "5 mins")
            what_to_show: Data type (TRADES, MIDPOINT, BID, ASK)

        Returns: DataFrame with OHLCV data
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        contract = IBStock(symbol, 'SMART', 'USD')
        self.ib.qualifyContracts(contract)

        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=True
        )

        df = util.df(bars)
        logger.info(f"Retrieved {len(df)} bars of historical data for {symbol}")
        return df

    def get_implied_volatility_history(
        self,
        symbol: str,
        strike: float,
        expiration: str,
        duration: str = "30 D"
    ) -> pd.DataFrame:
        """Get historical implied volatility for an option"""
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        contract = Option(symbol, expiration, strike, 'C', 'SMART')
        self.ib.qualifyContracts(contract)

        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting='1 day',
            whatToShow='OPTION_IMPLIED_VOLATILITY',
            useRTH=True
        )

        df = util.df(bars)
        logger.info(f"Retrieved IV history for {symbol} {strike}C")
        return df

    # ==================== Utilities ====================

    def get_open_orders(self) -> List[Trade]:
        """Get all open orders"""
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        trades = self.ib.openTrades()
        logger.info(f"Found {len(trades)} open orders")
        return trades

    def cancel_order(self, order: Order) -> bool:
        """Cancel an order"""
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        try:
            self.ib.cancelOrder(order)
            logger.info(f"Cancelled order {order.orderId}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False

    def get_contract_details(self, symbol: str, sec_type: str = "STK") -> List:
        """Get detailed contract information"""
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")

        if sec_type == "STK":
            contract = IBStock(symbol, 'SMART', 'USD')
        else:
            contract = Contract(symbol=symbol, secType=sec_type)

        details = self.ib.reqContractDetails(contract)
        return details


# Example usage and testing
if __name__ == "__main__":
    # Configuration for paper trading
    config = IBKRConfig(
        host="127.0.0.1",
        port=7497,  # TWS paper trading port
        client_id=1,
        readonly=True  # Set to True for testing
    )

    # Use context manager for automatic connection/disconnection
    with IBKRConnector(config) as ibkr:
        # Get account info
        account = ibkr.get_account_summary()
        print("\n=== Account Summary ===")
        for key, value in account.items():
            print(f"{key}: ${value:,.2f}")

        # Get stock positions
        stocks = ibkr.get_stock_positions()
        print(f"\n=== Stock Positions ({len(stocks)}) ===")
        for stock in stocks:
            print(f"{stock.symbol}: {stock.quantity} shares @ ${stock.avg_cost:.2f}")
            print(f"  Current: ${stock.current_price:.2f} | P&L: ${stock.unrealized_pnl:.2f} ({stock.unrealized_pnl_pct:.2f}%)")

        # Example: Get option chain for AAPL
        if stocks:
            symbol = stocks[0].symbol
            print(f"\n=== Getting OTM Calls for {symbol} ===")
            otm_calls = ibkr.get_otm_calls(symbol, stocks[0].current_price, days_to_expiration=30)

            print(f"Found {len(otm_calls)} OTM calls")
            for opt in otm_calls[:5]:  # Show top 5
                print(f"Strike ${opt.strike:.2f} | Premium: ${opt.premium:.2f} | "
                      f"Delta: {opt.delta:.3f} | IV: {opt.implied_volatility:.1f}% | "
                      f"DTE: {opt.days_to_expiration}")
