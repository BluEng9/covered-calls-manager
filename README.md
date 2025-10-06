# 📊 Covered Calls Manager

> **Professional Options Trading System for Covered Calls Strategy**  
> Automated strike selection, Greeks calculation, risk management, and execution

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 🌟 Features

### 📈 Strategy Management
- ✅ **Automated Strike Selection** - Find optimal strikes using Greeks and probabilities
- ✅ **Multi-Factor Scoring** - Score options by premium, delta, IV, and more
- ✅ **Risk Level Classification** - Conservative, Moderate, Aggressive strategies
- ✅ **Greeks Calculation** - Real-time Delta, Gamma, Theta, Vega using Black-Scholes
- ✅ **IV Analysis** - Implied Volatility calculation from market prices

### 🛡️ Risk Management
- ✅ **Pre-Trade Validation** - Comprehensive safety checks before execution
- ✅ **Position Limits** - Max contracts, position size, sector exposure
- ✅ **Earnings Protection** - Avoid trades around earnings announcements
- ✅ **Stop Loss** - Automatic position closing on adverse moves
- ✅ **Assignment Risk Monitoring** - Track and alert on ITM positions

### 💼 Execution & Management
- ✅ **IBKR Integration** - Direct connection to Interactive Brokers
- ✅ **Multiple Modes** - Demo, Paper Trading, and Live modes
- ✅ **Position Rolling** - Roll out, roll up, or both
- ✅ **Order Management** - Limit orders with price optimization
- ✅ **Trade Logging** - SQLite database for complete trade history

### 📊 Analytics & Reporting
- ✅ **Performance Tracking** - P&L, win rate, Sharpe ratio, max drawdown
- ✅ **Trade Analytics** - Best/worst trades, strategy comparison
- ✅ **Interactive Charts** - Plotly-based visualizations
- ✅ **CSV Export** - Download trade history and reports
- ✅ **Real-time Dashboard** - Streamlit-based UI with Hebrew support

---

## 🔐 Security & Setup

### ⚠️ IMPORTANT: Protect Your Credentials

**This project handles sensitive financial data. Follow these security best practices:**

✅ **NEVER commit these files to git:**
- `.env` - Contains your API keys and credentials
- `config_local.yaml` - Your personal configuration
- `trades.db` - Your actual trading history
- Any files with `real`, `live`, or `production` in the name

✅ **Safe to commit:**
- `.env.example` - Template with NO actual credentials
- `config.yaml` - Default configuration without secrets
- All code files (`.py`)

The `.gitignore` file is pre-configured to protect sensitive data. **Always verify before committing!**

### 🔑 Environment Variables Setup

**Step 1:** Copy the template file
```bash
cp .env.example .env
```

**Step 2:** Edit `.env` with your actual credentials
```bash
# NEVER commit this file!
nano .env  # or use your preferred editor
```

**Step 3:** Fill in your credentials:
```bash
# Interactive Brokers Configuration
IBKR_HOST=127.0.0.1
IBKR_PORT=7497              # 7497 for paper trading, 7496 for live
IBKR_CLIENT_ID=1
IBKR_READONLY=true          # Set to false for live trading

# Trading Risk Limits (IMPORTANT!)
MAX_POSITION_SIZE_USD=10000
MAX_DAILY_LOSS_USD=500
MAX_TOTAL_PORTFOLIO_RISK_PERCENT=5.0

# Database
DATABASE_PATH=./trades.db
```

### 🤖 Sharing with AI Assistants (Claude Desktop, etc.)

This project is properly structured for use with AI coding assistants:

✅ **What AI assistants can safely see:**
- All code files and structure
- Configuration templates (`.env.example`)
- Documentation and tests
- Sample data and demos

❌ **What AI assistants should NEVER see:**
- Your actual `.env` file
- `trades.db` with real trading data
- Any files with actual credentials or account information

**Best Practice:** Always review file contents before sharing with any AI assistant. When in doubt, check if the file is listed in `.gitignore`.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Interactive Brokers account (Paper Trading or Live)
- TWS or IB Gateway installed and running

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/BluEng9/covered-calls-manager.git
cd covered-calls-manager

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables (IMPORTANT!)
cp .env.example .env
nano .env  # Edit with your actual credentials

# 5. Configure application settings (optional)
cp config.yaml.example config.yaml  # If config.yaml.example exists
# Edit config.yaml with your preferences
```

### First Run

```bash
# 1. Start TWS or IB Gateway
# Enable API: Configure > Settings > API > Enable ActiveX and Socket Clients

# 2. Run dashboard
streamlit run dashboard.py --server.port 8508

