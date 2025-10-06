#!/usr/bin/env python3
"""
📝 Logging System
מערכת לוגים מקצועית ומתקדמת
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
import sys
import traceback
from functools import wraps

# Try to import config manager, fallback to defaults
try:
    from config_manager import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class TradingLogger:
    """
    Professional logging system for trading application
    Supports multiple log files, rotation, and colored console output
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(TradingLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logging system"""
        if self._initialized:
            return
        
        self.loggers = {}
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Get config
        if CONFIG_AVAILABLE:
            config = get_config()
            self.log_level = config.get('logging.level', 'INFO')
            self.max_bytes = config.get('logging.max_size_mb', 100) * 1024 * 1024
            self.backup_count = config.get('logging.backup_count', 5)
            self.console_output = config.get('logging.console_output', True)
        else:
            self.log_level = 'INFO'
            self.max_bytes = 100 * 1024 * 1024
            self.backup_count = 5
            self.console_output = True
        
        # Setup main logger
        self.setup_main_logger()
        
        # Setup specialized loggers
        self.setup_specialized_loggers()
        
        self._initialized = True
    
    def setup_main_logger(self):
        """Setup main application logger"""
        logger = logging.getLogger('trading')
        logger.setLevel(getattr(logging, self.log_level))
        
        # Clear existing handlers
        logger.handlers = []
        
        # File handler with rotation
        log_file = self.log_dir / 'trading.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Detailed format for file
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # Console handler with colors (if enabled)
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.log_level))
            
            # Simple format for console with colors
            console_format = ColoredFormatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_format)
            logger.addHandler(console_handler)
        
        self.loggers['main'] = logger
        logger.info("✅ Main logging system initialized")
    
    def setup_specialized_loggers(self):
        """Setup specialized loggers for different components"""
        
        specialized_logs = {
            'trades': 'trades.log',
            'orders': 'orders.log',
            'errors': 'errors.log',
            'performance': 'performance.log',
            'ibkr': 'ibkr.log'
        }
        
        for name, filename in specialized_logs.items():
            logger = logging.getLogger(f'trading.{name}')
            logger.setLevel(logging.DEBUG)
            
            # File handler
            log_file = self.log_dir / filename
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            
            # Format
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.propagate = False  # Don't propagate to root logger
            
            self.loggers[name] = logger
    
    def get_logger(self, name: str = 'main') -> logging.Logger:
        """Get logger by name"""
        if name in self.loggers:
            return self.loggers[name]
        
        # Return main logger if not found
        return self.loggers.get('main', logging.getLogger('trading'))


# ==================== Global Logger Access ====================

_trading_logger = None

def get_logger(name: str = 'main') -> logging.Logger:
    """Get trading logger instance"""
    global _trading_logger
    
    if _trading_logger is None:
        _trading_logger = TradingLogger()
    
    return _trading_logger.get_logger(name)


def get_trade_logger() -> logging.Logger:
    """Get specialized trade logger"""
    return get_logger('trades')


def get_order_logger() -> logging.Logger:
    """Get specialized order logger"""
    return get_logger('orders')


def get_error_logger() -> logging.Logger:
    """Get specialized error logger"""
    return get_logger('errors')


# ==================== Decorators ====================

def log_function_call(logger_name: str = 'main'):
    """Decorator to log function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            
            # Log function call
            func_name = func.__name__
            logger.debug(f"📞 Calling {func_name}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"✅ {func_name} completed successfully")
                return result
            
            except Exception as e:
                logger.error(f"❌ {func_name} failed: {e}")
                logger.error(traceback.format_exc())
                raise
        
        return wrapper
    return decorator


def log_errors(logger_name: str = 'errors', reraise: bool = True):
    """Decorator to log errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                # Log error with full traceback
                logger.error(f"❌ Error in {func.__name__}: {e}")
                logger.error(f"Args: {args}")
                logger.error(f"Kwargs: {kwargs}")
                logger.error(traceback.format_exc())
                
                if reraise:
                    raise
                
                return None
        
        return wrapper
    return decorator


def log_trade(func):
    """Decorator to log trade execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_trade_logger()
        
        # Extract trade details from args/kwargs
        trade_info = {
            'function': func.__name__,
            'timestamp': datetime.now().isoformat()
        }
        
        if 'symbol' in kwargs:
            trade_info['symbol'] = kwargs['symbol']
        if 'strike' in kwargs:
            trade_info['strike'] = kwargs['strike']
        
        logger.info(f"🔷 Trade attempt: {trade_info}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"✅ Trade executed successfully: {trade_info}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Trade failed: {trade_info} | Error: {e}")
            raise
    
    return wrapper


def log_performance(func):
    """Decorator to log performance metrics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        
        logger = get_logger('performance')
        func_name = func.__name__
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            logger.info(f"⏱️  {func_name} completed in {elapsed:.3f}s")
            
            return result
        
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"⏱️  {func_name} failed after {elapsed:.3f}s: {e}")
            raise
    
    return wrapper


# ==================== Log Utilities ====================

def log_separator(logger_name: str = 'main', char: str = '=', length: int = 80):
    """Log a separator line"""
    logger = get_logger(logger_name)
    logger.info(char * length)


def log_section(title: str, logger_name: str = 'main'):
    """Log a section header"""
    logger = get_logger(logger_name)
    log_separator(logger_name)
    logger.info(f"  {title}")
    log_separator(logger_name)


def log_trade_execution(
    symbol: str,
    action: str,
    quantity: int,
    strike: float,
    premium: float,
    status: str
):
    """Log trade execution details"""
    logger = get_trade_logger()
    
    log_msg = (
        f"TRADE | {status} | "
        f"{action} {quantity}x {symbol} ${strike} @ ${premium}"
    )
    
    if status in ['EXECUTED', 'SUCCESS']:
        logger.info(f"✅ {log_msg}")
    elif status in ['FAILED', 'ERROR']:
        logger.error(f"❌ {log_msg}")
    else:
        logger.warning(f"⚠️  {log_msg}")


def log_connection_event(event_type: str, details: str):
    """Log IBKR connection events"""
    logger = get_logger('ibkr')
    
    if event_type == 'CONNECTED':
        logger.info(f"🔗 Connected: {details}")
    elif event_type == 'DISCONNECTED':
        logger.warning(f"🔌 Disconnected: {details}")
    elif event_type == 'ERROR':
        logger.error(f"❌ Connection Error: {details}")
    else:
        logger.info(f"ℹ️  {event_type}: {details}")


def log_startup_info():
    """Log application startup information"""
    logger = get_logger('main')
    
    log_section("🚀 Covered Calls Manager Starting Up")
    
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Log Level: {logging.getLevelName(logger.level)}")
    
    if CONFIG_AVAILABLE:
        config = get_config()
        logger.info(f"Trading Mode: {config.get('modes.default_mode', 'unknown')}")
    
    log_separator()


# ==================== Testing ====================

if __name__ == "__main__":
    print("🧪 Testing Logging System\n")
    
    # Initialize logging
    log_startup_info()
    
    # Test different loggers
    main_logger = get_logger('main')
    trade_logger = get_trade_logger()
    error_logger = get_error_logger()
    
    # Test log levels
    main_logger.debug("🔍 Debug message")
    main_logger.info("ℹ️  Info message")
    main_logger.warning("⚠️  Warning message")
    main_logger.error("❌ Error message")
    
    # Test trade logging
    log_trade_execution(
        symbol='AAPL',
        action='SELL',
        quantity=1,
        strike=150.0,
        premium=2.50,
        status='EXECUTED'
    )
    
    # Test connection logging
    log_connection_event('CONNECTED', 'IBKR Paper Trading Port 7497')
    
    # Test decorators
    @log_function_call()
    @log_performance
    def test_function():
        import time
        time.sleep(0.1)
        return "Success"
    
    result = test_function()
    
    # Test error logging
    @log_errors()
    def error_function():
        raise ValueError("Test error")
    
    try:
        error_function()
    except ValueError:
        pass
    
    log_section("Testing Complete")
    
    print("\n✅ All logging tests passed!")
    print(f"📁 Check logs in: {Path('logs').absolute()}")
