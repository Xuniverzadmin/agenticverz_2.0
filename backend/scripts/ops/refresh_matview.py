#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Materialized View Refresh Automation
# artifact_class: CODE
"""
Materialized View Refresh Automation

Periodic job to refresh M10 Recovery materialized views with tracking.
Designed to run as cron job or systemd timer.

Features:
- Leader election: Only one instance refreshes a specific view at a time
- Concurrent-safe locking per view (not global)
- Refresh tracking with duration and success metrics

Usage:
    # One-time refresh
    python -m scripts.ops.refresh_matview

    # Refresh specific view
    python -m scripts.ops.refresh_matview --view mv_top_pending

    # Skip leader election (for debugging)
    python -m scripts.ops.refresh_matview --skip-leader-election

    # As cron (every 5 minutes)
    */5 * * * * cd /root/agenticverz2.0/backend && python -m scripts.ops.refresh_matview >> /var/log/m10_matview_refresh.log 2>&1

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL
    MATVIEW_LOCK_TTL: Lock TTL in seconds (default: 300)
"""

import argparse
import json
import logging
import os
import socket
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# DB-AUTH-001: Require Neon authority (HIGH - materialized view refresh)
from scripts._db_guard import require_neon
require_neon()

logger = logging.getLogger("nova.ops.refresh_matview")

# Leader election settings
LOCK_TTL = int(os.getenv("MATVIEW_LOCK_TTL", "300"))  # 5 minutes per view
HOLDER_ID = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"

# Default views to refresh
DEFAULT_VIEWS = ["mv_top_pending"]


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


def acquire_view_lock(view_name: str, db_url: Optional[str] = None) -> bool:
    """
    Acquire distributed lock for a specific view refresh.

    Each view has its own lock to allow parallel refresh of different views.

    Returns:
        True if lock acquired, False otherwise
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    lock_name = f"m10:matview:{view_name}"
    db_url = db_url or os.getenv("DATABASE_URL")

    if not db_url:
        logger.error("DATABASE_URL not configured - cannot acquire lock")
        return False

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with Session(engine) as session:
            result = session.execute(
                text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": lock_name, "holder_id": HOLDER_ID, "ttl": LOCK_TTL},
            )
            acquired = result.scalar()
            session.commit()

            # Update Prometheus metrics
            _update_lock_metric(lock_name, bool(acquired))

            if acquired:
                logger.info(f"Acquired lock {lock_name} as {HOLDER_ID}")
            else:
                logger.info(f"Lock {lock_name} held by another process")

            return bool(acquired)
    except Exception as e:
        logger.error(f"Failed to acquire lock for {view_name}: {e}")
        return False


def release_view_lock(view_name: str, db_url: Optional[str] = None) -> bool:
    """
    Release distributed lock for a view.

    Returns:
        True if lock released, False otherwise
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    lock_name = f"m10:matview:{view_name}"
    db_url = db_url or os.getenv("DATABASE_URL")

    if not db_url:
        return False

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with Session(engine) as session:
            result = session.execute(
                text("SELECT m10_recovery.release_lock(:lock_name, :holder_id)"),
                {"lock_name": lock_name, "holder_id": HOLDER_ID},
            )
            released = result.scalar()
            session.commit()

            if released:
                logger.debug(f"Released lock {lock_name}")

            return bool(released)
    except Exception as e:
        logger.error(f"Failed to release lock for {view_name}: {e}")
        return False


def refresh_matview_tracked(
    view_name: str = "mv_top_pending",
    db_url: Optional[str] = None,
) -> Dict[str, any]:
    """
    Refresh materialized view with tracking.

    Uses m10_recovery.refresh_mv_tracked() function which logs
    refresh operations for freshness monitoring.

    Args:
        view_name: Name of the materialized view
        db_url: Database URL (uses DATABASE_URL env if not provided)

    Returns:
        Dict with success, duration_ms, error (if any)
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or os.getenv("DATABASE_URL")
    if not db_url:
        return {"success": False, "error": "DATABASE_URL not configured"}

    start = time.perf_counter()

    try:
        engine = create_engine(db_url, pool_pre_ping=True)

        with Session(engine) as session:
            result = session.execute(
                text("SELECT * FROM m10_recovery.refresh_mv_tracked(:view_name)"), {"view_name": view_name}
            )
            row = result.fetchone()
            session.commit()

            if row:
                success, duration_ms, error = row
                return {
                    "success": success,
                    "duration_ms": duration_ms,
                    "error": error,
                    "view_name": view_name,
                }

            return {
                "success": False,
                "error": "No result from refresh function",
                "view_name": view_name,
            }

    except Exception as e:
        duration = int((time.perf_counter() - start) * 1000)
        logger.error(f"Failed to refresh {view_name}: {e}")
        return {
            "success": False,
            "duration_ms": duration,
            "error": str(e),
            "view_name": view_name,
        }


def get_matview_freshness(db_url: Optional[str] = None) -> Dict[str, Dict]:
    """
    Get freshness status of all tracked materialized views.

    Returns:
        Dict mapping view_name to freshness info
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or os.getenv("DATABASE_URL")
    if not db_url:
        return {}

    try:
        engine = create_engine(db_url, pool_pre_ping=True)

        with Session(engine) as session:
            result = session.execute(
                text(
                    """
                SELECT view_name, last_refresh, age_seconds, last_success, last_duration_ms
                FROM m10_recovery.matview_freshness
            """
                )
            )

            freshness = {}
            for row in result:
                view_name, last_refresh, age_seconds, last_success, last_duration_ms = row
                freshness[view_name] = {
                    "last_refresh": last_refresh.isoformat() if last_refresh else None,
                    "age_seconds": float(age_seconds) if age_seconds else None,
                    "last_success": last_success,
                    "last_duration_ms": last_duration_ms,
                }

            return freshness

    except Exception as e:
        logger.error(f"Failed to get matview freshness: {e}")
        return {}


