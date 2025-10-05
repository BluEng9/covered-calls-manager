"""
📅 Earnings Calendar - Avoid selling calls before earnings
Prevents risky trades during earnings announcements
"""

from datetime import datetime, timedelta
from typing import Dict
import yfinance as yf


class EarningsCalendar:
    """
    Earnings calendar checker to avoid selling calls before earnings

    Uses yfinance to check upcoming earnings dates
    """

    def __init__(self):
        self.cache = {}  # Cache earnings dates to avoid repeated API calls

    def check_before_trade(self, symbol: str, dte: int) -> Dict:
        """
        Check if it's safe to sell calls given upcoming earnings

        Args:
            symbol: Stock symbol
            dte: Days to expiration of the option

        Returns:
            Dict with keys:
                - safe: bool
                - reason: str
                - recommendation: str
                - earnings_date: str or None
        """
        try:
            # Get ticker
            ticker = yf.Ticker(symbol)

            # Try to get earnings date
            earnings_date = None

            # Method 1: Try calendar
            try:
                calendar = ticker.calendar
                if calendar is not None and len(calendar) > 0:
                    # Calendar returns DataFrame with earnings dates
                    if hasattr(calendar, 'iloc'):
                        earnings_date = calendar.iloc[0, 0]
                    elif isinstance(calendar, dict) and 'Earnings Date' in calendar:
                        earnings_date = calendar['Earnings Date']
            except:
                pass

            # Method 2: Try info dict
            if earnings_date is None:
                try:
                    info = ticker.info
                    if 'earningsDate' in info:
                        # earningsDate is often a timestamp
                        earnings_date = info['earningsDate']
                except:
                    pass

            # If we couldn't find earnings date, be conservative
            if earnings_date is None:
                return {
                    'safe': True,  # Allow trade but warn
                    'reason': 'Earnings date unavailable - exercise caution',
                    'recommendation': 'Consider checking earnings manually',
                    'earnings_date': None
                }

            # Convert to datetime if needed
            if isinstance(earnings_date, (int, float)):
                earnings_date = datetime.fromtimestamp(earnings_date)
            elif not isinstance(earnings_date, datetime):
                try:
                    earnings_date = datetime.fromisoformat(str(earnings_date))
                except:
                    earnings_date = None

            if earnings_date is None:
                return {
                    'safe': True,
                    'reason': 'Could not parse earnings date',
                    'recommendation': 'Consider checking earnings manually',
                    'earnings_date': None
                }

            # Calculate days until earnings
            days_until_earnings = (earnings_date - datetime.now()).days

            # Check if earnings is before option expiration
            if days_until_earnings <= dte and days_until_earnings >= 0:
                return {
                    'safe': False,
                    'reason': f'Earnings in {days_until_earnings} days (before expiration)',
                    'recommendation': f'⚠️ Wait until after earnings ({earnings_date.strftime("%Y-%m-%d")})',
                    'earnings_date': earnings_date.strftime('%Y-%m-%d')
                }

            # Check if earnings is very soon (within 7 days)
            elif days_until_earnings < 7 and days_until_earnings >= 0:
                return {
                    'safe': True,  # Allow but warn
                    'reason': f'Earnings in {days_until_earnings} days (after expiration)',
                    'recommendation': f'⚠️ Earnings soon ({earnings_date.strftime("%Y-%m-%d")}) - consider shorter DTE',
                    'earnings_date': earnings_date.strftime('%Y-%m-%d')
                }

            # Earnings is far enough away
            return {
                'safe': True,
                'reason': f'Earnings in ~{days_until_earnings} days',
                'recommendation': '✅ Safe to trade',
                'earnings_date': earnings_date.strftime('%Y-%m-%d') if earnings_date else None
            }

        except Exception as e:
            # If we can't check, be conservative and allow (with warning)
            return {
                'safe': True,
                'reason': f'Could not check earnings: {str(e)}',
                'recommendation': '⚠️ Manual earnings check recommended',
                'earnings_date': None
            }

    def get_earnings_info(self, symbol: str) -> Dict:
        """
        Get detailed earnings information for a symbol

        Returns:
            Dict with earnings details
        """
        try:
            ticker = yf.Ticker(symbol)

            info = {
                'symbol': symbol,
                'earnings_date': None,
                'last_earnings': None,
                'earnings_history': []
            }

            # Try to get calendar
            try:
                calendar = ticker.calendar
                if calendar is not None and len(calendar) > 0:
                    if hasattr(calendar, 'iloc'):
                        info['earnings_date'] = str(calendar.iloc[0, 0])
            except:
                pass

            # Try to get earnings history
            try:
                earnings = ticker.earnings
                if earnings is not None and not earnings.empty:
                    info['earnings_history'] = earnings.to_dict('records')
            except:
                pass

            return info

        except Exception as e:
            return {
                'symbol': symbol,
                'error': str(e)
            }
