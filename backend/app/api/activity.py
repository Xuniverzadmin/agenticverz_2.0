# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified ACTIVITY domain facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: ACTIVITY Domain - One Facade Architecture
#
# GOVERNANCE NOTE:
# This is the ONE facade for ACTIVITY domain.
# All activity data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Unified Activity API (L2)

Customer-facing endpoints for viewing execution activity.
All requests are tenant-scoped via auth_context.

Endpoints:
- GET /api/v1/activity/runs              → O2 list with filters
- GET /api/v1/activity/runs/{run_id}     → O3 detail
- GET /api/v1/activity/runs/{run_id}/evidence → O4 context (preflight)
- GET /api/v1/activity/runs/{run_id}/proof    → O5 raw (preflight)
- GET /api/v1/activity/summary/by-status → COMP-O3 status summary
- GET /api/v1/activity/runs/by-dimension → LIVE-O5 dimension grouping
- GET /api/v1/activity/patterns          → SIG-O3 pattern detection
- GET /api/v1/activity/cost-analysis     → SIG-O4 cost anomalies
- GET /api/v1/activity/attention-queue   → SIG-O5 attention ranking
- GET /api/v1/activity/risk-signals      → Risk signal aggregates

Architecture:
- ONE facade for all ACTIVITY needs
- Uses v_runs_o2 view (pre-computed risk, latency, evidence)
- Tenant isolation via auth_context (not header)
- SDSR validates this same production API
"""

import os
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.services.activity import (
    PatternDetectionService,
    CostAnalysisService,
    AttentionRankingService,
)
from app.schemas.response import wrap_dict

# =============================================================================
# Environment Configuration
# =============================================================================

_CURRENT_ENVIRONMENT = os.getenv("AOS_ENVIRONMENT", "preflight")


def require_preflight() -> None:
    """Guard for preflight-only endpoints (O4, O5)."""
    if _CURRENT_ENVIRONMENT != "preflight":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "preflight_only",
                "message": "This endpoint is only available in preflight console.",
            },
        )


# =============================================================================
# Enums
# =============================================================================


class RunState(str, Enum):
    """Run lifecycle state."""

    LIVE = "LIVE"
    COMPLETED = "COMPLETED"


class RunStatus(str, Enum):
    """Run execution status."""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABORTED = "aborted"
    QUEUED = "queued"
    RETRY = "retry"


class RiskLevel(str, Enum):
    """Risk classification."""

    NORMAL = "NORMAL"
    NEAR_THRESHOLD = "NEAR_THRESHOLD"
    AT_RISK = "AT_RISK"
    VIOLATED = "VIOLATED"


class LatencyBucket(str, Enum):
    """Latency classification."""

    OK = "OK"
    SLOW = "SLOW"
    STALLED = "STALLED"


class EvidenceHealth(str, Enum):
    """Evidence capture health."""

    FLOWING = "FLOWING"
    DEGRADED = "DEGRADED"
    MISSING = "MISSING"


class IntegrityStatus(str, Enum):
    """Integrity verification status."""

    UNKNOWN = "UNKNOWN"
    VERIFIED = "VERIFIED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class RunSource(str, Enum):
    """Run initiator type."""

    AGENT = "agent"
    HUMAN = "human"
    SDK = "sdk"


class ProviderType(str, Enum):
    """LLM provider."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    INTERNAL = "internal"


class SortField(str, Enum):
    """Allowed sort fields."""

    STARTED_AT = "started_at"
    COMPLETED_AT = "completed_at"
    DURATION_MS = "duration_ms"
    RISK_LEVEL = "risk_level"


class SortOrder(str, Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


# =============================================================================
# Response Models
# =============================================================================


class RunSummary(BaseModel):
    """Run summary for list view (O2)."""

    # Identity & Scope
    run_id: str
    tenant_id: str | None
    project_id: str | None
    is_synthetic: bool
    source: str
    provider_type: str

    # Execution State
    state: str
    status: str
    started_at: datetime | None
    last_seen_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None

    # Risk & Health (pre-computed)
    risk_level: str
    latency_bucket: str
    evidence_health: str
    integrity_status: str

    # Impact Signals
    incident_count: int = 0
    policy_draft_count: int = 0
    policy_violation: bool = False

    # Cost / Volume
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None

    class Config:
        from_attributes = True


class Pagination(BaseModel):
    """Pagination metadata."""

    limit: int
    offset: int
    next_offset: int | None = None


class RunListResponse(BaseModel):
    """GET /runs response."""

    items: list[RunSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]
    pagination: Pagination


class RunDetailResponse(BaseModel):
    """GET /runs/{run_id} response (O3)."""

    run_id: str
    tenant_id: str | None
    project_id: str | None
    is_synthetic: bool
    source: str
    provider_type: str
    state: str
    status: str
    started_at: datetime | None
    last_seen_at: datetime | None
    completed_at: datetime | None
    duration_ms: float | None
    risk_level: str
    latency_bucket: str
    evidence_health: str
    integrity_status: str
    incident_count: int
    policy_draft_count: int
    policy_violation: bool
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
    # O3 additions
    goal: str | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True


# =============================================================================
# COMP-O3 Response Models
# =============================================================================


class StatusBucket(BaseModel):
    """A bucket in status summary."""

    status: str
    count: int
    percentage: float


class StatusSummaryResponse(BaseModel):
    """GET /summary/by-status response (COMP-O3)."""

    buckets: list[StatusBucket]
    total_runs: int
    generated_at: datetime


# =============================================================================
# LIVE-O5 Response Models
# =============================================================================


class DimensionValue(str, Enum):
    """Allowed dimension values for grouping."""

    PROVIDER_TYPE = "provider_type"
    SOURCE = "source"
    AGENT_ID = "agent_id"
    RISK_LEVEL = "risk_level"
    STATUS = "status"


class DimensionGroup(BaseModel):
    """A group in dimension breakdown."""

    value: str
    count: int
    percentage: float


class DimensionBreakdownResponse(BaseModel):
    """GET /runs/by-dimension response (LIVE-O5)."""

    dimension: str
    groups: list[DimensionGroup]
    total_runs: int
    state_filter: str | None
    generated_at: datetime


# =============================================================================
# SIG-O3 Response Models (Patterns)
# =============================================================================


class PatternMatchResponse(BaseModel):
    """A detected pattern."""

    pattern_type: str
    run_id: str
    confidence: float
    details: dict


class PatternDetectionResponse(BaseModel):
    """GET /patterns response (SIG-O3)."""

    patterns: list[PatternMatchResponse]
    window_start: datetime
    window_end: datetime
    runs_analyzed: int


# =============================================================================
# SIG-O4 Response Models (Cost Analysis)
# =============================================================================


class AgentCostResponse(BaseModel):
    """Cost analysis for a single agent."""

    agent_id: str
    current_cost_usd: float
    run_count: int
    baseline_avg_usd: float | None
    baseline_p95_usd: float | None
    z_score: float
    is_anomaly: bool


class CostAnalysisResponse(BaseModel):
    """GET /cost-analysis response (SIG-O4)."""

    agents: list[AgentCostResponse]
    total_anomalies: int
    total_cost_usd: float
    window_current: str
    window_baseline: str


# =============================================================================
# SIG-O5 Response Models (Attention Queue)
# =============================================================================


class AttentionItemResponse(BaseModel):
    """An item in the attention queue."""

    run_id: str
    attention_score: float
    reasons: list[str]
    state: str
    status: str
    started_at: datetime | None


class AttentionQueueResponse(BaseModel):
    """GET /attention-queue response (SIG-O5)."""

    queue: list[AttentionItemResponse]
    total_attention_items: int
    weights_version: str
    generated_at: datetime


# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/activity",
    tags=["activity"],
)


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
# GET /runs - O2 List
# =============================================================================


