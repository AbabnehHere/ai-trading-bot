"""Market reporter — writes scan results to files for Claude Code review.

Instead of using the Claude API for analysis, this module writes
structured reports that Claude Code can read and analyze on a schedule.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.data.market_data import MarketDataClient
from src.data.news_feed import NewsFeed
from src.utils.logger import get_logger

logger = get_logger(__name__)

REPORTS_DIR = Path("data/reports")


class MarketReporter:
    """Writes market data and bot activity to files for external review."""

    def __init__(self, market_data: MarketDataClient) -> None:
        """Initialize the market reporter."""
        self._market_data = market_data
        self._news_feed = NewsFeed()
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def write_market_scan(self, markets: list[dict[str, Any]]) -> None:
        """Write top market opportunities for Claude Code to review.

        Selects the most interesting markets based on volume, liquidity,
        and price positioning (not extreme).
        """
        opportunities = []

        for market in markets[:50]:  # Top 50 by volume
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

            # Skip extreme prices — no edge to find
            if yes_price < 0.05 or yes_price > 0.95:
                continue

            question = market.get("question", "")
            # Fetch news for non-sports markets
            news_headlines: list[str] = []
            is_sports = any(
                kw in question.lower()
                for kw in [
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
                ]
            )
            if not is_sports:
                keywords = [w for w in question.split() if len(w) > 3][:3]
                try:
                    news = self._news_feed.get_market_relevant_news(keywords, limit=5)
                    news_headlines = [a.get("title", "")[:80] for a in news]
                except Exception as e:
                    logger.debug("News fetch failed for report", error=str(e))

            opportunities.append(
                {
                    "id": market.get("id", ""),
                    "question": question,
                    "category": market.get("category", ""),
                    "yes_price": yes_price,
                    "no_price": no_price,
                    "volume_24h": float(market.get("volume24hr", 0) or 0),
                    "liquidity": float(market.get("liquidityNum", 0) or 0),
                    "end_date": market.get("endDateIso", ""),
                    "slug": market.get("slug", ""),
                    "recent_news": news_headlines,
                }
            )

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_markets_scanned": len(markets),
            "opportunities": opportunities[:30],
        }

        path = REPORTS_DIR / "market_scan.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info("Market scan report written", opportunities=len(opportunities))

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

    def write_daily_summary(
        self,
        metrics: dict[str, Any],
        trades_today: list[dict[str, Any]],
        positions: list[dict[str, Any]],
    ) -> None:
        """Write end-of-day summary for nightly Claude Code review."""
        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "performance": metrics,
            "trades_today": trades_today,
            "open_positions": positions,
            "needs_review": True,
        }

        path = REPORTS_DIR / "daily_summary.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info("Daily summary report written")

    def read_trade_signals(self) -> list[dict[str, Any]]:
        """Read trade signals written by Claude Code.

        Claude Code writes signals to data/reports/signals.json
        after analyzing the market scan. The bot picks them up
        and executes them.
        """
        path = REPORTS_DIR / "signals.json"
        if not path.exists():
            return []

        try:
            with open(path) as f:
                data = json.load(f)

            signals = data.get("signals", [])
            if signals:
                # Archive processed signals
                archive = REPORTS_DIR / "signals_processed.json"
                with open(archive, "w") as f:
                    json.dump(data, f, indent=2)
                # Clear the signals file
                path.write_text('{"signals": []}')
                logger.info("Trade signals picked up", count=len(signals))

            return signals  # type: ignore[no-any-return]

        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read trade signals", error=str(e))
            return []
