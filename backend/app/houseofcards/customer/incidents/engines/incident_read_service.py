# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L6 driver)
# Role: Incident domain read operations (L4 facade over L6 driver)
# Callers: customer_incidents_adapter.py (L3)
# Allowed Imports: L6 (drivers only, NOT ORM models)
# Forbidden Imports: L1, L2, L3, L5, sqlalchemy, sqlmodel
# Reference: PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L4 engine delegates ALL database operations to IncidentReadDriver (L6).
# NO direct database access - only driver calls.
# Phase 2 extraction: DB operations moved to drivers/incident_read_driver.py
#
# EXTRACTION STATUS: COMPLETE (2026-01-23)

"""
Incident Read Service (L4)

This service provides all READ operations for the Incidents domain.
It delegates to IncidentReadDriver (L6) for all database access.

L3 (Adapter) → L4 (this service) → L6 (IncidentReadDriver)

Responsibilities:
- Delegate to L6 driver for data access
- Apply business rules (if any)
- Maintain backward compatibility for callers

Reference: PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple

# L6 driver import (allowed)
from app.houseofcards.customer.incidents.drivers.incident_read_driver import (
    IncidentReadDriver,
    get_incident_read_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session
    from app.models.killswitch import Incident, IncidentEvent


class IncidentReadService:
    """
    L4 service for incident read operations.

    Delegates all database operations to IncidentReadDriver (L6).
    Maintains backward compatibility for existing callers.

    NO DIRECT DB ACCESS - driver calls only.
    """

    def __init__(self, session: "Session"):
        """Initialize with database session (passed to driver)."""
        self._driver = get_incident_read_driver(session)

    def list_incidents(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List["Incident"], int]:
        """
        List incidents for a tenant with optional filters.

        Delegates to IncidentReadDriver.list_incidents().
        """
        return self._driver.list_incidents(
            tenant_id=tenant_id,
            status=status,
            severity=severity,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

    def get_incident(
        self,
        incident_id: str,
        tenant_id: str,
    ) -> Optional["Incident"]:
        """
        Get a single incident by ID with tenant isolation.

        Delegates to IncidentReadDriver.get_incident().
        """
        return self._driver.get_incident(incident_id=incident_id, tenant_id=tenant_id)

    def get_incident_events(
        self,
        incident_id: str,
    ) -> List["IncidentEvent"]:
        """
        Get timeline events for an incident.

        Delegates to IncidentReadDriver.get_incident_events().
        """
        return self._driver.get_incident_events(incident_id=incident_id)

    def count_incidents_since(
        self,
        tenant_id: str,
        since: datetime,
    ) -> int:
        """
        Count incidents since a given time.

        Delegates to IncidentReadDriver.count_incidents_since().
        """
        return self._driver.count_incidents_since(tenant_id=tenant_id, since=since)

    def get_last_incident(
        self,
        tenant_id: str,
    ) -> Optional["Incident"]:
        """
        Get the most recent incident for a tenant.

        Delegates to IncidentReadDriver.get_last_incident().
        """
        return self._driver.get_last_incident(tenant_id=tenant_id)


def get_incident_read_service(session: "Session") -> IncidentReadService:
    """Factory function to get IncidentReadService instance."""
    return IncidentReadService(session)


__all__ = [
    "IncidentReadService",
    "get_incident_read_service",
]
