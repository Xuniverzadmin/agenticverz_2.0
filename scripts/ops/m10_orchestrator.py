#!/usr/bin/env python3
"""
M10 Maintenance Orchestrator

Consolidates 5 systemd timers into 1 orchestrated maintenance job:
- Outbox processor (process pending outbox events)
- Dead-letter reconciliation (XACK orphaned pending entries)
- Matview refresh (refresh materialized views)
- Retention cleanup (archive old records)
- Reclaim GC (clean up stale reclaim attempts)

This reduces operational burden from 5 failure points to 1.

Usage:
    # Run all maintenance tasks
    python -m scripts.ops.m10_orchestrator

    # Run specific tasks only
    python -m scripts.ops.m10_orchestrator --tasks outbox,matview

    # Dry run (no changes)
    python -m scripts.ops.m10_orchestrator --dry-run

    # JSON output for monitoring
    python -m scripts.ops.m10_orchestrator --json

Systemd Timer Configuration:
    Create a single timer that runs this orchestrator every 5 minutes:

    [Timer]
    OnCalendar=*:0/5
    AccuracySec=30s
    Persistent=true

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL (required)
    REDIS_URL: Redis connection URL (optional, for stream tasks)
    M10_ORCHESTRATOR_TIMEOUT: Max runtime per task in seconds (default: 300)
"""

import argparse
import asyncio
import json
import logging
import os
import socket
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Add backend to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "backend",
    ),
)

logger = logging.getLogger("m10.orchestrator")

# Task timeout (5 minutes default)
TASK_TIMEOUT = int(os.getenv("M10_ORCHESTRATOR_TIMEOUT", "300"))

# Worker identity for distributed locks
WORKER_ID = f"orchestrator:{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"

# Available tasks in execution order
TASK_ORDER = [
    "outbox",  # Process pending outbox events first
    "dl_reconcile",  # Then reconcile dead-letter
    "matview",  # Refresh materialized views
    "retention",  # Archive old records
    "reclaim_gc",  # Clean up stale reclaim attempts
]


class TaskResult:
    """Result of a maintenance task execution."""

    def __init__(self, name: str):
        self.name = name
        self.success = False
        self.error: Optional[str] = None
        self.duration_seconds: float = 0
        self.details: Dict[str, Any] = {}
        self.skipped = False
        self.skip_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "success": self.success,
            "error": self.error,
            "duration_seconds": round(self.duration_seconds, 3),
            "details": self.details,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
        }


async def run_outbox_task(db_url: str, dry_run: bool = False) -> TaskResult:
    """Process pending outbox events."""
    result = TaskResult("outbox")

    try:
        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)

        with Session(engine) as session:
            # Get pending count (outbox table uses processed_at IS NULL for pending)
            pending = session.execute(
                text(
                    """
                SELECT COUNT(*) FROM m10_recovery.outbox WHERE processed_at IS NULL
            """
                )
            ).scalar()

            result.details["pending_count"] = pending

            if dry_run:
                result.success = True
                result.details["action"] = "dry_run"
                return result

            if pending == 0:
                result.success = True
                result.details["action"] = "no_work"
                return result

            # Import and run outbox processor
            try:
                from app.worker.outbox_processor import OutboxProcessor

                processor = OutboxProcessor(db_url)
                await processor.start()

                # Process up to 100 events per orchestrator run
                batch_result = await processor.process_batch(100)
                await processor.stop()

                result.details["processed"] = batch_result.get("processed", 0)
                result.details["failed"] = batch_result.get("failed", 0)
                result.success = True
            except ImportError:
                # Outbox processor not available, just report status
                result.details["action"] = "status_only"
                result.success = True

    except Exception as e:
        result.error = str(e)
        logger.error(f"Outbox task failed: {e}")

    return result


