# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: runs
#   Writes: runs
# Database:
#   Scope: domain (runs)
#   Models: Run
# Role: Orphan detection logic, PB-S2 truth guarantee
# Callers: L5 workers (startup), L7 ops scripts
# Allowed Imports: L6, L7 (models)
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, PIN-242 (Baseline Freeze)

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# Updates run status from "running" to "crashed" - factual state mutation
# Atomic updates with no external dependencies
FEATURE_INTENT = FeatureIntent.STATE_MUTATION
RETRY_POLICY = RetryPolicy.SAFE

"""
Orphan Run Recovery Service (PB-S2)

Detects and marks runs that were orphaned due to system crash.

PB-S2 Guarantee: Crashed runs are never silently lost.
- On startup, detect runs stuck in "queued" or "running"
- Mark them as "crashed" (factual status, not mutation)
- Log for operator visibility

Truth Constraints (S1-S6):
- We CANNOT mutate historical execution data
- We CAN update status to reflect the crash (this is a fact)
- Recovery = creating NEW retry run (PB-S1 compliant, done separately)

Reference: PIN-199 (PB-S1/S2 Implementation)
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.tenant import WorkerRun

logger = logging.getLogger("nova.services.orphan_recovery")

# Configuration
ORPHAN_THRESHOLD_MINUTES = int(os.getenv("ORPHAN_THRESHOLD_MINUTES", "30"))
RECOVERY_ENABLED = os.getenv("ORPHAN_RECOVERY_ENABLED", "true").lower() == "true"


async def detect_orphaned_runs(
    session: AsyncSession,
    threshold_minutes: int = ORPHAN_THRESHOLD_MINUTES,
) -> list[WorkerRun]:
    """
    Detect runs that appear to be orphaned.

    A run is orphaned if:
    - Status is "running" and created > threshold_minutes ago
    - Status is "queued" and created > threshold_minutes ago

    The threshold prevents marking in-progress runs as orphaned.
    """
    threshold_time = datetime.utcnow() - timedelta(minutes=threshold_minutes)

    result = await session.execute(
        select(WorkerRun)
        .where(WorkerRun.status.in_(["queued", "running"]))
        .where(WorkerRun.created_at < threshold_time)
        .order_by(WorkerRun.created_at.asc())
    )

    return list(result.scalars().all())


async def mark_run_as_crashed(
    session: AsyncSession,
    run: WorkerRun,
    reason: str = "System restart - run was in progress when system crashed",
) -> bool:
    """
    Mark a run as crashed.

    This is a factual status update, not a mutation of historical data.
    The run WAS running/queued, and it DID crash. We're recording that fact.

    Returns True if successfully marked, False otherwise.
    """
    try:
        # Update status to "crashed" with error explanation
        await session.execute(
            update(WorkerRun)
            .where(WorkerRun.id == run.id)
            .values(
                status="crashed",
                error=reason,
                completed_at=datetime.utcnow(),
            )
        )

        logger.info(
            "orphan_run_marked_crashed",
            extra={
                "run_id": run.id,
                "worker_id": run.worker_id,
                "tenant_id": run.tenant_id,
                "original_status": run.status,
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "reason": reason,
            },
        )
        return True

    except Exception as e:
        logger.error(
            "failed_to_mark_orphan_crashed",
            extra={"run_id": run.id, "error": str(e)},
        )
        return False


async def recover_orphaned_runs(
    threshold_minutes: Optional[int] = None,
) -> dict:
    """
    Main recovery function - called on startup.

    Detects and marks all orphaned runs as crashed.

    Returns a summary dict with:
    - detected: number of orphaned runs found
    - recovered: number successfully marked as crashed
    - failed: number that failed to mark
    - runs: list of run IDs processed
    """
    if not RECOVERY_ENABLED:
        logger.info("orphan_recovery_disabled")
        return {"detected": 0, "recovered": 0, "failed": 0, "runs": [], "enabled": False}

    threshold = threshold_minutes or ORPHAN_THRESHOLD_MINUTES

    logger.info(
        "orphan_recovery_starting",
        extra={"threshold_minutes": threshold},
    )

    result = {
        "detected": 0,
        "recovered": 0,
        "failed": 0,
        "runs": [],
        "enabled": True,
    }

    try:
        async with get_async_session() as session:
            orphans = await detect_orphaned_runs(session, threshold)
            result["detected"] = len(orphans)

            if not orphans:
                logger.info("no_orphaned_runs_found")
                return result

            logger.warning(
                "orphaned_runs_detected",
                extra={
                    "count": len(orphans),
                    "run_ids": [r.id for r in orphans],
                },
            )

            for run in orphans:
                success = await mark_run_as_crashed(session, run)
                result["runs"].append(
                    {
                        "run_id": run.id,
                        "worker_id": run.worker_id,
                        "original_status": run.status,
                        "marked_crashed": success,
                    }
                )

                if success:
                    result["recovered"] += 1
                else:
                    result["failed"] += 1

            # NO COMMIT — L4 coordinator owns transaction boundary

            logger.info(
                "orphan_recovery_complete",
                extra={
                    "detected": result["detected"],
                    "recovered": result["recovered"],
                    "failed": result["failed"],
                },
            )

    except Exception as e:
        logger.error(
            "orphan_recovery_failed",
            extra={"error": str(e)},
            exc_info=True,
        )
        result["error"] = str(e)

    return result


async def get_crash_recovery_summary() -> dict:
    """
    Get a summary of crashed runs for operator visibility.

    Returns counts and recent crashed runs for /ops dashboard.
    """
    async with get_async_session() as session:
        # Count crashed runs
        from sqlalchemy import func

        count_result = await session.execute(
            select(func.count()).select_from(WorkerRun).where(WorkerRun.status == "crashed")
        )
        crashed_count = count_result.scalar() or 0

        # Get recent crashed runs
        recent_result = await session.execute(
            select(WorkerRun).where(WorkerRun.status == "crashed").order_by(WorkerRun.completed_at.desc()).limit(10)
        )
        recent_crashes = recent_result.scalars().all()

        return {
            "total_crashed": crashed_count,
            "recent_crashes": [
                {
                    "run_id": r.id,
                    "worker_id": r.worker_id,
                    "tenant_id": r.tenant_id,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "crashed_at": r.completed_at.isoformat() if r.completed_at else None,
                    "error": r.error,
                }
                for r in recent_crashes
            ],
        }
