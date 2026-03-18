"""Historical backtesting engine.

Simulates strategy performance against historical market data
to validate strategies before live deployment.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np

from src.core.position_manager import PositionManager
from src.core.risk_manager import RiskManager
from src.data.market_data import MarketDataClient
from src.strategy.base_strategy import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)

HISTORICAL_DIR = Path("data/historical")


class Backtester:
    """Runs strategies against historical data."""

    def __init__(
        self,
        strategies: list[BaseStrategy],
        initial_balance: float = 1000.0,
        risk_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the backtester.

        Args:
            strategies: List of strategies to test.
            initial_balance: Starting balance for simulation.
            risk_config: Risk management configuration.
        """
        self._strategies = strategies
        self._initial_balance = initial_balance
        self._risk_config = risk_config
        self._results: dict[str, Any] = {}

    def run(self, data_dir: str | None = None) -> dict[str, Any]:
        """Run a backtest against all historical data files.

        Args:
            data_dir: Directory containing historical data JSON files.

        Returns:
            Backtest results including trades, P&L, and metrics.
        """
        data_path = Path(data_dir) if data_dir else HISTORICAL_DIR
        if not data_path.exists():
            return {"error": "No historical data directory found"}

        data_files = list(data_path.glob("*.json"))
        if not data_files:
            return {"error": "No historical data files found"}

        logger.info("Starting backtest", data_files=len(data_files))

        # Initialize simulation state
        market_data = MarketDataClient()
        positions = PositionManager(market_data, self._initial_balance, paper=True)
        risk_manager = RiskManager(positions, self._risk_config)

        trades: list[dict[str, Any]] = []
        equity_curve = [self._initial_balance]

        for data_file in data_files:
            try:
                with open(data_file) as f:
                    market_data_dict = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Skipping bad data file", file=str(data_file), error=str(e))
                continue

            market = market_data_dict.get("market", {})

            # Run each strategy on this market
            for strategy in self._strategies:
                signal = strategy.evaluate(market)
                if not signal:
                    continue

                # Calculate position size
                size_usd = risk_manager.calculate_position_size(signal.confidence, signal.price)
                if size_usd <= 0:
                    continue

                shares = size_usd / signal.price if signal.price > 0 else 0

                # Run risk checks
                check = risk_manager.check_trade(
                    signal.market_id, signal.side, shares, signal.price
                )
                if not check.approved:
                    continue

                # Simulate fill
                positions.record_fill(
                    signal.market_id, signal.token_id, signal.side, shares, signal.price
                )
                risk_manager.record_trade()

                trade = {
                    "market_id": signal.market_id,
                    "strategy": signal.strategy_name,
                    "side": signal.side,
                    "price": signal.price,
                    "size": shares,
                    "cost": size_usd,
                    "edge": signal.edge,
                    "reasoning": signal.reasoning,
                }
                trades.append(trade)
                equity_curve.append(positions.get_portfolio_value())

        # Calculate results
        self._results = self._calculate_results(trades, equity_curve)
        logger.info("Backtest complete", trades=len(trades), pnl=self._results.get("total_pnl", 0))
        return self._results

    def get_results_summary(self) -> dict[str, Any]:
        """Get a summary of the most recent backtest results."""
        return self._results

    def _calculate_results(
        self, trades: list[dict[str, Any]], equity_curve: list[float]
    ) -> dict[str, Any]:
        """Calculate backtest metrics from trades and equity curve."""
        if not trades:
            return {
                "total_trades": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "equity_curve": equity_curve,
                "trades": [],
            }

        final_value = equity_curve[-1] if equity_curve else self._initial_balance
        total_pnl = final_value - self._initial_balance

        # Calculate drawdown from equity curve
        eq = np.array(equity_curve)
        peak = np.maximum.accumulate(eq)
        drawdown = (peak - eq) / peak
        max_drawdown = float(np.max(drawdown)) if len(drawdown) > 0 else 0.0

        # Returns for Sharpe
        if len(equity_curve) > 1:
            returns = np.diff(eq) / eq[:-1]
            sharpe = (
                float(np.mean(returns) / np.std(returns) * np.sqrt(252))
                if np.std(returns) > 0
                else 0.0
            )
        else:
            sharpe = 0.0

        return {
            "total_trades": len(trades),
            "total_pnl": total_pnl,
            "total_return_pct": total_pnl / self._initial_balance,
            "final_balance": final_value,
            "win_rate": 0.0,  # Need resolution data for actual win/loss
            "profit_factor": 0.0,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe,
            "equity_curve": equity_curve,
            "trades": trades,
        }