async def run_dl_reconcile_task(db_url: str, dry_run: bool = False) -> TaskResult:
    """Reconcile dead-letter entries (XACK orphaned pending)."""
    result = TaskResult("dl_reconcile")

    try:
        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)

        # Check if we can acquire the lock
        with Session(engine) as session:
            lock_acquired = session.execute(
                text(
                    """
                SELECT m10_recovery.acquire_lock('dl_reconcile', :holder_id, 300)
            """
                ),
                {"holder_id": WORKER_ID},
            ).scalar()

            if not lock_acquired:
                result.skipped = True
                result.skip_reason = "Lock held by another instance"
                result.success = True
                return result

            try:
                # Get dead-letter count
                dl_count = session.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM m10_recovery.dead_letter_archive
                    WHERE archived_at > NOW() - INTERVAL '1 hour'
                """
                    )
                ).scalar()

                result.details["recent_dl_count"] = dl_count

                if dry_run:
                    result.success = True
                    result.details["action"] = "dry_run"
                    return result

                # Run actual reconciliation
                try:
                    from scripts.ops.reconcile_dl import reconcile_dead_letter

                    reconciled = reconcile_dead_letter(session)
                    result.details["reconciled"] = reconciled
                except ImportError:
                    result.details["action"] = "status_only"

                result.success = True
                session.commit()
            finally:
                # Release lock
                session.execute(
                    text(
                        """
                    SELECT m10_recovery.release_lock('dl_reconcile', :holder_id)
                """
                    ),
                    {"holder_id": WORKER_ID},
                )
                session.commit()

    except Exception as e:
        result.error = str(e)
        logger.error(f"DL reconcile task failed: {e}")

    return result


async def run_matview_task(db_url: str, dry_run: bool = False) -> TaskResult:
    """Refresh materialized views."""
    result = TaskResult("matview")

    try:
        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)

        views = ["mv_top_pending"]  # Add more views as needed
        refreshed = []

        with Session(engine) as session:
            for view_name in views:
                # Try to acquire view-specific lock
                lock_name = f"matview_{view_name}"
                lock_acquired = session.execute(
                    text(
                        """
                    SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, 120)
                """
                    ),
                    {"lock_name": lock_name, "holder_id": WORKER_ID},
                ).scalar()

                if not lock_acquired:
                    result.details[view_name] = "lock_held"
                    continue

                try:
                    # Check view age
                    age = session.execute(
                        text(
                            """
                        SELECT EXTRACT(EPOCH FROM (NOW() - last_refresh))::int
                        FROM pg_stat_user_tables
                        WHERE relname = :view_name
                    """
                        ),
                        {"view_name": view_name},
                    ).scalar()

                    result.details[f"{view_name}_age_seconds"] = age or 0

                    if dry_run:
                        result.details[view_name] = "dry_run"
                        continue

                    # Refresh if older than 5 minutes
                    if age is None or age > 300:
                        session.execute(
                            text(
                                f"""
                            REFRESH MATERIALIZED VIEW CONCURRENTLY m10_recovery.{view_name}
                        """
                            )
                        )
                        session.commit()
                        refreshed.append(view_name)
                        result.details[view_name] = "refreshed"
                    else:
                        result.details[view_name] = "fresh"
                finally:
                    session.execute(
                        text(
                            """
                        SELECT m10_recovery.release_lock(:lock_name, :holder_id)
                    """
                        ),
                        {"lock_name": lock_name, "holder_id": WORKER_ID},
                    )
                    session.commit()

        result.details["refreshed_count"] = len(refreshed)
        result.success = True

    except Exception as e:
        result.error = str(e)
        logger.error(f"Matview task failed: {e}")

    return result


async def run_retention_task(db_url: str, dry_run: bool = False) -> TaskResult:
    """Archive old records (retention cleanup)."""
    result = TaskResult("retention")

    try:
        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)

        with Session(engine) as session:
            # Acquire retention lock
            lock_acquired = session.execute(
                text(
                    """
                SELECT m10_recovery.acquire_lock('retention_cleanup', :holder_id, 600)
            """
                ),
                {"holder_id": WORKER_ID},
            ).scalar()

            if not lock_acquired:
                result.skipped = True
                result.skip_reason = "Lock held by another instance"
                result.success = True
                return result

            try:
                # Count old records (> 30 days)
                old_replay = session.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM m10_recovery.replay_log
                    WHERE processed_at < NOW() - INTERVAL '30 days'
                """
                    )
                ).scalar()

                old_archive = session.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM m10_recovery.dead_letter_archive
                    WHERE archived_at < NOW() - INTERVAL '30 days'
                """
                    )
                ).scalar()

                result.details["old_replay_log"] = old_replay
                result.details["old_archive"] = old_archive

                if dry_run:
                    result.success = True
                    result.details["action"] = "dry_run"
                    return result

                # Delete old records (keep last 30 days)
                deleted_replay = session.execute(
                    text(
                        """
                    DELETE FROM m10_recovery.replay_log
                    WHERE processed_at < NOW() - INTERVAL '30 days'
                    RETURNING 1
                """
                    )
                ).rowcount

                deleted_archive = session.execute(
                    text(
                        """
                    DELETE FROM m10_recovery.dead_letter_archive
                    WHERE archived_at < NOW() - INTERVAL '30 days'
                    RETURNING 1
                """
                    )
                ).rowcount

                session.commit()

                result.details["deleted_replay_log"] = deleted_replay
                result.details["deleted_archive"] = deleted_archive
                result.success = True
            finally:
                session.execute(
                    text(
                        """
                    SELECT m10_recovery.release_lock('retention_cleanup', :holder_id)
                """
                    ),
                    {"holder_id": WORKER_ID},
                )
                session.commit()

    except Exception as e:
        result.error = str(e)
        logger.error(f"Retention task failed: {e}")

    return result


async def run_reclaim_gc_task(db_url: str, dry_run: bool = False) -> TaskResult:
    """Clean up stale reclaim attempts."""
    result = TaskResult("reclaim_gc")

    try:
        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)

        with Session(engine) as session:
            # Acquire GC lock
            lock_acquired = session.execute(
                text(
                    """
                SELECT m10_recovery.acquire_lock('reclaim_gc', :holder_id, 300)
            """
                ),
                {"holder_id": WORKER_ID},
            ).scalar()

            if not lock_acquired:
                result.skipped = True
                result.skip_reason = "Lock held by another instance"
                result.success = True
                return result

            try:
                # Count stale locks (held > 1 hour with no heartbeat)
                stale_count = session.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM m10_recovery.distributed_locks
                    WHERE expires_at < NOW()
                """
                    )
                ).scalar()

                result.details["stale_locks"] = stale_count

                if dry_run:
                    result.success = True
                    result.details["action"] = "dry_run"
                    return result

                # Clean up expired locks
                cleaned = session.execute(
                    text(
                        """
                    DELETE FROM m10_recovery.distributed_locks
                    WHERE expires_at < NOW()
                    RETURNING 1
                """
                    )
                ).rowcount

                session.commit()

                result.details["cleaned_locks"] = cleaned
                result.success = True
            finally:
                session.execute(
                    text(
                        """
                    SELECT m10_recovery.release_lock('reclaim_gc', :holder_id)
                """
                    ),
                    {"holder_id": WORKER_ID},
                )
                session.commit()

    except Exception as e:
        result.error = str(e)
        logger.error(f"Reclaim GC task failed: {e}")

    return result


