# Layer: L4 — HOC Spine (Coordinator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — canary validation scheduling and execution
# Callers: Scheduler / cron jobs
# Allowed Imports: hoc_spine, hoc.cus.analytics.L5_engines (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3A1 Wiring
# artifact_class: CODE

"""
Canary Coordinator (PIN-513 Batch 3A1 Wiring)

L4 coordinator that owns scheduled canary validation runs.

Wires from analytics/L5_engines/canary_engine.py:
- run_canary(sample_count, drift_threshold)

Flow:
  Scheduler / Cron
    → CanaryCoordinator.run(...)
        → canary_engine.run_canary(...)
"""

import logging
from typing import Any

logger = logging.getLogger("nova.hoc_spine.coordinators.canary")


class CanaryCoordinator:
    """L4 coordinator: canary validation scheduling and execution.

    System-level safety mechanism — no API surface.
    """

    async def run(
        self,
        sample_count: int = 100,
        drift_threshold: float = 0.2,
    ) -> Any:
        """Execute a canary validation run."""
        from app.hoc.cus.analytics.L5_engines.canary_engine import run_canary

        result = await run_canary(
            sample_count=sample_count,
            drift_threshold=drift_threshold,
        )
        logger.info(
            "canary_run_completed",
            extra={
                "sample_count": sample_count,
                "drift_threshold": drift_threshold,
            },
        )
        return result
