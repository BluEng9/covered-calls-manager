#!/usr/bin/env python3
"""
Covered Calls Backtester
מבדק אסטרטגיות Covered Call היסטוריות על מניות
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class CoveredCallBacktester:
    """Backtester for Covered Call strategies"""

    def __init__(self, symbol: str, start_date: str, end_date: str, quantity: int = 100):
        """
        Initialize backtester

        Args:
            symbol: Stock ticker (e.g., 'TSLA')
            start_date: Start date 'YYYY-MM-DD'
            end_date: End date 'YYYY-MM-DD'
            quantity: Number of shares (must be multiple of 100)
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.quantity = quantity
        self.num_contracts = quantity // 100

        # Download historical data
        print(f"📊 Downloading {symbol} data from {start_date} to {end_date}...")
        self.stock = yf.Ticker(symbol)
        self.price_data = self.stock.history(start=start_date, end=end_date)

        if len(self.price_data) == 0:
            raise ValueError(f"No data found for {symbol}")

        print(f"✅ Downloaded {len(self.price_data)} days of data")

    def estimate_option_premium(self, stock_price: float, strike: float,
                                days_to_expiry: int, volatility: float = 0.5) -> float:
        """
        Estimate Call option premium using simplified Black-Scholes

        This is a ROUGH estimate. Real premiums vary based on:
        - Actual implied volatility
        - Bid-ask spread
        - Supply/demand

        Args:
            stock_price: Current stock price
            strike: Strike price
            days_to_expiry: Days until expiration
            volatility: Annualized volatility (default 50%)

        Returns:
            Estimated premium per share
        """
        # Simplified premium estimation
        # Real-world would use actual IV from options chain

        # Calculate moneyness
        moneyness = (strike - stock_price) / stock_price

        # Time value (theta decay)
        time_value = volatility * np.sqrt(days_to_expiry / 365) * stock_price * 0.4

        # Intrinsic value
        intrinsic_value = max(0, stock_price - strike)

        # Total premium
        premium = intrinsic_value + time_value

        # Adjust for moneyness (OTM options worth less)
        if moneyness > 0:
            premium *= np.exp(-moneyness * 5)  # Exponential decay for OTM

        # Floor at $0.10
        return max(0.10, premium)

    def backtest_strategy(self, strike_pct: float = 0.05, days: int = 30,
                          strategy_name: str = "Conservative") -> Dict:
        """
        Backtest a Covered Call strategy

        Args:
            strike_pct: Strike as percentage above current price (e.g., 0.05 = 5%)
            days: Days to expiration
            strategy_name: Name for this strategy

        Returns:
            Dictionary with backtest results
        """
        print(f"\n{'='*60}")
        print(f"🎯 Backtesting: {strategy_name}")
        print(f"   Strike: {strike_pct*100:.1f}% above stock price")
        print(f"   Expiration: {days} days")
        print(f"{'='*60}\n")

        results = {
            'strategy_name': strategy_name,
            'strike_pct': strike_pct,
            'days': days,
            'trades': [],
            'total_premium': 0,
            'total_stock_gains': 0,
            'total_missed_gains': 0,
            'num_trades': 0,
            'num_assigned': 0,
            'win_rate': 0,
            'avg_premium_per_trade': 0,
            'total_return': 0,
            'total_return_pct': 0,
            'annualized_return_pct': 0
        }

        # Start from first available trading day
        current_idx = 0

        holding_stock = True
        entry_price = None

        while current_idx < len(self.price_data):
            current_date = self.price_data.index[current_idx]
            stock_price = self.price_data.iloc[current_idx]['Close']

            # If not holding stock, skip
            if not holding_stock:
                current_idx += 1
                continue

            # Set entry price
            if entry_price is None:
                entry_price = stock_price

            # Sell Covered Call
            strike = stock_price * (1 + strike_pct)

            # Estimate premium (this is rough - real data would be better)
            avg_volatility = self.price_data['Close'].pct_change().std() * np.sqrt(252)
            premium = self.estimate_option_premium(
                stock_price, strike, days, avg_volatility
            )

            premium_total = premium * self.quantity

            # Find expiration date (look ahead 'days' trading days)
            expiry_idx = current_idx + days
            if expiry_idx >= len(self.price_data):
                # Not enough data left
                break

            expiry_date_actual = self.price_data.index[expiry_idx]
            expiry_price = self.price_data.iloc[expiry_idx]['Close']

            # Check if assigned (stock price > strike at expiry)
            assigned = expiry_price >= strike

            # Calculate P&L
            if assigned:
                # Stock called away at strike price
                stock_gain = (strike - entry_price) * self.quantity
                missed_gain = max(0, (expiry_price - strike) * self.quantity)
                # Reset entry price to strike (as if we bought back at strike)
                entry_price = strike
                holding_stock = True  # We still hold the position conceptually
            else:
                # Keep stock
                stock_gain = 0
                missed_gain = 0
                holding_stock = True

            total_profit = premium_total + stock_gain

            # Record trade
            trade = {
                'date': current_date.strftime('%Y-%m-%d'),
                'entry_price': round(stock_price, 2),
                'strike': round(strike, 2),
                'premium': round(premium, 2),
                'premium_total': round(premium_total, 2),
                'expiry_date': expiry_date_actual.strftime('%Y-%m-%d'),
                'expiry_price': round(expiry_price, 2),
                'assigned': assigned,
                'stock_gain': round(stock_gain, 2),
                'missed_gain': round(missed_gain, 2),
                'total_profit': round(total_profit, 2)
            }

            results['trades'].append(trade)
            results['total_premium'] += premium_total
            results['total_stock_gains'] += stock_gain
            results['total_missed_gains'] += missed_gain
            results['num_trades'] += 1
            if assigned:
                results['num_assigned'] += 1

            # Print trade summary
            status = "🔴 ASSIGNED" if assigned else "✅ EXPIRED"
            print(f"{current_date.strftime('%Y-%m-%d')}: {status}")
            print(f"   Entry: ${stock_price:.2f} | Strike: ${strike:.2f} | Expiry: ${expiry_price:.2f}")
            print(f"   Premium: ${premium_total:.2f} | Profit: ${total_profit:.2f}")
            if assigned:
                print(f"   Missed: ${missed_gain:.2f}")
            print()

            # Move to next trade date (start from expiry + 1)
            current_idx = expiry_idx + 1

        # Calculate summary statistics
        if results['num_trades'] > 0:
            results['win_rate'] = (results['num_trades'] - results['num_assigned']) / results['num_trades']
            results['avg_premium_per_trade'] = results['total_premium'] / results['num_trades']
            results['total_return'] = results['total_premium'] + results['total_stock_gains']
            results['total_return_pct'] = (results['total_return'] / (entry_price * self.quantity)) * 100 if entry_price else 0

            # Annualized return
            days_held = (pd.Timestamp(self.end_date) - pd.Timestamp(self.start_date)).days
            if days_held > 0:
                results['annualized_return_pct'] = results['total_return_pct'] * (365 / days_held)

        return results

    def compare_strategies(self) -> pd.DataFrame:
        """
        Compare multiple strategies

        Returns:
            DataFrame with comparison
        """
        strategies = [
            {
                'name': 'Very Conservative (10% OTM, 45 days)',
                'strike_pct': 0.10,
                'days': 45
            },
            {
                'name': 'Conservative (5% OTM, 30 days)',
                'strike_pct': 0.05,
                'days': 30
            },
            {
                'name': 'Moderate (3% OTM, 30 days)',
                'strike_pct': 0.03,
                'days': 30
            },
            {
                'name': 'Aggressive (2% OTM, 21 days)',
                'strike_pct': 0.02,
                'days': 21
            },
            {
                'name': 'Very Aggressive (ATM, 14 days)',
                'strike_pct': 0.00,
                'days': 14
            }
        ]

        comparison = []

        for strat in strategies:
            result = self.backtest_strategy(
                strike_pct=strat['strike_pct'],
                days=strat['days'],
                strategy_name=strat['name']
            )

            comparison.append({
                'Strategy': result['strategy_name'],
                'Trades': result['num_trades'],
                'Assigned': result['num_assigned'],
                'Win Rate': f"{result['win_rate']*100:.1f}%",
                'Total Premium': f"${result['total_premium']:.2f}",
                'Stock Gains': f"${result['total_stock_gains']:.2f}",
                'Missed Gains': f"${result['total_missed_gains']:.2f}",
                'Total Return': f"${result['total_return']:.2f}",
                'Return %': f"{result['total_return_pct']:.2f}%",
                'Annualized %': f"{result.get('annualized_return_pct', 0):.2f}%"
            })

        df = pd.DataFrame(comparison)
        return df

