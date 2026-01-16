# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified INCIDENTS domain facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: INCIDENTS Domain - One Facade Architecture
#
# GOVERNANCE NOTE:
# This is the ONE facade for INCIDENTS domain.
# All incident data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Unified Incidents API (L2)

Customer-facing endpoints for viewing incidents.
All requests are tenant-scoped via auth_context.

Endpoints:
- GET /api/v1/incidents                     → O2 list with filters
- GET /api/v1/incidents/{incident_id}       → O3 detail
- GET /api/v1/incidents/{incident_id}/evidence → O4 context (preflight)
- GET /api/v1/incidents/{incident_id}/proof    → O5 raw (preflight)
- GET /api/v1/incidents/by-run/{run_id}     → Incidents linked to run

Architecture:
- ONE facade for all INCIDENTS needs
- Tenant isolation via auth_context (not header)
- SDSR validates this same production API
"""

import os
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.models.killswitch import Incident

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


class LifecycleState(str, Enum):
    """Incident lifecycle state."""

    ACTIVE = "ACTIVE"
    ACKED = "ACKED"
    RESOLVED = "RESOLVED"


class Severity(str, Enum):
    """Incident severity."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CauseType(str, Enum):
    """Incident cause type."""

    LLM_RUN = "LLM_RUN"
    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"


class Topic(str, Enum):
    """UX topic for filtering."""

    ACTIVE = "ACTIVE"  # Includes ACTIVE + ACKED states
    RESOLVED = "RESOLVED"


class SortField(str, Enum):
    """Allowed sort fields."""

    CREATED_AT = "created_at"
    RESOLVED_AT = "resolved_at"
    SEVERITY = "severity"


