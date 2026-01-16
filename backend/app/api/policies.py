# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified POLICIES domain facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: POLICIES Domain - One Facade Architecture, PIN-412
#
# GOVERNANCE NOTE:
# This is the ONE facade for POLICIES domain.
# All policy rules and limits data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Unified Policies API (L2)

Customer-facing endpoints for viewing policy rules and limits.
All requests are tenant-scoped via auth_context.

Endpoints:
- GET /api/v1/policies/rules           → O2 list of policy rules
- GET /api/v1/policies/rules/{rule_id} → O3 rule detail
- GET /api/v1/policies/limits          → O2 list of limits
- GET /api/v1/policies/limits/{limit_id} → O3 limit detail

Architecture:
- ONE facade for all POLICIES needs (rules + limits)
- Queries PolicyRule, PolicyRuleIntegrity, Limit, LimitIntegrity tables
- Tenant isolation via auth_context (not header)
- SDSR validates this same production API
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.models.policy_control_plane import (
    Limit,
    LimitBreach,
    LimitIntegrity,
    PolicyEnforcement,
    PolicyRule,
    PolicyRuleIntegrity,
)

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
# Response Models — Policy Rules (O2)
# =============================================================================


class PolicyRuleSummary(BaseModel):
    """O2 Result Shape for policy rules."""

    rule_id: str
    name: str
    enforcement_mode: str  # BLOCK, WARN, AUDIT, DISABLED
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT
    source: str  # MANUAL, SYSTEM, LEARNED
    status: str  # ACTIVE, RETIRED
    created_at: datetime
    created_by: Optional[str]
    integrity_status: str  # VERIFIED, DEGRADED, FAILED
    integrity_score: Decimal
    trigger_count_30d: int
    last_triggered_at: Optional[datetime]


