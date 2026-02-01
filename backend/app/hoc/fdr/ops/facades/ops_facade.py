# Layer: L3 — Adapter
# Product: founder-console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Ops Domain Facade - Centralized access to ops operations
# Callers: Ops API routes (L2)
# Allowed Imports: L4 ops services, L5, L6 (models, db)
# Forbidden Imports: L1, L2, L3
# Reference: API-001 Guardrail (Domain Facade Required)

"""
Ops Domain Facade

This facade provides the external interface to the Ops domain.
All code outside the Ops domain MUST use this facade.

Why Facades Matter:
- Authorization checks happen in one place
- Audit logging is centralized
- Domain encapsulation is preserved
- Interface stability for external callers

Usage:
    from app.services.ops import get_ops_facade

    facade = get_ops_facade()
    incidents = facade.get_active_incidents(since, until)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.ops.facade")


class OpsFacade:
    """
    Facade for Ops domain operations.

    This is the ONLY entry point for external code to interact with
    ops services. Direct imports of OpsIncidentService from outside
    this domain are forbidden (API-001).
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize facade with optional database URL.

        Args:
            db_url: Optional database URL override. If not provided,
                    uses DATABASE_URL environment variable.
        """
        self._db_url = db_url
        self._ops_incident_service = None
        self._error_store = None

    @property
    def _store(self):
        """Lazy-load error store."""
        if self._error_store is None:
            from app.hoc.fdr.ops.drivers.error_store import DatabaseErrorStore
            self._error_store = DatabaseErrorStore(db_url=self._db_url)
        return self._error_store

    @property
    def _incident_service(self):
        """Lazy-load ops incident service with proper error store."""
        if self._ops_incident_service is None:
            from app.hoc.fdr.ops.engines.ops_incident_service import OpsIncidentService
            self._ops_incident_service = OpsIncidentService(error_store=self._store)
        return self._ops_incident_service

    # =========================================================================
    # Incident Aggregation Operations (for api/ops.py)
    # =========================================================================

    def get_active_incidents(
        self,
        since: datetime,
        until: Optional[datetime] = None,
        component: Optional[str] = None,
    ) -> List[Any]:
        """
        Get active incidents within a time window.

        Used by ops monitoring to query recent infrastructure incidents.

        Args:
            since: Start of time window
            until: End of time window (default: now)
            component: Optional component filter

        Returns:
            List of OpsIncident objects
        """
        logger.debug(
            "ops_facade.get_active_incidents",
            extra={"since": since.isoformat(), "until": until.isoformat() if until else "now"}
        )
        return self._incident_service.get_active_incidents(
            since=since,
            until=until,
            component=component,
        )

    def get_incident_summary(
        self,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated incident summary for a time window.

        Used by ops monitoring for dashboard summaries.

        Args:
            since: Start of time window
            until: End of time window (default: now)

        Returns:
            Summary dictionary with counts by severity
        """
        logger.debug(
            "ops_facade.get_incident_summary",
            extra={"since": since.isoformat(), "until": until.isoformat() if until else "now"}
        )
        return self._incident_service.get_incident_summary(since=since, until=until)

    # =========================================================================
    # Error Store Operations (direct access for special cases)
    # =========================================================================

    def get_error_counts_by_component(
        self,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get error counts grouped by component.

        Args:
            since: Start of time window
            until: End of time window (default: now)

        Returns:
            Dictionary mapping component name to error count
        """
        return self._store.get_error_counts_by_component(since=since, until=until)

    def get_error_counts_by_class(
        self,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get error counts grouped by error class.

        Args:
            since: Start of time window
            until: End of time window (default: now)

        Returns:
            Dictionary mapping error class to count
        """
        return self._store.get_error_counts_by_class(since=since, until=until)


# Module-level singleton accessor
_facade_instance: Optional[OpsFacade] = None


def get_ops_facade(db_url: Optional[str] = None) -> OpsFacade:
    """
    Get the ops facade instance.

    This is the recommended way to access ops operations from
    external code (outside the Ops domain).

    Args:
        db_url: Optional database URL override

    Returns:
        OpsFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = OpsFacade(db_url=db_url)
    return _facade_instance
