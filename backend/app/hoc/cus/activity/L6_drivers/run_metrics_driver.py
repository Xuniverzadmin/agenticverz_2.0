# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: RunMetricsDriver - updates run impact signals (policy_violation, policy_draft_count)
# Temporal:
#   Trigger: hoc_spine handlers (run governance, lessons conversion)
#   Execution: sync/async (two driver classes)
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: runs.policy_violation, runs.policy_draft_count
# Database:
#   Scope: domain (activity)
#   Models: Run
# Callers: RunGovernanceHandler, PoliciesLessonsHandler (L4)
# Allowed Imports: L6, sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-519 (Run introspection), domain_linkage_plan_v1

"""
Run Metrics Driver (L6)

Pure data access for run impact signals.
No business logic - only DB updates.
"""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.hoc.activity.run_metrics_driver")


class RunMetricsDriver:
    """Sync driver for run impact signals."""

    def __init__(self, session: Any):
        self._session = session

    def mark_policy_violation(self, run_id: str, violated: bool = True) -> None:
        """Set policy_violation flag for a run."""
        self._session.execute(
            text(
                """
                UPDATE runs
                SET policy_violation = :violated,
                    updated_at = NOW()
                WHERE id = :run_id
                """
            ),
            {"run_id": run_id, "violated": violated},
        )

        logger.info(
            "run_metrics.policy_violation_set",
            extra={"run_id": run_id, "violated": violated},
        )

    def increment_policy_draft_count(self, run_id: str, delta: int = 1) -> None:
        """Increment policy_draft_count for a run."""
        self._session.execute(
            text(
                """
                UPDATE runs
                SET policy_draft_count = COALESCE(policy_draft_count, 0) + :delta,
                    updated_at = NOW()
                WHERE id = :run_id
                """
            ),
            {"run_id": run_id, "delta": delta},
        )

        logger.info(
            "run_metrics.policy_draft_count_incremented",
            extra={"run_id": run_id, "delta": delta},
        )


class RunMetricsDriverAsync:
    """Async driver for run impact signals."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def mark_policy_violation(self, run_id: str, violated: bool = True) -> None:
        """Set policy_violation flag for a run."""
        await self._session.execute(
            text(
                """
                UPDATE runs
                SET policy_violation = :violated,
                    updated_at = NOW()
                WHERE id = :run_id
                """
            ),
            {"run_id": run_id, "violated": violated},
        )

        logger.info(
            "run_metrics.policy_violation_set",
            extra={"run_id": run_id, "violated": violated},
        )


__all__ = [
    "RunMetricsDriver",
    "RunMetricsDriverAsync",
]
