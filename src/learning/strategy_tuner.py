"""Adjust strategy parameters based on performance.

Analyzes performance data to suggest or automatically apply
parameter adjustments to improve strategy performance.
"""

import sqlite3
from typing import Any

from src.learning.performance import PerformanceTracker
from src.utils.helpers import now_iso
from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = "data/trades.db"


class StrategyTuner:
    """Tunes strategy parameters based on historical performance."""

    def __init__(
        self,
        performance: PerformanceTracker,
        review_interval: int = 20,
        db_path: str = DB_PATH,
    ) -> None:
        """Initialize the strategy tuner.

        Args:
            performance: Performance tracker for metrics.
            review_interval: Number of trades between reviews.
            db_path: Path to the SQLite database.
        """
        self._performance = performance
        self._review_interval = review_interval
        self._db_path = db_path
        self._trades_since_review = 0

    def should_review(self) -> bool:
        """Check if it's time for a strategy review.

        Returns:
            True if enough trades have occurred since last review.
        """
        self._trades_since_review += 1
        return self._trades_since_review >= self._review_interval

    def suggest_adjustments(self, current_config: dict[str, Any]) -> list[dict[str, Any]]:
        """Suggest parameter adjustments based on recent performance.

        Args:
            current_config: Current strategy configuration.

        Returns:
            List of suggested adjustments with reasoning.
        """
        metrics = self._performance.calculate_metrics()
        suggestions: list[dict[str, Any]] = []

        # Rule 1: If win rate is too low, increase minimum edge threshold
        if metrics["total_trades"] >= 10 and metrics["win_rate"] < 0.50:
            current_edge = current_config.get("min_edge_threshold", 0.08)
            new_edge = min(current_edge + 0.01, 0.15)
            suggestions.append(
                {
                    "parameter": "min_edge_threshold",
                    "current": current_edge,
                    "suggested": new_edge,
                    "reason": (
                        f"Win rate {metrics['win_rate']:.0%} below 50% — increase edge requirement"
                    ),
                }
            )

        # Rule 2: If max drawdown is high, reduce position size
        if metrics["max_drawdown"] > 0.08:
            current_size = current_config.get("max_position_pct", 0.03)
            new_size = max(current_size - 0.005, 0.01)
            suggestions.append(
                {
                    "parameter": "max_position_pct",
                    "current": current_size,
                    "suggested": new_size,
                    "reason": (
                        f"Max drawdown {metrics['max_drawdown']:.1%} is high — reduce position size"
                    ),
                }
            )

        # Rule 3: If profit factor is good, slightly relax edge threshold
        if (
            metrics["total_trades"] >= 20
            and metrics["profit_factor"] > 2.0
            and metrics["win_rate"] > 0.65
        ):
            current_edge = current_config.get("min_edge_threshold", 0.08)
            new_edge = max(current_edge - 0.005, 0.05)
            if new_edge < current_edge:
                suggestions.append(
                    {
                        "parameter": "min_edge_threshold",
                        "current": current_edge,
                        "suggested": new_edge,
                        "reason": (
                            f"Strong performance (PF={metrics['profit_factor']:.1f}, "
                            f"WR={metrics['win_rate']:.0%}) — slightly relax edge"
                        ),
                    }
                )

        if suggestions:
            logger.info("Strategy tuner suggestions", count=len(suggestions))
        else:
            logger.info("Strategy tuner: no adjustments needed")

        self._trades_since_review = 0
        return suggestions

    def apply_adjustments(self, adjustments: list[dict[str, Any]]) -> None:
        """Record parameter adjustments in the database.

        Args:
            adjustments: List of adjustment dicts from suggest_adjustments.
        """
        conn = sqlite3.connect(self._db_path)
        try:
            for adj in adjustments:
                conn.execute(
                    """INSERT INTO strategy_parameters
                       (parameter_name, current_value, previous_value,
                        changed_at, reason_for_change)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        adj["parameter"],
                        str(adj["suggested"]),
                        str(adj["current"]),
                        now_iso(),
                        adj["reason"],
                    ),
                )
                logger.info(
                    "Parameter adjusted",
                    parameter=adj["parameter"],
                    old=adj["current"],
                    new=adj["suggested"],
                )
            conn.commit()
        finally:
            conn.close()
