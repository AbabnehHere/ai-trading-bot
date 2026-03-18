# TODO: Implement in Phase 4
"""Basic sentiment analysis on news and social media.

Provides sentiment scoring for text data related to market events.
"""


class SentimentAnalyzer:
    """Analyzes sentiment of text data related to markets."""

    def analyze_text(self, text: str) -> float:
        """Analyze sentiment of a text string.

        Args:
            text: The text to analyze.

        Returns:
            Sentiment score from -1 (very negative) to 1 (very positive).
        """
        raise NotImplementedError("Phase 4")

    def analyze_news_batch(self, articles: list[dict[str, str]]) -> float:
        """Analyze aggregate sentiment across multiple news articles.

        Args:
            articles: List of article dicts with 'title' and 'summary' keys.

        Returns:
            Aggregate sentiment score from -1 to 1.
        """
        raise NotImplementedError("Phase 4")
