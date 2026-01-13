# Layer: L2 — Product APIs
# Product: ai-console
# Temporal:
#   Trigger: HTTP request
#   Execution: async
# Role: Incidents O2 Runtime Projection API (INC-RT-O2)
# Callers: Customer Console Incidents O2 List
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-412 Domain Design

"""
INC-RT-O2 — Incidents Runtime Projection Contract (LOCKED)

Deterministic, index-backed, read-only list view for Incidents O2.
This is the reference pattern for all future runtime projections.

Contract Rules:
- Tenant isolation is mandatory (from auth_context)
- Only indexed filters allowed
- No JOINs to policy tables (O3/O4 territory)
- No COUNT(*) subqueries or derived computations
- Pagination is non-negotiable
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.killswitch import Incident
from app.auth.tenant_auth import TenantContext, get_tenant_context

router = APIRouter(prefix="/incidents", tags=["runtime-incidents"])


# =============================================================================
# Response Models (INC-RT-O2 Contract Shape - EXACT)
# =============================================================================


class IncidentO2Row(BaseModel):
    """
    O2 Result Shape (EXACT from contract).
    No extra fields. No missing fields. No renaming.
    """

    incident_id: str
    lifecycle_state: str  # ACTIVE, ACKED, RESOLVED
    severity: str  # critical, high, medium, low
    category: str
    title: str
    llm_run_id: Optional[str]
    cause_type: str  # LLM_RUN, SYSTEM, HUMAN
    created_at: datetime
    resolved_at: Optional[datetime]


class IncidentsO2Response(BaseModel):
    """
    Response envelope (contract mandates this structure).
    Backend MUST return this shape even for empty results.
    """

    items: List[IncidentO2Row]
    total: int
    has_more: bool


# =============================================================================
# Query Function (INC-RT-O2 - COPY-PASTE from contract)
# =============================================================================


async def query_incidents_o2(
    *,
    session: AsyncSession,
    tenant_id: str,
    topic: str,
    limit: int,
    offset: int,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    cause_type: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> List[Incident]:
    """
    INC-RT-O2
    Deterministic, index-backed incident list query.
    Matches SQL contract exactly.

    UX Topic Mapping:
    - ACTIVE topic → includes ACTIVE + ACKED states (ACKED shown as badge)
    - RESOLVED topic → includes RESOLVED state only
    """

    # Map UX topic to DB lifecycle states
    if topic == "ACTIVE":
        # Active topic includes both ACTIVE and ACKED (ACKED shown as badge in UI)
        lifecycle_filter = Incident.lifecycle_state.in_(["ACTIVE", "ACKED"])
    else:
        # RESOLVED topic maps directly
        lifecycle_filter = Incident.lifecycle_state == "RESOLVED"

    stmt = (
        select(Incident)
        .where(Incident.tenant_id == tenant_id)
        .where(lifecycle_filter)
        .order_by(Incident.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if severity is not None:
        stmt = stmt.where(Incident.severity == severity)

    if category is not None:
        stmt = stmt.where(Incident.category == category)

    if cause_type is not None:
        stmt = stmt.where(Incident.cause_type == cause_type)

    if created_after is not None:
        stmt = stmt.where(Incident.created_at >= created_after)

    if created_before is not None:
        stmt = stmt.where(Incident.created_at <= created_before)

    result = await session.execute(stmt)
    return result.scalars().all()


async def count_incidents_o2(
    *,
    session: AsyncSession,
    tenant_id: str,
    topic: str,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    cause_type: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> int:
    """
    Count query for pagination metadata.
    Uses same filters as main query.
    """
    from sqlalchemy import func

    # Map UX topic to DB lifecycle states
    if topic == "ACTIVE":
        lifecycle_filter = Incident.lifecycle_state.in_(["ACTIVE", "ACKED"])
    else:
        lifecycle_filter = Incident.lifecycle_state == "RESOLVED"

    stmt = (
        select(func.count(Incident.id))
        .where(Incident.tenant_id == tenant_id)
        .where(lifecycle_filter)
    )

    if severity is not None:
        stmt = stmt.where(Incident.severity == severity)

    if category is not None:
        stmt = stmt.where(Incident.category == category)

    if cause_type is not None:
        stmt = stmt.where(Incident.cause_type == cause_type)

    if created_after is not None:
        stmt = stmt.where(Incident.created_at >= created_after)

    if created_before is not None:
        stmt = stmt.where(Incident.created_at <= created_before)

    result = await session.execute(stmt)
    return result.scalar() or 0


# =============================================================================
# API Endpoint (Minimal FastAPI Glue)
# =============================================================================


@router.get("", response_model=IncidentsO2Response)
async def list_incidents(
    # UX Topic filter (required for O2 from O1 navigation)
    # Maps to lifecycle states: ACTIVE topic = ACTIVE + ACKED, RESOLVED topic = RESOLVED
    topic: str = Query(
        ...,
        description="UX Topic: ACTIVE (includes ACKED as badge) or RESOLVED",
        regex="^(ACTIVE|RESOLVED)$",
    ),
    # Pagination (mandatory)
    limit: int = Query(20, ge=1, le=100, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
    # Optional indexed filters
    severity: Optional[str] = Query(
        None,
        description="Filter by severity: critical, high, medium, low",
        regex="^(critical|high|medium|low)$",
    ),
    category: Optional[str] = Query(None, description="Filter by category (exact match)"),
    cause_type: Optional[str] = Query(
        None,
        description="Filter by cause type: LLM_RUN, SYSTEM, HUMAN",
        regex="^(LLM_RUN|SYSTEM|HUMAN)$",
    ),
    created_after: Optional[datetime] = Query(None, description="Filter by created_at >= value"),
    created_before: Optional[datetime] = Query(None, description="Filter by created_at <= value"),
    # Dependencies
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session),
):
    """
    GET /api/v1/runtime/incidents

    INC-RT-O2: Incidents Runtime Projection

    Returns incidents matching the specified UX topic and filters.
    ACTIVE topic includes both ACTIVE and ACKED lifecycle states.
    ACKED items should be displayed with a badge in the UI.
    Tenant isolation is enforced from auth context.
    """

    # Query incidents
    incidents = await query_incidents_o2(
        session=session,
        tenant_id=tenant.tenant_id,
        topic=topic,
        limit=limit,
        offset=offset,
        severity=severity,
        category=category,
        cause_type=cause_type,
        created_after=created_after,
        created_before=created_before,
    )

    # Get total count for pagination
    total = await count_incidents_o2(
        session=session,
        tenant_id=tenant.tenant_id,
        topic=topic,
        severity=severity,
        category=category,
        cause_type=cause_type,
        created_after=created_after,
        created_before=created_before,
    )

    # Transform to O2 response shape (EXACT)
    items = [
        IncidentO2Row(
            incident_id=inc.id,
            lifecycle_state=inc.lifecycle_state,
            severity=inc.severity,
            category=inc.category,
            title=inc.title,
            llm_run_id=inc.llm_run_id,
            cause_type=inc.cause_type,
            created_at=inc.created_at,
            resolved_at=inc.resolved_at,
        )
        for inc in incidents
    ]

    return IncidentsO2Response(
        items=items,
        total=total,
        has_more=(offset + len(items)) < total,
    )
