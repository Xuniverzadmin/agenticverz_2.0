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
    Cross-domain service accessor.

    Provides lazy-loaded factory callables for services in other domains.
    All imports are lazy to avoid circular dependencies.
    L4 handlers bind session via the returned factories.

    Law 4 (PIN-507): DomainBridge never accepts session.
    It returns factory callables; the handler owns binding.

    Rules:
    - No retry logic
    - No decisions
    - No state
    - Only L4 handlers and coordinators may use this
    """

    def logs_read_service(self):
        """Get LogsReadService singleton (absorbs logs_coordinator.py)."""
        from app.hoc.cus.logs.L5_engines.logs_read_engine import get_logs_read_service
        return get_logs_read_service()

    def lessons_driver_factory(self):
        """Return a factory callable for LessonsDriver. Handler binds session.

        Usage:
            make_driver = bridge.lessons_driver_factory()
            driver = make_driver(session)  # handler owns binding
        """
        from app.hoc.cus.incidents.L6_drivers.lessons_driver import LessonsDriver
        return lambda session: LessonsDriver(session)

    def limits_read_driver_factory(self):
        """Return a factory callable for LimitsReadDriver. Handler binds session.

        Usage:
            make_driver = bridge.limits_read_driver_factory()
            driver = make_driver(session)  # handler owns binding
        """
        from app.hoc.cus.controls.L6_drivers.limits_read_driver import LimitsReadDriver
        return lambda session: LimitsReadDriver(session)

    def policy_limits_driver_factory(self):
        """Return a factory callable for PolicyLimitsDriver. Handler binds session.

        Usage:
            make_driver = bridge.policy_limits_driver_factory()
            driver = make_driver(session)  # handler owns binding
        """
        from app.hoc.cus.controls.L6_drivers.policy_limits_driver import PolicyLimitsDriver
        return lambda session: PolicyLimitsDriver(session)


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
