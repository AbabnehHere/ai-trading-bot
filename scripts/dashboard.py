"""Live dashboard — shows bot status, positions, trades, and performance.

Run with: python scripts/dashboard.py
Auto-refreshes every 30 seconds. Press Ctrl+C to exit.
"""

import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path

DB_PATH = Path("data/trades.db")


def clear_screen() -> None:
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")


def print_header() -> None:
    """Print dashboard header."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    print("=" * 70)
    print("  POLYMARKET BOT — LIVE DASHBOARD")
    print(f"  {now}")
    print("=" * 70)


def print_performance(conn: sqlite3.Connection) -> None:
    """Print performance metrics."""
    print("\n--- PERFORMANCE ---")

    trades = conn.execute(
        "SELECT * FROM trades WHERE status = 'filled' ORDER BY timestamp DESC"
    ).fetchall()

    if not trades:
        print("  No trades yet. Bot is scanning for opportunities...")
        return

    total = len(trades)
    buy_trades = [t for t in trades if t["direction"] == "BUY"]
    sell_trades = [t for t in trades if t["direction"] == "SELL"]

    # Calculate rough P&L from filled trades
    sum(t["price"] * t["size"] + t["fees"] for t in buy_trades)
    sum(t["price"] * t["size"] - t["fees"] for t in sell_trades)
    total_fees = sum(t["fees"] for t in trades)

    print(f"  Total trades:    {total}")
    print(f"  Buy orders:      {len(buy_trades)}")
    print(f"  Sell orders:     {len(sell_trades)}")
    print(f"  Total fees paid: ${total_fees:.2f}")

    # Latest snapshot
    snap = conn.execute(
        "SELECT * FROM performance_snapshots ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    if snap:
        print(f"  Win rate:        {snap['win_rate']:.0%}")
        print(f"  Total P&L:       ${snap['total_pnl']:.2f}")
        print(f"  Sharpe ratio:    {snap['sharpe_ratio']:.2f}")
        print(f"  Max drawdown:    {snap['max_drawdown']:.1%}")


def print_recent_trades(conn: sqlite3.Connection, limit: int = 10) -> None:
    """Print recent trades."""
    print(f"\n--- RECENT TRADES (last {limit}) ---")

    trades = conn.execute(
        "SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()

    if not trades:
        print("  No trades yet.")
        return

    header = f"  {'Time':<20} {'Strategy':<12} {'Side':<5} {'Price':>6} {'Size':>6} {'Fees':>5}"
    print(header)
    print(f"  {'-' * (len(header) - 2)}")

    for t in trades:
        ts = (t["timestamp"] or "?")[:16]
        strategy = (t["strategy_used"] or "?")[:12]
        side = t["direction"] or "?"
        price = t["price"] or 0
        size = t["size"] or 0
        fees = t["fees"] or 0
        print(f"  {ts:<20} {strategy:<12} {side:<5} ${price:.3f} {size:>6.1f} ${fees:.2f}")


def print_positions(conn: sqlite3.Connection) -> None:
    """Print open positions."""
    print("\n--- OPEN POSITIONS ---")

    positions = conn.execute("SELECT * FROM positions WHERE current_size > 0").fetchall()

    if not positions:
        print("  No open positions.")
        return

    for p in positions:
        print(
            f"  {p['market_id'][:30]}: "
            f"{p['side']} {p['current_size']:.1f} shares "
            f"@ ${p['avg_entry_price']:.3f}"
        )


def print_lessons(conn: sqlite3.Connection, limit: int = 5) -> None:
    """Print recent lessons."""
    print(f"\n--- RECENT LESSONS (last {limit}) ---")

    lessons = conn.execute(
        "SELECT * FROM trade_lessons ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()

    if not lessons:
        print("  No lessons yet.")
        return

    for les in lessons:
        print(f"  [{les['what_went_wrong_or_right']}] {les['lesson_learned']}")


def print_strategy_changes(conn: sqlite3.Connection, limit: int = 5) -> None:
    """Print recent strategy parameter changes."""
    print(f"\n--- STRATEGY CHANGES (last {limit}) ---")

    changes = conn.execute(
        "SELECT * FROM strategy_parameters ORDER BY changed_at DESC LIMIT ?",
        (limit,),
    ).fetchall()

    if not changes:
        print("  No parameter changes yet.")
        return

    for c in changes:
        ts = c["changed_at"][:19] if c["changed_at"] else "?"
        print(f"  [{ts}] {c['parameter_name']}: {c['previous_value']} → {c['current_value']}")
        if c["reason_for_change"]:
            print(f"    Reason: {c['reason_for_change'][:70]}")


def print_nightly_review() -> None:
    """Print latest nightly review."""
    review_path = Path("data/logs/nightly_review.log")
    if review_path.exists():
        content = review_path.read_text()
        # Show last review only
        reviews = content.split("=====")
        if len(reviews) >= 2:
            latest = reviews[-2].strip()
            print("\n--- LATEST NIGHTLY REVIEW ---")
            for line in latest.split("\n")[:8]:
                print(f"  {line}")
    else:
        print("\n--- NIGHTLY REVIEW ---")
        print("  No review yet.")


def main() -> None:
    """Run the dashboard."""
    if not DB_PATH.exists():
        print("Database not found. Run 'make setup-db' first.")
        return

    print("Dashboard starting... Press Ctrl+C to exit.\n")

    try:
        while True:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row

            clear_screen()
            print_header()
            print_performance(conn)
            print_recent_trades(conn)
            print_positions(conn)
            print_lessons(conn)
            print_strategy_changes(conn)
            print_nightly_review()

            print(f"\n{'─' * 70}")
            print("  Refreshing in 30s... Press Ctrl+C to exit.")

            conn.close()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\nDashboard closed.")


if __name__ == "__main__":
    main()
