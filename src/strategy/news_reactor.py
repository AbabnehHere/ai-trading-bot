"""News-based trading signals.

Monitors news feeds and generates trading signals when significant
news events affect the probability of market outcomes.
"""

from datetime import UTC, datetime
from typing import Any

from src.data.news_feed import NewsFeed
from src.data.sentiment import SentimentAnalyzer
from src.strategy.base_strategy import BaseStrategy, TradeSignal
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NewsReactor(BaseStrategy):
    """Generates signals based on breaking news and events."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the news reactor strategy.

        Args:
            config: Strategy configuration parameters.
        """
        cfg = config or {}
        self._enabled = cfg.get("enabled", True)
        self._min_sources = cfg.get("min_sources_to_confirm", 2)
        self._max_response_minutes = cfg.get("max_response_time_minutes", 15)
        self._edge_threshold = cfg.get("news_edge_threshold", 0.10)
        self._news_feed = NewsFeed()
        self._sentiment = SentimentAnalyzer()

    def evaluate(self, market_data: dict[str, Any]) -> TradeSignal | None:
        """Evaluate news impact on a market.

        Args:
            market_data: Full market context including:
                - market_id, question, tokens
                - keywords: list of relevant keywords

        Returns:
            TradeSignal if news significantly shifts probability, None otherwise.
        """
        if not self._enabled:
            return None

        market_id = market_data.get("id", "")
        question = market_data.get("question", "")
        tokens = market_data.get("tokens", [])
        keywords = market_data.get("keywords", [question])

        # Fetch recent news related to this market
        news = self._news_feed.get_market_relevant_news(keywords, limit=20)

        if not news:
            return None

        # Filter to recent news only
        now = datetime.now(UTC)
        recent_news = []
        for article in news:
            pub = article.get("published_at", "")
            try:
                pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                age_minutes = (now - pub_dt).total_seconds() / 60
                if age_minutes <= self._max_response_minutes:
                    recent_news.append(article)
            except (ValueError, TypeError):
                continue

        if len(recent_news) < self._min_sources:
            return None

        # Analyze sentiment of recent news
        articles_for_analysis = [
            {"title": a["title"], "summary": a["summary"]} for a in recent_news
        ]
        sentiment = self._sentiment.analyze_news_batch(articles_for_analysis)

        # Strong sentiment suggests probability shift
        if abs(sentiment) < 0.3:  # Weak sentiment — not actionable
            return None

        # Determine trade direction
        yes_token = next((t for t in tokens if t.get("outcome") == "Yes"), None)
        no_token = next((t for t in tokens if t.get("outcome") == "No"), None)

        if not yes_token:
            return None

        market_price = float(yes_token.get("price", 0.5))

        if sentiment > 0:
            # Positive news → probability should increase → buy YES
            estimated_shift = sentiment * 0.15  # Max 15% shift
            edge = estimated_shift
            if edge < self._edge_threshold:
                return None
            side = "BUY"
            token_id = yes_token.get("token_id", "")
            price = market_price
        else:
            # Negative news → probability should decrease → buy NO
            estimated_shift = abs(sentiment) * 0.15
            edge = estimated_shift
            if edge < self._edge_threshold:
                return None
            side = "BUY"
            if no_token:
                token_id = no_token.get("token_id", "")
                price = float(no_token.get("price", 1 - market_price))
            else:
                return None

        reasoning = (
            f"News reaction on '{question[:50]}': "
            f"{len(recent_news)} recent articles, sentiment={sentiment:.2f}, "
            f"estimated edge={edge:.3f}. "
            f"Headlines: {'; '.join(a['title'][:40] for a in recent_news[:3])}"
        )
        logger.info(
            "News signal",
            market_id=market_id,
            sentiment=sentiment,
            num_articles=len(recent_news),
        )

        return TradeSignal(
            market_id=market_id,
            token_id=token_id,
            side=side,
            confidence=min(abs(sentiment), 0.9),
            edge=edge,
            suggested_size=0,
            price=price,
            reasoning=reasoning,
            strategy_name=self.get_name(),
        )

    def get_name(self) -> str:
        """Return strategy name."""
        return "NewsReactor"
