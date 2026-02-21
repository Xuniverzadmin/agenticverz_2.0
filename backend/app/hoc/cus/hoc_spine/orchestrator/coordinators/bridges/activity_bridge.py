# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Role: Per-domain bridge for activity capabilities
# Reference: PIN-510 Phase 0A (G1 mitigation — no god object)
# artifact_class: CODE

"""
Activity Bridge (PIN-510)

Domain-scoped capability accessor for activity domain.
"""


class ActivityBridge:
    """Capabilities for activity domain. Max 5 methods."""

    def activity_query_capability(self, session):
        """Return activity query capability for the given session."""
        from app.hoc.cus.activity.L5_engines.activity_facade import ActivityFacade
        return ActivityFacade()


# Singleton
_instance = None


def get_activity_bridge() -> ActivityBridge:
    """Get the singleton ActivityBridge instance."""
    global _instance
    if _instance is None:
        _instance = ActivityBridge()
    return _instance


# =============================================================================
# ACTIVITY ENGINE BRIDGE (extends ActivityBridge to avoid 5-method limit)
# =============================================================================


class ActivityEngineBridge:
    """Extended capabilities for activity domain coordinators. Max 5 methods.

    PIN-520: These capabilities are injected into L5 ActivityFacade so it
    doesn't need to import L4 coordinators directly.
    """

    def run_evidence_coordinator_capability(self):
        """
        Return RunEvidenceCoordinator for cross-domain evidence queries (PIN-520).

        Used by activity_facade.py get_run_evidence() method.
        """
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_evidence_coordinator import (
            get_run_evidence_coordinator,
        )

        return get_run_evidence_coordinator()

    def run_proof_coordinator_capability(self):
        """
        Return RunProofCoordinator for integrity proof queries (PIN-520).

        Used by activity_facade.py get_run_proof() method.
        """
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_proof_coordinator import (
            get_run_proof_coordinator,
        )

        return get_run_proof_coordinator()

    def signal_feedback_coordinator_capability(self):
        """
        Return SignalFeedbackCoordinator for feedback queries (PIN-520).

        Used by activity_facade.py _get_signal_feedback() method.
        """
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.signal_feedback_coordinator import (
            get_signal_feedback_coordinator,
        )

        return get_signal_feedback_coordinator()


_engine_bridge_instance = None


def get_activity_engine_bridge() -> ActivityEngineBridge:
    """Get the singleton ActivityEngineBridge instance."""
    global _engine_bridge_instance
    if _engine_bridge_instance is None:
        _engine_bridge_instance = ActivityEngineBridge()
    return _engine_bridge_instance


__all__ = [
    "ActivityBridge",
    "get_activity_bridge",
    "ActivityEngineBridge",
    "get_activity_engine_bridge",
]
