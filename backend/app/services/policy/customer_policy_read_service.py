# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L6)
# Role: Customer policy domain read operations (L4)
# Callers: customer_policies_adapter.py (L3)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-281 (POLICY Domain Qualification)
#
# GOVERNANCE NOTE:
# This L4 service provides READ operations for the Policy domain.
# All policy constraint reads must go through this service.
# The L3 adapter should NOT import L6 directly.
# CUSTOMER-SAFE: No threshold values or internal rule configs exposed.

"""
Customer Policy Read Service (L4)

This service provides all READ operations for the Policy domain.
It sits between L3 (CustomerPoliciesAdapter) and L6 (Tenant, ProxyCall, DefaultGuardrail).

L3 (Adapter) → L4 (this service) → L6 (Models)

Responsibilities:
- Query tenant budget settings
- Calculate current period usage
- Query guardrails list
- Translate internal models → customer-visible policy constraints
- Hide internal fields (threshold values, rule configs)
- Stable period calculation

Reference: POLICY Domain Qualification Task
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, func
from sqlmodel import Session, select

# L6 imports (allowed)
from app.models.killswitch import DefaultGuardrail, ProxyCall
from app.models.tenant import Tenant


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

    Provides tenant-scoped, bounded reads for the Policy domain.
    All L3 adapters must use this service for policy reads.

    INVARIANT: tenant_id is REQUIRED for budget operations.
    """

    def __init__(self, session: Session):
        """
        Initialize with database session.

        Args:
            session: SQLModel session (injected by L3)
        """
        self._session = session

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

        # Get budget constraint
        budget = self._get_budget_constraint(tenant_id)

        # Get rate limits (simplified - could be expanded)
        rate_limits = self._get_rate_limits(tenant_id)

        # Get guardrails list
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

        stmt = select(DefaultGuardrail).where(DefaultGuardrail.id == guardrail_id)
        result = self._session.exec(stmt).first()

        if result is None:
            return None

        return self._to_guardrail_summary(result)

    def _get_budget_constraint(self, tenant_id: str) -> Optional[BudgetConstraint]:
        """
        Get budget constraint for tenant.

        Calculates current period usage and remaining budget.
        """
        # Get tenant settings
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = self._session.exec(stmt).first()

        if result is None:
            return None

        tenant = result

        # Extract budget settings (use defaults if not set)
        # Note: Tenant model may not have budget_limit_cents/budget_period
        # These could be derived from plan or explicit settings
        budget_limit = getattr(tenant, "budget_limit_cents", 10000)  # $100 default
        budget_period = getattr(tenant, "budget_period", "daily")

        # Calculate period start and reset time
        now = datetime.now(timezone.utc)
        period_start, reset_at = self._calculate_period_bounds(now, budget_period)

        # Query current usage from ProxyCall
        usage_stmt = select(func.coalesce(func.sum(ProxyCall.cost_cents), 0)).where(
            and_(
                ProxyCall.tenant_id == tenant_id,
                ProxyCall.created_at >= period_start,
            )
        )
        usage_result = self._session.exec(usage_stmt).first()
        current_usage = int(usage_result) if usage_result else 0

        # Calculate remaining and percentage
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

        Currently returns default rate limits.
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

        Default guardrails apply to all tenants.
        """
        stmt = select(DefaultGuardrail).order_by(DefaultGuardrail.priority)
        results = list(self._session.exec(stmt))

        return [self._to_guardrail_summary(g) for g in results]

    def _to_guardrail_summary(self, guardrail: DefaultGuardrail) -> GuardrailSummary:
        """
        Transform internal DefaultGuardrail to customer-safe GuardrailSummary.

        HIDES: priority, rule_type, rule_config_json, version
        """
        return GuardrailSummary(
            id=guardrail.id,
            name=guardrail.name,
            description=guardrail.description or "",
            enabled=guardrail.is_enabled,
            category=guardrail.category,
            action_on_trigger=guardrail.action,
        )


def get_customer_policy_read_service(session: Optional[Session] = None) -> CustomerPolicyReadService:
    """
    Factory function for CustomerPolicyReadService.

    Args:
        session: Optional SQLModel session. If not provided, creates one internally.

    Returns:
        Configured CustomerPolicyReadService instance
    """
    if session is None:
        from app.db import engine

        session = Session(engine)
    return CustomerPolicyReadService(session)
