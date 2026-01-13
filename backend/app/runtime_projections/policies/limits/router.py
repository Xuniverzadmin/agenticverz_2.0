# Layer: L2 — Product APIs
# Product: ai-console
# Temporal:
#   Trigger: HTTP request
#   Execution: async
# Role: Limits O2 Runtime Projection API (LIM-RT-O2)
# Callers: Customer Console Policies › Limits List
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-412 Domain Design

"""
LIM-RT-O2 — Limits Runtime Projection Contract (LOCKED)

Deterministic, index-backed, read-only list view for Limits.
Follows the exact pattern established by Governance O2.

Contract Rules:
- Tenant isolation is mandatory (from auth_context)
- Only indexed filters allowed
- Integrity comes from limit_integrity (1:1 join)
- Breach stats from limit_breaches (aggregation subquery)
- Pagination is non-negotiable
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.policy_control_plane import (
    Limit,
    LimitIntegrity,
    LimitBreach,
)
from app.auth.tenant_auth import TenantContext, get_tenant_context

router = APIRouter(prefix="/limits", tags=["runtime-limits"])


# =============================================================================
# Response Models (LIM-RT-O2 Contract Shape - EXACT)
# =============================================================================


class LimitSummary(BaseModel):
    """
    O2 Result Shape (EXACT from contract).
    No extra fields. No missing fields. No renaming.
    """

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


class LimitsO2Response(BaseModel):
    """
    Response envelope (contract mandates this structure).
    Backend MUST return this shape even for empty results.
    """

    items: List[LimitSummary]
    total: int
    has_more: bool


# =============================================================================
# Query Function (LIM-RT-O2 - EXACT from contract)
# =============================================================================


async def query_limits_o2(
    *,
    session: AsyncSession,
    tenant_id: str,
    limit_category: str,
    status: str,
    limit: int,
    offset: int,
    scope: Optional[str] = None,
    enforcement: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> List[dict]:
    """
    LIM-RT-O2
    Deterministic, index-backed limits list query.
    Matches contract exactly.
    """

    # Time window for breach stats (30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # Subquery: breach aggregation (indexed)
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
            # Core limit fields
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
            # Integrity (mandatory for ACTIVE limits)
            LimitIntegrity.integrity_status,
            LimitIntegrity.integrity_score,
            # Derived breach metrics (nullable)
            func.coalesce(
                breach_agg_subq.c.breach_count_30d, 0
            ).label("breach_count_30d"),
            breach_agg_subq.c.last_breached_at,
            # Metadata
            Limit.created_at,
        )
        .select_from(Limit)
        # Integrity JOIN (EXACTLY one row guaranteed)
        .join(
            LimitIntegrity,
            LimitIntegrity.limit_id == Limit.id,
        )
        # Breach aggregation (LEFT JOIN)
        .outerjoin(
            breach_agg_subq,
            breach_agg_subq.c.limit_id == Limit.id,
        )
        # Required filters
        .where(
            and_(
                Limit.tenant_id == tenant_id,
                Limit.limit_category == limit_category,
                Limit.status == status,
            )
        )
        # Ordering: most recently breached first, then by created_at
        .order_by(
            breach_agg_subq.c.last_breached_at.desc().nullslast(),
            Limit.created_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    # Optional indexed filters
    if scope is not None:
        stmt = stmt.where(Limit.scope == scope)

    if enforcement is not None:
        stmt = stmt.where(Limit.enforcement == enforcement)

    if created_after is not None:
        stmt = stmt.where(Limit.created_at >= created_after)

    if created_before is not None:
        stmt = stmt.where(Limit.created_at <= created_before)

    result = await session.execute(stmt)
    return [dict(row._mapping) for row in result.all()]


async def count_limits_o2(
    *,
    session: AsyncSession,
    tenant_id: str,
    limit_category: str,
    status: str,
    scope: Optional[str] = None,
    enforcement: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> int:
    """
    Count query for pagination metadata.
    Uses same filters as main query.
    """

    stmt = (
        select(func.count(Limit.id))
        .where(Limit.tenant_id == tenant_id)
        .where(Limit.limit_category == limit_category)
        .where(Limit.status == status)
    )

    if scope is not None:
        stmt = stmt.where(Limit.scope == scope)

    if enforcement is not None:
        stmt = stmt.where(Limit.enforcement == enforcement)

    if created_after is not None:
        stmt = stmt.where(Limit.created_at >= created_after)

    if created_before is not None:
        stmt = stmt.where(Limit.created_at <= created_before)

    result = await session.execute(stmt)
    return result.scalar() or 0


# =============================================================================
# API Endpoint (Minimal FastAPI Glue)
# =============================================================================


@router.get("", response_model=LimitsO2Response)
async def list_limits(
    # Category filter (required per contract)
    category: str = Query(
        ...,
        alias="type",
        description="Limit category: BUDGET, RATE, or THRESHOLD",
        regex="^(BUDGET|RATE|THRESHOLD)$",
    ),
    # Status filter (defaults to ACTIVE)
    status: str = Query(
        "ACTIVE",
        description="Limit status: ACTIVE or DISABLED",
        regex="^(ACTIVE|DISABLED)$",
    ),
    # Pagination (mandatory)
    limit: int = Query(20, ge=1, le=100, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
    # Optional indexed filters
    scope: Optional[str] = Query(
        None,
        description="Filter by scope: GLOBAL, TENANT, PROJECT, AGENT, PROVIDER",
        regex="^(GLOBAL|TENANT|PROJECT|AGENT|PROVIDER)$",
    ),
    enforcement: Optional[str] = Query(
        None,
        description="Filter by enforcement: BLOCK, WARN, REJECT, QUEUE, DEGRADE, ALERT",
        regex="^(BLOCK|WARN|REJECT|QUEUE|DEGRADE|ALERT)$",
    ),
    created_after: Optional[datetime] = Query(None, description="Filter by created_at >= value"),
    created_before: Optional[datetime] = Query(None, description="Filter by created_at <= value"),
    # Dependencies
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session),
):
    """
    GET /api/v1/runtime/policies/limits?type={BUDGET|RATE|THRESHOLD}

    LIM-RT-O2: Limits Runtime Projection

    Returns limits matching the specified category and filters.
    Includes integrity status and breach statistics.
    Tenant isolation is enforced from auth context.
    """

    # Query limits with integrity and breach stats
    rows = await query_limits_o2(
        session=session,
        tenant_id=tenant.tenant_id,
        limit_category=category,
        status=status,
        limit=limit,
        offset=offset,
        scope=scope,
        enforcement=enforcement,
        created_after=created_after,
        created_before=created_before,
    )

    # Get total count for pagination
    total = await count_limits_o2(
        session=session,
        tenant_id=tenant.tenant_id,
        limit_category=category,
        status=status,
        scope=scope,
        enforcement=enforcement,
        created_after=created_after,
        created_before=created_before,
    )

    # Transform to O2 response shape (EXACT)
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

    return LimitsO2Response(
        items=items,
        total=total,
        has_more=(offset + len(items)) < total,
    )
