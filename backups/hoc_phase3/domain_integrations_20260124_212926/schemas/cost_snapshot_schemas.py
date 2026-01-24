# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Cost snapshot dataclasses and enums
# Callers: cost_snapshot_engine, cost_snapshot_driver
# Allowed Imports: stdlib only
# Forbidden Imports: L6, sqlalchemy
# Reference: HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
M27 Cost Snapshot Schemas

Dataclasses and enums for the cost snapshot system.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


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
        entity_key = entity_id or "tenant"
        agg_id = f"agg_{hashlib.sha256(f'{snapshot_id}:{entity_type}:{entity_key}'.encode()).hexdigest()[:16]}"
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
        entity_key = entity_id or "tenant"
        baseline_id = f"base_{hashlib.sha256(f'{tenant_id}:{entity_type}:{entity_key}:{window_days}:{now.date().isoformat()}'.encode()).hexdigest()[:16]}"
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
