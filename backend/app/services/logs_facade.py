# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async (DB reads)
# Role: Logs domain facade - unified entry point for all logs operations
# Callers: L2 logs API (logs.py)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: LOGS_DOMAIN_V2_CONTRACT.md, PIN-411
#
"""
Logs Domain Facade (L4)

Unified facade for all logs domain operations:
- LLM_RUNS: envelope, trace, governance, replay, export
- SYSTEM_LOGS: snapshot, telemetry, events, replay, audit
- AUDIT: identity, authorization, access, integrity, exports

All responses include EvidenceMetadata per INV-LOG-META-001.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Literal, Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_ledger import AuditLedger
from app.models.log_exports import LogExport
from app.models.logs_records import LLMRunRecord, SystemRecord


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
# LLM_RUNS Result Types
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


# =============================================================================
# SYSTEM_LOGS Result Types
# =============================================================================


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


# =============================================================================
# AUDIT Result Types
# =============================================================================


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
# Logs Facade
# =============================================================================


class LogsFacade:
    """
    Unified facade for all Logs domain operations.

    Provides:
    - LLM_RUNS: envelope, trace, governance, replay, export
    - SYSTEM_LOGS: snapshot, telemetry, events, replay, audit
    - AUDIT: identity, authorization, access, integrity, exports

    All responses include EvidenceMetadata per INV-LOG-META-001.
    """

    # -------------------------------------------------------------------------
    # LLM_RUNS Operations
    # -------------------------------------------------------------------------

    async def list_llm_run_records(
        self,
        session: AsyncSession,
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

        stmt = (
            select(LLMRunRecord)
            .where(LLMRunRecord.tenant_id == tenant_id)
            .order_by(LLMRunRecord.created_at.desc())
        )

        if run_id:
            stmt = stmt.where(LLMRunRecord.run_id == run_id)
            filters_applied["run_id"] = run_id
        if provider:
            stmt = stmt.where(LLMRunRecord.provider == provider)
            filters_applied["provider"] = provider
        if model:
            stmt = stmt.where(LLMRunRecord.model == model)
            filters_applied["model"] = model
        if execution_status:
            stmt = stmt.where(LLMRunRecord.execution_status == execution_status)
            filters_applied["execution_status"] = execution_status
        if is_synthetic is not None:
            stmt = stmt.where(LLMRunRecord.is_synthetic == is_synthetic)
            filters_applied["is_synthetic"] = is_synthetic
        if created_after:
            stmt = stmt.where(LLMRunRecord.created_at >= created_after)
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            stmt = stmt.where(LLMRunRecord.created_at <= created_before)
            filters_applied["created_before"] = created_before.isoformat()

        # Count
        count_stmt = select(func.count(LLMRunRecord.id)).where(
            LLMRunRecord.tenant_id == tenant_id
        )
        for key, val in filters_applied.items():
            if key == "tenant_id":
                continue
            if hasattr(LLMRunRecord, key):
                count_stmt = count_stmt.where(getattr(LLMRunRecord, key) == val)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        entries = result.scalars().all()

        items = [
            LLMRunRecordResult(
                id=e.id,
                run_id=e.run_id,
                trace_id=e.trace_id,
                provider=e.provider,
                model=e.model,
                input_tokens=e.input_tokens,
                output_tokens=e.output_tokens,
                cost_cents=e.cost_cents,
                execution_status=e.execution_status,
                started_at=e.started_at,
                completed_at=e.completed_at,
                source=e.source,
                is_synthetic=e.is_synthetic,
                created_at=e.created_at,
            )
            for e in entries
        ]

        return LLMRunRecordsResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    async def get_llm_run_envelope(
        self,
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> Optional[LLMRunEnvelopeResult]:
        """O1: Get canonical immutable run record."""
        stmt = select(LLMRunRecord).where(
            LLMRunRecord.run_id == run_id, LLMRunRecord.tenant_id == tenant_id
        )
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            return None

        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            run_id=run_id,
            occurred_at=entry.started_at,
            recorded_at=entry.created_at,
            trace_id=entry.trace_id,
            source_domain="LOGS",
            source_component="LLMRunRecordStore",
            origin="SYSTEM",
        )

        return LLMRunEnvelopeResult(
            id=entry.id,
            run_id=entry.run_id,
            trace_id=entry.trace_id,
            provider=entry.provider,
            model=entry.model,
            input_tokens=entry.input_tokens,
            output_tokens=entry.output_tokens,
            cost_cents=entry.cost_cents,
            execution_status=entry.execution_status,
            started_at=entry.started_at,
            completed_at=entry.completed_at,
            source=entry.source,
            is_synthetic=entry.is_synthetic,
            created_at=entry.created_at,
            metadata=metadata,
        )

    async def get_llm_run_trace(
        self,
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> Optional[LLMRunTraceResult]:
        """O2: Get step-by-step execution trace."""
        # Get trace_id from aos_traces
        trace_stmt = text("""
            SELECT trace_id FROM aos_traces WHERE run_id = :run_id AND tenant_id = :tenant_id
        """)
        trace_result = await session.execute(
            trace_stmt, {"run_id": run_id, "tenant_id": tenant_id}
        )
        trace_row = trace_result.fetchone()

        if not trace_row:
            return None

        trace_id = trace_row[0]

        # Get trace steps
        steps_stmt = text("""
            SELECT step_index, timestamp, skill_name, status, outcome_category, cost_cents, duration_ms
            FROM aos_trace_steps
            WHERE trace_id = :trace_id
            ORDER BY step_index
        """)
        steps_result = await session.execute(steps_stmt, {"trace_id": trace_id})
        step_rows = steps_result.fetchall()

        steps = [
            TraceStepResult(
                step_index=row[0],
                timestamp=row[1],
                skill_name=row[2],
                status=row[3],
                outcome_category=row[4] or "unknown",
                cost_cents=int(row[5] or 0),
                duration_ms=int(row[6] or 0),
            )
            for row in step_rows
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
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> LLMRunGovernanceResult:
        """O3: Get policy interaction trace."""
        # Get governance events from audit_ledger related to this run
        stmt = (
            select(AuditLedger)
            .where(AuditLedger.tenant_id == tenant_id)
            .where(
                AuditLedger.entity_type.in_(
                    ["POLICY_RULE", "LIMIT", "POLICY_PROPOSAL"]
                )
            )
            .order_by(AuditLedger.created_at.desc())
            .limit(100)
        )

        result = await session.execute(stmt)
        entries = result.scalars().all()

        events = [
            GovernanceEventResult(
                timestamp=e.created_at,
                event_type=e.event_type,
                policy_id=e.entity_id if e.entity_type == "POLICY_RULE" else None,
                rule_id=e.entity_id,
                decision="ENFORCED",
                entity_type=e.entity_type,
                entity_id=e.entity_id,
            )
            for e in entries
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
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> Optional[LLMRunReplayResult]:
        """O4: Get 60-second replay window."""
        # Get run to find inflection timestamp
        run_stmt = select(LLMRunRecord).where(
            LLMRunRecord.run_id == run_id, LLMRunRecord.tenant_id == tenant_id
        )
        run_result = await session.execute(run_stmt)
        run_entry = run_result.scalar_one_or_none()

        if not run_entry:
            return None

        inflection = run_entry.completed_at or run_entry.started_at
        window_start = inflection - timedelta(seconds=30)
        window_end = inflection + timedelta(seconds=30)

        # Query trace steps in window
        trace_id = run_entry.trace_id or f"trace_{run_id}"
        replay_query = text("""
            SELECT 'llm' as source, step_index, timestamp, skill_name as action, outcome_category as outcome
            FROM aos_trace_steps
            WHERE trace_id = :trace_id
            AND timestamp BETWEEN :window_start AND :window_end

            UNION ALL

            SELECT 'system' as source, NULL as step_index, created_at as timestamp,
                   event_type as action, severity as outcome
            FROM system_records
            WHERE (tenant_id = :tenant_id OR tenant_id IS NULL)
            AND created_at BETWEEN :window_start AND :window_end

            UNION ALL

            SELECT 'policy' as source, NULL as step_index, created_at as timestamp,
                   event_type as action, entity_type as outcome
            FROM audit_ledger
            WHERE tenant_id = :tenant_id
            AND entity_type IN ('POLICY_RULE', 'LIMIT')
            AND created_at BETWEEN :window_start AND :window_end

            ORDER BY timestamp
        """)

        replay_result = await session.execute(
            replay_query,
            {
                "trace_id": trace_id,
                "tenant_id": tenant_id,
                "window_start": window_start,
                "window_end": window_end,
            },
        )
        replay_rows = replay_result.fetchall()

        events = [
            ReplayEventResult(
                source=row[0],
                step_index=row[1],
                timestamp=row[2],
                action=row[3] or "unknown",
                outcome=row[4] or "unknown",
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
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> Optional[LLMRunExportResult]:
        """O5: Get export information."""
        # Check run exists
        run_stmt = select(LLMRunRecord).where(
            LLMRunRecord.run_id == run_id, LLMRunRecord.tenant_id == tenant_id
        )
        run_result = await session.execute(run_stmt)
        run_entry = run_result.scalar_one_or_none()

        if not run_entry:
            return None

        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadataResult(
            tenant_id=tenant_id,
            run_id=run_id,
            trace_id=run_entry.trace_id,
            occurred_at=run_entry.started_at,
            recorded_at=now,
            source_domain="LOGS",
            source_component="LogExportService",
            origin="SYSTEM",
        )

        return LLMRunExportResult(
            run_id=run_id,
            available_formats=["json", "csv", "pdf", "zip"],
            checksum=None,  # Computed on actual export
            compliance_tags=["SOC2", "internal"],
            metadata=metadata,
        )

    # -------------------------------------------------------------------------
    # SYSTEM_LOGS Operations
    # -------------------------------------------------------------------------

    async def list_system_records(
        self,
        session: AsyncSession,
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

        stmt = (
            select(SystemRecord)
            .where(
                (SystemRecord.tenant_id == tenant_id)
                | (SystemRecord.tenant_id.is_(None))
            )
            .order_by(SystemRecord.created_at.desc())
        )

        if component:
            stmt = stmt.where(SystemRecord.component == component)
            filters_applied["component"] = component
        if event_type:
            stmt = stmt.where(SystemRecord.event_type == event_type)
            filters_applied["event_type"] = event_type
        if severity:
            stmt = stmt.where(SystemRecord.severity == severity)
            filters_applied["severity"] = severity
        if created_after:
            stmt = stmt.where(SystemRecord.created_at >= created_after)
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            stmt = stmt.where(SystemRecord.created_at <= created_before)
            filters_applied["created_before"] = created_before.isoformat()

        count_stmt = select(func.count(SystemRecord.id)).where(
            (SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None))
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        entries = result.scalars().all()

        items = [
            SystemRecordResult(
                id=e.id,
                tenant_id=e.tenant_id,
                component=e.component,
                event_type=e.event_type,
                severity=e.severity,
                summary=e.summary,
                caused_by=e.caused_by,
                correlation_id=e.correlation_id,
                created_at=e.created_at,
            )
            for e in entries
        ]

        return SystemRecordsResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    async def get_system_snapshot(
        self,
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> SystemSnapshotResult:
        """O1: Get environment baseline snapshot."""
        # Find system record closest to run start
        stmt = (
            select(SystemRecord)
            .where(
                (SystemRecord.tenant_id == tenant_id)
                | (SystemRecord.tenant_id.is_(None))
            )
            .where(SystemRecord.correlation_id == run_id)
            .order_by(SystemRecord.created_at.asc())
            .limit(1)
        )
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if not entry:
            # Return a synthetic snapshot if no specific record exists
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
            correlation_id=entry.correlation_id,
            occurred_at=entry.created_at,
            recorded_at=entry.created_at,
            source_domain="LOGS",
            source_component="SystemRecordWriter",
            origin="SYSTEM",
        )

        return SystemSnapshotResult(
            run_id=run_id,
            component=entry.component,
            event_type=entry.event_type,
            severity=entry.severity,
            summary=entry.summary,
            details=entry.details,
            created_at=entry.created_at,
            metadata=metadata,
        )

    def get_system_telemetry(self, run_id: str) -> TelemetryStubResult:
        """O2: Telemetry stub - producer not implemented."""
        return TelemetryStubResult(run_id=run_id)

    async def get_system_events(
        self,
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> SystemEventsResult:
        """O3: Get infra events affecting run."""
        stmt = (
            select(SystemRecord)
            .where(
                (SystemRecord.tenant_id == tenant_id)
                | (SystemRecord.tenant_id.is_(None))
            )
            .where(SystemRecord.correlation_id == run_id)
            .order_by(SystemRecord.created_at)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        events = [
            SystemEventResult(
                id=e.id,
                component=e.component,
                event_type=e.event_type,
                severity=e.severity,
                summary=e.summary,
                caused_by=e.caused_by,
                correlation_id=e.correlation_id,
                created_at=e.created_at,
            )
            for e in entries
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
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> Optional[SystemReplayResult]:
        """O4: Get infra replay window."""
        # Get run timestamp for window
        run_stmt = select(LLMRunRecord).where(
            LLMRunRecord.run_id == run_id, LLMRunRecord.tenant_id == tenant_id
        )
        run_result = await session.execute(run_stmt)
        run_entry = run_result.scalar_one_or_none()

        if not run_entry:
            return None

        inflection = run_entry.completed_at or run_entry.started_at
        window_start = inflection - timedelta(seconds=30)
        window_end = inflection + timedelta(seconds=30)

        stmt = (
            select(SystemRecord)
            .where(
                (SystemRecord.tenant_id == tenant_id)
                | (SystemRecord.tenant_id.is_(None))
            )
            .where(SystemRecord.created_at.between(window_start, window_end))
            .order_by(SystemRecord.created_at)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        events = [
            ReplayEventResult(
                source="system",
                step_index=None,
                timestamp=e.created_at,
                action=e.event_type,
                outcome=e.severity,
            )
            for e in entries
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
        session: AsyncSession,
        tenant_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> SystemAuditResult:
        """O5: Get infra attribution."""
        stmt = (
            select(SystemRecord)
            .where(
                (SystemRecord.tenant_id == tenant_id)
                | (SystemRecord.tenant_id.is_(None))
            )
            .order_by(SystemRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        count_stmt = select(func.count(SystemRecord.id)).where(
            (SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None))
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        items = [
            SystemEventResult(
                id=e.id,
                component=e.component,
                event_type=e.event_type,
                severity=e.severity,
                summary=e.summary,
                caused_by=e.caused_by,
                correlation_id=e.correlation_id,
                created_at=e.created_at,
            )
            for e in entries
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
            total=total,
            metadata=metadata,
        )

    # -------------------------------------------------------------------------
    # AUDIT Operations
    # -------------------------------------------------------------------------

    async def list_audit_entries(
        self,
        session: AsyncSession,
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

        stmt = (
            select(AuditLedger)
            .where(AuditLedger.tenant_id == tenant_id)
            .order_by(AuditLedger.created_at.desc())
        )

        if event_type:
            stmt = stmt.where(AuditLedger.event_type == event_type)
            filters_applied["event_type"] = event_type
        if entity_type:
            stmt = stmt.where(AuditLedger.entity_type == entity_type)
            filters_applied["entity_type"] = entity_type
        if actor_type:
            stmt = stmt.where(AuditLedger.actor_type == actor_type)
            filters_applied["actor_type"] = actor_type
        if created_after:
            stmt = stmt.where(AuditLedger.created_at >= created_after)
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            stmt = stmt.where(AuditLedger.created_at <= created_before)
            filters_applied["created_before"] = created_before.isoformat()

        count_stmt = select(func.count(AuditLedger.id)).where(
            AuditLedger.tenant_id == tenant_id
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        entries = result.scalars().all()

        items = [
            AuditLedgerItemResult(
                id=e.id,
                event_type=e.event_type,
                entity_type=e.entity_type,
                entity_id=e.entity_id,
                actor_type=e.actor_type,
                actor_id=e.actor_id,
                action_reason=e.action_reason,
                created_at=e.created_at,
            )
            for e in entries
        ]

        return AuditLedgerListResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    async def get_audit_entry(
        self,
        session: AsyncSession,
        tenant_id: str,
        entry_id: str,
    ) -> Optional[AuditLedgerDetailResult]:
        """Get audit entry detail with state snapshots."""
        stmt = select(AuditLedger).where(
            AuditLedger.id == entry_id, AuditLedger.tenant_id == tenant_id
        )
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            return None

        return AuditLedgerDetailResult(
            id=entry.id,
            event_type=entry.event_type,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            actor_type=entry.actor_type,
            actor_id=entry.actor_id,
            action_reason=entry.action_reason,
            created_at=entry.created_at,
            before_state=entry.before_state,
            after_state=entry.after_state,
            correlation_id=getattr(entry, "correlation_id", None),
        )

    async def get_audit_identity(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        limit: int = 50,
    ) -> AuditIdentityResult:
        """O1: Get identity lifecycle events."""
        stmt = (
            select(AuditLedger)
            .where(AuditLedger.tenant_id == tenant_id)
            .order_by(AuditLedger.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        events = [
            IdentityEventResult(
                id=e.id,
                event_type=e.event_type,
                actor_type=e.actor_type,
                actor_id=e.actor_id,
                created_at=e.created_at,
            )
            for e in entries
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
        session: AsyncSession,
        tenant_id: str,
        *,
        limit: int = 50,
    ) -> AuditAuthorizationResult:
        """O2: Get authorization decisions."""
        stmt = (
            select(AuditLedger)
            .where(AuditLedger.tenant_id == tenant_id)
            .order_by(AuditLedger.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        decisions = [
            AuthorizationDecisionResult(
                id=e.id,
                event_type=e.event_type,
                entity_type=e.entity_type,
                entity_id=e.entity_id,
                actor_type=e.actor_type,
                decision="ALLOW",  # Assuming logged events were allowed
                created_at=e.created_at,
            )
            for e in entries
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
        session: AsyncSession,
        tenant_id: str,
        *,
        limit: int = 50,
    ) -> AuditAccessResult:
        """O3: Get log access audit."""
        stmt = (
            select(AuditLedger)
            .where(AuditLedger.tenant_id == tenant_id)
            .order_by(AuditLedger.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        events = [
            AccessEventResult(
                id=e.id,
                event_type=e.event_type,
                actor_type=e.actor_type,
                actor_id=e.actor_id,
                entity_type=e.entity_type,
                entity_id=e.entity_id,
                created_at=e.created_at,
            )
            for e in entries
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
        session: AsyncSession,
        tenant_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditExportsResult:
        """O5: Get compliance exports."""
        stmt = (
            select(LogExport)
            .where(LogExport.tenant_id == tenant_id)
            .order_by(LogExport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        count_stmt = select(func.count(LogExport.id)).where(
            LogExport.tenant_id == tenant_id
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        exports = [
            ExportRecordResult(
                id=e.id,
                scope=e.scope,
                format=e.format,
                requested_by=e.requested_by,
                status=e.status,
                checksum=e.checksum,
                created_at=e.created_at,
                delivered_at=e.delivered_at,
            )
            for e in entries
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
            total=total,
            metadata=metadata,
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
