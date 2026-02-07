# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: internal
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policy_rules, policy_rule_integrity, policy_enforcements
#   Writes: none
# Role: Read operations for policy rules
# Callers: L5 policies_rules_query_engine
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Phase 3B P3 Design-First
"""
Policy Rules Read Driver (L6)

Pure data access layer for policy rules read operations.
All SQLAlchemy queries live here. No business logic.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_control_plane import (
    PolicyEnforcement,
    PolicyRule,
    PolicyRuleIntegrity,
)


class PolicyRulesReadDriver:
    """Read operations for policy rules."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_policy_rules(
        self,
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
    ) -> tuple[list[dict], int]:
        """
        Fetch policy rules with filters and pagination.

        Returns (items, total_count).
        """
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

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
                func.coalesce(enforcement_stats_subq.c.trigger_count_30d, 0).label(
                    "trigger_count_30d"
                ),
                enforcement_stats_subq.c.last_triggered_at,
            )
            .join(PolicyRuleIntegrity, PolicyRuleIntegrity.rule_id == PolicyRule.id)
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
            count_stmt = count_stmt.where(
                PolicyRule.enforcement_mode == enforcement_mode
            )
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

        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        rows = [dict(row._mapping) for row in result.all()]

        return rows, total

    async def fetch_policy_rule_by_id(
        self,
        tenant_id: str,
        rule_id: str,
    ) -> Optional[dict]:
        """Fetch policy rule detail. Returns None if not found."""
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

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
                func.coalesce(enforcement_stats_subq.c.trigger_count_30d, 0).label(
                    "trigger_count_30d"
                ),
                enforcement_stats_subq.c.last_triggered_at,
            )
            .join(PolicyRuleIntegrity, PolicyRuleIntegrity.rule_id == PolicyRule.id)
            .outerjoin(
                enforcement_stats_subq,
                enforcement_stats_subq.c.rule_id == PolicyRule.id,
            )
            .where(
                PolicyRule.id == rule_id,
                PolicyRule.tenant_id == tenant_id,
            )
        )

        result = await self._session.execute(stmt)
        row = result.first()

        if not row:
            return None

        rule = row[0]  # PolicyRule model

        return {
            "rule_id": rule.id,
            "name": rule.name,
            "description": getattr(rule, "description", None),
            "enforcement_mode": rule.enforcement_mode,
            "scope": rule.scope,
            "source": rule.source,
            "status": rule.status,
            "created_at": rule.created_at,
            "created_by": rule.created_by,
            "updated_at": getattr(rule, "updated_at", None),
            "integrity_status": row[1],
            "integrity_score": row[2],
            "trigger_count_30d": row[3],
            "last_triggered_at": row[4],
            "rule_definition": getattr(rule, "rule_definition", None),
        }

    async def count_policy_rules(
        self,
        tenant_id: str,
        status: str = "ACTIVE",
    ) -> int:
        """Count policy rules for tenant."""
        result = await self._session.execute(
            select(func.count(PolicyRule.id)).where(
                PolicyRule.tenant_id == tenant_id,
                PolicyRule.status == status,
            )
        )
        return result.scalar() or 0


def get_policy_rules_read_driver(session: AsyncSession) -> PolicyRulesReadDriver:
    """Factory function for PolicyRulesReadDriver."""
    return PolicyRulesReadDriver(session)


__all__ = [
    "PolicyRulesReadDriver",
    "get_policy_rules_read_driver",
]
