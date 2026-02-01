# Layer: L5 — Domain Schema
# AUDIENCE: INTERNAL
# Role: Decision contract for incident creation — L6 depends on this, L5 implements it
# Reference: PIN-511 Option B (dependency inversion)
# artifact_class: CODE

"""
Incident Decision Port (PIN-511 Option B)

Protocol that defines the decision surface of IncidentEngine (L5).
L6 incident_driver depends ONLY on this contract, never on the engine directly.

Dependency direction:
    L6 (incident_driver) → Protocol (this file) ← L5 (incident_engine implements)
    L4 (coordinator/bridge) wires them together.

This makes the L6→L5 import violation unrepresentable by construction.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class IncidentDecisionPort(Protocol):
    """Behavioral contract for incident domain decisions.

    Implemented by: IncidentEngine (L5)
    Consumed by: IncidentDriver (L6)
    Wired by: L4 (incidents bridge / coordinator)
    """

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
        """Check if a run warrants an incident and create one if so.

        Returns:
            incident_id if created, None otherwise
        """
        ...

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
        """Create an incident record for any run (success or failure).

        Returns:
            incident_id if created, None otherwise
        """
        ...

    def get_incidents_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all incidents associated with a run.

        Returns:
            List of incident dictionaries
        """
        ...
