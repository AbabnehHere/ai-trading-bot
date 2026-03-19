"""LLM-powered analysis using Claude API.

Provides intelligent news analysis, probability estimation,
trade review, and strategy improvement suggestions.
"""

import json
import os
from typing import Any

import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class LLMAnalyzer:
    """Claude-powered analysis for trading decisions."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        """Initialize the LLM analyzer.

        Args:
            model: Anthropic model ID to use.
        """
        self._api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._model = model
        self._http_client = httpx.Client(timeout=60.0)

        if not self._api_key:
            logger.warning(
                "ANTHROPIC_API_KEY not set — LLM analysis disabled. "
                "Bot will fall back to keyword-based analysis."
            )

    @property
    def is_available(self) -> bool:
        """Check if the LLM analyzer is configured and available."""
        return bool(self._api_key)

    def estimate_probability(
        self,
        market_question: str,
        news_articles: list[dict[str, str]],
        category: str = "",
    ) -> dict[str, Any]:
        """Ask Claude to estimate the probability of a market outcome.

        This is the core intelligence — Claude reads news and reasons
        about probability independently, without seeing the market price.

        Args:
            market_question: The prediction market question.
            news_articles: Recent news articles with 'title' and 'summary'.
            category: Market category for context.

        Returns:
            Dict with probability, confidence, reasoning.
        """
        if not self.is_available:
            return {"probability": None, "confidence": 0.0, "reasoning": "LLM unavailable"}

        # Format news for Claude
        news_text = ""
        for i, article in enumerate(news_articles[:10], 1):
            title = article.get("title", "")
            summary = article.get("summary", "")[:200]
            source = article.get("source", "unknown")
            news_text += f"{i}. [{source}] {title}\n   {summary}\n\n"

        prompt = f"""You are a probability analyst for prediction markets. Your job is to estimate the TRUE probability of an event occurring, based on available evidence.

MARKET QUESTION: "{market_question}"
CATEGORY: {category or "general"}

RECENT NEWS:
{news_text if news_text else "No recent news available."}

INSTRUCTIONS:
1. Analyze the question and available news carefully
2. Consider base rates — how often do events like this happen historically?
3. Consider the strength and reliability of the evidence
4. Account for uncertainty — don't be overconfident
5. If you have very little information, say so and give a probability near 50%

Respond in this exact JSON format (no other text):
{{"probability": 0.XX, "confidence": 0.XX, "reasoning": "your 1-2 sentence reasoning"}}

Where:
- probability: your estimate from 0.01 to 0.99
- confidence: how confident you are in your estimate (0.0 to 1.0). Use LOW confidence (0.1-0.3) when you have little information, MEDIUM (0.4-0.6) with some evidence, HIGH (0.7-0.9) only with strong evidence.
- reasoning: brief explanation"""

        try:
            result = self._call_claude(prompt, max_tokens=200)
            parsed = self._parse_json_response(result)
            if parsed and "probability" in parsed:
                prob = float(parsed["probability"])
                conf = float(parsed.get("confidence", 0.3))
                return {
                    "probability": max(0.01, min(0.99, prob)),
                    "confidence": max(0.0, min(1.0, conf)),
                    "reasoning": parsed.get("reasoning", ""),
                }
        except Exception as e:
            logger.warning("LLM probability estimation failed", error=str(e))

        return {"probability": None, "confidence": 0.0, "reasoning": "Analysis failed"}

    def analyze_news_impact(
        self,
        market_question: str,
        article_title: str,
        article_summary: str,
        current_market_price: float,
    ) -> dict[str, Any]:
        """Ask Claude to assess how a news article impacts a market.

        Args:
            market_question: The prediction market question.
            article_title: News article headline.
            article_summary: News article summary.
            current_market_price: Current market price (for context).

        Returns:
            Dict with impact assessment.
        """
        if not self.is_available:
            return {"impact": "unknown", "direction": 0, "magnitude": 0.0}

        prompt = f"""You are analyzing how a news article affects a prediction market.

