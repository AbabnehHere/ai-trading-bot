"""Portfolio and position tracking.

Tracks all open positions, calculates P&L, and provides portfolio overview.
"""

from typing import Any

from src.data.market_data import MarketDataClient
from src.utils.helpers import now_iso, safe_divide
from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = "data/trades.db"


class PositionManager:
    """Tracks and manages all trading positions."""

    def __init__(
        self,
        market_data: MarketDataClient,
        initial_balance: float = 1000.0,
        paper: bool = True,
    ) -> None:
        """Initialize the position manager.

        Args:
            market_data: Market data client for price lookups.
            initial_balance: Starting cash balance in USDC.
            paper: If True, track paper positions only.
        """
        self._market_data = market_data
        self._cash = initial_balance
        self._paper = paper
        self._positions: dict[str, dict[str, Any]] = {}
        self._peak_value = initial_balance

    def record_fill(
        self,
        market_id: str,
        token_id: str,
        side: str,
        size: float,
        price: float,
    ) -> None:
        """Record a filled order and update positions.

        Args:
            market_id: The market condition ID.
            token_id: The token ID (YES/NO).
            side: "BUY" or "SELL".
            size: Number of shares filled.
            price: Fill price.
        """
        cost = size * price

        if side == "BUY":
            self._cash -= cost
            key = f"{market_id}:{token_id}"
            if key in self._positions:
                pos = self._positions[key]
                total_size = pos["size"] + size
                pos["avg_entry_price"] = safe_divide(
                    pos["avg_entry_price"] * pos["size"] + price * size,
                    total_size,
                )
                pos["size"] = total_size
            else:
                self._positions[key] = {
                    "market_id": market_id,
                    "token_id": token_id,
                    "side": "YES",
                    "avg_entry_price": price,
                    "size": size,
                    "opened_at": now_iso(),
                }
            logger.info("Position opened/added", market_id=market_id, size=size, price=price)

        elif side == "SELL":
            key = f"{market_id}:{token_id}"
            if key in self._positions:
                pos = self._positions[key]
                sell_size = min(size, pos["size"])
                realized = sell_size * (price - pos["avg_entry_price"])
                self._cash += sell_size * price
                pos["size"] -= sell_size
                if pos["size"] <= 0.001:
                    del self._positions[key]
                logger.info(
                    "Position reduced/closed",
                    market_id=market_id,
                    realized_pnl=realized,
                )
            else:
                self._cash += cost  # Short sell (not typical for Polymarket)

    def get_positions(self) -> list[dict[str, Any]]:
        """Get all current positions.

        Returns:
            List of position details with current values.
        """
        return [
            {
                "key": key,
                "market_id": pos["market_id"],
                "token_id": pos["token_id"],
                "side": pos["side"],
                "size": pos["size"],
                "avg_entry_price": pos["avg_entry_price"],
                "opened_at": pos["opened_at"],
            }
            for key, pos in self._positions.items()
        ]

    def get_cash_balance(self) -> float:
        """Get current cash balance.

        Returns:
            Cash balance in USDC.
        """
        return self._cash

    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value including cash and positions.

        Estimates position values using entry price (for offline mode).

        Returns:
            Total portfolio value in USDC.
        """
        position_value = sum(
            pos["size"] * pos["avg_entry_price"] for pos in self._positions.values()
        )
        total = self._cash + position_value
        self._peak_value = max(self._peak_value, total)
        return float(total)

    def get_drawdown(self) -> float:
        """Calculate current drawdown from peak.

        Returns:
            Drawdown as a fraction (0 = no drawdown, 0.1 = 10% down from peak).
        """
        current = self.get_portfolio_value()
        if self._peak_value <= 0:
            return 0.0
        return (self._peak_value - current) / self._peak_value

    def get_position_count(self) -> int:
        """Get number of open positions."""
        return len(self._positions)

    def get_position_pnl(self, market_id: str, current_price: float) -> dict[str, Any]:
        """Calculate P&L for a specific position.

        Args:
            market_id: The market position to evaluate.
            current_price: Current market price for the token.

        Returns:
            P&L details including unrealized gains.
        """
        matching = [(k, p) for k, p in self._positions.items() if p["market_id"] == market_id]
        if not matching:
            return {"unrealized_pnl": 0.0, "pnl_pct": 0.0}

        _, pos = matching[0]
        unrealized = pos["size"] * (current_price - pos["avg_entry_price"])
        pnl_pct = safe_divide(current_price - pos["avg_entry_price"], pos["avg_entry_price"])
        return {"unrealized_pnl": unrealized, "pnl_pct": pnl_pct}

    def update_positions(self) -> None:
        """Sync positions with the exchange (stub for live mode)."""
        # In paper mode, positions are tracked internally
        if not self._paper:
            logger.info("Position sync with exchange not yet implemented")
