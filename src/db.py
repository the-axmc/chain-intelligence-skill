#!/usr/bin/env python3
"""
Database module for Chain Intelligence.
Handles SQLite storage and retrieval of market metrics.
"""

import os
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path


def get_db_path() -> str:
    """Get the database path from environment or use default."""
    env_path = os.environ.get('DATABASE_PATH')
    if env_path:
        return os.path.expanduser(env_path)
    default_path = '~/.openclaw/workspace-scout/signals/chain-intel/metrics.db'
    return os.path.expanduser(default_path)


def get_connection() -> sqlite3.Connection:
    """Get a database connection with Row factory."""
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Prices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_symbol TEXT NOT NULL,
            token_address TEXT,
            price REAL NOT NULL,
            volume_24h REAL,
            market_cap REAL,
            timestamp INTEGER NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    ''')
    
    # Gas table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gas_price_gwei REAL NOT NULL,
            block_time_ms INTEGER,
            timestamp INTEGER NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    ''')
    
    # Metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp INTEGER NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    ''')
    
    # Spreads table - stores cross-exchange price spreads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spreads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_symbol TEXT NOT NULL,
            min_price REAL NOT NULL,
            max_price REAL NOT NULL,
            avg_price REAL NOT NULL,
            spread REAL NOT NULL,
            spread_pct REAL NOT NULL,
            best_exchange TEXT NOT NULL,
            worst_exchange TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    ''')
    
    # Aave rates table - stores lending protocol rates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aave_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_symbol TEXT NOT NULL,
            supply_rate REAL NOT NULL,
            borrow_rate REAL NOT NULL,
            utilization_rate REAL NOT NULL,
            source TEXT,
            timestamp INTEGER NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_token ON prices(token_symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON prices(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gas_timestamp ON gas(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_token ON metrics(token_symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_spreads_token ON spreads(token_symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_spreads_timestamp ON spreads(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_aave_rates_token ON aave_rates(token_symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_aave_rates_timestamp ON aave_rates(timestamp)')
    
    conn.commit()
    conn.close()


def insert_price(token_symbol: str, token_address: Optional[str], 
                 price: float, volume_24h: Optional[float] = None,
                 market_cap: Optional[float] = None, 
                 timestamp: Optional[int] = None) -> int:
    """Insert a price record."""
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO prices (token_symbol, token_address, price, volume_24h, market_cap, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (token_symbol.upper(), token_address, price, volume_24h, market_cap, timestamp))
    
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return last_id


def insert_gas(gas_price_gwei: float, block_time_ms: Optional[int] = None,
               timestamp: Optional[int] = None) -> int:
    """Insert gas data record."""
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO gas (gas_price_gwei, block_time_ms, timestamp)
        VALUES (?, ?, ?)
    ''', (gas_price_gwei, block_time_ms, timestamp))
    
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return last_id


def insert_metric(token_symbol: str, name: str, value: float,
                  timestamp: Optional[int] = None) -> int:
    """Insert a generic metric record."""
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO metrics (token_symbol, name, value, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (token_symbol.upper(), name, value, timestamp))
    
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return last_id


def insert_spread(token_symbol: str,
                  min_price: float,
                  max_price: float,
                  avg_price: float,
                  spread: float,
                  spread_pct: float,
                  best_exchange: str,
                  worst_exchange: str,
                  timestamp: Optional[int] = None) -> int:
    """Insert a spread record."""
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO spreads (token_symbol, min_price, max_price, avg_price, spread, spread_pct, best_exchange, worst_exchange, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (token_symbol.upper(), min_price, max_price, avg_price, spread, spread_pct, best_exchange, worst_exchange, timestamp))
    
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return last_id


def insert_aave_rate(token_symbol: str,
                     supply_rate: float,
                     borrow_rate: float,
                     utilization_rate: float,
                     source: Optional[str] = None,
                     timestamp: Optional[int] = None) -> int:
    """Insert an Aave rate record."""
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO aave_rates (token_symbol, supply_rate, borrow_rate, utilization_rate, source, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (token_symbol.upper(), supply_rate, borrow_rate, utilization_rate, source, timestamp))
    
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return last_id


def get_prices(token_symbol: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Get price history for a token."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_time = int(datetime.now().timestamp()) - (hours * 3600)
    
    cursor.execute('''
        SELECT token_symbol, price, volume_24h, market_cap, timestamp
        FROM prices
        WHERE token_symbol = ? AND timestamp >= ?
        ORDER BY timestamp DESC
    ''', (token_symbol.upper(), cutoff_time))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'token_symbol': row['token_symbol'],
            'price': row['price'],
            'volume_24h': row['volume_24h'],
            'market_cap': row['market_cap'],
            'timestamp': row['timestamp']
        }
        for row in rows
    ]


