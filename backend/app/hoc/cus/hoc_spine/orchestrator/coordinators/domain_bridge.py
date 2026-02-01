# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (called by L4 handlers)
#   Execution: sync/async
# Role: Cross-domain service accessor — switchboard, not brain (C4 Loop Model)
# Callers: policies_handler.py (L4), integrations/adapters/customer_logs_adapter.py
# Allowed Imports: hoc_spine, hoc.cus.* (lazy — L4 can import L5/L6)
# Forbidden Imports: L1, L2
# Reference: PIN-504 (Cross-Domain Violation Resolution), PIN-487 (Loop Model), PIN-507 (Law 4)
# artifact_class: CODE

"""
Domain Bridge (C4 — Loop Model)

Cross-domain service accessor. Switchboard, not brain.
Returns factory callables — handler binds session (Law 4, PIN-507).

Rules:
- No retry logic
- No decisions
- No state
- No session parameters (Law 4)
- Only L4 handlers and coordinators may use this

Absorbs logs_coordinator.py (PIN-504).
"""


class DomainBridge:
    """
    Cross-domain service accessor — backward-compat facade.

    PIN-510 Phase 0A: Delegates to per-domain bridges.
    New code should import per-domain bridges directly:
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges import get_incidents_bridge

    This class remains for existing callers. No new methods should be added here.

    Law 4 (PIN-507): DomainBridge never accepts session.
    It returns factory callables; the handler owns binding.
    """

    # =========================================================================
    # Legacy factory methods (delegate to per-domain bridges)
    # =========================================================================

    def logs_read_service(self):
        """Get LogsReadService singleton. Delegates to LogsBridge."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge import get_logs_bridge
        return get_logs_bridge().logs_read_service()

    def lessons_driver_factory(self):
        """Return a factory callable for LessonsDriver. Delegates to IncidentsBridge."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.incidents_bridge import get_incidents_bridge
        bridge = get_incidents_bridge()
        return lambda session: bridge.lessons_capability(session)

    def limits_read_driver_factory(self):
        """Return a factory callable for LimitsReadDriver. Delegates to ControlsBridge."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.controls_bridge import get_controls_bridge
        bridge = get_controls_bridge()
        return lambda session: bridge.limits_query_capability(session)

    def policy_limits_driver_factory(self):
        """Return a factory callable for PolicyLimitsDriver. Delegates to ControlsBridge."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.controls_bridge import get_controls_bridge
        bridge = get_controls_bridge()
        return lambda session: bridge.policy_limits_capability(session)

    # =========================================================================
    # PIN-508 Phase 2: Capability-narrowed accessors (delegate to per-domain bridges)
    # =========================================================================

    def lessons_capability(self, session):
        """Return LessonsQueryCapability. Delegates to IncidentsBridge."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.incidents_bridge import get_incidents_bridge
        return get_incidents_bridge().lessons_capability(session)

    def limits_query_capability(self, session):
        """Return LimitsQueryCapability. Delegates to ControlsBridge."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.controls_bridge import get_controls_bridge
        return get_controls_bridge().limits_query_capability(session)

    def policy_limits_capability(self, session):
        """Return PolicyLimitsCapability. Delegates to ControlsBridge."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.controls_bridge import get_controls_bridge
        return get_controls_bridge().policy_limits_capability(session)


# =============================================================================
# Singleton
# =============================================================================

_domain_bridge_instance = None


def get_domain_bridge() -> DomainBridge:
    """Get the singleton DomainBridge instance."""
    global _domain_bridge_instance
    if _domain_bridge_instance is None:
        _domain_bridge_instance = DomainBridge()
    return _domain_bridge_instance


__all__ = [
    "DomainBridge",
    "get_domain_bridge",
]
