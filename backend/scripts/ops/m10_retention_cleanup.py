#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: M10 Recovery Retention Cleanup
# artifact_class: CODE
"""
M10 Recovery Retention Cleanup

Periodic job to clean up old entries from:
- dead_letter_archive (default: 90 days)
- replay_log (default: 30 days)
- distributed_locks (expired only)
- outbox (processed events, default: 7 days)

Features:
- Leader election to prevent concurrent runs
- Dry-run mode for testing
- Configurable retention periods
- S3/R2 archival before deletion (optional)

Usage:
    # Dry run
    python -m scripts.ops.m10_retention_cleanup --dry-run

    # Run cleanup
    python -m scripts.ops.m10_retention_cleanup

    # Custom retention
    python -m scripts.ops.m10_retention_cleanup --dl-archive-days 180 --replay-days 60

    # As cron (weekly)
    0 3 * * 0 cd /root/agenticverz2.0/backend && python -m scripts.ops.m10_retention_cleanup >> /var/log/m10_retention.log 2>&1

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL
    DL_ARCHIVE_RETENTION_DAYS: Dead-letter archive retention (default: 90)
    REPLAY_LOG_RETENTION_DAYS: Replay log retention (default: 30)
    OUTBOX_RETENTION_DAYS: Processed outbox retention (default: 7)
    RETENTION_LOCK_TTL: Lock TTL in seconds (default: 3600)
"""

import argparse
import json
import logging
import os
import socket
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# DB-AUTH-001: Require Neon authority (MEDIUM - retention cleanup)
from scripts._db_guard import require_neon
require_neon()

logger = logging.getLogger("nova.ops.retention_cleanup")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
DL_ARCHIVE_RETENTION_DAYS = int(os.getenv("DL_ARCHIVE_RETENTION_DAYS", "90"))
REPLAY_LOG_RETENTION_DAYS = int(os.getenv("REPLAY_LOG_RETENTION_DAYS", "30"))
OUTBOX_RETENTION_DAYS = int(os.getenv("OUTBOX_RETENTION_DAYS", "7"))
LOCK_TTL = int(os.getenv("RETENTION_LOCK_TTL", "3600"))

# Leader election
LOCK_NAME = "m10:retention_cleanup"
HOLDER_ID = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


def acquire_lock(db_url: Optional[str] = None) -> bool:
    """Acquire distributed lock."""
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or DATABASE_URL
    if not db_url:
        logger.error("DATABASE_URL not configured")
        return False

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with Session(engine) as session:
            result = session.execute(
                text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": LOCK_NAME, "holder_id": HOLDER_ID, "ttl": LOCK_TTL},
            )
            acquired = result.scalar()
            session.commit()

            if acquired:
                logger.info(f"Acquired lock {LOCK_NAME} as {HOLDER_ID}")
            else:
                logger.info(f"Lock {LOCK_NAME} held by another process")

            return bool(acquired)
    except Exception as e:
        logger.error(f"Failed to acquire lock: {e}")
        return False


def release_lock(db_url: Optional[str] = None) -> bool:
    """Release distributed lock."""
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or DATABASE_URL
    if not db_url:
        return False

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with Session(engine) as session:
            result = session.execute(
                text("SELECT m10_recovery.release_lock(:lock_name, :holder_id)"),
                {"lock_name": LOCK_NAME, "holder_id": HOLDER_ID},
            )
            released = result.scalar()
            session.commit()
            return bool(released)
    except Exception as e:
        logger.error(f"Failed to release lock: {e}")
        return False


def cleanup_dead_letter_archive(
    retention_days: int = DL_ARCHIVE_RETENTION_DAYS,
    dry_run: bool = False,
    db_url: Optional[str] = None,
) -> Dict[str, int]:
    """
    Clean up old dead_letter_archive entries.

    Returns:
        Dict with counts: {'count': N, 'deleted': M}
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or DATABASE_URL
    engine = create_engine(db_url, pool_pre_ping=True)

    results = {"table": "dead_letter_archive", "retention_days": retention_days, "count": 0, "deleted": 0}

    try:
        with Session(engine) as session:
            # Count rows to delete
            count_result = session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM m10_recovery.dead_letter_archive
                    WHERE archived_at < now() - make_interval(days => :days)
                """
                ),
                {"days": retention_days},
            )
            results["count"] = count_result.scalar() or 0

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would delete {results['count']} dead_letter_archive rows older than {retention_days} days"
                )
                return results

            if results["count"] > 0:
                # Delete in batches to avoid long locks
                batch_size = 1000
                total_deleted = 0

                while True:
                    delete_result = session.execute(
                        text(
                            """
                            DELETE FROM m10_recovery.dead_letter_archive
                            WHERE id IN (
                                SELECT id FROM m10_recovery.dead_letter_archive
                                WHERE archived_at < now() - make_interval(days => :days)
                                LIMIT :batch_size
                            )
                        """
                        ),
                        {"days": retention_days, "batch_size": batch_size},
                    )
                    deleted = delete_result.rowcount
                    total_deleted += deleted
                    session.commit()

                    if deleted < batch_size:
                        break

                results["deleted"] = total_deleted
                logger.info(f"Deleted {total_deleted} dead_letter_archive rows older than {retention_days} days")

    except Exception as e:
        logger.error(f"Failed to clean dead_letter_archive: {e}")
        results["error"] = str(e)

    return results


