"""Paper trading with live data.

Simulates trading with live market data but without placing real orders.
Used to validate strategies in real-time before live deployment.
"""

import time
from typing import Any

from src.core.market_analyzer import MarketAnalyzer
from src.core.order_manager import OrderManager
from src.core.position_manager import PositionManager
from src.core.risk_manager import RiskManager
from src.data.market_data import MarketDataClient
from src.learning.performance import PerformanceTracker
from src.learning.trade_journal import TradeJournal
from src.strategy.base_strategy import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PaperTrader:
    """Simulates trading with live market data."""

    def __init__(
        self,
        strategies: list[BaseStrategy],
        initial_balance: float = 1000.0,
        cycle_interval: int = 300,
        risk_config: dict[str, Any] | None = None,
        market_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the paper trader.

        Args:
            strategies: List of strategies to use.
            initial_balance: Starting simulated balance.
            cycle_interval: Seconds between trading cycles.
            risk_config: Risk management configuration.
            market_config: Market filtering configuration.
        """
        self._cycle_interval = cycle_interval
        self._running = False

        # Initialize all components
        self._market_data = MarketDataClient()
        self._positions = PositionManager(self._market_data, initial_balance, paper=True)
        self._risk_manager = RiskManager(self._positions, risk_config)
        self._order_manager = OrderManager(paper=True)
        self._analyzer = MarketAnalyzer(self._market_data, strategies, market_config)
        self._journal = TradeJournal()
        self._performance = PerformanceTracker()
        self._trade_count = 0

    def start(self) -> None:
        """Start paper trading session."""
        self._running = True
        logger.info("Paper trading started", balance=self._positions.get_cash_balance())

        while self._running:
            try:
                self._run_cycle()
            except KeyboardInterrupt:
                logger.info("Paper trading interrupted by user")
                break
            except Exception as e:
                logger.error("Paper trading cycle error", error=str(e))

            time.sleep(self._cycle_interval)

        self.stop()

    def stop(self) -> None:
        """Stop paper trading session and generate report."""
        self._running = False
        performance = self.get_performance()
        logger.info("Paper trading stopped", **performance)

    def _run_cycle(self) -> None:
        """Execute one paper trading cycle."""
        # 1. Scan markets
        candidates = self._analyzer.scan_markets()
        if not candidates:
            return

        # 2. Find opportunities
        signals = self._analyzer.find_opportunities(candidates)

        # 3. Process signals
        for signal in signals:
            # Calculate position size
            size_usd = self._risk_manager.calculate_position_size(signal.confidence, signal.price)
            if size_usd <= 0:
                continue

            shares = size_usd / signal.price if signal.price > 0 else 0

            # Run risk checks
            check = self._risk_manager.check_trade(
                signal.market_id, signal.side, shares, signal.price
            )
            if not check.approved:
                logger.info("Paper trade rejected", reason=check.reason)
                continue

            # Execute paper trade
            self._order_manager.place_order(
                token_id=signal.token_id,
                market_id=signal.market_id,
                side=signal.side,
                size=shares,
                price=signal.price,
                strategy=signal.strategy_name,
                reasoning=signal.reasoning,
            )

            # Update positions
            self._positions.record_fill(
                signal.market_id, signal.token_id, signal.side, shares, signal.price
            )
            self._risk_manager.record_trade()
            self._trade_count += 1

            logger.info(
                "Paper trade executed",
                market_id=signal.market_id,
                side=signal.side,
                price=signal.price,
                size=shares,
                strategy=signal.strategy_name,
            )

        # 4. Log performance
        balance = self._positions.get_portfolio_value()
        logger.info(
            "Paper trading cycle complete",
            balance=f"${balance:.2f}",
            positions=self._positions.get_position_count(),
            trades=self._trade_count,
        )

    def get_performance(self) -> dict[str, Any]:
        """Get current paper trading performance.

        Returns:
            Performance metrics from the paper trading session.
        """
        balance = self._positions.get_portfolio_value()
        cash = self._positions.get_cash_balance()
        return {
            "total_balance": balance,
            "cash": cash,
            "positions": self._positions.get_position_count(),
            "total_trades": self._trade_count,
            "drawdown": self._positions.get_drawdown(),
        }
