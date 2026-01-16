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

    return {
        "run_id": run_id,
        "incidents_caused": [],
        "policies_triggered": [],
        "decisions_made": [],
        "traces_linked": [],
    }


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
