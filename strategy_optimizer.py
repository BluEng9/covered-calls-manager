"""
Strategy Optimizer for Covered Calls
Analyzes historical trade performance and suggests optimal parameters

Features:
- Historical performance analysis
- Parameter optimization (DTE, delta, strikes)
- Best symbol identification
- Auto-adjustment recommendations
- Win rate and return analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

from trade_analytics import TradeDatabase, PerformanceAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Results from parameter optimization"""
    optimal_dte: int
    optimal_delta: float
    optimal_delta_range: Tuple[float, float]
    min_annual_return: float
    win_rate: float
    avg_return: float
    avg_profit_per_trade: float
    best_symbols: List[Dict]
    sample_size: int
    confidence: str  # 'high', 'medium', 'low'


class StrategyOptimizer:
    """Optimize covered call strategy parameters based on historical performance"""

    def __init__(self, db: TradeDatabase):
        self.db = db
        self.analyzer = PerformanceAnalyzer(db)

    def find_optimal_parameters(self, days: int = 90) -> Optional[OptimizationResult]:
        """
        Analyze trade history and suggest optimal parameters

        Args:
            days: Number of days of history to analyze

        Returns:
            OptimizationResult with recommended parameters
        """
        logger.info(f"🔍 Analyzing {days} days of trade history...")

        # Get trade history
        trades_df = self._get_trades_dataframe(days)

        if trades_df is None or len(trades_df) < 10:
            logger.warning(f"⚠️  Insufficient data: Only {len(trades_df) if trades_df is not None else 0} trades")
            return None

        logger.info(f"📊 Analyzing {len(trades_df)} trades...")

        # Analyze by DTE
        optimal_dte = self._find_optimal_dte(trades_df)

        # Analyze by Delta
        optimal_delta, delta_range = self._find_optimal_delta(trades_df)

        # Analyze symbols
        best_symbols = self._find_best_symbols(trades_df)

        # Calculate metrics
        win_rate = self._calculate_win_rate(trades_df)
        avg_return = trades_df['annualized_return'].mean()
        avg_profit = trades_df['profit_loss'].mean()

        # Determine confidence based on sample size
        confidence = self._determine_confidence(len(trades_df))

        # Calculate optimal minimum return threshold
        min_return = self._calculate_min_return_threshold(trades_df)

        result = OptimizationResult(
            optimal_dte=optimal_dte,
            optimal_delta=optimal_delta,
            optimal_delta_range=delta_range,
            min_annual_return=min_return,
            win_rate=win_rate,
            avg_return=avg_return,
            avg_profit_per_trade=avg_profit,
            best_symbols=best_symbols,
            sample_size=len(trades_df),
            confidence=confidence
        )

        self._print_results(result)
        return result

    def _get_trades_dataframe(self, days: int) -> Optional[pd.DataFrame]:
        """Get trades as DataFrame"""
        try:
            trades = self.db.get_trade_history(days=days)

            if not trades:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(trades)

            # Calculate additional metrics
            if 'profit_loss' in df.columns and 'premium' in df.columns:
                df['return_pct'] = (df['profit_loss'] / df['premium']) * 100

            # Calculate % OTM at entry
            if 'strike' in df.columns and 'entry_stock_price' in df.columns:
                df['percent_otm'] = ((df['strike'] - df['entry_stock_price']) / df['entry_stock_price']) * 100

            return df

        except Exception as e:
            logger.error(f"Error loading trades: {e}")
            return None

    def _find_optimal_dte(self, df: pd.DataFrame) -> int:
        """Find optimal DTE based on performance"""
        if 'dte_at_open' not in df.columns or 'profit_loss' not in df.columns:
            return 30  # Default

        # Group by DTE buckets
        dte_buckets = pd.cut(df['dte_at_open'],
                            bins=[0, 15, 25, 35, 45, 60, 90],
                            labels=['7-15', '15-25', '25-35', '35-45', '45-60', '60-90'])

        performance = df.groupby(dte_buckets).agg({
            'profit_loss': ['mean', 'sum', 'count'],
            'annualized_return': 'mean'
        })

        # Find DTE bucket with best average profit
        if len(performance) > 0:
            best_bucket_idx = performance['profit_loss']['mean'].idxmax()

            # Map bucket to midpoint
            bucket_midpoints = {
                '7-15': 12,
                '15-25': 21,
                '25-35': 30,
                '35-45': 40,
                '45-60': 52,
                '60-90': 75
            }

            optimal_dte = bucket_midpoints.get(best_bucket_idx, 30)
            logger.info(f"  📅 Optimal DTE: {optimal_dte} days (bucket: {best_bucket_idx})")
            return optimal_dte

        return 30

    def _find_optimal_delta(self, df: pd.DataFrame) -> Tuple[float, Tuple[float, float]]:
        """Find optimal delta based on performance"""
        if 'entry_delta' not in df.columns or 'profit_loss' not in df.columns:
            return 0.30, (0.25, 0.35)  # Defaults

        # Group by delta buckets
        delta_buckets = pd.cut(df['entry_delta'],
                              bins=[0, 0.15, 0.25, 0.35, 0.45, 0.60, 1.0],
                              labels=['<0.15', '0.15-0.25', '0.25-0.35', '0.35-0.45', '0.45-0.60', '>0.60'])

        performance = df.groupby(delta_buckets).agg({
            'profit_loss': ['mean', 'count'],
            'annualized_return': 'mean'
        })

        if len(performance) > 0:
            best_bucket_idx = performance['profit_loss']['mean'].idxmax()

            # Map bucket to range
            bucket_ranges = {
                '<0.15': (0.10, (0.10, 0.15)),
                '0.15-0.25': (0.20, (0.15, 0.25)),
                '0.25-0.35': (0.30, (0.25, 0.35)),
                '0.35-0.45': (0.40, (0.35, 0.45)),
                '0.45-0.60': (0.52, (0.45, 0.60)),
                '>0.60': (0.70, (0.60, 0.80))
            }

            optimal_delta, delta_range = bucket_ranges.get(best_bucket_idx, (0.30, (0.25, 0.35)))
            logger.info(f"  📊 Optimal Delta: {optimal_delta:.2f} (range: {delta_range[0]:.2f}-{delta_range[1]:.2f})")
            return optimal_delta, delta_range

        return 0.30, (0.25, 0.35)

    def _find_best_symbols(self, df: pd.DataFrame, top_n: int = 5) -> List[Dict]:
        """Find best performing symbols"""
        if 'symbol' not in df.columns or 'profit_loss' not in df.columns:
            return []

        symbol_performance = df.groupby('symbol').agg({
            'profit_loss': ['sum', 'mean', 'count'],
            'annualized_return': 'mean'
        }).round(2)

        # Filter symbols with at least 3 trades
        symbol_performance = symbol_performance[symbol_performance['profit_loss']['count'] >= 3]

        if len(symbol_performance) == 0:
            return []

        # Sort by average profit
        symbol_performance = symbol_performance.sort_values(
            ('profit_loss', 'mean'),
            ascending=False
        )

        # Convert to list of dicts
        best_symbols = []
        for symbol, row in symbol_performance.head(top_n).iterrows():
            best_symbols.append({
                'symbol': symbol,
                'avg_profit': float(row['profit_loss']['mean']),
                'total_profit': float(row['profit_loss']['sum']),
                'trades': int(row['profit_loss']['count']),
                'avg_annual_return': float(row['annualized_return']['mean'])
            })

        logger.info(f"  🏆 Best symbols: {[s['symbol'] for s in best_symbols]}")
        return best_symbols

    def _calculate_win_rate(self, df: pd.DataFrame) -> float:
        """Calculate win rate percentage"""
        if 'profit_loss' not in df.columns:
            return 0.0

        winning_trades = len(df[df['profit_loss'] > 0])
        total_trades = len(df)

        if total_trades > 0:
            win_rate = (winning_trades / total_trades) * 100
            logger.info(f"  ✅ Win rate: {win_rate:.1f}% ({winning_trades}/{total_trades})")
            return win_rate

        return 0.0

    def _calculate_min_return_threshold(self, df: pd.DataFrame) -> float:
        """Calculate recommended minimum return threshold"""
        if 'annualized_return' not in df.columns:
            return 20.0

        # Use median of winning trades as threshold
        winning_trades = df[df['profit_loss'] > 0]

        if len(winning_trades) > 0:
            median_return = winning_trades['annualized_return'].median()
            # Set threshold slightly below median to capture most winners
            threshold = max(15.0, median_return * 0.85)
            logger.info(f"  🎯 Recommended min return: {threshold:.1f}%")
            return threshold

        return 20.0

    def _determine_confidence(self, sample_size: int) -> str:
        """Determine confidence level based on sample size"""
        if sample_size >= 50:
            return 'high'
        elif sample_size >= 20:
            return 'medium'
        else:
            return 'low'

    def _print_results(self, result: OptimizationResult):
        """Print optimization results"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 OPTIMIZATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Sample Size: {result.sample_size} trades")
        logger.info(f"Confidence: {result.confidence.upper()}")
        logger.info("")
        logger.info(f"Optimal DTE: {result.optimal_dte} days")
        logger.info(f"Optimal Delta: {result.optimal_delta:.2f} ({result.optimal_delta_range[0]:.2f}-{result.optimal_delta_range[1]:.2f})")
        logger.info(f"Min Annual Return: {result.min_annual_return:.1f}%")
        logger.info("")
        logger.info(f"Performance:")
        logger.info(f"  Win Rate: {result.win_rate:.1f}%")
        logger.info(f"  Avg Annual Return: {result.avg_return:.1f}%")
        logger.info(f"  Avg Profit/Trade: ${result.avg_profit_per_trade:.2f}")
        logger.info("")
        if result.best_symbols:
            logger.info("Best Symbols:")
            for sym in result.best_symbols:
                logger.info(f"  {sym['symbol']}: ${sym['avg_profit']:.2f}/trade ({sym['trades']} trades)")
        logger.info("=" * 60)

    def auto_adjust_parameters(self,
                               current_params: Dict,
                               adjustment_rate: float = 0.3) -> Dict:
        """
        Automatically adjust trading parameters based on historical results

        Args:
            current_params: Current parameter settings
            adjustment_rate: How much to adjust (0.0-1.0, default 0.3 = 30% towards optimal)

        Returns:
            Adjusted parameters
        """
        logger.info("🔧 Auto-adjusting parameters...")

        optimal = self.find_optimal_parameters()

        if not optimal:
            logger.warning("⚠️  Insufficient data for auto-adjustment")
            return current_params

        # Gradually adjust towards optimal (weighted average)
        adjusted = {
            'target_dte': int(
                (1 - adjustment_rate) * current_params.get('dte', 30) +
                adjustment_rate * optimal.optimal_dte
            ),
            'target_delta': round(
                (1 - adjustment_rate) * current_params.get('delta', 0.30) +
                adjustment_rate * optimal.optimal_delta,
                2
            ),
            'min_delta': round(
                (1 - adjustment_rate) * current_params.get('min_delta', 0.20) +
                adjustment_rate * optimal.optimal_delta_range[0],
                2
            ),
            'max_delta': round(
                (1 - adjustment_rate) * current_params.get('max_delta', 0.40) +
                adjustment_rate * optimal.optimal_delta_range[1],
                2
            ),
            'min_annual_return': round(
                (1 - adjustment_rate) * current_params.get('min_annual_return', 20) +
                adjustment_rate * optimal.min_annual_return,
                1
            )
        }

        logger.info("\n📊 Parameter Adjustments:")
        logger.info(f"  DTE: {current_params.get('dte', 30)} → {adjusted['target_dte']}")
        logger.info(f"  Delta: {current_params.get('delta', 0.30):.2f} → {adjusted['target_delta']:.2f}")
        logger.info(f"  Min Return: {current_params.get('min_annual_return', 20):.1f}% → {adjusted['min_annual_return']:.1f}%")

        return adjusted

    def generate_report(self, days: int = 90) -> str:
        """Generate a text report of optimization analysis"""
        result = self.find_optimal_parameters(days)

        if not result:
            return "Insufficient data for optimization report"

        report = f"""
