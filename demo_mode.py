"""
Demo Mode - Mock IBKR data for testing the dashboard without live connection
"""
from datetime import datetime, timedelta
from typing import List, Dict
import random


class DemoIBKRConnector:
    """Mock IBKR connector with sample data"""

    def __init__(self):
        self.connected = True
        self.readonly = True

    def connect(self) -> bool:
        """Simulate connection"""
        self.connected = True
        return True

    def disconnect(self):
        """Simulate disconnection"""
        self.connected = False

    def get_account_summary(self) -> Dict:
        """Return mock account data"""
        return {
            'NetLiquidation': 125750.50,
            'TotalCashValue': 45250.00,
            'UnrealizedPnL': 3250.75,
            'RealizedPnL': 1850.25,
            'BuyingPower': 250000.00,
            'AvailableFunds': 45250.00
        }

    def get_stock_positions(self) -> List[Dict]:
        """Return mock stock positions"""
        return [
            {
                'symbol': 'AAPL',
                'quantity': 200,
                'avg_cost': 175.50,
                'current_price': 182.30
            },
            {
                'symbol': 'MSFT',
                'quantity': 100,
                'avg_cost': 385.00,
                'current_price': 392.15
            },
            {
                'symbol': 'TSLA',
                'quantity': 300,
                'avg_cost': 245.75,
                'current_price': 248.50
            }
        ]

    def get_covered_call_positions(self) -> List[Dict]:
        """Return mock covered call positions"""
        today = datetime.now()

        return [
            {
                'symbol': 'AAPL',
                'stock_qty': 200,
                'stock_price': 182.30,
                'option_strike': 185.0,
                'option_expiry': today + timedelta(days=15),
                'option_dte': 15,
                'contracts': -2,  # Short 2 contracts
                'premium_received': 580.00,
                'current_option_value': 320.00,
                'unrealized_pnl': 260.00,
                'delta': -0.35,
                'theta': 0.08
            },
            {
                'symbol': 'MSFT',
                'stock_qty': 100,
                'stock_price': 392.15,
                'option_strike': 400.0,
                'option_expiry': today + timedelta(days=22),
                'option_dte': 22,
                'contracts': -1,
                'premium_received': 450.00,
                'current_option_value': 280.00,
                'unrealized_pnl': 170.00,
                'delta': -0.28,
                'theta': 0.06
            },
            {
                'symbol': 'TSLA',
                'stock_qty': 300,
                'stock_price': 248.50,
                'option_strike': 255.0,
                'option_expiry': today + timedelta(days=8),
                'option_dte': 8,
                'contracts': -3,
                'premium_received': 1350.00,
                'current_option_value': 990.00,
                'unrealized_pnl': 360.00,
                'delta': -0.42,
                'theta': 0.12
            }
        ]

    def get_option_chain(self, symbol: str, exchange: str = "SMART"):
        """Return mock option chain"""
        import pandas as pd

        today = datetime.now()
        current_price = {
            'AAPL': 182.30,
            'MSFT': 392.15,
            'TSLA': 248.50,
            'NVDA': 875.50
        }.get(symbol, 150.00)

        # Generate strikes around current price
        strikes = []
        expirations = []

        # 3 expirations
        exp_dates = [
            (today + timedelta(days=15)).strftime('%Y%m%d'),
            (today + timedelta(days=30)).strftime('%Y%m%d'),
            (today + timedelta(days=45)).strftime('%Y%m%d')
        ]

        # 10 strikes around current price
        base_strike = round(current_price / 5) * 5
        for i in range(-4, 6):
            strikes.append(base_strike + (i * 5))

        return pd.DataFrame({
            'expirations': [exp_dates],
            'strikes': [strikes]
        })

    def get_call_options(self, symbol: str, expiration: str,
                        min_strike: float = None, max_strike: float = None):
        """Return mock call options for a specific expiration"""

        current_price = {
            'AAPL': 182.30,
            'MSFT': 392.15,
            'TSLA': 248.50,
            'NVDA': 875.50
        }.get(symbol, 150.00)

        # Parse expiration to calculate DTE
        exp_date = datetime.strptime(expiration, '%Y%m%d')
        dte = (exp_date - datetime.now()).days

        # Generate strikes
        base_strike = round(current_price / 5) * 5
        if min_strike is None:
            min_strike = base_strike - 20
        if max_strike is None:
            max_strike = base_strike + 30

        options = []

        for strike in range(int(min_strike), int(max_strike) + 1, 5):
            # Calculate mock option price based on moneyness
            moneyness = (strike - current_price) / current_price

            # Simple premium calculation
            if strike > current_price:  # OTM
                premium = max(0.50, (strike - current_price) * 0.15 * (dte / 30))
            else:  # ITM
                premium = (current_price - strike) + max(0.50, 5.0 * (dte / 30))

            # Add some randomness
            premium *= random.uniform(0.9, 1.1)

            # Calculate Greeks (simplified)
            delta = max(0.05, min(0.95, 0.5 + (current_price - strike) / (current_price * 0.1)))
            theta = -premium / dte if dte > 0 else -0.10

            options.append({
                'strike': strike,
                'expiration': exp_date,
                'last_price': round(premium, 2),
                'bid': round(premium * 0.97, 2),
                'ask': round(premium * 1.03, 2),
                'volume': random.randint(50, 500),
                'openInterest': random.randint(100, 2000),
                'impliedVolatility': round(random.uniform(0.20, 0.45), 4),
                'delta': round(delta, 4),
                'gamma': round(random.uniform(0.001, 0.01), 4),
                'theta': round(theta, 4),
                'vega': round(random.uniform(0.05, 0.15), 4)
            })

        return options

    def get_otm_calls(self, symbol: str, current_price: float, days_to_expiration: int = 30) -> List[Dict]:
        """Get out-of-the-money call options"""
        # Find closest expiration
        today = datetime.now()
        target_date = today + timedelta(days=days_to_expiration)
        expiration = target_date.strftime('%Y%m%d')

        # Get all call options for this expiration
        all_options = self.get_call_options(symbol, expiration)

        # Filter for OTM only (strike > current_price)
        otm_options = [opt for opt in all_options if opt['strike'] > current_price]

        return otm_options

    def sell_covered_call(self, symbol: str, quantity: int, strike: float,
                         expiration: str, limit_price: float = None):
        """Mock sell covered call - just return success"""

        # Simulate order
        class MockTrade:
            def __init__(self):
                self.orderStatus = type('obj', (object,), {'status': 'Filled'})()
                self.filled = quantity

        return MockTrade()
