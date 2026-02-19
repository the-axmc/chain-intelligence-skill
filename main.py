#!/usr/bin/env python3
"""
Chain Intelligence - On-chain Market Intelligence Skill
Main entry point for demonstration.
"""

from datetime import datetime
import json
import os
import sys

# Add src directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_dir, 'src'))

from db import init_db
from collector import ChainlinkCollector, collect_single_token
from reporter import get_metrics, get_summary
from analyzer import analyze_24h, get_asset_score
from pdf import generate_report


def main():
    """Run the Chain Intelligence demonstration."""
    print("=" * 60)
    print("Chain Intelligence - On-chain Market Intelligence")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize database
    print("1. Initializing database...")
    init_db()
    print("   Database initialized successfully!")
    print()
    
    # Collect sample data
    print("2. Collecting market data...")
    collector = ChainlinkCollector()
    results = collector.collect(['BTC', 'ETH'])
    print(f"   Prices collected: {len(results['prices'])}")
    print(f"   Gas data collected: {'Yes' if results['gas'] else 'No'}")
    print()
    
    # Get metrics
    print("3. Getting market metrics...")
    metrics = get_metrics(['BTC', 'ETH'], '24h')
    for token, data in metrics.items():
        if 'error' not in data:
            price = data['price']['current']
            change = data['price']['change_24h_pct']
            print(f"   {token}: ${price:.2f} ({change:+.2f}% change)")
        else:
            print(f"   {token}: {data['error']}")
    print()
    
    # Get summary
    print("4. Getting market summary...")
    summary = get_summary('24h')
    print(f"   Tokens analyzed: {summary['summary']['token_count']}")
    print()
    
    # Analyze fundamentals
    print("5. Analyzing market fundamentals...")
    analysis = analyze_24h(['BTC', 'ETH'])
    print(f"   Opportunities detected: {len(analysis['opportunities'])}")
    print(f"   Risks detected: {len(analysis['risks'])}")
    print()
    
    # Asset scores
    print("6. Computing asset scores...")
    for token in ['BTC', 'ETH']:
        score = get_asset_score(token)
        if 'error' not in score:
            print(f"   {token}: {score['score']:.1f}/100 ({score['rating']})")
        else:
            print(f"   {token}: {score['error']}")
    print()
    
    # Generate PDF report
    print("7. Generating PDF report...")
    output = generate_report('24h')
    print(f"   Report saved to: {output}")
    print()
    
    print("=" * 60)
    print("Chain Intelligence completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
