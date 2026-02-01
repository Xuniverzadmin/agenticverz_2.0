# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: scheduler (cron / job runner)
#   Execution: async
# Role: Analytics snapshot handler — owns scheduled snapshot computation lifecycle
# Callers: Scheduler (systemd timer, cron), OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.analytics.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-513 Wiring Plan (cost_snapshots_engine)
# artifact_class: CODE

"""
Analytics Snapshot Handler (L4 Orchestrator)

Owns the scheduled lifecycle for cost snapshot computation.
Routes to CostSnapshotsEngine (L5) via driver protocol injection.

Responsibilities:
- Owns schedule trigger authority (no L5 engine may self-trigger)
- Iterates tenants
- Injects CostSnapshotsDriverProtocol
- Calls engine entrypoints: hourly snapshots, daily baselines

Flow:
  Cron / Scheduler
    → AnalyticsSnapshotHandler.run_hourly()
        → CostSnapshotsEngine.compute_hourly_snapshot(driver)
    → AnalyticsSnapshotHandler.run_daily()
        → CostSnapshotsEngine.compute_daily_snapshot(driver)
        → CostSnapshotsEngine.compute_baselines(driver)
"""

import logging
from typing import Any

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)

logger = logging.getLogger("nova.hoc_spine.handlers.analytics_snapshot")


class AnalyticsSnapshotHandler:
    """
    Handler for analytics.snapshot operations.

    Dispatches scheduled snapshot computation to CostSnapshotsEngine (L5).
    The engine is pure business logic; the driver is injected by this handler.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L5_engines.cost_snapshots_engine import (
            SnapshotComputer,
            BaselineComputer,
            SnapshotAnomalyDetector,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        dispatch = {
            "run_hourly": self._run_hourly,
            "run_daily": self._run_daily,
            "evaluate_anomalies": self._evaluate_anomalies,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown snapshot method: {method_name}", "UNKNOWN_METHOD"
            )

        return await method(ctx)

    async def _run_hourly(self, ctx: OperationContext) -> OperationResult:
        """Run hourly snapshot computation for tenant."""
        from app.hoc.cus.analytics.L5_engines.cost_snapshots_engine import (
            SnapshotComputer,
        )
        from app.hoc.cus.analytics.L6_drivers.cost_snapshots_driver import (
            get_cost_snapshots_driver,
        )

        driver = get_cost_snapshots_driver(session=ctx.session)
        computer = SnapshotComputer(driver=driver)
        result = await computer.compute_hourly_snapshot(tenant_id=ctx.tenant_id)
        return OperationResult.ok(result)

    async def _run_daily(self, ctx: OperationContext) -> OperationResult:
        """Run daily snapshot + baseline computation for tenant."""
        from app.hoc.cus.analytics.L5_engines.cost_snapshots_engine import (
            SnapshotComputer,
            BaselineComputer,
        )
        from app.hoc.cus.analytics.L6_drivers.cost_snapshots_driver import (
            get_cost_snapshots_driver,
        )

        driver = get_cost_snapshots_driver(session=ctx.session)
        computer = SnapshotComputer(driver=driver)
        baseline = BaselineComputer(driver=driver)

        snapshot_result = await computer.compute_daily_snapshot(tenant_id=ctx.tenant_id)
        baseline_result = await baseline.compute_baselines(tenant_id=ctx.tenant_id)

        return OperationResult.ok({
            "snapshot": snapshot_result,
            "baselines": baseline_result,
        })

    async def _evaluate_anomalies(self, ctx: OperationContext) -> OperationResult:
        """Evaluate snapshots for anomalies."""
        from app.hoc.cus.analytics.L5_engines.cost_snapshots_engine import (
            SnapshotAnomalyDetector,
        )
        from app.hoc.cus.analytics.L6_drivers.cost_snapshots_driver import (
            get_cost_snapshots_driver,
        )

        driver = get_cost_snapshots_driver(session=ctx.session)
        detector = SnapshotAnomalyDetector(driver=driver)

        snapshot_id = ctx.params.get("snapshot_id")
        if not snapshot_id:
            return OperationResult.fail(
                "Missing 'snapshot_id' in params", "MISSING_PARAM"
            )

        result = await detector.evaluate_snapshot(snapshot_id=snapshot_id)
        return OperationResult.ok(result)


def register(registry: OperationRegistry) -> None:
    """Register analytics.snapshot operation with the OperationRegistry."""
    handler = AnalyticsSnapshotHandler()
    registry.register("analytics.snapshot", handler)
