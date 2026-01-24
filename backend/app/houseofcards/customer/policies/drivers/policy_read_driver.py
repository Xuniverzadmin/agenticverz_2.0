# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Data access for customer policy read operations
# Callers: policy engines (L4)
# Allowed Imports: ORM models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for policy reads.
# No business logic - only DB reads and ORM ↔ DTO transformation.
# Extracted from customer_policy_read_service.py (Phase 2)
#
# BUSINESS LOGIC stays in engine:
# - Period calculation (daily/weekly/monthly)
# - Budget remaining/percentage calculation
# - Rate limits defaults
# - DTO assembly with business rules

"""
Policy Read Driver (L6)

Pure data access layer for customer policy read operations.
No business logic - only query construction and data retrieval.

Architecture:
    L3 (Adapter) → L4 (Engine) → L6 (this driver) → Database

Operations:
- Query tenant settings
- Query usage totals (ProxyCall sum)
- Query guardrails
- No mutations (read-only)

Reference: PHASE2_EXTRACTION_PROTOCOL.md
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlmodel import Session

# L6 ORM model imports (allowed)
from app.models.killswitch import DefaultGuardrail, ProxyCall
from app.models.tenant import Tenant


# =============================================================================
# L6 DTOs (Raw data from database)
# =============================================================================


class TenantBudgetDataDTO(BaseModel):
    """Raw tenant budget settings from database."""

    tenant_id: str
    budget_limit_cents: int
    budget_period: str


class UsageSumDTO(BaseModel):
    """Raw usage sum from database."""

    total_cents: int


class GuardrailDTO(BaseModel):
    """Raw guardrail data from database."""

    id: str
    name: str
    description: Optional[str]
    is_enabled: bool
    category: str
    action: str
    priority: int


# =============================================================================
# L6 Driver Class
# =============================================================================


class PolicyReadDriver:
    """
    L6 driver for customer policy read operations.

    Pure data access - no business logic.
    All methods provide raw database data for L4 engine to process.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    def get_tenant_budget_settings(
        self,
        tenant_id: str,
    ) -> Optional[TenantBudgetDataDTO]:
        """
        Get raw tenant budget settings.

        Args:
            tenant_id: Tenant ID

        Returns:
            TenantBudgetDataDTO if tenant found, None otherwise
        """
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = self._session.exec(stmt).first()

        if result is None:
            return None

        tenant = result

        # Extract budget settings (use defaults if not set on model)
        budget_limit = getattr(tenant, "budget_limit_cents", 10000)  # $100 default
        budget_period = getattr(tenant, "budget_period", "daily")

        return TenantBudgetDataDTO(
            tenant_id=tenant_id,
            budget_limit_cents=budget_limit,
            budget_period=budget_period,
        )

    def get_usage_sum_since(
        self,
        tenant_id: str,
        since: datetime,
    ) -> UsageSumDTO:
        """
        Get total usage in cents since a given time.

        Args:
            tenant_id: Tenant ID
            since: Start datetime

        Returns:
            UsageSumDTO with total_cents
        """
        usage_stmt = select(func.coalesce(func.sum(ProxyCall.cost_cents), 0)).where(
            and_(
                ProxyCall.tenant_id == tenant_id,
                ProxyCall.created_at >= since,
            )
        )
        usage_result = self._session.exec(usage_stmt).first()
        current_usage = int(usage_result) if usage_result else 0

        return UsageSumDTO(total_cents=current_usage)

    def get_guardrail_by_id(
        self,
        guardrail_id: str,
    ) -> Optional[GuardrailDTO]:
        """
        Get a single guardrail by ID.

        Args:
            guardrail_id: Guardrail ID

        Returns:
            GuardrailDTO if found, None otherwise
        """
        stmt = select(DefaultGuardrail).where(DefaultGuardrail.id == guardrail_id)
        result = self._session.exec(stmt).first()

        if result is None:
            return None

        return self._to_guardrail_dto(result)

    def list_all_guardrails(self) -> List[GuardrailDTO]:
        """
        List all guardrails ordered by priority.

        Returns:
            List of GuardrailDTO
        """
        stmt = select(DefaultGuardrail).order_by(DefaultGuardrail.priority)
        results = list(self._session.exec(stmt))

        return [self._to_guardrail_dto(g) for g in results]

    def _to_guardrail_dto(self, guardrail: DefaultGuardrail) -> GuardrailDTO:
        """Transform ORM model to DTO."""
        return GuardrailDTO(
            id=guardrail.id,
            name=guardrail.name,
            description=guardrail.description,
            is_enabled=guardrail.is_enabled,
            category=guardrail.category,
            action=guardrail.action,
            priority=guardrail.priority,
        )


# =============================================================================
# Factory Function
# =============================================================================


def get_policy_read_driver(session: Session) -> PolicyReadDriver:
    """
    Get PolicyReadDriver instance.

    Args:
        session: SQLModel session

    Returns:
        PolicyReadDriver instance
    """
    return PolicyReadDriver(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PolicyReadDriver",
    "get_policy_read_driver",
    # DTOs
    "TenantBudgetDataDTO",
    "UsageSumDTO",
    "GuardrailDTO",
]
