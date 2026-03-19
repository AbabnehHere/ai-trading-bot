"""Multi-source price verification for commodity and crypto markets.

Never trust a single price source. This module cross-references
multiple APIs and news to get reliable current prices.
"""

import re
from typing import Any

import feedparser  # type: ignore[import-untyped]
import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Keywords that indicate a market references an asset price
PRICE_PATTERNS: dict[str, dict[str, str]] = {
    "crude oil": {
        "yahoo_symbol": "CL=F",
        "news_query": "crude+oil+price+barrel+today",
        "unit": "per barrel",
    },
    "brent": {
        "yahoo_symbol": "BZ=F",
        "news_query": "brent+crude+oil+price+today",
        "unit": "per barrel",
    },
    "gold": {
        "yahoo_symbol": "GC=F",
        "news_query": "gold+price+ounce+today",
        "unit": "per ounce",
    },
    "natural gas": {
        "yahoo_symbol": "NG=F",
        "news_query": "natural+gas+price+today",
        "unit": "per MMBtu",
    },
    "bitcoin": {
        "coingecko_id": "bitcoin",
        "news_query": "bitcoin+price+today",
        "unit": "USD",
    },
    "ethereum": {
        "coingecko_id": "ethereum",
        "news_query": "ethereum+price+today",
        "unit": "USD",
    },
    "s&p": {
        "yahoo_symbol": "^GSPC",
        "news_query": "S%26P+500+index+today",
        "unit": "points",
    },
}


class PriceChecker:
    """Cross-references multiple sources for reliable price data."""

    def __init__(self) -> None:
        self._http = httpx.Client(timeout=10.0)

    def detect_asset(self, question: str) -> str | None:
        """Detect if a market question references a priced asset."""
        q_lower = question.lower()
        for asset in PRICE_PATTERNS:
            if asset in q_lower:
                return asset
        return None

    def get_price(self, asset: str) -> dict[str, Any] | None:
        """Get cross-referenced price from multiple sources.

        Returns:
            Dict with price, sources used, and confidence.
        """
        config = PRICE_PATTERNS.get(asset)
        if not config:
            return None

        prices: list[dict[str, Any]] = []

        # Source 1: Yahoo Finance API
        if "yahoo_symbol" in config:
            yf_price = self._yahoo_price(config["yahoo_symbol"])
            if yf_price:
                prices.append({"source": "yahoo_finance", "price": yf_price})

        # Source 2: CoinGecko (for crypto)
        if "coingecko_id" in config:
            cg_price = self._coingecko_price(config["coingecko_id"])
            if cg_price:
                prices.append({"source": "coingecko", "price": cg_price})

        # Source 3: News headlines (extract price mentions)
        news_price = self._news_price(config["news_query"])
        if news_price:
            prices.append({"source": "news_headlines", "price": news_price})

        if not prices:
            return None

        # Cross-reference: if news price differs >10% from API, flag it
        api_prices = [p["price"] for p in prices if p["source"] != "news_headlines"]
        news_prices = [p["price"] for p in prices if p["source"] == "news_headlines"]

        best_price = prices[0]["price"]
        warning = ""

        if api_prices and news_prices:
            api_avg = sum(api_prices) / len(api_prices)
            news_avg = sum(news_prices) / len(news_prices)
            diff_pct = abs(api_avg - news_avg) / api_avg
            if diff_pct > 0.10:
                warning = (
                    f"PRICE MISMATCH: API says ${api_avg:.2f} but "
                    f"news says ${news_avg:.2f} ({diff_pct:.0%} diff). "
                    f"Trust news — API may be stale."
                )
                best_price = news_avg  # Trust news over stale API
            else:
                best_price = api_avg

        return {
            "asset": asset,
            "price": best_price,
            "unit": config["unit"],
            "sources": prices,
            "warning": warning,
        }

    def _yahoo_price(self, symbol: str) -> float | None:
        """Fetch price from Yahoo Finance."""
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
        """Fetch price from CoinGecko."""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            resp = self._http.get(url, params={"ids": coin_id, "vs_currencies": "usd"})
            if resp.status_code != 200:
                return None
            data = resp.json()
            return float(data.get(coin_id, {}).get("usd", 0)) or None
        except Exception as e:
            logger.debug("CoinGecko price failed", coin=coin_id, error=str(e))
            return None

    def _news_price(self, query: str) -> float | None:
        """Extract price from news headlines.

        Only trusts prices from reputable financial sources.
        Skips Polymarket listings and prediction market sites.
        """
        try:
            url = f"https://news.google.com/rss/search?q={query}&hl=en"
            feed = feedparser.parse(url)

            skip_sources = ["polymarket", "trading odds", "predictions", "kalshi"]
            price_candidates: list[float] = []

            for entry in feed.entries[:15]:
                title = entry.get("title", "").lower()
                # Skip prediction market listings
                if any(s in title for s in skip_sources):
                    continue
                # Match patterns like $96.85, $110, $1,234
                matches = re.findall(
                    r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)",
                    entry.get("title", ""),
                )
                for match in matches:
                    price = float(match.replace(",", ""))
                    # Reasonable commodity/crypto range
                    if 20 < price < 200_000:
                        price_candidates.append(price)

            # Take median to filter outliers
            if price_candidates:
                price_candidates.sort()
                mid = len(price_candidates) // 2
                return price_candidates[mid]
            return None
        except Exception as e:
            logger.debug("News price extraction failed", error=str(e))
            return None

    def close(self) -> None:
        """Close HTTP client."""
        self._http.close()
