"""
Trade Execution Module for Covered Calls Manager
Handles real order execution through Interactive Brokers
"""

from .trade_executor import TradeExecutor, TradeRequest, OrderType, OrderAction, ExecutionResult, ExecutionStatus
from .execution_logger import ExecutionLogger

__all__ = [
    'TradeExecutor',
    'TradeRequest',
    'OrderType',
    'OrderAction',
    'ExecutionResult',
    'ExecutionStatus',
    'ExecutionLogger'
]
