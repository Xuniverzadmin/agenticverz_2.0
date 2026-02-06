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

from datetime import datetime, timedelta
from typing import Annotated, Any, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from app.auth.gateway_middleware import get_auth_context
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)

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
    session = Depends(get_session_dep),
) -> LLMRunRecordsResponse:
    """List LLM run records. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "list_llm_run_records",
                "run_id": run_id,
                "provider": provider,
                "model": model,
                "execution_status": execution_status,
                "is_synthetic": is_synthetic,
                "created_after": created_after,
                "created_before": created_before,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    items = [
        LLMRunRecordItem(
            id=item.id,
            run_id=item.run_id,
            trace_id=item.trace_id,
            provider=item.provider,
            model=item.model,
            input_tokens=item.input_tokens,
            output_tokens=item.output_tokens,
            cost_cents=item.cost_cents,
            execution_status=item.execution_status,
            started_at=item.started_at,
            completed_at=item.completed_at,
            source=item.source,
            is_synthetic=item.is_synthetic,
            created_at=item.created_at,
        )
        for item in result.items
    ]

    return LLMRunRecordsResponse(
        items=items,
        total=result.total,
        has_more=result.has_more,
        filters_applied=result.filters_applied,
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
    session = Depends(get_session_dep),
) -> LLMRunEnvelope:
    """O1: Canonical immutable run record. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_llm_run_envelope", "run_id": run_id},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    if not result:
        raise HTTPException(status_code=404, detail="Run not found")

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        run_id=result.metadata.run_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        trace_id=result.metadata.trace_id,
        source_domain="LOGS",
        source_component=result.metadata.source_component,
        origin="SYSTEM",
    )

    return LLMRunEnvelope(
        id=result.id,
        run_id=result.run_id,
        trace_id=result.trace_id,
        provider=result.provider,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_cents=result.cost_cents,
        execution_status=result.execution_status,
        started_at=result.started_at,
        completed_at=result.completed_at,
        source=result.source,
        is_synthetic=result.is_synthetic,
        created_at=result.created_at,
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
    session = Depends(get_session_dep),
) -> LLMRunTrace:
    """O2: Step-by-step execution trace. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_llm_run_trace", "run_id": run_id},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    if not result:
        raise HTTPException(status_code=404, detail="Trace not found")

    steps = [
        TraceStep(
            step_index=step.step_index,
            timestamp=step.timestamp,
            skill_name=step.skill_name,
            status=step.status,
            outcome_category=step.outcome_category,
            cost_cents=step.cost_cents,
            duration_ms=step.duration_ms,
        )
        for step in result.steps
    ]

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        run_id=result.metadata.run_id,
        trace_id=result.metadata.trace_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain="LOGS",
        source_component=result.metadata.source_component,
        origin="SYSTEM",
    )

    return LLMRunTrace(
        run_id=result.run_id,
        trace_id=result.trace_id,
        steps=steps,
        total_steps=result.total_steps,
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
    session = Depends(get_session_dep),
) -> LLMRunGovernance:
    """O3: Policy interaction trace. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_llm_run_governance", "run_id": run_id},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    events = [
        GovernanceEvent(
            timestamp=event.timestamp,
            event_type=event.event_type,
            policy_id=event.policy_id,
            rule_id=event.rule_id,
            decision=event.decision,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
        )
        for event in result.events
    ]

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        run_id=result.metadata.run_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain="LOGS",
        source_component=result.metadata.source_component,
        origin="SYSTEM",
    )

    return LLMRunGovernance(
        run_id=result.run_id,
        events=events,
        total_events=result.total_events,
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
    session = Depends(get_session_dep),
) -> LLMRunReplay:
    """O4: 60-second replay window. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_llm_run_replay", "run_id": run_id},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    if not result:
        raise HTTPException(status_code=404, detail="Run not found")

    events = [
        ReplayEvent(
            source=event.source,
            step_index=event.step_index,
            timestamp=event.timestamp,
            action=event.action,
            outcome=event.outcome,
        )
        for event in result.events
    ]

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        run_id=result.metadata.run_id,
        trace_id=result.metadata.trace_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain="LOGS",
        source_component=result.metadata.source_component,
        origin="SYSTEM",
    )

    return LLMRunReplay(
        run_id=result.run_id,
        inflection_timestamp=result.inflection_timestamp,
        window_start=result.window_start,
        window_end=result.window_end,
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
    session = Depends(get_session_dep),
) -> LLMRunExport:
    """O5: Export information. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_llm_run_export", "run_id": run_id},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    if not result:
        raise HTTPException(status_code=404, detail="Run not found")

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        run_id=result.metadata.run_id,
        trace_id=result.metadata.trace_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain="LOGS",
        source_component=result.metadata.source_component,
        origin="SYSTEM",
    )

    return LLMRunExport(
        run_id=result.run_id,
        available_formats=result.available_formats,
        checksum=result.checksum,
        compliance_tags=result.compliance_tags,
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
    session = Depends(get_session_dep),
) -> SystemRecordsResponse:
    """List system records. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "list_system_records",
                "component": component,
                "event_type": event_type,
                "severity": severity,
                "created_after": created_after,
                "created_before": created_before,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    items = [
        SystemRecordItem(
            id=item.id,
            tenant_id=item.tenant_id,
            component=item.component,
            event_type=item.event_type,
            severity=item.severity,
            summary=item.summary,
            caused_by=item.caused_by,
            correlation_id=item.correlation_id,
            created_at=item.created_at,
        )
        for item in result.items
    ]

    return SystemRecordsResponse(
        items=items,
        total=result.total,
        has_more=result.has_more,
        filters_applied=result.filters_applied,
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
    session = Depends(get_session_dep),
) -> SystemSnapshot:
    """O1: Environment baseline snapshot. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_system_snapshot", "run_id": run_id},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        run_id=result.metadata.run_id,
        correlation_id=result.metadata.correlation_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain=result.metadata.source_domain,
        source_component=result.metadata.source_component,
        origin=result.metadata.origin,
    )

    return SystemSnapshot(
        run_id=result.run_id,
        component=result.component,
        event_type=result.event_type,
        severity=result.severity,
        summary=result.summary,
        details=result.details,
        created_at=result.created_at,
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
    """O2: Telemetry stub - producer not implemented. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=None,  # type: ignore
            tenant_id=tenant_id,
            params={"method": "get_system_telemetry", "run_id": run_id},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data
    return TelemetryStub(run_id=result.run_id)


@router.get(
    "/system/{run_id}/events",
    response_model=SystemEvents,
    summary="O3: Get infra events",
    description="Get infrastructure events affecting the run.",
)
async def get_system_events(
    request: Request,
    run_id: str,
    session = Depends(get_session_dep),
) -> SystemEvents:
    """O3: Infra events affecting run. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_system_events", "run_id": run_id},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

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
        for e in result.events
    ]

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        run_id=result.metadata.run_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain=result.metadata.source_domain,
        source_component=result.metadata.source_component,
        origin=result.metadata.origin,
    )

    return SystemEvents(
        run_id=result.run_id,
        events=events,
        total_events=result.total_events,
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
    session = Depends(get_session_dep),
) -> SystemReplay:
    """O4: Infra replay window. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_system_replay", "run_id": run_id},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    if not result:
        raise HTTPException(status_code=404, detail="Run not found")

    events = [
        ReplayEvent(
            source=e.source,
            step_index=e.step_index,
            timestamp=e.timestamp,
            action=e.action,
            outcome=e.outcome,
        )
        for e in result.events
    ]

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        run_id=result.metadata.run_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain=result.metadata.source_domain,
        source_component=result.metadata.source_component,
        origin=result.metadata.origin,
    )

    return SystemReplay(
        run_id=result.run_id,
        window_start=result.window_start,
        window_end=result.window_end,
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
    session = Depends(get_session_dep),
) -> SystemAudit:
    """O5: Infra attribution. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_system_audit", "limit": limit, "offset": offset},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

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
        for e in result.items
    ]

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain=result.metadata.source_domain,
        source_component=result.metadata.source_component,
        origin=result.metadata.origin,
    )

    return SystemAudit(
        items=items,
        total=result.total,
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
    session = Depends(get_session_dep),
) -> AuditLedgerResponse:
    """List audit entries. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "list_audit_entries",
                "event_type": event_type,
                "entity_type": entity_type,
                "actor_type": actor_type,
                "created_after": created_after,
                "created_before": created_before,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    items = [
        AuditLedgerItem(
            id=item.id,
            event_type=item.event_type,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            actor_type=item.actor_type,
            actor_id=item.actor_id,
            action_reason=item.action_reason,
            created_at=item.created_at,
        )
        for item in result.items
    ]

    return AuditLedgerResponse(
        items=items,
        total=result.total,
        has_more=result.has_more,
        filters_applied=result.filters_applied,
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
    session = Depends(get_session_dep),
) -> AuditLedgerDetailItem:
    """Get audit entry detail. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_audit_entry", "entry_id": entry_id},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    if not result:
        raise HTTPException(status_code=404, detail="Audit entry not found")

    return AuditLedgerDetailItem(
        id=result.id,
        event_type=result.event_type,
        entity_type=result.entity_type,
        entity_id=result.entity_id,
        actor_type=result.actor_type,
        actor_id=result.actor_id,
        action_reason=result.action_reason,
        created_at=result.created_at,
        before_state=result.before_state,
        after_state=result.after_state,
        correlation_id=result.correlation_id,
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
    session = Depends(get_session_dep),
) -> AuditIdentity:
    """O1: Identity lifecycle. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_audit_identity", "limit": limit},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    events = [
        IdentityEvent(
            id=e.id,
            event_type=e.event_type,
            actor_type=e.actor_type,
            actor_id=e.actor_id,
            created_at=e.created_at,
        )
        for e in result.events
    ]

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain=result.metadata.source_domain,
        source_component=result.metadata.source_component,
        origin=result.metadata.origin,
    )

    return AuditIdentity(
        events=events,
        total=result.total,
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
    session = Depends(get_session_dep),
) -> AuditAuthorization:
    """O2: Authorization decisions. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_audit_authorization", "limit": limit},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    decisions = [
        AuthorizationDecision(
            id=d.id,
            event_type=d.event_type,
            entity_type=d.entity_type,
            entity_id=d.entity_id,
            actor_type=d.actor_type,
            decision=d.decision,
            created_at=d.created_at,
        )
        for d in result.decisions
    ]

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain=result.metadata.source_domain,
        source_component=result.metadata.source_component,
        origin=result.metadata.origin,
    )

    return AuditAuthorization(
        decisions=decisions,
        total=result.total,
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
    session = Depends(get_session_dep),
) -> AuditAccess:
    """O3: Log access audit. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_audit_access", "limit": limit},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

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
        for e in result.events
    ]

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain=result.metadata.source_domain,
        source_component=result.metadata.source_component,
        origin=result.metadata.origin,
    )

    return AuditAccess(
        events=events,
        total=result.total,
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
    """O4: Tamper detection. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=None,  # type: ignore
            tenant_id=tenant_id,
            params={"method": "get_audit_integrity"},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain=result.metadata.source_domain,
        source_component=result.metadata.source_component,
        origin=result.metadata.origin,
    )

    return AuditIntegrity(
        integrity=IntegrityCheck(
            status=result.integrity.status,
            last_verified=result.integrity.last_verified,
            anomalies_detected=result.integrity.anomalies_detected,
            hash_chain_valid=result.integrity.hash_chain_valid,
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
    session = Depends(get_session_dep),
) -> AuditExports:
    """O5: Compliance exports. READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "logs.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_audit_exports", "limit": limit, "offset": offset},
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

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
        for e in result.exports
    ]

    metadata = EvidenceMetadata(
        tenant_id=result.metadata.tenant_id,
        occurred_at=result.metadata.occurred_at,
        recorded_at=result.metadata.recorded_at,
        source_domain=result.metadata.source_domain,
        source_component=result.metadata.source_component,
        origin=result.metadata.origin,
    )

    return AuditExports(
        exports=exports,
        total=result.total,
        metadata=metadata,
    )