def get_latest_prices(token_symbols: List[str]) -> List[Dict[str, Any]]:
    """Get the most recent price for each token."""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholders = ','.join('?' * len(token_symbols))
    cursor.execute(f'''
        SELECT p1.*
        FROM prices p1
        WHERE p1.timestamp = (
            SELECT MAX(p2.timestamp)
            FROM prices p2
            WHERE p2.token_symbol IN ({placeholders})
        )
        AND p1.token_symbol IN ({placeholders})
    ''', token_symbols + token_symbols)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'token_symbol': row['token_symbol'],
            'price': row['price'],
            'volume_24h': row['volume_24h'],
            'market_cap': row['market_cap'],
            'timestamp': row['timestamp']
        }
        for row in rows
    ]


def get_gas_history(hours: int = 24) -> List[Dict[str, Any]]:
    """Get gas price history."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_time = int(datetime.now().timestamp()) - (hours * 3600)
    
    cursor.execute('''
        SELECT gas_price_gwei, block_time_ms, timestamp
        FROM gas
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
    ''', (cutoff_time,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'gas_price_gwei': row['gas_price_gwei'],
            'block_time_ms': row['block_time_ms'],
            'timestamp': row['timestamp']
        }
        for row in rows
    ]


def get_metrics(token_symbol: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Get metric history for a token."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_time = int(datetime.now().timestamp()) - (hours * 3600)
    
    cursor.execute('''
        SELECT name, value, timestamp
        FROM metrics
        WHERE token_symbol = ? AND timestamp >= ?
        ORDER BY timestamp DESC
    ''', (token_symbol.upper(), cutoff_time))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'name': row['name'],
            'value': row['value'],
            'timestamp': row['timestamp']
        }
        for row in rows
    ]


def get_spreads(token_symbol: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Get spread history for a token."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_time = int(datetime.now().timestamp()) - (hours * 3600)
    
    cursor.execute('''
        SELECT token_symbol, min_price, max_price, avg_price, spread, spread_pct, best_exchange, worst_exchange, timestamp
        FROM spreads
        WHERE token_symbol = ? AND timestamp >= ?
        ORDER BY timestamp DESC
    ''', (token_symbol.upper(), cutoff_time))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'token_symbol': row['token_symbol'],
            'min_price': row['min_price'],
            'max_price': row['max_price'],
            'avg_price': row['avg_price'],
            'spread': row['spread'],
            'spread_pct': row['spread_pct'],
            'best_exchange': row['best_exchange'],
            'worst_exchange': row['worst_exchange'],
            'timestamp': row['timestamp']
        }
        for row in rows
    ]


def get_aave_rates(token_symbol: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Get Aave rate history for a token."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_time = int(datetime.now().timestamp()) - (hours * 3600)
    
    cursor.execute('''
        SELECT token_symbol, supply_rate, borrow_rate, utilization_rate, source, timestamp
        FROM aave_rates
        WHERE token_symbol = ? AND timestamp >= ?
        ORDER BY timestamp DESC
    ''', (token_symbol.upper(), cutoff_time))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'token_symbol': row['token_symbol'],
            'supply_rate': row['supply_rate'],
            'borrow_rate': row['borrow_rate'],
            'utilization_rate': row['utilization_rate'],
            'source': row['source'],
            'timestamp': row['timestamp']
        }
        for row in rows
    ]


def get_all_tokens() -> List[str]:
    """Get list of all token symbols in database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT token_symbol FROM prices ORDER BY token_symbol')
    rows = cursor.fetchall()
    conn.close()
    
    return [row['token_symbol'] for row in rows]


def prune_old_data(days: int = 7):
    """Remove data older than specified days."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_time = int(datetime.now().timestamp()) - (days * 86400)
    
    cursor.execute('DELETE FROM prices WHERE timestamp < ?', (cutoff_time,))
    cursor.execute('DELETE FROM gas WHERE timestamp < ?', (cutoff_time,))
    cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_time,))
    cursor.execute('DELETE FROM spreads WHERE timestamp < ?', (cutoff_time,))
    cursor.execute('DELETE FROM aave_rates WHERE timestamp < ?', (cutoff_time,))
    
    conn.commit()
    conn.close()


if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    print(f"Database path: {get_db_path()}")
