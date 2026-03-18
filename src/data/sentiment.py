"""Basic sentiment analysis on news and social media.

Provides keyword-based sentiment scoring for text data related to market events.
Uses a simple lexicon approach — no external ML models required.
"""

import re

# Positive and negative keyword lexicons
POSITIVE_WORDS = frozenset(
    [
        "approved",
        "confirmed",
        "passed",
        "won",
        "victory",
        "success",
        "agreement",
        "deal",
        "signed",
        "breakthrough",
        "surge",
        "gain",
        "rise",
        "increase",
        "positive",
        "strong",
        "support",
        "ahead",
        "leading",
        "likely",
        "expected",
        "certain",
        "confident",
        "optimistic",
        "rally",
        "boom",
        "record",
        "high",
        "upgrade",
        "bullish",
    ]
)

NEGATIVE_WORDS = frozenset(
    [
        "rejected",
        "denied",
        "failed",
        "lost",
        "defeat",
        "collapse",
        "crisis",
        "crash",
        "drop",
        "decline",
        "fall",
        "negative",
        "weak",
        "opposition",
        "behind",
        "trailing",
        "unlikely",
        "uncertain",
        "risk",
        "threat",
        "warning",
        "concern",
        "fear",
        "panic",
        "bearish",
        "downgrade",
        "scandal",
        "investigation",
        "recession",
        "inflation",
    ]
)

INTENSIFIERS = frozenset(
    ["very", "extremely", "highly", "significantly", "strongly", "sharply", "dramatically"]
)

NEGATORS = frozenset(["not", "no", "never", "neither", "nor", "hardly", "barely", "unlikely"])


class SentimentAnalyzer:
    """Analyzes sentiment of text data using keyword-based scoring."""

    def analyze_text(self, text: str) -> float:
        """Analyze sentiment of a text string.

        Args:
            text: The text to analyze.

        Returns:
            Sentiment score from -1 (very negative) to 1 (very positive).
        """
        if not text:
            return 0.0

        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return 0.0

        score = 0.0
        prev_word = ""

        for word in words:
            multiplier = 1.0
            if prev_word in INTENSIFIERS:
                multiplier = 1.5
            if prev_word in NEGATORS:
                multiplier = -1.0

            if word in POSITIVE_WORDS:
                score += 1.0 * multiplier
            elif word in NEGATIVE_WORDS:
                score -= 1.0 * multiplier

            prev_word = word

        # Normalize to -1 to 1 range
        max_possible = len(words) * 0.3  # Assume ~30% of words could be sentiment-bearing
        if max_possible == 0:
            return 0.0
        normalized = score / max(max_possible, abs(score) + 1)
        return max(-1.0, min(1.0, normalized))

    def analyze_news_batch(self, articles: list[dict[str, str]]) -> float:
        """Analyze aggregate sentiment across multiple news articles.

        Args:
            articles: List of article dicts with 'title' and 'summary' keys.

        Returns:
            Aggregate sentiment score from -1 to 1.
        """
        if not articles:
            return 0.0

        scores = []
        for article in articles:
            # Title carries more weight than summary
            title_score = self.analyze_text(article.get("title", ""))
            summary_score = self.analyze_text(article.get("summary", ""))
            combined = title_score * 0.6 + summary_score * 0.4
            scores.append(combined)

        return sum(scores) / len(scores)
