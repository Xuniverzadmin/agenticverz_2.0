#!/usr/bin/env python3
"""
C2 Prediction Expiry Cleanup Job
=================================
Deletes expired predictions from prediction_events table.

Reference: PIN-222 (C2 Implementation Specification)
Invariant: I-C2-5 (Delete Safety) - predictions are disposable

Usage:
    python3 c2_prediction_expiry_cleanup.py [--dry-run] [--verbose]

Environment:
    DATABASE_URL - Required. Postgres connection string.

Scheduling:
    Run via cron every 5 minutes:
    */5 * * * * /usr/bin/python3 /root/agenticverz2.0/scripts/ops/c2_prediction_expiry_cleanup.py >> /var/log/aos/c2_cleanup.log 2>&1
"""

import argparse
import os
import sys
from datetime import datetime, timezone

# Add backend to path for guard import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

# DB-AUTH-001: Require Neon authority (HIGH - prediction cleanup)
from scripts._db_guard import require_neon  # noqa: E402
require_neon()

import psycopg2


def get_connection():
    """Get database connection from DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is required. "
            "Set it to your Postgres connection string."
        )
    return psycopg2.connect(database_url)


def cleanup_expired_predictions(dry_run: bool = False, verbose: bool = False) -> int:
    """
    Delete expired predictions.

    Args:
        dry_run: If True, only count expired rows without deleting
        verbose: If True, print detailed information

    Returns:
        Number of rows deleted (or would be deleted in dry-run mode)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # First, count expired predictions
            cur.execute(
                """
                SELECT COUNT(*)
                FROM prediction_events
                WHERE expires_at < NOW()
            """
            )
            expired_count = cur.fetchone()[0]

            if verbose:
                print(
                    f"[{datetime.now(timezone.utc).isoformat()}] Found {expired_count} expired predictions"
                )

            if expired_count == 0:
                if verbose:
                    print("No expired predictions to clean up.")
                return 0

            if dry_run:
                print(f"[DRY RUN] Would delete {expired_count} expired predictions")
                return expired_count

            # Delete expired predictions
            cur.execute(
                """
                DELETE FROM prediction_events
                WHERE expires_at < NOW()
            """
            )
            deleted_count = cur.rowcount

            conn.commit()

            if verbose:
                print(f"Deleted {deleted_count} expired predictions")

            return deleted_count

    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Clean up expired predictions from prediction_events table"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count expired predictions without deleting",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print detailed output"
    )

    args = parser.parse_args()

    try:
        deleted = cleanup_expired_predictions(
            dry_run=args.dry_run, verbose=args.verbose
        )
        if not args.dry_run and deleted > 0:
            print(f"C2 Cleanup: Deleted {deleted} expired predictions")
        sys.exit(0)
    except Exception as e:
        print(f"C2 Cleanup FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