def main():
    """Run backtester"""

    # Configuration
    SYMBOL = 'TSLA'
    START_DATE = '2024-04-01'  # 6 months ago
    END_DATE = '2024-10-01'    # Before today
    QUANTITY = 194  # User's actual position

    print("="*60)
    print("📈 COVERED CALLS BACKTESTER")
    print("="*60)
    print(f"Symbol: {SYMBOL}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Quantity: {QUANTITY} shares ({QUANTITY//100} contracts)")
    print("="*60)

    # Create backtester
    try:
        backtester = CoveredCallBacktester(
            symbol=SYMBOL,
            start_date=START_DATE,
            end_date=END_DATE,
            quantity=QUANTITY
        )

        # Compare strategies
        print("\n🔍 Comparing strategies...\n")
        comparison = backtester.compare_strategies()

        print("\n" + "="*60)
        print("📊 STRATEGY COMPARISON")
        print("="*60)
        print(comparison.to_string(index=False))
        print("="*60)

        # Save results
        output_file = f'backtest_results_{SYMBOL}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        comparison.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")

        # Get current TSLA price
        current_price = backtester.price_data['Close'].iloc[-1]
        print(f"\n📍 Current {SYMBOL} price: ${current_price:.2f}")

        # Recommendations
        print("\n" + "="*60)
        print("💡 RECOMMENDATIONS")
        print("="*60)

        best_return = comparison.loc[comparison['Total Return'].str.replace('$', '').str.replace(',', '').astype(float).idxmax()]
        best_win_rate = comparison.loc[comparison['Win Rate'].str.replace('%', '').astype(float).idxmax()]

        print(f"\n🏆 Best Total Return: {best_return['Strategy']}")
        print(f"   Return: {best_return['Total Return']} ({best_return['Return %']})")
        print(f"   Annualized: {best_return['Annualized %']}")

        print(f"\n🎯 Best Win Rate: {best_win_rate['Strategy']}")
        print(f"   Win Rate: {best_win_rate['Win Rate']}")
        print(f"   Return: {best_win_rate['Total Return']} ({best_win_rate['Return %']})")

        print("\n" + "="*60)
        print("⚠️  IMPORTANT NOTES")
        print("="*60)
        print("1. These are ESTIMATES using simplified models")
        print("2. Real option premiums vary based on:")
        print("   - Actual Implied Volatility (IV)")
        print("   - Bid-Ask spreads")
        print("   - Market conditions")
        print("3. Past performance ≠ Future results")
        print("4. Consider transaction costs (~$0.65/contract)")
        print("5. Tax implications not included")
        print("="*60)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
