"""
Comprehensive Test Suite for Covered Calls System
Tests for strategy engine, IBKR connector, and portfolio management
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from covered_calls_system import (
    Stock, OptionContract, CoveredCall, OptionType, PositionStatus,
    RiskLevel, CoveredCallStrategy, RollStrategy, PortfolioManager,
    GreeksCalculator, AlertSystem
)


class TestStock(unittest.TestCase):
    """Test Stock class"""

    def setUp(self):
        self.stock = Stock(
            symbol="AAPL",
            quantity=100,
            avg_cost=180.0,
            current_price=185.0
        )

    def test_market_value(self):
        """Test market value calculation"""
        self.assertEqual(self.stock.market_value, 18500.0)

    def test_unrealized_pnl(self):
        """Test unrealized P&L calculation"""
        self.assertEqual(self.stock.unrealized_pnl, 500.0)

    def test_unrealized_pnl_pct(self):
        """Test unrealized P&L percentage"""
        expected = (185.0 / 180.0 - 1) * 100
        self.assertAlmostEqual(self.stock.unrealized_pnl_pct, expected, places=2)


class TestOptionContract(unittest.TestCase):
    """Test OptionContract class"""

    def setUp(self):
        self.option = OptionContract(
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

    def test_mid_price(self):
        """Test mid price calculation"""
        self.assertEqual(self.option.mid_price, 3.50)

    def test_days_to_expiration(self):
        """Test DTE calculation"""
        dte = self.option.days_to_expiration
        self.assertTrue(29 <= dte <= 31)  # Allow for timing differences

    def test_is_liquid(self):
        """Test liquidity check"""
        self.assertTrue(self.option.is_liquid)

        # Test illiquid option
        illiquid = OptionContract(
            symbol="TEST",
            strike=100.0,
            expiration=datetime.now() + timedelta(days=30),
            option_type=OptionType.CALL,
            premium=1.0,
            implied_volatility=30.0,
            delta=0.25,
            gamma=0.01,
            theta=-0.03,
            vega=0.10,
            volume=50,  # Low volume
            open_interest=100,  # Low OI
            bid=0.95,
            ask=1.05
        )
        self.assertFalse(illiquid.is_liquid)

    def test_bid_ask_spread(self):
        """Test bid-ask spread percentage"""
        expected = (3.55 - 3.45) / 3.50 * 100
        self.assertAlmostEqual(self.option.bid_ask_spread, expected, places=2)


class TestCoveredCall(unittest.TestCase):
    """Test CoveredCall position"""

    def setUp(self):
        self.stock = Stock("AAPL", 100, 180.0, 185.0)
        self.option = OptionContract(
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
        self.position = CoveredCall(
            id="CC001",
            stock=self.stock,
            option=self.option,
            quantity=1,
            entry_date=datetime.now(),
            status=PositionStatus.OPEN,
            premium_collected=350.0,
            commission=1.0
        )

    def test_net_premium(self):
        """Test net premium after commission"""
        self.assertEqual(self.position.net_premium, 349.0)

    def test_max_profit(self):
        """Test maximum profit calculation"""
        stock_profit = (190.0 - 180.0) * 100
        total = stock_profit + 349.0
        self.assertEqual(self.position.max_profit, total)

    def test_return_if_assigned(self):
        """Test return if assigned"""
        cost_basis = 180.0 * 100
        expected = (self.position.max_profit / cost_basis) * 100
        self.assertAlmostEqual(self.position.return_if_assigned, expected, places=2)

    def test_breakeven_price(self):
        """Test breakeven calculation"""
        expected = 180.0 - (349.0 / 100)
        self.assertAlmostEqual(self.position.breakeven_price, expected, places=2)

    def test_downside_protection(self):
        """Test downside protection percentage"""
        expected = (349.0 / (185.0 * 100)) * 100
        self.assertAlmostEqual(self.position.downside_protection, expected, places=2)

    def test_annualized_return(self):
        """Test annualized return calculation"""
        days = self.option.days_to_expiration
        expected = self.position.return_if_assigned * (365 / days)
        self.assertAlmostEqual(self.position.annualized_return, expected, places=2)


class TestGreeksCalculator(unittest.TestCase):
    """Test Greeks calculations"""

    def test_calculate_delta_call(self):
        """Test delta calculation for call option"""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        delta = GreeksCalculator.calculate_delta(S, K, T, r, sigma, OptionType.CALL)

        # Delta should be around 0.5 for ATM call with 1 year to expiration
        self.assertTrue(0.4 < delta < 0.7)

    def test_calculate_delta_put(self):
        """Test delta calculation for put option"""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        delta = GreeksCalculator.calculate_delta(S, K, T, r, sigma, OptionType.PUT)

        # Put delta should be negative
        self.assertTrue(-0.7 < delta < -0.3)

    def test_calculate_gamma(self):
        """Test gamma calculation"""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        gamma = GreeksCalculator.calculate_gamma(S, K, T, r, sigma)

        # Gamma should be positive
        self.assertGreater(gamma, 0)

    def test_calculate_theta(self):
        """Test theta calculation"""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        theta = GreeksCalculator.calculate_theta(S, K, T, r, sigma, OptionType.CALL)

        # Theta should be negative (time decay)
        self.assertLess(theta, 0)

    def test_calculate_vega(self):
        """Test vega calculation"""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        vega = GreeksCalculator.calculate_vega(S, K, T, r, sigma)

        # Vega should be positive
        self.assertGreater(vega, 0)


class TestCoveredCallStrategy(unittest.TestCase):
    """Test strategy selection and scoring"""

    def setUp(self):
        self.strategy = CoveredCallStrategy(RiskLevel.MODERATE)
        self.stock_price = 185.0

    def create_test_option(self, strike, premium, delta, iv, dte, volume=5000, oi=10000):
        """Helper to create test option"""
        return OptionContract(
            symbol="AAPL",
            strike=strike,
            expiration=datetime.now() + timedelta(days=dte),
            option_type=OptionType.CALL,
            premium=premium,
            implied_volatility=iv,
            delta=delta,
            gamma=0.015,
            theta=-0.05,
            vega=0.12,
            volume=volume,
            open_interest=oi,
            bid=premium - 0.05,
            ask=premium + 0.05
        )

    def test_score_option_moderate(self):
        """Test option scoring for moderate risk"""
        option = self.create_test_option(
            strike=190.0,
            premium=3.50,
            delta=0.30,
            iv=25.0,
            dte=30
        )

        score = self.strategy.score_option(option, self.stock_price)

        # Should score reasonably well
        self.assertGreater(score, 50)

    def test_score_option_high_iv(self):
        """Test scoring with high IV"""
        option = self.create_test_option(
            strike=190.0,
            premium=5.00,
            delta=0.30,
            iv=80.0,  # Very high IV
            dte=30
        )

        score = self.strategy.score_option(option, self.stock_price)

        # High IV should still score decently but get penalty
        self.assertGreater(score, 40)

    def test_score_option_illiquid(self):
        """Test scoring illiquid option"""
        option = self.create_test_option(
            strike=190.0,
            premium=3.50,
            delta=0.30,
            iv=25.0,
            dte=30,
            volume=50,  # Low volume
            oi=100  # Low OI
        )

        score = self.strategy.score_option(option, self.stock_price)

        # Should score lower due to liquidity
        self.assertLess(score, 80)

    def test_find_best_strike(self):
        """Test finding best strikes"""
        options = [
            self.create_test_option(185.0, 5.00, 0.50, 30.0, 30),
            self.create_test_option(190.0, 3.50, 0.30, 25.0, 30),
            self.create_test_option(195.0, 2.00, 0.20, 22.0, 30),
            self.create_test_option(200.0, 1.00, 0.10, 20.0, 30),
        ]

        best = self.strategy.find_best_strike(options, self.stock_price, top_n=3)

        # Should return 3 options
        self.assertEqual(len(best), 3)

        # Should be sorted by score
        self.assertGreaterEqual(best[0][1], best[1][1])
        self.assertGreaterEqual(best[1][1], best[2][1])


class TestRollStrategy(unittest.TestCase):
    """Test rolling strategy logic"""

    def setUp(self):
        self.stock = Stock("AAPL", 100, 180.0, 189.0)  # Stock near strike
        self.option = OptionContract(
            symbol="AAPL",
            strike=190.0,
            expiration=datetime.now() + timedelta(days=7),
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
        self.position = CoveredCall(
            id="CC001",
            stock=self.stock,
            option=self.option,
            quantity=1,
            entry_date=datetime.now() - timedelta(days=23),
            status=PositionStatus.OPEN,
            premium_collected=350.0
        )

    def test_should_roll_near_expiration(self):
        """Test rolling decision near expiration"""
        should_roll = RollStrategy.should_roll(self.position, 189.0)
        self.assertTrue(should_roll)

    def test_should_not_roll_far_from_expiration(self):
        """Test not rolling when far from expiration"""
        # Create position with more DTE
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
            stock=self.stock,
            option=option,
            quantity=1,
            entry_date=datetime.now(),
            status=PositionStatus.OPEN,
            premium_collected=350.0
        )

        should_roll = RollStrategy.should_roll(position, 185.0)
        self.assertFalse(should_roll)

    def test_calculate_roll_credit(self):
        """Test roll credit calculation"""
        old_option = OptionContract(
            symbol="AAPL",
            strike=190.0,
            expiration=datetime.now() + timedelta(days=7),
            option_type=OptionType.CALL,
            premium=3.50,
            implied_volatility=25.0,
            delta=0.30,
            gamma=0.015,
            theta=-0.05,
            vega=0.12,
            volume=5000,
            open_interest=10000,
            bid=2.00,
            ask=2.10
        )

        new_option = OptionContract(
            symbol="AAPL",
            strike=195.0,
            expiration=datetime.now() + timedelta(days=37),
            option_type=OptionType.CALL,
            premium=4.00,
            implied_volatility=26.0,
            delta=0.28,
            gamma=0.014,
            theta=-0.04,
            vega=0.13,
            volume=4000,
            open_interest=8000,
            bid=3.90,
            ask=4.10
        )

        credit = RollStrategy.calculate_roll_credit(old_option, new_option, 1)

        # Buy back at 2.10, sell new at 3.90
        expected = (3.90 - 2.10) * 100
        self.assertEqual(credit, expected)


class TestPortfolioManager(unittest.TestCase):
    """Test portfolio management"""

    def setUp(self):
        self.portfolio = PortfolioManager()

    def create_test_position(self, symbol, stock_price, strike, premium):
        """Helper to create test position"""
        stock = Stock(symbol, 100, stock_price - 5, stock_price)
        option = OptionContract(
            symbol=symbol,
            strike=strike,
            expiration=datetime.now() + timedelta(days=30),
            option_type=OptionType.CALL,
            premium=premium,
            implied_volatility=25.0,
            delta=0.30,
            gamma=0.015,
            theta=-0.05,
            vega=0.12,
            volume=5000,
            open_interest=10000,
            bid=premium - 0.05,
            ask=premium + 0.05
        )
        return CoveredCall(
            id=f"CC_{symbol}",
            stock=stock,
            option=option,
            quantity=1,
            entry_date=datetime.now(),
            status=PositionStatus.OPEN,
            premium_collected=premium * 100
        )

    def test_add_position(self):
        """Test adding position"""
        pos = self.create_test_position("AAPL", 185.0, 190.0, 3.50)
        self.portfolio.add_position(pos)

        self.assertEqual(len(self.portfolio.positions), 1)
        self.assertEqual(self.portfolio.positions[0].id, "CC_AAPL")

    def test_close_position(self):
        """Test closing position"""
        pos = self.create_test_position("AAPL", 185.0, 190.0, 3.50)
        self.portfolio.add_position(pos)
        self.portfolio.close_position("CC_AAPL", 0, datetime.now(), PositionStatus.EXPIRED)

        self.assertEqual(len(self.portfolio.positions), 0)
        self.assertEqual(len(self.portfolio.closed_positions), 1)

    def test_portfolio_metrics(self):
        """Test portfolio metrics calculation"""
        pos1 = self.create_test_position("AAPL", 185.0, 190.0, 3.50)
        pos2 = self.create_test_position("MSFT", 380.0, 390.0, 7.00)

        self.portfolio.add_position(pos1)
        self.portfolio.add_position(pos2)

        metrics = self.portfolio.get_portfolio_metrics()

        self.assertEqual(metrics['total_positions'], 2)
        self.assertGreater(metrics['total_stock_value'], 0)
        self.assertGreater(metrics['total_premium_collected'], 0)

    def test_expiration_calendar(self):
        """Test expiration calendar"""
        pos1 = self.create_test_position("AAPL", 185.0, 190.0, 3.50)
        pos2 = self.create_test_position("MSFT", 380.0, 390.0, 7.00)

        self.portfolio.add_position(pos1)
        self.portfolio.add_position(pos2)

        calendar = self.portfolio.get_expiration_calendar()

        # Should have entries
        self.assertGreater(len(calendar), 0)

    def test_at_risk_positions(self):
        """Test finding at-risk positions"""
        # Create ITM position
        pos = self.create_test_position("AAPL", 195.0, 190.0, 3.50)
        self.portfolio.add_position(pos)

        at_risk = self.portfolio.get_at_risk_positions(threshold_pct=5.0)

        # Should identify ITM position as at-risk
        self.assertEqual(len(at_risk), 1)


class TestAlertSystem(unittest.TestCase):
    """Test alert system"""

    def setUp(self):
        self.alert_system = AlertSystem()
        self.portfolio = PortfolioManager()

    def create_test_position(self, symbol, stock_price, strike, dte, volume=5000):
        """Helper to create test position"""
        stock = Stock(symbol, 100, stock_price - 5, stock_price)
        option = OptionContract(
            symbol=symbol,
            strike=strike,
            expiration=datetime.now() + timedelta(days=dte),
            option_type=OptionType.CALL,
            premium=3.50,
            implied_volatility=25.0,
            delta=0.30,
            gamma=0.015,
            theta=-0.05,
            vega=0.12,
            volume=volume,
            open_interest=10000,
            bid=3.45,
            ask=3.55
        )
        return CoveredCall(
            id=f"CC_{symbol}",
            stock=stock,
            option=option,
            quantity=1,
            entry_date=datetime.now(),
            status=PositionStatus.OPEN,
            premium_collected=350.0
        )

    def test_assignment_risk_alert(self):
        """Test assignment risk alert"""
        # Create ITM position
        pos = self.create_test_position("AAPL", 195.0, 190.0, 30)
        self.portfolio.add_position(pos)

        alerts = self.alert_system.check_alerts(self.portfolio)

        # Should have assignment risk alert
        assignment_alerts = [a for a in alerts if a['type'] == 'ASSIGNMENT_RISK']
        self.assertGreater(len(assignment_alerts), 0)

    def test_expiration_soon_alert(self):
        """Test expiration approaching alert"""
        pos = self.create_test_position("AAPL", 185.0, 190.0, 5)  # 5 DTE
        self.portfolio.add_position(pos)

        alerts = self.alert_system.check_alerts(self.portfolio)

        # Should have expiration alert
        exp_alerts = [a for a in alerts if a['type'] == 'EXPIRATION_SOON']
        self.assertGreater(len(exp_alerts), 0)

    def test_low_liquidity_alert(self):
        """Test low liquidity alert"""
        pos = self.create_test_position("TEST", 100.0, 105.0, 30, volume=50)
        self.portfolio.add_position(pos)

        alerts = self.alert_system.check_alerts(self.portfolio)

        # Should have liquidity alert
        liq_alerts = [a for a in alerts if a['type'] == 'LOW_LIQUIDITY']
        self.assertGreater(len(liq_alerts), 0)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestStock))
    suite.addTests(loader.loadTestsFromTestCase(TestOptionContract))
    suite.addTests(loader.loadTestsFromTestCase(TestCoveredCall))
    suite.addTests(loader.loadTestsFromTestCase(TestGreeksCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestCoveredCallStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestRollStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestPortfolioManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertSystem))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