def update_prometheus_metrics(freshness: Dict[str, Dict]) -> None:
    """Update Prometheus metrics for matview freshness."""
    try:
        from app.metrics import (
            recovery_matview_age_seconds,
            recovery_matview_last_refresh_timestamp,
        )

        for view_name, info in freshness.items():
            if info.get("age_seconds") is not None:
                recovery_matview_age_seconds.labels(view_name=view_name).set(info["age_seconds"])

            if info.get("last_refresh"):
                from datetime import datetime

                try:
                    ts = datetime.fromisoformat(info["last_refresh"]).timestamp()
                    recovery_matview_last_refresh_timestamp.labels(view_name=view_name).set(ts)
                except Exception:
                    pass

    except ImportError:
        pass  # Metrics not available
    except Exception as e:
        logger.warning(f"Failed to update Prometheus metrics: {e}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Refresh M10 Recovery materialized views")
    parser.add_argument(
        "--view",
        type=str,
        default=None,
        help="Specific view to refresh (default: all tracked views)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show freshness status without refreshing",
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

    # Status only mode (no lock needed)
    if args.status:
        freshness = get_matview_freshness()
        if args.json:
            print(json.dumps(freshness, indent=2, default=str))
        else:
            print("\n=== Matview Freshness Status ===")
            for view_name, info in freshness.items():
                print(f"\n{view_name}:")
                print(f"  Last refresh: {info.get('last_refresh', 'never')}")
                print(f"  Age: {info.get('age_seconds', 'unknown')}s")
                print(f"  Last success: {info.get('last_success', 'unknown')}")
                print(f"  Last duration: {info.get('last_duration_ms', 'unknown')}ms")
        return

    # Determine views to refresh
    views = [args.view] if args.view else DEFAULT_VIEWS

    results = {}
    all_success = True
    locks_acquired = {}

    # =========================================================================
    # Leader election - acquire locks for each view
    # =========================================================================
    if not args.skip_leader_election:
        for view_name in views:
            locks_acquired[view_name] = acquire_view_lock(view_name)
            if not locks_acquired[view_name]:
                results[view_name] = {
                    "success": False,
                    "skipped": True,
                    "reason": "failed_to_acquire_lock",
                    "view_name": view_name,
                }
                logger.info(f"Skipping {view_name} - another instance is refreshing")
    else:
        logger.warning("Leader election skipped - running without locks")
        for view_name in views:
            locks_acquired[view_name] = False  # Track that we didn't acquire

    try:
        for view_name in views:
            # Skip views where we didn't get the lock
            if not args.skip_leader_election and not locks_acquired.get(view_name):
                continue

            logger.info(f"Refreshing {view_name}...")
            result = refresh_matview_tracked(view_name)
            results[view_name] = result

            if result.get("success"):
                logger.info(f"Refreshed {view_name} in {result.get('duration_ms', 0)}ms")
            else:
                logger.error(f"Failed to refresh {view_name}: {result.get('error')}")
                all_success = False

        # Update metrics
        freshness = get_matview_freshness()
        update_prometheus_metrics(freshness)

        # Output results
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "holder_id": HOLDER_ID,
            "results": results,
            "all_success": all_success,
            "freshness": freshness,
        }

        if args.json:
            print(json.dumps(output, indent=2, default=str))
        else:
            print("\n=== Matview Refresh Complete ===")
            print(f"Timestamp: {output['timestamp']}")
            print(f"Holder ID: {HOLDER_ID}")
            print(f"All success: {all_success}")
            for view_name, result in results.items():
                if result.get("skipped"):
                    status = "SKIPPED (locked)"
                elif result.get("success"):
                    status = "OK"
                else:
                    status = "FAILED"
                duration = result.get("duration_ms", 0)
                print(f"  {view_name}: {status} ({duration}ms)")

    finally:
        # Always release locks when done
        for view_name, acquired in locks_acquired.items():
            if acquired:
                release_view_lock(view_name)

    # Exit with error code if any non-skipped view failed
    actual_failures = [r for r in results.values() if not r.get("success") and not r.get("skipped")]
    sys.exit(0 if not actual_failures else 1)


if __name__ == "__main__":
    main()
