"""Initialize the SQLite database with schema."""

import sqlite3
import sys
from pathlib import Path


DB_PATH = Path("data/trades.db")


SCHEMA = """
-- Markets tracked by the bot
CREATE TABLE IF NOT EXISTS markets (
    market_id TEXT PRIMARY KEY,
    slug TEXT,
    question TEXT NOT NULL,
    category TEXT,
    end_date TEXT,
    resolution TEXT,
    liquidity_score REAL,
    last_updated TEXT
);

-- All trades executed (or simulated)
CREATE TABLE IF NOT EXISTS trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('YES', 'NO')),
    direction TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')),
    price REAL NOT NULL,
    size REAL NOT NULL,
    timestamp TEXT NOT NULL,
    fees REAL DEFAULT 0,
    order_type TEXT DEFAULT 'limit',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'partial', 'cancelled', 'failed')),
    fill_price REAL,
    strategy_used TEXT,
    reasoning TEXT,
    is_paper BOOLEAN DEFAULT 0,
    FOREIGN KEY (market_id) REFERENCES markets(market_id)
);

-- Current open positions
CREATE TABLE IF NOT EXISTS positions (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('YES', 'NO')),
    avg_entry_price REAL NOT NULL,
    current_size REAL NOT NULL,
    unrealized_pnl REAL DEFAULT 0,
    realized_pnl REAL DEFAULT 0,
    opened_at TEXT NOT NULL,
    last_updated TEXT,
    is_paper BOOLEAN DEFAULT 0,
    FOREIGN KEY (market_id) REFERENCES markets(market_id)
);

-- Lessons learned from trades
CREATE TABLE IF NOT EXISTS trade_lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER,
    what_happened TEXT NOT NULL,
    what_was_expected TEXT,
    what_went_wrong_or_right TEXT,
    lesson_learned TEXT NOT NULL,
    parameter_adjustment_made TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id)
);

-- Performance snapshots over time
CREATE TABLE IF NOT EXISTS performance_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    total_balance REAL NOT NULL,
    total_pnl REAL NOT NULL,
    win_rate REAL,
    avg_profit REAL,
    avg_loss REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    total_trades INTEGER,
    is_paper BOOLEAN DEFAULT 0
);

-- News events tracked
CREATE TABLE IF NOT EXISTS news_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    source TEXT,
    headline TEXT NOT NULL,
    summary TEXT,
    relevant_markets TEXT,
    sentiment_score REAL,
    impact_assessment TEXT
);

-- Strategy parameter history
CREATE TABLE IF NOT EXISTS strategy_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parameter_name TEXT NOT NULL,
    current_value TEXT NOT NULL,
    previous_value TEXT,
    changed_at TEXT NOT NULL,
    reason_for_change TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_trades_market ON trades(market_id);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy_used);
CREATE INDEX IF NOT EXISTS idx_positions_market ON positions(market_id);
CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_snapshots(timestamp);
CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news_events(timestamp);
"""


def main() -> None:
    """Create database tables for trades, positions, and performance tracking."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        print(f"Database initialized successfully at {DB_PATH}")

        # Verify tables were created
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables created: {', '.join(tables)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
