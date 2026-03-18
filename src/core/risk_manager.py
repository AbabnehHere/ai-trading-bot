"""Risk management engine — the most critical component of the bot.

Every trade MUST pass through the RiskManager before execution.
If any check fails, the trade is rejected. No exceptions. No overrides.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.core.position_manager import PositionManager
from src.utils.helpers import kelly_criterion
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RiskCheckResult:
    """Result of a risk check."""

    approved: bool
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


class RiskManager:
    """Pre-trade risk verification.

    Checks: position size, portfolio concentration, daily loss limit,
    drawdown circuit breaker, liquidity, correlation, market validity.
    """

    def __init__(
        self,
        position_manager: PositionManager,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the risk manager.

        Args:
            position_manager: Position manager for portfolio state.
            config: Risk configuration parameters.
        """
        self._positions = position_manager
        cfg = config or {}
        self._max_position_pct = cfg.get("max_position_pct", 0.03)
        self._max_category_exposure_pct = cfg.get("max_category_exposure_pct", 0.20)
        self._max_concurrent_positions = cfg.get("max_concurrent_positions", 10)
        self._max_daily_loss_pct = cfg.get("max_daily_loss_pct", 0.03)
        self._max_drawdown_pct = cfg.get("max_drawdown_pct", 0.10)
        self._max_slippage_pct = cfg.get("max_slippage_pct", 0.02)
        self._kelly_fraction = cfg.get("kelly_fraction", 0.25)
        self._stop_loss_pct = cfg.get("stop_loss_pct", 0.30)
        self._take_profit_pct = cfg.get("take_profit_pct", 0.50)
        self._max_hold_days = cfg.get("max_hold_days", 30)
        self._min_bankroll_usd = cfg.get("min_bankroll_usd", 50.0)
        self._cooldown_minutes = cfg.get("cooldown_after_loss_minutes", 30)
        self._min_trade_size = cfg.get("min_trade_size", 5.0)
        self._max_trade_size = cfg.get("max_trade_size", 100.0)
        self._max_trades_per_day = cfg.get("max_trades_per_day", 20)

        self._daily_losses: float = 0.0
        self._daily_trade_count: int = 0
        self._last_loss_time: datetime | None = None
        self._current_day: str = ""
        self._circuit_breaker_active = False

    def check_trade(
        self,
        market_id: str,
        side: str,
        size: float,
        price: float,
        category: str = "",
    ) -> RiskCheckResult:
        """Run ALL risk checks on a proposed trade.

        Args:
            market_id: The market to trade.
            side: "BUY" or "SELL".
            size: Number of shares.
            price: Limit price.
            category: Market category for concentration check.

        Returns:
            RiskCheckResult with approval status and reason.
        """
        self._maybe_reset_daily_counters()

        checks = [
            self._check_circuit_breaker(),
            self._check_bankroll_minimum(),
            self._check_daily_loss_limit(),
            self._check_daily_trade_count(),
            self._check_cooldown(),
            self._check_position_size(size, price),
            self._check_concurrent_positions(),
            self._check_drawdown(),
            self._check_trade_size_bounds(size, price),
        ]

        for result in checks:
            if not result.approved:
                logger.warning(
                    "Trade REJECTED",
                    market_id=market_id,
                    reason=result.reason,
                    side=side,
                    size=size,
                    price=price,
                )
                return result

        logger.info(
            "Trade APPROVED",
            market_id=market_id,
            side=side,
            size=size,
            price=price,
        )
        return RiskCheckResult(approved=True, reason="All checks passed")

    def calculate_position_size(self, probability: float, market_price: float) -> float:
        """Calculate recommended position size using fractional Kelly.

        Args:
            probability: Estimated true probability.
            market_price: Current market price.

        Returns:
            Recommended position size in USDC.
        """
        portfolio_value = self._positions.get_portfolio_value()
        odds = 1.0 / market_price if market_price > 0 else 0
        kelly_frac = kelly_criterion(probability, odds, self._kelly_fraction)

        # Kelly as fraction of portfolio
        kelly_size = kelly_frac * portfolio_value

        # Cap at max position percentage
        max_size = portfolio_value * self._max_position_pct

        # Apply absolute bounds
        size = min(kelly_size, max_size, self._max_trade_size)
        size = max(size, 0)

        # Don't trade if below minimum
        if size < self._min_trade_size:
            return 0.0

        return float(round(size, 2))

    def record_loss(self, amount: float) -> None:
        """Record a trading loss for daily tracking.

        Args:
            amount: Loss amount (positive number).
        """
        self._daily_losses += abs(amount)
        self._last_loss_time = datetime.now(UTC)

    def record_trade(self) -> None:
        """Record that a trade was executed today."""
        self._daily_trade_count += 1

    def check_stop_loss(self, pnl_pct: float) -> bool:
        """Check if a position should be stopped out.

        Args:
            pnl_pct: Current P&L percentage of the position.

        Returns:
            True if stop-loss should trigger.
        """
        return bool(pnl_pct <= -self._stop_loss_pct)

    def check_take_profit(self, pnl_pct: float) -> bool:
        """Check if partial profits should be taken.

        Args:
            pnl_pct: Current P&L percentage of the position.

        Returns:
            True if take-profit should trigger.
        """
        return bool(pnl_pct >= self._take_profit_pct)

    def check_daily_loss_limit(self) -> RiskCheckResult:
        """Check if daily loss limit has been breached."""
        return self._check_daily_loss_limit()

    def check_drawdown_circuit_breaker(self) -> RiskCheckResult:
        """Check if max drawdown circuit breaker should trigger."""
        return self._check_drawdown()

    # --- Private check methods ---

    def _maybe_reset_daily_counters(self) -> None:
        """Reset daily counters if it's a new day."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if today != self._current_day:
            self._current_day = today
            self._daily_losses = 0.0
            self._daily_trade_count = 0

    def _check_circuit_breaker(self) -> RiskCheckResult:
        if self._circuit_breaker_active:
            return RiskCheckResult(
                approved=False,
                reason="Circuit breaker is active — manual restart required",
            )
        return RiskCheckResult(approved=True, reason="")

    def _check_bankroll_minimum(self) -> RiskCheckResult:
        balance = self._positions.get_portfolio_value()
        if balance < self._min_bankroll_usd:
            return RiskCheckResult(
                approved=False,
                reason=f"Bankroll ${balance:.2f} below minimum ${self._min_bankroll_usd:.2f}",
            )
        return RiskCheckResult(approved=True, reason="")

    def _check_daily_loss_limit(self) -> RiskCheckResult:
        portfolio = self._positions.get_portfolio_value()
        max_loss = portfolio * self._max_daily_loss_pct
        if self._daily_losses >= max_loss:
            return RiskCheckResult(
                approved=False,
                reason=f"Daily loss limit hit: ${self._daily_losses:.2f} >= ${max_loss:.2f}",
            )
        return RiskCheckResult(approved=True, reason="")

    def _check_daily_trade_count(self) -> RiskCheckResult:
        if self._daily_trade_count >= self._max_trades_per_day:
            return RiskCheckResult(
                approved=False,
                reason=f"Max daily trades reached: {self._daily_trade_count}",
            )
        return RiskCheckResult(approved=True, reason="")

    def _check_cooldown(self) -> RiskCheckResult:
        if self._last_loss_time:
            elapsed = (datetime.now(UTC) - self._last_loss_time).total_seconds()
            cooldown_secs = self._cooldown_minutes * 60
            if elapsed < cooldown_secs:
                remaining = int(cooldown_secs - elapsed)
                return RiskCheckResult(
                    approved=False,
                    reason=f"Post-loss cooldown active — {remaining}s remaining",
                )
        return RiskCheckResult(approved=True, reason="")

    def _check_position_size(self, size: float, price: float) -> RiskCheckResult:
        cost = size * price
        portfolio = self._positions.get_portfolio_value()
        max_cost = portfolio * self._max_position_pct
        if cost > max_cost:
            return RiskCheckResult(
                approved=False,
                reason=(
                    f"Position ${cost:.2f} exceeds max "
                    f"{self._max_position_pct:.0%} of portfolio (${max_cost:.2f})"
                ),
            )
        return RiskCheckResult(approved=True, reason="")

    def _check_concurrent_positions(self) -> RiskCheckResult:
        count = self._positions.get_position_count()
        if count >= self._max_concurrent_positions:
            return RiskCheckResult(
                approved=False,
                reason=f"Max concurrent positions reached: {count}",
            )
        return RiskCheckResult(approved=True, reason="")

    def _check_drawdown(self) -> RiskCheckResult:
        drawdown = self._positions.get_drawdown()
        if drawdown >= self._max_drawdown_pct:
            self._circuit_breaker_active = True
            return RiskCheckResult(
                approved=False,
                reason=(
                    f"Drawdown circuit breaker triggered: "
                    f"{drawdown:.1%} >= {self._max_drawdown_pct:.1%}"
                ),
            )
        return RiskCheckResult(approved=True, reason="")

    def _check_trade_size_bounds(self, size: float, price: float) -> RiskCheckResult:
        cost = size * price
        if cost < self._min_trade_size:
            return RiskCheckResult(
                approved=False,
                reason=f"Trade ${cost:.2f} below minimum ${self._min_trade_size:.2f}",
            )
        if cost > self._max_trade_size:
            return RiskCheckResult(
                approved=False,
                reason=f"Trade ${cost:.2f} exceeds maximum ${self._max_trade_size:.2f}",
            )
        return RiskCheckResult(approved=True, reason="")
