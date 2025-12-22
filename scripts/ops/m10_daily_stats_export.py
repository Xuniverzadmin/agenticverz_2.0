#!/usr/bin/env python3
"""
M10 Daily Stats Exporter

Exports dead_letter_archive and replay_log sizes to CSV for historical trending.
Designed to run daily via cron or systemd timer.

Usage:
    # Export to default location
    python -m scripts.ops.m10_daily_stats_export

    # Custom output directory
    python -m scripts.ops.m10_daily_stats_export --output-dir /var/log/m10

    # JSON output (for monitoring integration)
    python -m scripts.ops.m10_daily_stats_export --json

Cron (daily at 00:05 UTC):
    5 0 * * * cd /root/agenticverz2.0 && DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend python3 -m scripts.ops.m10_daily_stats_export >> /var/log/m10_stats.log 2>&1

Output CSV format:
    timestamp,dead_letter_count,dead_letter_oldest_days,replay_log_count,replay_log_oldest_days,outbox_pending,outbox_processed,active_locks

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL (required)
    M10_STATS_OUTPUT_DIR: Output directory for CSV (default: /var/log/m10)
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

logger = logging.getLogger("m10.daily_stats")

DATABASE_URL = os.getenv("DATABASE_URL")
DEFAULT_OUTPUT_DIR = os.getenv("M10_STATS_OUTPUT_DIR", "/var/log/m10")


def collect_stats() -> dict:
    """Collect M10 table statistics."""
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dead_letter_count": 0,
        "dead_letter_oldest_days": 0,
        "replay_log_count": 0,
        "replay_log_oldest_days": 0,
        "outbox_pending": 0,
        "outbox_processed": 0,
        "active_locks": 0,
        "error": None,
    }

    if not DATABASE_URL:
        stats["error"] = "DATABASE_URL not configured"
        return stats

    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)

        with Session(engine) as session:
            # Dead letter stats
            result = session.execute(
                text(
                    """
                SELECT
                    COUNT(*) as count,
                    COALESCE(EXTRACT(DAY FROM NOW() - MIN(dead_lettered_at)), 0) as oldest_days
                FROM m10_recovery.dead_letter_archive
            """
                )
            )
            row = result.fetchone()
            stats["dead_letter_count"] = row[0] if row else 0
            stats["dead_letter_oldest_days"] = float(row[1]) if row and row[1] else 0

            # Replay log stats
            result = session.execute(
                text(
                    """
                SELECT
                    COUNT(*) as count,
                    COALESCE(EXTRACT(DAY FROM NOW() - MIN(replayed_at)), 0) as oldest_days
                FROM m10_recovery.replay_log
            """
                )
            )
            row = result.fetchone()
            stats["replay_log_count"] = row[0] if row else 0
            stats["replay_log_oldest_days"] = float(row[1]) if row and row[1] else 0

            # Outbox stats
            result = session.execute(
                text(
                    """
                SELECT
                    COUNT(*) FILTER (WHERE processed_at IS NULL) as pending,
                    COUNT(*) FILTER (WHERE processed_at IS NOT NULL) as processed
                FROM m10_recovery.outbox
            """
                )
            )
            row = result.fetchone()
            stats["outbox_pending"] = row[0] if row else 0
            stats["outbox_processed"] = row[1] if row else 0

            # Active locks
            result = session.execute(
                text(
                    """
                SELECT COUNT(*) FROM m10_recovery.distributed_locks
                WHERE expires_at > NOW()
            """
                )
            )
            row = result.fetchone()
            stats["active_locks"] = row[0] if row else 0

    except Exception as e:
        stats["error"] = str(e)
        logger.error(f"Failed to collect stats: {e}")

    return stats


def append_to_csv(stats: dict, output_dir: str) -> str:
    """Append stats to daily CSV file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Use date-based filename for easy rotation
    today = datetime.now(timezone.utc).strftime("%Y-%m")
    csv_file = output_path / f"m10_stats_{today}.csv"

    # Check if file exists to determine if we need headers
    write_header = not csv_file.exists()

    fieldnames = [
        "timestamp",
        "dead_letter_count",
        "dead_letter_oldest_days",
        "replay_log_count",
        "replay_log_oldest_days",
        "outbox_pending",
        "outbox_processed",
        "active_locks",
    ]

    with open(csv_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        # Write row (exclude error field)
        row = {k: v for k, v in stats.items() if k in fieldnames}
        writer.writerow(row)

    return str(csv_file)


def main():
    parser = argparse.ArgumentParser(
        description="Export M10 stats to CSV for historical trending"
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for CSV files (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output stats as JSON instead of writing to CSV",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    logger.info("Collecting M10 stats...")
    stats = collect_stats()

    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        if stats["error"]:
            print(f"ERROR: {stats['error']}")
            sys.exit(1)

        csv_file = append_to_csv(stats, args.output_dir)
        print(f"Stats appended to {csv_file}")
        print(f"  dead_letter_count: {stats['dead_letter_count']}")
        print(f"  replay_log_count: {stats['replay_log_count']}")
        print(f"  outbox_pending: {stats['outbox_pending']}")
        print(f"  outbox_processed: {stats['outbox_processed']}")
        print(f"  active_locks: {stats['active_locks']}")

    sys.exit(0 if not stats["error"] else 1)


if __name__ == "__main__":
    main()
