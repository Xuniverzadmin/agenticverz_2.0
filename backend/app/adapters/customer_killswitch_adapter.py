# Layer: L3 — Boundary Adapter
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L4)
# Role: Customer killswitch boundary adapter (L2 → L3 → L4)
# Callers: guard.py (L2)
# Allowed Imports: L4
# Forbidden Imports: L1, L2, L5, L6
# Reference: PIN-280, PIN-281 (L2 Promotion Governance)
#
# GOVERNANCE NOTE:
# This L3 adapter is TRANSLATION ONLY. It enforces:
# - Tenant scoping (customer can only control their own killswitch)
# - Customer-safe schema (no internal state details)
# - Delegates to L4 for all DB operations

"""
Customer Killswitch Boundary Adapter (L3)

This adapter sits between L2 (guard.py API) and L4 services.

L2 (Guard API) → L3 (this adapter) → L4 (CustomerKillswitchReadService, GuardWriteService)

The adapter:
1. Receives API requests with tenant context
2. Enforces tenant isolation
3. Delegates to L4 for all operations
4. Transforms results to customer-safe DTOs

Reference: PIN-280 (L2 Promotion Governance), PIN-281 (Claude Task TODO)
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Session

# L4 TriggerType constant (imported via service re-export would be cleaner,
# but for now we import the enum value directly)
from app.models.killswitch import TriggerType

# L4 imports ONLY (no L6 direct queries!)
from app.hoc.cus.hoc_spine.authority.guard_write_engine import GuardWriteService
from app.hoc.cus.controls.L6_drivers.killswitch_read_driver import (
    CustomerKillswitchReadService,
    get_customer_killswitch_read_service,
)

# =============================================================================
# Customer-Safe DTOs
# =============================================================================


class CustomerKillswitchStatus(BaseModel):
    """Customer-safe killswitch status."""

    is_frozen: bool
    frozen_at: Optional[str] = None
    frozen_by: Optional[str] = None
    incidents_blocked_24h: int
    active_guardrails: List[str]
    last_incident_time: Optional[str] = None


class CustomerKillswitchAction(BaseModel):
    """Result of a killswitch action."""

    status: str  # frozen, active
    message: str
    frozen_at: Optional[str] = None


# =============================================================================
# L3 Adapter Class
# =============================================================================


class CustomerKillswitchAdapter:
    """
    Boundary adapter for customer killswitch operations.

    This class provides the ONLY interface that L2 (guard.py) may use
    to access killswitch functionality. It enforces tenant isolation and
    delegates to L4 for all operations.

    PIN-280 Rule: L3 Is Translation Only + Tenant Scoping
    """

    def __init__(self, session: Session):
        """Initialize adapter with database session.

        Args:
            session: Database session (needed for write operations)
        """
        self._session = session
        self._write_service = GuardWriteService(session)
        self._read_service: Optional[CustomerKillswitchReadService] = None

    def _get_read_service(self) -> CustomerKillswitchReadService:
        """Get the L4 read service (lazy loaded singleton)."""
        if self._read_service is None:
            self._read_service = get_customer_killswitch_read_service()
        return self._read_service

    def get_status(
        self,
        tenant_id: str,
    ) -> CustomerKillswitchStatus:
        """
        Get killswitch status for a customer.

        Enforces tenant isolation - customer can only see their own status.

        Args:
            tenant_id: Customer's tenant ID (REQUIRED, enforced)

        Returns:
            CustomerKillswitchStatus with protection status

        Raises:
            ValueError: If tenant_id is missing
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for get_status")

        # Delegate to L4 service
        result = self._get_read_service().get_killswitch_status(tenant_id=tenant_id)

        # Transform L4 DTOs to L3 customer-safe DTOs
        return CustomerKillswitchStatus(
            is_frozen=result.state.is_frozen,
            frozen_at=result.state.frozen_at.isoformat() if result.state.frozen_at else None,
            frozen_by=result.state.frozen_by,
            incidents_blocked_24h=result.incident_stats.incidents_blocked_24h,
            active_guardrails=result.active_guardrails,
            last_incident_time=(
                result.incident_stats.last_incident_time.isoformat()
                if result.incident_stats.last_incident_time
                else None
            ),
        )

    def activate(
        self,
        tenant_id: str,
    ) -> CustomerKillswitchAction:
        """
        Activate killswitch (stop all traffic).

        Args:
            tenant_id: Customer's tenant ID (REQUIRED, enforced)

        Returns:
            CustomerKillswitchAction with result

        Raises:
            ValueError: If already frozen or tenant_id is missing
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for activate")

        # Get or create state (delegates to L4)
        state, is_new = self._write_service.get_or_create_killswitch_state(
            entity_type="tenant",
            entity_id=tenant_id,
            tenant_id=tenant_id,
        )

        if state.is_frozen:
            raise ValueError("Traffic is already stopped")

        # Freeze (delegates to L4)
        self._write_service.freeze_killswitch(
            state=state,
            by="customer",
            reason="Manual kill switch activated via Customer Console",
            auto=False,
            trigger=TriggerType.MANUAL.value,
        )

        return CustomerKillswitchAction(
            status="frozen",
            message="All traffic stopped. Your systems are now protected.",
            frozen_at=datetime.now(timezone.utc).isoformat(),
        )

    def deactivate(
        self,
        tenant_id: str,
    ) -> CustomerKillswitchAction:
        """
        Deactivate killswitch (resume traffic).

        Args:
            tenant_id: Customer's tenant ID (REQUIRED, enforced)

        Returns:
            CustomerKillswitchAction with result

        Raises:
            ValueError: If not frozen or tenant_id is missing
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for deactivate")

        # Get or create state (delegates to L4)
        state, is_new = self._write_service.get_or_create_killswitch_state(
            entity_type="tenant",
            entity_id=tenant_id,
            tenant_id=tenant_id,
        )

        if not state.is_frozen:
            raise ValueError("Traffic is not stopped")

        # Unfreeze (delegates to L4)
        self._write_service.unfreeze_killswitch(
            state=state,
            by="customer",
        )

        return CustomerKillswitchAction(
            status="active",
            message="Traffic resumed. Guardrails continue protecting your systems.",
            frozen_at=None,
        )


# =============================================================================
# Factory
# =============================================================================


def get_customer_killswitch_adapter(session: Session) -> CustomerKillswitchAdapter:
    """
    Get a CustomerKillswitchAdapter instance.

    Args:
        session: Database session (required for write operations)

    Returns:
        CustomerKillswitchAdapter instance
    """
    return CustomerKillswitchAdapter(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CustomerKillswitchAdapter",
    "get_customer_killswitch_adapter",
    # DTOs for L2 convenience
    "CustomerKillswitchStatus",
    "CustomerKillswitchAction",
]
