"""Performance analytics and metrics.

Calculates and tracks key performance metrics like win rate,
Sharpe ratio, max drawdown, and strategy-level performance.
"""

import sqlite3
from typing import Any

import numpy as np

from src.utils.helpers import now_iso, safe_divide
from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = "data/trades.db"


class PerformanceTracker:
    """Tracks and calculates trading performance metrics."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        """Initialize the performance tracker.

        Args:
            db_path: Path to the SQLite database.
        """
        self._db_path = db_path

    def calculate_metrics(self, paper: bool = True) -> dict[str, Any]:
        """Calculate all performance metrics from trade history.

        Args:
            paper: If True, calculate for paper trades only.

        Returns:
            Dict with metrics: win_rate, total_pnl, sharpe_ratio,
            max_drawdown, avg_trade_pnl, profit_factor, etc.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                """SELECT * FROM trades
                    WHERE status = 'filled' AND is_paper = ?
                    ORDER BY timestamp ASC""",
                (1 if paper else 0,),
            )
            trades = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

        if not trades:
            return self._empty_metrics()

        # Calculate P&L for each trade
        pnls = []
        for trade in trades:
            entry_price = float(trade.get("price", 0))
            fill_price = float(trade.get("fill_price", entry_price))
            size = float(trade.get("size", 0))
            fees = float(trade.get("fees", 0))
            direction = trade.get("direction", "BUY")

            if direction == "BUY":
                # For buy trades, profit if price goes up (simplified)
                pnl = size * (fill_price - entry_price) - fees
            else:
                pnl = size * (entry_price - fill_price) - fees
            pnls.append(pnl)

        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        total_pnl = sum(pnls)
        win_rate = safe_divide(len(wins), len(pnls))
        avg_profit = np.mean(wins).item() if wins else 0.0
        avg_loss = np.mean(losses).item() if losses else 0.0
        profit_factor = safe_divide(sum(wins), abs(sum(losses))) if losses else float("inf")

        # Sharpe ratio (annualized, assuming daily returns)
        if len(pnls) > 1:
            returns = np.array(pnls)
            sharpe = (
                float(np.mean(returns) / np.std(returns) * np.sqrt(252))
                if np.std(returns) > 0
                else 0.0
            )
        else:
            sharpe = 0.0

        # Max drawdown
        cumulative = np.cumsum(pnls)
        peak = np.maximum.accumulate(cumulative)
        drawdowns = peak - cumulative
        max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

        return {
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "best_trade": max(pnls) if pnls else 0.0,
            "worst_trade": min(pnls) if pnls else 0.0,
        }

    def get_strategy_performance(self, strategy_name: str) -> dict[str, Any]:
        """Get performance metrics for a specific strategy.

        Args:
            strategy_name: Name of the strategy to evaluate.

        Returns:
            Strategy-specific performance metrics.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                """SELECT * FROM trades
                   WHERE strategy_used = ? AND status = 'filled'
                   ORDER BY timestamp ASC""",
                (strategy_name,),
            )
            trades = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

        if not trades:
            return self._empty_metrics()

        pnls = []
        for trade in trades:
            entry_price = float(trade.get("price", 0))
            fill_price = float(trade.get("fill_price", entry_price))
            size = float(trade.get("size", 0))
            pnl = size * (fill_price - entry_price)
            pnls.append(pnl)

        wins = [p for p in pnls if p > 0]
        [p for p in pnls if p < 0]

        return {
            "strategy": strategy_name,
            "total_trades": len(trades),
            "win_rate": safe_divide(len(wins), len(pnls)),
            "total_pnl": sum(pnls),
            "avg_pnl": float(np.mean(pnls)) if pnls else 0.0,
        }

    def save_snapshot(self, balance: float, pnl: float, paper: bool = True) -> None:
        """Save a performance snapshot to the database.

        Args:
            balance: Current total balance.
            pnl: Current total P&L.
            paper: Whether this is a paper trading snapshot.
        """
        metrics = self.calculate_metrics(paper=paper)
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute(
                """INSERT INTO performance_snapshots
                   (timestamp, total_balance, total_pnl, win_rate, avg_profit,
                    avg_loss, sharpe_ratio, max_drawdown, total_trades, is_paper)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    now_iso(),
                    balance,
                    pnl,
                    metrics["win_rate"],
                    metrics["avg_profit"],
                    metrics["avg_loss"],
                    metrics["sharpe_ratio"],
                    metrics["max_drawdown"],
                    metrics["total_trades"],
                    paper,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def _empty_metrics(self) -> dict[str, Any]:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_profit": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }
