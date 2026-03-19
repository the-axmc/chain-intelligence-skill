# Chain Intelligence Skill

An on-chain market intelligence system for collecting market data, generating reports, and browsing historical trends through a live dashboard.

## Overview

Chain Intelligence provides scheduled market data collection, analysis, report generation, and a web dashboard for cryptocurrency assets. It uses the Chainlink Data Feeds API as the primary data source, with CoinGecko as a fallback for volume and supply data when Chainlink is unreachable.

### Features

- **Scheduled Data Collection** - Fetches market data every 5 minutes via cron or a managed scheduler
- **Multi-Exchange Support** - Collects prices from Binance, Coinbase, and Kraken
- **Cross-Exchange Spread Analysis** - Identifies arbitrage opportunities
- **Aave Lending Rates** - Tracks supply, borrow, and utilization rates
- **Gas Price Monitoring** - Monitors Ethereum gas prices
- **Fundamental Analysis** - Analyzes 24-hour data for opportunities and risks
- **PDF Report Generation** - Creates comprehensive market reports
- **Live Web Dashboard** - Shows historical data, archives, and the latest generated report

## Architecture

### Components

1. **Snapshot Collector** (`src/collector.py`) - Collects market data and stores it in the database
2. **On-Demand Reporter** (`src/reporter.py`) - Retrieves metrics for specific tokens and timeframes
3. **Fundamental Analyzer** (`src/analyzer.py`) - Analyzes market data for opportunities and anomalies
4. **PDF Report Generator** (`src/pdf.py`) - Generates comprehensive market reports as PDFs and HTML snapshots
5. **Web Dashboard** (`src/webapp.py`) - Serves the live frontend and archived reports

### Data Flow

```
Chainlink API → Collector → Database → Analyzer → Reports → Web Dashboard
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

For production deployments, replace the local file-based paths with managed services:

- `DATABASE_PATH` should point to a managed database connection layer or be replaced by a Postgres client configuration.
- `OUTPUT_DIR` should map to object storage or a durable mounted volume for report artifacts.
- Secrets should come from a managed secret store instead of a local `.env` file.

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

The report generator also writes an HTML snapshot into the reports directory, so the latest report is visible in the web dashboard.

### Open the Web Dashboard

Serve the historical data and report archive locally:

```bash
./bin/web.sh
```

The dashboard auto-refreshes in place, so changing token/timeframe or generating a new report updates the charts and archive without reloading the page.

### Production Deployment

For a fully managed deployment, split the system into these pieces:

1. A managed web service for the dashboard.
2. A scheduled job that runs collection, analysis, and report generation.
3. A managed database for market data.
4. Durable object storage for PDF and HTML report artifacts.
5. A managed scheduler such as Cloud Scheduler to trigger ingestion.

In that setup, the dashboard only reads data and renders views. The scheduled job is the only path that writes new market snapshots and publishes fresh reports.

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
│   ├── report.sh            # Generate a PDF report
│   └── web.sh               # Launch the web dashboard
├── src/                      # Python source modules
│   ├── __init__.py
│   ├── collector.py         # Data collection from Chainlink, exchanges, Aave
│   ├── reporter.py          # On-demand metric retrieval
│   ├── analyzer.py          # 24h fundamental analysis
│   ├── pdf.py               # PDF report generation
│   ├── webapp.py            # Flask dashboard and archive
│   └── db.py                # Database operations
├── templates/                # HTML templates for reports
│   ├── dashboard.html       # Historical data dashboard
│   └── report.html          # HTML report template
├── SKILL.md                  # This skill's documentation
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── package.json              # npm-style metadata (optional)
└── .env                      # Environment configuration (created by user)
```

## Data Schema

The database stores the following tables locally by default. Production deployments should use a managed database backend:

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

## Production Notes

- The dashboard reads stored market data and the latest generated report.
- Scheduled ingestion should be idempotent because managed schedulers may deliver duplicate triggers.
- Managed deployments should avoid relying on local files for persistent data.
- The report archive should be treated as durable output, not temporary build artifacts.

## Cron Setup

Local-only setups can still use cron to run collection every 5 minutes:

```cron
*/5 * * * * /home/axmc/.openclaw/workspace/skills/chain-intelligence/bin/collect.sh
```

For production, prefer a managed scheduler instead of a host crontab.

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
