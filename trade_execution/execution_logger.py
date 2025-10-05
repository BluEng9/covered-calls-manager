"""
Trade execution logging system
Records all trades for audit trail and analysis
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import logging


class ExecutionLogger:
    """Log all trade executions to JSON file with timestamps"""

    def __init__(self, log_dir: str = "execution_logs"):
        """
        Initialize execution logger

        Args:
            log_dir: Directory to store execution logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with date
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"trades_{today}.jsonl"

        self.logger = logging.getLogger(__name__)

    def log_trade(self, trade_details: Dict[str, Any]):
        """
        Log a trade to file

        Args:
            trade_details: Dict containing trade information
        """
        # Add timestamp if not present
        if 'timestamp' not in trade_details:
            trade_details['timestamp'] = datetime.now().isoformat()

        try:
            # Append to JSONL file (one JSON object per line)
            with open(self.log_file, 'a') as f:
                json.dump(trade_details, f)
                f.write('\n')

            self.logger.info(f"Logged trade: {trade_details.get('type', 'UNKNOWN')}")

        except Exception as e:
            self.logger.error(f"Failed to log trade: {str(e)}")

    def get_trades(self, date: str = None) -> List[Dict]:
        """
        Retrieve trades from log

        Args:
            date: Date string (YYYY-MM-DD). If None, uses today.

        Returns:
            List of trade dicts
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        log_file = self.log_dir / f"trades_{date}.jsonl"

        if not log_file.exists():
            return []

        trades = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        trades.append(json.loads(line))
        except Exception as e:
            self.logger.error(f"Failed to read trades: {str(e)}")

        return trades

    def get_summary(self, date: str = None) -> Dict:
        """
        Get trade summary for a date

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            Summary dict with counts and totals
        """
        trades = self.get_trades(date)

        summary = {
            'total_trades': len(trades),
            'successful': sum(1 for t in trades if t.get('status') == 'Filled'),
            'errors': sum(1 for t in trades if t.get('status') == 'ERROR'),
            'covered_calls_sold': sum(
                1 for t in trades
                if t.get('type') == 'SELL_COVERED_CALL' and t.get('status') == 'Filled'
            )
        }

        return summary
