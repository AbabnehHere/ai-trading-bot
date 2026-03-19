"""Order placement, tracking, and cancellation.

Handles all interaction with the Polymarket CLOB API for order management.
"""

import os
import sqlite3
from typing import Any

from py_clob_client.client import ClobClient  # type: ignore[import-untyped]
from py_clob_client.clob_types import OrderArgs  # type: ignore[import-untyped]

from src.utils.helpers import now_iso
from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = "data/trades.db"
POLYMARKET_API_BASE = "https://clob.polymarket.com"
TAKER_FEE_RATE = 0.02
MAKER_FEE_RATE = 0.0


class OrderManager:
    """Manages order lifecycle: creation, tracking, cancellation."""

    def __init__(self, paper: bool = True) -> None:
        """Initialize the order manager.

        Args:
            paper: If True, simulate orders without placing real ones.
        """
        self._paper = paper
        self._clob_client: ClobClient | None = None
        self._next_paper_id = 1

        if not paper:
            private_key = os.getenv("PRIVATE_KEY", "")
            if private_key:
                try:
                    self._clob_client = ClobClient(
                        POLYMARKET_API_BASE,
                        key=private_key,
                        chain_id=137,
                    )
                    self._clob_client.set_api_creds(
                        self._clob_client.create_or_derive_api_creds()  # type: ignore[no-untyped-call]
                    )
                    logger.info("CLOB client initialized for live trading")
                except Exception as e:
                    logger.error("Failed to init CLOB client", error=str(e))
                    raise

    def place_order(
        self,
        token_id: str,
        market_id: str,
        side: str,
        size: float,
        price: float,
        strategy: str = "",
        reasoning: str = "",
    ) -> dict[str, Any]:
        """Place a limit order on Polymarket.

        Args:
            token_id: The token to trade (YES or NO token ID).
            market_id: The market condition ID (for logging).
            side: "BUY" or "SELL".
            size: Number of shares.
            price: Limit price (0-1).
            strategy: Name of the strategy that generated this trade.
            reasoning: Human-readable explanation of why.

        Returns:
            Order confirmation details.
        """
        logger.info(
            "Placing order",
            market_id=market_id,
            side=side,
            size=size,
            price=price,
            paper=self._paper,
            strategy=strategy,
        )

        if self._paper:
            order_id = f"paper_{self._next_paper_id}"
            self._next_paper_id += 1
            fees = size * price * TAKER_FEE_RATE
            result = {
                "order_id": order_id,
                "market_id": market_id,
                "token_id": token_id,
                "side": side,
                "size": size,
                "price": price,
                "fees": fees,
                "status": "filled",
                "fill_price": price,
                "is_paper": True,
            }
        else:
            if not self._clob_client:
                raise RuntimeError("CLOB client not initialized for live trading")

            clob_side = 0 if side == "BUY" else 1  # 0=BUY, 1=SELL in CLOB API
            order_args = OrderArgs(
                price=price,
                size=size,
                side=clob_side,
                token_id=token_id,
            )
            try:
                response = self._clob_client.create_and_post_order(order_args)  # type: ignore[no-untyped-call]
                result = {
                    "order_id": response.get("orderID", "unknown"),
                    "market_id": market_id,
                    "token_id": token_id,
                    "side": side,
                    "size": size,
                    "price": price,
                    "fees": size * price * TAKER_FEE_RATE,
                    "status": "pending",
                    "fill_price": None,
                    "is_paper": False,
                }
            except Exception as e:
                logger.error("Order placement failed", error=str(e))
                raise

        # Record trade in database
        self._record_trade(result, strategy, reasoning)
        return result

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order.

        Args:
            order_id: The order to cancel.

        Returns:
            True if cancellation was successful.
        """
        if self._paper or order_id.startswith("paper_"):
            logger.info("Paper order cancelled", order_id=order_id)
            return True

        if not self._clob_client:
            raise RuntimeError("CLOB client not initialized")

        try:
            self._clob_client.cancel(order_id)  # type: ignore[no-untyped-call]
            logger.info("Order cancelled", order_id=order_id)
            return True
        except Exception as e:
            logger.error("Cancel failed", order_id=order_id, error=str(e))
            return False

    def get_open_orders(self) -> list[dict[str, Any]]:
        """Retrieve all currently open orders.

        Returns:
            List of open order details.
        """
        if self._paper:
            return []

        if not self._clob_client:
            return []

        try:
            orders = self._clob_client.get_orders()  # type: ignore[no-untyped-call]
            return orders if isinstance(orders, list) else []
        except Exception as e:
            logger.error("Failed to fetch open orders", error=str(e))
            return []

    def _record_trade(self, order: dict[str, Any], strategy: str, reasoning: str) -> None:
        """Record a trade in the SQLite database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                """INSERT INTO trades
                   (market_id, side, direction, price, size, timestamp, fees,
                    order_type, status, fill_price, strategy_used, reasoning, is_paper)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    order["market_id"],
                    "YES",  # Simplified — would need token mapping
                    order["side"],
                    order["price"],
                    order["size"],
                    now_iso(),
                    order.get("fees", 0.0),
                    "limit",
                    order.get("status", "pending"),
                    order.get("fill_price"),
                    strategy,
                    reasoning,
                    order.get("is_paper", True),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("Failed to record trade to DB", error=str(e))
