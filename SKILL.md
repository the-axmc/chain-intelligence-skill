# Chain Intelligence Skill

A skill for on-chain market intelligence using Chainlink data feeds.

## Overview

Chain Intelligence provides real-time on-chain market data collection, analysis, and reporting for cryptocurrency assets. It uses the Chainlink Data Feeds API as the primary data source, with CoinGecko as a fallback for volume and supply data.

## Architecture

### Components

1. **Snapshot Collector** - Collects market data every 5 minutes and stores it in SQLite
2. **On-Demand Reporter** - Retrieves metrics for specific tokens and timeframes
3. **Fundamental Analyzer** - Analyzes 24-hour data for opportunities and anomalies
4. **PDF Report Generator** - Generates comprehensive market reports as PDFs

### Data Flow

```
Chainlink API → Collector → SQLite Database → Analyzer → Reports
```

## Installation

```bash
pip install requests python-dotenv reportlab jinja2
```

## Configuration

Create a `.env` file in the skill directory:

```env
CHAINLINK_API_URL=https://data-api.chain.link/v1
COINGECKO_API_URL=https://api.coingecko.com/api/v3
DATABASE_PATH=~/.openclaw/workspace-scout/signals/chain-intel/metrics.db
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

## Data Schema

The SQLite database stores the following tables:

### `prices`
- `id` (INTEGER, PRIMARY KEY)
- `token_symbol` (TEXT)
- `token_address` (TEXT)
- `price` (REAL)
- `volume_24h` (REAL)
- `market_cap` (REAL)
- `timestamp` (INTEGER)

### `gas`
- `id` (INTEGER, PRIMARY KEY)
- `gas_price_gwei` (REAL)
- `block_time_ms` (INTEGER)
- `timestamp` (INTEGER)

### `metrics`
- `id` (INTEGER, PRIMARY KEY)
- `name` (TEXT)
- `value` (REAL)
- `timestamp` (INTEGER)

## Data Sources

### Chainlink Data Feeds API
- Base URL: `https://data-api.chain.link/v1`
- Provides: Price feeds for various assets

### CoinGecko API
- Base URL: `https://api.coingecko.com/api/v3`
- Provides: Volume, market cap, and supply data as fallback

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
    "change_percent": 2.48
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
  "opportunities": [
    {
      "type": "bullish_divergence",
      "asset": "BTC",
      "description": "Price made lower low while RSI made higher low"
    }
  ],
  "risks": [
    {
      "type": "high_volatility",
      "asset": "ETH",
      "description": " volatility exceeded historical average"
    }
  ]
}
```

## PDF Report Contents

The generated PDF includes:

1. **Executive Summary** - Key metrics and highlights
2. **Price Action** - 24h price chart and performance
3. **Volume Analysis** - Trading volume trends
4. **Opportunities** - Detected bullish/bearish patterns
5. **Risks** - Identified market risks and warnings

## Extending

To add new data sources:

1. Add a new module in `src/`
2. Implement the data fetching logic
3. Update `collector.py` to include the new source
4. Update the database schema if needed

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

