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

import logging
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated, Any, List, Optional

logger = logging.getLogger(__name__)

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
    rule_type: Annotated[
        Optional[str],
        Query(
            description="Filter by rule type: SYSTEM, SAFETY, ETHICAL, TEMPORAL (PIN-411 Gap Closure)",
            pattern="^(SYSTEM|SAFETY|ETHICAL|TEMPORAL)$",
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

        if rule_type is not None:
            stmt = stmt.where(PolicyRule.rule_type == rule_type)
            filters_applied["rule_type"] = rule_type

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
        if rule_type:
            count_stmt = count_stmt.where(PolicyRule.rule_type == rule_type)
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
    limit_type: Annotated[
        Optional[str],
        Query(
            description="Filter by limit_type. Supports prefix match, e.g. RUNS_*, TOKENS_*, RISK_CEILING, COOLDOWN (PIN-411 Gap Closure)",
        ),
    ] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter by created_at >= value")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter by created_at <= value")] = None,
    # Pagination
    max_limit: Annotated[int, Query(ge=1, le=100, alias="limit", description="Max limits to return")] = 20,
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

        if limit_type is not None:
            # Support prefix match (e.g., RUNS_*, TOKENS_*)
            if limit_type.endswith("*"):
                prefix = limit_type[:-1]  # Remove the *
                stmt = stmt.where(Limit.limit_type.startswith(prefix))
            else:
                stmt = stmt.where(Limit.limit_type == limit_type)
            filters_applied["limit_type"] = limit_type

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
        if limit_type:
            if limit_type.endswith("*"):
                prefix = limit_type[:-1]
                count_stmt = count_stmt.where(Limit.limit_type.startswith(prefix))
            else:
                count_stmt = count_stmt.where(Limit.limit_type == limit_type)
        if created_after:
            count_stmt = count_stmt.where(Limit.created_at >= created_after)
        if created_before:
            count_stmt = count_stmt.where(Limit.created_at <= created_before)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(max_limit).offset(offset)
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


# =============================================================================
# Lessons Learned - Customer Facade (L2)
# Reference: PIN-411, POLICIES_DOMAIN_AUDIT.md Section 11
# =============================================================================


class LessonSummaryResponse(BaseModel):
    """O2 Result Shape for lessons."""

    id: str
    lesson_type: str
    severity: Optional[str]
    title: str
    status: str
    source_event_type: str
    created_at: datetime
    has_proposed_action: bool


class LessonsListResponse(BaseModel):
    """GET /lessons response (O2)."""

    items: List[LessonSummaryResponse]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class LessonDetailResponse(BaseModel):
    """GET /lessons/{id} response (O3)."""

    id: str
    lesson_type: str
    severity: Optional[str]
    source_event_id: Optional[str]
    source_event_type: str
    source_run_id: Optional[str]
    title: str
    description: str
    proposed_action: Optional[str]
    detected_pattern: Optional[dict[str, Any]]
    status: str
    draft_proposal_id: Optional[str]
    created_at: str
    converted_at: Optional[str]
    deferred_until: Optional[str]


class LessonStatsResponse(BaseModel):
    """Lesson statistics response."""

    total: int
    by_type: dict[str, int]
    by_status: dict[str, int]