MARKET: "{market_question}"
CURRENT MARKET PRICE: {current_market_price:.2f} (implied {current_market_price:.0%} probability)

NEWS ARTICLE:
Title: {article_title}
Summary: {article_summary[:300]}

How does this news affect the probability of the market question?

Respond in this exact JSON format (no other text):
{{"direction": X, "magnitude": 0.XX, "reasoning": "brief explanation"}}

Where:
- direction: 1 if this increases probability, -1 if decreases, 0 if neutral/irrelevant
- magnitude: estimated probability shift (0.0 to 0.30). Use small values (0.01-0.05) for minor news, larger (0.10-0.30) only for game-changing events.
- reasoning: brief explanation"""

        try:
            result = self._call_claude(prompt, max_tokens=150)
            parsed = self._parse_json_response(result)
            if parsed:
                return {
                    "direction": int(parsed.get("direction", 0)),
                    "magnitude": float(parsed.get("magnitude", 0.0)),
                    "reasoning": parsed.get("reasoning", ""),
                }
        except Exception as e:
            logger.warning("LLM news impact analysis failed", error=str(e))

        return {"direction": 0, "magnitude": 0.0, "reasoning": "Analysis failed"}

    def review_trade(
        self,
        trade_data: dict[str, Any],
        market_context: str,
    ) -> dict[str, Any]:
        """Ask Claude to review a completed trade and extract lessons.

        Args:
            trade_data: Trade details (entry/exit price, P&L, strategy, reasoning).
            market_context: What happened in the market.

        Returns:
            Dict with analysis, lesson, and suggested adjustments.
        """
        if not self.is_available:
            return {"lesson": "LLM unavailable", "category": "unknown"}

        prompt = f"""You are reviewing a completed prediction market trade to extract lessons.

TRADE DETAILS:
- Market: {trade_data.get("market_id", "unknown")}
- Strategy: {trade_data.get("strategy_used", "unknown")}
- Direction: {trade_data.get("direction", "BUY")}
- Entry price: {trade_data.get("price", 0):.3f}
- Exit/current price: {trade_data.get("fill_price", 0):.3f}
- Size: {trade_data.get("size", 0):.1f} shares
- P&L: ${trade_data.get("pnl", 0):.2f}
- Original reasoning: {trade_data.get("reasoning", "none")}

WHAT HAPPENED: {market_context}

Analyze this trade and respond in this exact JSON format (no other text):
{{"category": "X", "lesson": "one sentence lesson", "should_adjust": false, "adjustment": ""}}

