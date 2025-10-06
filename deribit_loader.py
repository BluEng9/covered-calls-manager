"""
Deribit Connector for Crypto Options Trading
Handles connection, data retrieval for BTC/ETH options from Deribit
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import logging
from deribit_wrapper import DeribitClient

from covered_calls_system import (
    Stock, OptionContract, OptionType, CoveredCall,
    PositionStatus, GreeksCalculator
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeribitConfig:
    """Deribit connection configuration"""
    env: str = 'test'  # 'test' for testnet, 'prod' for mainnet
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    simulated: bool = True  # True for simulated trading


class DeribitConnector:
    """Main connector class for Deribit crypto options exchange"""

    def __init__(self, config: DeribitConfig = None):
        self.config = config or DeribitConfig()
        self.client = None
        self.connected = False
        self._positions_cache = {}
        self._options_cache = {}

    def connect(self) -> bool:
        """Connect to Deribit API"""
        try:
            # Initialize Deribit client
            self.client = DeribitClient(
                env=self.config.env,
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                simulated=self.config.simulated
            )

            # Test connection by getting BTC index
            try:
                index = self.client.get_index_price(index_name="btc_usd")
                logger.info(f"✅ Connected to Deribit ({self.config.env}) - BTC Index: ${index['index_price']:,.2f}")
                self.connected = True
                return True
            except Exception as e:
                logger.error(f"❌ Connection test failed: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to connect to Deribit: {e}")
            return False

    def disconnect(self):
        """Disconnect from Deribit"""
        self.connected = False
        self.client = None
        logger.info("Disconnected from Deribit")

    def get_crypto_positions(self) -> Dict[str, Dict]:
        """
        Get current crypto positions (BTC, ETH)
        Returns dict with symbol -> {quantity, avg_cost, current_price}
        """
        if not self.connected or not self.client:
            logger.error("Not connected to Deribit")
            return {}

        positions = {}

        try:
            # Get BTC and ETH positions
            for currency in ['BTC', 'ETH']:
                try:
                    pos_data = self.client.get_positions(currency=currency)

                    for pos in pos_data:
                        if pos['size'] != 0:  # Only active positions
                            # Calculate current price from mark price
                            mark_price = pos.get('mark_price', 0)

                            positions[currency] = {
                                'quantity': abs(pos['size']),  # Convert to positive
                                'avg_cost': pos.get('average_price', 0),
                                'current_price': mark_price,
                                'pnl': pos.get('total_profit_loss', 0),
                                'direction': 'long' if pos['size'] > 0 else 'short'
                            }

                            logger.info(f"📊 {currency}: {pos['size']} @ ${mark_price:,.2f}")

                except Exception as e:
                    logger.warning(f"Could not get {currency} positions: {e}")

        except Exception as e:
            logger.error(f"Error fetching crypto positions: {e}")

        return positions

    def get_available_options(self, currency: str = 'BTC',
                            min_dte: int = 7, max_dte: int = 90) -> List[OptionContract]:
        """
        Get available options for a cryptocurrency

        Args:
            currency: 'BTC' or 'ETH'
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration
        """
        if not self.connected or not self.client:
            logger.error("Not connected to Deribit")
            return []

        options = []

        try:
            # Get all instruments for currency
            instruments = self.client.get_instruments(currency=currency, kind='option')

            current_time = datetime.utcnow()

            for inst in instruments:
                try:
                    # Parse instrument name: BTC-31MAY24-50000-C
                    parts = inst['instrument_name'].split('-')
                    if len(parts) != 4:
                        continue

                    exp_str = parts[1]  # e.g., "31MAY24"
                    strike = float(parts[2])
                    opt_type = parts[3]  # 'C' or 'P'

                    # Parse expiration date
                    exp_date = datetime.strptime(exp_str, '%d%b%y')
                    dte = (exp_date - current_time).days

                    # Filter by DTE
                    if dte < min_dte or dte > max_dte:
                        continue

                    # Create OptionContract
                    option = OptionContract(
                        symbol=currency,
                        strike=strike,
                        expiration=exp_date,
                        option_type=OptionType.CALL if opt_type == 'C' else OptionType.PUT,
                        contract_id=inst['instrument_name'],
                        bid=inst.get('bid_price', 0),
                        ask=inst.get('ask_price', 0),
                        last=inst.get('last_price', 0),
                        volume=inst.get('volume', 0),
                        open_interest=inst.get('open_interest', 0),
                        implied_volatility=inst.get('mark_iv', 0) / 100  # Convert from % to decimal
                    )

                    options.append(option)

                except Exception as e:
                    logger.debug(f"Could not parse instrument {inst.get('instrument_name')}: {e}")
                    continue

            logger.info(f"📋 Found {len(options)} {currency} options ({min_dte}-{max_dte} DTE)")

        except Exception as e:
            logger.error(f"Error fetching {currency} options: {e}")

        return options

    def get_option_chain(self, currency: str = 'BTC',
                        expiration: Optional[datetime] = None) -> pd.DataFrame:
        """
        Get option chain as DataFrame

        Args:
            currency: 'BTC' or 'ETH'
            expiration: Specific expiration date (None for all)
        """
        options = self.get_available_options(currency)

        if expiration:
            options = [opt for opt in options if opt.expiration.date() == expiration.date()]

        if not options:
            return pd.DataFrame()

        # Convert to DataFrame
        data = []
        for opt in options:
            data.append({
                'Strike': opt.strike,
                'Type': 'Call' if opt.option_type == OptionType.CALL else 'Put',
                'Expiration': opt.expiration,
                'DTE': (opt.expiration - datetime.now()).days,
                'Bid': opt.bid,
                'Ask': opt.ask,
                'Last': opt.last,
                'IV': opt.implied_volatility,
                'Volume': opt.volume,
                'OI': opt.open_interest,
                'Contract': opt.contract_id
            })

        df = pd.DataFrame(data)
        df = df.sort_values(['Expiration', 'Strike'])

        return df

    def get_index_price(self, currency: str = 'BTC') -> float:
        """Get current index price for BTC or ETH"""
        if not self.connected or not self.client:
            logger.error("Not connected to Deribit")
            return 0.0

        try:
            index_name = f"{currency.lower()}_usd"
            result = self.client.get_index_price(index_name=index_name)
            return result.get('index_price', 0.0)
        except Exception as e:
            logger.error(f"Error getting {currency} index price: {e}")
            return 0.0

    def get_order_book(self, instrument_name: str, depth: int = 5) -> Dict:
        """
        Get order book for a specific instrument

        Args:
            instrument_name: e.g., 'BTC-31MAY24-50000-C'
            depth: Number of price levels to retrieve
        """
        if not self.connected or not self.client:
            logger.error("Not connected to Deribit")
            return {}

        try:
            order_book = self.client.get_order_book(
                instrument_name=instrument_name,
                depth=depth
            )
            return order_book
        except Exception as e:
            logger.error(f"Error getting order book for {instrument_name}: {e}")
            return {}

    def calculate_covered_call_premium(self, currency: str = 'BTC',
                                      quantity: float = 1.0,
                                      min_dte: int = 7,
                                      max_dte: int = 30,
                                      delta_range: Tuple[float, float] = (0.2, 0.4)) -> List[Dict]:
        """
        Calculate potential covered call strategies

        Args:
            currency: 'BTC' or 'ETH'
            quantity: Number of coins held
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration
            delta_range: Target delta range for calls
        """
        if not self.connected:
            logger.error("Not connected to Deribit")
            return []

        # Get current price
        current_price = self.get_index_price(currency)
        if current_price == 0:
            return []

        # Get available options
        options = self.get_available_options(currency, min_dte, max_dte)

        # Filter for calls only
        calls = [opt for opt in options if opt.option_type == OptionType.CALL]

        # Calculate potential strategies
        strategies = []

        for call in calls:
            # Skip if no valid pricing
            if call.ask == 0 or call.bid == 0:
                continue

            # Calculate Greeks (simplified - Deribit provides greeks in API)
            dte_years = (call.expiration - datetime.now()).days / 365

            try:
                greeks = GreeksCalculator.calculate(
                    spot_price=current_price,
                    strike=call.strike,
                    time_to_expiry=dte_years,
                    volatility=call.implied_volatility,
                    risk_free_rate=0.05,
                    option_type=OptionType.CALL
                )

                # Filter by delta
                if not (delta_range[0] <= abs(greeks.delta) <= delta_range[1]):
                    continue

                # Calculate premium
                mid_price = (call.bid + call.ask) / 2
                premium = mid_price * quantity

                # Calculate annualized return
                days_to_exp = (call.expiration - datetime.now()).days
                annualized_return = (premium / (current_price * quantity)) * (365 / days_to_exp) * 100

                strategy = {
                    'strike': call.strike,
                    'expiration': call.expiration,
                    'dte': days_to_exp,
                    'premium': premium,
                    'premium_per_coin': mid_price,
                    'delta': greeks.delta,
                    'gamma': greeks.gamma,
                    'theta': greeks.theta,
                    'vega': greeks.vega,
                    'iv': call.implied_volatility,
                    'bid': call.bid,
                    'ask': call.ask,
                    'volume': call.volume,
                    'open_interest': call.open_interest,
                    'annualized_return': annualized_return,
                    'contract': call.contract_id
                }

                strategies.append(strategy)

            except Exception as e:
                logger.debug(f"Could not calculate Greeks for {call.contract_id}: {e}")
                continue

        # Sort by annualized return
        strategies.sort(key=lambda x: x['annualized_return'], reverse=True)

        logger.info(f"📊 Found {len(strategies)} covered call opportunities for {currency}")

        return strategies


def test_connection():
    """Test Deribit connection"""
    print("🔗 Testing Deribit connection...")

    config = DeribitConfig(env='test')  # Use testnet for testing
    connector = DeribitConnector(config)

    if connector.connect():
        print("✅ Connected to Deribit!")

        # Get BTC index price
        btc_price = connector.get_index_price('BTC')
        print(f"\n💰 BTC Index: ${btc_price:,.2f}")

        # Get ETH index price
        eth_price = connector.get_index_price('ETH')
        print(f"💰 ETH Index: ${eth_price:,.2f}")

        # Get available BTC options
        print("\n📋 Getting BTC options...")
        options = connector.get_available_options('BTC', min_dte=7, max_dte=30)
        print(f"Found {len(options)} BTC options")

        if options:
            print("\nSample options:")
            for opt in options[:5]:
                print(f"  {opt.contract_id}: Strike ${opt.strike:,.0f}, "
                      f"IV: {opt.implied_volatility*100:.1f}%, "
                      f"Last: {opt.last:.4f} BTC")

        # Calculate covered call strategies
        print("\n📊 Calculating BTC covered call strategies...")
        strategies = connector.calculate_covered_call_premium('BTC', quantity=1.0)

        if strategies:
            print(f"\nTop 5 strategies by annualized return:")
            for i, strat in enumerate(strategies[:5], 1):
                print(f"{i}. Strike ${strat['strike']:,.0f} - "
                      f"Premium: {strat['premium_per_coin']:.4f} BTC - "
                      f"Annualized: {strat['annualized_return']:.2f}% - "
                      f"Delta: {strat['delta']:.3f}")

        connector.disconnect()
    else:
        print("❌ Connection failed")


if __name__ == "__main__":
    test_connection()