# Task registry
TASKS = {
    "outbox": run_outbox_task,
    "dl_reconcile": run_dl_reconcile_task,
    "matview": run_matview_task,
    "retention": run_retention_task,
    "reclaim_gc": run_reclaim_gc_task,
}


async def run_orchestrator(
    db_url: str,
    tasks: Optional[List[str]] = None,
    dry_run: bool = False,
    timeout: int = TASK_TIMEOUT,
) -> Dict:
    """Run the maintenance orchestrator."""

    if tasks is None:
        tasks = TASK_ORDER
    else:
        # Validate task names
        invalid = set(tasks) - set(TASKS.keys())
        if invalid:
            raise ValueError(f"Unknown tasks: {invalid}")

    results = []
    start_time = time.time()

    for task_name in tasks:
        if task_name not in TASKS:
            continue

        task_func = TASKS[task_name]
        task_start = time.time()

        logger.info(f"Running task: {task_name}")

        try:
            # Run with timeout
            result = await asyncio.wait_for(
                task_func(db_url, dry_run=dry_run),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            result = TaskResult(task_name)
            result.error = f"Task timed out after {timeout}s"
            logger.error(f"Task {task_name} timed out")
        except Exception as e:
            result = TaskResult(task_name)
            result.error = str(e)
            logger.error(f"Task {task_name} failed: {e}")

        result.duration_seconds = time.time() - task_start
        results.append(result)

        if result.success:
            logger.info(f"Task {task_name} completed in {result.duration_seconds:.2f}s")
        else:
            logger.error(f"Task {task_name} failed: {result.error}")

    total_duration = time.time() - start_time
    success_count = sum(1 for r in results if r.success)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "total_duration_seconds": round(total_duration, 3),
        "tasks_run": len(results),
        "tasks_succeeded": success_count,
        "tasks_failed": len(results) - success_count,
        "all_success": success_count == len(results),
        "results": [r.to_dict() for r in results],
    }


def main():
    parser = argparse.ArgumentParser(description="M10 Maintenance Orchestrator")
    parser.add_argument(
        "--tasks",
        type=str,
        help=f"Comma-separated list of tasks to run. Available: {','.join(TASK_ORDER)}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report status without making changes",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=TASK_TIMEOUT,
        help=f"Timeout per task in seconds (default: {TASK_TIMEOUT})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
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

    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable required")
        sys.exit(1)

    # Parse tasks
    tasks = None
    if args.tasks:
        tasks = [t.strip() for t in args.tasks.split(",")]

    # Run orchestrator
    logger.info("=== M10 Maintenance Orchestrator ===")
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    results = asyncio.run(
        run_orchestrator(
            db_url=db_url,
            tasks=tasks,
            dry_run=args.dry_run,
            timeout=args.timeout,
        )
    )

    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print()
        print("=== Orchestrator Results ===")
        print(f"Total Duration: {results['total_duration_seconds']:.2f}s")
        print(f"Tasks: {results['tasks_succeeded']}/{results['tasks_run']} succeeded")
        print()

        for task_result in results["results"]:
            status = "✓" if task_result["success"] else "✗"
            if task_result["skipped"]:
                status = "⊘"

            print(
                f"  {status} {task_result['name']} ({task_result['duration_seconds']:.2f}s)"
            )

            if task_result["error"]:
                print(f"      Error: {task_result['error']}")
            elif task_result["skipped"]:
                print(f"      Skipped: {task_result['skip_reason']}")
            else:
                for key, value in task_result["details"].items():
                    print(f"      {key}: {value}")

        print()
        if results["all_success"]:
            print("Status: ALL TASKS SUCCEEDED")
        else:
            print("Status: SOME TASKS FAILED")
            sys.exit(1)


if __name__ == "__main__":
    main()
