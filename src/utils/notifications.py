"""Alert system for trade notifications and system alerts.

Supports Telegram notifications for trade executions, errors,
and daily performance summaries.
"""

import os
from typing import Any

import httpx

from src.utils.helpers import format_usd
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationManager:
    """Manages notifications via Telegram."""

    def __init__(self) -> None:
        """Initialize the notification manager."""
        self._telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self._enabled = bool(self._telegram_token and self._telegram_chat_id)
        self._http_client = httpx.Client(timeout=10.0)

        if not self._enabled:
            logger.info("Telegram notifications disabled — no bot token/chat ID configured")

    def send_trade_alert(
        self, market: str, side: str, size: float, price: float, strategy: str = ""
    ) -> None:
        """Send a notification about a trade execution.

        Args:
            market: Market description/question.
            side: "BUY" or "SELL".
            size: Trade size in shares.
            price: Execution price.
            strategy: Strategy that generated the trade.
        """
        cost = format_usd(size * price)
        msg = (
            f"{'🟢' if side == 'BUY' else '🔴'} *Trade Executed*\n"
            f"Market: {market[:80]}\n"
            f"Side: {side} | Size: {size:.1f} | Price: {price:.3f}\n"
            f"Cost: {cost}\n"
            f"Strategy: {strategy}"
        )
        self._send_telegram(msg)

    def send_error_alert(self, error: str, context: str) -> None:
        """Send a notification about an error.

        Args:
            error: Error message.
            context: Context about what was happening when the error occurred.
        """
        msg = f"⚠️ *Error*\nContext: {context}\nError: {error}"
        self._send_telegram(msg)

    def send_daily_summary(self, metrics: dict[str, Any]) -> None:
        """Send daily performance summary.

        Args:
            metrics: Dict of performance metrics.
        """
        pnl = metrics.get("total_pnl", 0)
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        msg = (
            f"{pnl_emoji} *Daily Summary*\n"
            f"Balance: {format_usd(metrics.get('total_balance', 0))}\n"
            f"P&L: {format_usd(pnl)}\n"
            f"Win Rate: {metrics.get('win_rate', 0):.0%}\n"
            f"Open Positions: {metrics.get('open_positions', 0)}\n"
            f"Trades Today: {metrics.get('trades_today', 0)}"
        )
        self._send_telegram(msg)

    def send_risk_alert(self, alert_type: str, details: str) -> None:
        """Send a risk management alert.

        Args:
            alert_type: Type of risk alert (e.g., "circuit_breaker", "daily_loss_limit").
            details: Details about the risk event.
        """
        msg = f"🚨 *Risk Alert: {alert_type}*\n{details}"
        self._send_telegram(msg)

    def _send_telegram(self, message: str) -> None:
        """Send a message via Telegram bot API."""
        if not self._enabled:
            logger.debug("Notification (disabled)", message=message[:100])
            return

        url = f"https://api.telegram.org/bot{self._telegram_token}/sendMessage"
        try:
            response = self._http_client.post(
                url,
                json={
                    "chat_id": self._telegram_chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                },
            )
            if response.status_code != 200:
                logger.warning("Telegram send failed", status=response.status_code)
        except Exception as e:
            logger.warning("Telegram notification failed", error=str(e))

    def close(self) -> None:
        """Close the HTTP client."""
        self._http_client.close()
