# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Role: Incident Domain Facade - Centralized access to incident operations
# Callers: API routes, worker runtime, governance services
# Allowed Imports: L4 incident services, L5, L6 (models, db)
# Forbidden Imports: L1, L2, L3
# Reference: API-001 Guardrail (Domain Facade Required)

"""
Incident Domain Facade

This facade provides the external interface to the Incidents domain.
All code outside the Incidents domain MUST use this facade.

Why Facades Matter:
- Authorization checks happen in one place
- Audit logging is centralized
- Domain encapsulation is preserved
- Interface stability for external callers

Usage:
    from app.services.incidents.facade import get_incident_facade

    facade = get_incident_facade()
    incident_id = facade.create_incident_for_run(...)
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.incidents.facade")


class IncidentFacade:
    """
    Facade for Incident domain operations.

    This is the ONLY entry point for external code to interact with
    incident services. Direct imports of IncidentEngine from outside
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
        self._incident_engine = None

    @property
    def _engine(self):
        """Lazy-load incident engine."""
        if self._incident_engine is None:
            from app.services.incident_engine import IncidentEngine
            self._incident_engine = IncidentEngine(db_url=self._db_url)
        return self._incident_engine

    # =========================================================================
    # Run Lifecycle Operations (for worker/runner.py)
    # =========================================================================

    def check_and_create_incident(
        self,
        run_id: str,
        status: str,
        error_message: Optional[str] = None,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Check if an incident should be created for a run and create it.

        This is the primary method for the worker runtime to create
        incidents from failed runs.

        Args:
            run_id: ID of the run
            status: Run status (e.g., "failed")
            error_message: Error message if run failed
            tenant_id: Tenant scope
            agent_id: Agent that executed the run
            is_synthetic: Whether this is a synthetic/test run
            synthetic_scenario_id: SDSR scenario ID if synthetic

        Returns:
            incident_id if created, None otherwise
        """
        logger.debug(
            "facade.check_and_create_incident",
            extra={"run_id": run_id, "status": status}
        )
        return self._engine.check_and_create_incident(
            run_id=run_id,
            status=status,
            error_message=error_message,
            tenant_id=tenant_id,
            agent_id=agent_id,
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
        )

    def create_incident_for_run(
        self,
        run_id: str,
        tenant_id: str,
        run_status: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        agent_id: Optional[str] = None,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create an incident record for any run (success or failure).

        PIN-407: Success as First-Class Data
        Every run produces an incident record with explicit outcome.

        Args:
            run_id: ID of the run
            tenant_id: Tenant scope
            run_status: Run outcome (SUCCESS, FAILED, BLOCKED, etc.)
            error_code: Error code if applicable
            error_message: Error message if applicable
            agent_id: Agent that executed the run
            is_synthetic: Whether this is a synthetic/test run
            synthetic_scenario_id: SDSR scenario ID if synthetic

        Returns:
            incident_id if created, None otherwise
        """
        logger.debug(
            "facade.create_incident_for_run",
            extra={"run_id": run_id, "run_status": run_status}
        )
        return self._engine.create_incident_for_run(
            run_id=run_id,
            tenant_id=tenant_id,
            run_status=run_status,
            error_code=error_code,
            error_message=error_message,
            agent_id=agent_id,
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
        )

    def get_incidents_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all incidents associated with a run.

        Args:
            run_id: ID of the run

        Returns:
            List of incident dictionaries
        """
        return self._engine.get_incidents_for_run(run_id)


# Module-level singleton accessor (matches get_incident_engine pattern)
_facade_instance: Optional[IncidentFacade] = None


def get_incident_facade(db_url: Optional[str] = None) -> IncidentFacade:
    """
    Get the incident facade instance.

    This is the recommended way to access incident operations from
    external code (outside the Incidents domain).

    Args:
        db_url: Optional database URL override

    Returns:
        IncidentFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = IncidentFacade(db_url=db_url)
    return _facade_instance
