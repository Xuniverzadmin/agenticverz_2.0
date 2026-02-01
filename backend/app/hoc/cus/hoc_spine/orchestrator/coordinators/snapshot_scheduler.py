# Layer: L4 — HOC Spine (Coordinator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — scheduled snapshot batch execution
# Callers: Cron / systemd timer / APScheduler
# Allowed Imports: hoc_spine, hoc.cus.analytics.L5_engines (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 4 Final Wiring
# artifact_class: CODE

"""
Snapshot Scheduler (PIN-513 Batch 4 Final Wiring)

L4 coordinator that owns multi-tenant scheduled snapshot batch execution.
Never called via handler or API — only via cron/scheduler.

Wires from analytics/L5_engines/cost_snapshots_engine.py:
- run_hourly_snapshot_job(driver, tenant_ids)
- run_daily_snapshot_and_baseline_job(driver, tenant_ids)

Flow:
  Cron / systemd timer
    → SnapshotScheduler.run_hourly(driver, tenant_ids)
        → cost_snapshots_engine.run_hourly_snapshot_job(...)
    → SnapshotScheduler.run_daily(driver, tenant_ids)
        → cost_snapshots_engine.run_daily_snapshot_and_baseline_job(...)
"""

import logging
from typing import Any, List

logger = logging.getLogger("nova.hoc_spine.coordinators.snapshot_scheduler")


class SnapshotScheduler:
    """L4 coordinator: scheduled snapshot batch execution.

    Entry points for cron/systemd timers only.
    Not API-driven. System authority.
    """

    async def run_hourly(
        self,
        driver: Any,
        tenant_ids: List[str],
    ) -> dict:
        """Run hourly snapshot job for multiple tenants.

        Schedule via cron every hour at :05.
        """
        from app.hoc.cus.analytics.L5_engines.cost_snapshots_engine import (
            run_hourly_snapshot_job,
        )

        result = await run_hourly_snapshot_job(
            driver=driver,
            tenant_ids=tenant_ids,
        )
        logger.info(
            "hourly_snapshot_job_completed",
            extra={
                "tenant_count": len(tenant_ids),
                "success": len(result.get("success", [])),
                "failed": len(result.get("failed", [])),
            },
        )
        return result

    async def run_daily(
        self,
        driver: Any,
        tenant_ids: List[str],
    ) -> dict:
        """Run daily snapshot + baseline + anomaly detection for multiple tenants.

        Schedule via cron daily at 00:30.
        """
        from app.hoc.cus.analytics.L5_engines.cost_snapshots_engine import (
            run_daily_snapshot_and_baseline_job,
        )

        result = await run_daily_snapshot_and_baseline_job(
            driver=driver,
            tenant_ids=tenant_ids,
        )
        logger.info(
            "daily_snapshot_job_completed",
            extra={
                "tenant_count": len(tenant_ids),
                "snapshots": len(result.get("snapshots", [])),
                "baselines": len(result.get("baselines", [])),
                "anomalies": len(result.get("anomalies", [])),
            },
        )
        return result
