"""
Covered Calls Management System - Enhanced Version
Advanced options trading system with risk management and profit optimization
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np
from scipy.stats import norm
import logging
import json

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Advanced Greeks calculations
try:
    from blackscholes import BlackScholesCall
    BLACKSCHOLES_AVAILABLE = True
except ImportError:
    BLACKSCHOLES_AVAILABLE = False
    logger.warning("blackscholes library not available. Using basic Greeks calculations.")

# Implied Volatility calculations
try:
    from py_vollib.black_scholes import black_scholes as bs_price
    from py_vollib.black_scholes.implied_volatility import implied_volatility as calc_iv
    VOLLIB_AVAILABLE = True
except ImportError:
    VOLLIB_AVAILABLE = False
    logger.warning("py_vollib library not available. IV calculations limited.")


class OptionType(Enum):
    """Option type enumeration"""
    CALL = "CALL"
    PUT = "PUT"


class PositionStatus(Enum):
    """Position status enumeration"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ASSIGNED = "ASSIGNED"
    EXPIRED = "EXPIRED"
    ROLLED = "ROLLED"


class RiskLevel(Enum):
    """Risk level for strategies"""
    CONSERVATIVE = "CONSERVATIVE"  # Low risk, low premium
    MODERATE = "MODERATE"          # Balanced risk/reward
    AGGRESSIVE = "AGGRESSIVE"      # Higher risk, higher premium


@dataclass
class Stock:
    """Stock position information"""
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float

    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss"""
        return (self.current_price - self.avg_cost) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L percentage"""
        return (self.current_price / self.avg_cost - 1) * 100


@dataclass
class OptionContract:
    """Option contract details"""
    symbol: str
    strike: float
    expiration: datetime
    option_type: OptionType
    premium: float
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    volume: int
    open_interest: int
    bid: float
    ask: float

    @property
    def mid_price(self) -> float:
        """Mid price between bid and ask"""
        return (self.bid + self.ask) / 2

    @property
    def days_to_expiration(self) -> int:
        """Days until expiration"""
        return (self.expiration - datetime.now()).days

    @property
    def is_liquid(self) -> bool:
        """Check if option has sufficient liquidity"""
        return self.volume > 100 and self.open_interest > 500

    @property
    def bid_ask_spread(self) -> float:
        """Bid-ask spread percentage"""
        return (self.ask - self.bid) / self.mid_price * 100


@dataclass
class CoveredCall:
    """Covered call position"""
    id: str
    stock: Stock
    option: OptionContract
    quantity: int  # Number of contracts (1 contract = 100 shares)
    entry_date: datetime
    status: PositionStatus
    premium_collected: float
    commission: float = 0.0
    notes: str = ""

    @property
    def net_premium(self) -> float:
        """Net premium after commissions"""
        return self.premium_collected - self.commission

    @property
    def max_profit(self) -> float:
        """Maximum profit if assigned"""
        stock_profit = (self.option.strike - self.stock.avg_cost) * self.quantity * 100
        return stock_profit + self.net_premium

    @property
    def return_if_assigned(self) -> float:
        """Return percentage if assigned"""
        cost_basis = self.stock.avg_cost * self.quantity * 100
        return (self.max_profit / cost_basis) * 100

    @property
    def breakeven_price(self) -> float:
        """Breakeven stock price"""
        return self.stock.avg_cost - (self.net_premium / (self.quantity * 100))

    @property
    def downside_protection(self) -> float:
        """Downside protection percentage"""
        return (self.net_premium / (self.stock.current_price * self.quantity * 100)) * 100

    @property
    def annualized_return(self) -> float:
        """Annualized return if assigned"""
        days = self.option.days_to_expiration
        if days == 0:
            return 0
        return self.return_if_assigned * (365 / days)


