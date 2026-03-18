"""Quick system health check."""

import os
import sqlite3
import sys
from pathlib import Path


def main() -> None:
    """Check API connectivity, database status, and system resources."""
    checks_passed = 0
    checks_failed = 0

    # Check 1: Environment variables
    print("--- Environment Variables ---")
    required_vars = ["POLYMARKET_API_KEY", "PRIVATE_KEY"]
    optional_vars = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]

    for var in required_vars:
        if os.getenv(var):
            print(f"  ✓ {var} is set")
            checks_passed += 1
        else:
            print(f"  ✗ {var} is NOT set (required)")
            checks_failed += 1

    for var in optional_vars:
        if os.getenv(var):
            print(f"  ✓ {var} is set")
        else:
            print(f"  ○ {var} is not set (optional)")

    # Check 2: Database
    print("\n--- Database ---")
    db_path = Path("data/trades.db")
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            print(f"  ✓ Database exists with {len(tables)} tables: {', '.join(tables)}")
            checks_passed += 1
        except Exception as e:
            print(f"  ✗ Database error: {e}")
            checks_failed += 1
    else:
        print("  ✗ Database not found — run 'make setup-db' first")
        checks_failed += 1

    # Check 3: Config files
    print("\n--- Configuration ---")
    config_files = [
        "config/settings.yaml",
        "config/risk_limits.yaml",
        "config/markets_watchlist.yaml",
    ]
    for cfg in config_files:
        if Path(cfg).exists():
            print(f"  ✓ {cfg}")
            checks_passed += 1
        else:
            print(f"  ✗ {cfg} not found")
            checks_failed += 1

    # Check 4: Data directories
    print("\n--- Data Directories ---")
    dirs = ["data/", "data/historical/", "data/logs/"]
    for d in dirs:
        if Path(d).exists():
            print(f"  ✓ {d}")
        else:
            print(f"  ✗ {d} not found")

    # Check 5: API connectivity
    print("\n--- API Connectivity ---")
    try:
        import httpx

        response = httpx.get("https://gamma-api.polymarket.com/markets?limit=1", timeout=10)
        if response.status_code == 200:
            print("  ✓ Polymarket API is reachable")
            checks_passed += 1
        else:
            print(f"  ✗ Polymarket API returned status {response.status_code}")
            checks_failed += 1
    except Exception as e:
        print(f"  ✗ Polymarket API unreachable: {e}")
        checks_failed += 1

    # Summary
    total = checks_passed + checks_failed
    print(f"\n--- Summary: {checks_passed}/{total} checks passed ---")
    if checks_failed > 0:
        print(f"  {checks_failed} check(s) failed — review above")
    else:
        print("  All checks passed! System is healthy.")

    sys.exit(0 if checks_failed == 0 else 1)


if __name__ == "__main__":
    main()
