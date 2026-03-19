"""Portfolio and position tracking.

Tracks all open positions, calculates P&L, and provides portfolio overview.
Properly accounts for trading fees on entry and exit.
"""

from pathlib import Path
from typing import Any

from src.data.market_data import MarketDataClient
from src.utils.helpers import now_iso, safe_divide
from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = "data/trades.db"

# Polymarket fee constants
MAKER_FEE_RATE = 0.0  # 0% for limit orders that add liquidity
TAKER_FEE_RATE = 0.02  # ~2% for orders that remove liquidity


class PositionManager:
    """Tracks and manages all trading positions."""

    def __init__(
        self,
        market_data: MarketDataClient,
        initial_balance: float = 1000.0,
        paper: bool = True,
        use_taker_fees: bool = True,
        skip_db_reload: bool = False,
    ) -> None:
        """Initialize the position manager.

        Args:
            market_data: Market data client for price lookups.
            initial_balance: Starting cash balance in USDC.
            paper: If True, track paper positions only.
            use_taker_fees: If True, assume taker fees on all trades.
                Set False if using limit orders that rest on the book (maker).
        """
        self._market_data = market_data
        self._cash = initial_balance
        self._paper = paper
        self._fee_rate = TAKER_FEE_RATE if use_taker_fees else MAKER_FEE_RATE
        self._positions: dict[str, dict[str, Any]] = {}
        self._peak_value = initial_balance
        self._total_fees_paid = 0.0
        self._realized_pnl = 0.0

        # Reload positions from database on startup (skip in tests)
        if not skip_db_reload:
            self._reload_from_db(initial_balance)

    def _reload_from_db(self, initial_balance: float) -> None:
        """Reload positions from the trades database on startup.

        Reconstructs position state from BUY/SELL history so the bot
        doesn't lose track of positions after a restart.
        """
        import sqlite3

        db_path = "data/trades.db"
        if not Path(db_path).exists():
            return

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            trades = conn.execute(
                """SELECT market_id, direction, price, size, fees
                   FROM trades WHERE status = 'filled'
                   ORDER BY timestamp ASC"""
            ).fetchall()
            conn.close()

            if not trades:
                return

            total_spent = 0.0
            total_received = 0.0
            total_fees = 0.0

            for t in trades:
                mkt = t["market_id"]
                side = t["direction"]
                price = float(t["price"])
                size = float(t["size"])
                fees = float(t["fees"] or 0)
                total_fees += fees

                if side == "BUY":
                    total_spent += size * price + fees
                    key = f"{mkt}:"
                    if key in self._positions:
                        pos = self._positions[key]
                        total_size = pos["size"] + size
                        pos["avg_entry_price"] = safe_divide(
                            pos["avg_entry_price"] * pos["size"] + price * size,
                            total_size,
                        )
                        pos["avg_cost_basis"] = safe_divide(
                            pos["avg_cost_basis"] * pos["size"]
                            + (price + price * self._fee_rate) * size,
                            total_size,
                        )
                        pos["size"] = total_size
                        pos["total_fees"] += fees
                    else:
                        self._positions[key] = {
                            "market_id": mkt,
                            "token_id": "",
                            "side": "YES",
                            "avg_entry_price": price,
                            "avg_cost_basis": price + price * self._fee_rate,
                            "size": size,
                            "total_fees": fees,
                            "opened_at": now_iso(),
                        }
                elif side == "SELL":
                    total_received += size * price - fees
                    key = f"{mkt}:"
                    if key in self._positions:
                        self._positions[key]["size"] -= size
                        if self._positions[key]["size"] <= 0.001:
                            del self._positions[key]

            self._cash = initial_balance - total_spent + total_received
            self._total_fees_paid = total_fees

            if self._positions:
                logger.info(
                    "Positions reloaded from DB",
                    positions=len(self._positions),
                    cash=f"${self._cash:.2f}",
                )

        except Exception as e:
            logger.warning("Failed to reload positions from DB", error=str(e))

    def record_fill(
        self,
        market_id: str,
        token_id: str,
        side: str,
        size: float,
        price: float,
    ) -> dict[str, Any]:
        """Record a filled order and update positions.

        Deducts fees from cash balance on every fill.

        Args:
            market_id: The market condition ID.
            token_id: The token ID (YES/NO).
            side: "BUY" or "SELL".
            size: Number of shares filled.
            price: Fill price.

        Returns:
            Dict with fill details including fees paid.
        """
        notional = size * price
        fees = notional * self._fee_rate
        self._total_fees_paid += fees

        if side == "BUY":
            total_cost = notional + fees
            self._cash -= total_cost
            key = f"{market_id}:{token_id}"
            if key in self._positions:
                pos = self._positions[key]
                total_size = pos["size"] + size
                # Track cost basis including fees
                old_cost = pos["avg_cost_basis"] * pos["size"]
                new_cost = (price + price * self._fee_rate) * size
                pos["avg_cost_basis"] = safe_divide(old_cost + new_cost, total_size)
                pos["avg_entry_price"] = safe_divide(
                    pos["avg_entry_price"] * pos["size"] + price * size,
                    total_size,
                )
                pos["size"] = total_size
                pos["total_fees"] += fees
            else:
                self._positions[key] = {
                    "market_id": market_id,
                    "token_id": token_id,
                    "side": "YES",
                    "avg_entry_price": price,
                    "avg_cost_basis": price + price * self._fee_rate,
                    "size": size,
                    "total_fees": fees,
                    "opened_at": now_iso(),
                }
            logger.info(
                "Position opened/added",
                market_id=market_id,
                size=size,
                price=price,
                fees=fees,
            )

            return {"side": "BUY", "cost": total_cost, "fees": fees}

        elif side == "SELL":
            key = f"{market_id}:{token_id}"
            if key in self._positions:
                pos = self._positions[key]
                sell_size = min(size, pos["size"])
                gross_proceeds = sell_size * price
                net_proceeds = gross_proceeds - fees
                self._cash += net_proceeds

                # Realized P&L: gross gain minus entry and exit fees
                entry_fees_share = pos["total_fees"] * sell_size / pos["size"]
                gross_gain = sell_size * (price - pos["avg_entry_price"])
                realized = gross_gain - fees - entry_fees_share
                self._realized_pnl += realized

                pos["size"] -= sell_size
                if pos["size"] <= 0.001:
                    del self._positions[key]
                else:
                    # Reduce tracked fees proportionally
                    pos["total_fees"] *= pos["size"] / (pos["size"] + sell_size)

                logger.info(
                    "Position reduced/closed",
                    market_id=market_id,
                    realized_pnl=realized,
                    fees=fees,
                )

                return {
                    "side": "SELL",
                    "proceeds": net_proceeds,
                    "fees": fees,
                    "realized_pnl": realized,
                }
            else:
                self._cash += notional - fees
                return {"side": "SELL", "proceeds": notional - fees, "fees": fees}

        return {"side": side, "fees": 0.0}

    def get_positions(self) -> list[dict[str, Any]]:
        """Get all current positions."""
        return [
            {
                "key": key,
                "market_id": pos["market_id"],
                "token_id": pos["token_id"],
                "side": pos["side"],
                "size": pos["size"],
                "avg_entry_price": pos["avg_entry_price"],
                "avg_cost_basis": pos["avg_cost_basis"],
                "total_fees": pos["total_fees"],
                "opened_at": pos["opened_at"],
            }
            for key, pos in self._positions.items()
        ]

    def get_cash_balance(self) -> float:
        """Get current cash balance."""
        return self._cash

    def get_total_fees_paid(self) -> float:
        """Get total fees paid across all trades."""
        return self._total_fees_paid

    def get_realized_pnl(self) -> float:
        """Get total realized P&L (after fees)."""
        return self._realized_pnl

    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value including cash and positions.

        Position values use entry price (conservative estimate).
        """
        position_value = sum(
            pos["size"] * pos["avg_entry_price"] for pos in self._positions.values()
        )
        total = self._cash + position_value
        self._peak_value = max(self._peak_value, total)
        return float(total)

    def get_drawdown(self) -> float:
        """Calculate current drawdown from peak."""
        current = self.get_portfolio_value()
        if self._peak_value <= 0:
            return 0.0
        return (self._peak_value - current) / self._peak_value

    def get_position_count(self) -> int:
        """Get number of open positions."""
        return len(self._positions)

    def get_position_pnl(self, market_id: str, current_price: float) -> dict[str, Any]:
        """Calculate P&L for a specific position including fee impact.

        Args:
            market_id: The market position to evaluate.
            current_price: Current market price for the token.

        Returns:
            P&L details including unrealized gains after estimated exit fees.
        """
        matching = [(k, p) for k, p in self._positions.items() if p["market_id"] == market_id]
        if not matching:
            return {"unrealized_pnl": 0.0, "pnl_pct": 0.0}

        _, pos = matching[0]
        # Gross unrealized P&L
        gross_pnl = pos["size"] * (current_price - pos["avg_entry_price"])
        # Estimated exit fees
        exit_fees = pos["size"] * current_price * self._fee_rate
        # Net unrealized P&L (after entry fees already paid + estimated exit fees)
        net_pnl = gross_pnl - exit_fees
        # P&L percentage based on cost basis (includes entry fees)
        pnl_pct = safe_divide(current_price - pos["avg_cost_basis"], pos["avg_cost_basis"])
        return {"unrealized_pnl": net_pnl, "pnl_pct": pnl_pct}

    def update_positions(self) -> None:
        """Sync positions with the exchange (stub for live mode)."""
        if not self._paper:
            logger.info("Position sync with exchange not yet implemented")
