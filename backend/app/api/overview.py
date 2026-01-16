# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified OVERVIEW domain facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: OVERVIEW Domain - One Facade Architecture, PIN-413
#
# GOVERNANCE NOTE:
# This is the ONE facade for OVERVIEW domain.
# All overview data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.
#
# ARCHITECTURAL RULE:
# - Overview DOES NOT own any tables
# - Overview aggregates/projects from existing domains
# - All endpoints are READ-ONLY

"""
Unified Overview API (L2)

Customer-facing endpoints for system overview and health.
All requests are tenant-scoped via auth_context.

Endpoints:
- GET /api/v1/overview/highlights  → O1 system pulse & domain counts
- GET /api/v1/overview/decisions   → O2 pending decisions queue
- GET /api/v1/overview/costs       → O2 cost intelligence summary

Architecture:
- ONE facade for all OVERVIEW needs
- PROJECTION-ONLY: aggregates from existing domain tables
- Tenant isolation via auth_context
- SDSR validates this same production API
"""

import os
from datetime import datetime, timedelta
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.models.audit_ledger import AuditLedger

# Import existing domain models (Overview does NOT own these)
from app.models.killswitch import Incident, IncidentLifecycleState
from app.models.policy import PolicyProposal
from app.models.policy_control_plane import Limit, LimitBreach, LimitCategory
from app.models.tenant import WorkerRun

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
# Response Models — System Pulse (O1)
# =============================================================================


class DomainCount(BaseModel):
    """Count for a specific domain."""

    domain: str
    total: int
    pending: int  # Items requiring human action
    critical: int  # High-priority items


class SystemPulse(BaseModel):
    """System health pulse summary."""

    status: str  # HEALTHY, ATTENTION_NEEDED, CRITICAL
    active_incidents: int
    pending_decisions: int
    recent_breaches: int  # Last 24h


class HighlightsResponse(BaseModel):
    """GET /highlights response (O1)."""

    pulse: SystemPulse
    domain_counts: List[DomainCount]
    last_activity_at: Optional[datetime]


# =============================================================================
# Response Models — Decisions Queue (O2)
# =============================================================================


class DecisionItem(BaseModel):
    """A pending decision requiring human action."""

    source_domain: str  # INCIDENT, POLICY
    entity_type: str
    entity_id: str
    decision_type: str  # ACK, APPROVE, OVERRIDE
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    summary: str
    created_at: datetime


class Pagination(BaseModel):
    """Pagination metadata."""

    limit: int
    offset: int
    next_offset: Optional[int] = None


class DecisionsResponse(BaseModel):
    """GET /decisions response (O2)."""

    items: List[DecisionItem]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]
    pagination: Pagination


# =============================================================================
# Response Models — Cost Intelligence (O2)
# =============================================================================


class CostPeriod(BaseModel):
    """Time period for cost calculation."""

    start: datetime
    end: datetime


class CostActuals(BaseModel):
    """Actual costs incurred."""

    llm_run_cost: float  # USD


class LimitCostItem(BaseModel):
    """Single limit with cost status."""

    limit_id: str
    name: str
    category: str  # BUDGET
    max_value: float
    used_value: float
    remaining_value: float
    status: str  # OK, NEAR_THRESHOLD, BREACHED


class CostViolations(BaseModel):
    """Cost violation summary."""

    breach_count: int
    total_overage: float  # USD


class CostsResponse(BaseModel):
    """GET /costs response (O2)."""

    currency: str  # Always "USD" in v1
    period: CostPeriod
    actuals: CostActuals
    limits: List[LimitCostItem]
    violations: CostViolations


# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/overview",
    tags=["overview"],
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
# GET /highlights - O1 System Pulse
# =============================================================================


