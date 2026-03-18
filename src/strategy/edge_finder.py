"""Core strategy: find mispriced markets.

Compares Polymarket prices against independently compiled "true odds"
to find edges where the market is mispriced.
"""

from typing import Any

from src.data.odds_compiler import OddsCompiler
from src.strategy.base_strategy import BaseStrategy, TradeSignal
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EdgeFinder(BaseStrategy):
    """Finds markets where Polymarket price diverges from true probability."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the edge finder strategy.

        Args:
            config: Strategy configuration parameters.
        """
        cfg = config or {}
        self._min_edge = cfg.get("min_edge_threshold", 0.08)
        self._confidence_required = cfg.get("confidence_required", 0.7)
        self._min_liquidity = cfg.get("min_liquidity_usd", 5000)
        self._min_time_to_resolution = cfg.get("min_time_to_resolution_hours", 24)
        self._odds_compiler = OddsCompiler()

    def evaluate(self, market_data: dict[str, Any]) -> TradeSignal | None:
        """Evaluate a market for mispricing edge.

        Args:
            market_data: Full market context including:
                - market_id, question, category
                - tokens: list of {token_id, outcome, price}
                - volume, liquidity
                - keywords: list of relevant keywords

        Returns:
            TradeSignal if edge exceeds minimum threshold, None otherwise.
        """
        market_id = market_data.get("id", "")
        question = market_data.get("question", "")
        tokens = market_data.get("tokens", [])
        liquidity = market_data.get("liquidity", 0)
        keywords = market_data.get("keywords", [])

        # Filter: minimum liquidity
        if liquidity < self._min_liquidity:
            return None

        # Evaluate each token (YES/NO)
        for token in tokens:
            token_id = token.get("token_id", "")
            token.get("outcome", "")
            market_price = float(token.get("price", 0))

            if market_price <= 0.05 or market_price >= 0.95:
                continue  # Skip extreme prices

            # Compile independent probability estimate
            compiled = self._odds_compiler.compile_probability(
                question, market_price, keywords or [question]
            )

            estimated_prob = compiled["probability"]
            confidence = compiled["confidence"]
            edge = compiled["edge"]

            # Check if edge and confidence meet thresholds
            if abs(edge) < self._min_edge:
                continue
            if confidence < self._confidence_required:
                continue

            # Determine trade direction
            if edge > 0:
                # Market underpriced — BUY
                side = "BUY"
            else:
                # Market overpriced — could buy NO (or sell YES)
                side = "BUY"  # Buy the opposite token
                # Find the other token
                other_tokens = [t for t in tokens if t.get("token_id") != token_id]
                if other_tokens:
                    token_id = other_tokens[0].get("token_id", token_id)
                    market_price = float(other_tokens[0].get("price", market_price))
                    edge = abs(edge)

            reasoning = (
                f"Edge detected on '{question[:60]}': "
                f"market={market_price:.3f}, estimated={estimated_prob:.3f}, "
                f"edge={edge:.3f}, confidence={confidence:.2f}"
            )
            logger.info("Edge found", market_id=market_id, edge=edge, confidence=confidence)

            return TradeSignal(
                market_id=market_id,
                token_id=token_id,
                side=side,
                confidence=confidence,
                edge=edge,
                suggested_size=0,  # Sized by risk manager
                price=market_price,
                reasoning=reasoning,
                strategy_name=self.get_name(),
            )

        return None

    def get_name(self) -> str:
        """Return strategy name."""
        return "EdgeFinder"
