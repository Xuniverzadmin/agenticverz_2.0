# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (DB writes)
# Role: Incident domain write operations (L4)
# Callers: customer_incidents_adapter.py (L3)
# Allowed Imports: L6, L4 (AuditLedgerService)
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-281 (L3 Adapter Closure - PHASE 1), PIN-413 (Logs Domain)
#
# GOVERNANCE NOTE:
# This L4 service provides WRITE operations for the Incidents domain.
# All incident mutations must go through this service.
# Read operations are handled by IncidentReadService.
# Audit events are emitted to AuditLedger for governance compliance.

"""
Incident Write Service (L4)

This service provides all WRITE operations for the Incidents domain.
It sits between L3 (CustomerIncidentsAdapter) and L6 (Database).

L3 (Adapter) → L4 (this service) → L6 (Database)

Responsibilities:
- Acknowledge incidents (with event creation + audit emit)
- Resolve incidents (with event creation + audit emit)
- No direct exposure to L2

Reference: PIN-281 (L3 Adapter Closure - PHASE 1)
Reference: PIN-413 (Logs Domain - Audit Ledger)
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

# L6 imports (allowed)
from app.models.killswitch import Incident, IncidentEvent, IncidentStatus

# L4 imports (audit ledger)
from app.models.audit_ledger import ActorType
from app.services.logs.audit_ledger_service import AuditLedgerService


class IncidentWriteService:
    """
    L4 service for incident write operations.

    Provides tenant-scoped mutations for the Incidents domain.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session
        self._audit = AuditLedgerService(session)

    def acknowledge_incident(
        self,
        incident: Incident,
        acknowledged_by: str = "customer",
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
    ) -> Incident:
        """
        Acknowledge an incident and create a timeline event.

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, incident change rolls back
        - No partial state is possible

        Args:
            incident: Incident to acknowledge
            acknowledged_by: Who acknowledged
            actor_type: Type of actor (HUMAN, SYSTEM, AGENT)
            reason: Optional reason for acknowledgment

        Returns:
            Updated Incident
        """
        now = datetime.now(timezone.utc)

        # ATOMIC BLOCK: state change + audit must succeed together
        with self._session.begin():
            # Update incident status
            incident.status = IncidentStatus.ACKNOWLEDGED
            incident.acknowledged_at = now
            incident.acknowledged_by = acknowledged_by

            # Create timeline event
            event = IncidentEvent(
                incident_id=incident.id,
                event_type="acknowledged",
                description=f"Incident acknowledged by {acknowledged_by}",
            )

            self._session.add(event)
            self._session.add(incident)

            # Emit audit event (PIN-413: Logs Domain)
            # Must be inside transaction - commits with state change
            self._audit.incident_acknowledged(
                tenant_id=incident.tenant_id,
                incident_id=str(incident.id),
                actor_id=acknowledged_by,
                actor_type=actor_type,
                reason=reason,
            )

        # Refresh after commit
        self._session.refresh(incident)

        return incident

    def resolve_incident(
        self,
        incident: Incident,
        resolved_by: str = "customer",
        resolution_notes: Optional[str] = None,
        resolution_method: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
    ) -> Incident:
        """
        Resolve an incident and create a timeline event.

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, incident change rolls back
        - No partial state is possible

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

        # ATOMIC BLOCK: state change + audit must succeed together
        with self._session.begin():
            # Update incident status
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = now
            incident.resolved_by = resolved_by

            # Set resolution method if provided
            if resolution_method:
                incident.resolution_method = resolution_method

            # Create timeline event
            description = f"Incident resolved by {resolved_by}"
            if resolution_method:
                description += f" ({resolution_method})"
            if resolution_notes:
                description += f": {resolution_notes}"

            event = IncidentEvent(
                incident_id=incident.id,
                event_type="resolved",
                description=description,
            )

            self._session.add(event)
            self._session.add(incident)

            # Emit audit event (PIN-413: Logs Domain)
            # Must be inside transaction - commits with state change
            self._audit.incident_resolved(
                tenant_id=incident.tenant_id,
                incident_id=str(incident.id),
                actor_id=resolved_by,
                actor_type=actor_type,
                reason=reason or resolution_notes,
                resolution_method=resolution_method,
            )

        # Refresh after commit
        self._session.refresh(incident)

        return incident

    def manual_close_incident(
        self,
        incident: Incident,
        closed_by: str = "customer",
        reason: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
    ) -> Incident:
        """
        Manually close an incident without resolution workflow.

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, incident change rolls back
        - No partial state is possible

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

        # Capture before state for audit
        before_state = {
            "status": incident.status.value if hasattr(incident.status, "value") else str(incident.status),
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        }

        # ATOMIC BLOCK: state change + audit must succeed together
        with self._session.begin():
            # Update incident status
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = now
            incident.resolved_by = closed_by
            incident.resolution_method = "manual_closure"

            # Create timeline event
            description = f"Incident manually closed by {closed_by}"
            if reason:
                description += f": {reason}"

            event = IncidentEvent(
                incident_id=incident.id,
                event_type="manually_closed",
                description=description,
            )

            self._session.add(event)
            self._session.add(incident)

            # Capture after state for audit
            after_state = {
                "status": incident.status.value if hasattr(incident.status, "value") else str(incident.status),
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "resolution_method": "manual_closure",
            }

            # Emit audit event (PIN-413: Logs Domain)
            # Must be inside transaction - commits with state change
            self._audit.incident_manually_closed(
                tenant_id=incident.tenant_id,
                incident_id=str(incident.id),
                actor_id=closed_by,
                actor_type=actor_type,
                reason=reason,
                before_state=before_state,
                after_state=after_state,
            )

        # Refresh after commit
        self._session.refresh(incident)

        return incident


def get_incident_write_service(session: Session) -> IncidentWriteService:
    """Factory function to get IncidentWriteService instance."""
    return IncidentWriteService(session)


__all__ = [
    "IncidentWriteService",
    "get_incident_write_service",
]
