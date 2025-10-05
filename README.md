# 📈 Covered Calls Manager

Advanced covered calls trading system with Interactive Brokers integration, real-time analytics, and portfolio management.

## 🎯 Features

### Core Strategy Engine
- **Smart Strike Selection**: Algorithmic strike price optimization based on Greeks, IV, and risk tolerance
- **Multiple Risk Levels**: Conservative, Moderate, and Aggressive strategies
- **Greeks Calculator**: Black-Scholes model for Delta, Gamma, Theta, and Vega
- **Rolling Strategy**: Automated position rolling logic to avoid assignment
- **Portfolio Analytics**: Real-time P&L tracking, annualized returns, and risk metrics

### Interactive Brokers Integration
- **Real-time Data**: Live stock prices, option chains, and Greeks from IBKR
- **Order Execution**: Automated covered call selling and rolling
- **Position Management**: Sync with IBKR portfolio
- **Historical Data**: IV history and price analysis
- **Paper & Live Trading**: Support for both paper and live accounts

### Web Dashboard
- **Interactive UI**: Streamlit-based dashboard with 5-tab organized interface
- **Portfolio Overview**: Account summary and position tracking
- **Strategy Finder**: Scan and score optimal strike prices
- **Backtesting Engine**: Historical strategy analysis with 5 risk levels
- **CSV Upload Mode**: Test strategies without IBKR connection
- **Alert System**: Notifications for assignment risk, expirations, and opportunities
- **Performance Charts**: Visual analytics for returns and Greeks exposure

### TradingView Integration
- **Pine Script Indicator**: Custom TradingView indicator for covered calls
- **Visual Signals**: Strike targets, risk zones, and entry signals
- **Statistics Table**: Real-time premium yields and return calculations
- **Alerts**: Price alerts for approaching strikes and assignment risk

## 📋 Requirements

