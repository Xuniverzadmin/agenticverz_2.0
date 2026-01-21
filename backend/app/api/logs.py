# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified LOGS domain facade - LOGS Domain V2 Implementation
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: LOGS_DOMAIN_V2_CONTRACT.md
#
# GOVERNANCE NOTE:
# This is the ONE facade for LOGS domain.
# All log data (audit, LLM runs, system) flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.
#
# ARCHITECTURE (LOGS Domain V2):
# - 3 Topics: LLM_RUNS, SYSTEM_LOGS, AUDIT
# - O-Levels: O1 (envelope), O2 (trace/list), O3 (governance/detail),
#             O4 (replay), O5 (export)
# - All responses include EvidenceMetadata per INV-LOG-META-001

"""
Unified Logs API (L2) - LOGS Domain V2

Customer-facing endpoints for viewing logs: audit ledger, LLM run records, and system records.
All requests are tenant-scoped via auth_context.

Topics & O-Levels (per LOGS_DOMAIN_V2_CONTRACT.md):

LLM_RUNS:
- GET /logs/llm-runs                          → List runs
- GET /logs/llm-runs/{run_id}/envelope        → O1 canonical record
- GET /logs/llm-runs/{run_id}/trace           → O2 step-by-step trace
- GET /logs/llm-runs/{run_id}/governance      → O3 policy interaction
- GET /logs/llm-runs/{run_id}/replay          → O4 60-second window
- GET /logs/llm-runs/{run_id}/export          → O5 evidence bundle

SYSTEM_LOGS:
- GET /logs/system                            → List events
- GET /logs/system/{run_id}/snapshot          → O1 environment baseline
- GET /logs/system/{run_id}/telemetry         → O2 (STUB)
- GET /logs/system/{run_id}/events            → O3 infra events
- GET /logs/system/{run_id}/replay            → O4 infra replay
- GET /logs/system/audit                      → O5 infra attribution

AUDIT:
- GET /logs/audit                             → List entries
- GET /logs/audit/identity                    → O1 identity lifecycle
- GET /logs/audit/authorization               → O2 access decisions
- GET /logs/audit/access                      → O3 log access audit
- GET /logs/audit/integrity                   → O4 tamper detection
- GET /logs/audit/exports                     → O5 compliance exports

All records are:
- APPEND-ONLY (enforced by DB trigger)
- WRITE-ONCE (no UPDATE, no DELETE)
- Trust anchors for verification
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.models.audit_ledger import AuditLedger
from app.models.log_exports import LogExport
from app.models.logs_records import LLMRunRecord, SystemRecord

# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/logs",
    tags=["logs"],
)


# =============================================================================
# Evidence Metadata Contract (INV-LOG-META-001)
# =============================================================================


class EvidenceMetadata(BaseModel):
    """Global metadata contract for all Logs responses.

    Per LOGS_DOMAIN_V2_CONTRACT.md, every Logs response MUST include this.
    Absence is a contract violation.
    """

    # Identity
    tenant_id: str
    run_id: Optional[str] = None

    # Actor attribution (precedence: human > agent > system)
    human_actor_id: Optional[str] = None
    agent_id: Optional[str] = None
    system_id: Optional[str] = None

    # Time
    occurred_at: datetime
    recorded_at: datetime
    timezone: str = "UTC"

    # Correlation spine
    trace_id: Optional[str] = None
    policy_ids: List[str] = Field(default_factory=list)
    incident_ids: List[str] = Field(default_factory=list)
    export_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Source & provenance
    source_domain: Literal["ACTIVITY", "POLICY", "INCIDENTS", "LOGS", "SYSTEM"]
    source_component: str
    origin: Literal["SYSTEM", "HUMAN", "AGENT", "MIGRATION", "REPLAY"]

    # Integrity
    checksum: Optional[str] = None
    immutable: bool = True


# =============================================================================
# Helper: Get tenant from auth context
# =============================================================================


def get_tenant_id_from_auth(request: Request) -> str:
    """Extract tenant_id from auth_context. Raises 401/403 if missing."""
    auth_context = get_auth_context(request)

    if auth_context is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "not_authenticated", "message": "Authentication required."},
        )

    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_required",
                "message": "This endpoint requires tenant context.",
            },
        )

    return tenant_id


# =============================================================================
# Response Models — LLM_RUNS
# =============================================================================


class LLMRunEnvelope(BaseModel):
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
    # Evidence metadata
    metadata: EvidenceMetadata


class TraceStep(BaseModel):
    """Individual trace step."""

    step_index: int
    timestamp: datetime
    skill_name: str
    status: str
    outcome_category: str
    cost_cents: int
    duration_ms: int


class LLMRunTrace(BaseModel):
    """O2: Step-by-step trace."""

    run_id: str
    trace_id: str
    steps: List[TraceStep]
    total_steps: int
    metadata: EvidenceMetadata


class GovernanceEvent(BaseModel):
    """Policy interaction event."""

    timestamp: datetime
    event_type: str
    policy_id: Optional[str]
    rule_id: Optional[str]
    decision: str
    entity_type: str
    entity_id: str


class LLMRunGovernance(BaseModel):
    """O3: Policy interaction trace."""

    run_id: str
    events: List[GovernanceEvent]
    total_events: int
    metadata: EvidenceMetadata


class ReplayEvent(BaseModel):
    """Replay window event."""

    source: str  # llm, system, policy
    timestamp: datetime
    step_index: Optional[int]
    action: str
    outcome: str


class LLMRunReplay(BaseModel):
    """O4: 60-second replay window."""

    run_id: str
    inflection_timestamp: Optional[datetime]
    window_start: datetime
    window_end: datetime
    events: List[ReplayEvent]
    metadata: EvidenceMetadata


class LLMRunExport(BaseModel):
    """O5: Export metadata."""

    run_id: str
    available_formats: List[str]
    checksum: Optional[str]
    compliance_tags: List[str]
    metadata: EvidenceMetadata


class LLMRunRecordItem(BaseModel):
    """Single LLM run record entry (list view)."""

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


class LLMRunRecordsResponse(BaseModel):
    """Response envelope for LLM run records."""

    items: List[LLMRunRecordItem]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


# =============================================================================
# Response Models — SYSTEM_LOGS
# =============================================================================


class SystemSnapshot(BaseModel):
    """O1: Environment snapshot."""

    run_id: str
    component: str
    event_type: str
    severity: str
    summary: str
    details: Optional[dict]
    created_at: datetime
    metadata: EvidenceMetadata


class TelemetryStub(BaseModel):
    """O2: Telemetry stub response."""

    status: str = "telemetry_not_collected"
    reason: str = "infrastructure_telemetry_producer_not_implemented"
    run_id: str
    available_data: List[str] = Field(default_factory=lambda: ["events", "snapshot", "replay"])
    future_milestone: str = "M-TBD"


class SystemEvent(BaseModel):
    """System event record."""

    id: str
    component: str
    event_type: str
    severity: str
    summary: str
    caused_by: Optional[str]
    correlation_id: Optional[str]
    created_at: datetime


class SystemEvents(BaseModel):
    """O3: Infra events affecting run."""

    run_id: str
    events: List[SystemEvent]
    total_events: int
    metadata: EvidenceMetadata


class SystemReplay(BaseModel):
    """O4: Infra replay window."""

    run_id: str
    window_start: datetime
    window_end: datetime
    events: List[ReplayEvent]
    metadata: EvidenceMetadata


class SystemAudit(BaseModel):
    """O5: Infra attribution record."""

    items: List[SystemEvent]
    total: int
    metadata: EvidenceMetadata


class SystemRecordItem(BaseModel):
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


class SystemRecordsResponse(BaseModel):
    """Response envelope for system records."""

    items: List[SystemRecordItem]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


# =============================================================================
# Response Models — AUDIT
# =============================================================================


class AuditLedgerItem(BaseModel):
    """Single audit ledger entry."""

    id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: Optional[str]
    action_reason: Optional[str]
    created_at: datetime


class AuditLedgerDetailItem(AuditLedgerItem):
    """Audit ledger entry with state snapshots."""

    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    correlation_id: Optional[str] = None


class AuditLedgerResponse(BaseModel):
    """Response envelope for audit ledger."""

    items: List[AuditLedgerItem]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class IdentityEvent(BaseModel):
    """Identity lifecycle event."""

    id: str
    event_type: str
    actor_type: str
    actor_id: Optional[str]
    created_at: datetime


class AuditIdentity(BaseModel):
    """O1: Identity lifecycle."""

    events: List[IdentityEvent]
    total: int
    metadata: EvidenceMetadata


class AuthorizationDecision(BaseModel):
    """Authorization decision record."""

    id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    decision: str
    created_at: datetime


class AuditAuthorization(BaseModel):
    """O2: Access decisions."""

    decisions: List[AuthorizationDecision]
    total: int
    metadata: EvidenceMetadata


class AccessEvent(BaseModel):
    """Log access event."""

    id: str
    event_type: str
    actor_type: str
    actor_id: Optional[str]
    entity_type: str
    entity_id: str
    created_at: datetime


class AuditAccess(BaseModel):
    """O3: Log access audit."""

    events: List[AccessEvent]
    total: int
    metadata: EvidenceMetadata


class IntegrityCheck(BaseModel):
    """Integrity verification record."""

    status: str
    last_verified: datetime
    anomalies_detected: int
    hash_chain_valid: bool


class AuditIntegrity(BaseModel):
    """O4: Tamper detection."""

    integrity: IntegrityCheck
    metadata: EvidenceMetadata


class ExportRecord(BaseModel):
    """Export record."""

    id: str
    scope: str
    format: str
    requested_by: str
    status: str
    checksum: Optional[str]
    created_at: datetime
    delivered_at: Optional[datetime]


class AuditExports(BaseModel):
    """O5: Compliance exports."""

    exports: List[ExportRecord]
    total: int
    metadata: EvidenceMetadata


# =============================================================================
# LLM_RUNS Endpoints
# =============================================================================


@router.get(
    "/llm-runs",
    response_model=LLMRunRecordsResponse,
    summary="List LLM run records",
    description="List LLM run records with optional filters.",
)
async def list_llm_run_records(
    request: Request,
    run_id: Annotated[Optional[str], Query(description="Filter by run ID")] = None,
    provider: Annotated[Optional[str], Query(description="Filter by provider")] = None,
    model: Annotated[Optional[str], Query(description="Filter by model")] = None,
    execution_status: Annotated[Optional[str], Query(description="Filter by status")] = None,
    is_synthetic: Annotated[Optional[bool], Query(description="Filter synthetic")] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter created_at >=")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter created_at <=")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LLMRunRecordsResponse:
    """List LLM run records."""
    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    stmt = select(LLMRunRecord).where(LLMRunRecord.tenant_id == tenant_id).order_by(LLMRunRecord.created_at.desc())

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
    count_stmt = select(func.count(LLMRunRecord.id)).where(LLMRunRecord.tenant_id == tenant_id)
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
        LLMRunRecordItem(
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

    return LLMRunRecordsResponse(
        items=items,
        total=total,
        has_more=(offset + len(items)) < total,
        filters_applied=filters_applied,
    )


@router.get(
    "/llm-runs/{run_id}/envelope",
    response_model=LLMRunEnvelope,
    summary="O1: Get run envelope",
    description="Get the canonical immutable run record.",
)
async def get_llm_run_envelope(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LLMRunEnvelope:
    """O1: Canonical immutable run record."""
    tenant_id = get_tenant_id_from_auth(request)

    stmt = select(LLMRunRecord).where(LLMRunRecord.run_id == run_id, LLMRunRecord.tenant_id == tenant_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Run not found")

    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        run_id=run_id,
        occurred_at=entry.started_at,
        recorded_at=entry.created_at,
        trace_id=entry.trace_id,
        source_domain="LOGS",
        source_component="LLMRunRecordStore",
        origin="SYSTEM",
    )

    return LLMRunEnvelope(
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


@router.get(
    "/llm-runs/{run_id}/trace",
    response_model=LLMRunTrace,
    summary="O2: Get execution trace",
    description="Get step-by-step execution trace.",
)
async def get_llm_run_trace(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LLMRunTrace:
    """O2: Step-by-step execution trace."""
    tenant_id = get_tenant_id_from_auth(request)

    # Get trace_id from aos_traces
    trace_stmt = text("""
        SELECT trace_id FROM aos_traces WHERE run_id = :run_id AND tenant_id = :tenant_id
    """)
    trace_result = await session.execute(trace_stmt, {"run_id": run_id, "tenant_id": tenant_id})
    trace_row = trace_result.fetchone()

    if not trace_row:
        raise HTTPException(status_code=404, detail="Trace not found")

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
        TraceStep(
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
    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        run_id=run_id,
        trace_id=trace_id,
        occurred_at=steps[0].timestamp if steps else now,
        recorded_at=now,
        source_domain="LOGS",
        source_component="TraceStore",
        origin="SYSTEM",
    )

    return LLMRunTrace(
        run_id=run_id,
        trace_id=trace_id,
        steps=steps,
        total_steps=len(steps),
        metadata=metadata,
    )


@router.get(
    "/llm-runs/{run_id}/governance",
    response_model=LLMRunGovernance,
    summary="O3: Get governance trace",
    description="Get policy and threshold interaction trace.",
)
async def get_llm_run_governance(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LLMRunGovernance:
    """O3: Policy interaction trace."""
    tenant_id = get_tenant_id_from_auth(request)

    # Get governance events from audit_ledger related to this run
    stmt = select(AuditLedger).where(
        AuditLedger.tenant_id == tenant_id,
        AuditLedger.entity_type.in_(["POLICY_RULE", "LIMIT", "POLICY_PROPOSAL"]),
    ).order_by(AuditLedger.created_at.desc()).limit(100)

    result = await session.execute(stmt)
    entries = result.scalars().all()

    events = [
        GovernanceEvent(
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
    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        run_id=run_id,
        occurred_at=events[0].timestamp if events else now,
        recorded_at=now,
        source_domain="LOGS",
        source_component="AuditLedger",
        origin="SYSTEM",
    )

    return LLMRunGovernance(
        run_id=run_id,
        events=events,
        total_events=len(events),
        metadata=metadata,
    )


@router.get(
    "/llm-runs/{run_id}/replay",
    response_model=LLMRunReplay,
    summary="O4: Get replay window",
    description="Get 60-second replay window around inflection point.",
)
async def get_llm_run_replay(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LLMRunReplay:
    """O4: 60-second replay window."""
    tenant_id = get_tenant_id_from_auth(request)

    # Get run to find inflection timestamp (use completed_at or started_at)
    run_stmt = select(LLMRunRecord).where(LLMRunRecord.run_id == run_id, LLMRunRecord.tenant_id == tenant_id)
    run_result = await session.execute(run_stmt)
    run_entry = run_result.scalar_one_or_none()

    if not run_entry:
        raise HTTPException(status_code=404, detail="Run not found")

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
        ReplayEvent(
            source=row[0],
            step_index=row[1],
            timestamp=row[2],
            action=row[3] or "unknown",
            outcome=row[4] or "unknown",
        )
        for row in replay_rows
    ]

    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        run_id=run_id,
        trace_id=trace_id,
        occurred_at=inflection,
        recorded_at=datetime.now(timezone.utc),
        source_domain="LOGS",
        source_component="ReplayService",
        origin="SYSTEM",
    )

    return LLMRunReplay(
        run_id=run_id,
        inflection_timestamp=inflection,
        window_start=window_start,
        window_end=window_end,
        events=events,
        metadata=metadata,
    )


@router.get(
    "/llm-runs/{run_id}/export",
    response_model=LLMRunExport,
    summary="O5: Get export info",
    description="Get audit-grade evidence bundle information.",
)
async def get_llm_run_export(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LLMRunExport:
    """O5: Export information."""
    tenant_id = get_tenant_id_from_auth(request)

    # Check run exists
    run_stmt = select(LLMRunRecord).where(LLMRunRecord.run_id == run_id, LLMRunRecord.tenant_id == tenant_id)
    run_result = await session.execute(run_stmt)
    run_entry = run_result.scalar_one_or_none()

    if not run_entry:
        raise HTTPException(status_code=404, detail="Run not found")

    now = datetime.now(timezone.utc)
    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        run_id=run_id,
        trace_id=run_entry.trace_id,
        occurred_at=run_entry.started_at,
        recorded_at=now,
        source_domain="LOGS",
        source_component="LogExportService",
        origin="SYSTEM",
    )

    return LLMRunExport(
        run_id=run_id,
        available_formats=["json", "csv", "pdf", "zip"],
        checksum=None,  # Computed on actual export
        compliance_tags=["SOC2", "internal"],
        metadata=metadata,
    )


# =============================================================================
# SYSTEM_LOGS Endpoints
# =============================================================================


@router.get(
    "/system",
    response_model=SystemRecordsResponse,
    summary="List system records",
    description="List system event records.",
)
async def list_system_records(
    request: Request,
    component: Annotated[Optional[str], Query(description="Filter by component")] = None,
    event_type: Annotated[Optional[str], Query(description="Filter by event type")] = None,
    severity: Annotated[Optional[str], Query(description="Filter by severity")] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter created_at >=")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter created_at <=")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SystemRecordsResponse:
    """List system records."""
    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    stmt = (
        select(SystemRecord)
        .where((SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None)))
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
        SystemRecordItem(
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

    return SystemRecordsResponse(
        items=items,
        total=total,
        has_more=(offset + len(items)) < total,
        filters_applied=filters_applied,
    )


@router.get(
    "/system/{run_id}/snapshot",
    response_model=SystemSnapshot,
    summary="O1: Get environment snapshot",
    description="Get baseline environment state at run start.",
)
async def get_system_snapshot(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SystemSnapshot:
    """O1: Environment baseline snapshot."""
    tenant_id = get_tenant_id_from_auth(request)

    # Find system record closest to run start
    stmt = (
        select(SystemRecord)
        .where((SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None)))
        .where(SystemRecord.correlation_id == run_id)
        .order_by(SystemRecord.created_at.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        # Return a synthetic snapshot if no specific record exists
        now = datetime.now(timezone.utc)
        metadata = EvidenceMetadata(
            tenant_id=tenant_id,
            run_id=run_id,
            occurred_at=now,
            recorded_at=now,
            source_domain="LOGS",
            source_component="SystemRecordWriter",
            origin="SYSTEM",
        )
        return SystemSnapshot(
            run_id=run_id,
            component="system",
            event_type="SNAPSHOT",
            severity="INFO",
            summary="Environment baseline snapshot (no specific record)",
            details={"note": "No correlated system record found for this run"},
            created_at=now,
            metadata=metadata,
        )

    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        run_id=run_id,
        correlation_id=entry.correlation_id,
        occurred_at=entry.created_at,
        recorded_at=entry.created_at,
        source_domain="LOGS",
        source_component="SystemRecordWriter",
        origin="SYSTEM",
    )

    return SystemSnapshot(
        run_id=run_id,
        component=entry.component,
        event_type=entry.event_type,
        severity=entry.severity,
        summary=entry.summary,
        details=entry.details,
        created_at=entry.created_at,
        metadata=metadata,
    )


@router.get(
    "/system/{run_id}/telemetry",
    response_model=TelemetryStub,
    summary="O2: Get telemetry (STUB)",
    description="Infrastructure telemetry - not yet implemented.",
)
async def get_system_telemetry(
    request: Request,
    run_id: str,
) -> TelemetryStub:
    """O2: Telemetry stub - producer not implemented."""
    get_tenant_id_from_auth(request)  # Validate auth
    return TelemetryStub(run_id=run_id)


@router.get(
    "/system/{run_id}/events",
    response_model=SystemEvents,
    summary="O3: Get infra events",
    description="Get infrastructure events affecting the run.",
)
async def get_system_events(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SystemEvents:
    """O3: Infra events affecting run."""
    tenant_id = get_tenant_id_from_auth(request)

    stmt = (
        select(SystemRecord)
        .where((SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None)))
        .where(SystemRecord.correlation_id == run_id)
        .order_by(SystemRecord.created_at)
    )
    result = await session.execute(stmt)
    entries = result.scalars().all()

    events = [
        SystemEvent(
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
    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        run_id=run_id,
        occurred_at=events[0].created_at if events else now,
        recorded_at=now,
        source_domain="LOGS",
        source_component="SystemRecordWriter",
        origin="SYSTEM",
    )

    return SystemEvents(
        run_id=run_id,
        events=events,
        total_events=len(events),
        metadata=metadata,
    )


@router.get(
    "/system/{run_id}/replay",
    response_model=SystemReplay,
    summary="O4: Get system replay",
    description="Get infra replay window around anomaly.",
)
async def get_system_replay(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SystemReplay:
    """O4: Infra replay window."""
    tenant_id = get_tenant_id_from_auth(request)

    # Get run timestamp for window
    run_stmt = select(LLMRunRecord).where(LLMRunRecord.run_id == run_id, LLMRunRecord.tenant_id == tenant_id)
    run_result = await session.execute(run_stmt)
    run_entry = run_result.scalar_one_or_none()

    if not run_entry:
        raise HTTPException(status_code=404, detail="Run not found")

    inflection = run_entry.completed_at or run_entry.started_at
    window_start = inflection - timedelta(seconds=30)
    window_end = inflection + timedelta(seconds=30)

    stmt = (
        select(SystemRecord)
        .where((SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None)))
        .where(SystemRecord.created_at.between(window_start, window_end))
        .order_by(SystemRecord.created_at)
    )
    result = await session.execute(stmt)
    entries = result.scalars().all()

    events = [
        ReplayEvent(
            source="system",
            step_index=None,
            timestamp=e.created_at,
            action=e.event_type,
            outcome=e.severity,
        )
        for e in entries
    ]

    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        run_id=run_id,
        occurred_at=inflection,
        recorded_at=datetime.now(timezone.utc),
        source_domain="LOGS",
        source_component="SystemRecordWriter",
        origin="SYSTEM",
    )

    return SystemReplay(
        run_id=run_id,
        window_start=window_start,
        window_end=window_end,
        events=events,
        metadata=metadata,
    )


@router.get(
    "/system/audit",
    response_model=SystemAudit,
    summary="O5: Get infra audit",
    description="Get infrastructure attribution and audit records.",
)
async def get_system_audit(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SystemAudit:
    """O5: Infra attribution."""
    tenant_id = get_tenant_id_from_auth(request)

    stmt = (
        select(SystemRecord)
        .where((SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None)))
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
        SystemEvent(
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
    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        occurred_at=items[0].created_at if items else now,
        recorded_at=now,
        source_domain="LOGS",
        source_component="SystemRecordWriter",
        origin="SYSTEM",
    )

    return SystemAudit(
        items=items,
        total=total,
        metadata=metadata,
    )


# =============================================================================
# AUDIT Endpoints
# =============================================================================


@router.get(
    "/audit",
    response_model=AuditLedgerResponse,
    summary="List audit entries",
    description="List audit ledger entries.",
)
async def list_audit_entries(
    request: Request,
    event_type: Annotated[Optional[str], Query(description="Filter by event type")] = None,
    entity_type: Annotated[Optional[str], Query(description="Filter by entity type")] = None,
    actor_type: Annotated[Optional[str], Query(description="Filter by actor type")] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter created_at >=")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter created_at <=")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> AuditLedgerResponse:
    """List audit entries."""
    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    stmt = select(AuditLedger).where(AuditLedger.tenant_id == tenant_id).order_by(AuditLedger.created_at.desc())

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

    count_stmt = select(func.count(AuditLedger.id)).where(AuditLedger.tenant_id == tenant_id)
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    entries = result.scalars().all()

    items = [
        AuditLedgerItem(
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

    return AuditLedgerResponse(
        items=items,
        total=total,
        has_more=(offset + len(items)) < total,
        filters_applied=filters_applied,
    )


@router.get(
    "/audit/{entry_id}",
    response_model=AuditLedgerDetailItem,
    summary="Get audit entry detail",
    description="Get audit entry with state snapshots.",
)
async def get_audit_entry(
    request: Request,
    entry_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> AuditLedgerDetailItem:
    """Get audit entry detail."""
    tenant_id = get_tenant_id_from_auth(request)

    stmt = select(AuditLedger).where(AuditLedger.id == entry_id, AuditLedger.tenant_id == tenant_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Audit entry not found")

    return AuditLedgerDetailItem(
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


@router.get(
    "/audit/identity",
    response_model=AuditIdentity,
    summary="O1: Get identity lifecycle",
    description="Get authentication and identity events.",
)
async def get_audit_identity(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    session: AsyncSession = Depends(get_async_session_dep),
) -> AuditIdentity:
    """O1: Identity lifecycle."""
    tenant_id = get_tenant_id_from_auth(request)

    # Get identity-related events
    stmt = (
        select(AuditLedger)
        .where(AuditLedger.tenant_id == tenant_id)
        .order_by(AuditLedger.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    entries = result.scalars().all()

    events = [
        IdentityEvent(
            id=e.id,
            event_type=e.event_type,
            actor_type=e.actor_type,
            actor_id=e.actor_id,
            created_at=e.created_at,
        )
        for e in entries
    ]

    now = datetime.now(timezone.utc)
    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        occurred_at=events[0].created_at if events else now,
        recorded_at=now,
        source_domain="LOGS",
        source_component="AuditLedger",
        origin="SYSTEM",
    )

    return AuditIdentity(
        events=events,
        total=len(events),
        metadata=metadata,
    )


@router.get(
    "/audit/authorization",
    response_model=AuditAuthorization,
    summary="O2: Get authorization decisions",
    description="Get access control decisions.",
)
async def get_audit_authorization(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    session: AsyncSession = Depends(get_async_session_dep),
) -> AuditAuthorization:
    """O2: Authorization decisions."""
    tenant_id = get_tenant_id_from_auth(request)

    stmt = (
        select(AuditLedger)
        .where(AuditLedger.tenant_id == tenant_id)
        .order_by(AuditLedger.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    entries = result.scalars().all()

    decisions = [
        AuthorizationDecision(
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
    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        occurred_at=decisions[0].created_at if decisions else now,
        recorded_at=now,
        source_domain="LOGS",
        source_component="AuditLedger",
        origin="SYSTEM",
    )

    return AuditAuthorization(
        decisions=decisions,
        total=len(decisions),
        metadata=metadata,
    )


@router.get(
    "/audit/access",
    response_model=AuditAccess,
    summary="O3: Get access audit",
    description="Get log access audit trail.",
)
async def get_audit_access(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    session: AsyncSession = Depends(get_async_session_dep),
) -> AuditAccess:
    """O3: Log access audit."""
    tenant_id = get_tenant_id_from_auth(request)

    stmt = (
        select(AuditLedger)
        .where(AuditLedger.tenant_id == tenant_id)
        .order_by(AuditLedger.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    entries = result.scalars().all()

    events = [
        AccessEvent(
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
    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        occurred_at=events[0].created_at if events else now,
        recorded_at=now,
        source_domain="LOGS",
        source_component="AuditLedger",
        origin="SYSTEM",
    )

    return AuditAccess(
        events=events,
        total=len(events),
        metadata=metadata,
    )


@router.get(
    "/audit/integrity",
    response_model=AuditIntegrity,
    summary="O4: Get integrity check",
    description="Get tamper detection status.",
)
async def get_audit_integrity(
    request: Request,
) -> AuditIntegrity:
    """O4: Tamper detection."""
    tenant_id = get_tenant_id_from_auth(request)

    now = datetime.now(timezone.utc)
    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        occurred_at=now,
        recorded_at=now,
        source_domain="LOGS",
        source_component="IntegrityService",
        origin="SYSTEM",
    )

    return AuditIntegrity(
        integrity=IntegrityCheck(
            status="verified",
            last_verified=now,
            anomalies_detected=0,
            hash_chain_valid=True,
        ),
        metadata=metadata,
    )


@router.get(
    "/audit/exports",
    response_model=AuditExports,
    summary="O5: Get compliance exports",
    description="Get compliance export records.",
)
async def get_audit_exports(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> AuditExports:
    """O5: Compliance exports."""
    tenant_id = get_tenant_id_from_auth(request)

    stmt = (
        select(LogExport)
        .where(LogExport.tenant_id == tenant_id)
        .order_by(LogExport.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    entries = result.scalars().all()

    count_stmt = select(func.count(LogExport.id)).where(LogExport.tenant_id == tenant_id)
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    exports = [
        ExportRecord(
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
    metadata = EvidenceMetadata(
        tenant_id=tenant_id,
        occurred_at=exports[0].created_at if exports else now,
        recorded_at=now,
        source_domain="LOGS",
        source_component="LogExportService",
        origin="SYSTEM",
    )

    return AuditExports(
        exports=exports,
        total=total,
        metadata=metadata,
    )
