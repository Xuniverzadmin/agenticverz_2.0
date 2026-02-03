# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: Limits Simulation Driver
"""Limits Simulation Driver

L6 driver for limits simulation data access.

Pure persistence - no business logic.
Returns raw facts: tenant quotas, limits, overrides.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_control_plane import Limit, LimitStatus
from app.models.tenant import Tenant


@dataclass(frozen=True)
class TenantQuotaRow:
    """Immutable tenant quota data."""

    tenant_id: str
    max_runs_per_day: int
    max_concurrent_runs: int
    max_tokens_per_month: int
    runs_today: int
    tokens_this_month: int


@dataclass(frozen=True)
class PolicyLimitRow:
    """Immutable policy limit data."""

    limit_id: str
    name: str
    limit_category: str
    limit_type: str
    max_value: Decimal
    enforcement: str
    scope: Optional[str]
    scope_id: Optional[str]


class LimitsSimulationDriver:
    """L6 driver for limits simulation data access.

    Pure persistence - no business logic.
    Returns raw facts for engine to interpret.
    """

    def __init__(self, session: AsyncSession):
        """Initialize driver with async database session.

        Args:
            session: AsyncSession for data access
        """
        self._session = session

    # =========================================================================
    # TENANT QUOTAS
    # =========================================================================

    async def fetch_tenant_quotas(self, tenant_id: str) -> Optional[TenantQuotaRow]:
        """Fetch tenant quota information.

        Args:
            tenant_id: Tenant ID

        Returns:
            TenantQuotaRow if found, None otherwise
        """
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await self._session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if not tenant:
            return None

        return TenantQuotaRow(
            tenant_id=tenant_id,
            max_runs_per_day=tenant.max_runs_per_day,
            max_concurrent_runs=tenant.max_concurrent_runs,
            max_tokens_per_month=tenant.max_tokens_per_month,
            runs_today=tenant.runs_today,
            tokens_this_month=tenant.tokens_this_month,
        )

    # =========================================================================
    # POLICY LIMITS
    # =========================================================================

    async def fetch_policy_limits(self, tenant_id: str) -> List[PolicyLimitRow]:
        """Fetch active policy limits for tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of PolicyLimitRow
        """
        stmt = select(Limit).where(
            and_(
                Limit.tenant_id == tenant_id,
                Limit.status == LimitStatus.ACTIVE.value,
            )
        )
        result = await self._session.execute(stmt)
        limits = result.scalars().all()

        return [
            PolicyLimitRow(
                limit_id=str(limit.id),
                name=limit.name,
                limit_category=limit.limit_category,
                limit_type=limit.limit_type,
                max_value=limit.max_value,
                enforcement=limit.enforcement,
                scope=limit.scope,
                scope_id=limit.scope_id,
            )
            for limit in limits
        ]

    # =========================================================================
    # COST BUDGETS (Stubbed)
    # =========================================================================

    async def fetch_cost_budgets(self, tenant_id: str) -> List[dict]:
        """Fetch cost budgets for tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of cost budget dicts (empty - not yet implemented)
        """
        # TODO: Query cost_budgets table when implemented
        return []

    # =========================================================================
    # WORKER LIMITS (Stubbed)
    # =========================================================================

    async def fetch_worker_limits(
        self, tenant_id: str, worker_id: str
    ) -> Optional[dict]:
        """Fetch worker-specific limits.

        Args:
            tenant_id: Tenant ID
            worker_id: Worker ID

        Returns:
            Worker limits dict or None (not yet implemented)
        """
        # TODO: Query worker config when implementing
        return None

    # =========================================================================
    # ACTIVE OVERRIDES (Stubbed)
    # =========================================================================

    async def fetch_active_overrides(self, tenant_id: str) -> List[dict]:
        """Fetch active limit overrides for tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of active override dicts (empty - not yet implemented)
        """
        # TODO: Query limit_overrides table when migration is created
        return []


# Factory function
def get_limits_simulation_driver(session: AsyncSession) -> LimitsSimulationDriver:
    """Get driver instance with session.

    Args:
        session: AsyncSession

    Returns:
        LimitsSimulationDriver instance
    """
    return LimitsSimulationDriver(session=session)
