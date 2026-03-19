#!/bin/bash
# chain-intelligence web dashboard
# Serves historical market data and generated reports

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

python3 -m src.webapp