class RulesListResponse(BaseModel):
    """GET /rules response (O2)."""

    items: List[PolicyRuleSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class PolicyRuleDetailResponse(BaseModel):
    """GET /rules/{rule_id} response (O3)."""

    rule_id: str
    name: str
    description: Optional[str]
    enforcement_mode: str
    scope: str
    source: str
    status: str
    created_at: datetime
    created_by: Optional[str]
    updated_at: Optional[datetime]
    integrity_status: str
    integrity_score: Decimal
    trigger_count_30d: int
    last_triggered_at: Optional[datetime]
    # O3 additions
    rule_definition: Optional[dict] = None
    violation_count_total: int = 0


# =============================================================================
# Response Models — Limits (O2)
# =============================================================================


class LimitSummary(BaseModel):
    """O2 Result Shape for limits."""

    limit_id: str
    name: str
    limit_category: str  # BUDGET, RATE, THRESHOLD
    limit_type: str  # COST_USD, TOKENS_*, REQUESTS_*, etc.
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT, PROVIDER
    enforcement: str  # BLOCK, WARN, REJECT, QUEUE, DEGRADE, ALERT
    status: str  # ACTIVE, DISABLED
    max_value: Decimal
    window_seconds: Optional[int]  # For RATE limits
    reset_period: Optional[str]  # For BUDGET limits: DAILY, WEEKLY, MONTHLY, NONE
    integrity_status: str  # VERIFIED, DEGRADED, FAILED
    integrity_score: Decimal
    breach_count_30d: int
    last_breached_at: Optional[datetime]
    created_at: datetime


class LimitsListResponse(BaseModel):
    """GET /limits response (O2)."""

    items: List[LimitSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class LimitDetailResponse(BaseModel):
    """GET /limits/{limit_id} response (O3)."""

    limit_id: str
    name: str
    description: Optional[str]
    limit_category: str
    limit_type: str
    scope: str
    enforcement: str
    status: str
    max_value: Decimal
    window_seconds: Optional[int]
    reset_period: Optional[str]
    integrity_status: str
    integrity_score: Decimal
    breach_count_30d: int
    last_breached_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    # O3 additions
    current_value: Optional[Decimal] = None
    utilization_percent: Optional[float] = None


# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/policies",
    tags=["policies"],
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
# GET /rules - O2 Policy Rules List
# =============================================================================


@router.get(
    "/rules",
    response_model=RulesListResponse,
    summary="List policy rules (O2)",
    description="""
    Returns paginated list of policy rules.
    Tenant isolation enforced via auth_context.
    Includes integrity status and trigger statistics.
    """,
)
async def list_policy_rules(
    request: Request,
    # Status filter
    status: Annotated[
        str,
        Query(
            description="Rule status: ACTIVE or RETIRED",
            pattern="^(ACTIVE|RETIRED)$",
        ),
    ] = "ACTIVE",
    # Optional filters
    enforcement_mode: Annotated[
        Optional[str],
        Query(
            description="Filter by enforcement mode: BLOCK, WARN, AUDIT, DISABLED",
            pattern="^(BLOCK|WARN|AUDIT|DISABLED)$",
        ),
    ] = None,
    scope: Annotated[
        Optional[str],
        Query(
            description="Filter by scope: GLOBAL, TENANT, PROJECT, AGENT",
            pattern="^(GLOBAL|TENANT|PROJECT|AGENT)$",
        ),
    ] = None,
    source: Annotated[
        Optional[str],
        Query(
            description="Filter by source: MANUAL, SYSTEM, LEARNED",
            pattern="^(MANUAL|SYSTEM|LEARNED)$",
        ),
    ] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter by created_at >= value")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter by created_at <= value")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max rules to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of rules to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> RulesListResponse:
    """List policy rules with unified query filters. READ-ONLY."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "status": status}

    # Time window for trigger stats (30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    try:
        # Subquery: enforcement aggregation
        enforcement_stats_subq = (
            select(
                PolicyEnforcement.rule_id.label("rule_id"),
                func.count(PolicyEnforcement.id).label("trigger_count_30d"),
                func.max(PolicyEnforcement.triggered_at).label("last_triggered_at"),
            )
            .where(PolicyEnforcement.triggered_at >= thirty_days_ago)
            .group_by(PolicyEnforcement.rule_id)
            .subquery()
        )

        # Main query
        stmt = (
            select(
                PolicyRule.id.label("rule_id"),
                PolicyRule.name,
                PolicyRule.enforcement_mode,
                PolicyRule.scope,
                PolicyRule.source,
                PolicyRule.status,
                PolicyRule.created_at,
                PolicyRule.created_by,
                PolicyRuleIntegrity.integrity_status,
                PolicyRuleIntegrity.integrity_score,
                func.coalesce(enforcement_stats_subq.c.trigger_count_30d, 0).label("trigger_count_30d"),
                enforcement_stats_subq.c.last_triggered_at,
            )
            .join(
                PolicyRuleIntegrity,
                PolicyRuleIntegrity.rule_id == PolicyRule.id,
            )
            .outerjoin(
                enforcement_stats_subq,
                enforcement_stats_subq.c.rule_id == PolicyRule.id,
            )
            .where(
                and_(
                    PolicyRule.tenant_id == tenant_id,
                    PolicyRule.status == status,
                )
            )
            .order_by(
                enforcement_stats_subq.c.last_triggered_at.desc().nullslast(),
                PolicyRule.created_at.desc(),
            )
        )

        # Optional filters
        if enforcement_mode is not None:
            stmt = stmt.where(PolicyRule.enforcement_mode == enforcement_mode)
            filters_applied["enforcement_mode"] = enforcement_mode

        if scope is not None:
            stmt = stmt.where(PolicyRule.scope == scope)
            filters_applied["scope"] = scope

        if source is not None:
            stmt = stmt.where(PolicyRule.source == source)
            filters_applied["source"] = source

        if created_after is not None:
            stmt = stmt.where(PolicyRule.created_at >= created_after)
            filters_applied["created_after"] = created_after.isoformat()

        if created_before is not None:
            stmt = stmt.where(PolicyRule.created_at <= created_before)
            filters_applied["created_before"] = created_before.isoformat()

        # Count query
        count_stmt = (
            select(func.count(PolicyRule.id))
            .where(PolicyRule.tenant_id == tenant_id)
            .where(PolicyRule.status == status)
        )
        if enforcement_mode:
            count_stmt = count_stmt.where(PolicyRule.enforcement_mode == enforcement_mode)
        if scope:
            count_stmt = count_stmt.where(PolicyRule.scope == scope)
        if source:
            count_stmt = count_stmt.where(PolicyRule.source == source)
        if created_after:
            count_stmt = count_stmt.where(PolicyRule.created_at >= created_after)
        if created_before:
            count_stmt = count_stmt.where(PolicyRule.created_at <= created_before)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = [dict(row._mapping) for row in result.all()]

        items = [
            PolicyRuleSummary(
                rule_id=row["rule_id"],
                name=row["name"],
                enforcement_mode=row["enforcement_mode"],
                scope=row["scope"],
                source=row["source"],
                status=row["status"],
                created_at=row["created_at"],
                created_by=row["created_by"],
                integrity_status=row["integrity_status"],
                integrity_score=row["integrity_score"],
                trigger_count_30d=row["trigger_count_30d"],
                last_triggered_at=row["last_triggered_at"],
            )
            for row in rows
        ]

        return RulesListResponse(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /rules/{rule_id} - O3 Policy Rule Detail
# =============================================================================


@router.get(
    "/rules/{rule_id}",
    response_model=PolicyRuleDetailResponse,
    summary="Get policy rule detail (O3)",
    description="Returns detailed information about a specific policy rule.",
)
async def get_policy_rule_detail(
    request: Request,
    rule_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> PolicyRuleDetailResponse:
    """Get policy rule detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    try:
        # Subquery for trigger stats
        enforcement_stats_subq = (
            select(
                PolicyEnforcement.rule_id.label("rule_id"),
                func.count(PolicyEnforcement.id).label("trigger_count_30d"),
                func.max(PolicyEnforcement.triggered_at).label("last_triggered_at"),
            )
            .where(
                PolicyEnforcement.rule_id == rule_id,
                PolicyEnforcement.triggered_at >= thirty_days_ago,
            )
            .group_by(PolicyEnforcement.rule_id)
            .subquery()
        )

        stmt = (
            select(
                PolicyRule,
                PolicyRuleIntegrity.integrity_status,
                PolicyRuleIntegrity.integrity_score,
                func.coalesce(enforcement_stats_subq.c.trigger_count_30d, 0).label("trigger_count_30d"),
                enforcement_stats_subq.c.last_triggered_at,
            )
            .join(PolicyRuleIntegrity, PolicyRuleIntegrity.rule_id == PolicyRule.id)
            .outerjoin(enforcement_stats_subq, enforcement_stats_subq.c.rule_id == PolicyRule.id)
            .where(
                PolicyRule.id == rule_id,
                PolicyRule.tenant_id == tenant_id,
            )
        )

        result = await session.execute(stmt)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Policy rule not found")

        rule = row[0]  # PolicyRule model

        return PolicyRuleDetailResponse(
            rule_id=rule.id,
            name=rule.name,
            description=getattr(rule, "description", None),
            enforcement_mode=rule.enforcement_mode,
            scope=rule.scope,
            source=rule.source,
            status=rule.status,
            created_at=rule.created_at,
            created_by=rule.created_by,
            updated_at=getattr(rule, "updated_at", None),
            integrity_status=row[1],
            integrity_score=row[2],
            trigger_count_30d=row[3],
            last_triggered_at=row[4],
            rule_definition=getattr(rule, "rule_definition", None),
            violation_count_total=0,  # Could add total count query
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /limits - O2 Limits List
# =============================================================================


@router.get(
    "/limits",
    response_model=LimitsListResponse,
    summary="List limits (O2)",
    description="""
    Returns paginated list of limits.
    Tenant isolation enforced via auth_context.
    Includes integrity status and breach statistics.
    """,
)
async def list_limits(
    request: Request,
    # Category filter
    category: Annotated[
        str,
        Query(
            alias="type",
            description="Limit category: BUDGET, RATE, or THRESHOLD",
            pattern="^(BUDGET|RATE|THRESHOLD)$",
        ),
    ] = "BUDGET",
    # Status filter
    status: Annotated[
        str,
        Query(
            description="Limit status: ACTIVE or DISABLED",
            pattern="^(ACTIVE|DISABLED)$",
        ),
    ] = "ACTIVE",
    # Optional filters
    scope: Annotated[
        Optional[str],
        Query(
            description="Filter by scope: GLOBAL, TENANT, PROJECT, AGENT, PROVIDER",
            pattern="^(GLOBAL|TENANT|PROJECT|AGENT|PROVIDER)$",
        ),
    ] = None,
    enforcement: Annotated[
        Optional[str],
        Query(
            description="Filter by enforcement: BLOCK, WARN, REJECT, QUEUE, DEGRADE, ALERT",
            pattern="^(BLOCK|WARN|REJECT|QUEUE|DEGRADE|ALERT)$",
        ),
    ] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter by created_at >= value")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter by created_at <= value")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max limits to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of limits to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> LimitsListResponse:
    """List limits with unified query filters. READ-ONLY."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {
        "tenant_id": tenant_id,
        "category": category,
        "status": status,
    }

    # Time window for breach stats (30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    try:
        # Subquery: breach aggregation
        breach_agg_subq = (
            select(
                LimitBreach.limit_id.label("limit_id"),
                func.count().label("breach_count_30d"),
                func.max(LimitBreach.breached_at).label("last_breached_at"),
            )
            .where(LimitBreach.breached_at >= thirty_days_ago)
            .group_by(LimitBreach.limit_id)
            .subquery()
        )

        # Main query
        stmt = (
            select(
                Limit.id.label("limit_id"),
                Limit.name,
                Limit.limit_category,
                Limit.limit_type,
                Limit.scope,
                Limit.enforcement,
                Limit.status,
                Limit.max_value,
                Limit.window_seconds,
                Limit.reset_period,
                LimitIntegrity.integrity_status,
                LimitIntegrity.integrity_score,
                func.coalesce(breach_agg_subq.c.breach_count_30d, 0).label("breach_count_30d"),
                breach_agg_subq.c.last_breached_at,
                Limit.created_at,
            )
            .select_from(Limit)
            .join(LimitIntegrity, LimitIntegrity.limit_id == Limit.id)
            .outerjoin(breach_agg_subq, breach_agg_subq.c.limit_id == Limit.id)
            .where(
                and_(
                    Limit.tenant_id == tenant_id,
                    Limit.limit_category == category,
                    Limit.status == status,
                )
            )
            .order_by(
                breach_agg_subq.c.last_breached_at.desc().nullslast(),
                Limit.created_at.desc(),
            )
        )

        # Optional filters
        if scope is not None:
            stmt = stmt.where(Limit.scope == scope)
            filters_applied["scope"] = scope

        if enforcement is not None:
            stmt = stmt.where(Limit.enforcement == enforcement)
            filters_applied["enforcement"] = enforcement

        if created_after is not None:
            stmt = stmt.where(Limit.created_at >= created_after)
            filters_applied["created_after"] = created_after.isoformat()

        if created_before is not None:
            stmt = stmt.where(Limit.created_at <= created_before)
            filters_applied["created_before"] = created_before.isoformat()

        # Count query
        count_stmt = (
            select(func.count(Limit.id))
            .where(Limit.tenant_id == tenant_id)
            .where(Limit.limit_category == category)
            .where(Limit.status == status)
        )
        if scope:
            count_stmt = count_stmt.where(Limit.scope == scope)
        if enforcement:
            count_stmt = count_stmt.where(Limit.enforcement == enforcement)
        if created_after:
            count_stmt = count_stmt.where(Limit.created_at >= created_after)
        if created_before:
            count_stmt = count_stmt.where(Limit.created_at <= created_before)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = [dict(row._mapping) for row in result.all()]

        items = [
            LimitSummary(
                limit_id=row["limit_id"],
                name=row["name"],
                limit_category=row["limit_category"],
                limit_type=row["limit_type"],
                scope=row["scope"],
                enforcement=row["enforcement"],
                status=row["status"],
                max_value=row["max_value"],
                window_seconds=row["window_seconds"],
                reset_period=row["reset_period"],
                integrity_status=row["integrity_status"],
                integrity_score=row["integrity_score"],
                breach_count_30d=row["breach_count_30d"],
                last_breached_at=row["last_breached_at"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

        return LimitsListResponse(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /limits/{limit_id} - O3 Limit Detail
# =============================================================================


@router.get(
    "/limits/{limit_id}",
    response_model=LimitDetailResponse,
    summary="Get limit detail (O3)",
    description="Returns detailed information about a specific limit.",
)
async def get_limit_detail(
    request: Request,
    limit_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LimitDetailResponse:
    """Get limit detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    try:
        # Subquery for breach stats
        breach_agg_subq = (
            select(
                LimitBreach.limit_id.label("limit_id"),
                func.count().label("breach_count_30d"),
                func.max(LimitBreach.breached_at).label("last_breached_at"),
            )
            .where(
                LimitBreach.limit_id == limit_id,
                LimitBreach.breached_at >= thirty_days_ago,
            )
            .group_by(LimitBreach.limit_id)
            .subquery()
        )

        stmt = (
            select(
                Limit,
                LimitIntegrity.integrity_status,
                LimitIntegrity.integrity_score,
                func.coalesce(breach_agg_subq.c.breach_count_30d, 0).label("breach_count_30d"),
                breach_agg_subq.c.last_breached_at,
            )
            .join(LimitIntegrity, LimitIntegrity.limit_id == Limit.id)
            .outerjoin(breach_agg_subq, breach_agg_subq.c.limit_id == Limit.id)
            .where(
                Limit.id == limit_id,
                Limit.tenant_id == tenant_id,
            )
        )

        result = await session.execute(stmt)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Limit not found")

        lim = row[0]  # Limit model

        return LimitDetailResponse(
            limit_id=lim.id,
            name=lim.name,
            description=getattr(lim, "description", None),
            limit_category=lim.limit_category,
            limit_type=lim.limit_type,
            scope=lim.scope,
            enforcement=lim.enforcement,
            status=lim.status,
            max_value=lim.max_value,
            window_seconds=lim.window_seconds,
            reset_period=lim.reset_period,
            integrity_status=row[1],
            integrity_score=row[2],
            breach_count_30d=row[3],
            last_breached_at=row[4],
            created_at=lim.created_at,
            updated_at=getattr(lim, "updated_at", None),
            current_value=None,  # Could add current usage query
            utilization_percent=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /rules/{rule_id}/evidence - O4 Context (Preflight Only)
# =============================================================================


@router.get(
    "/rules/{rule_id}/evidence",
    summary="Get rule evidence (O4)",
    description="Returns enforcement context and impact. Preflight only.",
)
async def get_rule_evidence(
    request: Request,
    rule_id: str,
) -> dict[str, Any]:
    """Get rule evidence (O4). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth

    return {
        "rule_id": rule_id,
        "recent_enforcements": [],
        "affected_runs": [],
        "violations_triggered": [],
    }


# =============================================================================
# GET /limits/{limit_id}/evidence - O4 Context (Preflight Only)
# =============================================================================


@router.get(
    "/limits/{limit_id}/evidence",
    summary="Get limit evidence (O4)",
    description="Returns breach history and impact. Preflight only.",
)
async def get_limit_evidence(
    request: Request,
    limit_id: str,
) -> dict[str, Any]:
    """Get limit evidence (O4). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth

    return {
        "limit_id": limit_id,
        "recent_breaches": [],
        "affected_runs": [],
        "usage_history": [],
    }
