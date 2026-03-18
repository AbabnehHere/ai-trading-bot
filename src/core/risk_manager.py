# TODO: Implement in Phase 5
"""Risk management engine — the most critical component of the bot.

Every trade MUST pass through the RiskManager before execution.
If any check fails, the trade is rejected. No exceptions. No overrides.
"""

from dataclasses import dataclass


@dataclass
class RiskCheckResult:
    """Result of a risk check."""

    approved: bool
    reason: str
    details: dict  # type: ignore[type-arg]


class RiskManager:
    """Pre-trade risk verification.

    Checks: position size, portfolio concentration, daily loss limit,
    drawdown circuit breaker, liquidity, correlation, market validity.
    """

    def check_trade(self, market_id: str, side: str, size: float, price: float) -> RiskCheckResult:
        """Run ALL risk checks on a proposed trade. Returns approval or rejection with reason.

        Args:
            market_id: The market to trade.
            side: "BUY" or "SELL".
            size: Number of shares.
            price: Limit price.

        Returns:
            RiskCheckResult with approval status and reason.
        """
        raise NotImplementedError("Phase 5")

    def check_daily_loss_limit(self) -> RiskCheckResult:
        """Check if daily loss limit has been breached.

        Returns:
            RiskCheckResult indicating if trading can continue.
        """
        raise NotImplementedError("Phase 5")

    def check_drawdown_circuit_breaker(self) -> RiskCheckResult:
        """Check if max drawdown circuit breaker should trigger.

        Returns:
            RiskCheckResult indicating if all trading should halt.
        """
        raise NotImplementedError("Phase 5")
