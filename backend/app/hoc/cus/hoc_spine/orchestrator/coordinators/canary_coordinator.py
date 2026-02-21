# capability_id: CAP-012
# Layer: L4 — HOC Spine (Coordinator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — canary validation scheduling and execution
# Callers: Scheduler / cron jobs
# Allowed Imports: hoc_spine, hoc.cus.analytics.L5_engines (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3A1 Wiring, PIN-520 (L4 Transaction Ownership)
# artifact_class: CODE

"""
Canary Coordinator (PIN-513 Batch 3A1 Wiring)

L4 coordinator that owns scheduled canary validation runs.

Wires from analytics/L5_engines/canary_engine.py:
- run_canary(sample_count, drift_threshold, session)

Flow:
  Scheduler / Cron
    → CanaryCoordinator.run(...)
        → canary_engine.run_canary(..., session)
        → L4 commits (transaction boundary owner)

Transaction Ownership (PIN-520):
  L4 coordinator creates session and owns commit/rollback.
  L5 engine and L6 driver do NOT commit.
"""

import logging
from typing import Any

logger = logging.getLogger("nova.hoc_spine.coordinators.canary")


class CanaryCoordinator:
    """L4 coordinator: canary validation scheduling and execution.

    System-level safety mechanism — no API surface.
    Transaction boundary owner for canary DB operations.
    """

    async def run(
        self,
        sample_count: int = 100,
        drift_threshold: float = 0.2,
    ) -> Any:
        """Execute a canary validation run.

        L4 owns transaction boundary: creates session, commits on success.
        """
        from app.db import get_async_session
        from app.hoc.cus.analytics.L5_engines.canary_engine import run_canary

        async with get_async_session() as session:
            result = await run_canary(
                sample_count=sample_count,
                drift_threshold=drift_threshold,
                session=session,
            )
            # L4 owns transaction boundary
            await session.commit()

            logger.info(
                "canary_run_completed",
                extra={
                    "sample_count": sample_count,
                    "drift_threshold": drift_threshold,
                    "passed": result.passed,
                },
            )
            return result
