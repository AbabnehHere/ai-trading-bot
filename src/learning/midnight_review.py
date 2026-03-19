"""Midnight strategy review — Claude analyzes the day's performance.

Runs at midnight UTC daily. Reviews all trades, performance metrics,
and lessons learned. Suggests parameter adjustments and can pause
trading if performance is deteriorating.
"""

import sqlite3
from typing import Any

from src.data.llm_analyzer import LLMAnalyzer
from src.learning.lessons import LessonExtractor
from src.learning.performance import PerformanceTracker
from src.learning.strategy_tuner import StrategyTuner
from src.learning.trade_journal import TradeJournal
from src.utils.helpers import now_iso
from src.utils.logger import get_logger
from src.utils.notifications import NotificationManager

logger = get_logger(__name__)

DB_PATH = "data/trades.db"


class MidnightReview:
    """Runs comprehensive daily strategy review using Claude."""

    def __init__(
        self,
        performance: PerformanceTracker,
        journal: TradeJournal,
        lessons: LessonExtractor,
        tuner: StrategyTuner,
        notifier: NotificationManager,
        current_config: dict[str, Any],
    ) -> None:
        """Initialize the midnight review.

        Args:
            performance: Performance tracker for metrics.
            journal: Trade journal for history.
            lessons: Lesson extractor for past insights.
            tuner: Strategy tuner to apply changes.
            notifier: Notification manager for alerts.
            current_config: Current strategy configuration.
        """
        self._performance = performance
        self._journal = journal
        self._lessons = lessons
        self._tuner = tuner
        self._notifier = notifier
        self._config = current_config
        self._llm = LLMAnalyzer()

    def run_review(self) -> dict[str, Any]:
        """Execute the midnight strategy review.

        1. Gather performance metrics
        2. Gather recent trades and lessons
        3. Ask Claude to analyze everything
        4. Apply suggested changes (conservatively)
        5. Log and notify

        Returns:
            Review results including analysis and any changes made.
        """
        logger.info("Starting midnight strategy review")

        # 1. Gather data
        metrics = self._performance.calculate_metrics()
        recent_trades = self._journal.get_trade_history(limit=50)
        recent_lessons = self._lessons.extract_lessons(last_n_trades=30)

        # 2. If LLM is available, use Claude for analysis
        if self._llm.is_available:
            review = self._llm.midnight_strategy_review(
                performance_metrics=metrics,
                recent_trades=recent_trades,
                current_config=self._config,
                lessons=recent_lessons,
            )
        else:
            # Fallback to rule-based review
            review = self._rule_based_review(metrics)

        # 3. Handle pause recommendation
        if review.get("should_pause", False):
            logger.warning(
                "MIDNIGHT REVIEW: Recommending PAUSE",
                reason=review.get("pause_reason", "Performance concerns"),
            )
            self._notifier.send_risk_alert(
                "strategy_pause",
                f"Midnight review recommends pausing: {review.get('pause_reason', 'unknown')}",
            )

        # 4. Apply suggestions (conservatively)
        suggestions = review.get("suggestions", [])
        applied = []
        if suggestions and metrics.get("total_trades", 0) >= 10:
            # Only apply max 2 changes per review
            for suggestion in suggestions[:2]:
                if self._validate_suggestion(suggestion):
                    applied.append(suggestion)
                    logger.info(
                        "Applying strategy adjustment",
                        parameter=suggestion.get("parameter"),
                        old=suggestion.get("current"),
                        new=suggestion.get("suggested"),
                        reason=suggestion.get("reason"),
                    )

            if applied:
                self._tuner.apply_adjustments(applied)

        # 5. Save review to database
        self._save_review(review, applied)

        # 6. Notify
        self._send_review_notification(review, applied, metrics)

        result = {
            "timestamp": now_iso(),
            "analysis": review.get("analysis", ""),
            "should_pause": review.get("should_pause", False),
            "suggestions": suggestions,
            "applied": applied,
            "metrics": metrics,
        }

        logger.info(
            "Midnight review complete",
            suggestions=len(suggestions),
            applied=len(applied),
            should_pause=review.get("should_pause", False),
        )

        return result

    def _rule_based_review(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Fallback rule-based review when LLM is unavailable."""
        suggestions = []
        should_pause = False
        analysis = "Rule-based review (Claude unavailable). "

        total = metrics.get("total_trades", 0)
        win_rate = metrics.get("win_rate", 0)
        drawdown = metrics.get("max_drawdown", 0)

        if total >= 10 and win_rate < 0.40:
            should_pause = True
            analysis += f"Win rate critically low ({win_rate:.0%}). "

        if drawdown > 0.08:
            should_pause = True
            analysis += f"Drawdown concerning ({drawdown:.1%}). "

        if total >= 10 and win_rate < 0.50:
            suggestions.append(
                {
                    "parameter": "min_edge_threshold",
                    "current": self._config.get("min_edge_threshold", 0.08),
                    "suggested": min(
                        self._config.get("min_edge_threshold", 0.08) + 0.01,
                        0.15,
                    ),
                    "reason": f"Win rate {win_rate:.0%} below 50%",
                }
            )

        if not suggestions and not should_pause:
            analysis += "Performance within acceptable range. No changes needed."

        return {
            "analysis": analysis,
            "should_pause": should_pause,
            "pause_reason": "Low performance" if should_pause else "",
            "suggestions": suggestions,
        }

    def _validate_suggestion(self, suggestion: dict[str, Any]) -> bool:
        """Validate a parameter adjustment is safe to apply."""
        param = suggestion.get("parameter", "")
        new_val = suggestion.get("suggested")
        if new_val is None:
            return False

        # Safety bounds
        bounds: dict[str, tuple[float, float]] = {
            "min_edge_threshold": (0.03, 0.20),
            "confidence_required": (0.4, 0.95),
            "max_position_pct": (0.01, 0.05),
            "kelly_fraction": (0.1, 0.5),
            "stop_loss_pct": (0.15, 0.50),
        }

        if param in bounds:
            low, high = bounds[param]
            return low <= float(new_val) <= high

        return False

    def _save_review(self, review: dict[str, Any], applied: list[dict[str, Any]]) -> None:
        """Save review results to the database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                """INSERT INTO strategy_parameters
                   (parameter_name, current_value, previous_value,
                    changed_at, reason_for_change)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    "_midnight_review",
                    str(len(applied)) + " changes applied",
                    review.get("analysis", "")[:200],
                    now_iso(),
                    f"Suggestions: {len(review.get('suggestions', []))}, "
                    f"Pause: {review.get('should_pause', False)}",
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("Failed to save review to DB", error=str(e))

    def _send_review_notification(
        self,
        review: dict[str, Any],
        applied: list[dict[str, Any]],
        metrics: dict[str, Any],
    ) -> None:
        """Send review summary via notifications."""
        changes_text = ""
        if applied:
            changes_text = "\n".join(
                f"  {a['parameter']}: {a['current']} → {a['suggested']}" for a in applied
            )
            changes_text = f"\n\nChanges Applied:\n{changes_text}"

        self._notifier.send_daily_summary(
            {
                "total_balance": metrics.get("total_pnl", 0),
                "total_pnl": metrics.get("total_pnl", 0),
                "win_rate": metrics.get("win_rate", 0),
                "open_positions": 0,
                "trades_today": metrics.get("total_trades", 0),
            }
        )
