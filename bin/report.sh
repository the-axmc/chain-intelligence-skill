#!/bin/bash
# chain-intelligence PDF Report Generator
# Generates comprehensive market analysis reports

set -e

# Get script directory (parent of bin)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="${SCRIPT_DIR}/src"

# Set up environment
export PYTHONPATH="${SRC_DIR}:${PYTHONPATH}"

# Timeframe (default: 24h)
TIMEFRAME="${1:-24h}"

# Run the PDF generator
python3 -c "import sys; sys.path.insert(0, '${SRC_DIR}'); from pdf import generate_report; generate_report('${TIMEFRAME}')"
