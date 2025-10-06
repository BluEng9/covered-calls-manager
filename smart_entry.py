"""
Smart Entry Filter for Covered Calls
Advanced filtering system that checks multiple quality criteria before trading

Features:
- IV Rank calculation (sell when IV is high)
- Earnings avoidance
- Liquidity checks (volume, open interest)
- Bid-ask spread validation
- Technical trend analysis
- Overall quality scoring
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import numpy as np

from earnings_calendar import EarningsCalendar
from ibkr_connector import IBKRConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartEntryFilter:
    """
    Advanced entry filter for covered call trading
    Only executes trades that meet high-quality criteria
    """

    def __init__(self, connector: IBKRConnector, min_score: float = 80.0):
        """
        Args:
            connector: IBKR connector instance
            min_score: Minimum quality score to execute trade (0-100)
        """
        self.connector = connector
        self.earnings = EarningsCalendar()
        self.min_score = min_score
        self._iv_cache = {}  # Cache IV history

    def calculate_iv_rank(self, symbol: str, current_iv: float) -> float:
        """
        Calculate IV Rank (Implied Volatility Rank)

        IV Rank = (Current IV - 52w Low IV) / (52w High IV - 52w Low IV) * 100

        Interpretation:
        - IV Rank > 50: Good time to sell premium
        - IV Rank > 70: Excellent time to sell premium
        - IV Rank < 30: Poor time to sell (wait for higher IV)

        Args:
            symbol: Stock symbol
            current_iv: Current implied volatility (decimal, e.g. 0.35 = 35%)

        Returns:
            IV Rank percentage (0-100)
        """
        # Get historical IV data
        iv_history = self._get_iv_history(symbol, days=252)  # 1 year

        if not iv_history or len(iv_history) < 30:
            logger.warning(f"⚠️  Insufficient IV history for {symbol}, using default rank 50")
            return 50.0  # Default middle rank

        iv_low = min(iv_history)
        iv_high = max(iv_history)

        # Avoid division by zero
        if iv_high == iv_low:
            return 50.0

        # Calculate IV Rank
        iv_rank = ((current_iv - iv_low) / (iv_high - iv_low)) * 100
        iv_rank = max(0, min(100, iv_rank))  # Clamp to 0-100

        logger.debug(f"   IV Rank: {iv_rank:.1f}% (current: {current_iv:.2%}, low: {iv_low:.2%}, high: {iv_high:.2%})")
        return iv_rank

    def should_enter_trade(self,
                          symbol: str,
                          option_data: Dict,
                          stock_price: float,
                          verbose: bool = True) -> Dict:
        """
        Comprehensive quality check for trade entry

        Args:
            symbol: Stock symbol
            option_data: Option contract data with keys:
                - impliedVolatility
                - daysToExpiration
                - volume
                - openInterest
                - bid
                - ask
                - strike
            stock_price: Current stock price
            verbose: Print detailed results

        Returns:
            Dictionary with:
            - should_trade: Boolean decision
            - score: Quality score (0-100)
            - checks: Individual check results
            - iv_rank: IV Rank value
            - reason: Rejection reason if applicable
        """
        if verbose:
            logger.info(f"\n🔍 Analyzing trade quality for {symbol}...")

        checks = {
            'iv_rank': False,
            'no_earnings': False,
            'liquidity': False,
            'spread': False,
            'strike_distance': False
        }

        reasons = []

        # 1. IV RANK CHECK - Only sell when IV is elevated
        iv = option_data.get('impliedVolatility', option_data.get('implied_volatility', 0.30))
        iv_rank = self.calculate_iv_rank(symbol, iv)

        if iv_rank >= 50:
            checks['iv_rank'] = True
        else:
            reasons.append(f"IV Rank too low ({iv_rank:.1f}% < 50%)")

        # 2. EARNINGS CHECK - Avoid trades near earnings
        dte = option_data.get('daysToExpiration', option_data.get('dte', 30))
        earnings_check = self.earnings.check_before_trade(symbol, dte)

        if earnings_check['safe']:
            checks['no_earnings'] = True
        else:
            reasons.append(f"Earnings in {earnings_check.get('days_to_earnings', 'unknown')} days")

        # 3. LIQUIDITY CHECK - Ensure sufficient volume and open interest
        volume = option_data.get('volume', 0)
        open_interest = option_data.get('openInterest', option_data.get('open_interest', 0))

        if volume >= 10 and open_interest >= 100:
            checks['liquidity'] = True
        else:
            reasons.append(f"Low liquidity (vol: {volume}, OI: {open_interest})")

        # 4. BID-ASK SPREAD CHECK - Tight spreads only
        bid = option_data.get('bid', 0)
        ask = option_data.get('ask', bid * 1.05 if bid > 0 else 1)  # Default to 5% spread if not provided

        mid_price = (bid + ask) / 2
        spread_pct = (ask - bid) / mid_price * 100 if mid_price > 0 else 100

        if spread_pct < 10:  # Less than 10% spread
            checks['spread'] = True
        else:
            reasons.append(f"Wide spread ({spread_pct:.1f}%)")

        # 5. STRIKE DISTANCE CHECK - Reasonable % OTM
        strike = option_data.get('strike', stock_price * 1.05)
        pct_otm = ((strike - stock_price) / stock_price) * 100

        # Prefer 2-10% OTM strikes
        if 2 <= pct_otm <= 10:
            checks['strike_distance'] = True
        else:
            reasons.append(f"Strike too {'far' if pct_otm > 10 else 'close'} ({pct_otm:.1f}% OTM)")

        # Calculate overall quality score
        score = (sum(checks.values()) / len(checks)) * 100

        # Determine if trade should execute
        should_trade = score >= self.min_score

        result = {
            'should_trade': should_trade,
            'score': score,
            'checks': checks,
            'iv_rank': iv_rank,
            'iv_percentile': self._get_iv_percentile(iv_rank),
            'earnings_risk': not checks['no_earnings'],
            'reasons': reasons if not should_trade else [],
            'recommendation': self._get_recommendation(score, iv_rank)
        }

        if verbose:
            self._print_analysis(symbol, result, option_data)

        return result

    def get_best_entry_time(self, symbol: str) -> Dict:
        """
        Analyze if now is a good time to enter trades for a symbol

        Returns:
            Dictionary with timing analysis
        """
        logger.info(f"📅 Analyzing entry timing for {symbol}...")

        # Get current IV from market
        # Simplified - in practice, fetch from IBKR
        current_iv = 0.35  # Placeholder

        iv_rank = self.calculate_iv_rank(symbol, current_iv)

        # Check earnings
        earnings_check = self.earnings.check_before_trade(symbol, dte=45)

        timing_quality = 'excellent' if iv_rank >= 70 else \
                        'good' if iv_rank >= 50 else \
                        'poor' if iv_rank >= 30 else 'very_poor'

        return {
            'symbol': symbol,
            'timing_quality': timing_quality,
            'iv_rank': iv_rank,
            'current_iv': current_iv,
            'next_earnings': earnings_check.get('next_earnings_date'),
            'should_wait': iv_rank < 50 or not earnings_check['safe'],
            'recommendation': self._get_timing_recommendation(iv_rank, earnings_check)
        }

    def batch_analyze_symbols(self, symbols: List[str]) -> List[Dict]:
        """
        Analyze multiple symbols and rank by trade quality

        Args:
            symbols: List of stock symbols

        Returns:
            List of analysis results sorted by IV Rank
        """
        logger.info(f"\n📊 Batch analyzing {len(symbols)} symbols...")

        results = []
        for symbol in symbols:
            try:
                timing = self.get_best_entry_time(symbol)
                results.append(timing)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")

        # Sort by IV Rank (highest first)
        results.sort(key=lambda x: x['iv_rank'], reverse=True)

        self._print_batch_results(results)
        return results

    def _get_iv_history(self, symbol: str, days: int = 252) -> List[float]:
        """
        Get historical IV data for the symbol

        In practice, this should fetch real data from IBKR or another source.
        For now, returns simulated data.

        Args:
            symbol: Stock symbol
            days: Number of days of history

        Returns:
            List of historical IV values
        """
        # Check cache
        cache_key = f"{symbol}_{days}"
        if cache_key in self._iv_cache:
            return self._iv_cache[cache_key]

        # TODO: Fetch real IV history from IBKR or data provider
        # For now, generate realistic IV history
        np.random.seed(hash(symbol) % 2**32)  # Consistent random data per symbol

        base_iv = 0.30
        iv_range = 0.25
        iv_history = np.random.beta(2, 2, days) * iv_range + (base_iv - iv_range/2)
        iv_history = np.clip(iv_history, 0.10, 0.80).tolist()

        # Cache it
        self._iv_cache[cache_key] = iv_history
        return iv_history

    def _get_iv_percentile(self, iv_rank: float) -> str:
        """Get descriptive percentile for IV Rank"""
        if iv_rank >= 90:
            return "Extremely High (Top 10%)"
        elif iv_rank >= 70:
            return "Very High (Top 30%)"
        elif iv_rank >= 50:
            return "Above Average"
        elif iv_rank >= 30:
            return "Below Average"
        else:
            return "Very Low (Bottom 30%)"

    def _get_recommendation(self, score: float, iv_rank: float) -> str:
        """Get recommendation based on score and IV rank"""
        if score >= 90 and iv_rank >= 70:
            return "EXCELLENT - Strong entry opportunity"
        elif score >= 80 and iv_rank >= 50:
            return "GOOD - Acceptable entry"
        elif score >= 70:
            return "FAIR - Consider waiting for better setup"
        else:
            return "POOR - Wait for better conditions"

    def _get_timing_recommendation(self, iv_rank: float, earnings_check: Dict) -> str:
        """Get timing recommendation"""
        if not earnings_check['safe']:
            return "WAIT - Earnings too close"
        elif iv_rank >= 70:
            return "ENTER NOW - Excellent IV conditions"
        elif iv_rank >= 50:
            return "GOOD TIME - Above average IV"
        elif iv_rank >= 30:
            return "WAIT - IV too low, be patient"
        else:
            return "AVOID - Very poor IV environment"

    def _print_analysis(self, symbol: str, result: Dict, option_data: Dict):
        """Print detailed analysis results"""
        logger.info(f"\n{'='*60}")
        logger.info(f"TRADE QUALITY ANALYSIS - {symbol}")
        logger.info(f"{'='*60}")
        logger.info(f"Overall Score: {result['score']:.1f}/100")
        logger.info(f"Decision: {'✅ TRADE' if result['should_trade'] else '❌ SKIP'}")
        logger.info("")
        logger.info(f"Quality Checks:")
        for check, passed in result['checks'].items():
            status = "✅" if passed else "❌"
            logger.info(f"  {status} {check.replace('_', ' ').title()}")
        logger.info("")
        logger.info(f"IV Rank: {result['iv_rank']:.1f}% - {result['iv_percentile']}")
        logger.info(f"Recommendation: {result['recommendation']}")

        if result['reasons']:
            logger.info(f"\nReasons to skip:")
            for reason in result['reasons']:
                logger.info(f"  - {reason}")

        logger.info(f"{'='*60}")

    def _print_batch_results(self, results: List[Dict]):
        """Print batch analysis results"""
        logger.info(f"\n{'='*60}")
        logger.info("BATCH ANALYSIS RESULTS (sorted by IV Rank)")
        logger.info(f"{'='*60}")

        for i, result in enumerate(results[:10], 1):  # Top 10
            quality = result['timing_quality'].upper()
            logger.info(f"{i:2}. {result['symbol']:6} - "
                       f"IV Rank: {result['iv_rank']:5.1f}% - "
                       f"{quality:12} - "
                       f"{result['recommendation']}")

        logger.info(f"{'='*60}")


def main():
    """Example usage"""
    from ibkr_connector import IBKRConnector, IBKRConfig

    # Initialize connector
    config = IBKRConfig(host='127.0.0.1', port=7497, client_id=1)
    connector = IBKRConnector(config)

    # Create smart entry filter
    filter_system = SmartEntryFilter(connector, min_score=80)

    # Example 1: Check single trade
    print("\n" + "="*60)
    print("EXAMPLE 1: Single Trade Analysis")
    print("="*60)

    option_data = {
        'impliedVolatility': 0.45,
        'daysToExpiration': 30,
        'volume': 150,
        'openInterest': 500,
        'bid': 2.40,
        'ask': 2.50,
        'strike': 440.0
    }

    result = filter_system.should_enter_trade(
        symbol='TSLA',
        option_data=option_data,
        stock_price=430.0,
        verbose=True
    )

    if result['should_trade']:
        print("\n✅ Trade approved - executing...")
    else:
        print(f"\n❌ Trade rejected - {', '.join(result['reasons'])}")

    # Example 2: Timing analysis
    print("\n" + "="*60)
    print("EXAMPLE 2: Entry Timing Analysis")
    print("="*60)

    timing = filter_system.get_best_entry_time('AAPL')
    print(f"\nTiming Quality: {timing['timing_quality']}")
    print(f"IV Rank: {timing['iv_rank']:.1f}%")
    print(f"Recommendation: {timing['recommendation']}")

    # Example 3: Batch analysis
    print("\n" + "="*60)
    print("EXAMPLE 3: Batch Symbol Analysis")
    print("="*60)

    symbols = ['TSLA', 'AAPL', 'MSFT', 'NVDA', 'AMD', 'GOOGL']
    batch_results = filter_system.batch_analyze_symbols(symbols)

    print("\nTop symbols for covered calls:")
    for result in batch_results[:3]:
        if result['iv_rank'] >= 50:
            print(f"  ✅ {result['symbol']} - IV Rank: {result['iv_rank']:.1f}%")


if __name__ == "__main__":
    main()