@router.get(
    "/lessons",
    response_model=LessonsListResponse,
    summary="List lessons learned (O2)",
    description="""
    Returns paginated list of lessons learned.
    Tenant isolation enforced via auth_context.
    """,
)
async def list_lessons(
    request: Request,
    # Optional filters
    lesson_type: Annotated[
        Optional[str],
        Query(
            description="Filter by type: failure, near_threshold, critical_success",
            pattern="^(failure|near_threshold|critical_success)$",
        ),
    ] = None,
    status: Annotated[
        Optional[str],
        Query(
            description="Filter by status: pending, converted_to_draft, deferred, dismissed",
            pattern="^(pending|converted_to_draft|deferred|dismissed)$",
        ),
    ] = None,
    severity: Annotated[
        Optional[str],
        Query(
            description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW",
            pattern="^(CRITICAL|HIGH|MEDIUM|LOW)$",
        ),
    ] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max lessons to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of lessons to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> LessonsListResponse:
    """List lessons learned (O2). READ-ONLY customer facade."""
    from app.services.lessons_learned_engine import get_lessons_learned_engine

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    if lesson_type:
        filters_applied["lesson_type"] = lesson_type
    if status:
        filters_applied["status"] = status
    if severity:
        filters_applied["severity"] = severity

    engine = get_lessons_learned_engine()
    lessons = engine.list_lessons(
        tenant_id=tenant_id,
        lesson_type=lesson_type,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
    )

    items = [
        LessonSummaryResponse(
            id=lesson["id"],
            lesson_type=lesson["lesson_type"],
            severity=lesson["severity"],
            title=lesson["title"],
            status=lesson["status"],
            source_event_type=lesson["source_event_type"],
            created_at=datetime.fromisoformat(lesson["created_at"]) if lesson["created_at"] else datetime.utcnow(),
            has_proposed_action=lesson["has_proposed_action"],
        )
        for lesson in lessons
    ]

    return LessonsListResponse(
        items=items,
        total=len(items),
        has_more=len(items) == limit,
        filters_applied=filters_applied,
    )


@router.get(
    "/lessons/stats",
    response_model=LessonStatsResponse,
    summary="Get lesson statistics (O1)",
    description="Returns lesson counts by type and status.",
)
async def get_lesson_stats(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LessonStatsResponse:
    """Get lesson statistics (O1). READ-ONLY customer facade."""
    from app.services.lessons_learned_engine import get_lessons_learned_engine

    tenant_id = get_tenant_id_from_auth(request)
    engine = get_lessons_learned_engine()
    stats = engine.get_lesson_stats(tenant_id=tenant_id)

    return LessonStatsResponse(
        total=stats.get("total", 0),
        by_type=stats.get("by_type", {}),
        by_status=stats.get("by_status", {}),
    )


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonDetailResponse,
    summary="Get lesson detail (O3)",
    description="Returns detailed information about a specific lesson.",
)
async def get_lesson_detail(
    request: Request,
    lesson_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LessonDetailResponse:
    """Get lesson detail (O3). READ-ONLY customer facade."""
    from uuid import UUID
    from app.services.lessons_learned_engine import get_lessons_learned_engine

    tenant_id = get_tenant_id_from_auth(request)
    engine = get_lessons_learned_engine()
    lesson = engine.get_lesson(lesson_id=UUID(lesson_id), tenant_id=tenant_id)

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return LessonDetailResponse(
        id=lesson["id"],
        lesson_type=lesson["lesson_type"],
        severity=lesson["severity"],
        source_event_id=lesson["source_event_id"],
        source_event_type=lesson["source_event_type"],
        source_run_id=lesson["source_run_id"],
        title=lesson["title"],
        description=lesson["description"],
        proposed_action=lesson["proposed_action"],
        detected_pattern=lesson["detected_pattern"],
        status=lesson["status"],
        draft_proposal_id=lesson["draft_proposal_id"],
        created_at=lesson["created_at"],
        converted_at=lesson["converted_at"],
        deferred_until=lesson["deferred_until"],
    )


# =============================================================================
# Policy State - ACT-O4 (PIN-411 Gap Closure)
# =============================================================================


class PolicyStateResponse(BaseModel):
    """Policy layer state summary (ACT-O4)."""

    total_policies: int
    active_policies: int
    drafts_pending_review: int
    conflicts_detected: int
    violations_24h: int
    lessons_pending_action: int
    last_updated: datetime


@router.get(
    "/state",
    response_model=PolicyStateResponse,
    summary="Get policy layer state (ACT-O4)",
    description="""
    Returns synthesized snapshot of the governance system.
    Shows what is currently being enforced.
    """,
)
async def get_policy_state(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> PolicyStateResponse:
    """Get policy layer state (ACT-O4). Customer facade."""
    from app.policy.engine import get_policy_engine
    from app.services.lessons_learned_engine import get_lessons_learned_engine

    tenant_id = get_tenant_id_from_auth(request)

    try:
        # Get state from policy engine
        engine = get_policy_engine()
        state = await engine.get_state(session)

        # Get pending lessons count
        lessons_engine = get_lessons_learned_engine()
        lessons_stats = lessons_engine.get_lesson_stats(tenant_id=tenant_id)
        pending_lessons = lessons_stats.get("by_status", {}).get("pending", 0)

        # Get drafts pending (from policy proposals)
        drafts_count = 0
        try:
            from app.models.policy import PolicyProposal
            drafts_result = await session.execute(
                select(func.count(PolicyProposal.id)).where(
                    PolicyProposal.tenant_id == tenant_id,
                    PolicyProposal.status == "pending",
                )
            )
            drafts_count = drafts_result.scalar() or 0
        except Exception:
            pass

        # Get conflicts count
        conflicts_count = 0
        try:
            conflicts = await engine.get_policy_conflicts(session, include_resolved=False)
            conflicts_count = len(conflicts)
        except Exception:
            pass

        return PolicyStateResponse(
            total_policies=state.total_policies,
            active_policies=state.active_policies,
            drafts_pending_review=drafts_count,
            conflicts_detected=conflicts_count,
            violations_24h=state.total_violations_today,
            lessons_pending_action=pending_lessons,
            last_updated=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "state_query_failed", "message": str(e)},
        )


# =============================================================================
# Policy Metrics - ACT-O5 (PIN-411 Gap Closure)
# =============================================================================


class PolicyMetricsResponse(BaseModel):
    """Policy enforcement metrics (ACT-O5)."""

    total_evaluations: int
    total_blocks: int
    total_allows: int
    block_rate: float
    avg_evaluation_ms: float
    violations_by_type: dict[str, int]
    evaluations_by_action: dict[str, int]
    window_hours: int


@router.get(
    "/metrics",
    response_model=PolicyMetricsResponse,
    summary="Get policy metrics (ACT-O5)",
    description="""
    Returns policy enforcement effectiveness metrics.
    Shows how policies are performing.
    """,
)
async def get_policy_metrics(
    request: Request,
    hours: Annotated[int, Query(ge=1, le=720, description="Time window in hours")] = 24,
    session: AsyncSession = Depends(get_async_session_dep),
) -> PolicyMetricsResponse:
    """Get policy metrics (ACT-O5). Customer facade."""
    from app.policy.engine import get_policy_engine

    _ = get_tenant_id_from_auth(request)  # Enforce auth

    try:
        engine = get_policy_engine()
        metrics = await engine.get_metrics(session, hours=hours)

        return PolicyMetricsResponse(
            total_evaluations=metrics.get("total_evaluations", 0),
            total_blocks=metrics.get("total_blocks", 0),
            total_allows=metrics.get("total_allows", 0),
            block_rate=metrics.get("block_rate", 0.0),
            avg_evaluation_ms=metrics.get("avg_evaluation_ms", 0.0),
            violations_by_type=metrics.get("violations_by_type", {}),
            evaluations_by_action=metrics.get("evaluations_by_action", {}),
            window_hours=hours,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "metrics_query_failed", "message": str(e)},
        )


# =============================================================================
# Policy Conflicts - DFT-O4 (PIN-411 Gap Closure)
# Uses PolicyConflictEngine for static conflict detection
# Conflict Types: SCOPE_OVERLAP, THRESHOLD_CONTRADICTION, TEMPORAL_CONFLICT, PRIORITY_OVERRIDE
# =============================================================================


class PolicyConflictResponse(BaseModel):
    """Policy conflict summary (DFT-O4 spec)."""

    policy_a_id: str
    policy_b_id: str
    policy_a_name: str
    policy_b_name: str
    conflict_type: str  # SCOPE_OVERLAP, THRESHOLD_CONTRADICTION, TEMPORAL_CONFLICT, PRIORITY_OVERRIDE
    severity: str  # BLOCKING, WARNING
    explanation: str
    recommended_action: str
    detected_at: datetime


class ConflictsListResponse(BaseModel):
    """GET /conflicts response (DFT-O4)."""

    items: List[PolicyConflictResponse]
    total: int
    unresolved_count: int
    computed_at: datetime


@router.get(
    "/conflicts",
    response_model=ConflictsListResponse,
    summary="Detect policy conflicts (DFT-O4)",
    description="""
    Detects logical contradictions, overlaps, or unsafe coexistence between policies.

    Conflict Types:
    - SCOPE_OVERLAP: Same scope, incompatible behavior
    - THRESHOLD_CONTRADICTION: Limits cannot both be satisfied
    - TEMPORAL_CONFLICT: Time windows clash
    - PRIORITY_OVERRIDE: Lower-priority rule nullifies higher-priority

    Severity:
    - BLOCKING: Activation must be prevented
    - WARNING: Allowed but requires review
    """,
)
async def list_policy_conflicts(
    request: Request,
    policy_id: Annotated[
        Optional[str],
        Query(description="Filter to conflicts involving this policy"),
    ] = None,
    severity: Annotated[
        Optional[str],
        Query(description="Filter by severity: BLOCKING, WARNING"),
    ] = None,
    include_resolved: Annotated[bool, Query(description="Include resolved conflicts")] = False,
    session: AsyncSession = Depends(get_async_session_dep),
) -> ConflictsListResponse:
    """Detect policy conflicts (DFT-O4). Uses PolicyConflictEngine."""
    from app.services.policy_graph_engine import ConflictSeverity, get_conflict_engine

    tenant_id = get_tenant_id_from_auth(request)

    try:
        engine = get_conflict_engine(tenant_id)

        # Parse severity filter
        severity_filter = None
        if severity:
            try:
                severity_filter = ConflictSeverity(severity.upper())
            except ValueError:
                pass

        result = await engine.detect_conflicts(
            session=session,
            policy_id=policy_id,
            severity_filter=severity_filter,
            include_resolved=include_resolved,
        )

        items = [
            PolicyConflictResponse(
                policy_a_id=c.policy_a_id,
                policy_b_id=c.policy_b_id,
                policy_a_name=c.policy_a_name,
                policy_b_name=c.policy_b_name,
                conflict_type=c.conflict_type.value,
                severity=c.severity.value,
                explanation=c.explanation,
                recommended_action=c.recommended_action,
                detected_at=c.detected_at,
            )
            for c in result.conflicts
        ]

        return ConflictsListResponse(
            items=items,
            total=len(items),
            unresolved_count=result.unresolved_count,
            computed_at=result.computed_at,
        )

    except Exception as e:
        logger.exception("Failed to detect policy conflicts")
        raise HTTPException(
            status_code=500,
            detail={"error": "conflicts_detection_failed", "message": str(e)},
        )


# =============================================================================
# Policy Dependencies - DFT-O5 (PIN-411 Gap Closure)
# Uses PolicyDependencyEngine for structural relationship analysis
# Dependency Types: EXPLICIT, IMPLICIT_SCOPE, IMPLICIT_LIMIT
# =============================================================================


class PolicyDependencyRelation(BaseModel):
    """A dependency relationship detail."""

    policy_id: str
    policy_name: str
    dependency_type: str  # EXPLICIT, IMPLICIT_SCOPE, IMPLICIT_LIMIT
    reason: str


class PolicyNodeResponse(BaseModel):
    """A node in the dependency graph (DFT-O5 spec)."""

    id: str
    name: str
    rule_type: str  # SYSTEM, SAFETY, ETHICAL, TEMPORAL
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT
    status: str  # ACTIVE, RETIRED
    enforcement_mode: str  # BLOCK, WARN, AUDIT, DISABLED
    depends_on: List[PolicyDependencyRelation]
    required_by: List[PolicyDependencyRelation]


class PolicyDependencyEdge(BaseModel):
    """A dependency edge in the graph."""

    policy_id: str
    depends_on_id: str
    policy_name: str
    depends_on_name: str
    dependency_type: str  # EXPLICIT, IMPLICIT_SCOPE, IMPLICIT_LIMIT
    reason: str


class DependencyGraphResponse(BaseModel):
    """GET /dependencies response (DFT-O5)."""

    nodes: List[PolicyNodeResponse]
    edges: List[PolicyDependencyEdge]
    nodes_count: int
    edges_count: int
    computed_at: datetime


@router.get(
    "/dependencies",
    response_model=DependencyGraphResponse,
    summary="Get policy dependency graph (DFT-O5)",
    description="""
    Computes structural relationships between policies.

    Dependency Types:
    - EXPLICIT: Declared via parent_rule_id or requires_policy_id
    - IMPLICIT_SCOPE: Same scope, rely on each other's assumptions
    - IMPLICIT_LIMIT: Limit-based dependencies (e.g., cooldown depends on run quota)

    Each node shows:
    - depends_on: Policies this one requires
    - required_by: Policies that depend on this one

    Enforcement Rules:
    - Cannot delete a policy with active required_by
    - Cannot activate a policy if depends_on is inactive
    """,
)
async def get_policy_dependencies(
    request: Request,
    policy_id: Annotated[
        Optional[str],
        Query(description="Filter to dependencies involving this policy"),
    ] = None,
    session: AsyncSession = Depends(get_async_session_dep),
) -> DependencyGraphResponse:
    """Get policy dependency graph (DFT-O5). Uses PolicyDependencyEngine."""
    from app.services.policy_graph_engine import get_dependency_engine

    tenant_id = get_tenant_id_from_auth(request)

    try:
        engine = get_dependency_engine(tenant_id)
        result = await engine.compute_dependency_graph(session, policy_id=policy_id)

        nodes = [
            PolicyNodeResponse(
                id=n.id,
                name=n.name,
                rule_type=n.rule_type,
                scope=n.scope,
                status=n.status,
                enforcement_mode=n.enforcement_mode,
                depends_on=[
                    PolicyDependencyRelation(
                        policy_id=d["policy_id"],
                        policy_name=d["policy_name"],
                        dependency_type=d["type"],
                        reason=d["reason"],
                    )
                    for d in n.depends_on
                ],
                required_by=[
                    PolicyDependencyRelation(
                        policy_id=d["policy_id"],
                        policy_name=d["policy_name"],
                        dependency_type=d["type"],
                        reason=d["reason"],
                    )
                    for d in n.required_by
                ],
            )
            for n in result.nodes
        ]

        edges = [
            PolicyDependencyEdge(
                policy_id=e.policy_id,
                depends_on_id=e.depends_on_id,
                policy_name=e.policy_name,
                depends_on_name=e.depends_on_name,
                dependency_type=e.dependency_type.value,
                reason=e.reason,
            )
            for e in result.edges
        ]

        return DependencyGraphResponse(
            nodes=nodes,
            edges=edges,
            nodes_count=len(nodes),
            edges_count=len(edges),
            computed_at=result.computed_at,
        )

    except Exception as e:
        logger.exception("Failed to compute dependency graph")
        raise HTTPException(
            status_code=500,
            detail={"error": "dependencies_query_failed", "message": str(e)},
        )


# =============================================================================
# Policy Violations - VIO-O1 (PIN-411 Gap Closure - Unified Facade)
# =============================================================================


class PolicyViolationSummary(BaseModel):
    """Policy violation summary (VIO-O1)."""

    id: str
    policy_id: Optional[str]
    policy_name: Optional[str]
    violation_type: str  # cost, quota, rate, temporal, safety, ethical
    severity: float
    source: str  # guard, sim, runtime
    agent_id: Optional[str]
    description: Optional[str]
    occurred_at: datetime
    is_synthetic: bool = False


class ViolationsListResponse(BaseModel):
    """GET /violations response (VIO-O1)."""

    items: List[PolicyViolationSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@router.get(
    "/violations",
    response_model=ViolationsListResponse,
    summary="List policy violations (VIO-O1)",
    description="""
    Returns unified list of policy violations.
    A violation is a normalized governance fact, regardless of origin.
    """,
)
async def list_policy_violations(
    request: Request,
    # Filters
    violation_type: Annotated[
        Optional[str],
        Query(
            description="Filter by type: cost, quota, rate, temporal, safety, ethical",
            pattern="^(cost|quota|rate|temporal|safety|ethical)$",
        ),
    ] = None,
    source: Annotated[
        Optional[str],
        Query(
            description="Filter by source: guard, sim, runtime, cost (PIN-411 Gap Closure)",
            pattern="^(guard|sim|runtime|cost)$",
        ),
    ] = None,
    severity_min: Annotated[
        Optional[float],
        Query(ge=0.0, le=1.0, description="Minimum severity (0.0-1.0)"),
    ] = None,
    violation_kind: Annotated[
        Optional[str],
        Query(
            description="Filter by violation kind: STANDARD, ANOMALY, DIVERGENCE (PIN-411 Gap Closure)",
            pattern="^(STANDARD|ANOMALY|DIVERGENCE)$",
        ),
    ] = None,
    hours: Annotated[int, Query(ge=1, le=720, description="Time window in hours")] = 24,
    include_synthetic: Annotated[bool, Query(description="Include synthetic/simulated")] = False,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max items")] = 50,
    offset: Annotated[int, Query(ge=0, description="Offset")] = 0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> ViolationsListResponse:
    """List policy violations (VIO-O1). Unified customer facade."""
    from app.policy.engine import get_policy_engine

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "hours": hours}

    if violation_type:
        filters_applied["violation_type"] = violation_type
    if source:
        filters_applied["source"] = source
    if severity_min:
        filters_applied["severity_min"] = severity_min
    if violation_kind:
        filters_applied["violation_kind"] = violation_kind

    try:
        engine = get_policy_engine()

        # Convert string violation_type to ViolationType enum if provided
        from app.policy.models import ViolationType as ViolationTypeEnum
        violation_type_enum = None
        if violation_type:
            # Map simplified types to enum values
            type_mapping = {
                "cost": ViolationTypeEnum.RISK_CEILING_BREACH,
                "quota": ViolationTypeEnum.TEMPORAL_LIMIT_EXCEEDED,
                "rate": ViolationTypeEnum.TEMPORAL_LIMIT_EXCEEDED,
                "temporal": ViolationTypeEnum.TEMPORAL_LIMIT_EXCEEDED,
                "safety": ViolationTypeEnum.SAFETY_RULE_TRIGGERED,
                "ethical": ViolationTypeEnum.ETHICAL_VIOLATION,
            }
            violation_type_enum = type_mapping.get(violation_type)

        violations = await engine.get_violations(
            session,
            tenant_id=tenant_id,
            violation_type=violation_type_enum,
            severity_min=severity_min,
            since=datetime.utcnow() - timedelta(hours=hours),
            limit=limit + 1,  # Fetch one extra to check has_more
        )

        # Filter by source if specified
        if source:
            violations = [v for v in violations if getattr(v, "source", "runtime") == source]

        # Filter by violation_kind if specified (PIN-411 Gap Closure)
        if violation_kind:
            violations = [v for v in violations if getattr(v, "violation_kind", "STANDARD") == violation_kind]

        # Filter synthetic
        if not include_synthetic:
            violations = [v for v in violations if not getattr(v, "is_synthetic", False)]

        # Check has_more
        has_more = len(violations) > limit
        violations = violations[:limit]

        items = [
            PolicyViolationSummary(
                id=str(v.id),
                policy_id=getattr(v, "policy_id", None),
                policy_name=getattr(v, "policy_name", None),
                violation_type=str(v.violation_type.value) if hasattr(v.violation_type, "value") else str(v.violation_type),
                severity=v.severity,
                source=getattr(v, "source", "runtime"),
                agent_id=v.agent_id,
                description=getattr(v, "description", None),
                occurred_at=v.detected_at,
                is_synthetic=getattr(v, "is_synthetic", False),
            )
            for v in violations
        ]

        return ViolationsListResponse(
            items=items,
            total=len(items),
            has_more=has_more,
            filters_applied=filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "violations_query_failed", "message": str(e)},
        )


# =============================================================================
# Policy Budgets - THR-O2 (PIN-411 Gap Closure)
# =============================================================================


class BudgetDefinitionSummary(BaseModel):
    """Budget definition summary (THR-O2)."""

    id: str
    name: str
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT
    max_value: Decimal
    reset_period: Optional[str]  # DAILY, WEEKLY, MONTHLY, NONE
    enforcement: str  # BLOCK, WARN
    status: str  # ACTIVE, DISABLED
    current_usage: Optional[Decimal] = None
    utilization_percent: Optional[float] = None


class BudgetsListResponse(BaseModel):
    """GET /budgets response (THR-O2)."""

    items: List[BudgetDefinitionSummary]
    total: int
    filters_applied: dict[str, Any]


@router.get(
    "/budgets",
    response_model=BudgetsListResponse,
    summary="List budget definitions (THR-O2)",
    description="""
    Returns budget definitions (enforcement limits).
    Budgets define spending ceilings, not analytics.
    """,
)
async def list_budget_definitions(
    request: Request,
    scope: Annotated[
        Optional[str],
        Query(
            description="Filter by scope: GLOBAL, TENANT, PROJECT, AGENT",
            pattern="^(GLOBAL|TENANT|PROJECT|AGENT)$",
        ),
    ] = None,
    status: Annotated[
        str,
        Query(
            description="Filter by status: ACTIVE, DISABLED",
            pattern="^(ACTIVE|DISABLED)$",
        ),
    ] = "ACTIVE",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> BudgetsListResponse:
    """List budget definitions (THR-O2). Customer facade."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "status": status}

    if scope:
        filters_applied["scope"] = scope

    try:
        # Query limits where category is BUDGET
        stmt = (
            select(Limit)
            .where(
                and_(
                    Limit.tenant_id == tenant_id,
                    Limit.limit_category == "BUDGET",
                    Limit.status == status,
                )
            )
            .order_by(Limit.created_at.desc())
        )

        if scope:
            stmt = stmt.where(Limit.scope == scope)

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        limits = result.scalars().all()

        items = [
            BudgetDefinitionSummary(
                id=str(lim.id),
                name=lim.name,
                scope=lim.scope,
                max_value=lim.max_value,
                reset_period=lim.reset_period,
                enforcement=lim.enforcement,
                status=lim.status,
                current_usage=None,  # Could add usage query
                utilization_percent=None,
            )
            for lim in limits
        ]

        return BudgetsListResponse(
            items=items,
            total=len(items),
            filters_applied=filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "budgets_query_failed", "message": str(e)},
        )


# =============================================================================
# ACT-O3: Policy Requests (Pending Approvals)
# =============================================================================


class PolicyRequestSummary(BaseModel):
    """Summary of a pending policy request (draft proposal)."""

    id: str
    proposal_name: str
    proposal_type: str
    rationale: str
    proposed_rule: dict
    status: str
    created_at: datetime
    triggering_feedback_count: int
    days_pending: int


class PolicyRequestsListResponse(BaseModel):
    """Response for policy requests list (ACT-O3)."""

    items: List[PolicyRequestSummary]
    total: int
    pending_count: int
    filters_applied: dict


@router.get(
    "/requests",
    response_model=PolicyRequestsListResponse,
    summary="List pending policy requests (ACT-O3)",
    description="""
    Returns pending policy requests (draft proposals awaiting human approval).
    These are recommendations generated by the system that need human review.

    PB-S4 Contract: Proposals are INERT until human approval.
    """,
)
async def list_policy_requests(
    request: Request,
    status: Annotated[
        str,
        Query(
            description="Filter by status: draft, approved, rejected (default: draft)",
            pattern="^(draft|approved|rejected)$",
        ),
    ] = "draft",
    proposal_type: Annotated[
        Optional[str],
        Query(
            description="Filter by proposal type: rate_limit, cost_cap, retry_policy",
        ),
    ] = None,
    days_old: Annotated[
        Optional[int],
        Query(
            ge=1,
            le=365,
            description="Filter to requests older than N days",
        ),
    ] = None,
    include_synthetic: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: AsyncSession = Depends(get_async_session_dep),
) -> PolicyRequestsListResponse:
    """List pending policy requests (ACT-O3). Customer facade."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "status": status}

    if proposal_type:
        filters_applied["proposal_type"] = proposal_type
    if days_old:
        filters_applied["days_old"] = days_old
    if include_synthetic:
        filters_applied["include_synthetic"] = True

    try:
        # Import here to avoid circular imports
        from app.models.policy import PolicyProposal

        now = datetime.now(timezone.utc)

        # Build query for policy proposals
        stmt = select(PolicyProposal).where(
            and_(
                PolicyProposal.tenant_id == tenant_id,
                PolicyProposal.status == status,
            )
        )

        # Filter synthetic data
        if not include_synthetic:
            stmt = stmt.where(
                (PolicyProposal.is_synthetic == False) | (PolicyProposal.is_synthetic.is_(None))
            )

        # Filter by proposal type
        if proposal_type:
            stmt = stmt.where(PolicyProposal.proposal_type == proposal_type)

        # Filter by age
        if days_old:
            cutoff = now - timedelta(days=days_old)
            stmt = stmt.where(PolicyProposal.created_at <= cutoff)

        # Count total pending (for the pending_count metric)
        count_stmt = select(func.count()).select_from(PolicyProposal).where(
            and_(
                PolicyProposal.tenant_id == tenant_id,
                PolicyProposal.status == "draft",
                (PolicyProposal.is_synthetic == False) | (PolicyProposal.is_synthetic.is_(None)),
            )
        )
        count_result = await session.execute(count_stmt)
        pending_count = count_result.scalar() or 0

        # Execute main query with pagination
        stmt = stmt.order_by(PolicyProposal.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        proposals = result.scalars().all()

        items = []
        for prop in proposals:
            # Calculate days pending
            created = prop.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            days_pending = (now - created).days

            # Count triggering feedback
            feedback_ids = prop.triggering_feedback_ids or []
            feedback_count = len(feedback_ids) if isinstance(feedback_ids, list) else 0

            items.append(
                PolicyRequestSummary(
                    id=str(prop.id),
                    proposal_name=prop.proposal_name,
                    proposal_type=prop.proposal_type,
                    rationale=prop.rationale,
                    proposed_rule=prop.proposed_rule or {},
                    status=prop.status,
                    created_at=prop.created_at,
                    triggering_feedback_count=feedback_count,
                    days_pending=days_pending,
                )
            )

        return PolicyRequestsListResponse(
            items=items,
            total=len(items),
            pending_count=pending_count,
            filters_applied=filters_applied,
        )

    except Exception as e:
        logger.exception("Failed to list policy requests")
        raise HTTPException(
            status_code=500,
            detail={"error": "policy_requests_query_failed", "message": str(e)},
        )
