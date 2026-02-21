# capability_id: CAP-012
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# NOTE: Renamed orphan_recovery.py → orphan_recovery_driver.py (2026-01-31)
#       per BANNED_NAMING rule (L6 files must be *_driver.py)
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
# Callers: OrphanRecoveryHandler (L4)
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
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import WorkerRun

logger = logging.getLogger("nova.services.orphan_recovery")

# Configuration (default threshold; L4 handler may override)
ORPHAN_THRESHOLD_MINUTES = int(os.getenv("ORPHAN_THRESHOLD_MINUTES", "30"))


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


# =============================================================================
# REMOVED (PIN-513 Batch 1A): recover_orphaned_runs, get_crash_recovery_summary
# Moved to L4: hoc_spine/orchestrator/handlers/orphan_recovery_handler.py
# Reason: L6 must not create sessions or schedule itself.
# =============================================================================
