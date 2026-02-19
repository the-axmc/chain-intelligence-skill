# Chain Intelligence Skill

A skill for on-chain market intelligence using Chainlink data feeds and CoinGecko as a fallback.

## Overview

Chain Intelligence provides real-time on-chain market data collection, analysis, and reporting for cryptocurrency assets. It uses the Chainlink Data Feeds API as the primary data source, with CoinGecko as a fallback for volume and supply data when Chainlink is unreachable.

### Features

- **Real-time Data Collection** - Fetches market data every 5 minutes via cron
- **Multi-Exchange Support** - Collects prices from Binance, Coinbase, and Kraken
- **Cross-Exchange Spread Analysis** - Identifies arbitrage opportunities
- **Aave Lending Rates** - Tracks supply, borrow, and utilization rates
- **Gas Price Monitoring** - Monitors Ethereum gas prices
- **Fundamental Analysis** - Analyzes 24-hour data for opportunities and risks
- **PDF Report Generation** - Creates comprehensive market reports

## Architecture

### Components

1. **Snapshot Collector** (`src/collector.py`) - Collects market data and stores it in SQLite
2. **On-Demand Reporter** (`src/reporter.py`) - Retrieves metrics for specific tokens and timeframes
3. **Fundamental Analyzer** (`src/analyzer.py`) - Analyzes 24-hour data for opportunities and anomalies
4. **PDF Report Generator** (`src/pdf.py`) - Generates comprehensive market reports as PDFs

### Data Flow

```
Chainlink API → Collector → SQLite Database → Analyzer → Reports
                                 ↳ CoinGecko (fallback)
                                 ↳ Exchange APIs (multi-exchange)
```

## Installation

### Requirements

- Python 3.8+
- pip

### Setup

```bash
cd ~/.openclaw/workspace/skills/chain-intelligence
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the skill directory:

```env
CHAINLINK_API_URL=https://data-api.chain.link/v1
COINGECKO_API_URL=https://api.coingecko.com/api/v3
DATABASE_PATH=~/.openclaw/workspace-scout/signals/chain-intel/metrics.db
OUTPUT_DIR=~/.openclaw/workspace-scout/signals/chain-intel/reports
```

## Usage

### Collect Market Data

Run the collector to fetch and store market snapshots:

```bash
./bin/collect.sh
```

Or run it manually:

```bash
python src/collector.py
```

### Get Market Metrics

Use the reporter to get current metrics:

```python
from src.reporter import get_metrics

# Get metrics for BTC and ETH over the last 24 hours
metrics = get_metrics(['btc', 'eth'], '24h')
print(metrics)
```

### Analyze Market Fundamentals

Run the analyzer to detect opportunities:

```bash
./bin/analyze.sh
```

Or programmatically:

```python
from src.analyzer import analyze_24h

analysis = analyze_24h()
print(analysis)
```

### Generate PDF Report

Generate a comprehensive market report:

```bash
./bin/report.sh
```

Or programmatically:

```python
from src.pdf import generate_report

