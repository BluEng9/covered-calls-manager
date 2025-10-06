#!/bin/bash
# 🚀 Quick Setup Script for Covered Calls Manager
# התקנה מהירה של הפרויקט

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║  📊 Covered Calls Manager Setup  📊   ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# Check Python version
echo -e "${YELLOW}🔍 Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo -e "${RED}❌ Python 3.11+ required. Found: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $python_version${NC}"

# Create virtual environment
echo -e "\n${YELLOW}🔧 Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${BLUE}ℹ️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "\n${YELLOW}📦 Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✅ Pip upgraded${NC}"

# Install requirements
echo -e "\n${YELLOW}📥 Installing dependencies...${NC}"
echo "This may take a few minutes..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Create necessary directories
echo -e "\n${YELLOW}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p data
mkdir -p backups
echo -e "${GREEN}✅ Directories created${NC}"

# Check if config exists
if [ ! -f "config.yaml" ]; then
    echo -e "\n${YELLOW}📋 Config file not found${NC}"
    echo -e "${BLUE}ℹ️  Please review and edit config.yaml${NC}"
else
    echo -e "\n${GREEN}✅ Config file exists${NC}"
fi

# Run tests
echo -e "\n${YELLOW}🧪 Running tests...${NC}"
python3 run_tests.py --verbose 0

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}⚠️  Some tests failed (non-critical)${NC}"
fi

# Print success message
echo -e "\n${GREEN}"
echo "╔════════════════════════════════════════╗"
echo "║     ✅ Setup Complete! ✅            ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BLUE}📚 Next steps:${NC}"
echo ""
echo "1. Review configuration:"
echo "   ${YELLOW}nano config.yaml${NC}"
echo ""
echo "2. Start TWS or IB Gateway"
echo "   - Enable API in settings"
echo "   - Port 7497 (Paper) or 7496 (Live)"
echo ""
echo "3. Run dashboard:"
echo "   ${YELLOW}streamlit run dashboard.py --server.port 8508${NC}"
echo ""
echo "4. Open browser:"
echo "   ${YELLOW}http://localhost:8508${NC}"
echo ""
echo -e "${GREEN}Happy Trading! 📊${NC}"
