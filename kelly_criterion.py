"""
Kelly Criterion Calculator for Position Sizing
Calculates optimal position sizes based on historical win rate and risk/reward

The Kelly Criterion is a formula for optimal bet sizing:
f* = (bp - q) / b

where:
- f* = fraction of portfolio to risk
- b = odds (avg win / avg loss)
- p = win probability
- q = loss probability (1-p)

For trading safety, we use "Fractional Kelly" (typically 25-50% of full Kelly)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional
import logging

from trade_analytics import TradeDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KellyCriterionCalculator:
    """Calculate optimal position sizing using Kelly Criterion"""

    def __init__(self, db: TradeDatabase, kelly_fraction: float = 0.25):
        """
        Args:
            db: TradeDatabase instance
            kelly_fraction: Fraction of full Kelly to use (default 0.25 = 25%)
                           Lower is more conservative
        """
        self.db = db
        self.kelly_fraction = kelly_fraction  # Fractional Kelly for safety

    def calculate_kelly_fraction(self,
                                 symbol: Optional[str] = None,
                                 days: int = 180) -> Dict:
        """
        Calculate Kelly fraction for position sizing

        Args:
            symbol: Optional specific symbol (None for all symbols)
            days: Number of days of history to analyze

        Returns:
            Dictionary with Kelly fraction and supporting metrics
        """
        logger.info(f"📊 Calculating Kelly Criterion for {symbol or 'all symbols'}...")

        # Get trade history
        trades = self._get_trades_dataframe(days, symbol)

        if trades is None or len(trades) < 20:
            logger.warning(f"⚠️  Insufficient data: {len(trades) if trades is not None else 0} trades")
            return {
                'kelly_fraction': 0.10,  # Conservative default
                'safe_kelly': 0.10,
                'win_probability': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'odds_ratio': 0.0,
                'sample_size': 0,
                'confidence': 'low'
            }

        # Separate winning and losing trades
        winning_trades = trades[trades['profit_loss'] > 0]
        losing_trades = trades[trades['profit_loss'] < 0]

        # Calculate win probability
        p = len(winning_trades) / len(trades)  # Win probability
        q = 1 - p  # Loss probability

        # Calculate average win/loss
        avg_win = winning_trades['profit_loss'].mean() if len(winning_trades) > 0 else 0
        avg_loss = abs(losing_trades['profit_loss'].mean()) if len(losing_trades) > 0 else 1

        # Calculate odds (b = avg win / avg loss)
        b = avg_win / avg_loss if avg_loss > 0 else 1.0

        # Kelly Formula: f* = (bp - q) / b
        kelly_full = (b * p - q) / b if b > 0 else 0

        # Apply fractional Kelly for safety (typically 25-50%)
        kelly_safe = kelly_full * self.kelly_fraction

        # Ensure it's positive and reasonable
        kelly_safe = max(0, min(kelly_safe, 0.30))  # Cap at 30% of portfolio

        # Determine confidence based on sample size
        confidence = self._determine_confidence(len(trades))

        result = {
            'kelly_fraction': kelly_full,
            'safe_kelly': kelly_safe,
            'win_probability': p,
            'loss_probability': q,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'odds_ratio': b,
            'sample_size': len(trades),
            'confidence': confidence,
            'recommendation': self._get_recommendation(kelly_safe, confidence)
        }

        self._print_kelly_results(result, symbol)
        return result

    def get_position_size(self,
                         symbol: str,
                         portfolio_value: float,
                         stock_price: Optional[float] = None) -> Dict:
        """
        Calculate optimal position size in dollars and contracts

        Args:
            symbol: Stock symbol
            portfolio_value: Total portfolio value
            stock_price: Current stock price (optional, for contract calculation)

        Returns:
            Dictionary with position sizing recommendations
        """
        logger.info(f"\n💰 Calculating position size for {symbol}...")
        logger.info(f"   Portfolio Value: ${portfolio_value:,.2f}")

        # Get Kelly fraction for this symbol
        kelly_result = self.calculate_kelly_fraction(symbol)
        kelly = kelly_result['safe_kelly']

        # Calculate position size
        position_size_usd = portfolio_value * kelly

        # Estimate number of contracts
        # Assume ~$100-500 per contract depending on stock price and strike
        if stock_price:
            # Rough estimate: 100 shares * stock price = position value
            position_value = position_size_usd
            shares = int(position_value / stock_price)
            contracts = shares // 100
            premium_per_contract = 50  # Conservative estimate
        else:
            # Generic estimate
            contracts = int(position_size_usd / 10000)  # Assume $10k per contract position
            premium_per_contract = 50

        result = {
            'symbol': symbol,
            'kelly_fraction': kelly,
            'position_size_usd': position_size_usd,
            'contracts': max(1, contracts),  # At least 1 contract
            'max_contracts': contracts + 2,  # Allow some flexibility
            'estimated_premium_per_contract': premium_per_contract,
            'confidence': kelly_result['confidence'],
            'win_probability': kelly_result['win_probability'],
            'recommendation': kelly_result['recommendation']
        }

        self._print_position_size(result)
        return result

    def get_portfolio_allocation(self,
                                portfolio_value: float,
                                symbols: list,
                                max_positions: int = 10) -> Dict:
        """
        Calculate optimal allocation across multiple symbols

        Args:
            portfolio_value: Total portfolio value
            symbols: List of symbols to consider
            max_positions: Maximum number of positions

        Returns:
            Dictionary with allocation for each symbol
        """
        logger.info(f"\n📊 Calculating portfolio allocation...")
        logger.info(f"   Portfolio: ${portfolio_value:,.2f}")
        logger.info(f"   Symbols: {symbols}")

        allocations = {}
        total_kelly = 0

        # Calculate Kelly for each symbol
        for symbol in symbols:
            kelly_result = self.calculate_kelly_fraction(symbol)
            kelly = kelly_result['safe_kelly']

            if kelly > 0.05:  # Only include if Kelly > 5%
                allocations[symbol] = {
                    'kelly': kelly,
                    'confidence': kelly_result['confidence'],
                    'win_rate': kelly_result['win_probability']
                }
                total_kelly += kelly

        # Normalize if total exceeds 1.0 (100%)
        if total_kelly > 1.0:
            logger.warning(f"⚠️  Total Kelly ({total_kelly:.2%}) exceeds 100%, normalizing...")
            for symbol in allocations:
                allocations[symbol]['kelly'] /= total_kelly
                allocations[symbol]['normalized'] = True
        else:
            for symbol in allocations:
                allocations[symbol]['normalized'] = False

        # Calculate position sizes
        for symbol in allocations:
            kelly = allocations[symbol]['kelly']
            allocations[symbol]['position_size_usd'] = portfolio_value * kelly
            allocations[symbol]['position_pct'] = kelly * 100

        # Sort by allocation
        sorted_allocations = dict(
            sorted(allocations.items(),
                   key=lambda x: x[1]['position_size_usd'],
                   reverse=True)
        )

        # Limit to max positions
        if len(sorted_allocations) > max_positions:
            sorted_allocations = dict(list(sorted_allocations.items())[:max_positions])

        self._print_allocation(sorted_allocations, portfolio_value)
        return sorted_allocations

    def _get_trades_dataframe(self, days: int, symbol: Optional[str]) -> Optional[pd.DataFrame]:
        """Get trades as DataFrame"""
        try:
            if symbol:
                trades = self.db.get_trade_history(days=days, symbol=symbol)
            else:
                trades = self.db.get_trade_history(days=days)

            if not trades:
                return None

            return pd.DataFrame(trades)
        except Exception as e:
            logger.error(f"Error loading trades: {e}")
            return None

    def _determine_confidence(self, sample_size: int) -> str:
        """Determine confidence level based on sample size"""
        if sample_size >= 50:
            return 'high'
        elif sample_size >= 30:
            return 'medium'
        else:
            return 'low'

    def _get_recommendation(self, kelly: float, confidence: str) -> str:
        """Get recommendation text"""
        if confidence == 'low':
            return "Conservative: Limited data - use minimum position sizes"
        elif kelly < 0.10:
            return "Conservative: Low Kelly suggests small positions"
        elif kelly < 0.20:
            return "Moderate: Reasonable position sizes"
        elif kelly < 0.30:
            return "Aggressive: Large positions - monitor closely"
        else:
            return "Very Aggressive: Maximum positions - high risk"

    def _print_kelly_results(self, result: Dict, symbol: Optional[str]):
        """Print Kelly calculation results"""
        symbol_str = f" for {symbol}" if symbol else ""
        logger.info(f"\n{'='*60}")
        logger.info(f"KELLY CRITERION RESULTS{symbol_str}")
        logger.info(f"{'='*60}")
        logger.info(f"Sample Size: {result['sample_size']} trades")
        logger.info(f"Confidence: {result['confidence'].upper()}")
        logger.info("")
        logger.info(f"Win Probability: {result['win_probability']:.1%}")
        logger.info(f"Avg Win: ${result['avg_win']:.2f}")
        logger.info(f"Avg Loss: ${result['avg_loss']:.2f}")
        logger.info(f"Odds Ratio (b): {result['odds_ratio']:.2f}")
        logger.info("")
        logger.info(f"Full Kelly: {result['kelly_fraction']:.1%}")
        logger.info(f"Safe Kelly ({self.kelly_fraction:.0%} of full): {result['safe_kelly']:.1%}")
        logger.info("")
        logger.info(f"Recommendation: {result['recommendation']}")
        logger.info(f"{'='*60}")

    def _print_position_size(self, result: Dict):
        """Print position sizing results"""
        logger.info(f"\n{'='*60}")
        logger.info(f"POSITION SIZE for {result['symbol']}")
        logger.info(f"{'='*60}")
        logger.info(f"Kelly Fraction: {result['kelly_fraction']:.1%}")
        logger.info(f"Position Size: ${result['position_size_usd']:,.2f}")
        logger.info(f"Recommended Contracts: {result['contracts']}")
        logger.info(f"Max Contracts: {result['max_contracts']}")
        logger.info(f"Win Probability: {result['win_probability']:.1%}")
        logger.info(f"Confidence: {result['confidence'].upper()}")
        logger.info("")
        logger.info(f"💡 {result['recommendation']}")
        logger.info(f"{'='*60}")

    def _print_allocation(self, allocations: Dict, portfolio_value: float):
        """Print portfolio allocation"""
        logger.info(f"\n{'='*60}")
        logger.info(f"PORTFOLIO ALLOCATION")
        logger.info(f"{'='*60}")
        logger.info(f"Total Portfolio: ${portfolio_value:,.2f}")
        logger.info(f"Number of Positions: {len(allocations)}")
        logger.info("")

        total_allocated = 0
        for symbol, data in allocations.items():
            logger.info(f"{symbol:6} - {data['position_pct']:5.1f}% "
                       f"(${data['position_size_usd']:10,.2f}) - "
                       f"{data['confidence']} confidence")
            total_allocated += data['position_size_usd']

        logger.info("")
        logger.info(f"Total Allocated: ${total_allocated:,.2f} ({total_allocated/portfolio_value:.1%})")
        logger.info(f"Cash Reserve: ${portfolio_value - total_allocated:,.2f}")
        logger.info(f"{'='*60}")


def main():
    """Example usage"""
    from trade_analytics import TradeDatabase

    # Initialize
    db = TradeDatabase()
    kelly = KellyCriterionCalculator(db, kelly_fraction=0.25)  # Use 25% of full Kelly

    # Example 1: Calculate Kelly for a specific symbol
    print("\n" + "="*60)
    print("EXAMPLE 1: Single Symbol Analysis")
    print("="*60)
    result = kelly.calculate_kelly_fraction(symbol='TSLA', days=180)

    # Example 2: Get position size
    print("\n" + "="*60)
    print("EXAMPLE 2: Position Sizing")
    print("="*60)
    position = kelly.get_position_size(
        symbol='TSLA',
        portfolio_value=200000,
        stock_price=430.0
    )

    print(f"\nFor TSLA with $200k portfolio:")
    print(f"  Position Size: ${position['position_size_usd']:,.2f}")
    print(f"  Contracts: {position['contracts']}")

    # Example 3: Portfolio allocation
    print("\n" + "="*60)
    print("EXAMPLE 3: Portfolio Allocation")
    print("="*60)
    symbols = ['TSLA', 'AAPL', 'MSFT', 'NVDA', 'AMD']
    allocation = kelly.get_portfolio_allocation(
        portfolio_value=200000,
        symbols=symbols,
        max_positions=5
    )

    print("\nRecommended Allocation:")
    for symbol, data in allocation.items():
        contracts = int(data['position_size_usd'] / 10000)
        print(f"  {symbol}: {contracts} contracts (${data['position_size_usd']:,.2f})")


if __name__ == "__main__":
    main()