# 3. Open browser
# http://localhost:8508
```

---

## 📋 Configuration

### config.yaml

The main configuration file controls all aspects of the system:

```yaml
# IBKR Connection
ibkr:
  port: 7497  # 7497 = Paper, 7496 = Live
  client_id: 1
  timeout: 30

# Strategy Parameters
strategy:
  dte_min: 21          # Minimum days to expiration
  dte_max: 45          # Maximum days to expiration
  delta_target: 0.30   # Target delta for options
  min_premium_dollars: 50

# Risk Management
risk:
  max_trades_per_day: 5
  max_position_size_pct: 10.0
  enable_stop_loss: true

# Trading Mode
modes:
  default_mode: "paper"  # demo, paper, or live
```

### Environment Variables

Override configuration using environment variables:

```bash
export CC_IBKR_PORT=7496
export CC_MODES_DEFAULT_MODE=live
export CC_STRATEGY_DTE_MIN=30
```

---

## 💡 Usage Examples

### Basic Usage - Find Best Strikes

```python
from covered_calls_system import CoveredCallStrategy, RiskLevel

# Initialize strategy
strategy = CoveredCallStrategy()

# Find best strikes for TSLA
strikes = strategy.find_best_strikes(
    symbol='TSLA',
    current_price=430.0,
    position_size=100,
    dte_min=21,
    dte_max=45,
    risk_level=RiskLevel.MODERATE
)

for strike in strikes[:5]:
    print(f"Strike ${strike['strike']} | "
          f"Score: {strike['score']}/100 | "
          f"Premium: ${strike['premium']:.2f} | "
          f"Delta: {strike['delta']:.3f}")
```

### Execute Trade with Safety Checks

```python
from safe_trade_integration import SafeTradeExecutor
from safety_features import TradingMode

# Initialize executor
executor = SafeTradeExecutor(ib_connector, mode=TradingMode.PAPER)

# Execute covered call
result = executor.execute_covered_call(
    symbol='AAPL',
    strike=150.0,
    expiration='20240119',
    contracts=1,
    current_price=145.0,
    delta=0.30,
    premium=2.50,
    dte=30
)

if result['success']:
    print(f"✅ Trade executed: {result['trade_id']}")
else:
    print(f"❌ Trade rejected: {result['messages']}")
```

### Query Trade History

```python
from trade_analytics import TradeDatabase, PerformanceAnalyzer

# Initialize database
db = TradeDatabase()

# Get open positions
open_positions = db.get_open_positions()

# Get performance summary
summary = db.get_performance_summary(days=30)
print(f"Win Rate: {summary['win_rate']:.1f}%")
print(f"Total P&L: ${summary['total_pnl']:,.2f}")

# Analyze performance
analyzer = PerformanceAnalyzer(db)
sharpe = analyzer.calculate_sharpe_ratio()
print(f"Sharpe Ratio: {sharpe:.2f}")
```

---

## 🏗️ Architecture

```
covered-calls-manager/
├── config.yaml                 # Main configuration
├── config_manager.py          # Configuration management
├── logging_system.py          # Professional logging
│
├── covered_calls_system.py    # Core strategy engine
├── ibkr_connector.py          # IBKR API integration
├── csv_portfolio_loader.py    # CSV data loader
│
├── safety_features.py         # Pre-trade validation
├── earnings_calendar.py       # Earnings data
├── trade_execution.py         # Order execution
├── safe_trade_integration.py  # Combined execution
│
├── trade_analytics.py         # Performance analytics
├── dashboard.py               # Streamlit UI
│
├── tests/                     # Unit tests
│   ├── test_config_manager.py
│   ├── test_logging_system.py
│   └── test_strategy.py
│
├── logs/                      # Log files
└── requirements.txt           # Dependencies
```

### Key Components

#### Core Engine
- **covered_calls_system.py** - Strategy logic, Greeks calculation, strike scoring
- **ibkr_connector.py** - IBKR API connection, market data, order placement

#### Safety & Execution
- **safety_features.py** - Pre-trade validation, risk limits
- **earnings_calendar.py** - Earnings detection and avoidance
- **trade_execution.py** - Order management and execution
- **safe_trade_integration.py** - Combined safety + execution

#### Analytics
- **trade_analytics.py** - SQLite database, performance metrics
- **dashboard.py** - Interactive Streamlit dashboard

#### Infrastructure
- **config_manager.py** - Centralized configuration
- **logging_system.py** - Multi-file logging with rotation

---

## 🧪 Testing

### Run All Tests

```bash
# Run complete test suite
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_config_manager.py -v
```

### Test Individual Components

```bash
# Test config manager
python config_manager.py

# Test logging system
python logging_system.py

