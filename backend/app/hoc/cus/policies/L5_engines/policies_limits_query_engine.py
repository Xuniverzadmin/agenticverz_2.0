# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: limits, limit_integrity, limit_breaches (via driver)
#   Writes: none
# Role: Limits query engine - read-only operations for limits
# Callers: L2 policies API
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, Phase 3B P3 Design-First
"""
Limits Query Engine (L5)

Read-only query operations for limits and budget definitions.
Provides list, get detail, filtering, and budget queries.

Invariant: This engine is READ-ONLY. No writes. No state mutation.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

# PIN-504: Driver injected by L4 handler via DomainBridge (no cross-domain module-level import)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class LimitSummaryResult:
    """Limit summary for list view (O2)."""

    limit_id: str
    name: str
    limit_category: str  # BUDGET, RATE, THRESHOLD
    limit_type: str  # COST_USD, TOKENS_*, REQUESTS_*, etc.
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT, PROVIDER
    enforcement: str  # BLOCK, WARN, REJECT, QUEUE, DEGRADE, ALERT
    status: str  # ACTIVE, DISABLED
    max_value: Decimal
    window_seconds: Optional[int]
    reset_period: Optional[str]  # DAILY, WEEKLY, MONTHLY, NONE
    integrity_status: str
    integrity_score: Decimal
    breach_count_30d: int
    last_breached_at: Optional[datetime]
    created_at: datetime


@dataclass
class LimitsListResult:
    """Limits list response."""

    items: list[LimitSummaryResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class LimitDetailResult:
    """Limit detail response (O3)."""

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
    current_value: Optional[Decimal] = None
    utilization_percent: Optional[float] = None


@dataclass
class BudgetDefinitionResult:
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


@dataclass
class BudgetsListResult:
    """Budget definitions list response."""

    items: list[BudgetDefinitionResult]
    total: int
    filters_applied: dict[str, Any]


# =============================================================================
# Query Engine
# =============================================================================


class LimitsQueryEngine:
    """
    L5 Query Engine for limits.

    Provides read-only operations:
    - List limits with filters
    - Get limit detail
    - List budget definitions

    All data access is delegated to L6 driver.
    """

    def __init__(self, driver: Any):
        """
        Args:
            driver: LimitsReadDriver instance (PIN-504: injected by L4 handler via DomainBridge).
        """
        self._driver = driver

    async def list_limits(
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
    ) -> LimitsListResult:
        """List limits for the tenant."""
        filters_applied: dict[str, Any] = {
            "tenant_id": tenant_id,
            "category": category,
            "status": status,
        }

        if scope:
            filters_applied["scope"] = scope
        if enforcement:
            filters_applied["enforcement"] = enforcement
        if limit_type:
            filters_applied["limit_type"] = limit_type
        if created_after:
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            filters_applied["created_before"] = created_before.isoformat()

        # Fetch from driver
        rows, total = await self._driver.fetch_limits(
            tenant_id=tenant_id,
            category=category,
            status=status,
            scope=scope,
            enforcement=enforcement,
            limit_type=limit_type,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
        )

        # Transform to result objects
        items = [
            LimitSummaryResult(
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

        return LimitsListResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    async def get_limit_detail(
        self,
        tenant_id: str,
        limit_id: str,
    ) -> Optional[LimitDetailResult]:
        """Get limit detail. Tenant isolation enforced."""
        row = await self._driver.fetch_limit_by_id(tenant_id, limit_id)

        if not row:
            return None

        return LimitDetailResult(
            limit_id=row["limit_id"],
            name=row["name"],
            description=row["description"],
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
            updated_at=row["updated_at"],
        )

    async def list_budgets(
        self,
        tenant_id: str,
        *,
        scope: Optional[str] = None,
        status: str = "ACTIVE",
        limit: int = 20,
        offset: int = 0,
    ) -> BudgetsListResult:
        """List budget definitions for the tenant."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "status": status}

        if scope:
            filters_applied["scope"] = scope

        # Fetch from driver
        rows = await self._driver.fetch_budget_limits(
            tenant_id=tenant_id,
            scope=scope,
            status=status,
            limit=limit,
            offset=offset,
        )

        # Transform to result objects
        items = [
            BudgetDefinitionResult(
                id=row["id"],
                name=row["name"],
                scope=row["scope"],
                max_value=row["max_value"],
                reset_period=row["reset_period"],
                enforcement=row["enforcement"],
                status=row["status"],
            )
            for row in rows
        ]

        return BudgetsListResult(
            items=items,
            total=len(items),
            filters_applied=filters_applied,
        )


# =============================================================================
# Factory
# =============================================================================


def get_limits_query_engine(session: "AsyncSession" = None, *, driver: Any = None) -> LimitsQueryEngine:
    """Get a LimitsQueryEngine instance.

    PIN-508 Phase 2B: Prefer passing driver (LimitsQueryCapability) from DomainBridge.
    Falls back to lazy cross-domain import if no driver provided (legacy path).
    """
    if driver is not None:
        return LimitsQueryEngine(driver=driver)

    # PIN-510 Phase 1B: Legacy fallback — assertion guards, env flag enforces
    import logging as _logging
    import os as _os

    if _os.environ.get("HOC_REQUIRE_L4_INJECTION"):
        raise RuntimeError(
            "get_limits_query_engine() called without driver injection. "
            "All callers must use L4 handler path (PIN-510 Phase 1B)."
        )
    _logging.getLogger(__name__).warning(
        "PIN-510: get_limits_query_engine() legacy fallback used — "
        "caller should inject driver via DomainBridge"
    )

    # Legacy path: lazy import (PIN-504) — to be removed after all callers migrate
    from app.hoc.cus.controls.L6_drivers.limits_read_driver import get_limits_read_driver

    return LimitsQueryEngine(
        driver=get_limits_read_driver(session),
    )


__all__ = [
    # Engine
    "LimitsQueryEngine",
    "get_limits_query_engine",
    # Result types
    "LimitSummaryResult",
    "LimitsListResult",
    "LimitDetailResult",
    "BudgetDefinitionResult",
    "BudgetsListResult",
]
