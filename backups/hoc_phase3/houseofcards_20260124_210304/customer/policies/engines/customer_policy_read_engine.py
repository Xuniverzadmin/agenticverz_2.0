# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L6 driver)
# Role: Customer policy domain read operations with business logic (pure logic)
# Callers: customer_policies_adapter.py (L3)
# Allowed Imports: L6 (drivers only, NOT ORM models)
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L5 engine delegates DB operations to PolicyReadDriver (L6).
# Business logic (period calculation, budget math) stays HERE.
# Phase 2 extraction: DB operations moved to drivers/policy_read_driver.py
#
# EXTRACTION STATUS: COMPLETE (2026-01-23)
# NOTE: Renamed customer_policy_read_service.py → customer_policy_read_engine.py (2026-01-24)
#       Reclassified L4→L5 per HOC Topology V1 - BANNED_NAMING fix

"""
Customer Policy Read Service (L4)

This service provides all READ operations for the Policy domain.
It delegates DB access to PolicyReadDriver (L6) and applies business logic.

L3 (Adapter) → L4 (this service) → L6 (PolicyReadDriver)

Responsibilities:
- Calculate period bounds (business logic)
- Calculate budget remaining/percentage (business logic)
- Assemble customer-safe DTOs
- Rate limits defaults (business logic)
- Delegate DB queries to driver

Business Logic (stays in L4):
- _calculate_period_bounds() - daily/weekly/monthly period calculation
- Budget remaining calculation
- Percentage calculation
- Rate limit defaults

Reference: PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, List, Optional

# L6 driver import (allowed)
from app.houseofcards.customer.policies.drivers.policy_read_driver import (
    PolicyReadDriver,
    get_policy_read_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session


@dataclass
class BudgetConstraint:
    """
    Customer-visible budget constraint.

    IMPORTANT: No internal threshold multipliers, no warning levels.
    This is what customers see for their budget status.
    """

    limit_cents: int
    period: str  # daily, weekly, monthly
    current_usage_cents: int
    remaining_cents: int
    percentage_used: float
    reset_at: Optional[str]  # ISO timestamp


@dataclass
class RateLimit:
    """
    Customer-visible rate limit.

    IMPORTANT: No internal bucket configuration exposed.
    """

    requests_per_period: int
    period: str  # minute, hour, day
    current_usage: int
    remaining: int


@dataclass
class GuardrailSummary:
    """
    Customer-visible guardrail summary.

    IMPORTANT: No threshold values, no rule_config, no priority.
    Customers see what guardrails exist and their actions, not how they're implemented.
    """

    id: str
    name: str
    description: str
    enabled: bool
    category: str  # safety, cost, rate, content
    action_on_trigger: str  # block, warn, log


@dataclass
class PolicyConstraints:
    """
    Customer-visible policy constraints summary.

    This is the aggregate view of all constraints affecting a tenant.
    """

    tenant_id: str
    budget: Optional[BudgetConstraint]
    rate_limits: List[RateLimit]
    guardrails: List[GuardrailSummary]
    last_updated: str  # ISO timestamp


class CustomerPolicyReadService:
    """
    L4 service for policy constraint read operations.

    Delegates DB operations to PolicyReadDriver (L6).
    Applies business logic for period calculation, budget math, etc.

    INVARIANT: tenant_id is REQUIRED for budget operations.
    NO DIRECT DB ACCESS - driver calls only.
    """

    def __init__(self, session: "Session"):
        """
        Initialize with database session (passed to driver).

        Args:
            session: SQLModel session (injected by L3)
        """
        self._driver = get_policy_read_driver(session)

    def get_policy_constraints(
        self,
        tenant_id: str,
    ) -> PolicyConstraints:
        """
        Get policy constraints for a tenant.

        Returns budget, rate limits, and guardrails applicable to this tenant.

        Args:
            tenant_id: Tenant ID (REQUIRED)

        Returns:
            PolicyConstraints with customer-safe data
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for get_policy_constraints")

        # Get budget constraint (business logic + driver data)
        budget = self._get_budget_constraint(tenant_id)

        # Get rate limits (business logic - defaults)
        rate_limits = self._get_rate_limits(tenant_id)

        # Get guardrails list (driver data + DTO transform)
        guardrails = self._get_guardrails()

        return PolicyConstraints(
            tenant_id=tenant_id,
            budget=budget,
            rate_limits=rate_limits,
            guardrails=guardrails,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    def get_guardrail_detail(
        self,
        tenant_id: str,
        guardrail_id: str,
    ) -> Optional[GuardrailSummary]:
        """
        Get guardrail detail.

        Args:
            tenant_id: Tenant ID (REQUIRED for audit logging)
            guardrail_id: Guardrail ID to fetch

        Returns:
            GuardrailSummary if found, None otherwise
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for get_guardrail_detail")
        if not guardrail_id:
            raise ValueError("guardrail_id is required for get_guardrail_detail")

        # Delegate to driver
        guardrail_dto = self._driver.get_guardrail_by_id(guardrail_id)

        if guardrail_dto is None:
            return None

        # Transform driver DTO to customer-safe summary
        return GuardrailSummary(
            id=guardrail_dto.id,
            name=guardrail_dto.name,
            description=guardrail_dto.description or "",
            enabled=guardrail_dto.is_enabled,
            category=guardrail_dto.category,
            action_on_trigger=guardrail_dto.action,
        )

    def _get_budget_constraint(self, tenant_id: str) -> Optional[BudgetConstraint]:
        """
        Get budget constraint for tenant.

        BUSINESS LOGIC: Calculates period bounds, remaining, percentage.
        """
        # Get tenant settings from driver
        tenant_data = self._driver.get_tenant_budget_settings(tenant_id)

        if tenant_data is None:
            return None

        budget_limit = tenant_data.budget_limit_cents
        budget_period = tenant_data.budget_period

        # BUSINESS LOGIC: Calculate period start and reset time
        now = datetime.now(timezone.utc)
        period_start, reset_at = self._calculate_period_bounds(now, budget_period)

        # Get usage from driver
        usage_data = self._driver.get_usage_sum_since(tenant_id, period_start)
        current_usage = usage_data.total_cents

        # BUSINESS LOGIC: Calculate remaining and percentage
        remaining = max(0, budget_limit - current_usage)
        percentage = (current_usage / budget_limit * 100) if budget_limit > 0 else 0

        return BudgetConstraint(
            limit_cents=budget_limit,
            period=budget_period,
            current_usage_cents=current_usage,
            remaining_cents=remaining,
            percentage_used=round(percentage, 1),
            reset_at=reset_at.isoformat() if reset_at else None,
        )

    def _calculate_period_bounds(
        self,
        now: datetime,
        period: str,
    ) -> tuple[datetime, datetime]:
        """
        Calculate period start and reset time.

        BUSINESS LOGIC: Defines how daily/weekly/monthly periods work.

        Args:
            now: Current time
            period: Period type (daily, weekly, monthly)

        Returns:
            (period_start, reset_at) tuple
        """
        if period == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            reset_at = period_start + timedelta(days=1)
        elif period == "weekly":
            days_since_monday = now.weekday()
            period_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            reset_at = period_start + timedelta(weeks=1)
        else:  # monthly
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                reset_at = now.replace(year=now.year + 1, month=1, day=1)
            else:
                reset_at = now.replace(month=now.month + 1, day=1)

        return period_start, reset_at

    def _get_rate_limits(self, tenant_id: str) -> List[RateLimit]:
        """
        Get rate limits for tenant.

        BUSINESS LOGIC: Currently returns default rate limits.
        Could be expanded to tenant-specific limits.
        """
        # Default rate limits (could be made tenant-specific based on plan)
        return [
            RateLimit(
                requests_per_period=1000,
                period="hour",
                current_usage=0,  # Would need rate limit tracking
                remaining=1000,
            )
        ]

    def _get_guardrails(self) -> List[GuardrailSummary]:
        """
        Get all guardrails.

        Transforms driver DTOs to customer-safe summaries.
        """
        # Delegate to driver
        guardrail_dtos = self._driver.list_all_guardrails()

        # Transform to customer-safe summaries (hides priority, rule_config)
        return [
            GuardrailSummary(
                id=g.id,
                name=g.name,
                description=g.description or "",
                enabled=g.is_enabled,
                category=g.category,
                action_on_trigger=g.action,
            )
            for g in guardrail_dtos
        ]


def get_customer_policy_read_service(session: "Session") -> CustomerPolicyReadService:
    """
    Factory function for CustomerPolicyReadService.

    Args:
        session: SQLModel session (REQUIRED - must be provided by L3 adapter)

    Returns:
        Configured CustomerPolicyReadService instance

    Note:
        Session must be provided by caller. This engine does not create sessions.
        Session creation is the responsibility of L3 adapters.
    """
    return CustomerPolicyReadService(session)
