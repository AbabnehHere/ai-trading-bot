# TODO: Implement in Phase 3
"""Alert system for trade notifications and system alerts.

Supports Telegram notifications for trade executions, errors,
and daily performance summaries.
"""


class NotificationManager:
    """Manages notifications via Telegram and other channels."""

    def send_trade_alert(self, market: str, side: str, size: float, price: float) -> None:
        """Send a notification about a trade execution.

        Args:
            market: Market description.
            side: "BUY" or "SELL".
            size: Trade size.
            price: Execution price.
        """
        raise NotImplementedError("Phase 3")

    def send_error_alert(self, error: str, context: str) -> None:
        """Send a notification about an error.

        Args:
            error: Error message.
            context: Context about what was happening when the error occurred.
        """
        raise NotImplementedError("Phase 3")

    def send_daily_summary(self, metrics: dict[str, float]) -> None:
        """Send daily performance summary.

        Args:
            metrics: Dict of performance metrics.
        """
        raise NotImplementedError("Phase 3")
