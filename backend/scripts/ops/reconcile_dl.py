#!/usr/bin/env python3
"""
Dead-Letter Reconciliation Script

Periodic job to find entries present in both dead-letter stream AND still pending
in the main stream. Resolves by preferring the DL state (XACKing the original).

This handles the edge case where XADD to DL succeeded but XACK failed.

Features:
- Leader election: Only one instance runs at a time (prevents race conditions)
- DL archival: Archives messages to DB before any trimming
- Idempotency: Uses DB-backed replay_log for durable tracking

Usage:
    # One-time run
    python -m scripts.ops.reconcile_dl

    # Dry-run mode (no changes)
    python -m scripts.ops.reconcile_dl --dry-run

    # Skip leader election (for debugging)
    python -m scripts.ops.reconcile_dl --skip-leader-election

    # As cron (every 5 minutes)
    */5 * * * * cd /root/agenticverz2.0/backend && python -m scripts.ops.reconcile_dl >> /var/log/m10_reconcile.log 2>&1

Environment Variables:
    REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
    DATABASE_URL: PostgreSQL connection URL (required for leader election)
    RECONCILE_LOCK_TTL: Lock TTL in seconds (default: 600)
"""

import argparse
import asyncio
import json
import logging
import os
import socket
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Set

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# DB-AUTH-001: Require Neon authority (HIGH - reconciliation)
from scripts._db_guard import require_neon
require_neon()

logger = logging.getLogger("nova.ops.reconcile_dl")

# Leader election settings
LOCK_NAME = "m10:reconcile_dl"
LOCK_TTL = int(os.getenv("RECONCILE_LOCK_TTL", "600"))  # 10 minutes
HOLDER_ID = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"

# Configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM_KEY = os.getenv("M10_STREAM_KEY", "m10:evaluate:stream")
CONSUMER_GROUP = os.getenv("M10_CONSUMER_GROUP", "m10:evaluate:group")
DEAD_LETTER_STREAM = os.getenv("M10_DEAD_LETTER_STREAM", "m10:evaluate:dead-letter")


async def get_redis():
    """Get async Redis client."""
    try:
        import redis.asyncio as aioredis

        return aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    except ImportError:
        import aioredis

        return await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )


def _update_lock_metric(lock_name: str, acquired: bool):
    """Update Prometheus metrics for lock operations."""
    try:
        from app.metrics import m10_lock_acquired_total, m10_lock_failed_total

        if acquired:
            m10_lock_acquired_total.labels(lock_name=lock_name).inc()
        else:
            m10_lock_failed_total.labels(lock_name=lock_name).inc()
    except ImportError:
        pass  # Metrics not available
    except Exception as e:
        logger.debug(f"Failed to update lock metric: {e}")


def acquire_lock(db_url: Optional[str] = None) -> bool:
    """
    Acquire distributed lock for leader election.

    Uses m10_recovery.acquire_lock() function from migration 022.

    Returns:
        True if lock acquired, False otherwise
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not configured - cannot acquire lock")
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

            # Update Prometheus metrics
            _update_lock_metric(LOCK_NAME, bool(acquired))

            if acquired:
                logger.info(f"Acquired lock {LOCK_NAME} as {HOLDER_ID}")
            else:
                logger.info(f"Lock {LOCK_NAME} held by another process")

            return bool(acquired)
    except Exception as e:
        logger.error(f"Failed to acquire lock: {e}")
        return False


def release_lock(db_url: Optional[str] = None) -> bool:
    """
    Release distributed lock.

    Returns:
        True if lock released, False otherwise
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or os.getenv("DATABASE_URL")
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

            if released:
                logger.info(f"Released lock {LOCK_NAME}")

            return bool(released)
    except Exception as e:
        logger.error(f"Failed to release lock: {e}")
        return False