@router.get(
    "/highlights",
    response_model=HighlightsResponse,
    summary="Get system highlights (O1)",
    description="""
    Cross-domain highlights: system pulse and domain counts.
    PROJECTION-ONLY: Aggregates from existing domain tables.
    """,
)
async def get_highlights(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> HighlightsResponse:
    """System pulse and domain counts. Tenant-scoped."""

    tenant_id = get_tenant_id_from_auth(request)

    # Use naive datetime for TIMESTAMP WITHOUT TIME ZONE columns
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)

    try:
        # Incident counts
        incident_stmt = select(
            func.count(Incident.id).label("total"),
            func.sum(case((Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value, 1), else_=0)).label(
                "pending"
            ),
            func.sum(
                case(
                    (
                        and_(
                            Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value,
                            Incident.severity.in_(["critical", "high"]),
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("critical"),
        ).where(Incident.tenant_id == tenant_id)
        incident_result = await session.execute(incident_stmt)
        incident_row = incident_result.one()

        # Policy proposal counts
        proposal_stmt = select(
            func.count(PolicyProposal.id).label("total"),
            func.count(case((PolicyProposal.status == "draft", 1))).label("pending"),
        ).where(PolicyProposal.tenant_id == tenant_id)
        proposal_result = await session.execute(proposal_stmt)
        proposal_row = proposal_result.one()

        # Limit breach counts (last 24h)
        breach_stmt = select(
            func.count(LimitBreach.id).label("recent"),
        ).where(
            LimitBreach.tenant_id == tenant_id,
            LimitBreach.breached_at >= last_24h,
        )
        breach_result = await session.execute(breach_stmt)
        breach_row = breach_result.one()

        # Last activity
        last_activity_stmt = select(func.max(AuditLedger.created_at)).where(AuditLedger.tenant_id == tenant_id)
        last_activity_result = await session.execute(last_activity_stmt)
        last_activity_at = last_activity_result.scalar()

        # Calculate system pulse
        active_incidents = incident_row.pending or 0
        pending_decisions = (incident_row.pending or 0) + (proposal_row.pending or 0)
        recent_breaches = breach_row.recent or 0

        if incident_row.critical and incident_row.critical > 0:
            pulse_status = "CRITICAL"
        elif pending_decisions > 0 or recent_breaches > 0:
            pulse_status = "ATTENTION_NEEDED"
        else:
            pulse_status = "HEALTHY"

        pulse = SystemPulse(
            status=pulse_status,
            active_incidents=active_incidents,
            pending_decisions=pending_decisions,
            recent_breaches=recent_breaches,
        )

        domain_counts = [
            DomainCount(
                domain="Incidents",
                total=incident_row.total or 0,
                pending=incident_row.pending or 0,
                critical=incident_row.critical or 0,
            ),
            DomainCount(
                domain="Policies",
                total=proposal_row.total or 0,
                pending=proposal_row.pending or 0,
                critical=0,
            ),
        ]

        return HighlightsResponse(
            pulse=pulse,
            domain_counts=domain_counts,
            last_activity_at=last_activity_at,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /decisions - O2 Pending Decisions Queue
# =============================================================================


@router.get(
    "/decisions",
    response_model=DecisionsResponse,
    summary="Get pending decisions (O2)",
    description="""
    Decisions queue: pending items requiring human action.
    PROJECTION-ONLY: Aggregates from incidents and policy_proposals.
    """,
)
async def get_decisions(
    request: Request,
    source_domain: Annotated[
        str | None,
        Query(
            description="Filter by source: INCIDENT, POLICY",
            pattern="^(INCIDENT|POLICY)$",
        ),
    ] = None,
    priority: Annotated[
        str | None,
        Query(
            description="Filter by priority: CRITICAL, HIGH, MEDIUM, LOW",
            pattern="^(CRITICAL|HIGH|MEDIUM|LOW)$",
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Max items")] = 50,
    offset: Annotated[int, Query(ge=0, description="Items to skip")] = 0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> DecisionsResponse:
    """Pending decisions from incidents and policy proposals. Tenant-scoped."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    if source_domain:
        filters_applied["source_domain"] = source_domain
    if priority:
        filters_applied["priority"] = priority

    items: List[DecisionItem] = []

    try:
        # 1. Project pending incidents (ACTIVE = needs ACK)
        if source_domain is None or source_domain == "INCIDENT":
            incident_stmt = (
                select(Incident)
                .where(
                    Incident.tenant_id == tenant_id,
                    Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value,
                )
                .order_by(Incident.created_at.desc())
            )
            incident_result = await session.execute(incident_stmt)
            incidents = incident_result.scalars().all()

            for inc in incidents:
                inc_priority = (
                    "CRITICAL" if inc.severity in ["critical"] else ("HIGH" if inc.severity in ["high"] else "MEDIUM")
                )
                if priority is not None and inc_priority != priority:
                    continue

                inc_created = inc.created_at
                if inc_created and inc_created.tzinfo is not None:
                    inc_created = inc_created.replace(tzinfo=None)

                items.append(
                    DecisionItem(
                        source_domain="INCIDENT",
                        entity_type="INCIDENT",
                        entity_id=str(inc.id),
                        decision_type="ACK",
                        priority=inc_priority,
                        summary=inc.title or f"Incident {inc.id}",
                        created_at=inc_created,
                    )
                )

        # 2. Project pending policy proposals (draft = needs approval)
        if source_domain is None or source_domain == "POLICY":
            proposal_stmt = (
                select(PolicyProposal)
                .where(
                    PolicyProposal.tenant_id == tenant_id,
                    PolicyProposal.status == "draft",
                )
                .order_by(PolicyProposal.created_at.desc())
            )
            proposal_result = await session.execute(proposal_stmt)
            proposals = proposal_result.scalars().all()

            for prop in proposals:
                prop_priority = "MEDIUM"
                if priority is not None and prop_priority != priority:
                    continue

                prop_created = prop.created_at
                if prop_created and prop_created.tzinfo is not None:
                    prop_created = prop_created.replace(tzinfo=None)

                items.append(
                    DecisionItem(
                        source_domain="POLICY",
                        entity_type="POLICY_PROPOSAL",
                        entity_id=str(prop.id),
                        decision_type="APPROVE",
                        priority=prop_priority,
                        summary=prop.proposal_name,
                        created_at=prop_created,
                    )
                )

        # Sort by created_at descending
        items.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        total = len(items)
        paginated = items[offset : offset + limit]
        has_more = offset + len(paginated) < total
        next_offset = offset + limit if has_more else None

        return DecisionsResponse(
            items=paginated,
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
# GET /costs - O2 Cost Intelligence
# =============================================================================


@router.get(
    "/costs",
    response_model=CostsResponse,
    summary="Get cost intelligence (O2)",
    description="""
    Cost intelligence: realized costs and budget status.
    PROJECTION-ONLY: Aggregates from limits, limit_breaches, worker_runs.
    """,
)
async def get_costs(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=365, description="Period in days")] = 30,
    session: AsyncSession = Depends(get_async_session_dep),
) -> CostsResponse:
    """Cost intelligence summary. Tenant-scoped."""

    tenant_id = get_tenant_id_from_auth(request)

    now = datetime.utcnow()
    period_start = now - timedelta(days=period_days)

    try:
        # 1. Calculate actual LLM cost from worker_runs
        cost_stmt = select(func.coalesce(func.sum(WorkerRun.cost_cents), 0).label("total_cost_cents")).where(
            WorkerRun.tenant_id == tenant_id,
            WorkerRun.created_at >= period_start,
        )
        cost_result = await session.execute(cost_stmt)
        total_cost_cents = cost_result.scalar() or 0
        llm_run_cost = float(total_cost_cents) / 100.0

        # 2. Get budget limits
        limits_stmt = (
            select(Limit)
            .where(
                Limit.tenant_id == tenant_id,
                Limit.limit_category == LimitCategory.BUDGET.value,
                Limit.status == "ACTIVE",
            )
            .order_by(Limit.name)
        )
        limits_result = await session.execute(limits_stmt)
        limits = limits_result.scalars().all()

        limit_items: List[LimitCostItem] = []
        for lim in limits:
            max_val = float(lim.max_value)
            used_val = llm_run_cost
            remaining_val = max(0, max_val - used_val)

            if used_val >= max_val:
                status = "BREACHED"
            elif used_val >= max_val * 0.8:
                status = "NEAR_THRESHOLD"
            else:
                status = "OK"

            limit_items.append(
                LimitCostItem(
                    limit_id=lim.id,
                    name=lim.name,
                    category=lim.limit_category,
                    max_value=max_val,
                    used_value=used_val,
                    remaining_value=remaining_val,
                    status=status,
                )
            )

        # 3. Get breach statistics
        breach_stmt = select(
            func.count(LimitBreach.id).label("breach_count"),
            func.coalesce(func.sum(LimitBreach.value_at_breach - LimitBreach.limit_value), 0).label("total_overage"),
        ).where(
            LimitBreach.tenant_id == tenant_id,
            LimitBreach.breached_at >= period_start,
        )
        breach_result = await session.execute(breach_stmt)
        breach_row = breach_result.one()

        return CostsResponse(
            currency="USD",
            period=CostPeriod(start=period_start, end=now),
            actuals=CostActuals(llm_run_cost=llm_run_cost),
            limits=limit_items,
            violations=CostViolations(
                breach_count=breach_row.breach_count or 0,
                total_overage=max(0, float(breach_row.total_overage or 0)),
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )
