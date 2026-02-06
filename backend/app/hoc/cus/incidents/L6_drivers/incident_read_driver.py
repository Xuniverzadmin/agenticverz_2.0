# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Incident, IncidentEvent
#   Writes: none
# Database:
#   Scope: domain (incidents)
#   Models: Incident, IncidentEvent
# Role: Data access for incident read operations
# Callers: incident engines (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for incident reads.
# No business logic - only DB reads and ORM ↔ DTO transformation.
# Extracted from incident_read_service.py (Phase 2)

"""
Incident Read Driver (L6)

Pure data access layer for incident read operations.
No business logic - only query construction and data retrieval.

Architecture:
    L3 (Adapter) → L4 (Engine) → L6 (this driver) → Database

Operations:
- Query incidents with tenant isolation
- Query incident events
- Count queries
- No mutations (read-only)

Reference: PHASE2_EXTRACTION_PROTOCOL.md
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlmodel import Session

# L6 ORM model imports (allowed)
from app.models.killswitch import Incident, IncidentEvent


class IncidentReadDriver:
    """
    L6 driver for incident read operations.

    Pure data access - no business logic.
    All methods require tenant_id for isolation.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    def list_incidents(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Incident], int]:
        """
        List incidents for a tenant with optional filters.

        Args:
            tenant_id: Tenant ID (required, enforces isolation)
            status: Optional status filter
            severity: Optional severity filter
            from_date: Optional start date filter
            to_date: Optional end date filter
            limit: Page size (max 100)
            offset: Pagination offset

        Returns:
            Tuple of (incidents list, total count)
        """
        # Enforce pagination limits
        limit = min(limit, 100)

        # Build query with tenant isolation
        conditions = [Incident.tenant_id == tenant_id]

        if status:
            conditions.append(Incident.status == status)
        if severity:
            conditions.append(Incident.severity == severity)
        if from_date:
            conditions.append(Incident.created_at >= from_date)
        if to_date:
            conditions.append(Incident.created_at <= to_date)

        # Query incidents
        stmt = select(Incident).where(and_(*conditions)).order_by(desc(Incident.created_at)).offset(offset).limit(limit)
        rows = self._session.exec(stmt).all()
        incidents = [row[0] if hasattr(row, "__getitem__") else row for row in rows]

        # Get total count
        count_stmt = select(func.count(Incident.id)).where(and_(*conditions))
        count_row = self._session.exec(count_stmt).first()
        total = count_row[0] if count_row else 0

        return incidents, total

    def get_incident(
        self,
        incident_id: str,
        tenant_id: str,
    ) -> Optional[Incident]:
        """
        Get a single incident by ID with tenant isolation.

        Args:
            incident_id: Incident ID
            tenant_id: Tenant ID (required, enforces isolation)

        Returns:
            Incident if found and belongs to tenant, None otherwise
        """
        stmt = select(Incident).where(
            and_(
                Incident.id == incident_id,
                Incident.tenant_id == tenant_id,
            )
        )
        row = self._session.exec(stmt).first()
        return row[0] if row else None

    def get_incident_events(
        self,
        incident_id: str,
    ) -> List[IncidentEvent]:
        """
        Get timeline events for an incident.

        Args:
            incident_id: Incident ID

        Returns:
            List of IncidentEvent ordered by created_at
        """
        stmt = select(IncidentEvent).where(IncidentEvent.incident_id == incident_id).order_by(IncidentEvent.created_at)
        rows = self._session.exec(stmt).all()
        return [row[0] if hasattr(row, "__getitem__") else row for row in rows]

    def count_incidents_since(
        self,
        tenant_id: str,
        since: datetime,
    ) -> int:
        """
        Count incidents since a given time.

        Args:
            tenant_id: Tenant ID
            since: Start datetime

        Returns:
            Count of incidents
        """
        stmt = select(func.count(Incident.id)).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.created_at >= since,
            )
        )
        row = self._session.exec(stmt).first()
        return row[0] if row else 0

    def get_last_incident(
        self,
        tenant_id: str,
    ) -> Optional[Incident]:
        """
        Get the most recent incident for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Most recent Incident or None
        """
        stmt = select(Incident).where(Incident.tenant_id == tenant_id).order_by(desc(Incident.created_at)).limit(1)
        row = self._session.exec(stmt).first()
        return row[0] if row else None


def get_incident_read_driver(session: Session) -> IncidentReadDriver:
    """Factory function to get IncidentReadDriver instance."""
    return IncidentReadDriver(session)


__all__ = [
    "IncidentReadDriver",
    "get_incident_read_driver",
]

# Backward compatibility alias (legacy name from app.services.incident_read_service)
get_incident_read_service = get_incident_read_driver
