# capability_id: CAP-009
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: Persistence driver for policies facade — all SQL queries for policy rules, limits, budgets, requests
# Temporal:
#   Trigger: engine
#   Execution: async (DB operations)
# Callers: policies_facade.py (L5 Engine)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-512 Category B — extracted from legacy app.services.policies_facade

"""
PoliciesFacadeDriver (L6)

Pure data access for the policies facade. Contains all SQL queries
previously embedded in the legacy PoliciesFacade class.

Methods return raw dicts/scalars — the L5 facade maps to result types.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_control_plane import (
    Limit,
    LimitBreach,
    LimitIntegrity,
    PolicyEnforcement,
    PolicyRule,
    PolicyRuleIntegrity,
)


class PoliciesFacadeDriver:
    """L6 driver for policies facade SQL operations."""

    # -------------------------------------------------------------------------
    # Policy Rules
    # -------------------------------------------------------------------------

    async def fetch_policy_rules(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: str = "ACTIVE",
        enforcement_mode: Optional[str] = None,
        scope: Optional[str] = None,
        source: Optional[str] = None,
        rule_type: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch policy rules with enforcement stats. Returns {items, total}."""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

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
            .join(PolicyRuleIntegrity, PolicyRuleIntegrity.rule_id == PolicyRule.id)
            .outerjoin(enforcement_stats_subq, enforcement_stats_subq.c.rule_id == PolicyRule.id)
            .where(
                and_(
                    PolicyRule.tenant_id == tenant_id,
                    PolicyRule.status == status,
                )
            )
            .order_by(
                enforcement_stats_subq.c.last_triggered_at.desc().nullslast(),
                PolicyRule.created_at.desc(),
                PolicyRule.id.desc(),
            )
        )

        # Apply optional filters
        if enforcement_mode is not None:
            stmt = stmt.where(PolicyRule.enforcement_mode == enforcement_mode)
        if scope is not None:
            stmt = stmt.where(PolicyRule.scope == scope)
        if source is not None:
            stmt = stmt.where(PolicyRule.source == source)
        if rule_type is not None:
            stmt = stmt.where(PolicyRule.rule_type == rule_type)
        if created_after is not None:
            stmt = stmt.where(PolicyRule.created_at >= created_after)
        if created_before is not None:
            stmt = stmt.where(PolicyRule.created_at <= created_before)

        # Count total
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

        return {"items": rows, "total": total}

    async def fetch_policy_rule_detail(
        self,
        session: AsyncSession,
        tenant_id: str,
        rule_id: str,
    ) -> Optional[dict[str, Any]]:
        """Fetch policy rule detail with enforcement stats. Returns dict or None."""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

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
            return None

        rule = row[0]
        return {
            "rule": rule,
            "integrity_status": row[1],
            "integrity_score": row[2],
            "trigger_count_30d": row[3],
            "last_triggered_at": row[4],
        }

    # -------------------------------------------------------------------------
    # Limits
    # -------------------------------------------------------------------------

    async def fetch_limits(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        category: str = "BUDGET",
        status: str = "ACTIVE",
        scope: Optional[str] = None,
        enforcement: Optional[str] = None,
        limit_type: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch limits with breach stats. Returns {items, total}."""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

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

        if scope is not None:
            stmt = stmt.where(Limit.scope == scope)
        if enforcement is not None:
            stmt = stmt.where(Limit.enforcement == enforcement)
        if limit_type is not None:
            if limit_type.endswith("*"):
                prefix = limit_type[:-1]
                stmt = stmt.where(Limit.limit_type.startswith(prefix))
            else:
                stmt = stmt.where(Limit.limit_type == limit_type)
        if created_after is not None:
            stmt = stmt.where(Limit.created_at >= created_after)
        if created_before is not None:
            stmt = stmt.where(Limit.created_at <= created_before)

        # Count total
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

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = [dict(row._mapping) for row in result.all()]

        return {"items": rows, "total": total}

    async def fetch_limit_detail(
        self,
        session: AsyncSession,
        tenant_id: str,
        limit_id: str,
    ) -> Optional[dict[str, Any]]:
        """Fetch limit detail with breach stats. Returns dict or None."""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

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
            return None

        lim = row[0]
        return {
            "limit": lim,
            "integrity_status": row[1],
            "integrity_score": row[2],
            "breach_count_30d": row[3],
            "last_breached_at": row[4],
        }

    # -------------------------------------------------------------------------
    # Policy Requests (Proposals)
    # -------------------------------------------------------------------------

    async def fetch_policy_requests(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: str = "draft",
        proposal_type: Optional[str] = None,
        days_old: Optional[int] = None,
        include_synthetic: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch policy requests. Returns {items (ORM objects), pending_count}."""
        from app.models.policy import PolicyProposal

        now = datetime.now(timezone.utc)

        stmt = select(PolicyProposal).where(
            and_(
                PolicyProposal.tenant_id == tenant_id,
                PolicyProposal.status == status,
            )
        )

        if not include_synthetic:
            stmt = stmt.where(
                (PolicyProposal.is_synthetic == False) | (PolicyProposal.is_synthetic.is_(None))  # noqa: E712
            )
        if proposal_type:
            stmt = stmt.where(PolicyProposal.proposal_type == proposal_type)
        if days_old:
            cutoff = now - timedelta(days=days_old)
            stmt = stmt.where(PolicyProposal.created_at <= cutoff)

        # Count pending
        count_stmt = select(func.count()).select_from(PolicyProposal).where(
            and_(
                PolicyProposal.tenant_id == tenant_id,
                PolicyProposal.status == "draft",
                (PolicyProposal.is_synthetic == False) | (PolicyProposal.is_synthetic.is_(None)),  # noqa: E712
            )
        )
        count_result = await session.execute(count_stmt)
        pending_count = count_result.scalar() or 0

        stmt = stmt.order_by(PolicyProposal.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        proposals = result.scalars().all()

        return {"items": proposals, "pending_count": pending_count}

    # -------------------------------------------------------------------------
    # Budget Definitions
    # -------------------------------------------------------------------------

    async def fetch_budgets(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        scope: Optional[str] = None,
        status: str = "ACTIVE",
        limit: int = 20,
        offset: int = 0,
    ) -> list[Any]:
        """Fetch budget definitions (Limit with category=BUDGET). Returns list of ORM objects."""
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
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Pending Drafts Count (for policy state)
    # -------------------------------------------------------------------------

    async def count_pending_drafts(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> int:
        """Count pending draft proposals for policy state summary."""
        from app.models.policy import PolicyProposal

        try:
            result = await session.execute(
                select(func.count(PolicyProposal.id)).where(
                    PolicyProposal.tenant_id == tenant_id,
                    PolicyProposal.status == "pending",
                )
            )
            return result.scalar() or 0
        except Exception:
            return 0