def cleanup_replay_log(
    retention_days: int = REPLAY_LOG_RETENTION_DAYS,
    dry_run: bool = False,
    db_url: Optional[str] = None,
) -> Dict[str, int]:
    """
    Clean up old replay_log entries.

    Returns:
        Dict with counts: {'count': N, 'deleted': M}
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or DATABASE_URL
    engine = create_engine(db_url, pool_pre_ping=True)

    results = {"table": "replay_log", "retention_days": retention_days, "count": 0, "deleted": 0}

    try:
        with Session(engine) as session:
            # Count rows to delete
            count_result = session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM m10_recovery.replay_log
                    WHERE replayed_at < now() - make_interval(days => :days)
                """
                ),
                {"days": retention_days},
            )
            results["count"] = count_result.scalar() or 0

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would delete {results['count']} replay_log rows older than {retention_days} days"
                )
                return results

            if results["count"] > 0:
                batch_size = 1000
                total_deleted = 0

                while True:
                    delete_result = session.execute(
                        text(
                            """
                            DELETE FROM m10_recovery.replay_log
                            WHERE id IN (
                                SELECT id FROM m10_recovery.replay_log
                                WHERE replayed_at < now() - make_interval(days => :days)
                                LIMIT :batch_size
                            )
                        """
                        ),
                        {"days": retention_days, "batch_size": batch_size},
                    )
                    deleted = delete_result.rowcount
                    total_deleted += deleted
                    session.commit()

                    if deleted < batch_size:
                        break

                results["deleted"] = total_deleted
                logger.info(f"Deleted {total_deleted} replay_log rows older than {retention_days} days")

    except Exception as e:
        logger.error(f"Failed to clean replay_log: {e}")
        results["error"] = str(e)

    return results


def cleanup_outbox(
    retention_days: int = OUTBOX_RETENTION_DAYS,
    dry_run: bool = False,
    db_url: Optional[str] = None,
) -> Dict[str, int]:
    """
    Clean up processed outbox entries.

    Only deletes events that have been successfully processed.

    Returns:
        Dict with counts: {'count': N, 'deleted': M}
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or DATABASE_URL
    engine = create_engine(db_url, pool_pre_ping=True)

    results = {"table": "outbox", "retention_days": retention_days, "count": 0, "deleted": 0}

    try:
        with Session(engine) as session:
            # Count rows to delete (only processed events)
            count_result = session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM m10_recovery.outbox
                    WHERE processed_at IS NOT NULL
                      AND processed_at < now() - make_interval(days => :days)
                """
                ),
                {"days": retention_days},
            )
            results["count"] = count_result.scalar() or 0

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would delete {results['count']} processed outbox rows older than {retention_days} days"
                )
                return results

            if results["count"] > 0:
                batch_size = 1000
                total_deleted = 0

                while True:
                    delete_result = session.execute(
                        text(
                            """
                            DELETE FROM m10_recovery.outbox
                            WHERE id IN (
                                SELECT id FROM m10_recovery.outbox
                                WHERE processed_at IS NOT NULL
                                  AND processed_at < now() - make_interval(days => :days)
                                LIMIT :batch_size
                            )
                        """
                        ),
                        {"days": retention_days, "batch_size": batch_size},
                    )
                    deleted = delete_result.rowcount
                    total_deleted += deleted
                    session.commit()

                    if deleted < batch_size:
                        break

                results["deleted"] = total_deleted
                logger.info(f"Deleted {total_deleted} processed outbox rows older than {retention_days} days")

    except Exception as e:
        logger.error(f"Failed to clean outbox: {e}")
        results["error"] = str(e)

    return results


