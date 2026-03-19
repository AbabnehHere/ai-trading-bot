"""Multi-source price verification for commodity and crypto markets.

Never trust a single price source. Cross-references multiple APIs.
Primary: Twelve Data (800 calls/day free). Fallback: Yahoo Finance, CoinGecko.
"""

import os
from typing import Any

import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)

PRICE_PATTERNS: dict[str, dict[str, str]] = {
    "crude oil": {
        "twelve_symbol": "CL",
        "yahoo_symbol": "CL=F",
        "unit": "per barrel",
    },
    "brent": {
        "twelve_symbol": "BZ",
        "yahoo_symbol": "BZ=F",
        "unit": "per barrel",
    },
    "gold": {
        "twelve_symbol": "XAU/USD",
        "yahoo_symbol": "GC=F",
        "unit": "per ounce",
    },
    "natural gas": {
        "twelve_symbol": "NG",
        "yahoo_symbol": "NG=F",
        "unit": "per MMBtu",
    },
    "bitcoin": {
        "coingecko_id": "bitcoin",
        "twelve_symbol": "BTC/USD",
        "unit": "USD",
    },
    "ethereum": {
        "coingecko_id": "ethereum",
        "twelve_symbol": "ETH/USD",
        "unit": "USD",
    },
    "s&p": {
        "twelve_symbol": "SPX",
        "yahoo_symbol": "^GSPC",
        "unit": "points",
    },
}


class PriceChecker:
    """Cross-references multiple sources for reliable price data."""

    def __init__(self) -> None:
        self._http = httpx.Client(timeout=10.0)
        self._twelve_key = os.getenv("TWELVE_DATA", "")

    def detect_asset(self, question: str) -> str | None:
        """Detect if a market question references a priced asset."""
        q_lower = question.lower()
        for asset in PRICE_PATTERNS:
            if asset in q_lower:
                return asset
        return None

    def get_price(self, asset: str) -> dict[str, Any] | None:
        """Get price from multiple sources. No caching — prices move fast."""
        config = PRICE_PATTERNS.get(asset)
        if not config:
            return None

        prices: list[dict[str, Any]] = []

        # Source 1: Twelve Data (primary — 800 calls/day free)
        if self._twelve_key and "twelve_symbol" in config:
            td_price = self._twelve_data_price(config["twelve_symbol"])
            if td_price:
                prices.append({"source": "twelve_data", "price": td_price})

        # Source 2: CoinGecko (for crypto — no key needed)
        if "coingecko_id" in config:
            cg_price = self._coingecko_price(config["coingecko_id"])
            if cg_price:
                prices.append({"source": "coingecko", "price": cg_price})

        # Source 3: Yahoo Finance (fallback — rate limited)
        if not prices and "yahoo_symbol" in config:
            yf_price = self._yahoo_price(config["yahoo_symbol"])
            if yf_price:
                prices.append({"source": "yahoo_finance", "price": yf_price})

        if not prices:
            return None

        # Use first available price (Twelve Data > CoinGecko > Yahoo)
        best_price = prices[0]["price"]

        # Cross-reference if multiple sources
        warning = ""
        if len(prices) >= 2:
            p1, p2 = prices[0]["price"], prices[1]["price"]
            diff_pct = abs(p1 - p2) / p1 if p1 > 0 else 0
            if diff_pct > 0.05:
                warning = (
                    f"CAUTION: {prices[0]['source']} says ${p1:.2f}, "
                    f"{prices[1]['source']} says ${p2:.2f} "
                    f"({diff_pct:.0%} diff). Verify manually."
                )

        return {
            "asset": asset,
            "price": best_price,
            "unit": config["unit"],
            "sources": prices,
            "warning": warning,
        }

    def _twelve_data_price(self, symbol: str) -> float | None:
        """Fetch price from Twelve Data (primary source)."""
        try:
            resp = self._http.get(
                "https://api.twelvedata.com/price",
                params={"symbol": symbol, "apikey": self._twelve_key},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            price = data.get("price")
            if price:
                return float(price)
            return None
        except Exception as e:
            logger.debug("Twelve Data failed", symbol=symbol, error=str(e))
            return None

    def _yahoo_price(self, symbol: str) -> float | None:
        """Fetch price from Yahoo Finance (fallback)."""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            resp = self._http.get(url, params={"interval": "1d", "range": "1d"})
            if resp.status_code != 200:
                return None
            data = resp.json()
            meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
            price = meta.get("regularMarketPrice")
            return float(price) if price else None
        except Exception as e:
            logger.debug("Yahoo price failed", symbol=symbol, error=str(e))
            return None

    def _coingecko_price(self, coin_id: str) -> float | None:
        """Fetch price from CoinGecko (crypto)."""
        try:
            resp = self._http.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd"},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            return float(data.get(coin_id, {}).get("usd", 0)) or None
        except Exception as e:
            logger.debug("CoinGecko failed", coin=coin_id, error=str(e))
            return None

    def close(self) -> None:
        """Close HTTP client."""
        self._http.close()
