# Layer: L2 — Product APIs
# Product: ai-console
# Temporal:
#   Trigger: HTTP request
#   Execution: async
# Role: Governance O2 Runtime Projection API (GOV-RT-O2)
# Callers: Customer Console Policies › Governance List
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-412 Domain Design

"""
GOV-RT-O2 — Governance Runtime Projection Contract (LOCKED)

Deterministic, index-backed, read-only list view for Policy Rules.
Follows the exact pattern established by Incidents O2.

Contract Rules:
- Tenant isolation is mandatory (from auth_context)
- Only indexed filters allowed
- Integrity comes from policy_rule_integrity (1:1 join)
- Trigger stats from policy_enforcements (aggregation subquery)
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
    PolicyRule,
    PolicyRuleIntegrity,
    PolicyEnforcement,
)
from app.auth.tenant_auth import TenantContext, get_tenant_context

router = APIRouter(prefix="/rules", tags=["runtime-governance"])


# =============================================================================
# Response Models (GOV-RT-O2 Contract Shape - EXACT)
# =============================================================================


class PolicyRuleSummary(BaseModel):
    """
    O2 Result Shape (EXACT from contract).
    No extra fields. No missing fields. No renaming.
    """

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


class GovernanceO2Response(BaseModel):
    """
    Response envelope (contract mandates this structure).
    Backend MUST return this shape even for empty results.
    """

    items: List[PolicyRuleSummary]
    total: int
    has_more: bool


# =============================================================================
# Query Function (GOV-RT-O2 - EXACT from contract)
# =============================================================================


async def query_governance_rules_o2(
    *,
    session: AsyncSession,
    tenant_id: str,
    status: str,
    limit: int,
    offset: int,
    enforcement_mode: Optional[str] = None,
    scope: Optional[str] = None,
    source: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> List[dict]:
    """
    GOV-RT-O2
    Deterministic, index-backed governance rules list query.
    Matches contract exactly.
    """

    # Time window for trigger stats (30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # Subquery: enforcement aggregation (indexed)
    # Note: Uses triggered_at per actual schema
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
            func.coalesce(
                enforcement_stats_subq.c.trigger_count_30d, 0
            ).label("trigger_count_30d"),
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
        .limit(limit)
        .offset(offset)
    )

    # Optional indexed filters
    if enforcement_mode is not None:
        stmt = stmt.where(PolicyRule.enforcement_mode == enforcement_mode)

    if scope is not None:
        stmt = stmt.where(PolicyRule.scope == scope)

    if source is not None:
        stmt = stmt.where(PolicyRule.source == source)

    if created_after is not None:
        stmt = stmt.where(PolicyRule.created_at >= created_after)

    if created_before is not None:
        stmt = stmt.where(PolicyRule.created_at <= created_before)

    result = await session.execute(stmt)
    return [dict(row._mapping) for row in result.all()]


async def count_governance_rules_o2(
    *,
    session: AsyncSession,
    tenant_id: str,
    status: str,
    enforcement_mode: Optional[str] = None,
    scope: Optional[str] = None,
    source: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> int:
    """
    Count query for pagination metadata.
    Uses same filters as main query.
    """

    stmt = (
        select(func.count(PolicyRule.id))
        .where(PolicyRule.tenant_id == tenant_id)
        .where(PolicyRule.status == status)
    )

    if enforcement_mode is not None:
        stmt = stmt.where(PolicyRule.enforcement_mode == enforcement_mode)

    if scope is not None:
        stmt = stmt.where(PolicyRule.scope == scope)

    if source is not None:
        stmt = stmt.where(PolicyRule.source == source)

    if created_after is not None:
        stmt = stmt.where(PolicyRule.created_at >= created_after)

    if created_before is not None:
        stmt = stmt.where(PolicyRule.created_at <= created_before)

    result = await session.execute(stmt)
    return result.scalar() or 0


# =============================================================================
# API Endpoint (Minimal FastAPI Glue)
# =============================================================================


@router.get("", response_model=GovernanceO2Response)
async def list_governance_rules(
    # Status filter (required per contract)
    status: str = Query(
        ...,
        description="Rule status: ACTIVE or RETIRED",
        regex="^(ACTIVE|RETIRED)$",
    ),
    # Pagination (mandatory)
    limit: int = Query(20, ge=1, le=100, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
    # Optional indexed filters
    enforcement_mode: Optional[str] = Query(
        None,
        description="Filter by enforcement mode: BLOCK, WARN, AUDIT, DISABLED",
        regex="^(BLOCK|WARN|AUDIT|DISABLED)$",
    ),
    scope: Optional[str] = Query(
        None,
        description="Filter by scope: GLOBAL, TENANT, PROJECT, AGENT",
        regex="^(GLOBAL|TENANT|PROJECT|AGENT)$",
    ),
    source: Optional[str] = Query(
        None,
        description="Filter by source: MANUAL, SYSTEM, LEARNED",
        regex="^(MANUAL|SYSTEM|LEARNED)$",
    ),
    created_after: Optional[datetime] = Query(None, description="Filter by created_at >= value"),
    created_before: Optional[datetime] = Query(None, description="Filter by created_at <= value"),
    # Dependencies
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session),
):
    """
    GET /api/v1/runtime/policies/rules

    GOV-RT-O2: Governance Runtime Projection

    Returns policy rules matching the specified status and filters.
    Includes integrity status and trigger statistics.
    Tenant isolation is enforced from auth context.
    """

    # Query rules with integrity and trigger stats
    rows = await query_governance_rules_o2(
        session=session,
        tenant_id=tenant.tenant_id,
        status=status,
        limit=limit,
        offset=offset,
        enforcement_mode=enforcement_mode,
        scope=scope,
        source=source,
        created_after=created_after,
        created_before=created_before,
    )

    # Get total count for pagination
    total = await count_governance_rules_o2(
        session=session,
        tenant_id=tenant.tenant_id,
        status=status,
        enforcement_mode=enforcement_mode,
        scope=scope,
        source=source,
        created_after=created_after,
        created_before=created_before,
    )

    # Transform to O2 response shape (EXACT)
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

    return GovernanceO2Response(
        items=items,
        total=total,
        has_more=(offset + len(items)) < total,
    )
