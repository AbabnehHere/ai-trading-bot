"""Detailed logging of every trade and its context.

Records comprehensive information about each trade for later analysis
and strategy improvement.
"""

import sqlite3
from typing import Any

from src.utils.helpers import now_iso
from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = "data/trades.db"


class TradeJournal:
    """Records and retrieves detailed trade logs."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        """Initialize the trade journal.

        Args:
            db_path: Path to the SQLite database.
        """
        self._db_path = db_path

    def record_trade(self, trade_data: dict[str, Any]) -> int:
        """Record a completed trade with full context.

        Args:
            trade_data: Complete trade information including:
                - market_id, side, direction, price, size
                - strategy_used, reasoning
                - is_paper (bool)

        Returns:
            The trade_id of the recorded trade.
        """
        conn = sqlite3.connect(self._db_path)
        try:
            cursor = conn.execute(
                """INSERT INTO trades
                   (market_id, side, direction, price, size, timestamp, fees,
                    order_type, status, fill_price, strategy_used, reasoning, is_paper)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    trade_data.get("market_id", ""),
                    trade_data.get("side", "YES"),
                    trade_data.get("direction", "BUY"),
                    trade_data.get("price", 0),
                    trade_data.get("size", 0),
                    now_iso(),
                    trade_data.get("fees", 0),
                    trade_data.get("order_type", "limit"),
                    trade_data.get("status", "filled"),
                    trade_data.get("fill_price", trade_data.get("price", 0)),
                    trade_data.get("strategy_used", ""),
                    trade_data.get("reasoning", ""),
                    trade_data.get("is_paper", True),
                ),
            )
            conn.commit()
            trade_id = cursor.lastrowid or 0
            logger.info("Trade recorded", trade_id=trade_id, market_id=trade_data.get("market_id"))
            return trade_id
        finally:
            conn.close()

    def get_trade_history(
        self,
        limit: int = 100,
        strategy: str | None = None,
        paper_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Retrieve trade history with optional filtering.

        Args:
            limit: Maximum number of trades to return.
            strategy: Filter by strategy name if provided.
            paper_only: If True, only return paper trades.

        Returns:
            List of trade records.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            query = "SELECT * FROM trades WHERE 1=1"
            params: list[Any] = []

            if strategy:
                query += " AND strategy_used = ?"
                params.append(strategy)
            if paper_only:
                query += " AND is_paper = 1"

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_recent_trades(self, count: int = 20) -> list[dict[str, Any]]:
        """Get the N most recent trades.

        Args:
            count: Number of trades to return.

        Returns:
            List of recent trade records.
        """
        return self.get_trade_history(limit=count)

    def get_trades_by_market(self, market_id: str) -> list[dict[str, Any]]:
        """Get all trades for a specific market.

        Args:
            market_id: The market to query.

        Returns:
            List of trade records for the market.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                "SELECT * FROM trades WHERE market_id = ? ORDER BY timestamp DESC",
                (market_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
