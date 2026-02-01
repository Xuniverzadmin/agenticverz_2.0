# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — orphan recovery orchestration (session + scheduling authority)
# Callers: App startup (lifespan), ops dashboard (L2 API)
# Allowed Imports: hoc_spine, hoc.cus.activity.L6_drivers (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 1A Wiring, PB-S2 guarantee
# artifact_class: CODE

"""
Orphan Recovery Handler (PIN-513 Batch 1A Wiring)

L4 handler that owns orphan recovery orchestration.

Extracted from activity/L6_drivers/orphan_recovery_driver.py which
violated "no implicit execution" — the driver was creating its own
sessions and scheduling itself.

L4 owns:
- Session lifecycle
- Scheduling authority (startup hook / cron)
- Transaction commit boundary

L6 provides:
- detect_orphaned_runs(session, threshold) → list[WorkerRun]
- mark_run_as_crashed(session, run, reason) → bool

Flow:
  App startup
    → OrphanRecoveryHandler.execute(threshold_minutes)
        → detect_orphaned_runs(session, threshold)
        → mark_run_as_crashed(session, run) [per orphan]

  GET /ops/crash-recovery
    → OrphanRecoveryHandler.get_summary()
        → query crashed runs (L6 read)
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("nova.hoc_spine.handlers.orphan_recovery")

# Configuration (read once, L4 owns interpretation)
ORPHAN_THRESHOLD_MINUTES = int(os.getenv("ORPHAN_THRESHOLD_MINUTES", "30"))
RECOVERY_ENABLED = os.getenv("ORPHAN_RECOVERY_ENABLED", "true").lower() == "true"


class OrphanRecoveryHandler:
    """L4 handler: orphan recovery orchestration.

    Owns session lifecycle and scheduling authority.
    L6 driver provides pure data primitives only.
    """

    async def execute(
        self,
        threshold_minutes: Optional[int] = None,
    ) -> dict:
        """Run orphan recovery — called on app startup.

        Args:
            threshold_minutes: Override for orphan threshold (default from env)

        Returns:
            Summary dict with detected, recovered, failed, runs, enabled
        """
        if not RECOVERY_ENABLED:
            logger.info("orphan_recovery_disabled")
            return {
                "detected": 0,
                "recovered": 0,
                "failed": 0,
                "runs": [],
                "enabled": False,
            }

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
            from app.db import get_async_session

            async with get_async_session() as session:
                from app.hoc.cus.activity.L6_drivers.orphan_recovery_driver import (
                    detect_orphaned_runs,
                    mark_run_as_crashed,
                )

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

                # L4 owns commit boundary
                await session.commit()

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

    async def get_summary(self) -> dict:
        """Get crash recovery summary for ops dashboard.

        Returns:
            Dict with total_crashed count and recent_crashes list
        """
        from sqlalchemy import func, select

        from app.db import get_async_session
        from app.models.tenant import WorkerRun

        async with get_async_session() as session:
            count_result = await session.execute(
                select(func.count())
                .select_from(WorkerRun)
                .where(WorkerRun.status == "crashed")
            )
            crashed_count = count_result.scalar() or 0

            recent_result = await session.execute(
                select(WorkerRun)
                .where(WorkerRun.status == "crashed")
                .order_by(WorkerRun.completed_at.desc())
                .limit(10)
            )
            recent_crashes = recent_result.scalars().all()

            return {
                "total_crashed": crashed_count,
                "recent_crashes": [
                    {
                        "run_id": r.id,
                        "worker_id": r.worker_id,
                        "tenant_id": r.tenant_id,
                        "created_at": (
                            r.created_at.isoformat() if r.created_at else None
                        ),
                        "crashed_at": (
                            r.completed_at.isoformat()
                            if r.completed_at
                            else None
                        ),
                        "error": r.error,
                    }
                    for r in recent_crashes
                ],
            }
