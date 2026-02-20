# capability_id: CAP-001
# Layer: L6 — Domain Driver
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Incident (via decision port)
#   Writes: Incident (via decision port)
# Role: Incident Domain Driver — delegates to IncidentDecisionPort (L5 contract)
# Callers: worker runtime, governance services, transaction coordinator
# Allowed Imports: L5_schemas
# Forbidden Imports: L1, L2, L3, L5_engines, sqlalchemy (runtime)
# Reference: PIN-470, FACADE_CONSOLIDATION_PLAN.md, PIN-454 (RAC), PIN-511 Option B
# Location: hoc/cus/incidents/L6_drivers/incident_driver.py
# PIN-511 Option B: Dependency inverted — depends on Protocol, not engine
# artifact_class: CODE
#
# GOVERNANCE NOTE:
# This is the INTERNAL driver for incident operations.
# CUSTOMER-facing operations use incidents_facade.py (L2 API projection).
# Workers and governance services use this driver directly.

"""
Incident Domain Driver (INTERNAL)

This driver provides the internal interface for incident operations.
Used by workers, governance services, and transaction coordinators.

For CUSTOMER API operations, use incidents_facade.py instead.

PIN-511 Option B — Dependency Inversion:
    Before: L6 driver → imports L5 engine (Law 1 violation)
    After:  L6 driver → imports L5_schemas Protocol (legal)
            L5 engine → implements Protocol
            L4 → wires them together

Usage:
    from app.hoc.cus.incidents.L6_drivers.incident_driver import IncidentDriver

    # L4 wiring (coordinator/bridge):
    engine = IncidentEngine(db_url=...)
    driver = IncidentDriver(decision_port=engine)

    # Or use the singleton (wired lazily via L4):
    driver = get_incident_driver()
    incident_id = driver.create_incident_for_run(...)
"""

import logging
import os
from typing import Any, Callable, Dict, List, Optional
from app.hoc.cus.incidents.L5_schemas.incident_decision_port import (
    IncidentDecisionPort,
)

logger = logging.getLogger("nova.services.incidents.driver")

# RAC integration flag (PIN-454)
RAC_ENABLED = os.getenv("RAC_ENABLED", "true").lower() == "true"


class IncidentDriver:
    """
    Driver for Incident domain operations (INTERNAL).

    This is the entry point for internal code (workers, governance)
    to interact with incident services.

    CUSTOMER-facing code should use incidents_facade.py instead.

    PIN-511 Option B: Accepts IncidentDecisionPort (Protocol) — never
    imports L5_engines directly. L4 wires the engine at construction time.
    """

    def __init__(
        self,
        decision_port: IncidentDecisionPort,
        ack_emitter: Optional[Callable[[str, Optional[str], Optional[str]], None]] = None,
    ):
        """
        Initialize driver with a decision port.

        Args:
            decision_port: L5 engine implementing IncidentDecisionPort.
                          Wired by L4 (bridge/coordinator).
            ack_emitter: Optional callback for emitting post-operation acknowledgements.
                         Wired by L4. This driver must not import hoc_spine.
        """
        self._decision = decision_port
        self._ack_emitter = ack_emitter

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
        return self._decision.check_and_create_incident(
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
            incident_id = self._decision.create_incident_for_run(
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

        # PIN-454: Emit RAC acknowledgment (wired by L4; no hoc_spine imports in L6)
        if RAC_ENABLED and self._ack_emitter is not None:
            self._emit_ack(run_id, incident_id, error)

        return incident_id

    def _emit_ack(
        self,
        run_id: str,
        result_id: Optional[str],
        error: Optional[str],
    ) -> None:
        """
        Emit RAC acknowledgment for incident creation (injected).

        PIN-454: Drivers emit acks after domain operations.
        Contract: This driver must not import hoc_spine; L4 wires the emitter.
        """
        try:
            if self._ack_emitter is None:
                return
            self._ack_emitter(run_id, result_id, error)

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
        return self._decision.get_incidents_for_run(run_id)


# Backward compatibility alias (DEPRECATED - will be removed)
IncidentFacade = IncidentDriver
