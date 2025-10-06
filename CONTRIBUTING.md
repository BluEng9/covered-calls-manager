# 🤝 Contributing to Covered Calls Manager

First off, thank you for considering contributing to Covered Calls Manager! It's people like you that make this project better for everyone.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

---

## 📜 Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:

- Be respectful and inclusive
- Welcome newcomers
- Focus on what is best for the community
- Show empathy towards other community members

---

## 🎯 How Can I Contribute?

### Reporting Bugs 🐛

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, configuration)
- **Describe the behavior you observed** and what you expected
- **Include logs and error messages**
- **Specify your environment** (OS, Python version, etc.)

**Template:**
```markdown
## Bug Description
[Clear description of the bug]

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

## Environment
- OS: [e.g., macOS 14.0]
- Python: [e.g., 3.11.5]
- Version: [e.g., v2.1.0]

## Logs
```
[Paste relevant logs]
```
```

### Suggesting Enhancements 💡

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the proposed enhancement
- **Explain why this enhancement would be useful**
- **Include code examples** if applicable
- **List any alternatives** you've considered

---

## 💻 Development Setup

### 1. Fork & Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR-USERNAME/covered-calls-manager.git
cd covered-calls-manager
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Install Pre-commit Hooks

```bash
pre-commit install
```

### 5. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

---

## 📏 Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length**: 100 characters (not 80)
- **Quotes**: Double quotes for strings
- **Imports**: Grouped and sorted (use `isort`)
- **Formatting**: Use `black` for auto-formatting

### Code Format

```python
# Good ✅
def calculate_premium(
    strike: float,
    current_price: float,
    days_to_expiration: int
) -> float:
    """
    Calculate option premium using simplified model.
    
    Args:
        strike: Strike price
        current_price: Current stock price
        days_to_expiration: Days until expiration
    
    Returns:
        Estimated premium in dollars
    """
    # Implementation
    pass


# Bad ❌
def calc_prem(s,p,d):
    # No docstring, unclear names, no type hints
    pass
```

### Documentation

- **All functions must have docstrings**
- Use Google-style docstrings
- Include type hints for parameters and returns
- Add examples for complex functions

```python
def find_best_strike(
    symbol: str,
    current_price: float,
    dte: int = 30,
    risk_level: RiskLevel = RiskLevel.MODERATE
) -> List[Dict]:
    """
    Find best strike prices for covered calls.
    
    Args:
        symbol: Stock ticker symbol
        current_price: Current stock price
        dte: Days to expiration (default: 30)
        risk_level: Risk tolerance level
    
    Returns:
        List of option dictionaries sorted by score
    
    Example:
        >>> strikes = find_best_strike("AAPL", 150.0, dte=30)
        >>> print(strikes[0]['strike'])
        155.0
    """
    # Implementation
    pass
```

### Naming Conventions

- **Functions/Methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

```python
# Classes
class OptionCalculator:
    pass

# Constants
MAX_CONTRACTS = 10
DEFAULT_DTE = 30

# Functions
def calculate_greeks():
    pass

# Private
def _internal_helper():
    pass
```

---

## 🧪 Testing

### Writing Tests

- **Every new feature must have tests**
- **Aim for >80% code coverage**
- **Test edge cases and error handling**
- **Use descriptive test names**

```python
import unittest

class TestOptionCalculations(unittest.TestCase):
    """Tests for option calculation functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.calculator = OptionCalculator()
    
    def test_delta_calculation_itm_option(self):
        """Test delta calculation for in-the-money option"""
        delta = self.calculator.calculate_delta(
            stock_price=100,
            strike=95,
            dte=30
        )
        
        # ITM call should have delta > 0.5
        self.assertGreater(delta, 0.5)
        self.assertLess(delta, 1.0)
    
    def test_delta_calculation_otm_option(self):
        """Test delta calculation for out-of-the-money option"""
        delta = self.calculator.calculate_delta(
            stock_price=100,
            strike=105,
            dte=30
        )
        
        # OTM call should have delta < 0.5
        self.assertLess(delta, 0.5)
        self.assertGreater(delta, 0.0)
    
    def test_invalid_input_raises_error(self):
        """Test that invalid inputs raise appropriate errors"""
        with self.assertRaises(ValueError):
            self.calculator.calculate_delta(
                stock_price=-100,  # Invalid negative price
                strike=95,
                dte=30
            )
```

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test file
python run_tests.py --file test_greeks.py

