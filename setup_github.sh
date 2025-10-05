#!/bin/bash

# ═══════════════════════════════════════════════════════════════════
# 🚀 Covered Calls Manager - GitHub Setup Script
# ═══════════════════════════════════════════════════════════════════
# This script sets up the GitHub repository and initializes the project
# ═══════════════════════════════════════════════════════════════════

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════════"
echo "  📈 Covered Calls Manager - Setup Script"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${NC}"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed. Please install git first.${NC}"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8+.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}\n"

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}📦 Initializing Git repository...${NC}"
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}\n"
else
    echo -e "${GREEN}✅ Git repository already exists${NC}\n"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}📝 Creating .gitignore...${NC}"
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover

# Jupyter
.ipynb_checkpoints
*.ipynb

# Environment variables
.env
.env.local
*.secret

# Logs
*.log
logs/

# Data files
*.csv
*.xlsx
*.db
*.sqlite

# IBKR
*.json.bak
twsapi_macunix.*.log

# OS
.DS_Store
Thumbs.db

# Project specific
portfolio_*.json
backtest_results/
EOF
    echo -e "${GREEN}✅ .gitignore created${NC}\n"
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}\n"
fi

# Activate virtual environment
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}\n"

# Upgrade pip
echo -e "${YELLOW}📦 Upgrading pip...${NC}"
pip install --upgrade pip
echo -e "${GREEN}✅ Pip upgraded${NC}\n"

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}📥 Installing dependencies...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}\n"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Create LICENSE if it doesn't exist
if [ ! -f "LICENSE" ]; then
    echo -e "${YELLOW}📜 Creating MIT License...${NC}"
    YEAR=$(date +%Y)
    cat > LICENSE << EOF
MIT License

Copyright (c) $YEAR Covered Calls Manager Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
    echo -e "${GREEN}✅ LICENSE created${NC}\n"
fi

# Run tests to verify installation
echo -e "${YELLOW}🧪 Running tests...${NC}"
if python test_system.py; then
    echo -e "${GREEN}✅ All tests passed!${NC}\n"
else
    echo -e "${RED}❌ Some tests failed. Please check the output above.${NC}\n"
fi

# Add all files to git
echo -e "${YELLOW}📤 Adding files to git...${NC}"
git add .

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}ℹ️  No changes to commit${NC}\n"
else
    # Commit
    echo -e "${YELLOW}💾 Creating initial commit...${NC}"
    git commit -m "Initial commit: Covered Calls Manager

Features:
- Core strategy engine with Greeks calculations
- Interactive Brokers connector
- Streamlit dashboard
- TradingView Pine Script indicator
- Comprehensive test suite
- Full documentation

Total: 2,150+ lines of code"
    echo -e "${GREEN}✅ Initial commit created${NC}\n"
fi

# Ask if user wants to create GitHub repository
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Would you like to push to GitHub? (y/n)${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${YELLOW}Please enter your GitHub repository URL:${NC}"
    echo -e "${BLUE}Example: https://github.com/username/covered-calls-manager.git${NC}"
    read -r repo_url

    if [ -n "$repo_url" ]; then
        # Add remote if it doesn't exist
        if ! git remote | grep -q "origin"; then
            git remote add origin "$repo_url"
            echo -e "${GREEN}✅ Remote 'origin' added${NC}\n"
        fi

        # Push to GitHub
        echo -e "${YELLOW}🚀 Pushing to GitHub...${NC}"
        git branch -M main
        git push -u origin main

        echo -e "${GREEN}✅ Successfully pushed to GitHub!${NC}\n"
        echo -e "${BLUE}Your repository is now live at:${NC}"
        echo -e "${BLUE}$repo_url${NC}\n"
    else
        echo -e "${YELLOW}⏭️  Skipping GitHub push${NC}\n"
    fi
else
    echo -e "${YELLOW}⏭️  Skipping GitHub setup${NC}\n"
fi

# Final instructions
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}\n"
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Configure Interactive Brokers TWS/Gateway"
echo -e "  2. Run the dashboard: ${YELLOW}streamlit run dashboard.py${NC}"
echo -e "  3. Or use the system programmatically in Python"
echo -e "  4. Import Pine Script to TradingView"
echo -e "\n${BLUE}Documentation:${NC}"
echo -e "  • README.md - Full documentation"
echo -e "  • test_system.py - Run tests"
echo -e "  • covered_calls_system.py - Core API"
echo -e "\n${YELLOW}⚠️  Remember:${NC}"
echo -e "  • Start with paper trading"
echo -e "  • This is not financial advice"
echo -e "  • Always manage your risk"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Deactivate virtual environment
deactivate 2>/dev/null || true

exit 0
