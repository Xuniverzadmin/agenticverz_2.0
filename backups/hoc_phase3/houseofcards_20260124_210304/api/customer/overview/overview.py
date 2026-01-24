# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
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
- GET /api/v1/overview/highlights      → O1 system pulse & domain counts (Activity, Incidents, Policies)
- GET /api/v1/overview/decisions       → O2 pending decisions queue
- GET /api/v1/overview/decisions/count → O2 decisions count summary
- GET /api/v1/overview/costs           → O2 cost intelligence summary
- GET /api/v1/overview/recovery-stats  → O3 recovery statistics

This is the ONLY facade for overview operations.
All overview APIs flow through this router.
"""

import logging
import os
from datetime import datetime
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.services.overview_facade import get_overview_facade

logger = logging.getLogger("nova.api.overview")


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
    pending: int
    critical: int


class SystemPulse(BaseModel):
    """System health pulse summary."""
    status: str
    active_incidents: int
    pending_decisions: int
    recent_breaches: int
    live_runs: int
    queued_runs: int


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
    source_domain: str
    entity_type: str
    entity_id: str
    decision_type: str
    priority: str
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
    llm_run_cost: float


class LimitCostItem(BaseModel):
    """Single limit with cost status."""
    limit_id: str
    name: str
    category: str
    max_value: float
    used_value: float
    remaining_value: float
    status: str


class CostViolations(BaseModel):
    """Cost violation summary."""
    breach_count: int
    total_overage: float


class CostsResponse(BaseModel):
    """GET /costs response (O2)."""
    currency: str
    period: CostPeriod
    actuals: CostActuals
    limits: List[LimitCostItem]
    violations: CostViolations


# =============================================================================
# Response Models — Decisions Count (O2)
# =============================================================================


class DecisionsCountResponse(BaseModel):
    """GET /decisions/count response."""
    total: int
    by_domain: dict[str, int]
    by_priority: dict[str, int]


# =============================================================================
# Response Models — Recovery Stats (O3)
# =============================================================================


class RecoveryStatsResponse(BaseModel):
    """GET /recovery-stats response."""
    total_incidents: int
    recovered: int
    pending_recovery: int
    failed_recovery: int
    recovery_rate_pct: float
    period: CostPeriod


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
    facade = get_overview_facade()

    try:
        result = await facade.get_highlights(session, tenant_id)

        return HighlightsResponse(
            pulse=SystemPulse(
                status=result.pulse.status,
                active_incidents=result.pulse.active_incidents,
                pending_decisions=result.pulse.pending_decisions,
                recent_breaches=result.pulse.recent_breaches,
                live_runs=result.pulse.live_runs,
                queued_runs=result.pulse.queued_runs,
            ),
            domain_counts=[
                DomainCount(
                    domain=dc.domain,
                    total=dc.total,
                    pending=dc.pending,
                    critical=dc.critical,
                )
                for dc in result.domain_counts
            ],
            last_activity_at=result.last_activity_at,
        )

    except Exception as e:
        logger.exception(f"[OVERVIEW] get_highlights failed: {e}")
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
    facade = get_overview_facade()

    try:
        result = await facade.get_decisions(
            session=session,
            tenant_id=tenant_id,
            source_domain=source_domain,
            priority=priority,
            limit=limit,
            offset=offset,
        )

        next_offset = offset + limit if result.has_more else None

        return DecisionsResponse(
            items=[
                DecisionItem(
                    source_domain=item.source_domain,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    decision_type=item.decision_type,
                    priority=item.priority,
                    summary=item.summary,
                    created_at=item.created_at,
                )
                for item in result.items
            ],
            total=result.total,
            has_more=result.has_more,
            filters_applied=result.filters_applied,
            pagination=Pagination(limit=limit, offset=offset, next_offset=next_offset),
        )

    except Exception as e:
        logger.exception(f"[OVERVIEW] get_decisions failed: {e}")
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
    facade = get_overview_facade()

    try:
        result = await facade.get_costs(
            session=session,
            tenant_id=tenant_id,
            period_days=period_days,
        )

        return CostsResponse(
            currency=result.currency,
            period=CostPeriod(start=result.period.start, end=result.period.end),
            actuals=CostActuals(llm_run_cost=result.llm_run_cost),
            limits=[
                LimitCostItem(
                    limit_id=lim.limit_id,
                    name=lim.name,
                    category=lim.category,
                    max_value=lim.max_value,
                    used_value=lim.used_value,
                    remaining_value=lim.remaining_value,
                    status=lim.status,
                )
                for lim in result.limits
            ],
            violations=CostViolations(
                breach_count=result.breach_count,
                total_overage=result.total_overage,
            ),
        )

    except Exception as e:
        logger.exception(f"[OVERVIEW] get_costs failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /decisions/count - O2 Decisions Count Summary
# =============================================================================


@router.get(
    "/decisions/count",
    response_model=DecisionsCountResponse,
    summary="Get decisions count summary (O2)",
    description="""
    Count of pending decisions by domain and priority.
    PROJECTION-ONLY: Aggregates from incidents and policy_proposals.
    """,
)
async def get_decisions_count(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> DecisionsCountResponse:
    """Decisions count by domain and priority. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    facade = get_overview_facade()

    try:
        result = await facade.get_decisions_count(session, tenant_id)

        return DecisionsCountResponse(
            total=result.total,
            by_domain=result.by_domain,
            by_priority=result.by_priority,
        )

    except Exception as e:
        logger.exception(f"[OVERVIEW] get_decisions_count failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /recovery-stats - O3 Recovery Statistics
# =============================================================================


@router.get(
    "/recovery-stats",
    response_model=RecoveryStatsResponse,
    summary="Get recovery statistics (O3)",
    description="""
    Recovery statistics from incident lifecycle.
    PROJECTION-ONLY: Aggregates from incidents table.
    """,
)
async def get_recovery_stats(
    request: Request,
    period_days: Annotated[int, Query(ge=1, le=365, description="Period in days")] = 30,
    session: AsyncSession = Depends(get_async_session_dep),
) -> RecoveryStatsResponse:
    """Recovery statistics from incidents. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    facade = get_overview_facade()

    try:
        result = await facade.get_recovery_stats(
            session=session,
            tenant_id=tenant_id,
            period_days=period_days,
        )

        return RecoveryStatsResponse(
            total_incidents=result.total_incidents,
            recovered=result.recovered,
            pending_recovery=result.pending_recovery,
            failed_recovery=result.failed_recovery,
            recovery_rate_pct=result.recovery_rate_pct,
            period=CostPeriod(start=result.period.start, end=result.period.end),
        )

    except Exception as e:
        logger.exception(f"[OVERVIEW] get_recovery_stats failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )
