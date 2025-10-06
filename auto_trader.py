"""
Auto-Trader for Covered Calls
Automated scanning and execution of covered call strategies

Features:
- Daily portfolio scanning
- Automatic strike selection based on criteria
- Trade execution with safety checks
- Logging and notifications
- Scheduler for hands-free operation
"""

import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass

from covered_calls_system import CoveredCallStrategy, RiskLevel
from ibkr_connector import IBKRConnector
from safety_features import PreTradeValidator, TradingMode
from trade_analytics import TradeDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AutoTraderConfig:
    """Configuration for auto-trader"""
    min_annual_return: float = 20.0  # Minimum annualized return %
    max_delta: float = 0.35          # Maximum delta (risk)
    min_delta: float = 0.20          # Minimum delta
    min_dte: int = 25                # Minimum days to expiration
    max_dte: int = 35                # Maximum days to expiration
    min_premium_dollars: float = 50.0  # Minimum premium per contract
    schedule_time: str = "10:00"     # Daily run time (ET)
    max_trades_per_day: int = 5      # Safety limit
    dry_run: bool = True             # Test mode (no actual trades)
    enable_notifications: bool = True  # Send trade notifications


class AutoTrader:
    """Automated Covered Call Trading System"""

    def __init__(self,
                 connector: IBKRConnector,
                 config: AutoTraderConfig = None):
        self.connector = connector
        self.config = config or AutoTraderConfig()
        self.strategy = CoveredCallStrategy()
        self.validator = PreTradeValidator()
        self.db = TradeDatabase()
        self.trades_today = 0

    def daily_scan_and_trade(self):
        """Main daily trading routine"""
        logger.info("=" * 60)
        logger.info(f"🔍 [{datetime.now()}] Starting daily auto-scan...")
        logger.info("=" * 60)

        # Reset daily counter
        self.trades_today = 0

        # Connect to IBKR
        if not self.connector.connected:
            logger.info("📡 Connecting to IBKR...")
            if not self.connector.connect():
                logger.error("❌ Failed to connect to IBKR")
                return

        # Get account summary
        summary = self.connector.get_account_summary()
        logger.info(f"💰 Account: ${summary.get('NetLiquidation', 0):,.2f}")

        # Get stock positions
        positions = self.connector.get_stock_positions()
        logger.info(f"📊 Found {len(positions)} stock positions\n")

        # Scan each position
        for position in positions:
            try:
                self._process_position(position)
            except Exception as e:
                logger.error(f"❌ Error processing {position.symbol}: {e}")
                continue

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ Daily scan complete - {self.trades_today} trades executed")
        logger.info("=" * 60)

    def _process_position(self, position):
        """Process a single stock position"""
        symbol = position.symbol
        shares = position.quantity
        price = position.current_price

        logger.info(f"📈 {symbol}: {shares} shares @ ${price:.2f}")

        # Check if enough shares for covered call
        if shares < 100:
            logger.info(f"   ⏭️  Skip: Need at least 100 shares (have {shares})")
            return

        # Check if already has covered call
        if self._has_covered_call(symbol):
            logger.info(f"   ⏭️  Skip: Already has active covered call")
            return

        # Check if close to earnings
        if self._near_earnings(symbol):
            logger.info(f"   ⏭️  Skip: Too close to earnings date")
            return

        # Find best opportunities
        opportunities = self.strategy.find_best_strikes(
            symbol=symbol,
            current_price=price,
            position_size=shares,
            dte_min=self.config.min_dte,
            dte_max=self.config.max_dte,
            risk_level=RiskLevel.MODERATE
        )

        if not opportunities:
            logger.info(f"   ⏭️  Skip: No suitable options found")
            return

        # Get best opportunity
        best = opportunities[0]
        annual_return = best.get('annualized_return', 0)
        delta = best.get('delta', 0)
        premium_total = best.get('premium', 0)

        logger.info(f"   🎯 Best strike: ${best['strike']:.2f}")
        logger.info(f"   💵 Premium: ${premium_total:.2f} ({annual_return:.1f}% annual)")
        logger.info(f"   📊 Delta: {delta:.3f} | DTE: {best['dte']}")

        # Check criteria
        if not self._meets_criteria(best):
            logger.info(f"   ⏭️  Skip: Doesn't meet criteria")
            return

        # Check daily limit
        if self.trades_today >= self.config.max_trades_per_day:
            logger.info(f"   ⏭️  Skip: Daily trade limit reached ({self.config.max_trades_per_day})")
            return

        # Execute trade
        self._execute_trade(symbol, shares, best)

    def _meets_criteria(self, opportunity: Dict) -> bool:
        """Check if opportunity meets trading criteria"""
        annual_return = opportunity.get('annualized_return', 0)
        delta = opportunity.get('delta', 0)
        premium = opportunity.get('premium', 0)

        # Check minimum return
        if annual_return < self.config.min_annual_return:
            logger.debug(f"   Annual return {annual_return:.1f}% < {self.config.min_annual_return:.1f}%")
            return False

        # Check delta range
        if not (self.config.min_delta <= delta <= self.config.max_delta):
            logger.debug(f"   Delta {delta:.3f} outside range [{self.config.min_delta}-{self.config.max_delta}]")
            return False

        # Check minimum premium
        if premium < self.config.min_premium_dollars:
            logger.debug(f"   Premium ${premium:.2f} < ${self.config.min_premium_dollars:.2f}")
            return False

        return True

    def _execute_trade(self, symbol: str, shares: int, opportunity: Dict):
        """Execute covered call trade"""
        contracts = shares // 100
        strike = opportunity['strike']
        expiration = opportunity['expiration']
        premium = opportunity['premium']
        delta = opportunity['delta']
        dte = opportunity['dte']

        logger.info(f"\n   🚀 EXECUTING TRADE:")
        logger.info(f"   Symbol: {symbol}")
        logger.info(f"   Contracts: {contracts}")
        logger.info(f"   Strike: ${strike:.2f}")
        logger.info(f"   Expiration: {expiration}")
        logger.info(f"   Premium: ${premium:.2f}")

        # DRY RUN MODE
        if self.config.dry_run:
            logger.info(f"   ⚠️  DRY RUN - No actual trade executed")
            self._log_simulated_trade(symbol, opportunity, contracts)
            return

        # SAFETY VALIDATION
        validation = self.validator.validate_covered_call(
            symbol=symbol,
            strike=strike,
            expiration_date=expiration,
            contracts=contracts,
            current_price=opportunity.get('current_price', 0),
            delta=delta,
            premium_per_contract=premium / contracts,
            dte=dte,
            mode=TradingMode.LIVE
        )

        if not validation['approved']:
            logger.warning(f"   ❌ Trade rejected by validator:")
            for msg in validation['messages']:
                logger.warning(f"      - {msg}")
            return

        # EXECUTE REAL TRADE
        try:
            result = self.connector.sell_covered_call(
                symbol=symbol,
                contracts=contracts,
                strike=strike,
                expiration=expiration,
                limit_price=premium / contracts  # Price per contract
            )

            if result and result.get('success'):
                logger.info(f"   ✅ Trade executed successfully!")
                logger.info(f"   Order ID: {result.get('order_id')}")

                # Log to database
                self._log_trade(symbol, opportunity, contracts, result)

                # Send notification
                if self.config.enable_notifications:
                    self._send_notification(
                        f"✅ Auto-Trader: Sold {contracts}x {symbol} ${strike:.2f} Call\n"
                        f"Premium: ${premium:.2f} ({opportunity['annualized_return']:.1f}% annual)"
                    )

                self.trades_today += 1
            else:
                logger.error(f"   ❌ Trade failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"   ❌ Trade execution error: {e}")

    def _has_covered_call(self, symbol: str) -> bool:
        """Check if symbol already has an active covered call"""
        try:
            open_positions = self.db.get_open_positions()
            for pos in open_positions:
                if pos.get('symbol') == symbol and pos.get('type') == 'covered_call':
                    return True
            return False
        except:
            return False

    def _near_earnings(self, symbol: str) -> bool:
        """Check if stock is close to earnings announcement"""
        try:
            from earnings_calendar import EarningsCalendar
            calendar = EarningsCalendar()

            # Check next 45 days
            next_earnings = calendar.get_next_earnings(symbol)
            if next_earnings:
                days_until = (next_earnings - datetime.now()).days
                if days_until < 45:
                    logger.info(f"   ⚠️  Earnings in {days_until} days")
                    return True
            return False
        except:
            # If earnings check fails, be conservative
            return False

    def _log_trade(self, symbol: str, opportunity: Dict, contracts: int, result: Dict):
        """Log trade to database"""
        try:
            self.db.add_trade(
                symbol=symbol,
                trade_type='covered_call',
                strike=opportunity['strike'],
                expiration=opportunity['expiration'],
                contracts=contracts,
                premium=opportunity['premium'],
                delta=opportunity.get('delta'),
                dte=opportunity.get('dte'),
                order_id=result.get('order_id'),
                metadata={
                    'auto_traded': True,
                    'annualized_return': opportunity.get('annualized_return'),
                    'executed_at': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to log trade: {e}")

    def _log_simulated_trade(self, symbol: str, opportunity: Dict, contracts: int):
        """Log simulated trade (dry run mode)"""
        logger.info(f"   📝 Simulated trade logged")
        # Could optionally write to CSV or separate log file

    def _send_notification(self, message: str):
        """Send notification (email/telegram/etc)"""
        # TODO: Implement notification system
        logger.info(f"📧 Notification: {message}")

    def start_scheduler(self, run_now: bool = False):
        """Start automated trading scheduler"""
        logger.info("=" * 60)
        logger.info("🤖 AUTO-TRADER STARTING")
        logger.info("=" * 60)
        logger.info(f"Schedule: Daily at {self.config.schedule_time} ET")
        logger.info(f"Min Annual Return: {self.config.min_annual_return}%")
        logger.info(f"Delta Range: {self.config.min_delta:.2f} - {self.config.max_delta:.2f}")
        logger.info(f"DTE Range: {self.config.min_dte} - {self.config.max_dte} days")
        logger.info(f"Mode: {'DRY RUN' if self.config.dry_run else 'LIVE TRADING'}")
        logger.info("=" * 60)

        # Schedule daily run
        schedule.every().day.at(self.config.schedule_time).do(self.daily_scan_and_trade)

        # Run immediately if requested
        if run_now:
            logger.info("🚀 Running initial scan now...")
            self.daily_scan_and_trade()

        # Main loop
        logger.info(f"\n⏰ Waiting for next scheduled run at {self.config.schedule_time}...")
        while True:
            schedule.run_pending()
            time.sleep(60)

    def run_once(self):
        """Run trading routine once (for testing)"""
        self.daily_scan_and_trade()


def main():
    """Example usage"""
    from ibkr_connector import IBKRConnector, IBKRConfig

    # Create configuration
    config = AutoTraderConfig(
        min_annual_return=25.0,  # Require 25% annualized
        max_delta=0.35,          # Max 35 delta
        min_delta=0.20,          # Min 20 delta
        min_dte=25,
        max_dte=35,
        min_premium_dollars=50,
        schedule_time="10:00",   # 10 AM ET daily
        max_trades_per_day=5,
        dry_run=True,            # Start in test mode!
        enable_notifications=True
    )

    # Create IBKR connector
    ibkr_config = IBKRConfig(
        host='127.0.0.1',
        port=7497,  # Paper trading
        client_id=1,
        readonly=False  # Need write access for trading
    )
    connector = IBKRConnector(ibkr_config)

    # Create auto-trader
    trader = AutoTrader(connector, config)

    # Start with immediate run
    trader.start_scheduler(run_now=True)


if __name__ == "__main__":
    main()
