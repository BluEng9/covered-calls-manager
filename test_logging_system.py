#!/usr/bin/env python3
"""
🧪 Unit Tests for Logging System
"""

import unittest
import sys
import os
from pathlib import Path
import tempfile
import logging
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_system import (
    TradingLogger, get_logger, get_trade_logger, get_error_logger,
    log_function_call, log_errors, log_trade, log_performance,
    log_trade_execution, log_connection_event
)


class TestTradingLogger(unittest.TestCase):
    """Test cases for TradingLogger"""
    
    def setUp(self):
        """Setup test fixtures"""
        # Change to temp directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Reset singleton
        TradingLogger._instance = None
        TradingLogger._initialized = False
    
    def tearDown(self):
        """Cleanup after tests"""
        # Return to original directory
        os.chdir(self.original_cwd)
        
        # Reset singleton
        TradingLogger._instance = None
        TradingLogger._initialized = False
    
    def test_singleton_pattern(self):
        """Test that TradingLogger uses singleton pattern"""
        logger1 = TradingLogger()
        logger2 = TradingLogger()
        
        self.assertIs(logger1, logger2, "TradingLogger should be singleton")
    
    def test_logger_initialization(self):
        """Test logger is properly initialized"""
        trading_logger = TradingLogger()
        
        # Check log directory was created
        log_dir = Path("logs")
        self.assertTrue(log_dir.exists(), "Log directory should be created")
        
        # Check main logger exists
        main_logger = trading_logger.get_logger('main')
        self.assertIsNotNone(main_logger)
    
    def test_get_logger(self):
        """Test getting different loggers"""
        # Get main logger
        main_logger = get_logger('main')
        self.assertIsNotNone(main_logger)
        
        # Get trade logger
        trade_logger = get_trade_logger()
        self.assertIsNotNone(trade_logger)
        
        # Get error logger
        error_logger = get_error_logger()
        self.assertIsNotNone(error_logger)
    
    def test_specialized_loggers(self):
        """Test specialized loggers are created"""
        trading_logger = TradingLogger()
        
        # Check specialized loggers
        self.assertIn('trades', trading_logger.loggers)
        self.assertIn('orders', trading_logger.loggers)
        self.assertIn('errors', trading_logger.loggers)
    
    def test_log_levels(self):
        """Test different log levels"""
        logger = get_logger('main')
        
        # These should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
    
    def test_log_files_created(self):
        """Test that log files are created"""
        # Initialize logger
        TradingLogger()
        
        # Write some logs
        logger = get_logger('main')
        logger.info("Test message")
        
        # Check log file was created
        log_file = Path("logs/trading.log")
        self.assertTrue(log_file.exists(), "Log file should be created")
        
        # Check file has content
        content = log_file.read_text()
        self.assertIn("Test message", content)


class TestLoggingDecorators(unittest.TestCase):
    """Test logging decorators"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        TradingLogger._instance = None
        TradingLogger._initialized = False
    
    def tearDown(self):
        """Cleanup"""
        os.chdir(self.original_cwd)
        TradingLogger._instance = None
        TradingLogger._initialized = False
    
    def test_log_function_call_decorator(self):
        """Test log_function_call decorator"""
        
        @log_function_call()
        def test_function():
            return "Success"
        
        # Should not raise exception
        result = test_function()
        self.assertEqual(result, "Success")
        
        # Check log file
        log_file = Path("logs/trading.log")
        if log_file.exists():
            content = log_file.read_text()
            self.assertIn("test_function", content)
    
    def test_log_errors_decorator(self):
        """Test log_errors decorator"""
        
        @log_errors(reraise=False)
        def error_function():
            raise ValueError("Test error")
        
        # Should not raise exception (reraise=False)
        result = error_function()
        self.assertIsNone(result)
        
        # Check error log
        error_log = Path("logs/errors.log")
        if error_log.exists():
            content = error_log.read_text()
            self.assertIn("Test error", content)
    
    def test_log_errors_decorator_reraise(self):
        """Test log_errors decorator with reraise=True"""
        
        @log_errors(reraise=True)
        def error_function():
            raise ValueError("Test error")
        
        # Should raise exception
        with self.assertRaises(ValueError):
            error_function()
    
    def test_log_performance_decorator(self):
        """Test log_performance decorator"""
        
        @log_performance
        def slow_function():
            time.sleep(0.1)
            return "Done"
        
        result = slow_function()
        self.assertEqual(result, "Done")
        
        # Check performance log
        perf_log = Path("logs/performance.log")
        if perf_log.exists():
            content = perf_log.read_text()
            self.assertIn("slow_function", content)
            self.assertIn("completed in", content)


class TestLoggingUtilities(unittest.TestCase):
    """Test logging utility functions"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        TradingLogger._instance = None
        TradingLogger._initialized = False
        
        # Initialize logger
        TradingLogger()
    
    def tearDown(self):
        """Cleanup"""
        os.chdir(self.original_cwd)
        TradingLogger._instance = None
        TradingLogger._initialized = False
    
    def test_log_trade_execution(self):
        """Test trade execution logging"""
        log_trade_execution(
            symbol='AAPL',
            action='SELL',
            quantity=1,
            strike=150.0,
            premium=2.50,
            status='EXECUTED'
        )
        
        # Check trade log
        trade_log = Path("logs/trades.log")
        self.assertTrue(trade_log.exists())
        
        content = trade_log.read_text()
        self.assertIn('AAPL', content)
        self.assertIn('SELL', content)
        self.assertIn('EXECUTED', content)
    
    def test_log_connection_event(self):
        """Test connection event logging"""
        log_connection_event('CONNECTED', 'IBKR Paper Trading')
        
        # Check IBKR log
        ibkr_log = Path("logs/ibkr.log")
        self.assertTrue(ibkr_log.exists())
        
        content = ibkr_log.read_text()
        self.assertIn('CONNECTED', content)
        self.assertIn('IBKR', content)


# ==================== Run Tests ====================

def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestTradingLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestLoggingDecorators))
    suite.addTests(loader.loadTestsFromTestCase(TestLoggingUtilities))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Running Logging System Tests\n")
    print("=" * 60)
    
    success = run_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)