STRATEGY OPTIMIZATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Analysis Period: Last {days} days
Sample Size: {result.sample_size} trades
Confidence Level: {result.confidence.upper()}

RECOMMENDED PARAMETERS
━━━━━━━━━━━━━━━━━━━━━━━━
DTE Range:          {result.optimal_dte - 5} - {result.optimal_dte + 5} days
Target DTE:         {result.optimal_dte} days
Delta Range:        {result.optimal_delta_range[0]:.2f} - {result.optimal_delta_range[1]:.2f}
Target Delta:       {result.optimal_delta:.2f}
Min Annual Return:  {result.min_annual_return:.1f}%

HISTORICAL PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━
Win Rate:           {result.win_rate:.1f}%
Avg Annual Return:  {result.avg_return:.1f}%
Avg Profit/Trade:   ${result.avg_profit_per_trade:.2f}

BEST PERFORMING SYMBOLS
━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for sym in result.best_symbols:
            report += f"{sym['symbol']:6} - ${sym['avg_profit']:7.2f}/trade ({sym['trades']} trades, {sym['avg_annual_return']:.1f}% annual)\n"

        report += "\n"
        return report


def main():
    """Example usage"""
    from trade_analytics import TradeDatabase

    # Initialize database
    db = TradeDatabase()

    # Create optimizer
    optimizer = StrategyOptimizer(db)

    # Find optimal parameters
    result = optimizer.find_optimal_parameters(days=90)

    if result:
        # Generate report
        report = optimizer.generate_report(days=90)
        print(report)

        # Example: Auto-adjust parameters
        current_params = {
            'dte': 30,
            'delta': 0.30,
            'min_delta': 0.20,
            'max_delta': 0.40,
            'min_annual_return': 20.0
        }

        adjusted = optimizer.auto_adjust_parameters(current_params, adjustment_rate=0.3)
        print("\nAdjusted Parameters:")
        for key, value in adjusted.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
