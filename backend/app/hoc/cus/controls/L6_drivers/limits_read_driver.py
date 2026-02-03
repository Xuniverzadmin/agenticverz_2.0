# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: internal
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: limits, limit_integrity, limit_breaches
#   Writes: none
# Role: Read operations for limits
# Callers: L5 policies_limits_query_engine
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Phase 3B P3 Design-First
"""
Limits Read Driver (L6)

Pure data access layer for limits read operations.
All SQLAlchemy queries live here. No business logic.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.hoc.cus.hoc_spine.services.time import utc_now
from app.models.policy_control_plane import Limit, LimitBreach, LimitIntegrity


class LimitsReadDriver:
    """Read operations for limits."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_limits(
        self,
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
    ) -> tuple[list[dict], int]:
        """
        Fetch limits with filters and pagination.

        Returns (items, total_count).
        """
        thirty_days_ago = utc_now() - timedelta(days=30)

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
                func.coalesce(breach_agg_subq.c.breach_count_30d, 0).label(
                    "breach_count_30d"
                ),
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

        # Apply optional filters
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

        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        rows = [dict(row._mapping) for row in result.all()]

        return rows, total

    async def fetch_limit_by_id(
        self,
        tenant_id: str,
        limit_id: str,
    ) -> Optional[dict]:
        """Fetch limit detail. Returns None if not found."""
        thirty_days_ago = utc_now() - timedelta(days=30)

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
                func.coalesce(breach_agg_subq.c.breach_count_30d, 0).label(
                    "breach_count_30d"
                ),
                breach_agg_subq.c.last_breached_at,
            )
            .join(LimitIntegrity, LimitIntegrity.limit_id == Limit.id)
            .outerjoin(breach_agg_subq, breach_agg_subq.c.limit_id == Limit.id)
            .where(
                Limit.id == limit_id,
                Limit.tenant_id == tenant_id,
            )
        )

        result = await self._session.execute(stmt)
        row = result.first()

        if not row:
            return None

        lim = row[0]

        return {
            "limit_id": lim.id,
            "name": lim.name,
            "description": getattr(lim, "description", None),
            "limit_category": lim.limit_category,
            "limit_type": lim.limit_type,
            "scope": lim.scope,
            "enforcement": lim.enforcement,
            "status": lim.status,
            "max_value": lim.max_value,
            "window_seconds": lim.window_seconds,
            "reset_period": lim.reset_period,
            "integrity_status": row[1],
            "integrity_score": row[2],
            "breach_count_30d": row[3],
            "last_breached_at": row[4],
            "created_at": lim.created_at,
            "updated_at": getattr(lim, "updated_at", None),
        }

    async def fetch_budget_limits(
        self,
        tenant_id: str,
        scope: Optional[str] = None,
        status: str = "ACTIVE",
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """Fetch budget definitions for tenant."""
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
        result = await self._session.execute(stmt)
        limits = result.scalars().all()

        return [
            {
                "id": str(lim.id),
                "name": lim.name,
                "scope": lim.scope,
                "max_value": lim.max_value,
                "reset_period": lim.reset_period,
                "enforcement": lim.enforcement,
                "status": lim.status,
            }
            for lim in limits
        ]

    async def fetch_limit_breaches_for_run(
        self,
        tenant_id: str,
        run_id: str,
        max_results: int = 100,
    ) -> list[dict]:
        """
        Fetch all limit breaches associated with a run (PIN-519).

        Args:
            tenant_id: Tenant owning the run
            run_id: Run ID to query breaches for
            max_results: Maximum breaches to return

        Returns:
            List of breach records with limit details
        """
        stmt = (
            select(
                LimitBreach.id.label("breach_id"),
                LimitBreach.limit_id,
                LimitBreach.value_at_breach,
                LimitBreach.limit_value,
                LimitBreach.breached_at,
                Limit.name.label("limit_name"),
                Limit.max_value.label("threshold_value"),
                Limit.limit_type,
            )
            .join(Limit, Limit.id == LimitBreach.limit_id)
            .where(
                and_(
                    LimitBreach.tenant_id == tenant_id,
                    LimitBreach.run_id == run_id,
                )
            )
            .order_by(LimitBreach.breached_at.desc())
            .limit(max_results)
        )

        result = await self._session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]


def get_limits_read_driver(session: AsyncSession) -> LimitsReadDriver:
    """Factory function for LimitsReadDriver."""
    return LimitsReadDriver(session)


__all__ = [
    "LimitsReadDriver",
    "get_limits_read_driver",
]
