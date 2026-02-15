# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Incident, Run, traces
#   Writes: none
# Database:
#   Scope: domain (logs)
#   Models: Incident, Run
# Role: Database operations for export bundle data (incidents, runs, traces)
# Callers: L3 ExportBundleAdapter
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470, HOC_LAYER_TOPOLOGY_V1.md, LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md
#
# DRIVER CONTRACT:
# - Returns domain objects (dataclasses), not ORM models
# - Owns query logic
# - Owns data shape transformation
# - NO business logic

"""
Export Bundle Store (L6)

Database driver for export bundle data access:
- Incidents
- Runs
- Trace summaries and steps

All methods return immutable snapshots, never ORM models.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

# NOTE: L6 drivers must not import L7 models via app.db.
# L7 models live under app.models/ by design (HOC Topology V2.0.0).
from app.db import Run, engine
from app.models.killswitch import Incident
from app.hoc.cus.logs.L6_drivers.trace_store import TraceStore


# =============================================================================
# Snapshot Types
# =============================================================================


@dataclass(frozen=True)
class IncidentSnapshot:
    """Immutable snapshot of incident."""

    id: str
    tenant_id: str
    source_run_id: Optional[str]
    severity: Optional[str]
    policy_id: Optional[str]
    policy_name: Optional[str]
    violation_type: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class RunSnapshot:
    """Immutable snapshot of run."""

    run_id: str
    tenant_id: str
    agent_id: Optional[str]
    goal: Optional[str]
    policy_snapshot_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    termination_reason: Optional[str]
    total_cost_cents: Optional[int]


@dataclass(frozen=True)
class TraceSummarySnapshot:
    """Immutable snapshot of trace summary."""

    trace_id: str
    run_id: str
    tenant_id: str
    violation_step_index: Optional[int]
    violation_timestamp: Optional[datetime]


@dataclass(frozen=True)
class TraceStepSnapshot:
    """Immutable snapshot of trace step."""

    step_index: int
    timestamp: datetime
    step_type: str
    tokens: int
    cost_cents: float
    duration_ms: float
    status: str
    content_hash: Optional[str]


# =============================================================================
# Export Bundle Store
# =============================================================================


class ExportBundleStore:
    """
    L6 Database Driver for export bundle data.

    All methods:
    - Use sync Session (for sqlmodel compatibility)
    - Return immutable snapshots
    - Contain NO business logic
    """

    def __init__(self, trace_store: Optional[TraceStore] = None):
        """Initialize with optional trace store for testing."""
        self._trace_store = trace_store

    @property
    def trace_store(self) -> TraceStore:
        """Get or create TraceStore instance."""
        if self._trace_store is None:
            self._trace_store = TraceStore()
        return self._trace_store

    def get_incident(self, incident_id: str) -> Optional[IncidentSnapshot]:
        """Get incident by ID."""
        with Session(engine) as session:
            incident = session.get(Incident, incident_id)
            if not incident:
                return None

            return IncidentSnapshot(
                id=incident.id,
                tenant_id=incident.tenant_id,
                source_run_id=incident.source_run_id,
                severity=getattr(incident, "severity", None),
                policy_id=getattr(incident, "policy_id", None),
                policy_name=getattr(incident, "policy_name", None),
                violation_type=getattr(incident, "violation_type", None),
                created_at=incident.created_at,
            )

    def get_run_by_run_id(self, run_id: str) -> Optional[RunSnapshot]:
        """Get run by run_id."""
        with Session(engine) as session:
            stmt = select(Run).where(Run.id == run_id)
            result = session.exec(stmt)
            run = result.first()

            if not run:
                return None

            return RunSnapshot(
                run_id=run.id,
                tenant_id=run.tenant_id,
                agent_id=run.agent_id,
                goal=run.goal,
                policy_snapshot_id=run.policy_snapshot_id,
                started_at=run.started_at,
                completed_at=run.completed_at,
                termination_reason=run.termination_reason,
                total_cost_cents=getattr(run, "total_cost_cents", None),
            )

    async def get_trace_summary(
        self,
        run_id: str,
        tenant_id: str,
    ) -> Optional[TraceSummarySnapshot]:
        """Get trace summary for a run."""
        summary = await self.trace_store.get_trace_summary(
            run_id=run_id,
            tenant_id=tenant_id,
        )

        if not summary:
            return None

        return TraceSummarySnapshot(
            trace_id=summary.trace_id,
            run_id=run_id,
            tenant_id=tenant_id,
            violation_step_index=summary.violation_step_index,
            violation_timestamp=summary.violation_timestamp,
        )

    async def get_trace_steps(
        self,
        trace_id: str,
        tenant_id: str,
    ) -> list[TraceStepSnapshot]:
        """Get trace steps for a trace."""
        steps = await self.trace_store.get_trace_steps(
            trace_id=trace_id,
            tenant_id=tenant_id,
        )

        return [
            TraceStepSnapshot(
                step_index=i,
                timestamp=step.timestamp,
                step_type=step.step_type or "unknown",
                tokens=step.tokens or 0,
                cost_cents=step.cost_cents or 0.0,
                duration_ms=step.duration_ms or 0.0,
                status="ok",
                content_hash=step.content_hash,
            )
            for i, step in enumerate(steps)
        ]


# =============================================================================
# Singleton Factory
# =============================================================================

_store_instance: ExportBundleStore | None = None


def get_export_bundle_store() -> ExportBundleStore:
    """Get the singleton ExportBundleStore instance."""
    global _store_instance
    if _store_instance is None:
        _store_instance = ExportBundleStore()
    return _store_instance


__all__ = [
    "ExportBundleStore",
    "get_export_bundle_store",
    "IncidentSnapshot",
    "RunSnapshot",
    "TraceSummarySnapshot",
    "TraceStepSnapshot",
]
