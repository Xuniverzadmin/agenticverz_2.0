# Layer: L5 — Domain Engine
# NOTE: Relocated from L5_controls/engines/ → L5_engines/ (2026-01-31) per standard directory topology
# AUDIENCE: CUSTOMER
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L6 driver)
# Role: Customer killswitch read operations (L5 engine over L6 driver)
# Callers: customer_killswitch_adapter.py (L3)
# Allowed Imports: L6 (drivers only, NOT ORM models)
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: PIN-280, PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L5 engine delegates ALL database operations to KillswitchReadDriver (L6).
# NO direct database access - only driver calls.
# Phase 2 extraction: DB operations moved to drivers/killswitch_read_driver.py
#
# EXTRACTION STATUS: COMPLETE (2026-01-23)
# NOTE: Renamed customer_killswitch_read_service.py → customer_killswitch_read_engine.py (2026-01-24)
#       Reclassified L4→L5 per HOC Topology V1 - BANNED_NAMING fix

"""
Customer Killswitch Read Service (L4)

This service provides read operations for customer killswitch status.
It delegates to KillswitchReadDriver (L6) for all database access.

L3 (customer_killswitch_adapter.py) → L4 (this service) → L6 (KillswitchReadDriver)

Responsibilities:
- Delegate to L6 driver for data access
- Apply business rules (if any)
- Maintain backward compatibility for callers

Reference: PIN-280, PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel

# L6 driver import (allowed)
from app.hoc.cus.policies.controls.drivers.killswitch_read_driver import (
    KillswitchReadDriver,
    get_killswitch_read_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session


# =============================================================================
# L4 DTOs (Backward compatibility - aliased from driver DTOs)
# =============================================================================


class KillswitchState(BaseModel):
    """Killswitch state information."""

    is_frozen: bool
    frozen_at: Optional[datetime] = None
    frozen_by: Optional[str] = None


class GuardrailInfo(BaseModel):
    """Active guardrail information."""

    name: str


class IncidentStats(BaseModel):
    """Incident statistics for a tenant."""

    incidents_blocked_24h: int
    last_incident_time: Optional[datetime] = None


class KillswitchStatusInfo(BaseModel):
    """Complete killswitch status information."""

    state: KillswitchState
    active_guardrails: List[str]
    incident_stats: IncidentStats


# =============================================================================
# L4 Service Class
# =============================================================================


class CustomerKillswitchReadService:
    """
    Read operations for customer killswitch status.

    Delegates all database operations to KillswitchReadDriver (L6).
    Maintains backward compatibility for existing callers.

    INVARIANT: All methods require tenant_id for isolation.
    INVARIANT: Read-only - no mutations.
    NO DIRECT DB ACCESS - driver calls only.
    """

    def __init__(self, session: Optional["Session"] = None):
        """Initialize service with optional session (passed to driver)."""
        self._driver = get_killswitch_read_driver(session)

    def get_killswitch_status(
        self,
        tenant_id: str,
    ) -> KillswitchStatusInfo:
        """
        Get complete killswitch status for a tenant.

        Delegates to KillswitchReadDriver.get_killswitch_status().

        Args:
            tenant_id: Customer's tenant ID (REQUIRED)

        Returns:
            KillswitchStatusInfo with state, guardrails, and incident stats

        Raises:
            ValueError: If tenant_id is missing
        """
        # Get status from driver
        driver_result = self._driver.get_killswitch_status(tenant_id)

        # Transform to engine DTOs (for backward compatibility)
        return KillswitchStatusInfo(
            state=KillswitchState(
                is_frozen=driver_result.state.is_frozen,
                frozen_at=driver_result.state.frozen_at,
                frozen_by=driver_result.state.frozen_by,
            ),
            active_guardrails=driver_result.active_guardrails,
            incident_stats=IncidentStats(
                incidents_blocked_24h=driver_result.incident_stats.incidents_blocked_24h,
                last_incident_time=driver_result.incident_stats.last_incident_time,
            ),
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_customer_killswitch_read_service_instance: Optional[CustomerKillswitchReadService] = None


def get_customer_killswitch_read_service() -> CustomerKillswitchReadService:
    """
    Get the singleton CustomerKillswitchReadService instance.

    This is the ONLY way L3 should obtain a killswitch read service.
    Direct instantiation is discouraged.

    Returns:
        CustomerKillswitchReadService singleton instance
    """
    global _customer_killswitch_read_service_instance
    if _customer_killswitch_read_service_instance is None:
        _customer_killswitch_read_service_instance = CustomerKillswitchReadService()
    return _customer_killswitch_read_service_instance


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CustomerKillswitchReadService",
    "get_customer_killswitch_read_service",
    # DTOs
    "KillswitchState",
    "GuardrailInfo",
    "IncidentStats",
    "KillswitchStatusInfo",
]
