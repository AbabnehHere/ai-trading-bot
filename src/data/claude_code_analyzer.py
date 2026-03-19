"""Claude Code CLI integration — calls Claude Code for free LLM analysis.

Instead of paying for the Anthropic API, this module calls the locally
installed Claude Code CLI using `claude -p` for non-interactive analysis.
This uses your existing Claude Code subscription — no additional cost.
"""

import json
import subprocess
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeCodeAnalyzer:
    """Calls Claude Code CLI for market analysis — free, no API key needed."""

    def __init__(self, timeout: int = 120) -> None:
        """Initialize the Claude Code analyzer.

        Args:
            timeout: Max seconds to wait for Claude Code response.
        """
        self._timeout = timeout
        self._available: bool | None = None

    @property
    def is_available(self) -> bool:
        """Check if Claude Code CLI is installed and accessible."""
        if self._available is None:
            try:
                result = subprocess.run(
                    ["claude", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self._available = result.returncode == 0
                if self._available:
                    logger.info("Claude Code CLI available")
                else:
                    logger.warning("Claude Code CLI not available")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._available = False
                logger.warning("Claude Code CLI not found")
        return self._available

    def analyze(self, prompt: str) -> str | None:
        """Send a prompt to Claude Code and get the response.

        Args:
            prompt: The analysis prompt.

        Returns:
            Claude's response text, or None if failed.
        """
        if not self.is_available:
            return None

        try:
            result = subprocess.run(
                [
                    "claude",
                    "-p",
                    prompt,
                    "--output-format",
                    "json",
                    "--max-turns",
                    "1",
                ],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )

            if result.returncode != 0:
                logger.warning(
                    "Claude Code returned non-zero",
                    code=result.returncode,
                    stderr=result.stderr[:200],
                )
                return None

            # Parse JSON response
            try:
                data = json.loads(result.stdout)
                return str(data.get("result", result.stdout))
            except json.JSONDecodeError:
                return result.stdout.strip()

        except subprocess.TimeoutExpired:
            logger.warning("Claude Code timed out", timeout=self._timeout)
            return None
        except Exception as e:
            logger.warning("Claude Code call failed", error=str(e))
            return None

    def estimate_probability(
        self,
        market_question: str,
        market_price: float,
        news_headlines: list[str],
        category: str = "",
    ) -> dict[str, Any]:
        """Ask Claude Code to estimate probability for a market.

        Args:
            market_question: The prediction market question.
            market_price: Current market price (for edge calculation only).
            news_headlines: Recent relevant news headlines.
            category: Market category.

        Returns:
            Dict with probability, confidence, reasoning.
        """
        news_text = "\n".join(f"- {h}" for h in news_headlines[:8])

        prompt = (
            f"You are a probability analyst. Estimate the TRUE probability "
            f"of this prediction market question. DO NOT use the market price "
            f"as your starting point — form an independent estimate.\n\n"
            f"QUESTION: {market_question}\n"
            f"CATEGORY: {category or 'general'}\n\n"
            f"RECENT NEWS:\n{news_text or 'No recent news.'}\n\n"
            f"Respond with ONLY a JSON object, no other text:\n"
            f'{{"probability": 0.XX, "confidence": 0.XX, '
            f'"reasoning": "one sentence"}}'
        )

        response = self.analyze(prompt)
        if not response:
            return {
                "probability": None,
                "confidence": 0.0,
                "reasoning": "Claude Code unavailable",
            }

        parsed = self._parse_json(response)
        if parsed and "probability" in parsed:
            prob = float(parsed["probability"])
            conf = float(parsed.get("confidence", 0.3))
            return {
                "probability": max(0.01, min(0.99, prob)),
                "confidence": max(0.0, min(1.0, conf)),
                "reasoning": parsed.get("reasoning", ""),
            }

        return {
            "probability": None,
            "confidence": 0.0,
            "reasoning": f"Failed to parse: {response[:100]}",
        }

    def review_trade(self, trade_info: str, market_context: str) -> dict[str, Any]:
        """Ask Claude Code to review a completed trade.

        Args:
            trade_info: Trade details as text.
            market_context: What happened in the market.

        Returns:
            Dict with lesson and category.
        """
        prompt = (
            f"Review this prediction market trade and categorize it:\n\n"
            f"TRADE: {trade_info}\n"
            f"CONTEXT: {market_context}\n\n"
            f"Respond with ONLY JSON:\n"
            f'{{"category": "good_trade_good_outcome|good_trade_bad_outcome|'
            f'bad_trade_good_outcome|bad_trade_bad_outcome", '
            f'"lesson": "one sentence lesson"}}'
        )
        response = self.analyze(prompt)
        if response:
            parsed = self._parse_json(response)
            if parsed:
                return dict(parsed)
        return {"category": "unknown", "lesson": "Review unavailable"}

    def _parse_json(self, text: str) -> dict[str, Any] | None:
        """Parse JSON from response, handling markdown fences."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])
            if text.endswith("```"):
                text = text[:-3].strip()

        try:
            return dict(json.loads(text))
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return dict(json.loads(text[start:end]))
                except json.JSONDecodeError:
                    pass
        return None
