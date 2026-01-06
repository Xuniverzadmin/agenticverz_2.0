# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (DB writes)
# Role: Incident domain write operations (L4)
# Callers: customer_incidents_adapter.py (L3)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-281 (L3 Adapter Closure - PHASE 1)
#
# GOVERNANCE NOTE:
# This L4 service provides WRITE operations for the Incidents domain.
# All incident mutations must go through this service.
# Read operations are handled by IncidentReadService.

"""
Incident Write Service (L4)

This service provides all WRITE operations for the Incidents domain.
It sits between L3 (CustomerIncidentsAdapter) and L6 (Database).

L3 (Adapter) → L4 (this service) → L6 (Database)

Responsibilities:
- Acknowledge incidents (with event creation)
- Resolve incidents (with event creation)
- No direct exposure to L2

Reference: PIN-281 (L3 Adapter Closure - PHASE 1)
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

# L6 imports (allowed)
from app.models.killswitch import Incident, IncidentEvent, IncidentStatus


class IncidentWriteService:
    """
    L4 service for incident write operations.

    Provides tenant-scoped mutations for the Incidents domain.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    def acknowledge_incident(
        self,
        incident: Incident,
        acknowledged_by: str = "customer",
    ) -> Incident:
        """
        Acknowledge an incident and create a timeline event.

        Args:
            incident: Incident to acknowledge
            acknowledged_by: Who acknowledged

        Returns:
            Updated Incident
        """
        now = datetime.now(timezone.utc)

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
        self._session.commit()
        self._session.refresh(incident)

        return incident

    def resolve_incident(
        self,
        incident: Incident,
        resolved_by: str = "customer",
        resolution_notes: Optional[str] = None,
    ) -> Incident:
        """
        Resolve an incident and create a timeline event.

        Args:
            incident: Incident to resolve
            resolved_by: Who resolved
            resolution_notes: Optional resolution notes

        Returns:
            Updated Incident
        """
        now = datetime.now(timezone.utc)

        # Update incident status
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = now
        incident.resolved_by = resolved_by

        # Create timeline event
        description = f"Incident resolved by {resolved_by}"
        if resolution_notes:
            description += f": {resolution_notes}"

        event = IncidentEvent(
            incident_id=incident.id,
            event_type="resolved",
            description=description,
        )

        self._session.add(event)
        self._session.add(incident)
        self._session.commit()
        self._session.refresh(incident)

        return incident


def get_incident_write_service(session: Session) -> IncidentWriteService:
    """Factory function to get IncidentWriteService instance."""
    return IncidentWriteService(session)


__all__ = [
    "IncidentWriteService",
    "get_incident_write_service",
]
