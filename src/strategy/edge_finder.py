# TODO: Implement in Phase 4
"""Core strategy: find mispriced markets.

Compares Polymarket prices against independently compiled "true odds"
to find edges where the market is mispriced.
"""

from typing import Any

from src.strategy.base_strategy import BaseStrategy, TradeSignal


class EdgeFinder(BaseStrategy):
    """Finds markets where Polymarket price diverges from true probability."""

    def evaluate(self, market_data: dict[str, Any]) -> TradeSignal | None:
        """Evaluate a market for mispricing edge.

        Args:
            market_data: Full market context.

        Returns:
            TradeSignal if edge exceeds minimum threshold, None otherwise.
        """
        raise NotImplementedError("Phase 4")

    def get_name(self) -> str:
        """Return strategy name."""
        return "EdgeFinder"

    def calculate_edge(self, market_price: float, true_probability: float) -> float:
        """Calculate the edge (difference between true probability and market price).

        Args:
            market_price: Current Polymarket price.
            true_probability: Our estimated true probability.

        Returns:
            Edge as a decimal (positive = underpriced, negative = overpriced).
        """
        raise NotImplementedError("Phase 4")