@router.get(
    "/runs",
    response_model=RunListResponse,
    summary="List runs (O2)",
    description="""
    Returns paginated list of runs matching filter criteria.
    Tenant isolation enforced via auth_context.

    Topic mapping:
    - Live Topic: `?state=LIVE`
    - Completed Topic: `?state=COMPLETED`
    - Risk Signals Topic: `?risk=true`
    """,
)
async def list_runs(
    request: Request,
    # Scope
    project_id: Annotated[str | None, Query(description="Project scope")] = None,
    # State filters
    state: Annotated[RunState | None, Query(description="Run lifecycle state")] = None,
    status: Annotated[list[str] | None, Query(description="Run status (multiple)")] = None,
    # Risk filters
    risk: Annotated[bool, Query(description="If true, returns runs with risk signals")] = False,
    risk_level: Annotated[list[RiskLevel] | None, Query(description="Filter by risk level")] = None,
    # Health filters
    latency_bucket: Annotated[list[LatencyBucket] | None, Query(description="Filter by latency")] = None,
    evidence_health: Annotated[list[EvidenceHealth] | None, Query(description="Filter by evidence health")] = None,
    integrity_status: Annotated[list[IntegrityStatus] | None, Query(description="Filter by integrity")] = None,
    # Source filters
    source: Annotated[list[RunSource] | None, Query(description="Filter by run source")] = None,
    provider_type: Annotated[list[ProviderType] | None, Query(description="Filter by LLM provider")] = None,
    # SDSR filter
    is_synthetic: Annotated[bool | None, Query(description="Filter by synthetic data flag")] = None,
    # Time filters
    started_after: Annotated[datetime | None, Query(description="Filter runs started after")] = None,
    started_before: Annotated[datetime | None, Query(description="Filter runs started before")] = None,
    completed_after: Annotated[datetime | None, Query(description="Filter runs completed after")] = None,
    completed_before: Annotated[datetime | None, Query(description="Filter runs completed before")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=200, description="Max runs to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of runs to skip")] = 0,
    # Sorting
    sort_by: Annotated[SortField, Query(description="Field to sort by")] = SortField.STARTED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.DESC,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> RunListResponse:
    """List runs with unified query filters. READ-ONLY from v_runs_o2 view."""

    # Tenant isolation from auth_context
    tenant_id = get_tenant_id_from_auth(request)

    # Build filters
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}
    where_clauses = ["tenant_id = :tenant_id"]
    params: dict[str, Any] = {"tenant_id": tenant_id}

    # Optional filters
    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id
        filters_applied["project_id"] = project_id

    if state:
        where_clauses.append("state = :state")
        params["state"] = state.value
        filters_applied["state"] = state.value

    if status:
        where_clauses.append("status = ANY(:status)")
        params["status"] = status
        filters_applied["status"] = status

    if risk:
        where_clauses.append("(risk_level != 'NORMAL' OR incident_count > 0 OR policy_violation = true)")
        filters_applied["risk"] = True

    if risk_level:
        values = [r.value for r in risk_level]
        where_clauses.append("risk_level = ANY(:risk_level)")
        params["risk_level"] = values
        filters_applied["risk_level"] = values

    if latency_bucket:
        values = [lb.value for lb in latency_bucket]
        where_clauses.append("latency_bucket = ANY(:latency_bucket)")
        params["latency_bucket"] = values
        filters_applied["latency_bucket"] = values

    if evidence_health:
        values = [e.value for e in evidence_health]
        where_clauses.append("evidence_health = ANY(:evidence_health)")
        params["evidence_health"] = values
        filters_applied["evidence_health"] = values

    if integrity_status:
        values = [i.value for i in integrity_status]
        where_clauses.append("integrity_status = ANY(:integrity_status)")
        params["integrity_status"] = values
        filters_applied["integrity_status"] = values

    if source:
        values = [s.value for s in source]
        where_clauses.append("source = ANY(:source)")
        params["source"] = values
        filters_applied["source"] = values

    if provider_type:
        values = [p.value for p in provider_type]
        where_clauses.append("provider_type = ANY(:provider_type)")
        params["provider_type"] = values
        filters_applied["provider_type"] = values

    if is_synthetic is not None:
        where_clauses.append("is_synthetic = :is_synthetic")
        params["is_synthetic"] = is_synthetic
        filters_applied["is_synthetic"] = is_synthetic

    if started_after:
        where_clauses.append("started_at >= :started_after")
        params["started_after"] = started_after
        filters_applied["started_after"] = started_after.isoformat()

    if started_before:
        where_clauses.append("started_at <= :started_before")
        params["started_before"] = started_before
        filters_applied["started_before"] = started_before.isoformat()

    if completed_after:
        where_clauses.append("completed_at >= :completed_after")
        params["completed_after"] = completed_after
        filters_applied["completed_after"] = completed_after.isoformat()

    if completed_before:
        where_clauses.append("completed_at <= :completed_before")
        params["completed_before"] = completed_before
        filters_applied["completed_before"] = completed_before.isoformat()

    where_sql = " AND ".join(where_clauses)
    sort_column = sort_by.value
    sort_dir = "DESC" if sort_order == SortOrder.DESC else "ASC"

    # Count query
    count_sql = f"SELECT COUNT(*) as total FROM v_runs_o2 WHERE {where_sql}"

    # Data query
    data_sql = f"""
        SELECT
            run_id, tenant_id, project_id, is_synthetic, source, provider_type,
            state, status, started_at, last_seen_at, completed_at, duration_ms,
            risk_level, latency_bucket, evidence_health, integrity_status,
            incident_count, policy_draft_count, policy_violation,
            input_tokens, output_tokens, estimated_cost_usd
        FROM v_runs_o2
        WHERE {where_sql}
        ORDER BY {sort_column} {sort_dir}
        LIMIT :limit OFFSET :offset
    """

    params["limit"] = limit
    params["offset"] = offset

    try:
        count_result = await session.execute(text(count_sql), params)
        total = count_result.scalar() or 0

        data_result = await session.execute(text(data_sql), params)
        rows = data_result.mappings().all()

        items = [
            RunSummary(
                run_id=row["run_id"],
                tenant_id=row["tenant_id"],
                project_id=row["project_id"],
                is_synthetic=row["is_synthetic"],
                source=row["source"],
                provider_type=row["provider_type"],
                state=row["state"],
                status=row["status"],
                started_at=row["started_at"],
                last_seen_at=row["last_seen_at"],
                completed_at=row["completed_at"],
                duration_ms=float(row["duration_ms"]) if row["duration_ms"] else None,
                risk_level=row["risk_level"],
                latency_bucket=row["latency_bucket"],
                evidence_health=row["evidence_health"],
                integrity_status=row["integrity_status"],
                incident_count=row["incident_count"] or 0,
                policy_draft_count=row["policy_draft_count"] or 0,
                policy_violation=row["policy_violation"] or False,
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                estimated_cost_usd=float(row["estimated_cost_usd"]) if row["estimated_cost_usd"] else None,
            )
            for row in rows
        ]

        has_more = offset + len(items) < total
        next_offset = offset + limit if has_more else None

        return RunListResponse(
            items=items,
            total=total,
            has_more=has_more,
            filters_applied=filters_applied,
            pagination=Pagination(limit=limit, offset=offset, next_offset=next_offset),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /runs/{run_id} - O3 Detail
# =============================================================================


@router.get(
    "/runs/{run_id}",
    response_model=RunDetailResponse,
    summary="Get run detail (O3)",
    description="Returns detailed information about a specific run.",
)
async def get_run_detail(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> RunDetailResponse:
    """Get run detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    sql = """
        SELECT *
        FROM v_runs_o2
        WHERE run_id = :run_id AND tenant_id = :tenant_id
    """

    result = await session.execute(text(sql), {"run_id": run_id, "tenant_id": tenant_id})
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunDetailResponse(
        run_id=row["run_id"],
        tenant_id=row["tenant_id"],
        project_id=row["project_id"],
        is_synthetic=row["is_synthetic"],
        source=row["source"],
        provider_type=row["provider_type"],
        state=row["state"],
        status=row["status"],
        started_at=row["started_at"],
        last_seen_at=row["last_seen_at"],
        completed_at=row["completed_at"],
        duration_ms=float(row["duration_ms"]) if row["duration_ms"] else None,
        risk_level=row["risk_level"],
        latency_bucket=row["latency_bucket"],
        evidence_health=row["evidence_health"],
        integrity_status=row["integrity_status"],
        incident_count=row["incident_count"] or 0,
        policy_draft_count=row["policy_draft_count"] or 0,
        policy_violation=row["policy_violation"] or False,
        input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"],
        estimated_cost_usd=float(row["estimated_cost_usd"]) if row["estimated_cost_usd"] else None,
        goal=row.get("goal"),
        error_message=row.get("error_message"),
    )


# =============================================================================
# GET /runs/{run_id}/evidence - O4 Context (Preflight Only)
# =============================================================================


@router.get(
    "/runs/{run_id}/evidence",
    summary="Get run evidence (O4)",
    description="Returns cross-domain impact and evidence context. Preflight only.",
)
async def get_run_evidence(
    request: Request,
    run_id: str,
) -> dict[str, Any]:
    """Get run evidence (O4). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth

    return wrap_dict({
        "run_id": run_id,
        "incidents_caused": [],
        "policies_triggered": [],
        "decisions_made": [],
        "traces_linked": [],
    })


# =============================================================================
# GET /runs/{run_id}/proof - O5 Raw (Preflight Only)
# =============================================================================


@router.get(
    "/runs/{run_id}/proof",
    summary="Get run proof (O5)",
    description="Returns raw traces, logs, and integrity proof. Preflight only.",
)
async def get_run_proof(
    request: Request,
    run_id: str,
    include_payloads: bool = False,
) -> dict[str, Any]:
    """Get run proof (O5). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth
    _ = include_payloads  # Reserved for future use

    return wrap_dict({
        "run_id": run_id,
        "integrity": {
            "root_hash": None,
            "verification_status": "UNKNOWN",
            "chain_length": 0,
        },
        "aos_traces": [],
        "aos_trace_steps": [],
        "raw_logs": [],
    })


# =============================================================================
# GET /summary/by-status - COMP-O3 Status Summary
# =============================================================================


@router.get(
    "/summary/by-status",
    response_model=StatusSummaryResponse,
    summary="Summary by status (COMP-O3)",
    description="""
    Returns run counts grouped by status for the tenant.
    Provides a high-level overview of execution distribution.
    """,
)
async def get_summary_by_status(
    request: Request,
    state: Annotated[RunState | None, Query(description="Filter by run state")] = None,
    session: AsyncSession = Depends(get_async_session_dep),
) -> StatusSummaryResponse:
    """Get run summary by status (COMP-O3). READ-ONLY from v_runs_o2."""

    tenant_id = get_tenant_id_from_auth(request)

    # Build query
    where_clause = "tenant_id = :tenant_id"
    params: dict[str, Any] = {"tenant_id": tenant_id}

    if state:
        where_clause += " AND state = :state"
        params["state"] = state.value

    sql = text(f"""
        SELECT
            status,
            COUNT(*) as count
        FROM v_runs_o2
        WHERE {where_clause}
        GROUP BY status
        ORDER BY count DESC
    """)

    result = await session.execute(sql, params)
    rows = result.mappings().all()

    # Calculate total and percentages
    total = sum(row["count"] for row in rows)

    buckets = [
        StatusBucket(
            status=row["status"],
            count=row["count"],
            percentage=round((row["count"] / total * 100) if total > 0 else 0, 2),
        )
        for row in rows
    ]

    return StatusSummaryResponse(
        buckets=buckets,
        total_runs=total,
        generated_at=datetime.utcnow(),
    )


# =============================================================================
# Internal Helper: Dimension Breakdown (Shared Logic)
# =============================================================================


async def _get_runs_by_dimension_internal(
    session: AsyncSession,
    tenant_id: str,
    dim: DimensionValue,
    state: RunState,
    limit: int = 20,
) -> DimensionBreakdownResponse:
    """
    Internal helper for dimension breakdown with HARDCODED state binding.

    This function is called by topic-scoped endpoints only.
    State is injected by the endpoint, never from caller.

    Policy: TOPIC-SCOPED-ENDPOINT-001
    """
    dimension_col = dim.value
    where_clause = "tenant_id = :tenant_id AND state = :state"
    params: dict[str, Any] = {
        "tenant_id": tenant_id,
        "state": state.value,
        "limit": limit,
    }

    sql = text(f"""
        SELECT
            COALESCE({dimension_col}::text, 'unknown') as value,
            COUNT(*) as count
        FROM v_runs_o2
        WHERE {where_clause}
        GROUP BY {dimension_col}
        ORDER BY count DESC
        LIMIT :limit
    """)

    result = await session.execute(sql, params)
    rows = result.mappings().all()

    total = sum(row["count"] for row in rows)

    groups = [
        DimensionGroup(
            value=row["value"],
            count=row["count"],
            percentage=round((row["count"] / total * 100) if total > 0 else 0, 2),
        )
        for row in rows
    ]

    return DimensionBreakdownResponse(
        dimension=dimension_col,
        groups=groups,
        total_runs=total,
        state_filter=state.value,
        generated_at=datetime.utcnow(),
    )


# =============================================================================
# GET /runs/live/by-dimension - LIVE Topic Distribution (LIVE-O5)
# =============================================================================


@router.get(
    "/runs/live/by-dimension",
    response_model=DimensionBreakdownResponse,
    summary="Live runs by dimension (LIVE-O5)",
    description="""
    Returns LIVE run counts grouped by a specified dimension.

    **Topic-Scoped Endpoint** - State filter is IMPLICIT (hardcoded to LIVE).
    This endpoint ONLY returns runs with state=LIVE.

    Policy: TOPIC-SCOPED-ENDPOINT-001
    Capability: activity.runs_by_dimension
    """,
)
async def get_live_runs_by_dimension(
    request: Request,
    dim: Annotated[DimensionValue, Query(description="Dimension to group by")],
    limit: Annotated[int, Query(ge=1, le=100, description="Max groups to return")] = 20,
    session: AsyncSession = Depends(get_async_session_dep),
) -> DimensionBreakdownResponse:
    """Get LIVE runs grouped by dimension. State=LIVE is hardcoded."""
    tenant_id = get_tenant_id_from_auth(request)
    return await _get_runs_by_dimension_internal(
        session=session,
        tenant_id=tenant_id,
        dim=dim,
        state=RunState.LIVE,  # HARDCODED - cannot be overridden
        limit=limit,
    )


# =============================================================================
# GET /runs/completed/by-dimension - COMPLETED Topic Distribution
# =============================================================================


@router.get(
    "/runs/completed/by-dimension",
    response_model=DimensionBreakdownResponse,
    summary="Completed runs by dimension",
    description="""
    Returns COMPLETED run counts grouped by a specified dimension.

    **Topic-Scoped Endpoint** - State filter is IMPLICIT (hardcoded to COMPLETED).
    This endpoint ONLY returns runs with state=COMPLETED.

    Policy: TOPIC-SCOPED-ENDPOINT-001
    Capability: activity.runs_by_dimension
    """,
)
async def get_completed_runs_by_dimension(
    request: Request,
    dim: Annotated[DimensionValue, Query(description="Dimension to group by")],
    limit: Annotated[int, Query(ge=1, le=100, description="Max groups to return")] = 20,
    session: AsyncSession = Depends(get_async_session_dep),
) -> DimensionBreakdownResponse:
    """Get COMPLETED runs grouped by dimension. State=COMPLETED is hardcoded."""
    tenant_id = get_tenant_id_from_auth(request)
    return await _get_runs_by_dimension_internal(
        session=session,
        tenant_id=tenant_id,
        dim=dim,
        state=RunState.COMPLETED,  # HARDCODED - cannot be overridden
        limit=limit,
    )


# =============================================================================
# GET /runs/by-dimension - INTERNAL/ADMIN ONLY (Deprecated for Panels)
# =============================================================================


@router.get(
    "/runs/by-dimension",
    response_model=DimensionBreakdownResponse,
    summary="[INTERNAL] Runs by dimension (admin only)",
    description="""
    **INTERNAL/ADMIN ENDPOINT - DO NOT USE FOR PANELS**

    This endpoint accepts an optional state filter and is NOT topic-scoped.
    For panel use, call the topic-scoped endpoints instead:
    - LIVE panels: /runs/live/by-dimension
    - COMPLETED panels: /runs/completed/by-dimension

    Policy: TOPIC-SCOPED-ENDPOINT-001 - Generic endpoints must not be panel-bound.
    """,
    deprecated=True,
)
async def get_runs_by_dimension(
    request: Request,
    dim: Annotated[DimensionValue, Query(description="Dimension to group by")],
    state: Annotated[RunState | None, Query(description="Filter by run state")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Max groups to return")] = 20,
    session: AsyncSession = Depends(get_async_session_dep),
) -> DimensionBreakdownResponse:
    """[INTERNAL] Get runs grouped by dimension with optional state. NOT FOR PANELS."""
    tenant_id = get_tenant_id_from_auth(request)

    dimension_col = dim.value
    where_clause = "tenant_id = :tenant_id"
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}

    if state:
        where_clause += " AND state = :state"
        params["state"] = state.value

    sql = text(f"""
        SELECT
            COALESCE({dimension_col}::text, 'unknown') as value,
            COUNT(*) as count
        FROM v_runs_o2
        WHERE {where_clause}
        GROUP BY {dimension_col}
        ORDER BY count DESC
        LIMIT :limit
    """)

    result = await session.execute(sql, params)
    rows = result.mappings().all()

    total = sum(row["count"] for row in rows)

    groups = [
        DimensionGroup(
            value=row["value"],
            count=row["count"],
            percentage=round((row["count"] / total * 100) if total > 0 else 0, 2),
        )
        for row in rows
    ]

    return DimensionBreakdownResponse(
        dimension=dimension_col,
        groups=groups,
        total_runs=total,
        state_filter=state.value if state else None,
        generated_at=datetime.utcnow(),
    )


# =============================================================================
# GET /patterns - SIG-O3 Pattern Detection
# =============================================================================


@router.get(
    "/patterns",
    response_model=PatternDetectionResponse,
    summary="Detect patterns (SIG-O3)",
    description="""
    Detects instability patterns in trace steps:
    - retry_loop: Repeated retries (>3 in same run)
    - step_oscillation: Same skill called non-consecutively
    - tool_call_loop: Repeated skill within sliding window
    - timeout_cascade: Multiple slow steps
    """,
)
async def get_patterns(
    request: Request,
    window_hours: Annotated[int, Query(ge=1, le=168, description="Hours to look back")] = 24,
    limit: Annotated[int, Query(ge=1, le=50, description="Max patterns per type")] = 10,
    session: AsyncSession = Depends(get_async_session_dep),
) -> PatternDetectionResponse:
    """Detect instability patterns (SIG-O3). READ-ONLY from aos_traces/aos_trace_steps."""

    tenant_id = get_tenant_id_from_auth(request)

    service = PatternDetectionService(session)
    result = await service.detect_patterns(
        tenant_id=tenant_id,
        window_hours=window_hours,
        limit=limit,
    )

    return PatternDetectionResponse(
        patterns=[
            PatternMatchResponse(
                pattern_type=p.pattern_type,
                run_id=p.run_id,
                confidence=p.confidence,
                details=p.details,
            )
            for p in result.patterns
        ],
        window_start=result.window_start,
        window_end=result.window_end,
        runs_analyzed=result.runs_analyzed,
    )


# =============================================================================
# GET /cost-analysis - SIG-O4 Cost Anomalies
# =============================================================================


@router.get(
    "/cost-analysis",
    response_model=CostAnalysisResponse,
    summary="Cost analysis (SIG-O4)",
    description="""
    Analyzes cost anomalies via Z-score comparison against baseline.
    Detects agents with unusual cost patterns.
    """,
)
async def get_cost_analysis(
    request: Request,
    baseline_days: Annotated[int, Query(ge=1, le=30, description="Days for baseline")] = 7,
    anomaly_threshold: Annotated[float, Query(ge=1.0, le=5.0, description="Z-score threshold")] = 2.0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> CostAnalysisResponse:
    """Analyze cost anomalies (SIG-O4). READ-ONLY from runs table."""

    tenant_id = get_tenant_id_from_auth(request)

    service = CostAnalysisService(session)
    result = await service.analyze_costs(
        tenant_id=tenant_id,
        baseline_days=baseline_days,
        anomaly_threshold=anomaly_threshold,
    )

    return CostAnalysisResponse(
        agents=[
            AgentCostResponse(
                agent_id=a.agent_id,
                current_cost_usd=a.current_cost_usd,
                run_count=a.run_count,
                baseline_avg_usd=a.baseline_avg_usd,
                baseline_p95_usd=a.baseline_p95_usd,
                z_score=a.z_score,
                is_anomaly=a.is_anomaly,
            )
            for a in result.agents
        ],
        total_anomalies=result.total_anomalies,
        total_cost_usd=result.total_cost_usd,
        window_current=result.window_current,
        window_baseline=result.window_baseline,
    )


# =============================================================================
# GET /attention-queue - SIG-O5 Attention Ranking
# =============================================================================


@router.get(
    "/attention-queue",
    response_model=AttentionQueueResponse,
    summary="Attention queue (SIG-O5)",
    description="""
    Returns runs ranked by composite attention score.
    Combines risk, impact, latency, recency, and evidence signals.

    Weight distribution (FROZEN):
    - risk: 35%
    - impact: 25%
    - latency: 15%
    - recency: 15%
    - evidence: 10%
    """,
)
async def get_attention_queue(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 20,
    session: AsyncSession = Depends(get_async_session_dep),
) -> AttentionQueueResponse:
    """Get attention queue (SIG-O5). READ-ONLY from v_runs_o2."""

    tenant_id = get_tenant_id_from_auth(request)

    service = AttentionRankingService(session)
    result = await service.get_attention_queue(
        tenant_id=tenant_id,
        limit=limit,
    )

    return AttentionQueueResponse(
        queue=[
            AttentionItemResponse(
                run_id=item.run_id,
                attention_score=item.attention_score,
                reasons=item.reasons,
                state=item.state,
                status=item.status,
                started_at=item.started_at,
            )
            for item in result.queue
        ],
        total_attention_items=result.total_attention_items,
        weights_version=result.weights_version,
        generated_at=result.generated_at,
    )


# =============================================================================
# GET /risk-signals - Risk Signal Aggregates
# =============================================================================
# PURPOSE: Returns aggregated risk counts for Customer Console panels
# CAPABILITY: activity.risk_signals
# SIGNALS: at_risk_count, cost_risk_count, time_risk_count, token_risk_count
# =============================================================================


class RiskSignalsResponse(BaseModel):
    """GET /risk-signals response."""

    at_risk_count: int
    violated_count: int
    at_risk_level_count: int
    near_threshold_count: int
    total_at_risk: int
    generated_at: datetime


@router.get(
    "/risk-signals",
    response_model=RiskSignalsResponse,
    summary="Risk signal aggregates",
    description="""
    Returns aggregated counts of runs at various risk levels.

    Risk levels:
    - NORMAL: No risk signals
    - NEAR_THRESHOLD: Approaching limits (warning)
    - AT_RISK: Threshold breach imminent
    - VIOLATED: Threshold exceeded

    Capability: activity.risk_signals
    Consumers: Overview panels, Activity summary panels
    """,
)
async def get_risk_signals(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> RiskSignalsResponse:
    """
    Returns aggregated risk signal counts.

    Supports: activity.risk_signals capability
    Consumers: Overview panels, Activity summary panels

    Only considers:
    - Live runs (state = 'LIVE')
    - Completed runs in the last 24 hours
    """
    tenant_id = get_tenant_id_from_auth(request)

    sql = text("""
        SELECT
            COUNT(*) FILTER (WHERE risk_level IN ('NEAR_THRESHOLD', 'AT_RISK', 'VIOLATED')) as at_risk_count,
            COUNT(*) FILTER (WHERE risk_level = 'VIOLATED') as violated_count,
            COUNT(*) FILTER (WHERE risk_level = 'AT_RISK') as at_risk_level_count,
            COUNT(*) FILTER (WHERE risk_level = 'NEAR_THRESHOLD') as near_threshold_count,
            COUNT(*) FILTER (WHERE risk_level != 'NORMAL') as total_at_risk
        FROM v_runs_o2
        WHERE tenant_id = :tenant_id
          AND (state = 'LIVE' OR completed_at >= NOW() - INTERVAL '24 hours')
    """)

    result = await session.execute(sql, {"tenant_id": tenant_id})
    row = result.mappings().first()

    return RiskSignalsResponse(
        at_risk_count=row["at_risk_count"] or 0 if row else 0,
        violated_count=row["violated_count"] or 0 if row else 0,
        at_risk_level_count=row["at_risk_level_count"] or 0 if row else 0,
        near_threshold_count=row["near_threshold_count"] or 0 if row else 0,
        total_at_risk=row["total_at_risk"] or 0 if row else 0,
        generated_at=datetime.utcnow(),
    )
