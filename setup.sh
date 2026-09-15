#!/usr/bin/env bash

# Enterprise Job Scraper & Resume Intelligence Engine - Local Setup Script
# Works on macOS and Linux

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}  Enterprise Job Scraper & Resume Intelligence Engine - Setup Script${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""

# 1. Check Python installation
echo -e "${CYAN}[1/6] Checking Python environment...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo -e "${RED}Error: Python 3 is not installed or not in PATH.${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

# 2. Virtual Environment Setup
echo ""
echo -e "${CYAN}[2/6] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment in ./venv..."
    $PYTHON_CMD -m venv venv
else
    echo "Virtual environment ./venv already exists."
fi

# Determine virtual environment python & pip binaries
VENV_PYTHON="./venv/bin/python"
VENV_PIP="./venv/bin/pip"
if [ -f "./venv/Scripts/python.exe" ]; then
    VENV_PYTHON="./venv/Scripts/python.exe"
    VENV_PIP="./venv/Scripts/pip.exe"
fi

echo -e "${CYAN}Upgrading pip and installing Python dependencies...${NC}"
$VENV_PIP install --upgrade pip --quiet
$VENV_PIP install -r requirements.txt --quiet
echo -e "${GREEN}✓ Python dependencies installed.${NC}"

# 3. Environment Configuration
echo ""
echo -e "${CYAN}[3/6] Setting up environment variables...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file from .env.example.${NC}"
        echo -e "${YELLOW}Notice: Default development credentials and settings have been applied in .env.${NC}"
    else
        echo -e "${YELLOW}Warning: .env.example not found. Skipping .env creation.${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file already exists.${NC}"
fi

# 4. Database Setup & Migration
echo ""
echo -e "${CYAN}[4/6] Initializing SQLite database and migrating historical data...${NC}"
$VENV_PYTHON -m backend.migrate
echo -e "${GREEN}✓ Database initialized (jobscraper.db).${NC}"

# 5. Frontend Dependencies Setup
echo ""
echo -e "${CYAN}[5/6] Checking Frontend environment (Node.js & npm)...${NC}"
if command -v npm &> /dev/null; then
    NODE_VERSION=$(node -v 2>/dev/null || echo "installed")
    echo -e "${GREEN}✓ Node.js ($NODE_VERSION) and npm found.${NC}"
    if [ -d "frontend" ]; then
        echo "Installing frontend npm packages..."
        (cd frontend && npm install --silent)
        echo -e "${GREEN}✓ Frontend dependencies installed.${NC}"
    fi
else
    echo -e "${YELLOW}Warning: npm is not installed. You can run the backend and scraper, but Node.js is required for the React Web Dashboard.${NC}"
fi

# 6. Verification & Test Suite Run
echo ""
echo -e "${CYAN}[6/6] Running automated unit test suite...${NC}"
$VENV_PYTHON -m unittest discover tests
echo -e "${GREEN}✓ All unit tests passed successfully!${NC}"

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}                     🎉 SETUP COMPLETE!                              ${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "You can now run the system using any of the following modes:"
echo ""
echo -e "${CYAN}1. Run Scraper Pipeline (CLI Mode):${NC}"
echo -e "   source venv/bin/activate && python main.py"
echo ""
echo -e "${CYAN}2. Run FastAPI REST API Server (Port 8000):${NC}"
echo -e "   source venv/bin/activate && uvicorn backend.api:app --reload"
echo -e "   Swagger Documentation: http://localhost:8000/docs"
echo ""
echo -e "${CYAN}3. Run Web Dashboard (Port 5173):${NC}"
echo -e "   cd frontend && npm run dev"
echo ""
echo -e "${CYAN}4. Run with Docker Compose (Full Stack):${NC}"
echo -e "   docker-compose up --build -d"
echo ""
