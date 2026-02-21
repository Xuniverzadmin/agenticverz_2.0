# capability_id: CAP-009
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policy_rules, policy_rule_integrity, policy_enforcements (via driver)
#   Writes: none
# Role: Policy rules query engine - read-only operations for policy rules
# Callers: L2 policies API
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, Phase 3B P3 Design-First
"""
Policy Rules Query Engine (L5)

Read-only query operations for policy rules.
Provides list, get detail, filtering, and counts.

Invariant: This engine is READ-ONLY. No writes. No state mutation.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from app.hoc.cus.policies.L6_drivers.policy_rules_read_driver import (
    PolicyRulesReadDriver,
    get_policy_rules_read_driver,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class PolicyRuleSummaryResult:
    """Policy rule summary for list view (O2)."""

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


@dataclass
class PolicyRulesListResult:
    """Policy rules list response."""

    items: list[PolicyRuleSummaryResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class PolicyRuleDetailResult:
    """Policy rule detail response (O3)."""

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
    rule_definition: Optional[dict] = None
    violation_count_total: int = 0


# =============================================================================
# Query Engine
# =============================================================================


class PolicyRulesQueryEngine:
    """
    L5 Query Engine for policy rules.

    Provides read-only operations:
    - List rules with filters
    - Get rule detail
    - Count rules

    All data access is delegated to L6 driver.
    """

    def __init__(self, driver: PolicyRulesReadDriver):
        self._driver = driver

    async def list_policy_rules(
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
    ) -> PolicyRulesListResult:
        """List policy rules for the tenant."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "status": status}

        if enforcement_mode:
            filters_applied["enforcement_mode"] = enforcement_mode
        if scope:
            filters_applied["scope"] = scope
        if source:
            filters_applied["source"] = source
        if rule_type:
            filters_applied["rule_type"] = rule_type
        if created_after:
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            filters_applied["created_before"] = created_before.isoformat()

        # Fetch from driver
        rows, total = await self._driver.fetch_policy_rules(
            tenant_id=tenant_id,
            status=status,
            enforcement_mode=enforcement_mode,
            scope=scope,
            source=source,
            rule_type=rule_type,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
        )

        # Transform to result objects
        items = [
            PolicyRuleSummaryResult(
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

        return PolicyRulesListResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    async def get_policy_rule_detail(
        self,
        tenant_id: str,
        rule_id: str,
    ) -> Optional[PolicyRuleDetailResult]:
        """Get policy rule detail. Tenant isolation enforced."""
        row = await self._driver.fetch_policy_rule_by_id(tenant_id, rule_id)

        if not row:
            return None

        return PolicyRuleDetailResult(
            rule_id=row["rule_id"],
            name=row["name"],
            description=row["description"],
            enforcement_mode=row["enforcement_mode"],
            scope=row["scope"],
            source=row["source"],
            status=row["status"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            updated_at=row["updated_at"],
            integrity_status=row["integrity_status"],
            integrity_score=row["integrity_score"],
            trigger_count_30d=row["trigger_count_30d"],
            last_triggered_at=row["last_triggered_at"],
            rule_definition=row["rule_definition"],
            violation_count_total=0,
        )

    async def count_rules(
        self,
        tenant_id: str,
        status: str = "ACTIVE",
    ) -> int:
        """Count policy rules for tenant."""
        return await self._driver.count_policy_rules(tenant_id, status)


# =============================================================================
# Factory
# =============================================================================


def get_policy_rules_query_engine(
    session: "AsyncSession",
) -> PolicyRulesQueryEngine:
    """Get a PolicyRulesQueryEngine instance."""
    return PolicyRulesQueryEngine(
        driver=get_policy_rules_read_driver(session),
    )


__all__ = [
    # Engine
    "PolicyRulesQueryEngine",
    "get_policy_rules_query_engine",
    # Result types
    "PolicyRuleSummaryResult",
    "PolicyRulesListResult",
    "PolicyRuleDetailResult",
]
