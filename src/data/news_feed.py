"""News aggregation from multiple sources.

Aggregates news from RSS feeds and APIs to provide
context for trading decisions.
"""

from datetime import UTC, datetime
from typing import Any

import feedparser  # type: ignore[import-untyped]
import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Public RSS feeds for news monitoring
DEFAULT_RSS_FEEDS = {
    "reuters_world": "https://feeds.reuters.com/reuters/worldNews",
    "reuters_politics": "https://feeds.reuters.com/reuters/politicsNews",
    "ap_news": "https://rsshub.app/apnews/topics/apf-topnews",
    "bbc_world": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "google_news": "https://news.google.com/rss",
}


class NewsFeed:
    """Aggregates news from multiple RSS and API sources."""

    def __init__(self, extra_feeds: dict[str, str] | None = None) -> None:
        """Initialize the news feed aggregator.

        Args:
            extra_feeds: Additional RSS feed URLs to monitor.
        """
        self._feeds = {**DEFAULT_RSS_FEEDS}
        if extra_feeds:
            self._feeds.update(extra_feeds)
        self._http_client = httpx.Client(timeout=15.0)

    def get_latest_news(self, topic: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Fetch latest news articles from all configured sources.

        Args:
            topic: Optional topic/keyword to filter articles.
            limit: Maximum number of articles to return.

        Returns:
            List of news article dicts with title, summary, source, and timestamp.
        """
        all_articles: list[dict[str, Any]] = []

        for source_name, feed_url in self._feeds.items():
            try:
                articles = self._parse_rss_feed(feed_url, source_name)
                all_articles.extend(articles)
            except Exception as e:
                logger.warning("Failed to fetch RSS feed", source=source_name, error=str(e))

        # Filter by topic if provided
        if topic:
            topic_lower = topic.lower()
            all_articles = [
                a
                for a in all_articles
                if topic_lower in a.get("title", "").lower()
                or topic_lower in a.get("summary", "").lower()
            ]

        # Sort by timestamp (newest first) and limit
        all_articles.sort(key=lambda a: a.get("published_at", ""), reverse=True)
        return all_articles[:limit]

    def _parse_rss_feed(self, feed_url: str, source_name: str) -> list[dict[str, Any]]:
        """Parse an RSS feed and return normalized articles."""
        feed = feedparser.parse(feed_url)
        articles = []

        for entry in feed.entries[:20]:  # Max 20 per feed
            published = entry.get("published_parsed")
            if published:
                pub_dt = datetime(*published[:6]).replace(tzinfo=UTC)
                pub_iso = pub_dt.isoformat()
            else:
                pub_iso = datetime.now(UTC).isoformat()

            articles.append(
                {
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "source": source_name,
                    "published_at": pub_iso,
                }
            )

        return articles

    def get_market_relevant_news(
        self, keywords: list[str], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Fetch news relevant to specific keywords (related to a market).

        Args:
            keywords: Keywords to search for in news articles.
            limit: Maximum number of articles to return.

        Returns:
            List of relevant news articles.
        """
        all_articles = self.get_latest_news(limit=200)
        relevant = []

        for article in all_articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            if any(kw.lower() in text for kw in keywords):
                relevant.append(article)

        return relevant[:limit]

    def close(self) -> None:
        """Close the HTTP client."""
        self._http_client.close()
