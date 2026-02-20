# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api|worker (via L5 engine)
#   Execution: async
# Data Access:
#   Reads: cost_records, cost_snapshots, cost_snapshot_aggregates, cost_snapshot_baselines, cost_anomalies
#   Writes: cost_snapshots, cost_snapshot_aggregates, cost_snapshot_baselines, cost_anomaly_evaluations, cost_anomalies
# Role: Data access for cost snapshot operations (extracted from cost_snapshots_engine.py)
# Callers: cost_snapshots_engine.py (L5)
# Allowed Imports: L6, L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-508 Phase 1A
# artifact_class: CODE

"""
Cost Snapshots Driver (L6)

Pure database operations for cost snapshot system.
Extracted from cost_snapshots_engine.py per PIN-508 Phase 1A.

Implements CostSnapshotsDriverProtocol for typed L5↔L6 boundary.
NO business logic — only DB operations.
NO session.commit() — L4 coordinator owns transaction boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.hoc.cus.analytics.L5_schemas.cost_snapshot_schemas import (
    AnomalyEvaluation,
    CostSnapshot,
    EntityType,
    SnapshotAggregate,
    SnapshotBaseline,
    SnapshotStatus,
    SnapshotType,
)


class CostSnapshotsDriver:
    """L6 driver for cost snapshot database operations.

    Implements CostSnapshotsDriverProtocol.
    Pure data access — no business logic.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def insert_snapshot(self, snapshot: CostSnapshot) -> None:
        query = """
            INSERT INTO cost_snapshots (
                id, tenant_id, snapshot_type, period_start, period_end,
                status, version, created_at
            ) VALUES (
                :id, :tenant_id, :snapshot_type, :period_start, :period_end,
                :status, :version, :created_at
            )
            ON CONFLICT (tenant_id, snapshot_type, period_start)
            DO UPDATE SET status = :status, version = cost_snapshots.version + 1
        """
        await self._session.execute(
            text(query),
            {
                "id": snapshot.id,
                "tenant_id": snapshot.tenant_id,
                "snapshot_type": snapshot.snapshot_type.value,
                "period_start": snapshot.period_start,
                "period_end": snapshot.period_end,
                "status": snapshot.status.value,
                "version": snapshot.version,
                "created_at": snapshot.created_at,
            },
        )

    async def update_snapshot(self, snapshot: CostSnapshot) -> None:
        query = """
            UPDATE cost_snapshots SET
                status = :status,
                records_processed = :records_processed,
                computation_ms = :computation_ms,
                completed_at = :completed_at,
                error_message = :error_message
            WHERE id = :id
        """
        await self._session.execute(
            text(query),
            {
                "id": snapshot.id,
                "status": snapshot.status.value,
                "records_processed": snapshot.records_processed,
                "computation_ms": snapshot.computation_ms,
                "completed_at": snapshot.completed_at,
                "error_message": snapshot.error_message,
            },
        )

    async def insert_aggregate(self, aggregate: SnapshotAggregate) -> None:
        query = """
            INSERT INTO cost_snapshot_aggregates (
                id, snapshot_id, tenant_id, entity_type, entity_id,
                total_cost_cents, request_count, total_input_tokens, total_output_tokens,
                avg_cost_per_request_cents, avg_tokens_per_request,
                baseline_7d_avg_cents, baseline_30d_avg_cents,
                deviation_from_7d_pct, deviation_from_30d_pct,
                created_at
            ) VALUES (
                :id, :snapshot_id, :tenant_id, :entity_type, :entity_id,
                :total_cost_cents, :request_count, :total_input_tokens, :total_output_tokens,
                :avg_cost_per_request_cents, :avg_tokens_per_request,
                :baseline_7d_avg_cents, :baseline_30d_avg_cents,
                :deviation_from_7d_pct, :deviation_from_30d_pct,
                :created_at
            )
            ON CONFLICT (snapshot_id, entity_type, entity_id) DO UPDATE SET
                total_cost_cents = :total_cost_cents,
                request_count = :request_count,
                deviation_from_7d_pct = :deviation_from_7d_pct
        """
        await self._session.execute(
            text(query),
            {
                "id": aggregate.id,
                "snapshot_id": aggregate.snapshot_id,
                "tenant_id": aggregate.tenant_id,
                "entity_type": aggregate.entity_type.value if isinstance(aggregate.entity_type, EntityType) else aggregate.entity_type,
                "entity_id": aggregate.entity_id,
                "total_cost_cents": aggregate.total_cost_cents,
                "request_count": aggregate.request_count,
                "total_input_tokens": aggregate.total_input_tokens,
                "total_output_tokens": aggregate.total_output_tokens,
                "avg_cost_per_request_cents": aggregate.avg_cost_per_request_cents,
                "avg_tokens_per_request": aggregate.avg_tokens_per_request,
                "baseline_7d_avg_cents": aggregate.baseline_7d_avg_cents,
                "baseline_30d_avg_cents": aggregate.baseline_30d_avg_cents,
                "deviation_from_7d_pct": aggregate.deviation_from_7d_pct,
                "deviation_from_30d_pct": aggregate.deviation_from_30d_pct,
                "created_at": datetime.now(timezone.utc),
            },
        )

    async def get_current_baseline(
        self,
        tenant_id: str,
        entity_type: EntityType,
        entity_id: str | None,
        window_days: int,
    ) -> SnapshotBaseline | None:
        query = """
            SELECT * FROM cost_snapshot_baselines
            WHERE tenant_id = :tenant_id
              AND entity_type = :entity_type
              AND (entity_id = :entity_id OR (entity_id IS NULL AND :entity_id IS NULL))
              AND window_days = :window_days
              AND is_current = true
            ORDER BY computed_at DESC
            LIMIT 1
        """
        result = await self._session.execute(
            text(query),
            {
                "tenant_id": tenant_id,
                "entity_type": entity_type.value if isinstance(entity_type, EntityType) else entity_type,
                "entity_id": entity_id,
                "window_days": window_days,
            },
        )
        row = result.fetchone()
        if row:
            return SnapshotBaseline(
                id=row.id,
                tenant_id=row.tenant_id,
                entity_type=EntityType(row.entity_type),
                entity_id=row.entity_id,
                avg_daily_cost_cents=row.avg_daily_cost_cents,
                stddev_daily_cost_cents=row.stddev_daily_cost_cents,
                avg_daily_requests=row.avg_daily_requests,
                max_daily_cost_cents=row.max_daily_cost_cents,
                min_daily_cost_cents=row.min_daily_cost_cents,
                window_days=row.window_days,
                samples_count=row.samples_count,
                computed_at=row.computed_at,
                valid_until=row.valid_until,
                is_current=row.is_current,
                last_snapshot_id=row.last_snapshot_id,
            )
        return None

    async def aggregate_cost_records(
        self,
        tenant_id: str,
        snapshot_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> list[SnapshotAggregate]:
        aggregates: list[SnapshotAggregate] = []
        params = {
            "tenant_id": tenant_id,
            "period_start": period_start,
            "period_end": period_end,
        }

        # 1. Tenant-level
        result = await self._session.execute(text("""
            SELECT COALESCE(SUM(cost_cents), 0) as total_cost,
                   COALESCE(COUNT(*), 0) as request_count,
                   COALESCE(SUM(input_tokens), 0) as input_tokens,
                   COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :period_start AND created_at < :period_end
        """), params)
        row = result.fetchone()
        if row and row.request_count > 0:
            aggregates.append(SnapshotAggregate.create(
                snapshot_id=snapshot_id, tenant_id=tenant_id,
                entity_type=EntityType.TENANT, entity_id=None,
                total_cost_cents=float(row.total_cost), request_count=int(row.request_count),
                total_input_tokens=int(row.input_tokens), total_output_tokens=int(row.output_tokens),
            ))

        # 2. User-level
        result = await self._session.execute(text("""
            SELECT user_id, COALESCE(SUM(cost_cents), 0) as total_cost,
                   COALESCE(COUNT(*), 0) as request_count,
                   COALESCE(SUM(input_tokens), 0) as input_tokens,
                   COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :period_start AND created_at < :period_end
              AND user_id IS NOT NULL
            GROUP BY user_id
        """), params)
        for row in result.fetchall():
            aggregates.append(SnapshotAggregate.create(
                snapshot_id=snapshot_id, tenant_id=tenant_id,
                entity_type=EntityType.USER, entity_id=row.user_id,
                total_cost_cents=float(row.total_cost), request_count=int(row.request_count),
                total_input_tokens=int(row.input_tokens), total_output_tokens=int(row.output_tokens),
            ))

        # 3. Feature-level
        result = await self._session.execute(text("""
            SELECT feature_tag, COALESCE(SUM(cost_cents), 0) as total_cost,
                   COALESCE(COUNT(*), 0) as request_count,
                   COALESCE(SUM(input_tokens), 0) as input_tokens,
                   COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :period_start AND created_at < :period_end
              AND feature_tag IS NOT NULL
            GROUP BY feature_tag
        """), params)
        for row in result.fetchall():
            aggregates.append(SnapshotAggregate.create(
                snapshot_id=snapshot_id, tenant_id=tenant_id,
                entity_type=EntityType.FEATURE, entity_id=row.feature_tag,
                total_cost_cents=float(row.total_cost), request_count=int(row.request_count),
                total_input_tokens=int(row.input_tokens), total_output_tokens=int(row.output_tokens),
            ))

        # 4. Model-level
        result = await self._session.execute(text("""
            SELECT model, COALESCE(SUM(cost_cents), 0) as total_cost,
                   COALESCE(COUNT(*), 0) as request_count,
                   COALESCE(SUM(input_tokens), 0) as input_tokens,
                   COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :period_start AND created_at < :period_end
            GROUP BY model
        """), params)
        for row in result.fetchall():
            aggregates.append(SnapshotAggregate.create(
                snapshot_id=snapshot_id, tenant_id=tenant_id,
                entity_type=EntityType.MODEL, entity_id=row.model,
                total_cost_cents=float(row.total_cost), request_count=int(row.request_count),
                total_input_tokens=int(row.input_tokens), total_output_tokens=int(row.output_tokens),
            ))

        return aggregates

    async def insert_baseline(self, baseline: SnapshotBaseline) -> None:
        # Mark existing baselines as not current
        await self._session.execute(text("""
            UPDATE cost_snapshot_baselines SET is_current = false
            WHERE tenant_id = :tenant_id AND entity_type = :entity_type
              AND (entity_id = :entity_id OR (entity_id IS NULL AND :entity_id IS NULL))
              AND window_days = :window_days AND is_current = true
        """), {
            "tenant_id": baseline.tenant_id,
            "entity_type": baseline.entity_type.value,
            "entity_id": baseline.entity_id,
            "window_days": baseline.window_days,
        })

        # Insert new baseline
        await self._session.execute(text("""
            INSERT INTO cost_snapshot_baselines (
                id, tenant_id, entity_type, entity_id,
                avg_daily_cost_cents, stddev_daily_cost_cents,
                avg_daily_requests, max_daily_cost_cents, min_daily_cost_cents,
                window_days, samples_count, computed_at, valid_until,
                is_current, last_snapshot_id
            ) VALUES (
                :id, :tenant_id, :entity_type, :entity_id,
                :avg_daily_cost_cents, :stddev_daily_cost_cents,
                :avg_daily_requests, :max_daily_cost_cents, :min_daily_cost_cents,
                :window_days, :samples_count, :computed_at, :valid_until,
                :is_current, :last_snapshot_id
            )
        """), {
            "id": baseline.id, "tenant_id": baseline.tenant_id,
            "entity_type": baseline.entity_type.value, "entity_id": baseline.entity_id,
            "avg_daily_cost_cents": baseline.avg_daily_cost_cents,
            "stddev_daily_cost_cents": baseline.stddev_daily_cost_cents,
            "avg_daily_requests": baseline.avg_daily_requests,
            "max_daily_cost_cents": baseline.max_daily_cost_cents,
            "min_daily_cost_cents": baseline.min_daily_cost_cents,
            "window_days": baseline.window_days, "samples_count": baseline.samples_count,
            "computed_at": baseline.computed_at, "valid_until": baseline.valid_until,
            "is_current": baseline.is_current, "last_snapshot_id": baseline.last_snapshot_id,
        })

    async def get_snapshot(self, snapshot_id: str) -> CostSnapshot | None:
        query = "SELECT * FROM cost_snapshots WHERE id = :id"
        result = await self._session.execute(text(query), {"id": snapshot_id})
        row = result.fetchone()
        if row:
            return CostSnapshot(
                id=row.id, tenant_id=row.tenant_id,
                snapshot_type=SnapshotType(row.snapshot_type),
                period_start=row.period_start, period_end=row.period_end,
                status=SnapshotStatus(row.status), version=row.version,
                records_processed=row.records_processed,
                computation_ms=row.computation_ms, completed_at=row.completed_at,
            )
        return None

    async def get_aggregates_with_baseline(self, snapshot_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT * FROM cost_snapshot_aggregates
            WHERE snapshot_id = :snapshot_id
              AND baseline_7d_avg_cents IS NOT NULL
              AND baseline_7d_avg_cents > 0
        """
        result = await self._session.execute(text(query), {"snapshot_id": snapshot_id})
        rows = []
        for row in result.fetchall():
            rows.append({
                "tenant_id": row.tenant_id, "entity_type": row.entity_type,
                "entity_id": row.entity_id, "total_cost_cents": row.total_cost_cents,
                "baseline_7d_avg_cents": row.baseline_7d_avg_cents,
                "deviation_from_7d_pct": row.deviation_from_7d_pct,
            })
        return rows

    async def insert_evaluation(self, evaluation: AnomalyEvaluation) -> None:
        query = """
            INSERT INTO cost_anomaly_evaluations (
                id, tenant_id, snapshot_id, entity_type, entity_id,
                current_value_cents, baseline_value_cents, threshold_pct, deviation_pct,
                triggered, severity_computed, anomaly_id, evaluation_reason, evaluated_at
            ) VALUES (
                :id, :tenant_id, :snapshot_id, :entity_type, :entity_id,
                :current_value_cents, :baseline_value_cents, :threshold_pct, :deviation_pct,
                :triggered, :severity_computed, :anomaly_id, :evaluation_reason, :evaluated_at
            )
        """
        await self._session.execute(text(query), {
            "id": evaluation.id, "tenant_id": evaluation.tenant_id,
            "snapshot_id": evaluation.snapshot_id,
            "entity_type": evaluation.entity_type.value,
            "entity_id": evaluation.entity_id,
            "current_value_cents": evaluation.current_value_cents,
            "baseline_value_cents": evaluation.baseline_value_cents,
            "threshold_pct": evaluation.threshold_pct,
            "deviation_pct": evaluation.deviation_pct,
            "triggered": evaluation.triggered,
            "severity_computed": evaluation.severity_computed,
            "anomaly_id": evaluation.anomaly_id,
            "evaluation_reason": evaluation.evaluation_reason,
            "evaluated_at": evaluation.evaluated_at,
        })

    async def insert_anomaly(
        self,
        anomaly_id: str,
        tenant_id: str,
        anomaly_type: str,
        severity: str | None,
        entity_type: str,
        entity_id: str | None,
        current_value_cents: float,
        expected_value_cents: float,
        deviation_pct: float,
        threshold_pct: float,
        message: str,
        snapshot_id: str,
        detected_at: datetime,
    ) -> None:
        query = """
            INSERT INTO cost_anomalies (
                id, tenant_id, anomaly_type, severity, entity_type, entity_id,
                current_value_cents, expected_value_cents, deviation_pct, threshold_pct,
                message, snapshot_id, detected_at
            ) VALUES (
                :id, :tenant_id, :anomaly_type, :severity, :entity_type, :entity_id,
                :current_value_cents, :expected_value_cents, :deviation_pct, :threshold_pct,
                :message, :snapshot_id, :detected_at
            )
        """
        await self._session.execute(text(query), {
            "id": anomaly_id, "tenant_id": tenant_id,
            "anomaly_type": anomaly_type, "severity": severity,
            "entity_type": entity_type, "entity_id": entity_id,
            "current_value_cents": current_value_cents,
            "expected_value_cents": expected_value_cents,
            "deviation_pct": deviation_pct, "threshold_pct": threshold_pct,
            "message": message, "snapshot_id": snapshot_id, "detected_at": detected_at,
        })

    async def compute_baselines(
        self,
        tenant_id: str,
        window_days: int,
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT
                csa.entity_type, csa.entity_id,
                AVG(csa.total_cost_cents) as avg_cost,
                STDDEV(csa.total_cost_cents) as stddev_cost,
                AVG(csa.request_count) as avg_requests,
                MAX(csa.total_cost_cents) as max_cost,
                MIN(csa.total_cost_cents) as min_cost,
                COUNT(*) as samples,
                MAX(csa.snapshot_id) as last_snapshot
            FROM cost_snapshot_aggregates csa
            JOIN cost_snapshots cs ON csa.snapshot_id = cs.id
            WHERE cs.tenant_id = :tenant_id
              AND cs.snapshot_type = 'daily'
              AND cs.status = 'complete'
              AND cs.period_start >= NOW() - INTERVAL '{window_days} days'
            GROUP BY csa.entity_type, csa.entity_id
        """
        result = await self._session.execute(text(query), {"tenant_id": tenant_id})
        rows = []
        for row in result.fetchall():
            rows.append({
                "entity_type": row.entity_type, "entity_id": row.entity_id,
                "avg_cost": row.avg_cost, "stddev_cost": row.stddev_cost,
                "avg_requests": row.avg_requests, "max_cost": row.max_cost,
                "min_cost": row.min_cost, "samples": row.samples,
                "last_snapshot": row.last_snapshot,
            })
        return rows


def get_cost_snapshots_driver(session: AsyncSession) -> CostSnapshotsDriver:
    """Factory function to get CostSnapshotsDriver instance."""
    return CostSnapshotsDriver(session)


__all__ = [
    "CostSnapshotsDriver",
    "get_cost_snapshots_driver",
]
