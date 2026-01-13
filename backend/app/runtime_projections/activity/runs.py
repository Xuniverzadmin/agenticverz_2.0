# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: READ-ONLY runs list endpoint for Aurora O2 panels
# Callers: Frontend via slot binding
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: PIN-411

"""
GET /runs - Aurora O2 Runtime Projection

READ-ONLY endpoint. All data pre-computed upstream, stored in Neon.

Non-Negotiable Constraints:
- NO risk computation in queries
- NO joins that derive meaning
- NO JSON aggregation in hot paths
- Everything returned already exists in Neon
- Pagination is mandatory
- Every filter is optional and orthogonal

Invariants (PIN-411):
- INV-RISK-001: Risk computed upstream, not at query time
- INV-RISK-004: /runs is read-only for derived columns
"""

import os
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session_dep
from app.auth.gateway_middleware import get_auth_context


# =============================================================================
# Environment Configuration
# =============================================================================

_CURRENT_ENVIRONMENT = os.getenv("AOS_ENVIRONMENT", "preflight")


def require_preflight() -> None:
    """
    Guard function for preflight-only endpoints.

    Raises HTTPException 403 if not in preflight environment.

    INVARIANT (PIN-411):
    - O4 and O5 endpoints are preflight-only
    - Production console users cannot access evidence or proof data
    """
    if _CURRENT_ENVIRONMENT != "preflight":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "preflight_only",
                "message": "This endpoint is only available in preflight console.",
            },
        )


# =============================================================================
# Enums (match O2 schema exactly)
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
# Response Models (match OpenAPI spec exactly)
# =============================================================================


class RunSummary(BaseModel):
    """O2 table row - one run summary for list view."""

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

    # Risk & Health (Derived, pre-computed)
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


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    details: dict[str, Any] | None = None


# =============================================================================
# Router
# =============================================================================


activity_runs_router = APIRouter(
    prefix="/activity",
    tags=["runtime-projections", "activity", "o2-list"],
)


# =============================================================================
# GET /runs - O2 List Endpoint
# =============================================================================


