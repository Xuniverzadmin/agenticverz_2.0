# Layer: L6 — Driver
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: engine-call
#   Execution: sync
# Role: Data access for incident write operations
# Callers: IncidentWriteEngine (L4)
# Allowed Imports: sqlalchemy, sqlmodel, app.models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Incident Write Driver

L6 driver for incident write data access.

Pure persistence - no business logic.
Executes writes as directed by engine.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.killswitch import Incident, IncidentEvent, IncidentStatus


@dataclass(frozen=True)
class IncidentUpdateRow:
    """Immutable incident data for updates."""

    id: str
    tenant_id: str
    status: str
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution_method: Optional[str]


class IncidentWriteDriver:
    """L6 driver for incident write data access.

    Pure persistence - no business logic.
    Executes writes as directed by engine.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    # =========================================================================
    # FETCH OPERATIONS
    # =========================================================================

    def fetch_incident(
        self,
        incident_id: str,
        tenant_id: str,
    ) -> Optional[Incident]:
        """Fetch incident by ID with tenant isolation.

        Args:
            incident_id: Incident ID
            tenant_id: Tenant ID for ownership verification

        Returns:
            Incident if found, None otherwise
        """
        stmt = select(Incident).where(
            Incident.id == UUID(incident_id),
            Incident.tenant_id == UUID(tenant_id),
        )
        return self._session.exec(stmt).first()

    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================

    def update_incident_acknowledged(
        self,
        incident: Incident,
        acknowledged_at: datetime,
        acknowledged_by: str,
    ) -> None:
        """Update incident to acknowledged state.

        Args:
            incident: Incident to update
            acknowledged_at: Timestamp
            acknowledged_by: Who acknowledged
        """
        incident.status = IncidentStatus.ACKNOWLEDGED
        incident.acknowledged_at = acknowledged_at
        incident.acknowledged_by = acknowledged_by
        self._session.add(incident)

    def update_incident_resolved(
        self,
        incident: Incident,
        resolved_at: datetime,
        resolved_by: str,
        resolution_method: Optional[str] = None,
    ) -> None:
        """Update incident to resolved state.

        Args:
            incident: Incident to update
            resolved_at: Timestamp
            resolved_by: Who resolved
            resolution_method: How it was resolved
        """
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = resolved_at
        incident.resolved_by = resolved_by
        if resolution_method:
            incident.resolution_method = resolution_method
        self._session.add(incident)

    # =========================================================================
    # EVENT OPERATIONS
    # =========================================================================

    def create_event(
        self,
        incident_id: str,
        event_type: str,
        description: str,
    ) -> IncidentEvent:
        """Create a timeline event for an incident.

        Args:
            incident_id: Parent incident ID
            event_type: Type of event
            description: Event description

        Returns:
            Created IncidentEvent
        """
        event = IncidentEvent(
            incident_id=incident_id,
            event_type=event_type,
            description=description,
        )
        self._session.add(event)
        return event

    # =========================================================================
    # TRANSACTION OPERATIONS
    # =========================================================================

    def begin_transaction(self):
        """Begin a nested transaction.

        Returns:
            Transaction context manager
        """
        return self._session.begin()

    def commit(self) -> None:
        """Commit the current transaction."""
        self._session.commit()

    def refresh(self, obj) -> None:
        """Refresh object from database.

        Args:
            obj: Object to refresh
        """
        self._session.refresh(obj)


# Factory function
def get_incident_write_driver(session: Session) -> IncidentWriteDriver:
    """Get driver instance.

    Args:
        session: Database session

    Returns:
        IncidentWriteDriver instance
    """
    return IncidentWriteDriver(session)