class GreeksCalculator:
    """Calculate option Greeks using Black-Scholes model (enhanced with blackscholes library)"""

    @staticmethod
    def calculate_d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1 parameter"""
        return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))

    @staticmethod
    def calculate_d2(d1: float, sigma: float, T: float) -> float:
        """Calculate d2 parameter"""
        return d1 - sigma * np.sqrt(T)

    @classmethod
    def calculate_delta(cls, S: float, K: float, T: float, r: float, sigma: float,
                       option_type: OptionType) -> float:
        """Calculate delta (enhanced with blackscholes library if available)"""
        if BLACKSCHOLES_AVAILABLE and option_type == OptionType.CALL:
            try:
                bs = BlackScholesCall(S=S, K=K, T=T, r=r, sigma=sigma)
                return bs.delta()
            except:
                pass  # Fall back to basic calculation

        # Fallback to basic calculation
        d1 = cls.calculate_d1(S, K, T, r, sigma)
        if option_type == OptionType.CALL:
            return norm.cdf(d1)
        else:
            return norm.cdf(d1) - 1

    @classmethod
    def calculate_gamma(cls, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate gamma (enhanced with blackscholes library if available)"""
        if BLACKSCHOLES_AVAILABLE:
            try:
                bs = BlackScholesCall(S=S, K=K, T=T, r=r, sigma=sigma)
                return bs.gamma()
            except:
                pass

        # Fallback to basic calculation
        d1 = cls.calculate_d1(S, K, T, r, sigma)
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))

    @classmethod
    def calculate_theta(cls, S: float, K: float, T: float, r: float, sigma: float,
                       option_type: OptionType) -> float:
        """Calculate theta - daily time decay (enhanced with blackscholes library if available)"""
        if BLACKSCHOLES_AVAILABLE and option_type == OptionType.CALL:
            try:
                bs = BlackScholesCall(S=S, K=K, T=T, r=r, sigma=sigma)
                return bs.theta() / 365  # Convert to daily
            except:
                pass

        # Fallback to basic calculation
        d1 = cls.calculate_d1(S, K, T, r, sigma)
        d2 = cls.calculate_d2(d1, sigma, T)

        term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))

        if option_type == OptionType.CALL:
            term2 = -r * K * np.exp(-r * T) * norm.cdf(d2)
            return (term1 + term2) / 365  # Daily theta
        else:
            term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
            return (term1 + term2) / 365

    @classmethod
    def calculate_vega(cls, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate vega - sensitivity to IV (enhanced with blackscholes library if available)"""
        if BLACKSCHOLES_AVAILABLE:
            try:
                bs = BlackScholesCall(S=S, K=K, T=T, r=r, sigma=sigma)
                return bs.vega()
            except:
                pass

        # Fallback to basic calculation
        d1 = cls.calculate_d1(S, K, T, r, sigma)
        return S * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% IV change

    @classmethod
    def calculate_implied_volatility(cls, market_price: float, S: float, K: float,
                                    T: float, r: float, option_type: OptionType) -> Optional[float]:
        """Calculate implied volatility from market price (using py_vollib if available)"""
        if VOLLIB_AVAILABLE:
            try:
                flag = 'c' if option_type == OptionType.CALL else 'p'
                iv = calc_iv(
                    price=market_price,
                    S=S,
                    K=K,
                    t=T,
                    r=r,
                    flag=flag
                )
                return iv * 100  # Convert to percentage
            except:
                pass

        return None  # Cannot calculate without py_vollib


class CoveredCallStrategy:
    """Covered call strategy selector and analyzer"""

    def __init__(self, risk_level: RiskLevel = RiskLevel.MODERATE):
        self.risk_level = risk_level
        self.min_premium_pct = self._get_min_premium_pct()
        self.max_dte = self._get_max_dte()
        self.target_delta = self._get_target_delta()

    def _get_min_premium_pct(self) -> float:
        """Minimum premium percentage based on risk level"""
        return {
            RiskLevel.CONSERVATIVE: 0.5,
            RiskLevel.MODERATE: 1.0,
            RiskLevel.AGGRESSIVE: 1.5
        }[self.risk_level]

    def _get_max_dte(self) -> int:
        """Maximum days to expiration"""
        return {
            RiskLevel.CONSERVATIVE: 60,
            RiskLevel.MODERATE: 45,
            RiskLevel.AGGRESSIVE: 30
        }[self.risk_level]

    def _get_target_delta(self) -> Tuple[float, float]:
        """Target delta range"""
        return {
            RiskLevel.CONSERVATIVE: (0.15, 0.25),  # Far OTM
            RiskLevel.MODERATE: (0.25, 0.35),      # Moderate OTM
            RiskLevel.AGGRESSIVE: (0.35, 0.50)     # Near/At the money
        }[self.risk_level]

    def score_option(self, option: OptionContract, stock_price: float) -> float:
        """
        Score an option based on multiple criteria
        Returns: score from 0-100
        """
        score = 0

        # 1. Premium yield (30 points)
        premium_pct = (option.premium / stock_price) * 100
        annualized_premium = premium_pct * (365 / max(option.days_to_expiration, 1))
        score += min(annualized_premium / 2, 30)  # Cap at 30

        # 2. Delta in target range (25 points)
        delta_min, delta_max = self.target_delta
        if delta_min <= abs(option.delta) <= delta_max:
            score += 25
        elif abs(option.delta) < delta_min:
            score += 15  # Too far OTM
        else:
            score += 10  # Too close to ATM

        # 3. Liquidity (20 points)
        if option.is_liquid:
            score += 20
            # Bonus for tight spreads
            if option.bid_ask_spread < 5:
                score += 5

        # 4. Implied Volatility (15 points)
        # Higher IV = better premium, but check if it's reasonable
        if 20 <= option.implied_volatility <= 60:
            score += 15
        elif option.implied_volatility > 60:
            score += 10  # Very high IV - risky
        else:
            score += 5   # Low IV - low premium

        # 5. Time to expiration (10 points)
        if 20 <= option.days_to_expiration <= self.max_dte:
            score += 10
        elif option.days_to_expiration < 20:
            score += 5

        return min(score, 100)

    def find_best_strike(self, options: List[OptionContract],
                        stock_price: float,
                        top_n: int = 5) -> List[Tuple[OptionContract, float]]:
        """
        Find best strike prices from available options
        Returns: List of (option, score) tuples
        """
        # Filter options
        valid_options = [
            opt for opt in options
            if opt.option_type == OptionType.CALL
            and opt.days_to_expiration <= self.max_dte
            and opt.days_to_expiration >= 7  # Minimum 1 week
        ]

        # Score each option
        scored_options = [
            (opt, self.score_option(opt, stock_price))
            for opt in valid_options
        ]

        # Sort by score and return top N
        scored_options.sort(key=lambda x: x[1], reverse=True)
        return scored_options[:top_n]


class RollStrategy:
    """Strategy for rolling covered calls"""

    @staticmethod
    def should_roll(position: CoveredCall, current_stock_price: float,
                   roll_threshold_pct: float = 5.0) -> bool:
        """
        Determine if position should be rolled

        Args:
            position: Current covered call position
            current_stock_price: Current stock price
            roll_threshold_pct: Roll if stock is within this % of strike

        Returns: True if should roll
        """
        # Don't roll if too far from expiration
        if position.option.days_to_expiration > 21:
            return False

        # Don't roll if far from strike
        distance_to_strike = ((position.option.strike / current_stock_price) - 1) * 100
        if distance_to_strike > roll_threshold_pct:
            return False

        # Roll if near expiration and near strike
        if position.option.days_to_expiration <= 7:
            return True

        # Roll if deeply ITM and want to avoid assignment
        if current_stock_price > position.option.strike * 1.05:
            return True

        return False

    @staticmethod
    def calculate_roll_credit(old_option: OptionContract,
                            new_option: OptionContract,
                            quantity: int) -> float:
        """
        Calculate net credit/debit for rolling

        Returns: Net credit (positive) or debit (negative)
        """
        # Buy back old option (debit)
        buyback_cost = old_option.ask * quantity * 100

        # Sell new option (credit)
        new_premium = new_option.bid * quantity * 100

        return new_premium - buyback_cost


class PortfolioManager:
    """Manage portfolio of covered calls"""

    def __init__(self):
        self.positions: List[CoveredCall] = []
        self.closed_positions: List[CoveredCall] = []

    def add_position(self, position: CoveredCall):
        """Add new covered call position"""
        self.positions.append(position)
        logger.info(f"Added position: {position.id} - {position.stock.symbol}")

    def close_position(self, position_id: str, close_price: float,
                      close_date: datetime, status: PositionStatus):
        """Close a position"""
        position = self._find_position(position_id)
        if position:
            position.status = status
            self.positions.remove(position)
            self.closed_positions.append(position)
            logger.info(f"Closed position: {position_id} - {status.value}")

    def _find_position(self, position_id: str) -> Optional[CoveredCall]:
        """Find position by ID"""
        for pos in self.positions:
            if pos.id == position_id:
                return pos
        return None

    def get_portfolio_metrics(self) -> Dict:
        """Calculate portfolio-wide metrics"""
        if not self.positions:
            return {}

        total_stock_value = sum(pos.stock.market_value for pos in self.positions)
        total_premium = sum(pos.net_premium for pos in self.positions)
        total_max_profit = sum(pos.max_profit for pos in self.positions)

        # Calculate weighted average metrics
        weighted_dte = sum(
            pos.option.days_to_expiration * pos.stock.market_value
            for pos in self.positions
        ) / total_stock_value

        weighted_delta = sum(
            abs(pos.option.delta) * pos.stock.market_value
            for pos in self.positions
        ) / total_stock_value

        return {
            "total_positions": len(self.positions),
            "total_stock_value": total_stock_value,
            "total_premium_collected": total_premium,
            "total_max_profit": total_max_profit,
            "avg_days_to_expiration": weighted_dte,
            "avg_delta": weighted_delta,
            "portfolio_return_if_assigned": (total_max_profit / total_stock_value) * 100
        }

    def get_expiration_calendar(self) -> Dict[str, List[CoveredCall]]:
        """Get positions grouped by expiration date"""
        calendar = {}
        for pos in self.positions:
            exp_date = pos.option.expiration.strftime("%Y-%m-%d")
            if exp_date not in calendar:
                calendar[exp_date] = []
            calendar[exp_date].append(pos)
        return calendar

    def get_at_risk_positions(self, price_threshold_pct: float = 5.0) -> List[CoveredCall]:
        """
        Find positions at risk of assignment

        Args:
            price_threshold_pct: Consider at-risk if within this % of strike
        """
        at_risk = []
        for pos in self.positions:
            if pos.stock.current_price >= pos.option.strike * (1 - price_threshold_pct/100):
                at_risk.append(pos)
        return at_risk

    def calculate_total_theta(self) -> float:
        """Calculate total portfolio theta (daily decay)"""
        return sum(pos.option.theta * pos.quantity * 100 for pos in self.positions)

    def calculate_total_delta(self) -> float:
        """Calculate total portfolio delta"""
        # Stock delta = 1, short call delta = negative
        stock_delta = sum(pos.stock.quantity for pos in self.positions)
        option_delta = sum(pos.option.delta * pos.quantity * 100 for pos in self.positions)
        return stock_delta + option_delta

    def export_to_json(self, filename: str):
        """Export portfolio to JSON"""
        data = {
            "positions": [self._position_to_dict(pos) for pos in self.positions],
            "closed_positions": [self._position_to_dict(pos) for pos in self.closed_positions],
            "metrics": self.get_portfolio_metrics()
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Portfolio exported to {filename}")

    @staticmethod
    def _position_to_dict(pos: CoveredCall) -> Dict:
        """Convert position to dictionary"""
        return {
            "id": pos.id,
            "symbol": pos.stock.symbol,
            "quantity": pos.quantity,
            "strike": pos.option.strike,
            "expiration": pos.option.expiration.isoformat(),
            "premium": pos.premium_collected,
            "status": pos.status.value,
            "max_profit": pos.max_profit,
            "return_if_assigned": pos.return_if_assigned,
            "annualized_return": pos.annualized_return
        }


class AlertSystem:
    """Alert system for important events"""

    def __init__(self):
        self.alerts: List[Dict] = []

    def check_alerts(self, portfolio: PortfolioManager) -> List[Dict]:
        """Check for alerts across portfolio"""
        alerts = []

        for pos in portfolio.positions:
            # Assignment risk alert
            if pos.stock.current_price >= pos.option.strike:
                alerts.append({
                    "type": "ASSIGNMENT_RISK",
                    "severity": "HIGH",
                    "position_id": pos.id,
                    "message": f"{pos.stock.symbol} is ITM - assignment risk",
                    "action": "Consider rolling or accepting assignment"
                })

            # Expiration approaching
            if pos.option.days_to_expiration <= 7:
                alerts.append({
                    "type": "EXPIRATION_SOON",
                    "severity": "MEDIUM",
                    "position_id": pos.id,
                    "message": f"{pos.stock.symbol} expires in {pos.option.days_to_expiration} days",
                    "action": "Decide: let expire, roll, or close"
                })

            # Low liquidity warning
            if not pos.option.is_liquid:
                alerts.append({
                    "type": "LOW_LIQUIDITY",
                    "severity": "LOW",
                    "position_id": pos.id,
                    "message": f"{pos.stock.symbol} option has low liquidity",
                    "action": "May be difficult to roll or close"
                })

        self.alerts = alerts
        return alerts


# Example usage
if __name__ == "__main__":
    # Example: Create a covered call position
    stock = Stock(
        symbol="AAPL",
        quantity=100,
        avg_cost=180.0,
        current_price=185.0
    )

    option = OptionContract(
        symbol="AAPL",
        strike=190.0,
        expiration=datetime.now() + timedelta(days=30),
        option_type=OptionType.CALL,
        premium=3.50,
        implied_volatility=25.0,
        delta=0.30,
        gamma=0.015,
        theta=-0.05,
        vega=0.12,
        volume=5000,
        open_interest=10000,
        bid=3.45,
        ask=3.55
    )

    position = CoveredCall(
        id="CC001",
        stock=stock,
        option=option,
        quantity=1,
        entry_date=datetime.now(),
        status=PositionStatus.OPEN,
        premium_collected=350.0,
        commission=1.0
    )

    print(f"Position: {position.stock.symbol}")
    print(f"Max Profit: ${position.max_profit:.2f}")
    print(f"Return if Assigned: {position.return_if_assigned:.2f}%")
    print(f"Annualized Return: {position.annualized_return:.2f}%")
    print(f"Downside Protection: {position.downside_protection:.2f}%")
