# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: AI Console (Guard)
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L6 driver)
# Role: Guard write operations (L5 engine delegating to L6 driver) - pure business logic
# Callers: api/guard.py
# Allowed Imports: L6 (drivers only, NOT ORM models)
# Forbidden Imports: L1, L2 (api), L3 (adapters), L4, sqlalchemy, sqlmodel
# Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
# NOTE: Reclassified L4→L5 (2026-01-24) - Per HOC topology, engines are L5 (business logic)
#
# GOVERNANCE NOTE:
# This L4 engine delegates ALL database operations to GuardWriteDriver (L6).
# NO direct database access - only driver calls.
# Phase 2 extraction: DB operations moved to drivers/guard_write_driver.py
#
# EXTRACTION STATUS: COMPLETE (2026-01-23)

"""
Guard Write Service (L4)

DB write operations for Guard API.
Delegates to GuardWriteDriver (L6) for all database access.

L2 (API) → L4 (this service) → L6 (GuardWriteDriver)

Responsibilities:
- Delegate to L6 driver for data access
- Maintain backward compatibility for callers

Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
"""

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional, Tuple

# L6 driver import (allowed)
from app.houseofcards.customer.general.controls.drivers.guard_write_driver import (
    GuardWriteDriver,
    get_guard_write_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session
    from app.models.killswitch import (
        Incident,
        IncidentEvent,
        KillSwitchState,
    )


class GuardWriteService:
    """
    DB write operations for Guard Console.

    Delegates all operations to GuardWriteDriver (L6).
    NO DIRECT DB ACCESS - driver calls only.
    """

    def __init__(self, session: "Session"):
        self._driver = get_guard_write_driver(session)

    # =========================================================================
    # KillSwitch Operations
    # =========================================================================

    def get_or_create_killswitch_state(
        self,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
    ) -> Tuple["KillSwitchState", bool]:
        """Delegate to driver."""
        return self._driver.get_or_create_killswitch_state(
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
        )

    def freeze_killswitch(
        self,
        state: "KillSwitchState",
        by: str,
        reason: str,
        auto: bool = False,
        trigger: Optional[str] = None,
    ) -> "KillSwitchState":
        """Delegate to driver."""
        return self._driver.freeze_killswitch(
            state=state,
            by=by,
            reason=reason,
            auto=auto,
            trigger=trigger,
        )

    def unfreeze_killswitch(
        self,
        state: "KillSwitchState",
        by: str,
    ) -> "KillSwitchState":
        """Delegate to driver."""
        return self._driver.unfreeze_killswitch(state=state, by=by)

    # =========================================================================
    # Incident Operations
    # =========================================================================

    def acknowledge_incident(self, incident: "Incident") -> "Incident":
        """Delegate to driver."""
        return self._driver.acknowledge_incident(incident=incident)

    def resolve_incident(self, incident: "Incident") -> "Incident":
        """Delegate to driver."""
        return self._driver.resolve_incident(incident=incident)

    def create_demo_incident(
        self,
        incident_id: str,
        tenant_id: str,
        title: str,
        trigger_type: str,
        policy_id: str,
        auto_action: str,
        events: List[Tuple[str, str]],  # List of (event_type, description)
        severity: str = "HIGH",
        calls_affected: int = 0,
        cost_delta_cents: Decimal = Decimal("0"),
        call_id: Optional[str] = None,
    ) -> Tuple["Incident", List["IncidentEvent"]]:
        """Delegate to driver."""
        return self._driver.create_demo_incident(
            incident_id=incident_id,
            tenant_id=tenant_id,
            title=title,
            trigger_type=trigger_type,
            policy_id=policy_id,
            auto_action=auto_action,
            events=events,
            severity=severity,
            calls_affected=calls_affected,
            cost_delta_cents=cost_delta_cents,
            call_id=call_id,
        )
