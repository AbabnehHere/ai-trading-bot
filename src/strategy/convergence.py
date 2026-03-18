"""Late-stage convergence trading.

Trades markets that are near resolution where the outcome is highly
predictable but the price hasn't fully converged to 0 or 1.
"""

from datetime import UTC, datetime
from typing import Any

from src.strategy.base_strategy import BaseStrategy, TradeSignal
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConvergenceStrategy(BaseStrategy):
    """Trades near-resolution markets where outcome is near-certain."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the convergence strategy.

        Args:
            config: Strategy configuration parameters.
        """
        cfg = config or {}
        self._enabled = cfg.get("enabled", True)
        self._min_probability = cfg.get("min_probability_for_entry", 0.95)
        self._max_days = cfg.get("max_days_to_resolution", 14)
        self._min_spread = cfg.get("min_spread_cents", 0.03)

    def evaluate(self, market_data: dict[str, Any]) -> TradeSignal | None:
        """Evaluate a market for convergence opportunity.

        Args:
            market_data: Full market context including:
                - market_id, question, tokens
                - end_date_iso: resolution date

        Returns:
            TradeSignal if convergence opportunity exists, None otherwise.
        """
        if not self._enabled:
            return None

        market_id = market_data.get("id", "")
        question = market_data.get("question", "")
        tokens = market_data.get("tokens", [])
        end_date_str = market_data.get("end_date_iso", "")

        # Check time to resolution
        if not end_date_str:
            return None

        try:
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            days_remaining = (end_date - datetime.now(UTC)).days
        except (ValueError, TypeError):
            return None

        if days_remaining < 0 or days_remaining > self._max_days:
            return None

        # Look for near-certain outcomes
        for token in tokens:
            token_id = token.get("token_id", "")
            outcome = token.get("outcome", "")
            market_price = float(token.get("price", 0))

            # Check if price indicates near-certainty but hasn't converged fully
            if market_price >= self._min_probability:
                # This outcome is near-certain
                spread = 1.0 - market_price  # Distance from $1.00
                if spread >= self._min_spread:
                    edge = spread * 0.5  # Conservative: assume we capture half the spread
                    reasoning = (
                        f"Convergence on '{question[:50]}': "
                        f"{outcome} at {market_price:.3f}, "
                        f"spread={spread:.3f}, days_remaining={days_remaining}"
                    )
                    logger.info(
                        "Convergence signal",
                        market_id=market_id,
                        price=market_price,
                        spread=spread,
                        days=days_remaining,
                    )

                    return TradeSignal(
                        market_id=market_id,
                        token_id=token_id,
                        side="BUY",
                        confidence=market_price,  # Price itself is the confidence
                        edge=edge,
                        suggested_size=0,
                        price=market_price,
                        reasoning=reasoning,
                        strategy_name=self.get_name(),
                    )

        return None

    def get_name(self) -> str:
        """Return strategy name."""
        return "Convergence"
