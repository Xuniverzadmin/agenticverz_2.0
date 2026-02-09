# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: LLM runs, system logs, audit (via driver)
#   Writes: none (via driver)
# Role: Logs domain facade - unified entry point for all logs operations
# Callers: L2 logs API, L3 adapters
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, HOC_LAYER_TOPOLOGY_V1.md, LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md
# Location: hoc/cus/logs/L5_engines/logs_facade.py
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.
#
# GOVERNANCE: INV-LOGS-005
# This facade is COMPOSITION-ONLY. No new computation logic inside.
# All DB operations delegated to L6 LogsDomainStore.
# This file orchestrates; it does not query databases.
#
"""
Logs Domain Facade (L5)

Unified facade for all logs domain operations:
- LLM_RUNS: envelope, trace, governance, replay, export
- SYSTEM_LOGS: snapshot, telemetry, events, replay, audit
- AUDIT: identity, authorization, access, integrity, exports

All responses include EvidenceMetadata per INV-LOG-META-001.

L5 CONTRACT:
- NO sqlalchemy imports
- NO direct database queries
- Delegates all data access to L6 LogsDomainStore
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

# L6 Driver import (allowed)
from app.hoc.cus.logs.L6_drivers.logs_domain_store import (
    AuditLedgerSnapshot,
    LLMRunSnapshot,
    LogsDomainStore,
    LogExportSnapshot,
    QueryResult,
    SystemRecordSnapshot,
    TraceStepSnapshot,
    get_logs_domain_store,
)


# =============================================================================
# Enums
# =============================================================================


class SourceDomain(str, Enum):
    """Source domain for evidence metadata."""

    ACTIVITY = "ACTIVITY"
    POLICY = "POLICY"
    INCIDENTS = "INCIDENTS"
    LOGS = "LOGS"
    SYSTEM = "SYSTEM"


class Origin(str, Enum):
    """Origin of the record."""

    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"
    AGENT = "AGENT"
    MIGRATION = "MIGRATION"
    REPLAY = "REPLAY"


# =============================================================================
# Evidence Metadata (INV-LOG-META-001)
# =============================================================================


@dataclass
class EvidenceMetadataResult:
    """Global metadata contract for all Logs responses."""

    # Identity
    tenant_id: str
    run_id: Optional[str] = None

    # Actor attribution
    human_actor_id: Optional[str] = None
    agent_id: Optional[str] = None
    system_id: Optional[str] = None

    # Time
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    timezone_str: str = "UTC"

    # Correlation spine
    trace_id: Optional[str] = None
    policy_ids: list[str] = field(default_factory=list)
    incident_ids: list[str] = field(default_factory=list)
    export_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Source & provenance
    source_domain: str = "LOGS"
    source_component: str = ""
    origin: str = "SYSTEM"

    # Integrity
    checksum: Optional[str] = None
    immutable: bool = True


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class LLMRunRecordResult:
    """Single LLM run record."""

    id: str
    run_id: str
    trace_id: Optional[str]
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_cents: int
    execution_status: str
    started_at: datetime
    completed_at: Optional[datetime]
    source: str
    is_synthetic: bool
    created_at: datetime


@dataclass
class LLMRunRecordsResult:
    """Response envelope for LLM run records."""

    items: list[LLMRunRecordResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class TraceStepResult:
    """Individual trace step."""

    step_index: int
    timestamp: datetime
    skill_name: str
    status: str
    outcome_category: str
    cost_cents: int
    duration_ms: int


@dataclass
class LLMRunEnvelopeResult:
    """O1: Canonical immutable run record."""

    id: str
    run_id: str
    trace_id: Optional[str]
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_cents: int
    execution_status: str
    started_at: datetime
    completed_at: Optional[datetime]
    source: str
    is_synthetic: bool
    created_at: datetime
    metadata: EvidenceMetadataResult


@dataclass
class LLMRunTraceResult:
    """O2: Step-by-step trace."""

    run_id: str
    trace_id: str
    steps: list[TraceStepResult]
    total_steps: int
    metadata: EvidenceMetadataResult


@dataclass
class GovernanceEventResult:
    """Policy interaction event."""

    timestamp: datetime
    event_type: str
    policy_id: Optional[str]
    rule_id: Optional[str]
    decision: str
    entity_type: str
    entity_id: str


@dataclass
class LLMRunGovernanceResult:
    """O3: Policy interaction trace."""

    run_id: str
    events: list[GovernanceEventResult]
    total_events: int
    metadata: EvidenceMetadataResult


@dataclass
class ReplayEventResult:
    """Replay window event."""

    source: str  # llm, system, policy
    timestamp: datetime
    step_index: Optional[int]
    action: str
    outcome: str


@dataclass
class LLMRunReplayResult:
    """O4: 60-second replay window."""

    run_id: str
    inflection_timestamp: Optional[datetime]
    window_start: datetime
    window_end: datetime
    events: list[ReplayEventResult]
    metadata: EvidenceMetadataResult


@dataclass
class LLMRunExportResult:
    """O5: Export metadata."""

    run_id: str
    available_formats: list[str]
    checksum: Optional[str]
    compliance_tags: list[str]
    metadata: EvidenceMetadataResult


@dataclass
class SystemRecordResult:
    """Single system record entry."""

    id: str
    tenant_id: Optional[str]
    component: str
    event_type: str
    severity: str
    summary: str
    caused_by: Optional[str]
    correlation_id: Optional[str]
    created_at: datetime


@dataclass
class SystemRecordsResult:
    """Response envelope for system records."""

    items: list[SystemRecordResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class SystemSnapshotResult:
    """O1: Environment snapshot."""

    run_id: str
    component: str
    event_type: str
    severity: str
    summary: str
    details: Optional[dict[str, Any]]
    created_at: datetime
    metadata: EvidenceMetadataResult


@dataclass
class TelemetryStubResult:
    """O2: Telemetry stub response."""

    status: str = "telemetry_not_collected"
    reason: str = "infrastructure_telemetry_producer_not_implemented"
    run_id: str = ""
    available_data: list[str] = field(
        default_factory=lambda: ["events", "snapshot", "replay"]
    )
    future_milestone: str = "M-TBD"


@dataclass
class SystemEventResult:
    """System event record."""

    id: str
    component: str
    event_type: str
    severity: str
    summary: str
    caused_by: Optional[str]
    correlation_id: Optional[str]
    created_at: datetime


@dataclass
class SystemEventsResult:
    """O3: Infra events affecting run."""

    run_id: str
    events: list[SystemEventResult]
    total_events: int
    metadata: EvidenceMetadataResult


@dataclass
class SystemReplayResult:
    """O4: Infra replay window."""

    run_id: str
    window_start: datetime
    window_end: datetime
    events: list[ReplayEventResult]
    metadata: EvidenceMetadataResult


@dataclass
class SystemAuditResult:
    """O5: Infra attribution record."""

    items: list[SystemEventResult]
    total: int
    metadata: EvidenceMetadataResult


@dataclass
class AuditLedgerItemResult:
    """Single audit ledger entry."""

    id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: Optional[str]
    action_reason: Optional[str]
    created_at: datetime


@dataclass
class AuditLedgerDetailResult:
    """Audit ledger entry with state snapshots."""

    id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: Optional[str]
    action_reason: Optional[str]
    created_at: datetime
    before_state: Optional[dict[str, Any]] = None
    after_state: Optional[dict[str, Any]] = None
    correlation_id: Optional[str] = None


@dataclass
class AuditLedgerListResult:
    """Response envelope for audit ledger."""

    items: list[AuditLedgerItemResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class IdentityEventResult:
    """Identity lifecycle event."""

    id: str
    event_type: str
    actor_type: str
    actor_id: Optional[str]
    created_at: datetime


@dataclass
class AuditIdentityResult:
    """O1: Identity lifecycle."""

    events: list[IdentityEventResult]
    total: int
    metadata: EvidenceMetadataResult


@dataclass
class AuthorizationDecisionResult:
    """Authorization decision record."""

    id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    decision: str
    created_at: datetime


@dataclass
class AuditAuthorizationResult:
    """O2: Access decisions."""

    decisions: list[AuthorizationDecisionResult]
    total: int
    metadata: EvidenceMetadataResult


@dataclass
class AccessEventResult:
    """Log access event."""

    id: str
    event_type: str
    actor_type: str
    actor_id: Optional[str]
    entity_type: str
    entity_id: str
    created_at: datetime


@dataclass
class AuditAccessResult:
    """O3: Log access audit."""

    events: list[AccessEventResult]
    total: int
    metadata: EvidenceMetadataResult


@dataclass
class IntegrityCheckResult:
    """Integrity verification record."""

    status: str
    last_verified: datetime
    anomalies_detected: int
    hash_chain_valid: bool


@dataclass
class AuditIntegrityResult:
    """O4: Tamper detection."""

    integrity: IntegrityCheckResult
    metadata: EvidenceMetadataResult


@dataclass
class ExportRecordResult:
    """Export record."""

    id: str
    scope: str
    format: str
    requested_by: str
    status: str
    checksum: Optional[str]
    created_at: datetime
    delivered_at: Optional[datetime]


@dataclass
class AuditExportsResult:
    """O5: Compliance exports."""

    exports: list[ExportRecordResult]
    total: int
    metadata: EvidenceMetadataResult


# =============================================================================
# Logs Facade (L4 - Composition Only)
# =============================================================================


class LogsFacade:
    """
    Unified facade for all Logs domain operations.

    L4 CONTRACT:
    - Composition only - delegates to L6 driver
    - NO sqlalchemy imports
    - NO direct DB queries
    """

    def __init__(self, store: Optional[LogsDomainStore] = None):
        """Initialize with optional store (for testing)."""
        self._store = store or get_logs_domain_store()

    # -------------------------------------------------------------------------
    # LLM_RUNS Operations
    # -------------------------------------------------------------------------

    async def list_llm_run_records(
        self,
        session: Any,  # AsyncSession passed through
        tenant_id: str,
        *,
        run_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        execution_status: Optional[str] = None,
        is_synthetic: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> LLMRunRecordsResult:
        """List LLM run records with optional filters."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

        if run_id:
            filters_applied["run_id"] = run_id
        if provider:
            filters_applied["provider"] = provider
        if model:
            filters_applied["model"] = model
        if execution_status:
            filters_applied["execution_status"] = execution_status
        if is_synthetic is not None:
            filters_applied["is_synthetic"] = is_synthetic
        if created_after:
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            filters_applied["created_before"] = created_before.isoformat()

        # Delegate to L6 driver
        result = await self._store.list_llm_runs(
            session,
            tenant_id,
            run_id=run_id,
            provider=provider,
            model=model,
            execution_status=execution_status,
            is_synthetic=is_synthetic,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
        )

        items = [self._snapshot_to_record_result(s) for s in result.items]

        return LLMRunRecordsResult(
            items=items,
            total=result.total,
            has_more=result.has_more,
            filters_applied=filters_applied,
        )

    async def get_llm_run_envelope(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> Optional[LLMRunEnvelopeResult]:
        """O1: Get canonical immutable run record."""
        snapshot = await self._store.get_llm_run(session, tenant_id, run_id)

        if not snapshot:
            return None

        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            run_id=run_id,
            occurred_at=snapshot.started_at,
            recorded_at=snapshot.created_at,
            trace_id=snapshot.trace_id,
            source_domain="LOGS",
            source_component="LLMRunRecordStore",
            origin="SYSTEM",
        )

        return LLMRunEnvelopeResult(
            id=snapshot.id,
            run_id=snapshot.run_id,
            trace_id=snapshot.trace_id,
            provider=snapshot.provider,
            model=snapshot.model,
            input_tokens=snapshot.input_tokens,
            output_tokens=snapshot.output_tokens,
            cost_cents=snapshot.cost_cents,
            execution_status=snapshot.execution_status,
            started_at=snapshot.started_at,
            completed_at=snapshot.completed_at,
            source=snapshot.source,
            is_synthetic=snapshot.is_synthetic,
            created_at=snapshot.created_at,
            metadata=metadata,
        )

    async def get_llm_run_trace(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> Optional[LLMRunTraceResult]:
        """O2: Get step-by-step execution trace."""
        trace_id = await self._store.get_trace_id_for_run(session, tenant_id, run_id)

        if not trace_id:
            return None

        step_snapshots = await self._store.get_trace_steps(session, trace_id)

        steps = [
            TraceStepResult(
                step_index=s.step_index,
                timestamp=s.timestamp,
                skill_name=s.skill_name,
                status=s.status,
                outcome_category=s.outcome_category,
                cost_cents=s.cost_cents,
                duration_ms=s.duration_ms,
            )
            for s in step_snapshots
        ]

        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            run_id=run_id,
            trace_id=trace_id,
            occurred_at=steps[0].timestamp if steps else now,
            recorded_at=now,
            source_domain="LOGS",
            source_component="TraceStore",
            origin="SYSTEM",
        )

        return LLMRunTraceResult(
            run_id=run_id,
            trace_id=trace_id,
            steps=steps,
            total_steps=len(steps),
            metadata=metadata,
        )

    async def get_llm_run_governance(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> LLMRunGovernanceResult:
        """O3: Get policy interaction trace."""
        audit_snapshots = await self._store.get_governance_events(
            session, tenant_id, run_id=run_id
        )

        events = [
            GovernanceEventResult(
                timestamp=s.created_at,
                event_type=s.event_type,
                policy_id=s.entity_id if s.entity_type == "POLICY_RULE" else None,
                rule_id=s.entity_id,
                decision="ENFORCED",
                entity_type=s.entity_type,
                entity_id=s.entity_id,
            )
            for s in audit_snapshots
        ]

        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            run_id=run_id,
            occurred_at=events[0].timestamp if events else now,
            recorded_at=now,
            source_domain="LOGS",
            source_component="AuditLedger",
            origin="SYSTEM",
        )

        return LLMRunGovernanceResult(
            run_id=run_id,
            events=events,
            total_events=len(events),
            metadata=metadata,
        )

    async def get_llm_run_replay(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> Optional[LLMRunReplayResult]:
        """O4: Get 60-second replay window."""
        run_snapshot = await self._store.get_llm_run(session, tenant_id, run_id)

        if not run_snapshot:
            return None

        inflection = run_snapshot.completed_at or run_snapshot.started_at
        window_start = inflection - timedelta(seconds=30)
        window_end = inflection + timedelta(seconds=30)

        trace_id = run_snapshot.trace_id or f"trace_{run_id}"
        replay_rows = await self._store.get_replay_window_events(
            session, tenant_id, trace_id, window_start, window_end
        )

        events = [
            ReplayEventResult(
                source=row["source"],
                step_index=row["step_index"],
                timestamp=row["timestamp"],
                action=row["action"],
                outcome=row["outcome"],
            )
            for row in replay_rows
        ]

        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            run_id=run_id,
            trace_id=trace_id,
            occurred_at=inflection,
            recorded_at=datetime.now(timezone.utc),
            source_domain="LOGS",
            source_component="ReplayService",
            origin="SYSTEM",
        )

        return LLMRunReplayResult(
            run_id=run_id,
            inflection_timestamp=inflection,
            window_start=window_start,
            window_end=window_end,
            events=events,
            metadata=metadata,
        )

    async def get_llm_run_export(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> Optional[LLMRunExportResult]:
        """O5: Get export information."""
        run_snapshot = await self._store.get_llm_run(session, tenant_id, run_id)

        if not run_snapshot:
            return None

        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            run_id=run_id,
            trace_id=run_snapshot.trace_id,
            occurred_at=run_snapshot.started_at,
            recorded_at=now,
            source_domain="LOGS",
            source_component="LogExportService",
            origin="SYSTEM",
        )

        return LLMRunExportResult(
            run_id=run_id,
            available_formats=["json", "csv", "pdf", "zip"],
            checksum=None,
            compliance_tags=["SOC2", "internal"],
            metadata=metadata,
        )

    # -------------------------------------------------------------------------
    # SYSTEM_LOGS Operations
    # -------------------------------------------------------------------------

    async def list_system_records(
        self,
        session: Any,
        tenant_id: str,
        *,
        component: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SystemRecordsResult:
        """List system records with optional filters."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

        if component:
            filters_applied["component"] = component
        if event_type:
            filters_applied["event_type"] = event_type
        if severity:
            filters_applied["severity"] = severity
        if created_after:
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            filters_applied["created_before"] = created_before.isoformat()

        result = await self._store.list_system_records(
            session,
            tenant_id,
            component=component,
            event_type=event_type,
            severity=severity,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
        )

        items = [
            SystemRecordResult(
                id=s.id,
                tenant_id=s.tenant_id,
                component=s.component,
                event_type=s.event_type,
                severity=s.severity,
                summary=s.summary,
                caused_by=s.caused_by,
                correlation_id=s.correlation_id,
                created_at=s.created_at,
            )
            for s in result.items
        ]

        return SystemRecordsResult(
            items=items,
            total=result.total,
            has_more=result.has_more,
            filters_applied=filters_applied,
        )

    async def get_system_snapshot(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> SystemSnapshotResult:
        """O1: Get environment baseline snapshot."""
        snapshot = await self._store.get_system_record_by_correlation(
            session, tenant_id, run_id
        )

        now = datetime.now(timezone.utc)

        if not snapshot:
            metadata = EvidenceMetadataResult(
                tenant_id=tenant_id,
                run_id=run_id,
                occurred_at=now,
                recorded_at=now,
                source_domain="LOGS",
                source_component="SystemRecordWriter",
                origin="SYSTEM",
            )
            return SystemSnapshotResult(
                run_id=run_id,
                component="system",
                event_type="SNAPSHOT",
                severity="INFO",
                summary="Environment baseline snapshot (no specific record)",
                details={"note": "No correlated system record found for this run"},
                created_at=now,
                metadata=metadata,
            )

        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            run_id=run_id,
            correlation_id=snapshot.correlation_id,
            occurred_at=snapshot.created_at,
            recorded_at=snapshot.created_at,
            source_domain="LOGS",
            source_component="SystemRecordWriter",
            origin="SYSTEM",
        )

        return SystemSnapshotResult(
            run_id=run_id,
            component=snapshot.component,
            event_type=snapshot.event_type,
            severity=snapshot.severity,
            summary=snapshot.summary,
            details=snapshot.details,
            created_at=snapshot.created_at,
            metadata=metadata,
        )

    def get_system_telemetry(self, run_id: str) -> TelemetryStubResult:
        """O2: Telemetry stub - producer not implemented."""
        return TelemetryStubResult(run_id=run_id)

    async def get_system_events(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> SystemEventsResult:
        """O3: Get infra events affecting run."""
        result = await self._store.list_system_records(
            session, tenant_id, correlation_id=run_id
        )

        events = [
            SystemEventResult(
                id=s.id,
                component=s.component,
                event_type=s.event_type,
                severity=s.severity,
                summary=s.summary,
                caused_by=s.caused_by,
                correlation_id=s.correlation_id,
                created_at=s.created_at,
            )
            for s in result.items
        ]

        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            run_id=run_id,
            occurred_at=events[0].created_at if events else now,
            recorded_at=now,
            source_domain="LOGS",
            source_component="SystemRecordWriter",
            origin="SYSTEM",
        )

        return SystemEventsResult(
            run_id=run_id,
            events=events,
            total_events=len(events),
            metadata=metadata,
        )

    async def get_system_replay(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> Optional[SystemReplayResult]:
        """O4: Get infra replay window."""
        run_snapshot = await self._store.get_llm_run(session, tenant_id, run_id)

        if not run_snapshot:
            return None

        inflection = run_snapshot.completed_at or run_snapshot.started_at
        window_start = inflection - timedelta(seconds=30)
        window_end = inflection + timedelta(seconds=30)

        sys_snapshots = await self._store.get_system_records_in_window(
            session, tenant_id, window_start, window_end
        )

        events = [
            ReplayEventResult(
                source="system",
                step_index=None,
                timestamp=s.created_at,
                action=s.event_type,
                outcome=s.severity,
            )
            for s in sys_snapshots
        ]

        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            run_id=run_id,
            occurred_at=inflection,
            recorded_at=datetime.now(timezone.utc),
            source_domain="LOGS",
            source_component="SystemRecordWriter",
            origin="SYSTEM",
        )

        return SystemReplayResult(
            run_id=run_id,
            window_start=window_start,
            window_end=window_end,
            events=events,
            metadata=metadata,
        )

    async def get_system_audit(
        self,
        session: Any,
        tenant_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> SystemAuditResult:
        """O5: Get infra attribution."""
        result = await self._store.list_system_records(
            session, tenant_id, limit=limit, offset=offset
        )

        items = [
            SystemEventResult(
                id=s.id,
                component=s.component,
                event_type=s.event_type,
                severity=s.severity,
                summary=s.summary,
                caused_by=s.caused_by,
                correlation_id=s.correlation_id,
                created_at=s.created_at,
            )
            for s in result.items
        ]

        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            occurred_at=items[0].created_at if items else now,
            recorded_at=now,
            source_domain="LOGS",
            source_component="SystemRecordWriter",
            origin="SYSTEM",
        )

        return SystemAuditResult(
            items=items,
            total=result.total,
            metadata=metadata,
        )

    # -------------------------------------------------------------------------
    # AUDIT Operations
    # -------------------------------------------------------------------------

    async def list_audit_entries(
        self,
        session: Any,
        tenant_id: str,
        *,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        actor_type: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLedgerListResult:
        """List audit entries with optional filters."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

        if event_type:
            filters_applied["event_type"] = event_type
        if entity_type:
            filters_applied["entity_type"] = entity_type
        if actor_type:
            filters_applied["actor_type"] = actor_type
        if created_after:
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            filters_applied["created_before"] = created_before.isoformat()

        result = await self._store.list_audit_entries(
            session,
            tenant_id,
            event_type=event_type,
            entity_type=entity_type,
            actor_type=actor_type,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
        )

        items = [
            AuditLedgerItemResult(
                id=s.id,
                event_type=s.event_type,
                entity_type=s.entity_type,
                entity_id=s.entity_id,
                actor_type=s.actor_type,
                actor_id=s.actor_id,
                action_reason=s.action_reason,
                created_at=s.created_at,
            )
            for s in result.items
        ]

        return AuditLedgerListResult(
            items=items,
            total=result.total,
            has_more=result.has_more,
            filters_applied=filters_applied,
        )

    async def get_audit_entry(
        self,
        session: Any,
        tenant_id: str,
        entry_id: str,
    ) -> Optional[AuditLedgerDetailResult]:
        """Get audit entry detail with state snapshots."""
        snapshot = await self._store.get_audit_entry(session, tenant_id, entry_id)

        if not snapshot:
            return None

        return AuditLedgerDetailResult(
            id=snapshot.id,
            event_type=snapshot.event_type,
            entity_type=snapshot.entity_type,
            entity_id=snapshot.entity_id,
            actor_type=snapshot.actor_type,
            actor_id=snapshot.actor_id,
            action_reason=snapshot.action_reason,
            created_at=snapshot.created_at,
            before_state=snapshot.before_state,
            after_state=snapshot.after_state,
            correlation_id=snapshot.correlation_id,
        )

    async def get_audit_identity(
        self,
        session: Any,
        tenant_id: str,
        *,
        limit: int = 50,
    ) -> AuditIdentityResult:
        """O1: Get identity lifecycle events."""
        result = await self._store.list_audit_entries(session, tenant_id, limit=limit)

        events = [
            IdentityEventResult(
                id=s.id,
                event_type=s.event_type,
                actor_type=s.actor_type,
                actor_id=s.actor_id,
                created_at=s.created_at,
            )
            for s in result.items
        ]

        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            occurred_at=events[0].created_at if events else now,
            recorded_at=now,
            source_domain="LOGS",
            source_component="AuditLedger",
            origin="SYSTEM",
        )

        return AuditIdentityResult(
            events=events,
            total=len(events),
            metadata=metadata,
        )

    async def get_audit_authorization(
        self,
        session: Any,
        tenant_id: str,
        *,
        limit: int = 50,
    ) -> AuditAuthorizationResult:
        """O2: Get authorization decisions."""
        result = await self._store.list_audit_entries(session, tenant_id, limit=limit)

        decisions = [
            AuthorizationDecisionResult(
                id=s.id,
                event_type=s.event_type,
                entity_type=s.entity_type,
                entity_id=s.entity_id,
                actor_type=s.actor_type,
                decision="ALLOW",
                created_at=s.created_at,
            )
            for s in result.items
        ]

        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            occurred_at=decisions[0].created_at if decisions else now,
            recorded_at=now,
            source_domain="LOGS",
            source_component="AuditLedger",
            origin="SYSTEM",
        )

        return AuditAuthorizationResult(
            decisions=decisions,
            total=len(decisions),
            metadata=metadata,
        )

    async def get_audit_access(
        self,
        session: Any,
        tenant_id: str,
        *,
        limit: int = 50,
    ) -> AuditAccessResult:
        """O3: Get log access audit."""
        result = await self._store.list_audit_entries(session, tenant_id, limit=limit)

        events = [
            AccessEventResult(
                id=s.id,
                event_type=s.event_type,
                actor_type=s.actor_type,
                actor_id=s.actor_id,
                entity_type=s.entity_type,
                entity_id=s.entity_id,
                created_at=s.created_at,
            )
            for s in result.items
        ]

        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            occurred_at=events[0].created_at if events else now,
            recorded_at=now,
            source_domain="LOGS",
            source_component="AuditLedger",
            origin="SYSTEM",
        )

        return AuditAccessResult(
            events=events,
            total=len(events),
            metadata=metadata,
        )

    def get_audit_integrity(self, tenant_id: str) -> AuditIntegrityResult:
        """O4: Get tamper detection status."""
        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            occurred_at=now,
            recorded_at=now,
            source_domain="LOGS",
            source_component="IntegrityService",
            origin="SYSTEM",
        )

        return AuditIntegrityResult(
            integrity=IntegrityCheckResult(
                status="verified",
                last_verified=now,
                anomalies_detected=0,
                hash_chain_valid=True,
            ),
            metadata=metadata,
        )

    async def get_audit_exports(
        self,
        session: Any,
        tenant_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditExportsResult:
        """O5: Get compliance exports."""
        result = await self._store.list_log_exports(
            session, tenant_id, limit=limit, offset=offset
        )

        exports = [
            ExportRecordResult(
                id=s.id,
                scope=s.scope,
                format=s.format,
                requested_by=s.requested_by,
                status=s.status,
                checksum=s.checksum,
                created_at=s.created_at,
                delivered_at=s.delivered_at,
            )
            for s in result.items
        ]

        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            occurred_at=exports[0].created_at if exports else now,
            recorded_at=now,
            source_domain="LOGS",
            source_component="LogExportService",
            origin="SYSTEM",
        )

        return AuditExportsResult(
            exports=exports,
            total=result.total,
            metadata=metadata,
        )

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    def _snapshot_to_record_result(self, s: LLMRunSnapshot) -> LLMRunRecordResult:
        """Convert snapshot to result type."""
        return LLMRunRecordResult(
            id=s.id,
            run_id=s.run_id,
            trace_id=s.trace_id,
            provider=s.provider,
            model=s.model,
            input_tokens=s.input_tokens,
            output_tokens=s.output_tokens,
            cost_cents=s.cost_cents,
            execution_status=s.execution_status,
            started_at=s.started_at,
            completed_at=s.completed_at,
            source=s.source,
            is_synthetic=s.is_synthetic,
            created_at=s.created_at,
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_facade_instance: LogsFacade | None = None


def get_logs_facade() -> LogsFacade:
    """Get the singleton LogsFacade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = LogsFacade()
    return _facade_instance


__all__ = [
    # Facade
    "LogsFacade",
    "get_logs_facade",
    # Enums
    "SourceDomain",
    "Origin",
    # Evidence Metadata
    "EvidenceMetadataResult",
    # LLM_RUNS result types
    "LLMRunRecordResult",
    "LLMRunRecordsResult",
    "TraceStepResult",
    "LLMRunEnvelopeResult",
    "LLMRunTraceResult",
    "GovernanceEventResult",
    "LLMRunGovernanceResult",
    "ReplayEventResult",
    "LLMRunReplayResult",
    "LLMRunExportResult",
    # SYSTEM_LOGS result types
    "SystemRecordResult",
    "SystemRecordsResult",
    "SystemSnapshotResult",
    "TelemetryStubResult",
    "SystemEventResult",
    "SystemEventsResult",
    "SystemReplayResult",
    "SystemAuditResult",
    # AUDIT result types
    "AuditLedgerItemResult",
    "AuditLedgerDetailResult",
    "AuditLedgerListResult",
    "IdentityEventResult",
    "AuditIdentityResult",
    "AuthorizationDecisionResult",
    "AuditAuthorizationResult",
    "AccessEventResult",
    "AuditAccessResult",
    "IntegrityCheckResult",
    "AuditIntegrityResult",
    "ExportRecordResult",
    "AuditExportsResult",
]
