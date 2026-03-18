"""Export trade history to CSV."""

import csv
import sqlite3
import sys
from pathlib import Path


def main() -> None:
    """Export all trade records from the database to a CSV file."""
    db_path = Path("data/trades.db")
    if not db_path.exists():
        print("Database not found. Run 'make setup-db' first.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM trades ORDER BY timestamp DESC")
    trades = cursor.fetchall()
    conn.close()

    if not trades:
        print("No trades found in database.")
        sys.exit(0)

    output_path = Path("data/trades_export.csv")
    columns = trades[0].keys()

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for trade in trades:
            writer.writerow(dict(trade))

    print(f"Exported {len(trades)} trades to {output_path}")


if __name__ == "__main__":
    main()
