# Layer: L5 — Domain Engine
# NOTE: Renamed cost_snapshots.py → cost_snapshots_engine.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api|worker
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: (via CostSnapshotsDriverProtocol)
#   Writes: (via CostSnapshotsDriverProtocol)
# Role: Cost snapshot computation — pure business logic
# Callers: workers, cost services
# Allowed Imports: L5, L5_schemas
# Forbidden Imports: L1, L2, L3, L6, sqlalchemy
# Forbidden: session.commit(), session.rollback(), session.execute()
# Note: DB operations extracted to L6_drivers/cost_snapshots_driver.py (PIN-508 Phase 1A)
# Reference: PIN-470, PIN-508, HOC_LAYER_TOPOLOGY_V2.md

"""M27 Cost Snapshots - Deterministic Enforcement Barrier

This module provides the snapshot layer between async cost ingestion
and synchronous anomaly detection.

THE INVARIANT:
  Anomaly detection reads ONLY from complete snapshots, never from live data.

Architecture:
  cost_records (streaming, async)
         ↓
  SnapshotComputer.compute_snapshot()
         ↓
  cost_snapshots (status='complete')
         ↓
  CostAnomalyDetector.evaluate_from_snapshot()

Usage:
  # Scheduled job (e.g., every hour)
  driver = get_cost_snapshots_driver(session)
  computer = SnapshotComputer(driver)
  snapshot = await computer.compute_hourly_snapshot(tenant_id)

  # Anomaly detection (only reads complete snapshots)
  detector = SnapshotAnomalyDetector(driver)
  anomalies = await detector.evaluate_from_snapshot(snapshot.id)
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from app.hoc.cus.analytics.L5_schemas.cost_snapshot_schemas import (
    SEVERITY_THRESHOLDS,
    AnomalyEvaluation,
    CostSnapshot,
    CostSnapshotsDriverProtocol,
    EntityType,
    SnapshotAggregate,
    SnapshotBaseline,
    SnapshotStatus,
    SnapshotType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# NOTE: Enums and dataclasses in schemas/cost_snapshot_schemas.py.
# DB operations extracted to L6_drivers/cost_snapshots_driver.py (PIN-508).
# =============================================================================


# =============================================================================
# Snapshot Computer
# =============================================================================


class SnapshotComputer:
    """Computes cost snapshots from raw cost_records.

    PIN-508: Accepts CostSnapshotsDriverProtocol — no session parameter.

    Usage:
        driver = get_cost_snapshots_driver(session)
        computer = SnapshotComputer(driver)
        snapshot = await computer.compute_hourly_snapshot(tenant_id)
    """

    def __init__(self, driver: CostSnapshotsDriverProtocol):
        self._driver = driver

    async def compute_hourly_snapshot(
        self,
        tenant_id: str,
        hour: datetime | None = None,
    ) -> CostSnapshot:
        """Compute hourly snapshot for a tenant."""
        if hour is None:
            now = datetime.now(timezone.utc)
            hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)

        period_start = hour
        period_end = hour + timedelta(hours=1)

        return await self._compute_snapshot(
            tenant_id=tenant_id,
            snapshot_type=SnapshotType.HOURLY,
            period_start=period_start,
            period_end=period_end,
        )

    async def compute_daily_snapshot(
        self,
        tenant_id: str,
        date: datetime | None = None,
    ) -> CostSnapshot:
        """Compute daily snapshot for a tenant."""
        if date is None:
            now = datetime.now(timezone.utc)
            date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        period_start = date
        period_end = date + timedelta(days=1)

        return await self._compute_snapshot(
            tenant_id=tenant_id,
            snapshot_type=SnapshotType.DAILY,
            period_start=period_start,
            period_end=period_end,
        )

    async def _compute_snapshot(
        self,
        tenant_id: str,
        snapshot_type: SnapshotType,
        period_start: datetime,
        period_end: datetime,
    ) -> CostSnapshot:
        """Internal snapshot computation."""
        import time

        start_time = time.time()

        snapshot = CostSnapshot.create(
            tenant_id=tenant_id,
            snapshot_type=snapshot_type,
            period_start=period_start,
            period_end=period_end,
        )
        snapshot.status = SnapshotStatus.COMPUTING

        try:
            await self._driver.insert_snapshot(snapshot)

            aggregates = await self._driver.aggregate_cost_records(
                tenant_id=tenant_id,
                snapshot_id=snapshot.id,
                period_start=period_start,
                period_end=period_end,
            )

            for agg in aggregates:
                baseline = await self._driver.get_current_baseline(
                    tenant_id=tenant_id,
                    entity_type=agg.entity_type,
                    entity_id=agg.entity_id,
                    window_days=7,
                )
                if baseline:
                    agg.baseline_7d_avg_cents = baseline.avg_daily_cost_cents
                    if baseline.avg_daily_cost_cents > 0:
                        agg.deviation_from_7d_pct = (
                            (agg.total_cost_cents - baseline.avg_daily_cost_cents) / baseline.avg_daily_cost_cents
                        ) * 100

                await self._driver.insert_aggregate(agg)

            elapsed_ms = int((time.time() - start_time) * 1000)
            snapshot.status = SnapshotStatus.COMPLETE
            snapshot.records_processed = sum(a.request_count for a in aggregates)
            snapshot.computation_ms = elapsed_ms
            snapshot.completed_at = datetime.now(timezone.utc)

            await self._driver.update_snapshot(snapshot)

            logger.info(f"Snapshot complete: {snapshot.id} ({snapshot.records_processed} records, {elapsed_ms}ms)")

        except Exception as e:
            snapshot.status = SnapshotStatus.FAILED
            snapshot.error_message = str(e)
            await self._driver.update_snapshot(snapshot)
            logger.error(f"Snapshot failed: {snapshot.id} - {e}")

        return snapshot


# =============================================================================
# Baseline Computer
# =============================================================================


class BaselineComputer:
    """Computes rolling baselines from historical snapshots.

    PIN-508: Accepts CostSnapshotsDriverProtocol — no session parameter.
    """

    def __init__(self, driver: CostSnapshotsDriverProtocol):
        self._driver = driver

    async def compute_baselines(
        self,
        tenant_id: str,
        window_days: int = 7,
    ) -> list[SnapshotBaseline]:
        """Compute baselines for all entities from historical snapshots."""
        baselines: list[SnapshotBaseline] = []

        rows = await self._driver.compute_baselines(tenant_id, window_days)

        for row in rows:
            baseline = SnapshotBaseline.create(
                tenant_id=tenant_id,
                entity_type=EntityType(row["entity_type"]),
                entity_id=row["entity_id"],
                window_days=window_days,
                avg_daily_cost_cents=float(row["avg_cost"] or 0),
                avg_daily_requests=float(row["avg_requests"] or 0),
                samples_count=int(row["samples"]),
                stddev=float(row["stddev_cost"]) if row["stddev_cost"] else None,
                max_cost=float(row["max_cost"]) if row["max_cost"] else None,
                min_cost=float(row["min_cost"]) if row["min_cost"] else None,
                last_snapshot_id=row["last_snapshot"],
            )
            baselines.append(baseline)
            await self._driver.insert_baseline(baseline)

        return baselines


# =============================================================================
# Snapshot-Based Anomaly Detector
# =============================================================================


class SnapshotAnomalyDetector:
    """Detects anomalies from complete snapshots only.

    THE INVARIANT:
      This detector NEVER reads from cost_records.
      It ONLY reads from complete snapshots.

    PIN-508: Accepts CostSnapshotsDriverProtocol — no session parameter.
    """

    def __init__(self, driver: CostSnapshotsDriverProtocol):
        self._driver = driver

    async def evaluate_snapshot(
        self,
        snapshot_id: str,
        threshold_pct: float = 200,
    ) -> list[AnomalyEvaluation]:
        """Evaluate all aggregates in a snapshot for anomalies."""
        evaluations: list[AnomalyEvaluation] = []

        snapshot = await self._driver.get_snapshot(snapshot_id)
        if not snapshot or snapshot.status != SnapshotStatus.COMPLETE:
            logger.warning(f"Cannot evaluate incomplete snapshot: {snapshot_id}")
            return evaluations

        rows = await self._driver.get_aggregates_with_baseline(snapshot_id)

        for row in rows:
            deviation = row.get("deviation_from_7d_pct") or 0
            triggered = deviation >= threshold_pct

            severity = None
            if triggered:
                if deviation >= SEVERITY_THRESHOLDS["critical"]:
                    severity = "critical"
                elif deviation >= SEVERITY_THRESHOLDS["high"]:
                    severity = "high"
                elif deviation >= SEVERITY_THRESHOLDS["medium"]:
                    severity = "medium"
                else:
                    severity = "low"

            eval_id = (
                f"eval_{hashlib.sha256(f'{snapshot_id}:{row['entity_type']}:{row['entity_id']}'.encode()).hexdigest()[:16]}"
            )
            evaluation = AnomalyEvaluation(
                id=eval_id,
                tenant_id=row["tenant_id"],
                snapshot_id=snapshot_id,
                entity_type=EntityType(row["entity_type"]),
                entity_id=row["entity_id"],
                current_value_cents=row["total_cost_cents"],
                baseline_value_cents=row["baseline_7d_avg_cents"],
                threshold_pct=threshold_pct,
                deviation_pct=deviation,
                triggered=triggered,
                severity_computed=severity,
                evaluation_reason=f"{'TRIGGERED' if triggered else 'OK'}: {deviation:.1f}% deviation (threshold: {threshold_pct}%)",
            )
            evaluations.append(evaluation)

            await self._driver.insert_evaluation(evaluation)

            if triggered:
                anomaly_type_map = {
                    EntityType.USER: "user_spike",
                    EntityType.FEATURE: "feature_spike",
                    EntityType.MODEL: "model_spike",
                    EntityType.TENANT: "tenant_spike",
                }
                anomaly_id = f"anom_{hashlib.sha256(f'{evaluation.id}'.encode()).hexdigest()[:16]}"
                anomaly_type = anomaly_type_map.get(evaluation.entity_type, "unknown")

                await self._driver.insert_anomaly(
                    anomaly_id=anomaly_id,
                    tenant_id=evaluation.tenant_id,
                    anomaly_type=anomaly_type,
                    severity=evaluation.severity_computed,
                    entity_type=evaluation.entity_type.value,
                    entity_id=evaluation.entity_id,
                    current_value_cents=evaluation.current_value_cents,
                    expected_value_cents=evaluation.baseline_value_cents,
                    deviation_pct=evaluation.deviation_pct,
                    threshold_pct=evaluation.threshold_pct,
                    message=f"Cost spike detected from snapshot {snapshot.id}: {evaluation.deviation_pct:.1f}% above 7-day baseline",
                    snapshot_id=snapshot.id,
                    detected_at=evaluation.evaluated_at,
                )
                evaluation.anomaly_id = anomaly_id

                logger.info(f"Created anomaly {anomaly_id} from snapshot evaluation")

        return evaluations


# =============================================================================
# Convenience Functions
# =============================================================================


async def run_hourly_snapshot_job(driver: CostSnapshotsDriverProtocol, tenant_ids: list[str]) -> dict:
    """Run hourly snapshot job for multiple tenants.

    Schedule this via cron/systemd timer every hour at :05.
    PIN-508: Accepts driver Protocol, not session.
    """
    results: dict[str, list] = {"success": [], "failed": []}
    computer = SnapshotComputer(driver)

    for tenant_id in tenant_ids:
        try:
            snapshot = await computer.compute_hourly_snapshot(tenant_id)
            if snapshot.status == SnapshotStatus.COMPLETE:
                results["success"].append(tenant_id)
            else:
                results["failed"].append({"tenant_id": tenant_id, "error": snapshot.error_message})
        except Exception as e:
            results["failed"].append({"tenant_id": tenant_id, "error": str(e)})

    return results


async def run_daily_snapshot_and_baseline_job(driver: CostSnapshotsDriverProtocol, tenant_ids: list[str]) -> dict:
    """Run daily snapshot and baseline computation for multiple tenants.

    Schedule this via cron/systemd timer daily at 00:30.
    PIN-508: Accepts driver Protocol, not session.
    """
    results: dict[str, list] = {"snapshots": [], "baselines": [], "anomalies": []}

    snapshot_computer = SnapshotComputer(driver)
    baseline_computer = BaselineComputer(driver)
    detector = SnapshotAnomalyDetector(driver)

    for tenant_id in tenant_ids:
        snapshot = await snapshot_computer.compute_daily_snapshot(tenant_id)
        results["snapshots"].append({
            "tenant_id": tenant_id,
            "snapshot_id": snapshot.id,
            "status": snapshot.status.value,
        })

        if snapshot.status == SnapshotStatus.COMPLETE:
            baselines = await baseline_computer.compute_baselines(tenant_id)
            results["baselines"].append({
                "tenant_id": tenant_id,
                "count": len(baselines),
            })

            evaluations = await detector.evaluate_snapshot(snapshot.id)
            triggered = [e for e in evaluations if e.triggered]
            results["anomalies"].append({
                "tenant_id": tenant_id,
                "evaluated": len(evaluations),
                "triggered": len(triggered),
            })

    return results
