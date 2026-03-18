"""Collect and store historical market data for backtesting."""

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.data.market_data import MarketDataClient
from src.utils.helpers import now_iso
from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = "data/trades.db"
HISTORICAL_DIR = Path("data/historical")


class DataCollector:
    """Collects and stores historical market data."""

    def __init__(self, market_data: MarketDataClient | None = None) -> None:
        """Initialize the data collector.

        Args:
            market_data: Market data client. Creates one if not provided.
        """
        self._market_data = market_data or MarketDataClient()
        HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)

    def collect_market_data(self, market_id: str, days: int = 90) -> dict[str, Any]:
        """Collect historical data for a market and store it.

        Args:
            market_id: The market identifier.
            days: Number of days of history to collect.

        Returns:
            Summary of data collected.
        """
        try:
            market = self._market_data.get_market(market_id)
            history = self._market_data.get_market_history(market_id, days=days)

            data = {
                "market_id": market_id,
                "market": market,
                "history": history,
                "collected_at": now_iso(),
            }

            # Save to file
            filepath = HISTORICAL_DIR / f"{market_id[:20]}.json"
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            # Save market to database
            self._save_market_to_db(market)

            logger.info(
                "Market data collected",
                market_id=market_id,
                history_points=len(history) if isinstance(history, list) else 0,
            )

            return {
                "market_id": market_id,
                "question": market.get("question", ""),
                "history_points": len(history) if isinstance(history, list) else 0,
            }

        except Exception as e:
            logger.error("Data collection failed", market_id=market_id, error=str(e))
            return {"market_id": market_id, "error": str(e)}

    def collect_all_active_markets(self, limit: int = 50) -> dict[str, Any]:
        """Collect data for all currently active markets.

        Args:
            limit: Maximum number of markets to collect.

        Returns:
            Summary of data collected.
        """
        try:
            markets = self._market_data.get_markets(active_only=True, limit=limit)
        except Exception as e:
            logger.error("Failed to fetch market list", error=str(e))
            return {"error": str(e), "collected": 0}

        collected = 0
        errors = 0
        for market in markets:
            market_id = market.get("id", market.get("condition_id", ""))
            if not market_id:
                continue
            result = self.collect_market_data(market_id, days=30)
            if "error" in result:
                errors += 1
            else:
                collected += 1

        logger.info("Bulk collection complete", collected=collected, errors=errors)
        return {"collected": collected, "errors": errors, "total": len(markets)}

    def _save_market_to_db(self, market: dict[str, Any]) -> None:
        """Save market metadata to the database."""
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(
                """INSERT OR REPLACE INTO markets
                   (market_id, slug, question, category, end_date,
                    resolution, liquidity_score, last_updated)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    market.get("id", market.get("condition_id", "")),
                    market.get("slug", ""),
                    market.get("question", ""),
                    market.get("category", ""),
                    market.get("end_date_iso", ""),
                    market.get("resolution", ""),
                    float(market.get("liquidity", 0) or 0),
                    now_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()
