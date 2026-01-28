# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Incident (via L6 drivers)
#   Writes: Incident (via L6 drivers)
# Role: Incident Domain Engine - Internal orchestration for incident operations
# Callers: worker runtime, governance services, transaction coordinator
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, FACADE_CONSOLIDATION_PLAN.md, PIN-454 (RAC)
# Location: hoc/cus/incidents/L5_engines/incident_driver.py
# Reclassified L6→L5 (2026-01-24) - no DB operations, pure orchestration logic
#
# GOVERNANCE NOTE:
# This is the INTERNAL engine for incident operations.
# CUSTOMER-facing operations use incidents_facade.py (L2 API projection).
# Workers and governance services use this engine directly.

"""
Incident Domain Driver (INTERNAL)

This driver provides the internal interface for incident operations.
Used by workers, governance services, and transaction coordinators.

For CUSTOMER API operations, use incidents_facade.py instead.

Why Drivers (not Facades for internal use):
- Facades are API projection layers (CUSTOMER-facing)
- Drivers are orchestration layers (INTERNAL)
- Clear separation prevents confusion
- Import rules become enforceable

Usage:
    from app.hoc.cus.incidents.L5_engines.incident_driver import get_incident_driver

    driver = get_incident_driver()
    incident_id = driver.create_incident_for_run(...)
"""

import logging
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger("nova.services.incidents.driver")

# RAC integration flag (PIN-454)
RAC_ENABLED = os.getenv("RAC_ENABLED", "true").lower() == "true"


class IncidentDriver:
    """
    Driver for Incident domain operations (INTERNAL).

    This is the entry point for internal code (workers, governance)
    to interact with incident services.

    CUSTOMER-facing code should use incidents_facade.py instead.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize driver with optional database URL.

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
            # L5 engine import (migrated to HOC per SWEEP-05)
            from app.hoc.cus.incidents.L5_engines.incident_engine import IncidentEngine
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
            "driver.check_and_create_incident",
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

        PIN-454: Emits RAC acknowledgment after creation.

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
            "driver.create_incident_for_run",
            extra={"run_id": run_id, "run_status": run_status}
        )

        incident_id = None
        error = None

        try:
            incident_id = self._engine.create_incident_for_run(
                run_id=run_id,
                tenant_id=tenant_id,
                run_status=run_status,
                error_code=error_code,
                error_message=error_message,
                agent_id=agent_id,
                is_synthetic=is_synthetic,
                synthetic_scenario_id=synthetic_scenario_id,
            )
        except Exception as e:
            error = str(e)
            logger.error(
                "driver.create_incident_for_run failed",
                extra={"run_id": run_id, "error": error}
            )

        # PIN-454: Emit RAC acknowledgment
        if RAC_ENABLED:
            self._emit_ack(run_id, incident_id, error)

        return incident_id

    def _emit_ack(
        self,
        run_id: str,
        result_id: Optional[str],
        error: Optional[str],
    ) -> None:
        """
        Emit RAC acknowledgment for incident creation.

        PIN-454: Drivers emit acks after domain operations.
        """
        try:
            # L5 imports (migrated to HOC per SWEEP-04)
            from app.hoc.cus.general.L5_schemas.rac_models import AuditAction, AuditDomain, DomainAck
            from app.hoc.cus.general.L5_engines.audit_store import get_audit_store

            ack = DomainAck(
                run_id=UUID(run_id),
                domain=AuditDomain.INCIDENTS,
                action=AuditAction.CREATE_INCIDENT,
                result_id=result_id,
                error=error,
            )

            store = get_audit_store()
            store.add_ack(UUID(run_id), ack)

            logger.debug(
                "driver.emit_ack",
                extra={
                    "run_id": run_id,
                    "domain": "incidents",
                    "action": "create_incident",
                    "success": error is None,
                }
            )
        except Exception as e:
            # RAC failures should not block the driver
            logger.warning(f"Failed to emit RAC ack: {e}")

    def get_incidents_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all incidents associated with a run.

        Args:
            run_id: ID of the run

        Returns:
            List of incident dictionaries
        """
        return self._engine.get_incidents_for_run(run_id)


# Module-level singleton accessor
_driver_instance: Optional[IncidentDriver] = None


def get_incident_driver(db_url: Optional[str] = None) -> IncidentDriver:
    """
    Get the incident driver instance.

    This is the recommended way to access incident operations from
    internal code (workers, governance services).

    For CUSTOMER API operations, use get_incidents_facade() instead.

    Args:
        db_url: Optional database URL override

    Returns:
        IncidentDriver instance
    """
    global _driver_instance
    if _driver_instance is None:
        _driver_instance = IncidentDriver(db_url=db_url)
    return _driver_instance


# Backward compatibility alias (DEPRECATED - will be removed)
# This allows gradual migration from facade to driver
IncidentFacade = IncidentDriver
get_incident_facade = get_incident_driver
