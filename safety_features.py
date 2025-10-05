"""
🛡️ Safety Features for Covered Calls Trading
Pre-trade validation and risk management
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Tuple
from datetime import datetime


class TradingMode(Enum):
    """Trading mode enumeration"""
    DEMO = "Demo"
    PAPER = "Paper Trading"
    LIVE = "Live Trading"


@dataclass
class TradingLimits:
    """Trading limits and restrictions"""
    max_trades_per_day: int = 5
    max_contracts_per_trade: int = 10
    min_dte: int = 21  # Minimum days to expiration
    max_dte: int = 45  # Maximum days to expiration
    min_delta: float = 0.15  # Minimum option delta
    max_delta: float = 0.40  # Maximum option delta
    min_premium: float = 0.50  # Minimum premium per contract ($)
    max_position_pct: float = 0.25  # Max 25% of portfolio in one position


class SafetyManager:
    """
    Pre-trade safety validation system

    Validates trades against:
    - Trading limits
    - Risk parameters
    - Portfolio constraints
    - Daily limits
    """

    def __init__(self, mode: TradingMode = TradingMode.PAPER):
        self.mode = mode
        self.limits = TradingLimits()
        self.todays_trades = 0
        self.start_of_day = datetime.now().date()

    def pre_trade_validation(self, trade_request: Dict) -> Tuple[bool, List[str]]:
        """
        Comprehensive pre-trade validation

        Args:
            trade_request: Dict with keys:
                - symbol: str
                - contracts: int
                - delta: float
                - dte: int (days to expiration)
                - premium: float (per contract)
                - strike: float

        Returns:
            Tuple of (approved: bool, messages: List[str])
        """
        messages = []
        approved = True

        # Reset daily counter if new day
        if datetime.now().date() > self.start_of_day:
            self.todays_trades = 0
            self.start_of_day = datetime.now().date()

        # Check 1: Daily trade limit
        if self.todays_trades >= self.limits.max_trades_per_day:
            approved = False
            messages.append(
                f"❌ Daily trade limit reached ({self.limits.max_trades_per_day})"
            )
        else:
            messages.append(
                f"✅ Daily trades: {self.todays_trades}/{self.limits.max_trades_per_day}"
            )

        # Check 2: Contracts per trade
        contracts = trade_request.get('contracts', 0)
        if contracts > self.limits.max_contracts_per_trade:
            approved = False
            messages.append(
                f"❌ Too many contracts ({contracts} > {self.limits.max_contracts_per_trade})"
            )
        else:
            messages.append(f"✅ Contracts: {contracts}")

        # Check 3: Days to expiration
        dte = trade_request.get('dte', 0)
        if dte < self.limits.min_dte:
            approved = False
            messages.append(
                f"❌ Expiration too soon ({dte} < {self.limits.min_dte} days)"
            )
        elif dte > self.limits.max_dte:
            approved = False
            messages.append(
                f"❌ Expiration too far ({dte} > {self.limits.max_dte} days)"
            )
        else:
            messages.append(f"✅ DTE: {dte} days")

        # Check 4: Delta range
        delta = trade_request.get('delta', 0)
        if delta < self.limits.min_delta:
            approved = False
            messages.append(
                f"❌ Delta too low ({delta:.3f} < {self.limits.min_delta})"
            )
        elif delta > self.limits.max_delta:
            approved = False
            messages.append(
                f"⚠️  Warning: High delta ({delta:.3f} > {self.limits.max_delta})"
            )
            # Don't block, just warn
        else:
            messages.append(f"✅ Delta: {delta:.3f}")

        # Check 5: Minimum premium
        premium = trade_request.get('premium', 0)
        if premium < self.limits.min_premium:
            approved = False
            messages.append(
                f"❌ Premium too low (${premium:.2f} < ${self.limits.min_premium})"
            )
        else:
            messages.append(f"✅ Premium: ${premium:.2f}/contract")

        # Check 6: Symbol validation
        symbol = trade_request.get('symbol', '')
        if not symbol or len(symbol) > 5:
            approved = False
            messages.append(f"❌ Invalid symbol: {symbol}")
        else:
            messages.append(f"✅ Symbol: {symbol}")

        # Check 7: Strike price
        strike = trade_request.get('strike', 0)
        if strike <= 0:
            approved = False
            messages.append(f"❌ Invalid strike price: ${strike}")
        else:
            messages.append(f"✅ Strike: ${strike}")

        # Add mode warning
        if self.mode == TradingMode.LIVE:
            messages.insert(0, "⚠️  LIVE TRADING MODE - Real money at risk!")
        elif self.mode == TradingMode.PAPER:
            messages.insert(0, "📝 Paper trading mode - Simulated execution")
        else:
            messages.insert(0, "🎮 Demo mode - No real execution")

        return approved, messages

    def get_safety_summary(self) -> Dict:
        """Get current safety status"""
        return {
            'mode': self.mode.value,
            'todays_trades': self.todays_trades,
            'max_daily_trades': self.limits.max_trades_per_day,
            'trades_remaining': self.limits.max_trades_per_day - self.todays_trades,
            'limits': {
                'max_contracts': self.limits.max_contracts_per_trade,
                'dte_range': f"{self.limits.min_dte}-{self.limits.max_dte} days",
                'delta_range': f"{self.limits.min_delta}-{self.limits.max_delta}",
                'min_premium': f"${self.limits.min_premium}"
            }
        }
