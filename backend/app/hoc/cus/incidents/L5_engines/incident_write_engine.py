# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L6 driver)
# Lifecycle:
#   Emits: incident_acknowledged, incident_resolved
#   Subscribes: none
# Data Access:
#   Reads: Incident (via driver)
#   Writes: Incident, IncidentEvent (via driver)
# Role: Incident domain write operations with audit (L5 facade over L6 driver)
# Callers: customer_incidents_adapter.py (L3)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-281, PIN-413, PHASE2_EXTRACTION_PROTOCOL.md
# NOTE: Renamed incident_write_service.py → incident_write_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
#       Reclassified L4→L5 - Per HOC topology, engines are L5 (business logic)
#
# GOVERNANCE NOTE:
# This L5 engine delegates DB operations to IncidentWriteDriver (L6).
# Business logic (audit events, transaction orchestration) stays HERE.
# Phase 2 extraction: DB operations moved to drivers/incident_write_driver.py
#
# EXTRACTION STATUS: COMPLETE (2026-01-23)

"""
Incident Write Service (L4)

This service provides all WRITE operations for the Incidents domain.
It delegates DB access to IncidentWriteDriver (L6) and applies business logic.

L3 (Adapter) → L4 (this service) → L6 (IncidentWriteDriver)

Responsibilities:
- Acknowledge incidents (audit emit + delegate DB to driver)
- Resolve incidents (audit emit + delegate DB to driver)
- Transaction orchestration (begin/commit/rollback)
- Audit event emission (L4 responsibility)
- NO direct DB access - driver calls only

Reference: PIN-281, PIN-413, PHASE2_EXTRACTION_PROTOCOL.md
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

# L6 driver import (allowed)
from app.hoc.cus.incidents.L6_drivers.incident_write_driver import (
    IncidentWriteDriver,
    get_incident_write_driver,
)

# ActorType mirror (PIN-520 Phase 3: no runtime app.models imports in L5)
from app.hoc.cus.hoc_spine.schemas.domain_enums import ActorType

if TYPE_CHECKING:
    from sqlmodel import Session
    from app.models.killswitch import Incident


class IncidentWriteService:
    """
    L5 engine for incident write operations.

    Delegates DB operations to IncidentWriteDriver (L6).
    Maintains business logic (audit events, transactions) in L5.
    Audit service is injected by L4 handler (PIN-504: no cross-domain imports).

    NO DIRECT DB ACCESS - driver calls only.
    """

    def __init__(self, session: "Session", audit: Any = None):
        """
        Initialize with database session and optional audit service.

        Args:
            session: SQLAlchemy sync Session
            audit: Audit service instance (injected by L4 handler).
                   Must have incident_acknowledged, incident_resolved,
                   incident_manually_closed methods.
        """
        self._session = session
        self._driver = get_incident_write_driver(session)
        self._audit = audit

    def acknowledge_incident(
        self,
        incident: "Incident",
        acknowledged_by: str = "customer",
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
    ) -> "Incident":
        """
        Acknowledge an incident and create a timeline event.

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, incident change rolls back
        - No partial state is possible

        Delegates DB operations to IncidentWriteDriver (L6).
        Keeps audit logic (L4 responsibility) here.

        Args:
            incident: Incident to acknowledge
            acknowledged_by: Who acknowledged
            actor_type: Type of actor (HUMAN, SYSTEM, AGENT)
            reason: Optional reason for acknowledgment

        Returns:
            Updated Incident
        """
        now = datetime.now(timezone.utc)

        # ATOMIC BLOCK: L4 owns transaction boundary (PIN-520)
        # Delegate DB operations to driver
        self._driver.update_incident_acknowledged(
            incident=incident,
            acknowledged_at=now,
            acknowledged_by=acknowledged_by,
        )

        # Delegate event creation to driver
        self._driver.create_incident_event(
            incident_id=str(incident.id),
            event_type="acknowledged",
            description=f"Incident acknowledged by {acknowledged_by}",
        )

        # Emit audit event (PIN-413: Logs Domain)
        # Audit service injected by L4 handler (PIN-504)
        if self._audit:
            incident_state = {"status": "acknowledged"}
            if incident.source_run_id:
                incident_state["run_id"] = incident.source_run_id
            self._audit.incident_acknowledged(
                tenant_id=incident.tenant_id,
                incident_id=str(incident.id),
                actor_id=acknowledged_by,
                actor_type=actor_type,
                reason=reason,
                incident_state=incident_state,
            )

        # Refresh via driver
        return self._driver.refresh_incident(incident)

    def resolve_incident(
        self,
        incident: "Incident",
        resolved_by: str = "customer",
        resolution_notes: Optional[str] = None,
        resolution_method: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
    ) -> "Incident":
        """
        Resolve an incident and create a timeline event.

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, incident change rolls back
        - No partial state is possible

        Delegates DB operations to IncidentWriteDriver (L6).
        Keeps audit logic (L4 responsibility) here.

        Args:
            incident: Incident to resolve
            resolved_by: Who resolved
            resolution_notes: Optional resolution notes
            resolution_method: How the incident was resolved (auto, manual, rollback)
            actor_type: Type of actor (HUMAN, SYSTEM, AGENT)
            reason: Optional reason for resolution (used in audit)

        Returns:
            Updated Incident
        """
        now = datetime.now(timezone.utc)

        # Build description for event (L4 logic)
        description = f"Incident resolved by {resolved_by}"
        if resolution_method:
            description += f" ({resolution_method})"
        if resolution_notes:
            description += f": {resolution_notes}"

        # ATOMIC BLOCK: L4 owns transaction boundary (PIN-520)
        # Delegate DB operations to driver
        self._driver.update_incident_resolved(
            incident=incident,
            resolved_at=now,
            resolved_by=resolved_by,
            resolution_method=resolution_method,
        )

        # Delegate event creation to driver
        self._driver.create_incident_event(
            incident_id=str(incident.id),
            event_type="resolved",
            description=description,
        )

        # Emit audit event (PIN-413: Logs Domain)
        # Audit service injected by L4 handler (PIN-504)
        if self._audit:
            after_state = {"status": "resolved"}
            if resolution_method:
                after_state["resolution_method"] = resolution_method
            if incident.source_run_id:
                after_state["run_id"] = incident.source_run_id
            self._audit.incident_resolved(
                tenant_id=incident.tenant_id,
                incident_id=str(incident.id),
                actor_id=resolved_by,
                actor_type=actor_type,
                reason=reason or resolution_notes,
                after_state=after_state,
                resolution_method=resolution_method,
            )

        # Refresh via driver
        return self._driver.refresh_incident(incident)

    def manual_close_incident(
        self,
        incident: "Incident",
        closed_by: str = "customer",
        reason: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
    ) -> "Incident":
        """
        Manually close an incident without resolution workflow.

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, incident change rolls back
        - No partial state is possible

        Delegates DB operations to IncidentWriteDriver (L6).
        Keeps audit logic (L4 responsibility) here.

        Use this for incidents that are:
        - False positives
        - Duplicates
        - No longer relevant

        Args:
            incident: Incident to close
            closed_by: Who closed the incident
            reason: Required reason for manual closure
            actor_type: Type of actor (HUMAN, SYSTEM, AGENT)

        Returns:
            Updated Incident
        """
        now = datetime.now(timezone.utc)

        # Capture before state for audit (L4 logic)
        before_state = {
            "status": incident.status.value if hasattr(incident.status, "value") else str(incident.status),
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        }
        if incident.source_run_id:
            before_state["run_id"] = incident.source_run_id

        # Build description for event (L4 logic)
        description = f"Incident manually closed by {closed_by}"
        if reason:
            description += f": {reason}"

        # ATOMIC BLOCK: L4 owns transaction boundary (PIN-520)
        # Delegate DB operations to driver
        self._driver.update_incident_resolved(
            incident=incident,
            resolved_at=now,
            resolved_by=closed_by,
            resolution_method="manual_closure",
        )

        # Delegate event creation to driver
        self._driver.create_incident_event(
            incident_id=str(incident.id),
            event_type="manually_closed",
            description=description,
        )

        # Capture after state for audit
        after_state = {
            "status": "RESOLVED",  # Known state after update
            "resolved_at": now.isoformat(),
            "resolution_method": "manual_closure",
        }
        if incident.source_run_id:
            after_state["run_id"] = incident.source_run_id

        # Emit audit event (PIN-413: Logs Domain)
        # Audit service injected by L4 handler (PIN-504)
        if self._audit:
            self._audit.incident_manually_closed(
                tenant_id=incident.tenant_id,
                incident_id=str(incident.id),
                actor_id=closed_by,
                actor_type=actor_type,
                reason=reason,
                before_state=before_state,
                after_state=after_state,
            )

        # Refresh via driver
        return self._driver.refresh_incident(incident)


def get_incident_write_service(session: "Session", audit: Any = None) -> IncidentWriteService:
    """
    Factory function to get IncidentWriteService instance.

    Args:
        session: SQLAlchemy sync Session
        audit: Optional audit service (injected by L4 handler for cross-domain audit)
    """
    return IncidentWriteService(session, audit=audit)


__all__ = [
    "IncidentWriteService",
    "get_incident_write_service",
]
