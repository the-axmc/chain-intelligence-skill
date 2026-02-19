#!/bin/bash
# chain-intelligence Snapshot Collector
# Fetches and stores market data from Chainlink API

set -e

# Get script directory (parent of bin)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="${SCRIPT_DIR}/src"

# Set up environment
export PYTHONPATH="${SRC_DIR}:${PYTHONPATH}"

# Check for required dependencies
echo "Checking dependencies..."
python3 -c "import requests" 2>/dev/null || { echo "Error: requests library not found"; exit 1; }

# Run the collector
echo "Starting data collection..."
python3 -c "import sys; sys.path.insert(0, '${SRC_DIR}'); from collector import main; main()"
