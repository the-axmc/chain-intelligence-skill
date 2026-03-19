#!/usr/bin/env python3
"""
Analyzer module for Chain Intelligence.
Performs fundamental analysis on on-chain market data.
"""

import json
import math
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from src.db import get_prices, get_latest_prices, get_metrics, get_gas_history


class FundamentalAnalyzer:
    """24-hour fundamental analyzer for crypto markets."""
    
    # Volatility thresholds
    VOLATILITY_THRESHOLD_LOW = 2.0
    VOLATILITY_THRESHOLD_MODERATE = 5.0
    VOLATILITY_THRESHOLD_HIGH = 10.0
    
    # Volume change thresholds
    VOLUME_CHANGE_THRESHOLD_LOW = 10
    VOLUME_CHANGE_THRESHOLD_HIGH = 50
    
    # Price action thresholds
    PRICE_CHANGE_BULLISH = 5.0
    PRICE_CHANGE_BEARISH = -5.0
    
    def __init__(self):
        """Initialize the analyzer."""
        self.tokens = ['BTC', 'ETH', 'LINK', 'SOL', 'AVAX', 'MATIC']
        self.hours = 24
    
    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse a timeframe string into hours."""
        timeframe = timeframe.strip().lower()

        if timeframe.endswith('d'):
            return int(timeframe[:-1]) * 24
        if timeframe.endswith('h'):
            return int(timeframe[:-1])
        if timeframe == '24h':
            return 24
        return 24

    def analyze(self, timeframe: str = '24h', tokens: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze market fundamentals for the requested timeframe.
        
        Args:
            timeframe: Time window to analyze.
            tokens: List of tokens to analyze. If None, analyzes all default tokens.
            
        Returns:
            Dict with analysis results including opportunities and risks
        """
        previous_hours = self.hours
        self.hours = self._parse_timeframe(timeframe)

        try:
            if tokens is None:
                tokens = self.tokens
            
            results = {
                'timestamp': int(datetime.now().timestamp()),
                'analysis_period': timeframe,
                'price_action': {},
                'volume_trend': {},
                'volatility': {},
                'opportunities': [],
                'risks': []
            }
            
            for token in tokens:
                token_upper = token.upper()
                token_history = get_prices(token_upper, hours=self.hours)
                
                if not token_history:
                    continue
                
                # Sort by timestamp descending
                token_history.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Calculate price action metrics
                price_metrics = self._analyze_price_action(token_upper, token_history)
                if price_metrics:
                    results['price_action'][token_upper] = price_metrics
                
                # Calculate volume metrics
                volume_metrics = self._analyze_volume(token_upper, token_history)
                if volume_metrics:
                    results['volume_trend'][token_upper] = volume_metrics
                
                # Calculate volatility metrics
                volatility_metrics = self._analyze_volatility(token_upper, token_history)
                if volatility_metrics:
                    results['volatility'][token_upper] = volatility_metrics
            
            # Analyze relationships between tokens
            results['opportunities'].extend(self._detect_opportunities(results))
            results['risks'].extend(self._detect_risks(results))
            
            return results
        finally:
            self.hours = previous_hours

    def analyze_24h(self, tokens: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze 24-hour market fundamentals."""
        return self.analyze('24h', tokens)

    def _analyze_price_action(self, token: str, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze price action for a token."""
        if len(history) < 2:
            return None
        
        # Current price
        current_price = history[0]['price']
        
        # Find price from 24h ago
        current_ts = history[0]['timestamp']
        start_ts = current_ts - (self.hours * 3600)
        
        start_price = None
        for price in history:
            if price['timestamp'] <= start_ts:
                start_price = price['price']
                break
        
        if start_price is None:
            start_price = history[-1]['price']
        
        # Calculate metrics
        price_change_pct = ((current_price - start_price) / start_price) * 100
        
        # Price range
        prices = [p['price'] for p in history]
        price_high = max(prices)
        price_low = min(prices)
        
        return {
            'current_price': round(current_price, 2),
            'open_24h': round(start_price, 2),
            'high_24h': round(price_high, 2),
            'low_24h': round(price_low, 2),
            'price_change_pct': round(price_change_pct, 2),
            'price_trend': 'bullish' if price_change_pct > 0 else 'bearish' if price_change_pct < 0 else 'neutral'
        }
    
    def _analyze_volume(self, token: str, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze volume trends for a token."""
        # Get volume data
        volumes = [p['volume_24h'] for p in history if p.get('volume_24h')]
        
        if not volumes:
            return None
        
        # Current volume (latest)
        current_volume = volumes[0]
        avg_volume = sum(volumes) / len(volumes)
        
        # Calculate volume change vs 24h ago
        current_ts = history[0]['timestamp']
        start_ts = current_ts - (self.hours * 3600)
        
        start_volume = None
        for price in history:
            if price['timestamp'] <= start_ts:
                start_volume = price['volume_24h']
                break
        
        if start_volume is None:
            start_volume = volumes[-1] if len(volumes) > 1 else volumes[0]
        
        volume_change_pct = ((current_volume - start_volume) / start_volume) * 100 if start_volume else 0
        
        # Determine trend
        if volume_change_pct > self.VOLUME_CHANGE_THRESHOLD_HIGH:
            trend = 'strongly_increasing'
        elif volume_change_pct > self.VOLUME_CHANGE_THRESHOLD_LOW:
            trend = 'increasing'
        elif volume_change_pct < -self.VOLUME_CHANGE_THRESHOLD_HIGH:
            trend = 'strongly_decreasing'
        elif volume_change_pct < -self.VOLUME_CHANGE_THRESHOLD_LOW:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'current_volume': round(current_volume, 2),
            'average_24h': round(avg_volume, 2),
            'volume_change_pct': round(volume_change_pct, 2),
            'trend': trend
        }
    
    def _analyze_volatility(self, token: str, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze volatility for a token."""
        prices = [p['price'] for p in history]
        
        if len(prices) < 2:
            return None
        
        # Calculate returns
        returns = [(prices[i] - prices[i-1]) / prices[i-1] * 100 for i in range(1, len(prices))]
        
        if not returns:
            return None
        
        # Calculate standard deviation (historical volatility)
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance)
        
        # Current volatility (last 6 hours)
        recent_returns = returns[:6] if len(returns) >= 6 else returns
        if recent_returns:
            recent_mean = sum(recent_returns) / len(recent_returns)
            recent_variance = sum((r - recent_mean) ** 2 for r in recent_returns) / len(recent_returns)
            current_volatility = math.sqrt(recent_variance)
        else:
            current_volatility = volatility
        
        # Determine volatility level
        if volatility > self.VOLATILITY_THRESHOLD_HIGH:
            level = 'high'
        elif volatility > self.VOLATILITY_THRESHOLD_MODERATE:
            level = 'moderate'
        elif volatility > self.VOLATILITY_THRESHOLD_LOW:
            level = 'low'
        else:
            level = 'very_low'
        
        return {
            'historical_volatility': round(volatility, 2),
            'current_volatility': round(current_volatility, 2),
            'level': level
        }
    
    def _detect_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect trading opportunities based on analysis."""
        opportunities = []
        
        price_action = analysis.get('price_action', {})
        volume_trend = analysis.get('volume_trend', {})
        volatility = analysis.get('volatility', {})
        
        for token in price_action:
            token_analysis = price_action[token]
            token_volume = volume_trend.get(token, {})
            token_vol = volatility.get(token, {})
            
            # Bullish price momentum
            if token_analysis.get('price_change_pct', 0) > self.PRICE_CHANGE_BULLISH:
                opportunities.append({
                    'type': 'momentum_bullish',
                    'asset': token,
                    'description': f"{token} showing strong bullish momentum with {token_analysis['price_change_pct']:.1f}% rise",
                    'confidence': 'high' if token_analysis['price_change_pct'] > 10 else 'medium'
                })
            
            # Bullish volume divergence
            if token_volume.get('volume_change_pct', 0) > self.VOLUME_CHANGE_THRESHOLD_HIGH and token_analysis['price_change_pct'] > 0:
                opportunities.append({
                    'type': 'bullish_volume_divergence',
                    'asset': token,
                    'description': f"{token} price increasing on significantly higher volume ({token_volume['volume_change_pct']:.1f}%)",
                    'confidence': 'medium'
                })
            
            # Low volatility breakouts
            if token_vol.get('level') == 'very_low' and len(analysis.get('risks', [])) == 0:
                opportunities.append({
                    'type': 'low_volatility_setup',
                    'asset': token,
                    'description': f"{token} in low volatility state, potential breakout opportunity",
                    'confidence': 'low'
                })
        
        return opportunities
    
    def _detect_risks(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect market risks based on analysis."""
        risks = []
        
        price_action = analysis.get('price_action', {})
        volume_trend = analysis.get('volume_trend', {})
        volatility = analysis.get('volatility', {})
        
        for token in price_action:
            token_analysis = price_action[token]
            token_volume = volume_trend.get(token, {})
            token_vol = volatility.get(token, {})
            
            # Bearish price momentum
            if token_analysis.get('price_change_pct', 0) < self.PRICE_CHANGE_BEARISH:
                risks.append({
                    'type': 'momentum_bearish',
                    'asset': token,
                    'description': f"{token} showing strong bearish momentum with {token_analysis['price_change_pct']:.1f}% drop",
                    'severity': 'high' if token_analysis['price_change_pct'] < -10 else 'medium'
                })
            
            # Volume divergence with price decline
            if token_volume.get('volume_change_pct', 0) < -self.VOLUME_CHANGE_THRESHOLD_HIGH and token_analysis['price_change_pct'] < 0:
                risks.append({
                    'type': 'bearish_volume_divergence',
                    'asset': token,
                    'description': f"{token} price declining on significantly higher volume ({token_volume['volume_change_pct']:.1f}%)",
                    'severity': 'medium'
                })
            
            # High volatility
            if token_vol.get('level') == 'high':
                risks.append({
                    'type': 'high_volatility',
                    'asset': token,
                    'description': f"{token} experiencing high volatility ({token_vol['historical_volatility']:.1f}%)",
                    'severity': 'medium'
                })
        
        return risks
    
    def get_asset_score(self, token: str) -> Dict[str, Any]:
        """Calculate a composite score for an asset."""
        history = get_prices(token.upper(), hours=24)
        
        if not history:
            return {'error': 'No data available'}
        
        analysis = self._analyze_price_action(token.upper(), history)
        if not analysis:
            return {'error': 'Insufficient data'}
        
        # Base score on price change
        price_change = analysis['price_change_pct']
        
        # Adjust based on volatility
        vol_history = get_prices(token.upper(), hours=1)  # Recent history for volatility
        if vol_history:
            recent_prices = [p['price'] for p in vol_history]
            if len(recent_prices) > 1:
                returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] for i in range(1, len(recent_prices))]
                volatility = sum(abs(r) for r in returns) / len(returns) * 100 if returns else 0
                
                # Volatility penalty
                if volatility > 5:
                    volatility_penalty = -20
                elif volatility > 2:
                    volatility_penalty = -10
                else:
                    volatility_penalty = 0
            else:
                volatility_penalty = 0
        else:
            volatility_penalty = 0
        
        # Calculate score (0-100)
        base_score = 50 + (price_change * 2) + volatility_penalty
        score = max(0, min(100, base_score))
        
        # Determine rating
        if score >= 80:
            rating = 'strong_buy'
            color = 'green'
        elif score >= 60:
            rating = 'buy'
            color = 'light_green'
        elif score >= 40:
            rating = 'hold'
            color = 'yellow'
        elif score >= 20:
            rating = 'sell'
            color = 'orange'
        else:
            rating = 'strong_sell'
            color = 'red'
        
        return {
            'score': round(score, 1),
            'rating': rating,
            'color': color,
            'details': {
                'price_change_24h': analysis['price_change_pct'],
                'current_price': analysis['current_price'],
                'est_volatility': volatility if 'volatility' in locals() else None
            }
        }


def analyze_24h(tokens: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convenience function to run 24h analysis."""
    analyzer = FundamentalAnalyzer()
    return analyzer.analyze_24h(tokens)


def get_asset_score(token: str) -> Dict[str, Any]:
    """Convenience function to get asset score."""
    analyzer = FundamentalAnalyzer()
    return analyzer.get_asset_score(token)


if __name__ == '__main__':
    # Example usage
    import sys

    timeframe = sys.argv[1] if len(sys.argv) > 1 else '24h'
    tokens = sys.argv[2:] if len(sys.argv) > 2 else None

    analyzer = FundamentalAnalyzer()
    
    # Run full analysis
    results = analyzer.analyze(timeframe, tokens)
    print(json.dumps(results, indent=2))
    
    # Get scores for tokens
    print("\nAsset Scores:")
    for token in ['BTC', 'ETH', 'LINK']:
        score = analyzer.get_asset_score(token)
        print(f"\n{token}: {score}")
