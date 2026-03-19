"""Core strategy: find mispriced markets.

Compares Polymarket prices against independently compiled "true odds"
to find edges where the market is mispriced. Only trades when the edge
is positive AFTER accounting for fees.
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
        self._min_sources = cfg.get("min_independent_sources", 2)
        self._odds_compiler = OddsCompiler()

    def evaluate(self, market_data: dict[str, Any]) -> TradeSignal | None:
        """Evaluate a market for mispricing edge.

        Only generates a signal when:
        1. We have independent probability sources (not derived from market price)
        2. The edge exceeds minimum threshold AFTER fees
        3. Confidence meets the required threshold
        4. Market has sufficient liquidity

        Args:
            market_data: Full market context.

        Returns:
            TradeSignal if profitable edge found, None otherwise.
        """
        market_id = market_data.get("id", "")
        question = market_data.get("question", "")
        tokens = market_data.get("tokens", [])
        liquidity = float(market_data.get("liquidity", 0) or 0)
        keywords = market_data.get("keywords", [])
        category = market_data.get("category", "")

        if liquidity < self._min_liquidity:
            return None

        # Use question words as fallback keywords
        if not keywords:
            keywords = [w for w in question.split() if len(w) > 3][:5]

        # Get the YES token
        yes_token = next((t for t in tokens if t.get("outcome") == "Yes"), None)
        no_token = next((t for t in tokens if t.get("outcome") == "No"), None)

        if not yes_token:
            # Try first token if outcomes aren't labeled
            if tokens:
                yes_token = tokens[0]
                no_token = tokens[1] if len(tokens) > 1 else None
            else:
                return None

        market_price = float(yes_token.get("price", 0))
        if market_price <= 0.05 or market_price >= 0.95:
            return None  # Skip extreme prices — not enough room for edge

        # Compile INDEPENDENT probability estimate
        compiled = self._odds_compiler.compile_probability(
            market_question=question,
            market_price=market_price,
            keywords=keywords,
            category=category,
        )

        # Reject if we have no independent estimate
        if not compiled.get("has_independent_estimate", False):
            return None

        # Reject if not enough independent sources
        if compiled.get("num_sources", 0) < self._min_sources:
            return None

        estimated_prob = compiled["probability"]
        confidence = compiled["confidence"]
        raw_edge = compiled["edge"]
        edge_after_fees = compiled["edge_after_fees"]

        # The critical check: is there edge AFTER fees?
        if edge_after_fees <= 0:
            return None

        # Is the raw edge large enough to be meaningful?
        if abs(raw_edge) < self._min_edge:
            return None

        # Is our confidence high enough?
        if confidence < self._confidence_required:
            return None

        # Determine trade direction
        if raw_edge > 0:
            # Our estimate > market price → buy YES
            side = "BUY"
            token_id = yes_token.get("token_id", "")
            trade_price = market_price
        else:
            # Our estimate < market price → buy NO
            side = "BUY"
            if no_token:
                token_id = no_token.get("token_id", "")
                trade_price = float(no_token.get("price", 1 - market_price))
            else:
                return None

        sources_str = ", ".join(s["source"] for s in compiled.get("sources", []))
        reasoning = (
            f"Edge on '{question[:50]}': "
            f"market={market_price:.3f}, "
            f"estimated={estimated_prob:.3f}, "
            f"raw_edge={raw_edge:+.3f}, "
            f"edge_after_fees={edge_after_fees:+.3f}, "
            f"confidence={confidence:.2f}, "
            f"sources=[{sources_str}]"
        )
        logger.info(
            "Edge found",
            market_id=market_id,
            raw_edge=raw_edge,
            edge_after_fees=edge_after_fees,
            confidence=confidence,
            sources=compiled.get("num_sources", 0),
        )

        return TradeSignal(
            market_id=market_id,
            token_id=token_id,
            side=side,
            confidence=confidence,
            edge=edge_after_fees,  # Use fee-adjusted edge
            suggested_size=0,  # Sized by risk manager
            price=trade_price,
            reasoning=reasoning,
            strategy_name=self.get_name(),
        )

    def get_name(self) -> str:
        """Return strategy name."""
        return "EdgeFinder"
