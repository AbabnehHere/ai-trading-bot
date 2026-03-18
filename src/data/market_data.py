"""Polymarket API data fetching.

Handles all communication with the Polymarket CLOB API for market data,
orderbooks, and trade history using the py-clob-client SDK.
"""

import os
from typing import Any

import httpx
from py_clob_client.client import ClobClient  # type: ignore[import-untyped]

from src.utils.logger import get_logger

logger = get_logger(__name__)

POLYMARKET_API_BASE = "https://clob.polymarket.com"
GAMMA_API_BASE = "https://gamma-api.polymarket.com"


class MarketDataClient:
    """Client for fetching data from the Polymarket API."""

    def __init__(self) -> None:
        """Initialize the market data client."""
        self._api_key = os.getenv("POLYMARKET_API_KEY", "")
        self._secret = os.getenv("POLYMARKET_SECRET", "")
        self._passphrase = os.getenv("POLYMARKET_PASSPHRASE", "")
        self._private_key = os.getenv("PRIVATE_KEY", "")

        # Initialize CLOB client
        self._clob_client: ClobClient | None = None
        if self._private_key:
            try:
                self._clob_client = ClobClient(
                    POLYMARKET_API_BASE,
                    key=self._private_key,
                    chain_id=137,  # Polygon mainnet
                )
                if self._api_key:
                    self._clob_client.set_api_creds(
                        self._clob_client.create_or_derive_api_creds()  # type: ignore[no-untyped-call]
                    )
            except Exception as e:
                logger.warning("Failed to initialize CLOB client", error=str(e))

        self._http_client = httpx.Client(timeout=30.0)

    def get_markets(self, active_only: bool = True, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch markets from Polymarket via the Gamma API.

        Args:
            active_only: If True, only return active (open) markets.
            limit: Maximum number of markets to return.

        Returns:
            List of market data dicts.
        """
        params: dict[str, Any] = {"limit": limit}
        if active_only:
            params["active"] = True
            params["closed"] = False

        response = self._http_client.get(f"{GAMMA_API_BASE}/markets", params=params)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def get_market(self, market_id: str) -> dict[str, Any]:
        """Fetch a single market by condition ID.

        Args:
            market_id: The market condition ID.

        Returns:
            Market data dict.
        """
        response = self._http_client.get(f"{GAMMA_API_BASE}/markets/{market_id}")
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def get_orderbook(self, token_id: str) -> dict[str, Any]:
        """Fetch the current orderbook for a token.

        Args:
            token_id: The token identifier (YES or NO token).

        Returns:
            Orderbook with bids and asks.
        """
        if self._clob_client:
            try:
                book = self._clob_client.get_order_book(token_id)  # type: ignore[no-untyped-call]
                return {
                    "bids": [{"price": float(o.price), "size": float(o.size)} for o in book.bids],  # type: ignore[union-attr]
                    "asks": [{"price": float(o.price), "size": float(o.size)} for o in book.asks],  # type: ignore[union-attr]
                }
            except Exception as e:
                logger.warning("CLOB orderbook failed, using REST", error=str(e))

        response = self._http_client.get(
            f"{POLYMARKET_API_BASE}/book", params={"token_id": token_id}
        )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def get_midpoint(self, token_id: str) -> float:
        """Get the midpoint price for a token.

        Args:
            token_id: The token identifier.

        Returns:
            Midpoint price.
        """
        if self._clob_client:
            try:
                mid = self._clob_client.get_midpoint(token_id)  # type: ignore[no-untyped-call]
                return float(mid)
            except Exception as e:
                logger.debug("CLOB midpoint fallback to REST", error=str(e))

        response = self._http_client.get(
            f"{POLYMARKET_API_BASE}/midpoint", params={"token_id": token_id}
        )
        response.raise_for_status()
        data = response.json()
        return float(data.get("mid", 0))

    def get_market_history(self, market_id: str, days: int = 30) -> list[dict[str, Any]]:
        """Fetch price history for a market.

        Args:
            market_id: The market identifier (condition_id or slug).
            days: Number of days of history to fetch.

        Returns:
            List of historical price data points.
        """
        response = self._http_client.get(
            f"{GAMMA_API_BASE}/markets/{market_id}/history",
            params={"days": days},
        )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def close(self) -> None:
        """Close the HTTP client."""
        self._http_client.close()
