# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Product: AI Console (Guard)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: DB write operations for Guard API - pure data access
# Callers: api/guard.py (L2)
# Allowed Imports: L7 (sqlalchemy, sqlmodel, models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-250 Phase 2B Batch 1, INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Phase II.2
# NOTE: Renamed guard_write_service.py → guard_write_driver.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_driver.py for L6 files)
#
# RECLASSIFICATION NOTE (2026-01-24):
# This file was previously declared as L4 (Domain Engine).
# Reclassified to L6 because it contains pure DB write operations.
# No business logic decisions, only persistence.
#
# =============================================================================
# AGGREGATION NOTE:
# This bundles KillSwitch, Incident, and IncidentEvent writes together.
# May be split in the future if the operations become more complex.
# =============================================================================

"""
Guard Write Service - DB write operations for Guard API.

Phase 2B Batch 1: Extracted from api/guard.py.

Constraints (enforced by PIN-250):
- Write-only: No policy logic
- No cross-service calls
- No domain refactoring
- Call-path relocation only
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import and_, select
from sqlmodel import Session

from app.models.killswitch import (
    Incident,
    IncidentEvent,
    IncidentSeverity,
    IncidentStatus,
    KillSwitchState,
    TriggerType,
)


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class GuardWriteService:
    """
    DB write operations for Guard Console.

    Write-only facade. No policy logic, no branching beyond DB operations.
    """

    def __init__(self, session: Session):
        self.session = session

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
        row = self.session.exec(stmt).first()
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
        self.session.add(state)
        self.session.commit()
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
        self.session.add(state)
        self.session.commit()
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
        self.session.add(incident)
        self.session.commit()
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
        self.session.add(incident)
        self.session.commit()
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

        self.session.add(incident)

        created_events = []
        for event_type, description in events:
            event = IncidentEvent(
                id=str(uuid.uuid4()),
                incident_id=incident_id,
                event_type=event_type,
                description=description,
            )
            self.session.add(event)
            created_events.append(event)

        self.session.commit()

        return incident, created_events
