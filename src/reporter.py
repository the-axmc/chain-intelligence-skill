#!/usr/bin/env python3
"""
Reporter module for Chain Intelligence.
Provides on-demand metric retrieval and analysis.
"""

import os
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from src.db import get_prices, get_latest_prices, get_metrics, get_gas_history


class MarketReporter:
    """On-demand market data reporter."""
    
    # Token addresses for reference
    TOKEN_METADATA = {
        'BTC': {'name': 'Bitcoin', 'type': 'cryptocurrency'},
        'ETH': {'name': 'Ethereum', 'type': 'cryptocurrency'},
        'LINK': {'name': 'Chainlink', 'type': 'token'},
        'SOL': {'name': 'Solana', 'type': 'cryptocurrency'},
        'AVAX': {'name': 'Avalanche', 'type': 'cryptocurrency'},
        'MATIC': {'name': 'Polygon', 'type': 'token'},
    }
    
    def __init__(self):
        """Initialize the reporter."""
        pass
    
    def get_metrics(self, tokens: List[str], timeframe: str = '24h') -> Dict[str, Dict[str, Any]]:
        """
        Get current market metrics for specified tokens.
        
        Args:
            tokens: List of token symbols (e.g., ['BTC', 'ETH'])
            timeframe: Time window ('1h', '6h', '24h', '7d', '30d')
            
        Returns:
            Dict mapping token symbol to metrics dict
        """
        results = {}
        
        # Parse timeframe to hours
        timeframe_hours = self._parse_timeframe(timeframe)
        
        for token in tokens:
            token_upper = token.upper()
            token_history = get_prices(token_upper, hours=timeframe_hours)
            
            if not token_history:
                # Try to get latest price even if history isn't available
                latest = get_latest_prices([token_upper])
                if latest:
                    token_history = latest
                else:
                    results[token_upper] = {
                        'error': 'No data available',
                        'token': token_upper
                    }
                    continue
            
            # Sort by timestamp descending
            token_history.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Get current and historical prices
            current_price = token_history[0]
            current_ts = current_price['timestamp']
            
            # Find price at timeframe start
            start_ts = current_ts - (timeframe_hours * 3600)
            start_price = None
            start_idx = None
            
            for i, price in enumerate(token_history):
                if price['timestamp'] <= start_ts:
                    start_price = price
                    start_idx = i
                    break
            
            if start_idx is None:
                start_price = token_history[-1]
                start_idx = len(token_history) - 1
            
            # Calculate metrics
            price_change_pct = None
            if start_price:
                price_change_pct = ((current_price['price'] - start_price['price']) / start_price['price']) * 100
            
            # Price range
            prices = [p['price'] for p in token_history if p.get('price') is not None]
            if not prices:
                prices = [0]  # Default to avoid empty sequence error
            price_high = max(prices)
            price_low = min(prices)
            
            # Volume metrics
            volumes = [p['volume_24h'] for p in token_history if p.get('volume_24h') is not None]
            avg_volume = sum(volumes) / len(volumes) if volumes else None
            current_volume = current_price.get('volume_24h')
            
            # Calculate volume change
            volume_change_pct = None
            if start_price and start_price.get('volume_24h') and current_volume is not None:
                if start_price['volume_24h'] != 0:
                    volume_change_pct = ((current_volume - start_price['volume_24h']) / start_price['volume_24h']) * 100
            
            # Market cap
            market_cap = current_price.get('market_cap')
            
            # Calculate 24h volume if not available in database
            if current_volume is None and avg_volume is not None:
                current_volume = avg_volume
            
            results[token_upper] = {
                'token': token_upper,
                'metadata': self.TOKEN_METADATA.get(token_upper, {'name': token_upper}),
                'price': {
                    'current': round(current_price['price'], 4) if current_price.get('price') is not None else None,
                    'high_24h': round(price_high, 4),
                    'low_24h': round(price_low, 4),
                    'change_24h_pct': round(price_change_pct, 4) if price_change_pct is not None else None,
                    'timestamp': current_ts
                },
                'volume': {
                    'current': current_volume,
                    'change_24h_pct': round(volume_change_pct, 4) if volume_change_pct is not None else None,
                    'avg_24h': avg_volume
                },
                'market_cap': market_cap,
                'history': token_history
            }
        
        return results
    
    def get_summary(self, timeframe: str = '24h') -> Dict[str, Any]:
        """
        Get market summary for all tokens.
        
        Args:
            timeframe: Time window
            
        Returns:
            Summary dict with overall market metrics
        """
        tokens = ['BTC', 'ETH', 'LINK', 'SOL', 'AVAX', 'MATIC']
        metrics = self.get_metrics(tokens, timeframe)
        
        # Filter out errors
        valid_metrics = {k: v for k, v in metrics.items() if 'error' not in v}
        
        # Calculate aggregations
        total_mkt_cap = sum(v.get('market_cap', 0) or 0 for v in valid_metrics.values())
        
        # Get gas data
        gas_history = get_gas_history(hours=self._parse_timeframe(timeframe))
        current_gas = gas_history[0] if gas_history else None
        
        # Get latest snapshot time
        timestamps = [v['price']['timestamp'] for v in valid_metrics.values()]
        latest_time = max(timestamps) if timestamps else int(datetime.now().timestamp())
        time_ago = int(datetime.now().timestamp()) - latest_time
        
        return {
            'timestamp': latest_time,
            'time_ago_seconds': time_ago,
            'tokens': valid_metrics,
            'summary': {
                'total_market_cap': total_mkt_cap,
                'token_count': len(valid_metrics),
                'gas_price_gwei': current_gas['gas_price_gwei'] if current_gas else None
            }
        }
    
    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to hours."""
        if timeframe.endswith('d'):
            return int(timeframe[:-1]) * 24
        elif timeframe.endswith('h'):
            return int(timeframe[:-1])
        elif timeframe == '24h':
            return 24
        else:
            return 24  # Default to 24 hours


def get_metrics(tokens: List[str], timeframe: str = '24h') -> Dict[str, Dict[str, Any]]:
    """Convenience function to get market metrics."""
    reporter = MarketReporter()
    return reporter.get_metrics(tokens, timeframe)


def get_summary(timeframe: str = '24h') -> Dict[str, Any]:
    """Convenience function to get market summary."""
    reporter = MarketReporter()
    return reporter.get_summary(timeframe)


if __name__ == '__main__':
    # Example usage
    import json
    
    reporter = MarketReporter()
    
    # Get metrics for BTC and ETH
    metrics = reporter.get_metrics(['BTC', 'ETH'], '24h')
    print("BTC Metrics:")
    print(json.dumps(metrics.get('BTC', {}), indent=2))
    
    print("\nETH Metrics:")
    print(json.dumps(metrics.get('ETH', {}), indent=2))
    
    # Get summary
    summary = reporter.get_summary('24h')
    print("\nMarket Summary:")
    print(json.dumps(summary, indent=2))
