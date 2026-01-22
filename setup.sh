#!/bin/bash

echo "=== Job Scraper Setup ==="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To run the scraper:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run scraper: python main.py"
echo ""
echo "To test the setup:"
echo "  python test_scraper.py"
echo ""