@activity_runs_router.get(
    "/runs",
    response_model=RunListResponse,
    summary="List runs with unified query filters",
    description="""
    Returns paginated list of runs matching filter criteria.
    This is the canonical O2 endpoint for all Activity domain topics.

    Topic mapping:
    - Live Topic: `?state=LIVE`
    - Completed Topic: `?state=COMPLETED`
    - Risk Signals Topic: `?risk=true`

    READ-ONLY: All data pre-computed upstream. No query-time computation.

    SECURITY INVARIANT (PIN-411):
    - tenant_id is derived from auth_context, NEVER from query params
    - Supplying tenant_id in query params is rejected with 400
    """,
)
async def list_runs(
    request: Request,
    # Optional scope
    project_id: Annotated[str | None, Query(description="Project scope")] = None,
    # State filters
    state: Annotated[RunState | None, Query(description="Run lifecycle state")] = None,
    status: Annotated[list[str] | None, Query(description="Run status (can specify multiple)")] = None,
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
    """
    List runs with unified query filters.

    READ-ONLY: Pure SELECT from v_runs_o2 view.
    NO risk computation. NO joins. All filters map 1:1 to stored columns.

    SECURITY INVARIANT (PIN-411):
    - tenant_id derived from auth_context
    - Frontend MUST NOT supply tenant_id
    """

    # ==========================================================================
    # SECURITY GUARDRAIL: Reject tenant_id from query params (PIN-411)
    # ==========================================================================
    if "tenant_id" in request.query_params:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "tenant_id_rejected",
                "message": "tenant_id must not be provided by client. It is derived from auth_context.",
            },
        )

    # ==========================================================================
    # Get tenant_id from auth_context (MANDATORY)
    # ==========================================================================
    auth_context = get_auth_context(request)

    if auth_context is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "not_authenticated",
                "message": "Authentication required.",
            },
        )

    # Extract tenant_id based on context type
    # HumanAuthContext and MachineCapabilityContext have tenant_id
    # FounderAuthContext does NOT (founders access cross-tenant)
    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    # Founders cannot access tenant-scoped data via this endpoint
    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_required",
                "message": "This endpoint requires tenant context. Founders must use admin APIs.",
            },
        )

    # Build filters applied dict for response echo
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    # Base WHERE clause - tenant isolation is mandatory
    where_clauses = ["tenant_id = :tenant_id"]
    params: dict[str, Any] = {"tenant_id": tenant_id}

    # Optional project scope
    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id
        filters_applied["project_id"] = project_id

    # State filter
    if state:
        where_clauses.append("state = :state")
        params["state"] = state.value
        filters_applied["state"] = state.value

    # Status filter (multiple values)
    if status:
        where_clauses.append("status = ANY(:status)")
        params["status"] = status
        filters_applied["status"] = status

    # Risk topic filter (special case: risk_level != NORMAL OR impact signals)
    if risk:
        where_clauses.append(
            "(risk_level != 'NORMAL' OR incident_count > 0 OR policy_violation = true)"
        )
        filters_applied["risk"] = True

    # Risk level filter (specific values)
    if risk_level:
        values = [r.value for r in risk_level]
        where_clauses.append("risk_level = ANY(:risk_level)")
        params["risk_level"] = values
        filters_applied["risk_level"] = values

    # Latency bucket filter
    if latency_bucket:
        values = [l.value for l in latency_bucket]
        where_clauses.append("latency_bucket = ANY(:latency_bucket)")
        params["latency_bucket"] = values
        filters_applied["latency_bucket"] = values

    # Evidence health filter
    if evidence_health:
        values = [e.value for e in evidence_health]
        where_clauses.append("evidence_health = ANY(:evidence_health)")
        params["evidence_health"] = values
        filters_applied["evidence_health"] = values

    # Integrity status filter
    if integrity_status:
        values = [i.value for i in integrity_status]
        where_clauses.append("integrity_status = ANY(:integrity_status)")
        params["integrity_status"] = values
        filters_applied["integrity_status"] = values

    # Source filter
    if source:
        values = [s.value for s in source]
        where_clauses.append("source = ANY(:source)")
        params["source"] = values
        filters_applied["source"] = values

    # Provider type filter
    if provider_type:
        values = [p.value for p in provider_type]
        where_clauses.append("provider_type = ANY(:provider_type)")
        params["provider_type"] = values
        filters_applied["provider_type"] = values

    # SDSR filter
    if is_synthetic is not None:
        where_clauses.append("is_synthetic = :is_synthetic")
        params["is_synthetic"] = is_synthetic
        filters_applied["is_synthetic"] = is_synthetic

    # Time filters
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

    # Build WHERE clause
    where_sql = " AND ".join(where_clauses)

    # Sorting (explicit allowlist only)
    sort_column = sort_by.value
    sort_dir = "DESC" if sort_order == SortOrder.DESC else "ASC"

    # Count query (for pagination)
    count_sql = f"""
        SELECT COUNT(*) as total
        FROM v_runs_o2
        WHERE {where_sql}
    """

    # Data query
    data_sql = f"""
        SELECT
            run_id,
            tenant_id,
            project_id,
            is_synthetic,
            source,
            provider_type,
            state,
            status,
            started_at,
            last_seen_at,
            completed_at,
            duration_ms,
            risk_level,
            latency_bucket,
            evidence_health,
            integrity_status,
            incident_count,
            policy_draft_count,
            policy_violation,
            input_tokens,
            output_tokens,
            estimated_cost_usd
        FROM v_runs_o2
        WHERE {where_sql}
        ORDER BY {sort_column} {sort_dir}
        LIMIT :limit
        OFFSET :offset
    """

    params["limit"] = limit
    params["offset"] = offset

    # Execute queries
    try:
        # Get total count
        count_result = await session.execute(text(count_sql), params)
        total = count_result.scalar() or 0

        # Get data
        data_result = await session.execute(text(data_sql), params)
        rows = data_result.mappings().all()

        # Convert to response models
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
            pagination=Pagination(
                limit=limit,
                offset=offset,
                next_offset=next_offset,
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /runs/{run_id} - O3 Detail Endpoint (Stub for now)
# =============================================================================


@activity_runs_router.get(
    "/runs/{run_id}",
    summary="Get run detail (O3)",
    description="Returns detailed information about a specific run.",
    tags=["o3-detail"],
)
async def get_run_detail(
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> dict[str, Any]:
    """
    Get run detail (O3).

    TODO: Implement full O3 response with execution timeline.
    """
    sql = """
        SELECT *
        FROM v_runs_o2
        WHERE run_id = :run_id
    """

    result = await session.execute(text(sql), {"run_id": run_id})
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Run not found")

    return dict(row)


# =============================================================================
# O4 and O5 endpoints (preflight only - stubs)
# =============================================================================


@activity_runs_router.get(
    "/runs/{run_id}/evidence",
    summary="Get run evidence (O4)",
    description="Returns cross-domain impact and evidence context. Preflight only.",
    tags=["o4-evidence", "preflight-only"],
)
async def get_run_evidence(run_id: str) -> dict[str, Any]:
    """
    Get run evidence (O4).

    TODO: Implement with taxonomy B/D/G/H categories.
    Preflight console only.
    """
    # PREFLIGHT GATE (PIN-411)
    require_preflight()

    return {
        "run_id": run_id,
        "incidents_caused": [],
        "policies_triggered": [],
        "decisions_made": [],
        "traces_linked": [],
    }


@activity_runs_router.get(
    "/runs/{run_id}/proof",
    summary="Get run proof (O5)",
    description="Returns raw traces, logs, and integrity proof. Preflight only.",
    tags=["o5-proof", "preflight-only"],
)
async def get_run_proof(
    run_id: str,
    include_payloads: bool = False,  # noqa: ARG001 - reserved for future use
) -> dict[str, Any]:
    """
    Get run proof (O5).

    TODO: Implement with integrity verification.
    Preflight console only.

    Args:
        run_id: Run identifier
        include_payloads: If True, include full request/response payloads (future)
    """
    # PREFLIGHT GATE (PIN-411)
    require_preflight()

    _ = include_payloads  # Reserved for future use
    return {
        "run_id": run_id,
        "integrity": {
            "root_hash": None,
            "verification_status": "UNKNOWN",
            "chain_length": 0,
        },
        "aos_traces": [],
        "aos_trace_steps": [],
        "raw_logs": [],
    }
