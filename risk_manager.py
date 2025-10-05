"""
Risk Management System for Covered Calls
==========================================
מערכת ניהול סיכונים למסחר באופציות

Features:
- Portfolio concentration limits
- Position sizing rules
- Assignment risk monitoring
- Diversification checks
- Capital requirements validation
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import pandas as pd
from datetime import datetime, timedelta


class RiskLevel(Enum):
    """רמות סיכון"""
    LOW = "נמוך"
    MEDIUM = "בינוני"
    HIGH = "גבוה"
    CRITICAL = "קריטי"


@dataclass
class RiskAlert:
    """התראת סיכון"""
    level: RiskLevel
    title: str
    message: str
    recommendation: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PositionRisk:
    """ניתוח סיכון לפוזיציה"""
    symbol: str
    quantity: int
    current_price: float
    strike: float
    expiration: str
    delta: float
    days_to_expiry: int
    assignment_probability: float
    max_loss: float
    risk_level: RiskLevel


class RiskManager:
    """
    מנהל סיכונים ראשי
    """

    def __init__(self,
                 max_position_pct: float = 0.25,      # מקסימום 25% מהתיק בפוזיציה אחת
                 max_cc_pct: float = 0.70,             # מקסימום 70% מהתיק ב-CC
                 min_cash_reserve: float = 0.10,       # שמור לפחות 10% מזומן
                 max_delta: float = 0.75,              # Delta מקסימלי להתראה
                 min_dte_warning: int = 7):            # התראה ל-DTE נמוך

        self.max_position_pct = max_position_pct
        self.max_cc_pct = max_cc_pct
        self.min_cash_reserve = min_cash_reserve
        self.max_delta = max_delta
        self.min_dte_warning = min_dte_warning

        self.alerts: List[RiskAlert] = []


    def analyze_portfolio(self,
                         account_value: float,
                         cash_balance: float,
                         positions: List[Dict]) -> Dict:
        """
        ניתוח סיכוני תיק מלא

        Args:
            account_value: שווי חשבון כולל
            cash_balance: מזומן זמין
            positions: רשימת פוזיציות

        Returns:
            Dict עם ניתוח מלא
        """
        self.alerts.clear()

        # 1. בדוק ריכוזיות
        concentration = self._check_concentration(account_value, positions)

        # 2. בדוק מזומן זמין
        cash_check = self._check_cash_reserve(account_value, cash_balance)

        # 3. בדוק חשיפה ל-CC
        cc_exposure = self._check_covered_calls_exposure(account_value, positions)

        # 4. בדוק סיכון הקצאה
        assignment_risk = self._check_assignment_risk(positions)

        # 5. בדוק גיוון
        diversification = self._check_diversification(positions)

        return {
            'overall_risk': self._calculate_overall_risk(),
            'concentration': concentration,
            'cash_reserve': cash_check,
            'cc_exposure': cc_exposure,
            'assignment_risk': assignment_risk,
            'diversification': diversification,
            'alerts': self.alerts,
            'recommendations': self._generate_recommendations()
        }


    def validate_new_position(self,
                            symbol: str,
                            contracts: int,
                            strike: float,
                            current_price: float,
                            account_value: float,
                            existing_positions: List[Dict]) -> tuple[bool, str]:
        """
        בדוק אם פוזיציה חדשה בטוחה

        Returns:
            (approved: bool, reason: str)
        """
        position_value = contracts * 100 * current_price

        # 1. בדוק גודל פוזיציה
        position_pct = position_value / account_value
        if position_pct > self.max_position_pct:
            return False, f"⛔ פוזיציה גדולה מדי: {position_pct*100:.1f}% (מקסימום {self.max_position_pct*100:.0f}%)"

        # 2. בדוק סך חשיפה ל-CC
        existing_cc_value = sum(
            pos.get('quantity', 0) * pos.get('price', 0) * 100
            for pos in existing_positions
            if pos.get('has_covered_call', False)
        )
        total_cc_value = existing_cc_value + position_value
        cc_pct = total_cc_value / account_value

        if cc_pct > self.max_cc_pct:
            return False, f"⛔ יותר מדי חשיפה ל-Covered Calls: {cc_pct*100:.1f}% (מקסימום {self.max_cc_pct*100:.0f}%)"

        # 3. בדוק ריכוזיות במניה אחת
        symbol_positions = [p for p in existing_positions if p.get('symbol') == symbol]
        if symbol_positions:
            existing_symbol_value = sum(
                p.get('quantity', 0) * p.get('price', 0) * 100
                for p in symbol_positions
            )
            total_symbol_value = existing_symbol_value + position_value
            symbol_pct = total_symbol_value / account_value

            if symbol_pct > self.max_position_pct:
                return False, f"⛔ יותר מדי חשיפה ל-{symbol}: {symbol_pct*100:.1f}% (מקסימום {self.max_position_pct*100:.0f}%)"

        return True, f"✅ פוזיציה מאושרת ({position_pct*100:.1f}% מהתיק)"


    def calculate_position_size(self,
                               account_value: float,
                               risk_per_trade: float = 0.02,
                               stock_price: float = 0) -> int:
        """
        חשב כמות חוזים מומלצת

        Args:
            account_value: שווי חשבון
            risk_per_trade: סיכון מקסימלי לעסקה (default 2%)
            stock_price: מחיר מניה

        Returns:
            מספר חוזים מומלץ
        """
        if stock_price == 0:
            return 0

        max_position_value = account_value * self.max_position_pct
        max_contracts = int(max_position_value / (stock_price * 100))

        # אל תעבור את הסיכון למסחר
        risk_based_value = account_value * risk_per_trade
        risk_based_contracts = int(risk_based_value / (stock_price * 100))

        # קח את הנמוך מבין השניים
        recommended = min(max_contracts, risk_based_contracts)

        return max(1, recommended)  # לפחות חוזה אחד


    def _check_concentration(self,
                           account_value: float,
                           positions: List[Dict]) -> Dict:
        """בדוק ריכוזיות תיק"""

        if not positions:
            return {'status': 'OK', 'message': 'אין פוזיציות'}

        # חשב ערך כל מניה
        position_values = {}
        for pos in positions:
            symbol = pos.get('symbol', 'UNKNOWN')
            value = pos.get('quantity', 0) * pos.get('price', 0) * 100
            position_values[symbol] = position_values.get(symbol, 0) + value

        # מצא את הפוזיציה הגדולה ביותר
        max_symbol = max(position_values, key=position_values.get)
        max_value = position_values[max_symbol]
        max_pct = (max_value / account_value) * 100

        if max_pct > self.max_position_pct * 100:
            self.alerts.append(RiskAlert(
                level=RiskLevel.HIGH,
                title=f"ריכוזיות גבוהה ב-{max_symbol}",
                message=f"{max_symbol} מהווה {max_pct:.1f}% מהתיק",
                recommendation=f"שקול להפחית חשיפה ל-{max_symbol} מתחת ל-{self.max_position_pct*100:.0f}%"
            ))
            status = 'WARNING'
        else:
            status = 'OK'

        return {
            'status': status,
            'largest_position': max_symbol,
            'largest_pct': max_pct,
            'positions_breakdown': position_values
        }


    def _check_cash_reserve(self,
                          account_value: float,
                          cash_balance: float) -> Dict:
        """בדוק מזומן זמין"""

        cash_pct = (cash_balance / account_value) * 100
        required_pct = self.min_cash_reserve * 100

        if cash_pct < required_pct:
            self.alerts.append(RiskAlert(
                level=RiskLevel.MEDIUM,
                title="מזומן נמוך",
                message=f"יש לך רק {cash_pct:.1f}% מזומן (נדרש {required_pct:.0f}%)",
                recommendation="שקול לשמור יותר מזומן למקרי חירום או הזדמנויות"
            ))
            status = 'LOW'
        else:
            status = 'OK'

        return {
            'status': status,
            'cash_pct': cash_pct,
            'required_pct': required_pct,
            'cash_amount': cash_balance
        }


    def _check_covered_calls_exposure(self,
                                     account_value: float,
                                     positions: List[Dict]) -> Dict:
        """בדוק כמה מהתיק תחת Covered Calls"""

        cc_positions = [p for p in positions if p.get('has_covered_call', False)]

        if not cc_positions:
            return {'status': 'OK', 'exposure_pct': 0, 'message': 'אין Covered Calls פעילים'}

        cc_value = sum(
            p.get('quantity', 0) * p.get('price', 0) * 100
            for p in cc_positions
        )
        cc_pct = (cc_value / account_value) * 100

        if cc_pct > self.max_cc_pct * 100:
            self.alerts.append(RiskAlert(
                level=RiskLevel.HIGH,
                title="חשיפת Covered Calls גבוהה",
                message=f"{cc_pct:.1f}% מהתיק תחת CC (מקסימום {self.max_cc_pct*100:.0f}%)",
                recommendation="אל תמכור יותר Covered Calls עד שתסגור פוזיציות קיימות"
            ))
            status = 'HIGH'
        elif cc_pct > self.max_cc_pct * 0.8 * 100:
            status = 'MEDIUM'
        else:
            status = 'OK'

        return {
            'status': status,
            'exposure_pct': cc_pct,
            'num_positions': len(cc_positions),
            'total_value': cc_value
        }


    def _check_assignment_risk(self, positions: List[Dict]) -> Dict:
        """בדוק סיכון להקצאה"""

        high_risk_positions = []

        for pos in positions:
            if not pos.get('has_covered_call', False):
                continue

            delta = pos.get('option_delta', 0)
            dte = pos.get('days_to_expiry', 999)

            # Delta גבוה = סיכון גבוה
            # DTE נמוך = סיכון גבוה
            risk_score = delta * (1 - dte/30)  # נורמליזציה ל-30 ימים

            if delta > self.max_delta and dte < self.min_dte_warning:
                high_risk_positions.append({
                    'symbol': pos.get('symbol'),
                    'delta': delta,
                    'dte': dte,
                    'risk_score': risk_score
                })

                self.alerts.append(RiskAlert(
                    level=RiskLevel.HIGH,
                    title=f"סיכון הקצאה גבוה - {pos.get('symbol')}",
                    message=f"Delta: {delta:.2f}, DTE: {dte}",
                    recommendation="שקול Rolling או סגירת הפוזיציה"
                ))

        return {
            'high_risk_count': len(high_risk_positions),
            'positions': high_risk_positions
        }


    def _check_diversification(self, positions: List[Dict]) -> Dict:
        """בדוק גיוון תיק"""

        if not positions:
            return {'status': 'N/A', 'num_symbols': 0}

        num_symbols = len(set(p.get('symbol') for p in positions))

        if num_symbols < 3:
            self.alerts.append(RiskAlert(
                level=RiskLevel.MEDIUM,
                title="גיוון נמוך",
                message=f"יש לך רק {num_symbols} מניות שונות",
                recommendation="שקול להוסיף 2-3 מניות נוספות לגיוון טוב יותר"
            ))
            status = 'LOW'
        elif num_symbols < 5:
            status = 'MEDIUM'
        else:
            status = 'GOOD'

        return {
            'status': status,
            'num_symbols': num_symbols,
            'recommendation': 'מומלץ 5-10 מניות שונות'
        }


    def _calculate_overall_risk(self) -> RiskLevel:
        """חשב רמת סיכון כוללת"""

        if not self.alerts:
            return RiskLevel.LOW

        # ספור התראות לפי רמת חומרה
        critical_count = sum(1 for a in self.alerts if a.level == RiskLevel.CRITICAL)
        high_count = sum(1 for a in self.alerts if a.level == RiskLevel.HIGH)
        medium_count = sum(1 for a in self.alerts if a.level == RiskLevel.MEDIUM)

        if critical_count > 0 or high_count >= 3:
            return RiskLevel.CRITICAL
        elif high_count >= 1 or medium_count >= 3:
            return RiskLevel.HIGH
        elif medium_count >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


    def _generate_recommendations(self) -> List[str]:
        """צור המלצות בסיס על ניתוח הסיכונים"""

        recommendations = []

        # המלצות כלליות
        if not self.alerts:
            recommendations.append("✅ התיק נראה מאוזן ובריא")
            return recommendations

        # המלצות ספציפיות לפי התראות
        for alert in self.alerts:
            if alert.recommendation:
                recommendations.append(f"• {alert.recommendation}")

        return recommendations


# ========================
# Helper Functions
# ========================

def format_risk_report(risk_analysis: Dict) -> str:
    """
    פורמט דוח סיכונים לתצוגה
    """
    report = []
    report.append("=" * 50)
    report.append("📊 דוח ניתוח סיכונים")
    report.append("=" * 50)
    report.append("")

    # סיכון כללי
    overall = risk_analysis['overall_risk']
    emoji = {
        RiskLevel.LOW: "🟢",
        RiskLevel.MEDIUM: "🟡",
        RiskLevel.HIGH: "🟠",
        RiskLevel.CRITICAL: "🔴"
    }
    report.append(f"רמת סיכון כללית: {emoji[overall]} {overall.value}")
    report.append("")

    # התראות
    if risk_analysis['alerts']:
        report.append("⚠️  התראות:")
        for alert in risk_analysis['alerts']:
            report.append(f"  {emoji[alert.level]} {alert.title}")
            report.append(f"     {alert.message}")
        report.append("")

    # המלצות
    if risk_analysis['recommendations']:
        report.append("💡 המלצות:")
        for rec in risk_analysis['recommendations']:
            report.append(f"  {rec}")
        report.append("")

    report.append("=" * 50)

    return "\n".join(report)


# ========================
# Example Usage
# ========================

if __name__ == "__main__":
    # דוגמה לשימוש

    rm = RiskManager(
        max_position_pct=0.25,
        max_cc_pct=0.70,
        min_cash_reserve=0.10
    )

    # דוגמה לפוזיציות
    positions = [
        {
            'symbol': 'TSLA',
            'quantity': 300,
            'price': 430,
            'has_covered_call': True,
            'option_delta': 0.65,
            'days_to_expiry': 15
        },
        {
            'symbol': 'AAPL',
            'quantity': 200,
            'price': 180,
            'has_covered_call': True,
            'option_delta': 0.45,
            'days_to_expiry': 25
        }
    ]

    # ניתוח תיק
    analysis = rm.analyze_portfolio(
        account_value=266296,
        cash_balance=137296,
        positions=positions
    )

    # הצג דוח
    print(format_risk_report(analysis))

    # בדוק פוזיציה חדשה
    approved, reason = rm.validate_new_position(
        symbol='NVDA',
        contracts=1,
        strike=450,
        current_price=440,
        account_value=266296,
        existing_positions=positions
    )

    print(f"\nבדיקת פוזיציה חדשה:")
    print(reason)
