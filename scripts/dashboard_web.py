"""Web dashboard — real-time bot monitoring with clean UI.

Run with: python scripts/dashboard_web.py
Opens at: http://localhost:8050

Auto-refreshes every 10 seconds. Shows:
- Bot status (running/stopped)
- Portfolio summary (balance, P&L, fees)
- Open positions with exit strategies
- Recent trades log
- Claude Code review log
- Strategy review log
"""

import json
import sqlite3
import subprocess
from datetime import UTC, datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

DB_PATH = Path("data/trades.db")
REPORTS_DIR = Path("data/reports")
LOGS_DIR = Path("data/logs")
PORT = 8050


def get_bot_status() -> dict[str, Any]:
    """Check if bot is running."""
    result = subprocess.run(["pgrep", "-f", "paper-trade"], capture_output=True, text=True)
    pids = result.stdout.strip().split("\n") if result.stdout.strip() else []
    return {"running": bool(pids), "pid": pids[0] if pids else None}


def get_trades() -> list[dict[str, Any]]:
    """Get recent trades from database."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT 20").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_positions() -> list[dict[str, Any]]:
    """Get open positions from trade log."""
    path = REPORTS_DIR / "trade_log.json"
    if not path.exists():
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("open_positions", [])
    except (json.JSONDecodeError, OSError):
        return []


def get_scan_summary() -> dict[str, Any]:
    """Get latest market scan summary."""
    path = REPORTS_DIR / "market_scan.json"
    if not path.exists():
        return {"timestamp": "N/A", "opportunities": 0}
    try:
        with open(path) as f:
            data = json.load(f)
        return {
            "timestamp": data.get("timestamp", "N/A")[:19],
            "total_scanned": data.get("total_markets_scanned", 0),
            "opportunities": len(data.get("opportunities", [])),
        }
    except (json.JSONDecodeError, OSError):
        return {"timestamp": "N/A", "opportunities": 0}


def get_review_log(limit: int = 10) -> list[str]:
    """Get recent Claude review entries."""
    path = LOGS_DIR / "claude_review.log"
    if not path.exists():
        return []
    lines = path.read_text().strip().split("\n")
    # Filter to compact log lines (not the big first review)
    compact = [line for line in lines if line.startswith("2026-")]
    return compact[-limit:]


def get_strategy_review() -> str:
    """Get latest strategy review."""
    path = LOGS_DIR / "strategy_review.log"
    if not path.exists():
        return "No strategy review yet."
    content = path.read_text().strip()
    # Get last review block
    blocks = content.split("=====")
    if len(blocks) >= 2:
        return blocks[-2].strip()[:500]
    return content[:500]


def get_bot_log(limit: int = 15) -> list[str]:
    """Get recent bot log lines."""
    path = LOGS_DIR / "bot.log"
    if not path.exists():
        return []
    lines = path.read_text().strip().split("\n")
    return lines[-limit:]


def get_performance() -> dict[str, Any]:
    """Get performance metrics from database."""
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    snap = conn.execute(
        "SELECT * FROM performance_snapshots ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    trade_count = conn.execute("SELECT COUNT(*) as c FROM trades").fetchone()
    total_fees = conn.execute("SELECT COALESCE(SUM(fees), 0) as f FROM trades").fetchone()
    conn.close()
    return {
        "total_trades": trade_count["c"] if trade_count else 0,
        "total_fees": total_fees["f"] if total_fees else 0,
        "snapshot": dict(snap) if snap else None,
    }


def render_html() -> str:
    """Render the full dashboard HTML."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    status = get_bot_status()
    trades = get_trades()
    get_positions()
    scan = get_scan_summary()
    reviews = get_review_log()
    strategy = get_strategy_review()
    perf = get_performance()
    bot_log = get_bot_log()

    status_color = "#22c55e" if status["running"] else "#ef4444"
    status_text = f"RUNNING (PID {status['pid']})" if status["running"] else "STOPPED"

    # Build trades table
    trades_html = ""
    for t in trades:
        ts = (t.get("timestamp") or "?")[:16]
        strat = t.get("strategy_used") or "-"
        side = t.get("direction") or "?"
        price = float(t.get("price") or 0)
        size = float(t.get("size") or 0)
        fees = float(t.get("fees") or 0)
        reasoning = (t.get("reasoning") or "")[:60]
        side_color = "#22c55e" if side == "BUY" else "#ef4444"
        trades_html += f"""
        <tr>
            <td>{ts}</td>
            <td>{strat}</td>
            <td style="color:{side_color};font-weight:bold">{side}</td>
            <td>${price:.3f}</td>
            <td>{size:.0f}</td>
            <td>${fees:.2f}</td>
            <td class="reasoning">{reasoning}</td>
        </tr>"""

    # Build reviews list
    reviews_html = ""
    for r in reviews:
        reviews_html += f"<div class='review-line'>{r}</div>"

    # Build bot log
    log_html = ""
    for line in bot_log:
        # Strip ANSI codes
        import re

        clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
        if "error" in clean.lower():
            log_html += f"<div class='log-error'>{clean[:120]}</div>"
        elif "warning" in clean.lower():
            log_html += f"<div class='log-warn'>{clean[:120]}</div>"
        else:
            log_html += f"<div class='log-info'>{clean[:120]}</div>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="10">
    <title>Polymarket Bot Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{ color: #f8fafc; margin-bottom: 5px; font-size: 24px; }}
        .subtitle {{ color: #94a3b8; margin-bottom: 20px; font-size: 14px; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }}
        .card {{
            background: #1e293b;
            border-radius: 10px;
            padding: 16px;
            border: 1px solid #334155;
        }}
        .card-label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
        .card-value {{ font-size: 28px; font-weight: bold; margin-top: 4px; }}
        .section {{
            background: #1e293b;
            border-radius: 10px;
            padding: 16px;
            border: 1px solid #334155;
            margin-bottom: 16px;
        }}
        .section-title {{
            color: #f8fafc;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #334155;
        }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ text-align: left; color: #94a3b8; font-weight: 500; padding: 8px 6px;
              border-bottom: 1px solid #334155; font-size: 11px; text-transform: uppercase; }}
        td {{ padding: 8px 6px; border-bottom: 1px solid #1e293b; }}
        tr:hover {{ background: #334155; }}
        .reasoning {{ color: #94a3b8; font-size: 12px; max-width: 200px;
                      overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .review-line {{
            font-size: 12px;
            padding: 6px 0;
            border-bottom: 1px solid #334155;
            color: #cbd5e1;
            line-height: 1.5;
        }}
        .log-info {{ font-size: 11px; color: #94a3b8; padding: 2px 0; font-family: monospace; }}
        .log-warn {{ font-size: 11px; color: #f59e0b; padding: 2px 0; font-family: monospace; }}
        .log-error {{ font-size: 11px; color: #ef4444; padding: 2px 0; font-family: monospace; }}
        .status-dot {{
            display: inline-block;
            width: 10px; height: 10px;
            border-radius: 50%;
            margin-right: 6px;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    </style>
</head>
<body>
    <h1>Polymarket Trading Bot</h1>
    <div class="subtitle">Paper Trading Mode &bull; {now} &bull; Auto-refreshes every 10s</div>

    <div class="grid">
        <div class="card">
            <div class="card-label">Status</div>
            <div class="card-value">
                <span class="status-dot" style="background:{status_color}"></span>
                <span style="color:{status_color};font-size:18px">{status_text}</span>
            </div>
        </div>
        <div class="card">
            <div class="card-label">Total Trades</div>
            <div class="card-value">{perf.get("total_trades", 0)}</div>
        </div>
        <div class="card">
            <div class="card-label">Markets Scanned</div>
            <div class="card-value">{scan.get("total_scanned", 0)}</div>
        </div>
        <div class="card">
            <div class="card-label">Total Fees Paid</div>
            <div class="card-value" style="color:#f59e0b">${perf.get("total_fees", 0):.2f}</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Recent Trades</div>
        {
        f'''<table>
            <tr>
                <th>Time</th><th>Strategy</th><th>Side</th>
                <th>Price</th><th>Shares</th><th>Fees</th><th>Reasoning</th>
            </tr>
            {trades_html}
        </table>'''
        if trades_html
        else '<div style="color:#94a3b8;padding:20px;text-align:center">No trades yet</div>'
    }
    </div>

    <div class="two-col">
        <div class="section">
            <div class="section-title">Claude Code Analysis Log</div>
            {reviews_html if reviews_html else '<div style="color:#94a3b8">No reviews yet</div>'}
        </div>
        <div class="section">
            <div class="section-title">Bot Log (last 15 lines)</div>
            {log_html if log_html else '<div style="color:#94a3b8">No logs yet</div>'}
        </div>
    </div>

    <div class="section">
        <div class="section-title">Latest Strategy Review</div>
        <pre style="font-size:12px;color:#cbd5e1;white-space:pre-wrap">{strategy}</pre>
    </div>
</body>
</html>"""


class DashboardHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves the dashboard."""

    def do_GET(self) -> None:
        """Serve dashboard HTML."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = render_html()
        self.wfile.write(html.encode())

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default request logging."""
        pass


def main() -> None:
    """Start the dashboard web server."""
    print(f"Dashboard starting at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.\n")

    server = HTTPServer(("", PORT), DashboardHandler)
    try:
        import webbrowser

        webbrowser.open(f"http://localhost:{PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
