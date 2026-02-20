# capability_id: CAP-009
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: incidents, proxy_calls, incident_events
#   Writes: none
# Database:
#   Scope: domain (policies/replay)
#   Models: Incident, ProxyCall, IncidentEvent
# Role: Data access for replay UX read operations
# Callers: L4 handlers (PoliciesReplayHandler)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Replay UX API (H1)
# artifact_class: CODE

"""
Replay Read Driver (L6)

Pure data access layer for replay UX read operations.
No business logic - only query construction and data retrieval.

Architecture:
    L2 (API) -> L4 (Handler) -> L6 (this driver) -> Database

Operations:
- get_incident: Fetch incident by ID with tenant isolation
- get_proxy_calls_in_window: Fetch proxy calls by IDs within time window
- get_incident_events_in_window: Fetch incident events within time window
- get_proxy_calls_for_timeline: Fetch all proxy calls for incident timeline
- get_all_incident_events: Fetch all events for an incident
- get_proxy_call_by_id: Fetch single proxy call
- get_incident_event_by_id: Fetch single incident event for an incident

Reference: Replay UX API (H1) - READ-ONLY slice and timeline endpoints
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlmodel import Session


class ReplayReadDriver:
    """
    L6 driver for replay UX read operations.

    Pure data access - no business logic.
    All incident access requires tenant_id for isolation.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    def get_incident(
        self,
        incident_id: str,
        tenant_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single incident by ID with tenant isolation.

        Args:
            incident_id: Incident ID
            tenant_id: Tenant ID (required, enforces isolation)

        Returns:
            Incident row as dict if found and belongs to tenant, None otherwise
        """
        result = self._session.execute(
            text("SELECT * FROM incidents WHERE id = :id AND tenant_id = :tenant_id"),
            {"id": incident_id, "tenant_id": tenant_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    def get_incident_no_tenant_check(
        self,
        incident_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single incident by ID without tenant check.

        Used when tenant check is done separately (e.g., by caller).

        Args:
            incident_id: Incident ID

        Returns:
            Incident row as dict if found, None otherwise
        """
        result = self._session.execute(
            text("SELECT * FROM incidents WHERE id = :id"),
            {"id": incident_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    def get_proxy_calls_in_window(
        self,
        call_ids: List[str],
        window_start: datetime,
        window_end: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Fetch proxy calls by IDs within a time window.

        Args:
            call_ids: List of proxy call IDs
            window_start: Start of time window
            window_end: End of time window

        Returns:
            List of proxy call rows as dicts, ordered by created_at
        """
        if not call_ids:
            return []

        # Build parameterized IN clause
        id_params = {f"cid_{i}": cid for i, cid in enumerate(call_ids)}
        id_placeholders = ", ".join(f":cid_{i}" for i in range(len(call_ids)))

        result = self._session.execute(
            text(
                f"SELECT * FROM proxy_calls WHERE id IN ({id_placeholders}) "
                "AND created_at >= :window_start AND created_at <= :window_end "
                "ORDER BY created_at"
            ),
            {**id_params, "window_start": window_start, "window_end": window_end},
        )
        return [dict(r) for r in result.mappings().all()]

    def get_incident_events_in_window(
        self,
        incident_id: str,
        window_start: datetime,
        window_end: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Fetch incident events within a time window.

        Args:
            incident_id: Incident ID
            window_start: Start of time window
            window_end: End of time window

        Returns:
            List of incident event rows as dicts, ordered by created_at
        """
        result = self._session.execute(
            text(
                "SELECT * FROM incident_events WHERE incident_id = :incident_id "
                "AND created_at >= :window_start AND created_at <= :window_end "
                "ORDER BY created_at"
            ),
            {
                "incident_id": incident_id,
                "window_start": window_start,
                "window_end": window_end,
            },
        )
        return [dict(r) for r in result.mappings().all()]

    def get_proxy_calls_for_timeline(
        self,
        call_ids: List[str],
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all proxy calls for incident timeline (no time window filter).

        Args:
            call_ids: List of proxy call IDs
            limit: Maximum number of calls to return

        Returns:
            List of proxy call rows as dicts, ordered by created_at
        """
        if not call_ids:
            return []

        # Build parameterized IN clause
        id_params = {f"cid_{i}": cid for i, cid in enumerate(call_ids)}
        id_placeholders = ", ".join(f":cid_{i}" for i in range(len(call_ids)))

        result = self._session.execute(
            text(
                f"SELECT * FROM proxy_calls WHERE id IN ({id_placeholders}) "
                "ORDER BY created_at LIMIT :lim"
            ),
            {**id_params, "lim": limit},
        )
        return [dict(r) for r in result.mappings().all()]

    def get_all_incident_events(
        self,
        incident_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all incident events for an incident (no time window).

        Args:
            incident_id: Incident ID

        Returns:
            List of incident event rows as dicts, ordered by created_at
        """
        result = self._session.execute(
            text(
                "SELECT * FROM incident_events WHERE incident_id = :incident_id "
                "ORDER BY created_at"
            ),
            {"incident_id": incident_id},
        )
        return [dict(r) for r in result.mappings().all()]

    def get_proxy_call_by_id(
        self,
        call_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single proxy call by ID.

        Args:
            call_id: Proxy call ID

        Returns:
            Proxy call row as dict if found, None otherwise
        """
        result = self._session.execute(
            text("SELECT * FROM proxy_calls WHERE id = :id"),
            {"id": call_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    def get_incident_event_by_id(
        self,
        event_id: str,
        incident_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single incident event by ID with incident validation.

        Args:
            event_id: Incident event ID
            incident_id: Incident ID (for validation)

        Returns:
            Incident event row as dict if found and belongs to incident, None otherwise
        """
        result = self._session.execute(
            text(
                "SELECT * FROM incident_events WHERE id = :id AND incident_id = :incident_id"
            ),
            {"id": event_id, "incident_id": incident_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None


def get_replay_read_driver(session: Session) -> ReplayReadDriver:
    """Factory function to get ReplayReadDriver instance."""
    return ReplayReadDriver(session)


__all__ = [
    "ReplayReadDriver",
    "get_replay_read_driver",
]
