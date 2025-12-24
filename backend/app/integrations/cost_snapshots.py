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
  computer = SnapshotComputer(session)
  snapshot = await computer.compute_hourly_snapshot(tenant_id)

  # Anomaly detection (only reads complete snapshots)
  detector = CostAnomalyDetector(session)
  anomalies = await detector.evaluate_from_snapshot(snapshot.id)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class SnapshotType(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"


class SnapshotStatus(str, Enum):
    PENDING = "pending"
    COMPUTING = "computing"
    COMPLETE = "complete"
    FAILED = "failed"


class EntityType(str, Enum):
    TENANT = "tenant"
    USER = "user"
    FEATURE = "feature"
    MODEL = "model"


# Severity thresholds (deviation from baseline)
SEVERITY_THRESHOLDS = {
    "low": 200,  # 2x baseline
    "medium": 300,  # 3x baseline
    "high": 400,  # 4x baseline (this is what triggers M27 loop)
    "critical": 500,  # 5x baseline
}


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class CostSnapshot:
    """Point-in-time cost snapshot definition."""

    id: str
    tenant_id: str
    snapshot_type: SnapshotType
    period_start: datetime
    period_end: datetime
    status: SnapshotStatus
    version: int = 1
    records_processed: int | None = None
    computation_ms: int | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @classmethod
    def create(
        cls,
        tenant_id: str,
        snapshot_type: SnapshotType,
        period_start: datetime,
        period_end: datetime,
    ) -> "CostSnapshot":
        """Create a new snapshot in pending status."""
        snapshot_id = f"snap_{hashlib.sha256(f'{tenant_id}:{snapshot_type}:{period_start.isoformat()}'.encode()).hexdigest()[:16]}"
        return cls(
            id=snapshot_id,
            tenant_id=tenant_id,
            snapshot_type=snapshot_type,
            period_start=period_start,
            period_end=period_end,
            status=SnapshotStatus.PENDING,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "snapshot_type": self.snapshot_type.value
            if isinstance(self.snapshot_type, SnapshotType)
            else self.snapshot_type,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "status": self.status.value if isinstance(self.status, SnapshotStatus) else self.status,
            "version": self.version,
            "records_processed": self.records_processed,
            "computation_ms": self.computation_ms,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class SnapshotAggregate:
    """Aggregated cost data for an entity within a snapshot."""

    id: str
    snapshot_id: str
    tenant_id: str
    entity_type: EntityType
    entity_id: str | None
    total_cost_cents: float
    request_count: int
    total_input_tokens: int
    total_output_tokens: int
    avg_cost_per_request_cents: float | None = None
    avg_tokens_per_request: float | None = None
    baseline_7d_avg_cents: float | None = None
    baseline_30d_avg_cents: float | None = None
    deviation_from_7d_pct: float | None = None
    deviation_from_30d_pct: float | None = None

    @classmethod
    def create(
        cls,
        snapshot_id: str,
        tenant_id: str,
        entity_type: EntityType,
        entity_id: str | None,
        total_cost_cents: float,
        request_count: int,
        total_input_tokens: int,
        total_output_tokens: int,
    ) -> "SnapshotAggregate":
        agg_id = (
            f"agg_{hashlib.sha256(f'{snapshot_id}:{entity_type}:{entity_id or "tenant"}'.encode()).hexdigest()[:16]}"
        )
        avg_cost = total_cost_cents / request_count if request_count > 0 else None
        avg_tokens = (total_input_tokens + total_output_tokens) / request_count if request_count > 0 else None
        return cls(
            id=agg_id,
            snapshot_id=snapshot_id,
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            total_cost_cents=total_cost_cents,
            request_count=request_count,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            avg_cost_per_request_cents=avg_cost,
            avg_tokens_per_request=avg_tokens,
        )


@dataclass
class SnapshotBaseline:
    """Rolling baseline for an entity (used for anomaly threshold)."""

    id: str
    tenant_id: str
    entity_type: EntityType
    entity_id: str | None
    avg_daily_cost_cents: float
    stddev_daily_cost_cents: float | None
    avg_daily_requests: float
    max_daily_cost_cents: float | None
    min_daily_cost_cents: float | None
    window_days: int
    samples_count: int
    computed_at: datetime
    valid_until: datetime
    is_current: bool = True
    last_snapshot_id: str | None = None

    @classmethod
    def create(
        cls,
        tenant_id: str,
        entity_type: EntityType,
        entity_id: str | None,
        window_days: int,
        avg_daily_cost_cents: float,
        avg_daily_requests: float,
        samples_count: int,
        stddev: float | None = None,
        max_cost: float | None = None,
        min_cost: float | None = None,
        last_snapshot_id: str | None = None,
    ) -> "SnapshotBaseline":
        now = datetime.now(timezone.utc)
        baseline_id = f"base_{hashlib.sha256(f'{tenant_id}:{entity_type}:{entity_id or "tenant"}:{window_days}:{now.date().isoformat()}'.encode()).hexdigest()[:16]}"
        return cls(
            id=baseline_id,
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            avg_daily_cost_cents=avg_daily_cost_cents,
            stddev_daily_cost_cents=stddev,
            avg_daily_requests=avg_daily_requests,
            max_daily_cost_cents=max_cost,
            min_daily_cost_cents=min_cost,
            window_days=window_days,
            samples_count=samples_count,
            computed_at=now,
            valid_until=now + timedelta(days=1),  # Valid for 1 day
            is_current=True,
            last_snapshot_id=last_snapshot_id,
        )


@dataclass
class AnomalyEvaluation:
    """Audit record for an anomaly evaluation."""

    id: str
    tenant_id: str
    snapshot_id: str | None
    entity_type: EntityType
    entity_id: str | None
    current_value_cents: float
    baseline_value_cents: float
    threshold_pct: float
    deviation_pct: float
    triggered: bool
    severity_computed: str | None = None
    anomaly_id: str | None = None
    evaluation_reason: str | None = None
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# Snapshot Computer
# =============================================================================


class SnapshotComputer:
    """Computes cost snapshots from raw cost_records.

    Usage:
        computer = SnapshotComputer(session)
        snapshot = await computer.compute_hourly_snapshot(tenant_id)
        # snapshot.status == 'complete' if successful
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def compute_hourly_snapshot(
        self,
        tenant_id: str,
        hour: datetime | None = None,
    ) -> CostSnapshot:
        """Compute hourly snapshot for a tenant.

        Args:
            tenant_id: Tenant to compute snapshot for
            hour: Start of hour (defaults to previous hour)

        Returns:
            CostSnapshot with status='complete' or status='failed'
        """
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
        """Compute daily snapshot for a tenant.

        Args:
            tenant_id: Tenant to compute snapshot for
            date: Date to snapshot (defaults to yesterday)

        Returns:
            CostSnapshot with status='complete' or status='failed'
        """
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

        # Create snapshot record
        snapshot = CostSnapshot.create(
            tenant_id=tenant_id,
            snapshot_type=snapshot_type,
            period_start=period_start,
            period_end=period_end,
        )
        snapshot.status = SnapshotStatus.COMPUTING

        try:
            # Insert snapshot record
            await self._insert_snapshot(snapshot)

            # Aggregate cost records for the period
            aggregates = await self._aggregate_cost_records(
                tenant_id=tenant_id,
                snapshot_id=snapshot.id,
                period_start=period_start,
                period_end=period_end,
            )

            # Load baselines and compute deviations
            for agg in aggregates:
                baseline = await self._get_current_baseline(
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

                # Insert aggregate
                await self._insert_aggregate(agg)

            # Update snapshot as complete
            elapsed_ms = int((time.time() - start_time) * 1000)
            snapshot.status = SnapshotStatus.COMPLETE
            snapshot.records_processed = sum(a.request_count for a in aggregates)
            snapshot.computation_ms = elapsed_ms
            snapshot.completed_at = datetime.now(timezone.utc)

            await self._update_snapshot(snapshot)

            logger.info(f"Snapshot complete: {snapshot.id} ({snapshot.records_processed} records, {elapsed_ms}ms)")

        except Exception as e:
            snapshot.status = SnapshotStatus.FAILED
            snapshot.error_message = str(e)
            await self._update_snapshot(snapshot)
            logger.error(f"Snapshot failed: {snapshot.id} - {e}")

        return snapshot

    async def _aggregate_cost_records(
        self,
        tenant_id: str,
        snapshot_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> list[SnapshotAggregate]:
        """Aggregate cost records by entity type."""
        aggregates: list[SnapshotAggregate] = []

        # Raw SQL for aggregation (faster than ORM for large datasets)
        # 1. Tenant-level aggregate
        tenant_query = """
            SELECT
                COALESCE(SUM(cost_cents), 0) as total_cost,
                COALESCE(COUNT(*), 0) as request_count,
                COALESCE(SUM(input_tokens), 0) as input_tokens,
                COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :period_start
              AND created_at < :period_end
        """
        result = await self.session.execute(
            __import__("sqlalchemy").text(tenant_query),
            {
                "tenant_id": tenant_id,
                "period_start": period_start,
                "period_end": period_end,
            },
        )
        row = result.fetchone()
        if row and row.request_count > 0:
            aggregates.append(
                SnapshotAggregate.create(
                    snapshot_id=snapshot_id,
                    tenant_id=tenant_id,
                    entity_type=EntityType.TENANT,
                    entity_id=None,
                    total_cost_cents=float(row.total_cost),
                    request_count=int(row.request_count),
                    total_input_tokens=int(row.input_tokens),
                    total_output_tokens=int(row.output_tokens),
                )
            )

        # 2. User-level aggregates
        user_query = """
            SELECT
                user_id,
                COALESCE(SUM(cost_cents), 0) as total_cost,
                COALESCE(COUNT(*), 0) as request_count,
                COALESCE(SUM(input_tokens), 0) as input_tokens,
                COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :period_start
              AND created_at < :period_end
              AND user_id IS NOT NULL
            GROUP BY user_id
        """
        result = await self.session.execute(
            __import__("sqlalchemy").text(user_query),
            {
                "tenant_id": tenant_id,
                "period_start": period_start,
                "period_end": period_end,
            },
        )
        for row in result.fetchall():
            aggregates.append(
                SnapshotAggregate.create(
                    snapshot_id=snapshot_id,
                    tenant_id=tenant_id,
                    entity_type=EntityType.USER,
                    entity_id=row.user_id,
                    total_cost_cents=float(row.total_cost),
                    request_count=int(row.request_count),
                    total_input_tokens=int(row.input_tokens),
                    total_output_tokens=int(row.output_tokens),
                )
            )

        # 3. Feature-level aggregates
        feature_query = """
            SELECT
                feature_tag,
                COALESCE(SUM(cost_cents), 0) as total_cost,
                COALESCE(COUNT(*), 0) as request_count,
                COALESCE(SUM(input_tokens), 0) as input_tokens,
                COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :period_start
              AND created_at < :period_end
              AND feature_tag IS NOT NULL
            GROUP BY feature_tag
        """
        result = await self.session.execute(
            __import__("sqlalchemy").text(feature_query),
            {
                "tenant_id": tenant_id,
                "period_start": period_start,
                "period_end": period_end,
            },
        )
        for row in result.fetchall():
            aggregates.append(
                SnapshotAggregate.create(
                    snapshot_id=snapshot_id,
                    tenant_id=tenant_id,
                    entity_type=EntityType.FEATURE,
                    entity_id=row.feature_tag,
                    total_cost_cents=float(row.total_cost),
                    request_count=int(row.request_count),
                    total_input_tokens=int(row.input_tokens),
                    total_output_tokens=int(row.output_tokens),
                )
            )

        # 4. Model-level aggregates
        model_query = """
            SELECT
                model,
                COALESCE(SUM(cost_cents), 0) as total_cost,
                COALESCE(COUNT(*), 0) as request_count,
                COALESCE(SUM(input_tokens), 0) as input_tokens,
                COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :period_start
              AND created_at < :period_end
            GROUP BY model
        """
        result = await self.session.execute(
            __import__("sqlalchemy").text(model_query),
            {
                "tenant_id": tenant_id,
                "period_start": period_start,
                "period_end": period_end,
            },
        )
        for row in result.fetchall():
            aggregates.append(
                SnapshotAggregate.create(
                    snapshot_id=snapshot_id,
                    tenant_id=tenant_id,
                    entity_type=EntityType.MODEL,
                    entity_id=row.model,
                    total_cost_cents=float(row.total_cost),
                    request_count=int(row.request_count),
                    total_input_tokens=int(row.input_tokens),
                    total_output_tokens=int(row.output_tokens),
                )
            )

        return aggregates

    async def _get_current_baseline(
        self,
        tenant_id: str,
        entity_type: EntityType,
        entity_id: str | None,
        window_days: int,
    ) -> SnapshotBaseline | None:
        """Get current baseline for an entity."""
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
        result = await self.session.execute(
            __import__("sqlalchemy").text(query),
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

    async def _insert_snapshot(self, snapshot: CostSnapshot) -> None:
        """Insert snapshot record."""
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
        await self.session.execute(
            __import__("sqlalchemy").text(query),
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
        await self.session.commit()

    async def _update_snapshot(self, snapshot: CostSnapshot) -> None:
        """Update snapshot record."""
        query = """
            UPDATE cost_snapshots SET
                status = :status,
                records_processed = :records_processed,
                computation_ms = :computation_ms,
                completed_at = :completed_at,
                error_message = :error_message
            WHERE id = :id
        """
        await self.session.execute(
            __import__("sqlalchemy").text(query),
            {
                "id": snapshot.id,
                "status": snapshot.status.value,
                "records_processed": snapshot.records_processed,
                "computation_ms": snapshot.computation_ms,
                "completed_at": snapshot.completed_at,
                "error_message": snapshot.error_message,
            },
        )
        await self.session.commit()

    async def _insert_aggregate(self, agg: SnapshotAggregate) -> None:
        """Insert aggregate record."""
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
        await self.session.execute(
            __import__("sqlalchemy").text(query),
            {
                "id": agg.id,
                "snapshot_id": agg.snapshot_id,
                "tenant_id": agg.tenant_id,
                "entity_type": agg.entity_type.value if isinstance(agg.entity_type, EntityType) else agg.entity_type,
                "entity_id": agg.entity_id,
                "total_cost_cents": agg.total_cost_cents,
                "request_count": agg.request_count,
                "total_input_tokens": agg.total_input_tokens,
                "total_output_tokens": agg.total_output_tokens,
                "avg_cost_per_request_cents": agg.avg_cost_per_request_cents,
                "avg_tokens_per_request": agg.avg_tokens_per_request,
                "baseline_7d_avg_cents": agg.baseline_7d_avg_cents,
                "baseline_30d_avg_cents": agg.baseline_30d_avg_cents,
                "deviation_from_7d_pct": agg.deviation_from_7d_pct,
                "deviation_from_30d_pct": agg.deviation_from_30d_pct,
                "created_at": datetime.now(timezone.utc),
            },
        )
        await self.session.commit()


# =============================================================================
# Baseline Computer
# =============================================================================


class BaselineComputer:
    """Computes rolling baselines from historical snapshots.

    Run daily after daily snapshot completes.

    Usage:
        computer = BaselineComputer(session)
        baselines = await computer.compute_baselines(tenant_id)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def compute_baselines(
        self,
        tenant_id: str,
        window_days: int = 7,
    ) -> list[SnapshotBaseline]:
        """Compute baselines for all entities from historical snapshots."""
        baselines: list[SnapshotBaseline] = []

        # Query historical daily snapshots
        query = """
            SELECT
                csa.entity_type,
                csa.entity_id,
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
              AND cs.period_start >= NOW() - INTERVAL ':window_days days'
            GROUP BY csa.entity_type, csa.entity_id
        """
        # Note: Can't use :window_days in interval directly, need to format
        formatted_query = query.replace(":window_days days", f"{window_days} days")

        result = await self.session.execute(__import__("sqlalchemy").text(formatted_query), {"tenant_id": tenant_id})

        for row in result.fetchall():
            baseline = SnapshotBaseline.create(
                tenant_id=tenant_id,
                entity_type=EntityType(row.entity_type),
                entity_id=row.entity_id,
                window_days=window_days,
                avg_daily_cost_cents=float(row.avg_cost or 0),
                avg_daily_requests=float(row.avg_requests or 0),
                samples_count=int(row.samples),
                stddev=float(row.stddev_cost) if row.stddev_cost else None,
                max_cost=float(row.max_cost) if row.max_cost else None,
                min_cost=float(row.min_cost) if row.min_cost else None,
                last_snapshot_id=row.last_snapshot,
            )
            baselines.append(baseline)

            # Insert baseline (mark old ones as not current first)
            await self._insert_baseline(baseline)

        return baselines

    async def _insert_baseline(self, baseline: SnapshotBaseline) -> None:
        """Insert baseline, marking old ones as not current."""
        # Mark existing baselines as not current
        await self.session.execute(
            __import__("sqlalchemy").text(
                """
                UPDATE cost_snapshot_baselines SET is_current = false
                WHERE tenant_id = :tenant_id
                  AND entity_type = :entity_type
                  AND (entity_id = :entity_id OR (entity_id IS NULL AND :entity_id IS NULL))
                  AND window_days = :window_days
                  AND is_current = true
            """
            ),
            {
                "tenant_id": baseline.tenant_id,
                "entity_type": baseline.entity_type.value,
                "entity_id": baseline.entity_id,
                "window_days": baseline.window_days,
            },
        )

        # Insert new baseline
        await self.session.execute(
            __import__("sqlalchemy").text(
                """
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
            """
            ),
            {
                "id": baseline.id,
                "tenant_id": baseline.tenant_id,
                "entity_type": baseline.entity_type.value,
                "entity_id": baseline.entity_id,
                "avg_daily_cost_cents": baseline.avg_daily_cost_cents,
                "stddev_daily_cost_cents": baseline.stddev_daily_cost_cents,
                "avg_daily_requests": baseline.avg_daily_requests,
                "max_daily_cost_cents": baseline.max_daily_cost_cents,
                "min_daily_cost_cents": baseline.min_daily_cost_cents,
                "window_days": baseline.window_days,
                "samples_count": baseline.samples_count,
                "computed_at": baseline.computed_at,
                "valid_until": baseline.valid_until,
                "is_current": baseline.is_current,
                "last_snapshot_id": baseline.last_snapshot_id,
            },
        )
        await self.session.commit()


# =============================================================================
# Snapshot-Based Anomaly Detector
# =============================================================================


class SnapshotAnomalyDetector:
    """Detects anomalies from complete snapshots only.

    THE INVARIANT:
      This detector NEVER reads from cost_records.
      It ONLY reads from complete snapshots.

    Usage:
        detector = SnapshotAnomalyDetector(session)
        anomalies = await detector.evaluate_snapshot(snapshot_id)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def evaluate_snapshot(
        self,
        snapshot_id: str,
        threshold_pct: float = 200,
    ) -> list[AnomalyEvaluation]:
        """Evaluate all aggregates in a snapshot for anomalies.

        Args:
            snapshot_id: Complete snapshot to evaluate
            threshold_pct: Minimum deviation % to trigger anomaly

        Returns:
            List of evaluations (some may have triggered=True)
        """
        evaluations: list[AnomalyEvaluation] = []

        # Verify snapshot is complete
        snapshot = await self._get_snapshot(snapshot_id)
        if not snapshot or snapshot.status != SnapshotStatus.COMPLETE:
            logger.warning(f"Cannot evaluate incomplete snapshot: {snapshot_id}")
            return evaluations

        # Get all aggregates with deviation data
        query = """
            SELECT * FROM cost_snapshot_aggregates
            WHERE snapshot_id = :snapshot_id
              AND baseline_7d_avg_cents IS NOT NULL
              AND baseline_7d_avg_cents > 0
        """
        result = await self.session.execute(__import__("sqlalchemy").text(query), {"snapshot_id": snapshot_id})

        for row in result.fetchall():
            deviation = row.deviation_from_7d_pct or 0
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
                f"eval_{hashlib.sha256(f'{snapshot_id}:{row.entity_type}:{row.entity_id}'.encode()).hexdigest()[:16]}"
            )
            evaluation = AnomalyEvaluation(
                id=eval_id,
                tenant_id=row.tenant_id,
                snapshot_id=snapshot_id,
                entity_type=EntityType(row.entity_type),
                entity_id=row.entity_id,
                current_value_cents=row.total_cost_cents,
                baseline_value_cents=row.baseline_7d_avg_cents,
                threshold_pct=threshold_pct,
                deviation_pct=deviation,
                triggered=triggered,
                severity_computed=severity,
                evaluation_reason=f"{'TRIGGERED' if triggered else 'OK'}: {deviation:.1f}% deviation (threshold: {threshold_pct}%)",
            )
            evaluations.append(evaluation)

            # Persist evaluation
            await self._insert_evaluation(evaluation)

            # If triggered, create anomaly via M26 bridge
            if triggered:
                anomaly_id = await self._create_anomaly_from_evaluation(evaluation, snapshot)
                evaluation.anomaly_id = anomaly_id

        return evaluations

    async def _get_snapshot(self, snapshot_id: str) -> CostSnapshot | None:
        """Get snapshot by ID."""
        query = "SELECT * FROM cost_snapshots WHERE id = :id"
        result = await self.session.execute(__import__("sqlalchemy").text(query), {"id": snapshot_id})
        row = result.fetchone()
        if row:
            return CostSnapshot(
                id=row.id,
                tenant_id=row.tenant_id,
                snapshot_type=SnapshotType(row.snapshot_type),
                period_start=row.period_start,
                period_end=row.period_end,
                status=SnapshotStatus(row.status),
                version=row.version,
                records_processed=row.records_processed,
                computation_ms=row.computation_ms,
                completed_at=row.completed_at,
            )
        return None

    async def _insert_evaluation(self, evaluation: AnomalyEvaluation) -> None:
        """Persist evaluation record."""
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
        await self.session.execute(
            __import__("sqlalchemy").text(query),
            {
                "id": evaluation.id,
                "tenant_id": evaluation.tenant_id,
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
            },
        )
        await self.session.commit()

    async def _create_anomaly_from_evaluation(
        self,
        evaluation: AnomalyEvaluation,
        snapshot: CostSnapshot,
    ) -> str:
        """Create cost anomaly from evaluation (bridges to M26)."""
        anomaly_id = f"anom_{hashlib.sha256(f'{evaluation.id}'.encode()).hexdigest()[:16]}"

        # Map entity_type to anomaly_type
        anomaly_type_map = {
            EntityType.USER: "user_spike",
            EntityType.FEATURE: "feature_spike",
            EntityType.MODEL: "model_spike",
            EntityType.TENANT: "tenant_spike",
        }
        anomaly_type = anomaly_type_map.get(evaluation.entity_type, "unknown")

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
        await self.session.execute(
            __import__("sqlalchemy").text(query),
            {
                "id": anomaly_id,
                "tenant_id": evaluation.tenant_id,
                "anomaly_type": anomaly_type,
                "severity": evaluation.severity_computed,
                "entity_type": evaluation.entity_type.value,
                "entity_id": evaluation.entity_id,
                "current_value_cents": evaluation.current_value_cents,
                "expected_value_cents": evaluation.baseline_value_cents,
                "deviation_pct": evaluation.deviation_pct,
                "threshold_pct": evaluation.threshold_pct,
                "message": f"Cost spike detected from snapshot {snapshot.id}: {evaluation.deviation_pct:.1f}% above 7-day baseline",
                "snapshot_id": snapshot.id,
                "detected_at": evaluation.evaluated_at,
            },
        )
        await self.session.commit()

        logger.info(f"Created anomaly {anomaly_id} from snapshot evaluation")
        return anomaly_id


# =============================================================================
# Convenience Functions
# =============================================================================


async def run_hourly_snapshot_job(session: AsyncSession, tenant_ids: list[str]) -> dict:
    """Run hourly snapshot job for multiple tenants.

    Schedule this via cron/systemd timer every hour at :05.
    """
    results = {"success": [], "failed": []}
    computer = SnapshotComputer(session)

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


async def run_daily_snapshot_and_baseline_job(session: AsyncSession, tenant_ids: list[str]) -> dict:
    """Run daily snapshot and baseline computation for multiple tenants.

    Schedule this via cron/systemd timer daily at 00:30.
    """
    results = {"snapshots": [], "baselines": [], "anomalies": []}

    snapshot_computer = SnapshotComputer(session)
    baseline_computer = BaselineComputer(session)
    detector = SnapshotAnomalyDetector(session)

    for tenant_id in tenant_ids:
        # 1. Compute daily snapshot
        snapshot = await snapshot_computer.compute_daily_snapshot(tenant_id)
        results["snapshots"].append(
            {
                "tenant_id": tenant_id,
                "snapshot_id": snapshot.id,
                "status": snapshot.status.value,
            }
        )

        if snapshot.status == SnapshotStatus.COMPLETE:
            # 2. Compute baselines
            baselines = await baseline_computer.compute_baselines(tenant_id)
            results["baselines"].append(
                {
                    "tenant_id": tenant_id,
                    "count": len(baselines),
                }
            )

            # 3. Evaluate for anomalies
            evaluations = await detector.evaluate_snapshot(snapshot.id)
            triggered = [e for e in evaluations if e.triggered]
            results["anomalies"].append(
                {
                    "tenant_id": tenant_id,
                    "evaluated": len(evaluations),
                    "triggered": len(triggered),
                }
            )

    return results
