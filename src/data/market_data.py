# TODO: Implement in Phase 3
"""Polymarket API data fetching.

Handles all communication with the Polymarket CLOB API for market data,
orderbooks, and trade history.
"""

from typing import Any


class MarketDataClient:
    """Client for fetching data from the Polymarket API."""

    def get_markets(self, active_only: bool = True) -> list[dict[str, Any]]:
        """Fetch all markets from Polymarket.

        Args:
            active_only: If True, only return active (open) markets.

        Returns:
            List of market data dicts.
        """
        raise NotImplementedError("Phase 3")

    def get_orderbook(self, market_id: str) -> dict[str, Any]:
        """Fetch the current orderbook for a market.

        Args:
            market_id: The market identifier.

        Returns:
            Orderbook with bids and asks.
        """
        raise NotImplementedError("Phase 3")

    def get_market_history(self, market_id: str, days: int = 30) -> list[dict[str, Any]]:
        """Fetch price history for a market.

        Args:
            market_id: The market identifier.
            days: Number of days of history to fetch.

        Returns:
            List of historical price data points.
        """
        raise NotImplementedError("Phase 3")
