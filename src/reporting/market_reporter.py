"""Market reporter — writes scan results to files for Claude Code review.

Fetches topic-specific news via Google News RSS for each non-sports market.
Cross-references prices from multiple sources.
"""

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import feedparser  # type: ignore[import-untyped]
import httpx

from src.data.market_data import MarketDataClient
from src.data.price_checker import PriceChecker
from src.utils.logger import get_logger

logger = get_logger(__name__)

REPORTS_DIR = Path("data/reports")

# Sports keywords — skip these markets entirely
SPORTS_KEYWORDS = frozenset(
    [
        " vs.",
        " vs ",
        "bulls",
        "tigers",
        "cardinals",
        "zips",
        "raiders",
        "billikens",
        "pride",
        "cavaliers",
        "lakers",
        "clippers",
        "bucks",
        "jazz",
        "heat",
        "pelicans",
        "knights",
        "hofstra",
        "saint louis",
        "counter-strike",
        "handicap",
        "parivision",
        "utah",
        "trojans",
        "crimson",
        "bulldogs",
        "hurricanes",
        "red raiders",
        "warriors",
        "nuggets",
        "magic",
        "spurs",
        "o/u ",
        "game handicap",
        "map handicap",
        "tweets",
        "tweet",
        "musk post",
    ]
)

# Slug prefixes for sports
SPORTS_SLUGS = frozenset(["cbb-", "nba-", "nhl-", "lol-", "cs2-"])


class MarketReporter:
    """Writes market data and bot activity to files for external review."""

    def __init__(self, market_data: MarketDataClient) -> None:
        """Initialize the market reporter."""
        self._market_data = market_data
        self._price_checker = PriceChecker()
        self._http_client = httpx.Client(timeout=10.0)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def _is_sports(self, question: str, slug: str) -> bool:
        """Check if a market is sports/esports/noise."""
        q_lower = question.lower()
        return any(kw in q_lower for kw in SPORTS_KEYWORDS) or any(
            slug.startswith(p) for p in SPORTS_SLUGS
        )

    def _fetch_google_news(self, query: str, max_items: int = 5) -> list[dict[str, str]]:
        """Fetch fresh news via Google News RSS topic search.

        Returns only headlines from the last 12 hours.
        """
        try:
            url = f"https://news.google.com/rss/search?q={query}&hl=en"
            feed = feedparser.parse(url)
            cutoff = datetime.now(UTC) - timedelta(hours=24)
            results = []

            for entry in feed.entries[:15]:
                # Parse publication date
                pub = entry.get("published_parsed")
                if pub:
                    pub_dt = datetime(*pub[:6]).replace(tzinfo=UTC)
                    if pub_dt < cutoff:
                        continue  # Skip stale news
                else:
                    continue  # Skip if no date

                title = entry.get("title", "")
                # Skip Polymarket listings and prediction market noise
                if any(
                    s in title.lower()
                    for s in ["trading odds", "polymarket", "predictions", "kalshi"]
                ):
                    continue
                # Strip source suffix (e.g., " - CNN")
                title = re.sub(r"\s*-\s*[A-Z][A-Za-z\s.]+$", "", title)
                # Get summary from description field
                summary = entry.get("summary", entry.get("description", ""))
                # Strip HTML tags
                summary = re.sub(r"<[^>]+>", "", summary)[:150]

                results.append(
                    {
                        "title": title[:100],
                        "summary": summary,
                        "published": pub_dt.strftime("%H:%M UTC"),
                    }
                )

                if len(results) >= max_items:
                    break

            return results

        except Exception as e:
            logger.debug("Google News fetch failed", query=query, error=str(e))
            return []

    def _extract_search_query(self, question: str) -> str:
        """Extract a good Google News search query from a market question."""
        # Remove common filler words
        q = question.lower()
        for word in [
            "will",
            "the",
            "by",
            "before",
            "after",
            "in",
            "a",
            "an",
            "be",
            "there",
            "from",
            "to",
            "of",
            "?",
            "2026",
            "2027",
        ]:
            q = q.replace(f" {word} ", " ")
        # Take the most meaningful words
        words = [w for w in q.split() if len(w) > 2][:5]
        return "+".join(words)

    def write_market_scan(self, markets: list[dict[str, Any]]) -> None:
        """Write top market opportunities with fresh topic-specific news."""
        opportunities: list[dict[str, Any]] = []
        non_sports_count = 0

        for market in markets[:80]:
            outcomes = market.get("outcomes", "[]")
            prices = market.get("outcomePrices", "[]")

            if isinstance(outcomes, str):
                try:
                    outcomes = json.loads(outcomes)
                    prices = json.loads(prices)
                except (ValueError, TypeError):
                    continue

            if not prices or len(prices) < 2:
                continue

            yes_price = float(prices[0]) if prices else 0
            no_price = float(prices[1]) if len(prices) > 1 else 0

            if yes_price < 0.05 or yes_price > 0.95:
                continue

            question = market.get("question", "")
            slug = market.get("slug", "")

            if self._is_sports(question, slug):
                continue

            non_sports_count += 1
            news_items: list[dict[str, str]] = []

            # Fetch Google News for top 15 non-sports markets
            if non_sports_count <= 15:
                query = self._extract_search_query(question)
                news_items = self._fetch_google_news(query, max_items=4)

            # Check for asset price data
            asset_price: dict[str, Any] | None = None
            detected_asset = self._price_checker.detect_asset(question)
            if detected_asset and non_sports_count <= 15:
                asset_price = self._price_checker.get_price(detected_asset)

            entry: dict[str, Any] = {
                "id": market.get("id", ""),
                "question": question,
                "category": market.get("category", ""),
                "yes_price": yes_price,
                "no_price": no_price,
                "volume_24h": float(market.get("volume24hr", 0) or 0),
                "liquidity": float(market.get("liquidityNum", 0) or 0),
                "end_date": market.get("endDateIso", ""),
                "slug": slug,
                "recent_news": [f"{n['title']} — {n.get('summary', '')}" for n in news_items],
                "news_times": [n["published"] for n in news_items],
            }
            if asset_price:
                entry["current_asset_price"] = asset_price["price"]
                entry["asset_unit"] = asset_price["unit"]
                entry["price_sources"] = [
                    f"{s['source']}: ${s['price']:.2f}" for s in asset_price["sources"]
                ]
                if asset_price.get("warning"):
                    entry["price_warning"] = asset_price["warning"]

            opportunities.append(entry)

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_markets_scanned": len(markets),
            "non_sports_found": non_sports_count,
            "opportunities": opportunities[:30],
        }

        path = REPORTS_DIR / "market_scan.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(
            "Market scan report written",
            non_sports=non_sports_count,
            total_opps=len(opportunities),
        )

    def write_trade_log(
        self, trades: list[dict[str, Any]], positions: list[dict[str, Any]]
    ) -> None:
        """Write current trades and positions for review."""
        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "open_positions": positions,
            "recent_trades": trades[:20],
        }
        path = REPORTS_DIR / "trade_log.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)

    def read_trade_signals(self) -> list[dict[str, Any]]:
        """Read trade signals written by Claude Code."""
        path = REPORTS_DIR / "signals.json"
        if not path.exists():
            return []

        try:
            with open(path) as f:
                data = json.load(f)

            signals = data.get("signals", [])
            if signals:
                archive = REPORTS_DIR / "signals_processed.json"
                with open(archive, "w") as f:
                    json.dump(data, f, indent=2)
                path.write_text('{"signals": []}')
                logger.info("Trade signals picked up", count=len(signals))

            return signals  # type: ignore[no-any-return]

        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read trade signals", error=str(e))
            return []
