"""Compile "true odds" from independent external data sources.

Builds probability estimates WITHOUT using the market price as a starting point.
Aggregates signals from polling data, bookmaker odds, news analysis, and
base rates to form an independent view, then compares to market price to find edges.
"""

import os
from typing import Any

import httpx

from src.data.claude_code_analyzer import ClaudeCodeAnalyzer
from src.data.llm_analyzer import LLMAnalyzer
from src.data.news_feed import NewsFeed
from src.data.sentiment import SentimentAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Fee constants — Polymarket charges ~2% taker, 0% maker
TAKER_FEE_RATE = 0.02
MAKER_FEE_RATE = 0.0


class ProbabilitySource:
    """A single probability signal with its source metadata."""

    def __init__(
        self,
        source_name: str,
        probability: float,
        confidence: float,
        details: str = "",
    ) -> None:
        self.source_name = source_name
        self.probability = max(0.01, min(0.99, probability))
        self.confidence = max(0.0, min(1.0, confidence))
        self.details = details


class OddsCompiler:
    """Compiles true probability estimates from independent external sources.

    IMPORTANT: This compiler does NOT use the market price as a starting point.
    It builds independent estimates and only compares to market price at the end
    to calculate edge.
    """

    def __init__(self) -> None:
        """Initialize the odds compiler with data sources."""
        self._news_feed = NewsFeed()
        self._sentiment = SentimentAnalyzer()
        self._llm = LLMAnalyzer()
        self._claude_code = ClaudeCodeAnalyzer()
        self._http_client = httpx.Client(timeout=10.0)
        self._odds_api_key = os.getenv("ODDS_API_KEY", "")
        self._metaculus_disabled = False  # Circuit breaker for 403s

    def compile_probability(
        self,
        market_question: str,
        market_price: float,
        keywords: list[str],
        category: str = "",
    ) -> dict[str, Any]:
        """Compile an independent probability estimate for a market.

        Gathers signals from multiple independent sources, weights them,
        and produces a final estimate. Only compares to market_price at the
        end to calculate edge.

        Args:
            market_question: The market question text.
            market_price: Current Polymarket price (used ONLY for edge calc).
            keywords: Keywords related to the market.
            category: Market category (politics, sports, crypto, etc.).

        Returns:
            Dict with estimated probability, confidence, edge, and sources.
        """
        sources: list[ProbabilitySource] = []

        # Source 1: Bookmaker odds (for sports markets)
        if category in ("sports", "esports"):
            bookmaker_source = self._get_bookmaker_probability(keywords, market_question)
            if bookmaker_source:
                sources.append(bookmaker_source)

        # Source 2: Claude Code CLI (free — uses local Claude Code installation)
        claude_source = self._get_claude_code_probability(market_question, keywords, category)
        if claude_source:
            sources.append(claude_source)

        # Source 3: Claude API fallback (paid — only if Claude Code unavailable)
        if not claude_source:
            llm_source = self._get_llm_probability(market_question, keywords, category)
            if llm_source:
                sources.append(llm_source)

        # Source 4: News-based probability (keyword fallback if no LLM at all)
        if not claude_source and not llm_source:
            news_source = self._get_news_probability(keywords, market_question)
            if news_source:
                sources.append(news_source)

        # Source 4: Base rate / prior probability
        base_rate_source = self._get_base_rate(market_question, category)
        if base_rate_source:
            sources.append(base_rate_source)

        # Source 5: Cross-platform comparison (Metaculus, etc.)
        cross_platform_source = self._get_cross_platform_probability(keywords, market_question)
        if cross_platform_source:
            sources.append(cross_platform_source)

        # If we have no independent sources, we have no edge
        if not sources:
            return {
                "probability": market_price,
                "confidence": 0.0,
                "edge": 0.0,
                "edge_after_fees": 0.0,
                "sources": [],
                "has_independent_estimate": False,
            }

        # Weighted average of independent sources
        estimated_prob = self._weighted_average(sources)
        overall_confidence = self._aggregate_confidence(sources)

        # NOW compare to market price to find edge
        raw_edge = estimated_prob - market_price
        edge_after_fees = self._edge_after_fees(raw_edge, market_price, estimated_prob)

        source_dicts = [
            {
                "source": s.source_name,
                "probability": s.probability,
                "confidence": s.confidence,
                "details": s.details,
            }
            for s in sources
        ]

        return {
            "probability": estimated_prob,
            "confidence": overall_confidence,
            "edge": raw_edge,
            "edge_after_fees": edge_after_fees,
            "sources": source_dicts,
            "has_independent_estimate": True,
            "num_sources": len(sources),
        }

    def _get_bookmaker_probability(
        self, keywords: list[str], question: str
    ) -> ProbabilitySource | None:
        """Fetch probability from bookmaker odds via The Odds API.

        Bookmaker odds are one of the best independent probability sources
        because bookmakers have strong financial incentives to be accurate.
        """
        if not self._odds_api_key:
            return None

        try:
            # Search for matching sport event
            response = self._http_client.get(
                "https://api.the-odds-api.com/v4/sports",
                params={"apiKey": self._odds_api_key},
            )
            if response.status_code != 200:
                return None

            sports = response.json()
            # Find matching sport based on keywords
            matching_sport = None
            keyword_lower = [k.lower() for k in keywords]
            for sport in sports:
                title = sport.get("title", "").lower()
                if any(kw in title for kw in keyword_lower):
                    matching_sport = sport.get("key")
                    break

            if not matching_sport:
                return None

            # Fetch odds for that sport
            odds_response = self._http_client.get(
                f"https://api.the-odds-api.com/v4/sports/{matching_sport}/odds",
                params={
                    "apiKey": self._odds_api_key,
                    "regions": "us,eu",
                    "markets": "h2h",
                    "oddsFormat": "decimal",
                },
            )
            if odds_response.status_code != 200:
                return None

            events = odds_response.json()
            if not events:
                return None

            # Find matching event and extract implied probability
            for event in events:
                event_name = (
                    f"{event.get('home_team', '')} vs {event.get('away_team', '')}"
                ).lower()
                if any(kw in event_name for kw in keyword_lower):
                    # Average odds across bookmakers
                    probs = self._extract_bookmaker_probs(event)
                    if probs:
                        avg_prob = sum(probs) / len(probs)
                        return ProbabilitySource(
                            source_name="bookmaker_odds",
                            probability=avg_prob,
                            confidence=0.85,  # Bookmakers are highly reliable
                            details=(f"{len(probs)} bookmakers, avg implied prob={avg_prob:.3f}"),
                        )

        except Exception as e:
            logger.debug("Bookmaker odds lookup failed", error=str(e))

        return None

    def _extract_bookmaker_probs(self, event: dict[str, Any]) -> list[float]:
        """Extract implied probabilities from bookmaker odds."""
        probs = []
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    for outcome in outcomes:
                        decimal_odds = outcome.get("price", 0)
                        if decimal_odds > 1:
                            # Implied probability = 1 / decimal_odds
                            # Remove overround by normalizing
                            implied = 1.0 / decimal_odds
                            probs.append(implied)
                    break
        # Normalize to remove overround
        if probs:
            total = sum(probs)
            if total > 0:
                probs = [p / total for p in probs]
        return probs

    def _get_claude_code_probability(
        self, question: str, keywords: list[str], category: str
    ) -> ProbabilitySource | None:
        """Use Claude Code CLI (free) for probability estimation.

        Calls `claude -p` locally — no API key needed, uses existing
        Claude Code subscription.
        """
        if not self._claude_code.is_available:
            return None

        try:
            # Fetch news headlines to give Claude context
            news = self._news_feed.get_market_relevant_news(keywords, limit=5)
            headlines = [a.get("title", "") for a in (news or [])]

            result = self._claude_code.estimate_probability(
                market_question=question,
                market_price=0.5,  # Don't reveal market price
                news_headlines=headlines,
                category=category,
            )

            prob = result.get("probability")
            if prob is not None:
                return ProbabilitySource(
                    source_name="claude_code_cli",
                    probability=float(prob),
                    confidence=float(result.get("confidence", 0.5)),
                    details=f"Claude Code: {result.get('reasoning', '')[:80]}",
                )

        except Exception as e:
            logger.warning("Claude Code probability failed", error=str(e))

        return None

    def _get_llm_probability(
        self, question: str, keywords: list[str], category: str
    ) -> ProbabilitySource | None:
        """Use Claude to analyze news and estimate probability.

        This is the highest-quality signal — Claude reads actual news articles
        and reasons about their impact on the market question.
        """
        if not self._llm.is_available:
            return None

        try:
            # Fetch news for Claude to analyze
            news = self._news_feed.get_market_relevant_news(keywords, limit=10)
            articles = [
                {
                    "title": a.get("title", ""),
                    "summary": a.get("summary", ""),
                    "source": a.get("source", ""),
                }
                for a in (news or [])
            ]

            result = self._llm.estimate_probability(
                market_question=question,
                news_articles=articles,
                category=category,
            )

            prob = result.get("probability")
            if prob is not None:
                return ProbabilitySource(
                    source_name="claude_llm",
                    probability=float(prob),
                    confidence=float(result.get("confidence", 0.5)),
                    details=f"Claude: {result.get('reasoning', '')[:80]}",
                )

        except Exception as e:
            logger.warning("LLM probability source failed", error=str(e))

        return None

    def _get_news_probability(self, keywords: list[str], question: str) -> ProbabilitySource | None:
        """Build probability estimate from news analysis.

        Uses volume and direction of news as a signal, NOT as a
        market-price adjustment. More positive news = higher probability.
        """
        try:
            news = self._news_feed.get_market_relevant_news(keywords, limit=15)
            if not news or len(news) < 3:
                return None  # Need minimum news volume for confidence

            articles = [{"title": a["title"], "summary": a["summary"]} for a in news]
            sentiment = self._sentiment.analyze_news_batch(articles)

            # Convert sentiment (-1 to 1) to a probability signal (0.2 to 0.8)
            # This is a WEAK signal — sentiment alone can't determine probability
            # Centered at 0.5, scaled by sentiment strength
            news_prob = 0.5 + (sentiment * 0.3)  # Range: 0.2 to 0.8

            # Low confidence — news sentiment is noisy
            # More articles increase confidence slightly
            confidence = min(0.3, len(news) / 50.0)

            return ProbabilitySource(
                source_name="news_sentiment",
                probability=news_prob,
                confidence=confidence,
                details=(
                    f"{len(news)} articles, sentiment={sentiment:.2f}, implied_prob={news_prob:.3f}"
                ),
            )

        except Exception as e:
            logger.debug("News probability failed", error=str(e))
            return None

    def _get_base_rate(self, question: str, category: str) -> ProbabilitySource | None:
        """Estimate base rate probability from the question structure.

        Simple heuristic: most prediction market questions have a base rate
        near 50% unless the question structure implies otherwise.
        """
        question_lower = question.lower()

        # Questions with "will X happen" default to uncertain base rate
        # But some structures imply lower base rates
        if any(
            word in question_lower for word in ["first", "record", "highest ever", "unprecedented"]
        ):
            # Rare events — lower base rate
            return ProbabilitySource(
                source_name="base_rate",
                probability=0.25,
                confidence=0.15,
                details="Rare event indicator words detected",
            )

        if any(word in question_lower for word in ["reelected", "incumbent", "continue", "remain"]):
            # Status quo bias — slight lean toward continuation
            return ProbabilitySource(
                source_name="base_rate",
                probability=0.55,
                confidence=0.1,
                details="Status quo / incumbent bias",
            )

        # Default: uninformative prior
        return ProbabilitySource(
            source_name="base_rate",
            probability=0.5,
            confidence=0.05,  # Very low confidence — this is just a prior
            details="Default uninformative prior",
        )

    def _get_cross_platform_probability(
        self, keywords: list[str], question: str
    ) -> ProbabilitySource | None:
        """Check other prediction platforms for their probability estimates.

        Metaculus community predictions are well-calibrated and free.
        Disabled automatically if API returns 403.
        """
        if self._metaculus_disabled:
            return None

        try:
            response = self._http_client.get(
                "https://www.metaculus.com/api/questions/",
                params={
                    "search": " ".join(keywords[:3]),
                    "limit": 5,
                    "status": "open",
                },
                headers={"Accept": "application/json"},
            )
            if response.status_code == 403:
                logger.info("Metaculus returned 403 — disabling for this session")
                self._metaculus_disabled = True
                return None
            if response.status_code != 200:
                return None

            data = response.json()
            results = data.get("results", [])
            if not results:
                return None

            # Find best matching question
            for result in results:
                title = result.get("title", "").lower()
                # Simple keyword overlap check
                overlap = sum(1 for kw in keywords if kw.lower() in title)
                if overlap >= 2 or (overlap >= 1 and len(keywords) <= 2):
                    # Get community prediction
                    prediction = result.get("community_prediction", {})
                    if isinstance(prediction, dict):
                        prob = prediction.get("full", {}).get("q2")
                    else:
                        prob = prediction
                    if prob and isinstance(prob, (int, float)):
                        return ProbabilitySource(
                            source_name="metaculus",
                            probability=float(prob),
                            confidence=0.6,  # Metaculus is well-calibrated
                            details=f"Metaculus: '{result.get('title', '')[:50]}'",
                        )

        except Exception as e:
            logger.debug("Metaculus lookup failed", error=str(e))

        return None

    def _weighted_average(self, sources: list[ProbabilitySource]) -> float:
        """Compute confidence-weighted average probability."""
        total_weight = sum(s.confidence for s in sources)
        if total_weight <= 0:
            return 0.5

        weighted_sum = sum(s.probability * s.confidence for s in sources)
        result = weighted_sum / total_weight
        return max(0.01, min(0.99, result))

    def _aggregate_confidence(self, sources: list[ProbabilitySource]) -> float:
        """Aggregate confidence across sources.

        More independent sources = higher confidence (up to a cap).
        Agreement between sources also boosts confidence.
        """
        if not sources:
            return 0.0

        # Base: average confidence of sources
        avg_conf = sum(s.confidence for s in sources) / len(sources)

        # Bonus for multiple sources (diminishing returns)
        source_bonus = min(0.2, len(sources) * 0.05)

        # Bonus for agreement (low spread in estimates)
        probs = [s.probability for s in sources]
        if len(probs) > 1:
            spread = max(probs) - min(probs)
            agreement_bonus = max(0, 0.15 - spread * 0.5)
        else:
            agreement_bonus = 0.0

        return min(1.0, avg_conf + source_bonus + agreement_bonus)

    @staticmethod
    def _edge_after_fees(raw_edge: float, market_price: float, estimated_prob: float) -> float:
        """Calculate edge after accounting for trading fees.

        For a BUY trade: you pay market_price + taker fee, receive $1 if correct.
        EV = (estimated_prob * $1) - (market_price * (1 + taker_fee))
        Edge after fees = EV / cost

        Args:
            raw_edge: estimated_prob - market_price.
            market_price: Current market price.
            estimated_prob: Our estimated probability.

        Returns:
            Edge after fees. Only positive if trade is profitable after costs.
        """
        if raw_edge > 0:
            # Buying YES: cost = price + taker fee on entry
            entry_cost = market_price * (1 + TAKER_FEE_RATE)
            expected_payout = estimated_prob * 1.0  # $1 if correct
            edge_after = expected_payout - entry_cost
        elif raw_edge < 0:
            # Buying NO: cost = (1 - market_price) + taker fee
            no_price = 1.0 - market_price
            entry_cost = no_price * (1 + TAKER_FEE_RATE)
            no_prob = 1.0 - estimated_prob
            expected_payout = no_prob * 1.0
            edge_after = expected_payout - entry_cost
        else:
            edge_after = 0.0

        return edge_after

    def close(self) -> None:
        """Close the HTTP client."""
        self._http_client.close()
