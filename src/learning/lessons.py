"""Extract and store lessons from trades.

Analyzes trade outcomes to extract patterns and lessons that can
be used to improve future trading decisions.
"""

import sqlite3
from typing import Any

from src.utils.helpers import now_iso
from src.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = "data/trades.db"


class LessonExtractor:
    """Extracts actionable lessons from trade history."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        """Initialize the lesson extractor.

        Args:
            db_path: Path to the SQLite database.
        """
        self._db_path = db_path

    def analyze_trade(self, trade_id: int, actual_outcome: str) -> dict[str, Any]:
        """Analyze a completed trade and extract a lesson.

        Categorizes outcome as:
        - Good trade, good outcome: Edge was real, strategy worked
        - Good trade, bad outcome: Edge was real but low-probability event occurred
        - Bad trade, good outcome: Got lucky, reasoning was flawed
        - Bad trade, bad outcome: Reasoning was wrong and lost money

        Args:
            trade_id: ID of the trade to analyze.
            actual_outcome: What actually happened.

        Returns:
            Lesson dict with analysis.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT * FROM trades WHERE trade_id = ?", (trade_id,))
            trade = cursor.fetchone()
            if not trade:
                return {"error": "Trade not found"}
            trade = dict(trade)
        finally:
            conn.close()

        entry_price = float(trade.get("price", 0))
        fill_price = float(trade.get("fill_price", entry_price))
        pnl = float(trade.get("size", 0)) * (fill_price - entry_price)
        reasoning = trade.get("reasoning", "")
        profitable = pnl > 0
        good_reasoning = bool(reasoning and len(reasoning) > 10)

        if profitable and good_reasoning:
            category = "good_trade_good_outcome"
            lesson = "Strategy worked as expected. Reinforce this pattern."
        elif not profitable and good_reasoning:
            category = "good_trade_bad_outcome"
            lesson = "Edge was real but variance occurred. No parameter change needed."
        elif profitable and not good_reasoning:
            category = "bad_trade_good_outcome"
            lesson = "Got lucky — reasoning was weak. Tighten entry criteria."
        else:
            category = "bad_trade_bad_outcome"
            lesson = "Reasoning was flawed and lost money. Deep-dive required."

        lesson_data = {
            "trade_id": trade_id,
            "what_happened": actual_outcome,
            "what_was_expected": reasoning,
            "what_went_wrong_or_right": category,
            "lesson_learned": lesson,
            "pnl": pnl,
            "category": category,
        }

        # Store lesson in database
        self._save_lesson(lesson_data)
        return lesson_data

    def extract_lessons(self, last_n_trades: int = 20) -> list[dict[str, Any]]:
        """Analyze recent trades and extract aggregate lessons.

        Args:
            last_n_trades: Number of recent trades to analyze.

        Returns:
            List of lesson dicts with patterns identified.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                """SELECT * FROM trade_lessons
                   ORDER BY timestamp DESC LIMIT ?""",
                (last_n_trades,),
            )
            lessons = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

        return lessons

    def get_lessons_for_strategy(self, strategy_name: str) -> list[dict[str, Any]]:
        """Get lessons from trades using a specific strategy.

        Args:
            strategy_name: Name of the strategy.

        Returns:
            List of relevant lessons.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                """SELECT tl.* FROM trade_lessons tl
                   JOIN trades t ON tl.trade_id = t.trade_id
                   WHERE t.strategy_used = ?
                   ORDER BY tl.timestamp DESC""",
                (strategy_name,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _save_lesson(self, lesson: dict[str, Any]) -> None:
        """Save a lesson to the database."""
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute(
                """INSERT INTO trade_lessons
                   (trade_id, what_happened, what_was_expected,
                    what_went_wrong_or_right, lesson_learned,
                    parameter_adjustment_made, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    lesson.get("trade_id"),
                    lesson.get("what_happened", ""),
                    lesson.get("what_was_expected", ""),
                    lesson.get("what_went_wrong_or_right", ""),
                    lesson.get("lesson_learned", ""),
                    lesson.get("parameter_adjustment_made", ""),
                    now_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()
