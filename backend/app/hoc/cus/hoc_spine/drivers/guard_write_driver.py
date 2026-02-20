# capability_id: CAP-012
# Layer: L4 — HOC Spine (Driver)
# AUDIENCE: CUSTOMER
# Product: AI Console (Guard)
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: KillSwitchState, Incident
#   Writes: KillSwitchState, Incident, IncidentEvent
# Database:
#   Scope: hoc_spine
#   Models: KillSwitchState, Incident, IncidentEvent
# Role: Data access for guard/killswitch write operations
# Callers: guard engines (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for guard writes.
# NO business logic - only DB operations.
#
# EXTRACTION STATUS: RECLASSIFIED (2026-01-23)

"""
Guard Write Driver (L6)

Pure database write operations for Guard Console (KillSwitch, Incidents).

L4 (GuardWriteService) → L6 (this driver)

Responsibilities:
- Get/create KillSwitchState records
- Freeze/unfreeze killswitch
- Acknowledge/resolve incidents
- Create demo incidents with events
- NO business logic (L4 responsibility)

Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import and_, select
from sqlmodel import Session

from app.hoc.cus.hoc_spine.services.time import utc_now
from app.models.killswitch import (
    Incident,
    IncidentEvent,
    IncidentSeverity,
    IncidentStatus,
    KillSwitchState,
    TriggerType,
)


class GuardWriteDriver:
    """
    L6 driver for guard write operations.

    Pure database access - no business logic.
    """

    def __init__(self, session: Session):
        self._session = session

    # =========================================================================
    # KillSwitch Operations
    # =========================================================================

    def get_or_create_killswitch_state(
        self,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
    ) -> Tuple[KillSwitchState, bool]:
        """
        Get existing KillSwitchState or create a new unfrozen one.

        Returns:
            Tuple of (state, is_new)
        """
        stmt = select(KillSwitchState).where(
            and_(
                KillSwitchState.entity_type == entity_type,
                KillSwitchState.entity_id == entity_id,
            )
        )
        row = self._session.exec(stmt).first()
        state = row[0] if row else None

        if state:
            return state, False

        state = KillSwitchState(
            id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            is_frozen=False,
        )
        return state, True

    def freeze_killswitch(
        self,
        state: KillSwitchState,
        by: str,
        reason: str,
        auto: bool = False,
        trigger: Optional[str] = None,
    ) -> KillSwitchState:
        """
        Freeze a KillSwitchState and persist.

        Args:
            state: The state to freeze
            by: Who triggered the freeze
            reason: Why the freeze occurred
            auto: Whether this was automatic
            trigger: Trigger type (defaults to MANUAL)
        """
        state.freeze(
            by=by,
            reason=reason,
            auto=auto,
            trigger=trigger or TriggerType.MANUAL.value,
        )
        self._session.add(state)
        # NO COMMIT — L4 coordinator owns transaction boundary
        return state

    def unfreeze_killswitch(
        self,
        state: KillSwitchState,
        by: str,
    ) -> KillSwitchState:
        """
        Unfreeze a KillSwitchState and persist.

        Args:
            state: The state to unfreeze
            by: Who triggered the unfreeze
        """
        state.unfreeze(by=by)
        self._session.add(state)
        # NO COMMIT — L4 coordinator owns transaction boundary
        return state

    # =========================================================================
    # Incident Operations
    # =========================================================================

    def acknowledge_incident(self, incident: Incident) -> Incident:
        """
        Mark an incident as acknowledged and persist.

        Args:
            incident: The incident to acknowledge
        """
        incident.status = IncidentStatus.ACKNOWLEDGED.value
        self._session.add(incident)
        # NO COMMIT — L4 coordinator owns transaction boundary
        return incident

    def resolve_incident(self, incident: Incident) -> Incident:
        """
        Mark an incident as resolved and persist.

        Args:
            incident: The incident to resolve
        """
        incident.status = IncidentStatus.RESOLVED.value
        incident.ended_at = utc_now()
        if incident.started_at:
            incident.duration_seconds = int((incident.ended_at - incident.started_at).total_seconds())
        self._session.add(incident)
        # NO COMMIT — L4 coordinator owns transaction boundary
        return incident

    def create_demo_incident(
        self,
        incident_id: str,
        tenant_id: str,
        title: str,
        trigger_type: str,
        policy_id: str,
        auto_action: str,
        events: List[Tuple[str, str]],  # List of (event_type, description)
        severity: str = IncidentSeverity.HIGH.value,
        calls_affected: int = 0,
        cost_delta_cents: Decimal = Decimal("0"),
        call_id: Optional[str] = None,
    ) -> Tuple[Incident, List[IncidentEvent]]:
        """
        Create a demo incident with timeline events for onboarding verification.

        Args:
            incident_id: Pre-generated incident ID
            tenant_id: Tenant ID
            title: Incident title
            trigger_type: What triggered this
            policy_id: Policy that fired
            auto_action: Automatic action taken
            events: List of (event_type, description) tuples
            severity: Incident severity
            calls_affected: Number of calls affected
            cost_delta_cents: Cost impact
            call_id: Optional related call ID

        Returns:
            Tuple of (incident, list of events)
        """
        now = utc_now()

        incident = Incident(
            id=incident_id,
            tenant_id=tenant_id,
            title=title,
            severity=severity,
            status=IncidentStatus.RESOLVED.value,
            trigger_type=trigger_type,
            policy_id=policy_id,
            calls_affected=calls_affected,
            cost_delta_cents=cost_delta_cents,
            auto_action=auto_action,
            started_at=now,
            resolved_at=now,
        )

        if call_id:
            incident.add_related_call(call_id)

        self._session.add(incident)

        created_events = []
        for event_type, description in events:
            event = IncidentEvent(
                id=str(uuid.uuid4()),
                incident_id=incident_id,
                event_type=event_type,
                description=description,
            )
            self._session.add(event)
            created_events.append(event)

        # NO COMMIT — L4 coordinator owns transaction boundary

        return incident, created_events


def get_guard_write_driver(session: Session) -> GuardWriteDriver:
    """Factory function to get GuardWriteDriver instance."""
    return GuardWriteDriver(session)


__all__ = [
    "GuardWriteDriver",
    "get_guard_write_driver",
]
