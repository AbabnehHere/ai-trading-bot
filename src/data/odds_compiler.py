"""Compile "true odds" from external data sources.

Aggregates probability estimates from multiple external sources
to build an independent probability estimate for comparison with
Polymarket prices.
"""

from typing import Any

from src.data.news_feed import NewsFeed
from src.data.sentiment import SentimentAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OddsCompiler:
    """Compiles true probability estimates from external sources."""

    def __init__(self) -> None:
        """Initialize the odds compiler with data sources."""
        self._news_feed = NewsFeed()
        self._sentiment = SentimentAnalyzer()

    def compile_probability(
        self, market_question: str, market_price: float, keywords: list[str]
    ) -> dict[str, Any]:
        """Compile a true probability estimate for a market.

        Uses multiple signals: news sentiment, market price momentum,
        and source consensus.

        Args:
            market_question: The market question text.
            market_price: Current Polymarket price (0-1).
            keywords: Keywords related to the market.

        Returns:
            Dict with estimated probability, confidence, and sources.
        """
        signals: list[dict[str, Any]] = []

        # Signal 1: News sentiment
        try:
            news = self._news_feed.get_market_relevant_news(keywords, limit=10)
            if news:
                articles = [{"title": a["title"], "summary": a["summary"]} for a in news]
                sentiment = self._sentiment.analyze_news_batch(articles)
                # Map sentiment (-1 to 1) to probability adjustment
                sentiment_adjustment = sentiment * 0.1  # Max ±10% adjustment
                signals.append(
                    {
                        "source": "news_sentiment",
                        "adjustment": sentiment_adjustment,
                        "confidence": min(len(news) / 5.0, 1.0),  # More articles = more confident
                        "details": f"{len(news)} articles, sentiment={sentiment:.2f}",
                    }
                )
        except Exception as e:
            logger.warning("News sentiment signal failed", error=str(e))

        # Signal 2: Market price as base (markets are generally efficient)
        signals.append(
            {
                "source": "market_price",
                "probability": market_price,
                "confidence": 0.7,  # Markets are a good baseline
                "details": f"Market price: {market_price:.3f}",
            }
        )

        # Combine signals
        if not signals:
            return {
                "probability": market_price,
                "confidence": 0.0,
                "edge": 0.0,
                "sources": [],
            }

        # Weighted average with market price as base
        total_adjustment = sum(
            s.get("adjustment", 0) * s.get("confidence", 0) for s in signals if "adjustment" in s
        )
        total_confidence = sum(s.get("confidence", 0) for s in signals if "adjustment" in s)

        avg_adjustment = total_adjustment / total_confidence if total_confidence > 0 else 0.0

        estimated_prob = max(0.01, min(0.99, market_price + avg_adjustment))
        edge = estimated_prob - market_price
        overall_confidence = min(sum(s.get("confidence", 0) for s in signals) / len(signals), 1.0)

        return {
            "probability": estimated_prob,
            "confidence": overall_confidence,
            "edge": edge,
            "sources": signals,
        }