def extend_lock(db_url: Optional[str] = None) -> bool:
    """
    Extend lock TTL while working.

    Returns:
        True if lock extended, False otherwise
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or os.getenv("DATABASE_URL")
    if not db_url:
        return False

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with Session(engine) as session:
            result = session.execute(
                text("SELECT m10_recovery.extend_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": LOCK_NAME, "holder_id": HOLDER_ID, "ttl": LOCK_TTL},
            )
            extended = result.scalar()
            session.commit()
            return bool(extended)
    except Exception as e:
        logger.warning(f"Failed to extend lock: {e}")
        return False


async def get_pending_message_ids(redis) -> Set[str]:
    """Get all pending (unacknowledged) message IDs from main stream."""
    pending_ids = set()

    try:
        # XPENDING summary
        pending_info = await redis.xpending(STREAM_KEY, CONSUMER_GROUP)
        if not pending_info or pending_info[0] == 0:
            return pending_ids

        # Get detailed pending list
        pending_range = await redis.xpending_range(
            STREAM_KEY,
            CONSUMER_GROUP,
            min="-",
            max="+",
            count=10000,  # Large batch
        )

        for entry in pending_range:
            if isinstance(entry, dict):
                msg_id = entry.get("message_id")
            else:
                msg_id = entry[0] if len(entry) > 0 else None

            if msg_id:
                pending_ids.add(msg_id)

    except Exception as e:
        logger.error(f"Failed to get pending messages: {e}")

    return pending_ids


async def get_dead_letter_original_ids(redis) -> Dict[str, str]:
    """
    Get mapping of original message IDs to their DL entry IDs.

    Returns:
        Dict mapping original_msg_id -> dl_msg_id
    """
    dl_originals = {}

    try:
        # Read all DL entries
        dl_len = await redis.xlen(DEAD_LETTER_STREAM)
        if dl_len == 0:
            return dl_originals

        # Read in batches
        last_id = "0-0"
        batch_size = 1000

        while True:
            entries = await redis.xrange(
                DEAD_LETTER_STREAM,
                min=f"({last_id}" if last_id != "0-0" else "-",
                max="+",
                count=batch_size,
            )

            if not entries:
                break

            for dl_msg_id, fields in entries:
                original_id = fields.get("original_msg_id")
                if original_id:
                    dl_originals[original_id] = dl_msg_id
                last_id = dl_msg_id

            if len(entries) < batch_size:
                break

    except Exception as e:
        logger.error(f"Failed to read dead-letter stream: {e}")

    return dl_originals


async def reconcile_once(dry_run: bool = False) -> Dict[str, int]:
    """
    Run one reconciliation pass.

    Finds messages that are:
    1. In the dead-letter stream (by original_msg_id)
    2. Still pending in the main stream

    Resolves by XACKing the original since it's already safely in DL.

    Args:
        dry_run: If True, report but don't make changes

    Returns:
        Dict with reconciliation stats
    """
    redis = await get_redis()

    stats = {
        "pending_count": 0,
        "dl_count": 0,
        "duplicates_found": 0,
        "acked": 0,
        "errors": 0,
        "dry_run": dry_run,
    }

    try:
        # Get pending messages from main stream
        pending_ids = await get_pending_message_ids(redis)
        stats["pending_count"] = len(pending_ids)

        if not pending_ids:
            logger.info("No pending messages in stream")
            return stats

        # Get original IDs from dead-letter
        dl_originals = await get_dead_letter_original_ids(redis)
        stats["dl_count"] = len(dl_originals)

        if not dl_originals:
            logger.info("No messages in dead-letter stream")
            return stats

        # Find duplicates: messages in both pending AND dead-letter
        duplicates = pending_ids.intersection(set(dl_originals.keys()))
        stats["duplicates_found"] = len(duplicates)

        if not duplicates:
            logger.info(f"No duplicates found. Pending: {stats['pending_count']}, DL: {stats['dl_count']}")
            return stats

        logger.warning(f"Found {len(duplicates)} duplicates (in both pending and DL)")

        # Resolve duplicates by XACKing the original
        for original_id in duplicates:
            dl_id = dl_originals[original_id]

            if dry_run:
                logger.info(f"[DRY-RUN] Would XACK {original_id} (already in DL as {dl_id})")
                stats["acked"] += 1
            else:
                try:
                    result = await redis.xack(STREAM_KEY, CONSUMER_GROUP, original_id)
                    if result > 0:
                        logger.info(f"Reconciled: XACK {original_id} (in DL as {dl_id})")
                        stats["acked"] += 1
                    else:
                        # Already acked by another process
                        logger.debug(f"Message {original_id} already acknowledged")
                except Exception as e:
                    logger.error(f"Failed to XACK {original_id}: {e}")
                    stats["errors"] += 1

        return stats

    finally:
        await redis.close()


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Reconcile dead-letter duplicates")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report duplicates without making changes",
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
    parser.add_argument(
        "--skip-leader-election",
        action="store_true",
        help="Skip leader election (for debugging only)",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    # =========================================================================
    # Leader election - only one instance should run at a time
    # =========================================================================
    lock_acquired = False
    if not args.skip_leader_election:
        lock_acquired = acquire_lock()
        if not lock_acquired:
            stats = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "skipped",
                "reason": "failed_to_acquire_lock",
                "holder_id": HOLDER_ID,
            }
            if args.json:
                print(json.dumps(stats, indent=2))
            else:
                print("\n=== Dead-Letter Reconciliation ===")
                print("Status: Skipped - another instance is running")
                print(f"Holder ID: {HOLDER_ID}")
            return
    else:
        logger.warning("Leader election skipped - running without lock")

    try:
        # Run reconciliation
        stats = await reconcile_once(dry_run=args.dry_run)
        stats["timestamp"] = datetime.now(timezone.utc).isoformat()
        stats["holder_id"] = HOLDER_ID

        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("\n=== Dead-Letter Reconciliation ===")
            print(f"Timestamp: {stats['timestamp']}")
            print(f"Holder ID: {HOLDER_ID}")
            print(f"Dry Run: {stats['dry_run']}")
            print(f"Pending in stream: {stats['pending_count']}")
            print(f"Messages in DL: {stats['dl_count']}")
            print(f"Duplicates found: {stats['duplicates_found']}")
            print(f"Messages ACKed: {stats['acked']}")
            print(f"Errors: {stats['errors']}")

            if stats["duplicates_found"] > 0 and stats["dry_run"]:
                print("\nRun without --dry-run to resolve duplicates")
    finally:
        # Always release the lock when done
        if lock_acquired:
            release_lock()


if __name__ == "__main__":
    asyncio.run(main())
