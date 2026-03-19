"""Main bot orchestrator — coordinates all components.

The TradingBot class is the central coordinator that ties together
market analysis, strategy execution, risk management, and order management.
"""

import time
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]

from src.core.market_analyzer import MarketAnalyzer
from src.core.order_manager import OrderManager
from src.core.position_manager import PositionManager
from src.core.risk_manager import RiskManager
from src.data.market_data import MarketDataClient
from src.learning.lessons import LessonExtractor
from src.learning.midnight_review import MidnightReview
from src.learning.performance import PerformanceTracker
from src.learning.strategy_tuner import StrategyTuner
from src.learning.trade_journal import TradeJournal
from src.reporting.market_reporter import MarketReporter
from src.strategy.convergence import ConvergenceStrategy
from src.strategy.edge_finder import EdgeFinder
from src.strategy.news_reactor import NewsReactor
from src.utils.config_loader import ConfigLoader
from src.utils.logger import get_logger
from src.utils.notifications import NotificationManager

logger = get_logger(__name__)


class TradingBot:
    """Main trading bot orchestrator.

    Coordinates the flow: data → analysis → strategy → risk check → execution.
    """

    def __init__(self, config_path: str = "config/settings.yaml", paper: bool = True) -> None:
        """Initialize the trading bot.

        Args:
            config_path: Path to the YAML configuration file.
            paper: If True, run in paper trading mode (no real orders).
        """
        self._paper = paper
        self._running = False
        self._config = ConfigLoader(config_path)

        # Get config sections
        bot_cfg = self._config.get("bot", {})
        trading_cfg = self._config.get("trading", {})
        market_cfg = self._config.get("markets", {})

        self._cycle_interval = bot_cfg.get("cycle_interval_seconds", 300)

        # Initialize strategies
        edge_cfg = self._config.get("strategy.edge_detection", {})
        news_cfg = self._config.get("strategy.news_reactive", {})
        conv_cfg = self._config.get("strategy.convergence", {})

        strategies = [
            EdgeFinder(edge_cfg if isinstance(edge_cfg, dict) else {}),
            NewsReactor(news_cfg if isinstance(news_cfg, dict) else {}),
            ConvergenceStrategy(conv_cfg if isinstance(conv_cfg, dict) else {}),
        ]

        # Initialize core components
        self._market_data = MarketDataClient()
        self._positions = PositionManager(
            self._market_data,
            initial_balance=1000.0,
            paper=paper,
        )
        self._risk_manager = RiskManager(self._positions, self._config.get("risk", {}))
        self._order_manager = OrderManager(paper=paper)
        self._analyzer = MarketAnalyzer(self._market_data, strategies, market_cfg)

        # Initialize learning components
        self._journal = TradeJournal()
        self._performance = PerformanceTracker()
        self._lessons = LessonExtractor()
        self._tuner = StrategyTuner(
            self._performance,
            review_interval=trading_cfg.get("review_interval", 20),
        )

        # Market reporter — writes data for Claude Code to review
        self._reporter = MarketReporter(self._market_data)

        # Notifications
        self._notifier = NotificationManager()

        # Midnight review
        self._midnight_review = MidnightReview(
            performance=self._performance,
            journal=self._journal,
            lessons=self._lessons,
            tuner=self._tuner,
            notifier=self._notifier,
            current_config=self._config.get_all(),
        )

        # Scheduler for midnight review
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            self._run_midnight_review,
            "cron",
            hour=0,
            minute=0,
            id="midnight_review",
        )

        mode_str = "PAPER" if paper else "LIVE"
        logger.info(f"TradingBot initialized in {mode_str} mode")

    def run(self) -> None:
        """Start the main trading loop."""
        self._running = True
        self._scheduler.start()
        mode = "paper" if self._paper else "live"
        logger.info(
            f"Bot started in {mode} mode",
            interval=self._cycle_interval,
            midnight_review="scheduled at 00:00 UTC",
        )

        while self._running:
            try:
                result = self._trading_cycle()
                logger.info("Cycle complete", **result)
            except KeyboardInterrupt:
                logger.info("Bot interrupted by user")
                break
            except Exception as e:
                logger.error("Trading cycle error", error=str(e))
                self._notifier.send_error_alert(str(e), "trading_cycle")

            time.sleep(self._cycle_interval)

        self.shutdown()

    def shutdown(self) -> None:
        """Gracefully shut down the bot."""
        self._running = False
        self._scheduler.shutdown(wait=False)
        balance = self._positions.get_portfolio_value()
        self._performance.save_snapshot(balance, 0.0, paper=self._paper)
        self._market_data.close()
        self._notifier.close()
        logger.info("Bot shut down", final_balance=f"${balance:.2f}")

    def _run_midnight_review(self) -> None:
        """Execute the midnight strategy review (called by scheduler)."""
        try:
            logger.info("Midnight strategy review starting")
            result = self._midnight_review.run_review()

            if result.get("should_pause"):
                logger.warning(
                    "MIDNIGHT REVIEW RECOMMENDS PAUSING",
                    analysis=result.get("analysis", ""),
                )
                # Don't auto-pause — just alert. User must decide.

            applied = result.get("applied", [])
            if applied:
                # Update the live config with applied changes
                for change in applied:
                    param = change.get("parameter", "")
                    new_val = change.get("suggested")
                    if param and new_val is not None:
                        logger.info(
                            "Config updated by midnight review",
                            parameter=param,
                            new_value=new_val,
                        )

            logger.info(
                "Midnight review complete",
                analysis=result.get("analysis", "")[:100],
                changes=len(applied),
            )
        except Exception as e:
            logger.error("Midnight review failed", error=str(e))
            self._notifier.send_error_alert(str(e), "midnight_review")

    def _trading_cycle(self) -> dict[str, Any]:
        """Execute one full trading cycle: scan → analyze → trade."""
        result: dict[str, Any] = {"trades": 0, "signals": 0, "rejected": 0}

        # 1. Check existing positions for stop-loss / take-profit
        self._check_existing_positions()

        # 2. Check for trade signals from Claude Code
        claude_signals = self._reporter.read_trade_signals()
        for sig in claude_signals:
            self._execute_claude_signal(sig)
            result["trades"] += 1

        # 3. Scan for new opportunities
        candidates = self._analyzer.scan_markets()
        result["markets_scanned"] = len(candidates)

        # 4. Write market scan report for Claude Code
        self._reporter.write_market_scan(candidates)

        # 5. Find opportunities via built-in strategies
        signals = self._analyzer.find_opportunities(candidates)
        result["signals"] = len(signals)

        # 4. Process each signal
        for signal in signals:
            size_usd = self._risk_manager.calculate_position_size(signal.confidence, signal.price)
            if size_usd <= 0:
                result["rejected"] += 1
                continue

            shares = size_usd / signal.price if signal.price > 0 else 0

            check = self._risk_manager.check_trade(
                signal.market_id, signal.side, shares, signal.price
            )
            if not check.approved:
                result["rejected"] += 1
                continue

            # Execute trade
            try:
                self._order_manager.place_order(
                    token_id=signal.token_id,
                    market_id=signal.market_id,
                    side=signal.side,
                    size=shares,
                    price=signal.price,
                    strategy=signal.strategy_name,
                    reasoning=signal.reasoning,
                )
                self._positions.record_fill(
                    signal.market_id, signal.token_id, signal.side, shares, signal.price
                )
                self._risk_manager.record_trade()
                result["trades"] += 1

                # Notify
                self._notifier.send_trade_alert(
                    signal.market_id, signal.side, shares, signal.price, signal.strategy_name
                )

                # Check if strategy review is needed
                if self._tuner.should_review():
                    current_cfg = self._config.get_all()
                    suggestions = self._tuner.suggest_adjustments(current_cfg)
                    if suggestions:
                        self._tuner.apply_adjustments(suggestions)

            except Exception as e:
                logger.error("Trade execution failed", error=str(e))
                self._notifier.send_error_alert(str(e), f"trade_{signal.market_id}")

        result["balance"] = f"${self._positions.get_portfolio_value():.2f}"
        result["positions"] = self._positions.get_position_count()

        # Write trade log for Claude Code
        self._reporter.write_trade_log(
            trades=self._journal.get_recent_trades(20),
            positions=self._positions.get_positions(),
        )
        return result

    def _execute_claude_signal(self, signal: dict[str, Any]) -> None:
        """Execute a trade signal written by Claude Code.

        Claude Code writes signals to data/reports/signals.json.
        Format: {"market_id": "...", "token_id": "...", "side": "BUY",
                 "size": 10, "price": 0.50, "reasoning": "..."}
        """
        try:
            market_id = signal["market_id"]
            token_id = signal.get("token_id", "")
            side = signal.get("side", "BUY")
            size = float(signal.get("size", 0))
            price = float(signal.get("price", 0))
            reasoning = signal.get("reasoning", "Claude Code signal")

            if size <= 0 or price <= 0:
                logger.warning("Invalid Claude signal", signal=signal)
                return

            # Still run risk checks
            check = self._risk_manager.check_trade(market_id, side, size, price)
            if not check.approved:
                logger.warning(
                    "Claude signal rejected by risk manager",
                    reason=check.reason,
                )
                return

            self._order_manager.place_order(
                token_id=token_id,
                market_id=market_id,
                side=side,
                size=size,
                price=price,
                strategy="claude_code",
                reasoning=reasoning,
            )
            self._positions.record_fill(market_id, token_id, side, size, price)
            self._risk_manager.record_trade()
            logger.info(
                "Claude Code signal executed",
                market_id=market_id,
                side=side,
                size=size,
                price=price,
            )
        except Exception as e:
            logger.error("Failed to execute Claude signal", error=str(e))

    def _check_existing_positions(self) -> None:
        """Check existing positions for stop-loss and take-profit conditions."""
        for pos in self._positions.get_positions():
            try:
                token_id = pos["token_id"]
                market_id = pos["market_id"]
                mid = self._market_data.get_midpoint(token_id)
                pnl = self._positions.get_position_pnl(market_id, mid)
                pnl_pct = pnl["pnl_pct"]

                if self._risk_manager.check_stop_loss(pnl_pct):
                    logger.warning("Stop-loss triggered", market_id=market_id, pnl_pct=pnl_pct)
                    self._order_manager.place_order(
                        token_id=token_id,
                        market_id=market_id,
                        side="SELL",
                        size=pos["size"],
                        price=mid,
                        strategy="stop_loss",
                        reasoning=f"Stop-loss at {pnl_pct:.1%}",
                    )
                    self._positions.record_fill(market_id, token_id, "SELL", pos["size"], mid)
                    self._risk_manager.record_loss(abs(pnl["unrealized_pnl"]))

                elif self._risk_manager.check_take_profit(pnl_pct):
                    # Take partial profit (50% of position)
                    sell_size = pos["size"] * 0.5
                    logger.info("Take-profit triggered", market_id=market_id, pnl_pct=pnl_pct)
                    self._order_manager.place_order(
                        token_id=token_id,
                        market_id=market_id,
                        side="SELL",
                        size=sell_size,
                        price=mid,
                        strategy="take_profit",
                        reasoning=f"Partial take-profit at {pnl_pct:.1%}",
                    )
                    self._positions.record_fill(market_id, token_id, "SELL", sell_size, mid)

            except Exception as e:
                logger.warning(
                    "Position check failed", market_id=pos.get("market_id"), error=str(e)
                )