- Python 3.8+
- Interactive Brokers TWS or IB Gateway
- TradingView account (for Pine Script indicator)

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/covered-calls-manager.git
cd covered-calls-manager
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure IBKR
1. Install [Interactive Brokers TWS](https://www.interactivebrokers.com/en/trading/tws.php) or IB Gateway
2. Enable API access in TWS/Gateway settings:
   - File → Global Configuration → API → Settings
   - Enable "ActiveX and Socket Clients"
   - Add trusted IP: 127.0.0.1
3. Note your port:
   - TWS Paper: 7497
   - TWS Live: 7496
   - Gateway Paper: 4002
   - Gateway Live: 4001

## 📖 Usage

### Running the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

#### Dashboard Features:
1. **Connect to IBKR**: Use sidebar to configure and connect (or upload CSV)
2. **Tab 1 - Overview**: Account summary, portfolio, alerts, positions
3. **Tab 2 - Strategy Finder**: Scan for optimal strike prices
4. **Tab 3 - Active Positions**: Monitor open positions with expiration calendar
5. **Tab 4 - Backtesting**: Historical strategy analysis with 5 risk levels
6. **Tab 5 - Analytics**: Performance charts and returns

#### CSV Upload Mode:
For testing without IBKR connection:
1. Click "Upload CSV" in sidebar
2. Upload portfolio CSV (see `IBKR_PORTFOLIO_GUIDE.md` for format)
3. All features work except live trading

### Using the Core System

```python
from covered_calls_system import (
    Stock, CoveredCallStrategy, RiskLevel, PortfolioManager
)
from ibkr_connector import IBKRConnector, IBKRConfig

# Connect to IBKR
config = IBKRConfig(port=7497, readonly=True)
ibkr = IBKRConnector(config)
ibkr.connect()

# Get stock position
stocks = ibkr.get_stock_positions()
my_stock = stocks[0]  # AAPL, for example

# Find optimal strikes
strategy = CoveredCallStrategy(RiskLevel.MODERATE)
options = ibkr.get_otm_calls(
    my_stock.symbol,
    my_stock.current_price,
    days_to_expiration=30
)

# Score and rank options
best_strikes = strategy.find_best_strike(
    options,
    my_stock.current_price,
    top_n=5
)

# Display results
for option, score in best_strikes:
    print(f"Strike: ${option.strike:.2f}")
    print(f"Premium: ${option.premium:.2f}")
    print(f"Score: {score:.0f}/100")
    print(f"Delta: {option.delta:.3f}")
    print("---")

# Sell covered call
trade = ibkr.sell_covered_call(
    symbol=my_stock.symbol,
    quantity=1,  # 1 contract = 100 shares
    strike=best_strikes[0][0].strike,
    expiration="20240215",  # YYYYMMDD
    limit_price=best_strikes[0][0].bid
)
```

### Using TradingView Indicator

1. Open TradingView
2. Open Pine Editor (Alt+E)
3. Copy contents of `tradingview_covered_calls.pine`
4. Click "Add to Chart"
5. Configure settings:
   - Position Size: Your shares owned
   - Average Cost: Your entry price
   - Risk Level: Conservative/Moderate/Aggressive
   - Target DTE: Days to expiration

The indicator will display:
- **Target Strike** (blue line)
- **Risk Zones** (green = safe, red = assignment risk)
- **Statistics Table** with premium yields
- **Signals** for good entries and warnings

### Running Tests

```bash
# Run all tests
python test_system.py

# Or use pytest
pytest test_system.py -v

# With coverage
pytest test_system.py --cov=covered_calls_system --cov-report=html
```

## 📊 Strategy Guide

### Conservative Strategy
- **Target Delta**: 0.15 - 0.25
- **Strike Distance**: ~5-7% OTM
- **Best For**: Capital preservation, long-term holdings
- **Expected Return**: 0.5-1.5% per month
- **Assignment Risk**: Low

### Moderate Strategy (Default)
- **Target Delta**: 0.25 - 0.35
- **Strike Distance**: ~3-5% OTM
- **Best For**: Balanced risk/reward
- **Expected Return**: 1-2.5% per month
- **Assignment Risk**: Medium

### Aggressive Strategy
- **Target Delta**: 0.35 - 0.50
- **Strike Distance**: ~1-3% OTM
- **Best For**: Maximum premium collection
- **Expected Return**: 1.5-4% per month
- **Assignment Risk**: High

## 🎓 Example Strategies

### Monthly Income Strategy
```python
# Sell 30-45 DTE calls, moderate delta
strategy = CoveredCallStrategy(RiskLevel.MODERATE)
options = ibkr.get_otm_calls(symbol, price, days_to_expiration=35)
```

### Earnings Play
```python
# Sell calls before earnings with high IV
# Higher premium but higher assignment risk
strategy = CoveredCallStrategy(RiskLevel.AGGRESSIVE)
options = ibkr.get_otm_calls(symbol, price, days_to_expiration=7)
```

### Rolling Strategy
```python
from covered_calls_system import RollStrategy

# Check if should roll
if RollStrategy.should_roll(position, current_price):
    # Calculate credit
    credit = RollStrategy.calculate_roll_credit(
        old_option, new_option, quantity=1
    )

    if credit > 0:  # Only roll for credit
        ibkr.roll_call(symbol, quantity, old_strike, old_exp,
                      new_strike, new_exp, min_credit=0)
```

## ⚠️ Risk Management

### Before Selling Covered Calls:
1. ✅ Own 100+ shares (multiples of 100)
2. ✅ Comfortable being assigned at strike price
3. ✅ Understand tax implications
4. ✅ Consider dividend dates
5. ✅ Check earnings calendar

### Position Management:
- **Monitor Delta**: Close position if delta > 0.70
- **Roll Before Expiration**: 7-14 days before expiration
- **Set Alerts**: Use TradingView or dashboard alerts
- **Size Appropriately**: Don't over-leverage

### Common Pitfalls:
- ❌ Selling calls on stocks you want to keep long-term
- ❌ Ignoring dividend capture opportunities
- ❌ Rolling for a debit (paying to roll)
- ❌ Chasing high premiums without checking IV percentile

## 📁 Project Structure

```
covered-calls-manager/
├── covered_calls_system.py         # Core strategy engine (508 lines)
├── ibkr_connector.py               # IBKR integration (596 lines)
├── dashboard.py                    # Streamlit dashboard with tabs (1072 lines)
├── covered_calls_backtester.py     # Historical backtesting (368 lines)
├── csv_portfolio_loader.py         # CSV upload mode (106 lines)
├── demo_mode.py                    # Mock IBKR connector (153 lines)
├── ibkr_portfolio_converter.py     # PDF parser for IBKR exports (119 lines)
├── test_system.py                  # Test suite (294 lines)
├── tradingview_covered_calls.pine  # TradingView indicator
├── requirements.txt                # Python dependencies
├── IBKR_PORTFOLIO_GUIDE.md        # Hebrew portfolio upload guide
├── README.md                       # This file
├── TODO.md                         # Development roadmap
└── setup_github.sh                 # GitHub setup script
```

**Total:** ~3,200 lines of Python code + Pine Script + documentation

## 🔧 Configuration

### IBKR Settings
```python
config = IBKRConfig(
    host="127.0.0.1",
    port=7497,  # Your TWS/Gateway port
    client_id=1,
    readonly=False  # Set True for paper trading
)
```

### Strategy Settings
```python
strategy = CoveredCallStrategy(
    risk_level=RiskLevel.MODERATE  # CONSERVATIVE, MODERATE, AGGRESSIVE
)
```

### Dashboard Settings
- Configure in sidebar when running
- Auto-save preferences to session state

## 📈 Performance Metrics

The system tracks:
- **Total Premium Collected**: Sum of all premiums
- **Return if Assigned**: Expected return if all positions assigned
- **Annualized Return**: Return extrapolated to yearly basis
- **Portfolio Delta**: Net delta exposure
- **Portfolio Theta**: Daily time decay
- **Win Rate**: Percentage of profitable closes
- **Assignment Rate**: How often positions are assigned

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## ⚖️ Legal Disclaimer

**This software is for educational purposes only.**

- Not financial advice
- Trading involves substantial risk
- Past performance ≠ future results
- Consult a financial advisor before trading
- Use paper trading before going live

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Interactive Brokers API via [ib_insync](https://github.com/erdewit/ib_insync)
- Options pricing models from academic literature
- TradingView for charting platform

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/covered-calls-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/covered-calls-manager/discussions)
- **Email**: your.email@example.com

## 🗺️ Roadmap

### Completed Features:
- [x] Backtesting engine with 5 strategy comparison
- [x] CSV upload mode for testing without IBKR
- [x] Modern dashboard with tabs
- [x] IBKR PDF transaction history parser

### Planned Features:
- [ ] Machine learning strike selection
- [ ] Multi-leg strategies (spreads, collars)
- [ ] Mobile app
- [ ] Telegram/Discord bot alerts
- [ ] Tax reporting integration
- [ ] Portfolio optimization
- [ ] Risk-parity position sizing

---

**⭐ Star this repo if you find it useful!**

Built with ❤️ by options traders, for options traders.