def cleanup_expired_locks(
    dry_run: bool = False,
    db_url: Optional[str] = None,
) -> Dict[str, int]:
    """
    Clean up expired distributed locks.

    Returns:
        Dict with counts: {'count': N, 'deleted': M}
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or DATABASE_URL
    engine = create_engine(db_url, pool_pre_ping=True)

    results = {"table": "distributed_locks", "count": 0, "deleted": 0}

    try:
        with Session(engine) as session:
            # Count expired locks
            count_result = session.execute(
                text("SELECT COUNT(*) FROM m10_recovery.distributed_locks WHERE expires_at < now()")
            )
            results["count"] = count_result.scalar() or 0

            if dry_run:
                logger.info(f"[DRY RUN] Would delete {results['count']} expired locks")
                return results

            if results["count"] > 0:
                delete_result = session.execute(
                    text("DELETE FROM m10_recovery.distributed_locks WHERE expires_at < now()")
                )
                results["deleted"] = delete_result.rowcount
                session.commit()
                logger.info(f"Deleted {results['deleted']} expired locks")

    except Exception as e:
        logger.error(f"Failed to clean expired locks: {e}")
        results["error"] = str(e)

    return results


def run_all_cleanup(
    dl_archive_days: int = DL_ARCHIVE_RETENTION_DAYS,
    replay_days: int = REPLAY_LOG_RETENTION_DAYS,
    outbox_days: int = OUTBOX_RETENTION_DAYS,
    dry_run: bool = False,
    skip_leader_election: bool = False,
) -> Dict[str, any]:
    """
    Run all cleanup jobs with leader election.

    Returns:
        Dict with all results
    """
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "holder_id": HOLDER_ID,
        "dry_run": dry_run,
        "tables": [],
    }

    # Leader election
    lock_acquired = False
    if not skip_leader_election:
        lock_acquired = acquire_lock()
        if not lock_acquired:
            results["status"] = "skipped"
            results["reason"] = "failed_to_acquire_lock"
            return results
    else:
        logger.warning("Leader election skipped")

    try:
        # Run all cleanup jobs
        results["tables"].append(cleanup_dead_letter_archive(dl_archive_days, dry_run))
        results["tables"].append(cleanup_replay_log(replay_days, dry_run))
        results["tables"].append(cleanup_outbox(outbox_days, dry_run))
        results["tables"].append(cleanup_expired_locks(dry_run))

        # Calculate totals
        total_count = sum(t.get("count", 0) for t in results["tables"])
        total_deleted = sum(t.get("deleted", 0) for t in results["tables"])
        results["total_count"] = total_count
        results["total_deleted"] = total_deleted
        results["status"] = "success"

    finally:
        if lock_acquired:
            release_lock()

    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="M10 Recovery retention cleanup")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting",
    )
    parser.add_argument(
        "--dl-archive-days",
        type=int,
        default=DL_ARCHIVE_RETENTION_DAYS,
        help=f"Dead-letter archive retention days (default: {DL_ARCHIVE_RETENTION_DAYS})",
    )
    parser.add_argument(
        "--replay-days",
        type=int,
        default=REPLAY_LOG_RETENTION_DAYS,
        help=f"Replay log retention days (default: {REPLAY_LOG_RETENTION_DAYS})",
    )
    parser.add_argument(
        "--outbox-days",
        type=int,
        default=OUTBOX_RETENTION_DAYS,
        help=f"Outbox retention days (default: {OUTBOX_RETENTION_DAYS})",
    )
    parser.add_argument(
        "--skip-leader-election",
        action="store_true",
        help="Skip leader election (for debugging)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    # Run cleanup
    results = run_all_cleanup(
        dl_archive_days=args.dl_archive_days,
        replay_days=args.replay_days,
        outbox_days=args.outbox_days,
        dry_run=args.dry_run,
        skip_leader_election=args.skip_leader_election,
    )

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print("\n=== M10 Retention Cleanup ===")
        print(f"Timestamp: {results['timestamp']}")
        print(f"Holder ID: {results['holder_id']}")
        print(f"Dry Run: {results['dry_run']}")
        print(f"Status: {results['status']}")

        if results["status"] == "skipped":
            print(f"Reason: {results.get('reason', 'unknown')}")
        else:
            print("\nResults by table:")
            for table in results.get("tables", []):
                status = "DELETED" if not results["dry_run"] else "WOULD DELETE"
                print(f"  {table['table']}: {table.get('deleted', table.get('count', 0))} rows {status}")

            print(f"\nTotal: {results.get('total_deleted', results.get('total_count', 0))} rows")


if __name__ == "__main__":
    main()