class SortOrder(str, Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


# =============================================================================
# Response Models
# =============================================================================


class IncidentSummary(BaseModel):
    """Incident summary for list view (O2)."""

    incident_id: str
    tenant_id: str
    lifecycle_state: str
    severity: str
    category: str
    title: str
    description: Optional[str] = None
    llm_run_id: Optional[str] = None
    cause_type: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    is_synthetic: bool = False

    class Config:
        from_attributes = True


class Pagination(BaseModel):
    """Pagination metadata."""

    limit: int
    offset: int
    next_offset: Optional[int] = None


class IncidentListResponse(BaseModel):
    """GET /incidents response."""

    items: List[IncidentSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]
    pagination: Pagination


class IncidentDetailResponse(BaseModel):
    """GET /incidents/{incident_id} response (O3)."""

    incident_id: str
    tenant_id: str
    lifecycle_state: str
    severity: str
    category: str
    title: str
    description: Optional[str] = None
    llm_run_id: Optional[str] = None
    source_run_id: Optional[str] = None
    cause_type: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    affected_agent_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    is_synthetic: bool = False
    synthetic_scenario_id: Optional[str] = None

    class Config:
        from_attributes = True


class IncidentsByRunResponse(BaseModel):
    """GET /incidents/by-run/{run_id} response."""

    run_id: str
    incidents: List[IncidentSummary]
    total: int


# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["incidents"],
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
# GET /incidents - O2 List
# =============================================================================


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List incidents (O2)",
    description="""
    Returns paginated list of incidents matching filter criteria.
    Tenant isolation enforced via auth_context.

    Topic mapping:
    - ACTIVE topic: includes ACTIVE + ACKED lifecycle states
    - RESOLVED topic: includes RESOLVED state only
    """,
)
async def list_incidents(
    request: Request,
    # Topic filter (maps to lifecycle states)
    topic: Annotated[Topic | None, Query(description="UX Topic: ACTIVE or RESOLVED")] = None,
    # Direct filters
    lifecycle_state: Annotated[LifecycleState | None, Query(description="Direct lifecycle state filter")] = None,
    severity: Annotated[Severity | None, Query(description="Filter by severity")] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    cause_type: Annotated[CauseType | None, Query(description="Filter by cause type")] = None,
    # SDSR filter
    is_synthetic: Annotated[bool | None, Query(description="Filter by synthetic data flag")] = None,
    # Time filters
    created_after: Annotated[datetime | None, Query(description="Filter incidents created after")] = None,
    created_before: Annotated[datetime | None, Query(description="Filter incidents created before")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max incidents to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of incidents to skip")] = 0,
    # Sorting
    sort_by: Annotated[SortField, Query(description="Field to sort by")] = SortField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.DESC,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> IncidentListResponse:
    """List incidents with unified query filters. Tenant-scoped."""

    tenant_id = get_tenant_id_from_auth(request)

    # Build filters
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    # Base query with tenant isolation
    stmt = select(Incident).where(Incident.tenant_id == tenant_id)

    # Topic filter (maps to lifecycle states)
    if topic:
        if topic == Topic.ACTIVE:
            stmt = stmt.where(Incident.lifecycle_state.in_(["ACTIVE", "ACKED"]))
            filters_applied["topic"] = "ACTIVE"
        else:
            stmt = stmt.where(Incident.lifecycle_state == "RESOLVED")
            filters_applied["topic"] = "RESOLVED"
    elif lifecycle_state:
        stmt = stmt.where(Incident.lifecycle_state == lifecycle_state.value)
        filters_applied["lifecycle_state"] = lifecycle_state.value

    if severity:
        stmt = stmt.where(Incident.severity == severity.value)
        filters_applied["severity"] = severity.value

    if category:
        stmt = stmt.where(Incident.category == category)
        filters_applied["category"] = category

    if cause_type:
        stmt = stmt.where(Incident.cause_type == cause_type.value)
        filters_applied["cause_type"] = cause_type.value

    if is_synthetic is not None:
        stmt = stmt.where(Incident.is_synthetic == is_synthetic)
        filters_applied["is_synthetic"] = is_synthetic

    if created_after:
        stmt = stmt.where(Incident.created_at >= created_after)
        filters_applied["created_after"] = created_after.isoformat()

    if created_before:
        stmt = stmt.where(Incident.created_at <= created_before)
        filters_applied["created_before"] = created_before.isoformat()

    # Count query (same filters, no pagination)
    count_stmt = select(func.count(Incident.id)).where(Incident.tenant_id == tenant_id)
    if topic:
        if topic == Topic.ACTIVE:
            count_stmt = count_stmt.where(Incident.lifecycle_state.in_(["ACTIVE", "ACKED"]))
        else:
            count_stmt = count_stmt.where(Incident.lifecycle_state == "RESOLVED")
    elif lifecycle_state:
        count_stmt = count_stmt.where(Incident.lifecycle_state == lifecycle_state.value)
    if severity:
        count_stmt = count_stmt.where(Incident.severity == severity.value)
    if category:
        count_stmt = count_stmt.where(Incident.category == category)
    if cause_type:
        count_stmt = count_stmt.where(Incident.cause_type == cause_type.value)
    if is_synthetic is not None:
        count_stmt = count_stmt.where(Incident.is_synthetic == is_synthetic)
    if created_after:
        count_stmt = count_stmt.where(Incident.created_at >= created_after)
    if created_before:
        count_stmt = count_stmt.where(Incident.created_at <= created_before)

    # Sorting
    sort_column = getattr(Incident, sort_by.value)
    if sort_order == SortOrder.DESC:
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    # Pagination
    stmt = stmt.limit(limit).offset(offset)

    try:
        # Execute count
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Execute data query
        result = await session.execute(stmt)
        incidents = result.scalars().all()

        items = [
            IncidentSummary(
                incident_id=inc.id,
                tenant_id=inc.tenant_id,
                lifecycle_state=inc.lifecycle_state or "ACTIVE",
                severity=inc.severity or "medium",
                category=inc.category or "UNKNOWN",
                title=inc.title or "Untitled Incident",
                description=inc.description,
                llm_run_id=inc.llm_run_id,
                cause_type=inc.cause_type or "SYSTEM",
                error_code=inc.error_code,
                error_message=inc.error_message,
                created_at=inc.created_at,
                resolved_at=inc.resolved_at,
                is_synthetic=inc.is_synthetic or False,
            )
            for inc in incidents
        ]

        has_more = offset + len(items) < total
        next_offset = offset + limit if has_more else None

        return IncidentListResponse(
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
# GET /incidents/by-run/{run_id} - Incidents for a Run
# =============================================================================


@router.get(
    "/by-run/{run_id}",
    response_model=IncidentsByRunResponse,
    summary="Get incidents for a run",
    description="Returns all incidents linked to a specific run.",
)
async def get_incidents_for_run(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> IncidentsByRunResponse:
    """Get all incidents linked to a specific run. Tenant-scoped."""

    tenant_id = get_tenant_id_from_auth(request)

    stmt = (
        select(Incident)
        .where(Incident.tenant_id == tenant_id)
        .where(Incident.source_run_id == run_id)
        .order_by(Incident.created_at.desc())
    )

    result = await session.execute(stmt)
    incidents = result.scalars().all()

    items = [
        IncidentSummary(
            incident_id=inc.id,
            tenant_id=inc.tenant_id,
            lifecycle_state=inc.lifecycle_state or "ACTIVE",
            severity=inc.severity or "medium",
            category=inc.category or "UNKNOWN",
            title=inc.title or "Untitled Incident",
            description=inc.description,
            llm_run_id=inc.llm_run_id,
            cause_type=inc.cause_type or "SYSTEM",
            error_code=inc.error_code,
            error_message=inc.error_message,
            created_at=inc.created_at,
            resolved_at=inc.resolved_at,
            is_synthetic=inc.is_synthetic or False,
        )
        for inc in incidents
    ]

    return IncidentsByRunResponse(
        run_id=run_id,
        incidents=items,
        total=len(items),
    )


# =============================================================================
# GET /incidents/{incident_id} - O3 Detail
# =============================================================================


@router.get(
    "/{incident_id}",
    response_model=IncidentDetailResponse,
    summary="Get incident detail (O3)",
    description="Returns detailed information about a specific incident.",
)
async def get_incident_detail(
    request: Request,
    incident_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> IncidentDetailResponse:
    """Get incident detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    stmt = select(Incident).where(Incident.id == incident_id).where(Incident.tenant_id == tenant_id)

    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return IncidentDetailResponse(
        incident_id=incident.id,
        tenant_id=incident.tenant_id,
        lifecycle_state=incident.lifecycle_state or "ACTIVE",
        severity=incident.severity or "medium",
        category=incident.category or "UNKNOWN",
        title=incident.title or "Untitled Incident",
        description=incident.description,
        llm_run_id=incident.llm_run_id,
        source_run_id=incident.source_run_id,
        cause_type=incident.cause_type or "SYSTEM",
        error_code=incident.error_code,
        error_message=incident.error_message,
        affected_agent_id=incident.affected_agent_id,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        resolved_at=incident.resolved_at,
        is_synthetic=incident.is_synthetic or False,
        synthetic_scenario_id=incident.synthetic_scenario_id,
    )


# =============================================================================
# GET /incidents/{incident_id}/evidence - O4 Context (Preflight Only)
# =============================================================================


@router.get(
    "/{incident_id}/evidence",
    summary="Get incident evidence (O4)",
    description="Returns cross-domain impact and evidence context. Preflight only.",
)
async def get_incident_evidence(
    request: Request,
    incident_id: str,
) -> dict[str, Any]:
    """Get incident evidence (O4). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth

    return {
        "incident_id": incident_id,
        "source_run": None,
        "policies_triggered": [],
        "related_incidents": [],
        "recovery_suggestions": [],
    }


# =============================================================================
# GET /incidents/{incident_id}/proof - O5 Raw (Preflight Only)
# =============================================================================


@router.get(
    "/{incident_id}/proof",
    summary="Get incident proof (O5)",
    description="Returns raw traces, logs, and integrity proof. Preflight only.",
)
async def get_incident_proof(
    request: Request,
    incident_id: str,
) -> dict[str, Any]:
    """Get incident proof (O5). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth

    return {
        "incident_id": incident_id,
        "integrity": {
            "verification_status": "UNKNOWN",
        },
        "aos_traces": [],
        "raw_logs": [],
        "timeline": [],
    }
