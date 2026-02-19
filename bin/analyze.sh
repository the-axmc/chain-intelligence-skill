#!/bin/bash
# chain-intelligence Fundamental Analyzer
# Analyzes market data for opportunities and risks

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/src"

# Set up environment
export PYTHONPATH="${SRC_DIR}:${PYTHONPATH}"

# Change to source directory
cd "${SRC_DIR}"

# Timeframe (default: 24h)
TIMEFRAME="${1:-24h}"

# Run the analyzer
python3 analyzer.py