# Test strategy engine
python covered_calls_system.py
```

---

## 📊 Dashboard Guide

### Main Sections

1. **Account Overview**
   - Cash balance, net liquidation, P&L
   - Account summary and buying power

2. **Portfolio**
   - Stock positions with current prices
   - Unrealized P&L per position
   - Available contracts for covered calls

3. **Strategy Finder** 🎯
   - Select stock from portfolio
   - Set DTE range and risk level
   - View top strikes with scores
   - Execute trades directly

4. **Active Positions**
   - Open covered calls
   - Greeks and P&L tracking
   - Roll or close options

5. **Analytics** 📈
   - Performance charts (P&L curve)
   - Trade history
   - Win rate analysis
   - Best/worst trades

### Trading Modes

#### 🎮 Demo Mode
- Simulated data for testing
- No connection required
- Perfect for learning

#### 📝 Paper Trading
- Connect to IBKR Paper account
- Virtual money, real market data
- Test strategies risk-free

#### 💰 Live Trading
- Real money, real trades
- Requires extra confirmation
- Use with caution!

---

## ⚙️ Advanced Features

### Backtesting

```python
from trade_analytics import BacktestEngine

engine = BacktestEngine(strategy, data_source)
results = engine.run(
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_capital=100000
)

print(f"Total Return: {results['total_return']:.1f}%")
print(f"Win Rate: {results['win_rate']:.1f}%")
print(f"Sharpe: {results['sharpe_ratio']:.2f}")
```

### Custom Strategy

```python
from covered_calls_system import CoveredCallStrategy

class MyStrategy(CoveredCallStrategy):
    def score_option(self, option, **params):
        # Custom scoring logic
        score = 0
        
        # Favor high premium
        score += option['premium'] * 10
        
        # Favor moderate delta
        if 0.25 <= option['delta'] <= 0.35:
            score += 30
        
        # Your custom criteria here
        
        return min(score, 100)
```

### Alerts & Notifications

Configure alerts in `config.yaml`:

```yaml
alerts:
  enabled: true
  on_trade_execution: true
  on_assignment_risk: true
  
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    from_address: "your-email@gmail.com"
    to_addresses:
      - "alerts@example.com"
  
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
```

---

## 🔐 Security Best Practices

1. **Never commit credentials**
   ```bash
   # Add to .gitignore
   .credentials.enc
   *.log
   config_local.yaml
   ```

2. **Use environment variables**
   ```bash
   export CC_IBKR_USERNAME="your-username"
   export CC_IBKR_PASSWORD="your-password"
   ```

3. **Enable 2FA in config**
   ```yaml
   security:
     require_auth: true
     session_timeout_minutes: 60
   ```

4. **Encrypt sensitive data**
   ```python
   from config_manager import ConfigManager
   config = ConfigManager()
   config.get('security.encrypt_credentials')  # True
   ```

---

## 🐛 Troubleshooting

### Connection Issues

**Problem:** Can't connect to IBKR  
**Solution:**
1. Check TWS/Gateway is running
2. Verify API is enabled in settings
3. Check port number (7497 for Paper, 7496 for Live)
4. Ensure client ID is unique

### Logging Issues

**Problem:** Logs not appearing  
**Solution:**
```bash
# Check log directory
ls -la logs/

# Set debug level
export CC_LOGGING_LEVEL=DEBUG

# View logs in real-time
tail -f logs/trading.log
```

### Performance Issues

**Problem:** Dashboard is slow  
**Solution:**
- Enable caching in config
- Reduce refresh interval
- Use smaller DTE range
- Limit number of strikes

---

## 📚 Documentation

- **Strategy Guide**: `docs/STRATEGY.md`
- **API Reference**: `docs/API.md`
- **Configuration**: `docs/CONFIG.md`
- **Contributing**: `CONTRIBUTING.md`

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black .
```

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

**This software is for educational purposes only. Options trading involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results. Always do your own research and consider consulting with a licensed financial advisor before making investment decisions.**

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/covered-calls-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/covered-calls-manager/discussions)
- **Email**: support@example.com

---

## 🙏 Acknowledgments

- Interactive Brokers for API access
- [ib_async](https://github.com/erdewit/ib_async) for Python IBKR connector
- [Streamlit](https://streamlit.io/) for the amazing dashboard framework
- [py-vollib](https://github.com/vollib/py_vollib) for IV calculations
- [blackscholes](https://github.com/vollib/py_vollib) for Greeks

---

## 📈 Roadmap

- [ ] Machine Learning strike selection
- [ ] Multi-broker support (TD Ameritrade, E*TRADE)
- [ ] Mobile app (React Native)
- [ ] Cloud deployment (AWS/GCP)
- [ ] Advanced portfolio optimization
- [ ] Social trading features

---

**Made with ❤️ by Options Traders, for Options Traders**

*Happy Trading! 📊*