# Run with coverage
python run_tests.py --coverage

# Run with pytest (alternative)
pytest tests/ -v
pytest tests/test_greeks.py -v
```

### Test Coverage

We aim for >80% code coverage:

```bash
# Generate coverage report
coverage run -m pytest
coverage report
coverage html  # Creates htmlcov/index.html
```

---

## 🔄 Pull Request Process

### Before Submitting

1. **Run all tests** and ensure they pass
2. **Update documentation** if needed
3. **Add/update tests** for your changes
4. **Run code formatters**:
   ```bash
   black .
   isort .
   flake8
   ```
5. **Check type hints**: `mypy .`
6. **Update CHANGELOG.md**

### Submitting

1. **Push your branch** to your fork
2. **Create a Pull Request** on GitHub
3. **Fill in the PR template**:

```markdown
## Description
[Describe your changes]

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Tested manually

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

4. **Wait for review** and address feedback

### Review Process

- Maintainers will review within 3-5 days
- Address review comments
- Once approved, your PR will be merged!

---

## 🏗️ Project Structure

Understanding the project structure helps with contributions:

```
covered-calls-manager/
├── config.yaml               # Configuration
├── config_manager.py        # Config management
├── logging_system.py        # Logging
│
├── covered_calls_system.py  # Core engine
├── ibkr_connector.py        # IBKR API
├── safety_features.py       # Pre-trade checks
├── trade_execution.py       # Order execution
├── trade_analytics.py       # Performance tracking
│
├── dashboard.py             # Streamlit UI
│
├── tests/                   # Unit tests
│   ├── test_config_manager.py
│   ├── test_greeks.py
│   └── test_strategy.py
│
├── docs/                    # Documentation
└── requirements.txt         # Dependencies
```

---

## 📝 Commit Messages

Use clear, descriptive commit messages:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Examples

```bash
# Good ✅
feat(strategy): add volatility-based strike selection

Implement new algorithm that adjusts strike selection based on
current IV percentile. Includes backtesting results showing 15%
improvement in returns.

Closes #123

# Bad ❌
updated stuff
```

---

## 🎨 Style Guide Summary

```python
# Imports (grouped and sorted)
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from config_manager import get_config
from logging_system import get_logger

# Constants
MAX_POSITION_SIZE = 1000
DEFAULT_TIMEOUT = 30

# Class
class TradingStrategy:
    """Strategy for selecting covered call strikes."""
    
    def __init__(self, risk_level: RiskLevel):
        self.risk_level = risk_level
        self.logger = get_logger(__name__)
    
    def find_strikes(self, symbol: str) -> List[Dict]:
        """Find optimal strikes for given symbol."""
        self.logger.info(f"Finding strikes for {symbol}")
        # Implementation
        pass

# Function
def calculate_premium(
    strike: float,
    stock_price: float,
    dte: int
) -> float:
    """Calculate estimated premium."""
    if strike <= 0 or stock_price <= 0:
        raise ValueError("Prices must be positive")
    
    # Calculation
    return premium
```

---

## 🐛 Debugging Tips

### Enable Debug Logging

```python
# In config.yaml
logging:
  level: DEBUG
  
# Or via environment variable
export CC_LOGGING_LEVEL=DEBUG
```

### Interactive Debugging

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use IPython
from IPython import embed; embed()
```

### Check Logs

```bash
# View logs in real-time
tail -f logs/trading.log
tail -f logs/errors.log

# Search for errors
grep ERROR logs/trading.log
```

---

## 📞 Getting Help

- **Discussions**: [GitHub Discussions](https://github.com/yourusername/covered-calls-manager/discussions)
- **Issues**: [GitHub Issues](https://github.com/yourusername/covered-calls-manager/issues)
- **Email**: contribute@example.com

---

## 🎁 Recognition

Contributors will be acknowledged in:
- README.md Contributors section
- CHANGELOG.md for each release
- GitHub contributor graph

Thank you for contributing! 🙏

---

**Happy Coding! 🚀**
