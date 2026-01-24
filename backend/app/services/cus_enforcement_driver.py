# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: engine-call
#   Execution: sync
# Role: Data access for customer enforcement evaluation
# Callers: CusEnforcementEngine (L4)
# Allowed Imports: sqlalchemy, sqlmodel, app.models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Customer Enforcement Driver

L6 driver for customer enforcement data access.

Pure persistence - no business logic.
Returns raw facts: integration data, usage counts, etc.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Session, func, select

from app.db import get_engine
from app.models.cus_models import (
    CusIntegration,
    CusLLMUsage,
)


@dataclass(frozen=True)
class IntegrationRow:
    """Immutable integration data for enforcement."""

    id: str
    tenant_id: str
    status: str
    health_state: str
    health_message: Optional[str]
    budget_limit_cents: int
    token_limit_month: int
    rate_limit_rpm: int
    has_budget_limit: bool
    has_token_limit: bool
    has_rate_limit: bool


@dataclass(frozen=True)
class UsageSnapshot:
    """Immutable usage snapshot for enforcement status."""

    budget_used_cents: int
    tokens_used: int
    current_rpm: int


class CusEnforcementDriver:
    """L6 driver for customer enforcement data access.

    Pure persistence - no business logic.
    Returns raw facts for engine to make decisions.
    """

    # =========================================================================
    # FETCH OPERATIONS
    # =========================================================================

    def fetch_integration(
        self,
        tenant_id: str,
        integration_id: str,
    ) -> Optional[IntegrationRow]:
        """Fetch integration data for enforcement.

        Args:
            tenant_id: Tenant ID
            integration_id: Integration ID

        Returns:
            IntegrationRow if found, None otherwise
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == integration_id,
                    CusIntegration.tenant_id == tenant_id,
                )
            ).first()

            if not integration:
                return None

            return IntegrationRow(
                id=str(integration.id),
                tenant_id=integration.tenant_id,
                status=integration.status.value if hasattr(integration.status, 'value') else str(integration.status),
                health_state=integration.health_state.value if hasattr(integration.health_state, 'value') else str(integration.health_state),
                health_message=integration.health_message,
                budget_limit_cents=integration.budget_limit_cents,
                token_limit_month=integration.token_limit_month,
                rate_limit_rpm=integration.rate_limit_rpm,
                has_budget_limit=integration.has_budget_limit,
                has_token_limit=integration.has_token_limit,
                has_rate_limit=integration.has_rate_limit,
            )

    def fetch_budget_usage(
        self,
        integration_id: str,
        tenant_id: str,
        period_start: date,
    ) -> int:
        """Fetch current budget usage for period.

        Args:
            integration_id: Integration ID
            tenant_id: Tenant ID
            period_start: Start of billing period

        Returns:
            Total cost in cents
        """
        engine = get_engine()

        with Session(engine) as session:
            result = session.exec(
                select(func.coalesce(func.sum(CusLLMUsage.cost_cents), 0)).where(
                    CusLLMUsage.integration_id == integration_id,
                    CusLLMUsage.tenant_id == tenant_id,
                    func.date(CusLLMUsage.created_at) >= period_start,
                )
            ).first()

            return int(result) if result else 0

    def fetch_token_usage(
        self,
        integration_id: str,
        tenant_id: str,
        period_start: date,
    ) -> int:
        """Fetch current token usage for period.

        Args:
            integration_id: Integration ID
            tenant_id: Tenant ID
            period_start: Start of billing period

        Returns:
            Total tokens (in + out)
        """
        engine = get_engine()

        with Session(engine) as session:
            result = session.exec(
                select(
                    func.coalesce(
                        func.sum(CusLLMUsage.tokens_in + CusLLMUsage.tokens_out), 0
                    )
                ).where(
                    CusLLMUsage.integration_id == integration_id,
                    CusLLMUsage.tenant_id == tenant_id,
                    func.date(CusLLMUsage.created_at) >= period_start,
                )
            ).first()

            return int(result) if result else 0

    def fetch_rate_count(
        self,
        integration_id: str,
        window_start: datetime,
    ) -> int:
        """Fetch request count in rate limit window.

        Args:
            integration_id: Integration ID
            window_start: Start of rate limit window

        Returns:
            Count of requests in window
        """
        engine = get_engine()

        with Session(engine) as session:
            result = session.exec(
                select(func.count()).where(
                    CusLLMUsage.integration_id == integration_id,
                    CusLLMUsage.created_at >= window_start,
                )
            ).first()

            return int(result) if result else 0

    def fetch_usage_snapshot(
        self,
        integration_id: str,
        tenant_id: str,
        period_start: date,
        rate_window_start: datetime,
    ) -> UsageSnapshot:
        """Fetch complete usage snapshot for status display.

        Args:
            integration_id: Integration ID
            tenant_id: Tenant ID
            period_start: Start of billing period
            rate_window_start: Start of rate limit window

        Returns:
            UsageSnapshot with all current values
        """
        engine = get_engine()

        with Session(engine) as session:
            # Budget usage
            budget_result = session.exec(
                select(func.coalesce(func.sum(CusLLMUsage.cost_cents), 0)).where(
                    CusLLMUsage.integration_id == integration_id,
                    CusLLMUsage.tenant_id == tenant_id,
                    func.date(CusLLMUsage.created_at) >= period_start,
                )
            ).first()
            budget_used = int(budget_result) if budget_result else 0

            # Token usage
            token_result = session.exec(
                select(
                    func.coalesce(
                        func.sum(CusLLMUsage.tokens_in + CusLLMUsage.tokens_out), 0
                    )
                ).where(
                    CusLLMUsage.integration_id == integration_id,
                    CusLLMUsage.tenant_id == tenant_id,
                    func.date(CusLLMUsage.created_at) >= period_start,
                )
            ).first()
            tokens_used = int(token_result) if token_result else 0

            # Rate count
            rate_result = session.exec(
                select(func.count()).where(
                    CusLLMUsage.integration_id == integration_id,
                    CusLLMUsage.created_at >= rate_window_start,
                )
            ).first()
            current_rpm = int(rate_result) if rate_result else 0

            return UsageSnapshot(
                budget_used_cents=budget_used,
                tokens_used=tokens_used,
                current_rpm=current_rpm,
            )


# Factory function
def get_cus_enforcement_driver() -> CusEnforcementDriver:
    """Get driver instance.

    Returns:
        CusEnforcementDriver instance
    """
    return CusEnforcementDriver()
