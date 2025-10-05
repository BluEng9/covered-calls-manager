"""
CSV Portfolio Loader - Parse IBKR portfolio exports and other CSV formats
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import io


class CSVPortfolioLoader:
    """Parse various CSV formats for portfolio data"""

    @staticmethod
    def parse_ibkr_portfolio(csv_content: str) -> Dict:
        """
        Parse IBKR portfolio export CSV

        Expected columns: Symbol, Quantity, Price, Market Value, Average Cost, etc.

        Returns: Dict with 'stocks' and 'options' lists
        """
        try:
            # Read CSV
            df = pd.read_csv(io.StringIO(csv_content))

            # Clean column names
            df.columns = df.columns.str.strip()

            stocks = []
            options = []

            # Process each row
            for _, row in df.iterrows():
                # Determine if stock or option
                symbol = str(row.get('Symbol', '')).strip()

                if not symbol or symbol == 'Total':
                    continue

                # Options usually have spaces or special format in symbol
                if ' ' in symbol or 'C' in symbol[-8:] or 'P' in symbol[-8:]:
                    # Option position
                    options.append({
                        'symbol': symbol,
                        'quantity': float(row.get('Quantity', 0)),
                        'avg_cost': float(row.get('Average Cost', 0)),
                        'current_price': float(row.get('Price', 0)),
                        'market_value': float(row.get('Market Value', 0))
                    })
                else:
                    # Stock position
                    stocks.append({
                        'symbol': symbol,
                        'quantity': int(float(row.get('Quantity', 0))),
                        'avg_cost': float(row.get('Average Cost', 0)),
                        'current_price': float(row.get('Price', 0)),
                        'market_value': float(row.get('Market Value', 0))
                    })

            return {
                'stocks': stocks,
                'options': options,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            raise ValueError(f"Error parsing IBKR CSV: {str(e)}")

    @staticmethod
    def parse_simple_portfolio(csv_content: str) -> Dict:
        """
        Parse simple CSV format: Symbol,Quantity,AvgCost,CurrentPrice

        Returns: Dict with 'stocks' list
        """
        try:
            df = pd.read_csv(io.StringIO(csv_content))

            # Clean column names
            df.columns = df.columns.str.strip()

            stocks = []

            for _, row in df.iterrows():
                symbol = str(row.get('Symbol', '')).strip()

                if not symbol:
                    continue

                stocks.append({
                    'symbol': symbol.upper(),
                    'quantity': int(float(row.get('Quantity', 0))),
                    'avg_cost': float(row.get('AvgCost', row.get('Average Cost', 0))),
                    'current_price': float(row.get('CurrentPrice', row.get('Price', 0)))
                })

            return {
                'stocks': stocks,
                'options': [],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            raise ValueError(f"Error parsing simple CSV: {str(e)}")

    @staticmethod
    def auto_detect_format(csv_content: str) -> str:
        """
        Auto-detect CSV format

        Returns: 'ibkr', 'simple', or 'unknown'
        """
        try:
            df = pd.read_csv(io.StringIO(csv_content), nrows=1)
            columns = [col.strip().lower() for col in df.columns]

            # Check for IBKR format (has "Market Value" or "Average Cost")
            if 'market value' in columns or 'average cost' in columns:
                return 'ibkr'

            # Check for simple format
            required_simple = ['symbol', 'quantity']
            if all(col in columns for col in required_simple):
                return 'simple'

            return 'unknown'

        except Exception:
            return 'unknown'

    @staticmethod
    def load_portfolio(csv_content: str, format_type: Optional[str] = None) -> Dict:
        """
        Load portfolio from CSV with auto-detection

        Args:
            csv_content: CSV file content as string
            format_type: Optional format override ('ibkr', 'simple')

        Returns: Dict with stocks and options
        """
        if format_type is None:
            format_type = CSVPortfolioLoader.auto_detect_format(csv_content)

        if format_type == 'ibkr':
            return CSVPortfolioLoader.parse_ibkr_portfolio(csv_content)
        elif format_type == 'simple':
            return CSVPortfolioLoader.parse_simple_portfolio(csv_content)
        else:
            raise ValueError(
                "Unable to detect CSV format. Please use IBKR export format or simple format:\n"
                "Symbol,Quantity,AvgCost,CurrentPrice"
            )


class PortfolioDataStore:
    """Store uploaded portfolio data in session"""

    def __init__(self):
        self.stocks = []
        self.options = []
        self.timestamp = None

    def load_from_csv(self, csv_content: str, format_type: Optional[str] = None):
        """Load portfolio from CSV content"""
        data = CSVPortfolioLoader.load_portfolio(csv_content, format_type)

        self.stocks = data['stocks']
        self.options = data['options']
        self.timestamp = data['timestamp']

    def get_stock_positions(self) -> List[Dict]:
        """Return stock positions in IBKR connector format"""
        return self.stocks

    def get_account_summary(self) -> Dict:
        """Calculate account summary from positions"""
        total_value = sum(
            stock['quantity'] * stock['current_price']
            for stock in self.stocks
        )

        total_cost = sum(
            stock['quantity'] * stock['avg_cost']
            for stock in self.stocks
        )

        unrealized_pnl = total_value - total_cost

        return {
            'NetLiquidation': total_value,
            'TotalCashValue': 0,  # Not available from CSV
            'UnrealizedPnL': unrealized_pnl,
            'RealizedPnL': 0,  # Not available from CSV
            'BuyingPower': 0,  # Not available from CSV
            'AvailableFunds': 0  # Not available from CSV
        }
