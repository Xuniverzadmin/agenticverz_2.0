# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Role: Per-domain bridge for controls capabilities
# Reference: PIN-510 Phase 0A (G1 mitigation — no god object)
# artifact_class: CODE

"""
Controls Bridge (PIN-510)

Domain-scoped capability accessor for controls domain.
Returns capability-satisfying objects bound to caller's session.
"""


class ControlsBridge:
    """Capabilities for controls domain. Max 5 methods."""

    def limits_query_capability(self, session):
        """Return LimitsQueryCapability for the given session."""
        from app.hoc.cus.controls.L6_drivers.limits_read_driver import LimitsReadDriver
        return LimitsReadDriver(session)

    def policy_limits_capability(self, session):
        """Return PolicyLimitsCapability for the given session."""
        from app.hoc.cus.controls.L6_drivers.policy_limits_driver import PolicyLimitsDriver
        return PolicyLimitsDriver(session)

    def killswitch_capability(self, session):
        """Return killswitch read capability for the given session."""
        from app.hoc.cus.controls.L6_drivers.killswitch_read_driver import get_killswitch_read_driver
        return get_killswitch_read_driver(session)

    def limit_breaches_capability(self, session):
        """Return limit breaches read capability for run queries (PIN-519)."""
        from app.hoc.cus.controls.L6_drivers.limits_read_driver import LimitsReadDriver
        return LimitsReadDriver(session)

    def scoped_execution_capability(self):
        """
        Return scoped execution module for risk-gated recovery actions (PIN-L2-PURITY).

        Used by recovery.py for scoped execution of recovery actions.
        Provides: test_recovery_scope, create_recovery_scope, execute_with_scope,
                  validate_scope_required, get_scope_store, and exception types.
        """
        from app.hoc.cus.controls.L6_drivers import scoped_execution

        return scoped_execution


# Singleton
_instance = None


def get_controls_bridge() -> ControlsBridge:
    """Get the singleton ControlsBridge instance."""
    global _instance
    if _instance is None:
        _instance = ControlsBridge()
    return _instance


__all__ = ["ControlsBridge", "get_controls_bridge"]
