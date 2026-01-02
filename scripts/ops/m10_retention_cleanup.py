#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cron / CI
#   Execution: sync
# Role: M10 retention cleanup operations
# Reference: PIN-276

"""
M10 Retention Cleanup

Provides cleanup operations for M10 recovery tables:
- Dead letter archive cleanup
- Replay log cleanup
- Outbox cleanup (processed events)
- Expired locks cleanup

Usage:
    from scripts.ops.m10_retention_cleanup import run_all_cleanup, cleanup_expired_locks

    # Run all cleanup jobs
    results = run_all_cleanup(dry_run=True)

    # Cleanup expired locks only
    results = cleanup_expired_locks(dry_run=True)
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlmodel import Session, create_engine


def run_all_cleanup(
    dl_archive_days: int = 90,
    replay_days: int = 30,
    outbox_days: int = 7,
    dry_run: bool = False,
    skip_leader_election: bool = False,
    db_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run all retention cleanup jobs.

    Args:
        dl_archive_days: Archive dead letter records older than this
        replay_days: Archive replay log records older than this
        outbox_days: Archive processed outbox events older than this
        dry_run: If True, don't actually delete anything
        skip_leader_election: If True, skip leader election check
        db_url: Database URL (defaults to DATABASE_URL env var)

    Returns:
        Dict with status, dry_run flag, and tables cleaned
    """
    db_url = db_url or os.getenv("DATABASE_URL")
    if not db_url:
        return {"status": "error", "error": "DATABASE_URL not set", "dry_run": dry_run}

    engine = create_engine(db_url)
    tables_cleaned: List[Dict[str, Any]] = []

    try:
        with Session(engine) as session:
            # 1. Dead letter archive cleanup
            dl_result = _cleanup_table(
                session,
                table="m10_recovery.dead_letter_archive",
                date_column="archived_at",
                days=dl_archive_days,
                dry_run=dry_run,
            )
            tables_cleaned.append({"table": "dead_letter_archive", **dl_result})

            # 2. Replay log cleanup
            replay_result = _cleanup_table(
                session,
                table="m10_recovery.replay_log",
                date_column="replayed_at",
                days=replay_days,
                dry_run=dry_run,
            )
            tables_cleaned.append({"table": "replay_log", **replay_result})

            # 3. Outbox cleanup (processed events only)
            outbox_result = _cleanup_outbox(
                session,
                days=outbox_days,
                dry_run=dry_run,
            )
            tables_cleaned.append({"table": "outbox", **outbox_result})

            # 4. Expired locks cleanup
            locks_result = _cleanup_expired_locks_impl(session, dry_run=dry_run)
            tables_cleaned.append({"table": "distributed_locks", **locks_result})

            if not dry_run:
                session.commit()

        return {
            "status": "success",
            "dry_run": dry_run,
            "tables": tables_cleaned,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "dry_run": dry_run,
            "tables": tables_cleaned,
        }


def _cleanup_table(
    session: Session,
    table: str,
    date_column: str,
    days: int,
    dry_run: bool,
) -> Dict[str, Any]:
    """Clean up old records from a table."""
    # Count candidates
    count_result = session.execute(
        text(
            f"""
            SELECT COUNT(*) FROM {table}
            WHERE {date_column} < now() - make_interval(days => :days)
            """
        ),
        {"days": days},
    )
    count = count_result.scalar() or 0

    deleted = 0
    if not dry_run and count > 0:
        delete_result = session.execute(
            text(
                f"""
                DELETE FROM {table}
                WHERE {date_column} < now() - make_interval(days => :days)
                """
            ),
            {"days": days},
        )
        deleted = delete_result.rowcount

    return {"candidates": count, "deleted": deleted if not dry_run else 0}


def _cleanup_outbox(session: Session, days: int, dry_run: bool) -> Dict[str, Any]:
    """Clean up processed outbox events."""
    # Only clean up PROCESSED events (processed_at IS NOT NULL)
    count_result = session.execute(
        text(
            """
            SELECT COUNT(*) FROM m10_recovery.outbox
            WHERE processed_at IS NOT NULL
            AND processed_at < now() - make_interval(days => :days)
            """
        ),
        {"days": days},
    )
    count = count_result.scalar() or 0

    deleted = 0
    if not dry_run and count > 0:
        delete_result = session.execute(
            text(
                """
                DELETE FROM m10_recovery.outbox
                WHERE processed_at IS NOT NULL
                AND processed_at < now() - make_interval(days => :days)
                """
            ),
            {"days": days},
        )
        deleted = delete_result.rowcount

    return {"candidates": count, "deleted": deleted if not dry_run else 0}


def _cleanup_expired_locks_impl(session: Session, dry_run: bool) -> Dict[str, Any]:
    """Clean up expired distributed locks."""
    # Count expired locks
    count_result = session.execute(
        text(
            """
            SELECT COUNT(*) FROM m10_recovery.distributed_locks
            WHERE expires_at < now()
            """
        )
    )
    count = count_result.scalar() or 0

    deleted = 0
    if not dry_run and count > 0:
        delete_result = session.execute(
            text(
                """
                DELETE FROM m10_recovery.distributed_locks
                WHERE expires_at < now()
                """
            )
        )
        deleted = delete_result.rowcount

    return {"candidates": count, "deleted": deleted if not dry_run else 0}


def cleanup_expired_locks(
    dry_run: bool = False,
    db_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Clean up expired distributed locks from m10_recovery.distributed_locks.

    Args:
        dry_run: If True, just count without deleting
        db_url: Database URL (defaults to DATABASE_URL env var)

    Returns:
        Dict with deleted count and status
    """
    db_url = db_url or os.getenv("DATABASE_URL")
    if not db_url:
        return {"status": "error", "error": "DATABASE_URL not set", "deleted": 0}

    engine = create_engine(db_url)

    try:
        with Session(engine) as session:
            result = _cleanup_expired_locks_impl(session, dry_run=dry_run)
            if not dry_run:
                session.commit()

        return {
            "status": "success",
            "deleted": result["deleted"],
            "candidates": result["candidates"],
            "dry_run": dry_run,
        }

    except Exception as e:
        return {"status": "error", "error": str(e), "deleted": 0}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="M10 Retention Cleanup")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually delete")
    parser.add_argument(
        "--dl-days", type=int, default=90, help="Dead letter archive retention days"
    )
    parser.add_argument(
        "--replay-days", type=int, default=30, help="Replay log retention days"
    )
    parser.add_argument(
        "--outbox-days", type=int, default=7, help="Processed outbox retention days"
    )
    parser.add_argument(
        "--locks-only", action="store_true", help="Only clean expired locks"
    )
    args = parser.parse_args()

    if args.locks_only:
        result = cleanup_expired_locks(dry_run=args.dry_run)
        print(f"Expired locks cleanup: {result}")
    else:
        result = run_all_cleanup(
            dl_archive_days=args.dl_days,
            replay_days=args.replay_days,
            outbox_days=args.outbox_days,
            dry_run=args.dry_run,
        )
        print(f"Cleanup results: {result}")