generate_report('24h')
```

### Run the Full Demonstration

```bash
python main.py
```

## File Structure

```
chain-intelligence/
├── bin/                      # Shell scripts for quick execution
│   ├── collect.sh           # Run the data collector
│   ├── analyze.sh           # Run the fundamental analyzer
│   └── report.sh            # Generate a PDF report
├── src/                      # Python source modules
│   ├── __init__.py
│   ├── collector.py         # Data collection from Chainlink, exchanges, Aave
│   ├── reporter.py          # On-demand metric retrieval
│   ├── analyzer.py          # 24h fundamental analysis
│   ├── pdf.py               # PDF report generation
│   └── db.py                # SQLite database operations
├── templates/                # HTML templates for reports
│   └── report.html          # HTML report template
├── SKILL.md                  # This skill's documentation
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── package.json              # npm-style metadata (optional)
└── .env                      # Environment configuration (created by user)
```

## Data Schema

The SQLite database stores the following tables:

### `prices`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| token_symbol | TEXT | Token symbol (e.g., BTC, ETH) |
| token_address | TEXT | Contract address (optional) |
| price | REAL | Current price in USD |
| volume_24h | REAL | 24-hour trading volume |
| market_cap | REAL | Market capitalization |
| timestamp | INTEGER | Unix timestamp |
| created_at | INTEGER | Creation time (auto) |

### `gas`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| gas_price_gwei | REAL | Gas price in Gwei |
| block_time_ms | INTEGER | Block time estimate |
| timestamp | INTEGER | Unix timestamp |
| created_at | INTEGER | Creation time (auto) |

### `metrics`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| token_symbol | TEXT | Token symbol |
| name | TEXT | Metric name |
| value | REAL | Metric value |
| timestamp | INTEGER | Unix timestamp |
| created_at | INTEGER | Creation time (auto) |

### `spreads`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| token_symbol | TEXT | Token symbol |
| min_price | REAL | Minimum price across exchanges |
| max_price | REAL | Maximum price across exchanges |
| avg_price | REAL | Average price |
| spread | REAL | Price spread (max - min) |
| spread_pct | REAL | Spread percentage |
| best_exchange | TEXT | Exchange with lowest price |
| worst_exchange | TEXT | Exchange with highest price |
| timestamp | INTEGER | Unix timestamp |
| created_at | INTEGER | Creation time (auto) |

### `aave_rates`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| token_symbol | TEXT | Token symbol |
| supply_rate | REAL | Supply APR (%) |
| borrow_rate | REAL | Borrow APR (%) |
| utilization_rate | REAL | Utilization rate (%) |
| source | TEXT | Data source identifier |
| timestamp | INTEGER | Unix timestamp |
| created_at | INTEGER | Creation time (auto) |

## Data Sources

### Chainlink Data Feeds API
- **Base URL**: `https://data-api.chain.link/v1`
- **Provides**: Price feeds for various assets
- **Limitation**: May be unreachable from some environments

### CoinGecko API
- **Base URL**: `https://api.coingecko.com/api/v3`
- **Provides**: Volume, market cap, and supply data as fallback

### Exchange APIs
- **Binance**: `https://api.binance.com`
- **Coinbase**: `https://api.coinbase.com`
- **Kraken**: `https://api.kraken.com`
- **Provides**: Multi-exchange price data for spread analysis

### Aave Subgraph API
- **URL**: `https://api.thegraph.com/subgraphs/name/aave/protocol-v3`
- **Provides**: Lending protocol rates

## Cron Setup

Add to your crontab to run collection every 5 minutes:

```cron
*/5 * * * * /home/axmc/.openclaw/workspace/skills/chain-intelligence/bin/collect.sh
```

## Output Format

### Metrics Output (JSON)
```json
{
  "price": 65432.10,
  "volume_24h": 35000000000,
  "market_cap": 1280000000000,
  "price_change_24h": 2.45,
  "volume_change_24h": -1.2,
  "timestamp": 1708288800
}
```

### Analysis Output (JSON)
```json
{
  "price_action": {
    "current_price": 65432.10,
    "open_24h": 63850.00,
    "high_24h": 65890.00,
    "low_24h": 63780.00,
    "price_change_pct": 2.48
  },
  "volume_trend": {
    "current_volume": 35000000000,
    "average_24h": 33500000000,
    "trend": "increasing"
  },
  "volatility": {
    "historical_volatility": 3.2,
    "current_volatility": 2.8,
    "level": "moderate"
  },
  "opportunities": [...],
  "risks": [...]
}
```

## Troubleshooting

### Connection Errors
If you encounter connection errors, check:
- API availability (`curl $CHAINLINK_API_URL`)
- Network connectivity
- Firewall settings

### Database Issues
If the database is corrupted:
```bash
rm ~/.openclaw/workspace-scout/signals/chain-intel/metrics.db
python src/collector.py
```

### Missing Data
Some assets may not have data available. Check:
- Asset symbol/contract address
- API rate limits
- Data availability in the source

## Extending

To add new data sources:

1. Add a new module in `src/`
2. Implement the data fetching logic
3. Update `collector.py` to include the new source
4. Update the database schema if needed

## License

MIT License - see license file for details.
