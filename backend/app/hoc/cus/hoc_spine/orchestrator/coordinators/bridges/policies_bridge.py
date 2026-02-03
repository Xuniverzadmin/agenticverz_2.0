# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Role: Per-domain bridge for policies capabilities
# Reference: PIN-510 Phase 0A (G1 mitigation — no god object)
# artifact_class: CODE

"""
Policies Bridge (PIN-510)

Domain-scoped capability accessor for policies domain.
"""


class PoliciesBridge:
    """Capabilities for policies domain. Max 5 methods."""

    def customer_policy_read_capability(self, session):
        """Return customer policy read capability for the given session."""
        from app.hoc.cus.policies.L5_engines.customer_policy_read_engine import CustomerPolicyReadService
        return CustomerPolicyReadService(session)

    def policy_evaluations_capability(self, session):
        """Return policy evaluations read capability for run queries (PIN-519)."""
        from app.hoc.cus.policies.L6_drivers.policy_enforcement_driver import (
            PolicyEnforcementReadDriver,
        )
        return PolicyEnforcementReadDriver(session)

    def recovery_write_capability(self, session):
        """
        Return recovery write service for sync transaction control (PIN-520 Phase 1).

        Used by recovery_ingest.py which needs explicit commit/rollback control.
        """
        from app.hoc.cus.policies.L6_drivers.recovery_write_driver import (
            RecoveryWriteService,
        )
        return RecoveryWriteService(session)

    def recovery_matcher_capability(self, session):
        """
        Return recovery matcher for pattern matching (PIN-520 Phase 1).

        Used by recovery.py for failure pattern matching and suggestion generation.
        """
        from app.hoc.cus.policies.L6_drivers.recovery_matcher import RecoveryMatcher
        return RecoveryMatcher(session)


# Singleton
_instance = None


def get_policies_bridge() -> PoliciesBridge:
    """Get the singleton PoliciesBridge instance."""
    global _instance
    if _instance is None:
        _instance = PoliciesBridge()
    return _instance


__all__ = ["PoliciesBridge", "get_policies_bridge"]