Where category is one of:
- "good_trade_good_outcome": Edge was real, strategy worked
- "good_trade_bad_outcome": Edge was real but low-probability event occurred (normal variance)
- "bad_trade_good_outcome": Got lucky — reasoning was flawed
- "bad_trade_bad_outcome": Reasoning was wrong and lost money"""

        try:
            result = self._call_claude(prompt, max_tokens=200)
            parsed = self._parse_json_response(result)
            if parsed:
                return parsed
        except Exception as e:
            logger.warning("LLM trade review failed", error=str(e))

        return {"lesson": "Review failed", "category": "unknown"}

    def midnight_strategy_review(
        self,
        performance_metrics: dict[str, Any],
        recent_trades: list[dict[str, Any]],
        current_config: dict[str, Any],
        lessons: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Comprehensive strategy review — runs at midnight daily.

        Claude analyzes overall performance, recent trades, and lessons
        to suggest concrete parameter adjustments.

        Args:
            performance_metrics: Overall performance stats.
            recent_trades: Last 20-50 trades with details.
            current_config: Current strategy parameters.
            lessons: Recent lessons from trade reviews.

        Returns:
            Dict with analysis, suggestions, and whether to pause trading.
        """
        if not self.is_available:
            return {
                "analysis": "LLM unavailable",
                "suggestions": [],
                "should_pause": False,
            }

        # Summarize recent trades
        trades_summary = []
        for t in recent_trades[:30]:
            trades_summary.append(
                f"  {t.get('strategy_used', '?')}: "
                f"{t.get('direction', '?')} at {t.get('price', 0):.3f}, "
                f"P&L: ${t.get('pnl', 0):.2f}, "
                f"reason: {t.get('reasoning', 'none')[:60]}"
            )
        trades_text = "\n".join(trades_summary) if trades_summary else "No trades yet."

        # Summarize lessons
        lessons_text = (
            "\n".join(f"  - {lesson.get('lesson_learned', 'none')}" for lesson in lessons[:10])
            if lessons
            else "No lessons yet."
        )

        prompt = f"""You are the chief strategist for a conservative Polymarket trading bot. It is midnight and time for your daily strategy review.

PERFORMANCE METRICS:
- Total trades: {performance_metrics.get("total_trades", 0)}
- Win rate: {performance_metrics.get("win_rate", 0):.1%}
- Total P&L: ${performance_metrics.get("total_pnl", 0):.2f}
- Profit factor: {performance_metrics.get("profit_factor", 0):.2f}
- Max drawdown: {performance_metrics.get("max_drawdown", 0):.1%}
- Sharpe ratio: {performance_metrics.get("sharpe_ratio", 0):.2f}

CURRENT STRATEGY PARAMETERS:
- min_edge_threshold: {current_config.get("min_edge_threshold", 0.08)}
- confidence_required: {current_config.get("confidence_required", 0.7)}
- max_position_pct: {current_config.get("max_position_pct", 0.03)}
- kelly_fraction: {current_config.get("kelly_fraction", 0.25)}
- stop_loss_pct: {current_config.get("stop_loss_pct", 0.30)}

RECENT TRADES:
{trades_text}

LESSONS LEARNED:
{lessons_text}

Based on this data, provide your analysis and recommendations.

Respond in this exact JSON format (no other text):
{{
  "analysis": "2-3 sentence overall assessment",
  "should_pause": false,
  "pause_reason": "",
  "suggestions": [
    {{"parameter": "param_name", "current": 0.08, "suggested": 0.09, "reason": "why"}}
  ]
}}

RULES:
- Only suggest changes if there's clear evidence (10+ trades minimum)
- Never change more than 2 parameters at once
- Changes should be SMALL (10-20% adjustments, not dramatic)
- Set should_pause=true ONLY if drawdown > 8% or win rate < 40%
- If performance is good, suggest NO changes (empty suggestions array)"""

        try:
            result = self._call_claude(prompt, max_tokens=500)
            parsed = self._parse_json_response(result)
            if parsed:
                return {
                    "analysis": parsed.get("analysis", ""),
                    "should_pause": parsed.get("should_pause", False),
                    "pause_reason": parsed.get("pause_reason", ""),
                    "suggestions": parsed.get("suggestions", []),
                }
        except Exception as e:
            logger.error("Midnight strategy review failed", error=str(e))

        return {
            "analysis": "Review failed",
            "suggestions": [],
            "should_pause": False,
        }

    def _call_claude(self, prompt: str, max_tokens: int = 300) -> str:
        """Make a call to the Anthropic API.

        Args:
            prompt: The prompt to send.
            max_tokens: Maximum response tokens.

        Returns:
            Claude's text response.
        """
        response = self._http_client.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data.get("content", [])
        if content and isinstance(content, list):
            return str(content[0].get("text", ""))
        return ""

    def _parse_json_response(self, text: str) -> dict[str, Any] | None:
        """Parse JSON from Claude's response, handling markdown fences."""
        text = text.strip()
        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        try:
            return json.loads(text)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            # Try to find JSON in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])  # type: ignore[no-any-return]
                except json.JSONDecodeError:
                    pass
            logger.warning("Failed to parse LLM JSON response", text=text[:100])
            return None

    def close(self) -> None:
        """Close the HTTP client."""
        self._http_client.close()
