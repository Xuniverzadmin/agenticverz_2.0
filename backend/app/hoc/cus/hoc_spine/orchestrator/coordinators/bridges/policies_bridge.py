# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Role: Per-domain bridge for policies capabilities
# Reference: PIN-510 Phase 0A (G1 mitigation — no god object)
# artifact_class: CODE

"""
Policies Bridge (PIN-510)

Domain-scoped capability accessor for policies domain.
"""

from contextlib import contextmanager


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

    def recovery_read_capability(self, session):
        """
        Return recovery read driver for DB read operations (L2 first-principles purity).

        Used by recovery.py for candidate detail, actions list, etc.
        Removes session.execute() from L2.
        """
        from app.hoc.cus.policies.L6_drivers.recovery_read_driver import RecoveryReadDriver
        return RecoveryReadDriver(session)


# =============================================================================
# POLICIES ENGINE BRIDGE (extends PoliciesBridge to avoid 5-method limit)
# =============================================================================


class PoliciesEngineBridge:
    """Extended capabilities for policies domain engines. Max 5 methods."""

    def prevention_hook_capability(self):
        """
        Return prevention hook engine for response evaluation (PIN-L2-PURITY).

        Used by guard.py for evaluating AI responses against prevention policies.
        """
        from app.hoc.cus.policies.L5_engines import prevention_hook

        return prevention_hook

    def policy_engine_capability(self):
        """
        Return policy engine for violation queries and pre-checks (PIN-L2-PURITY).

        Used by policy.py for policy enforcement.
        """
        from app.hoc.cus.policies.L5_engines.engine import get_policy_engine

        return get_policy_engine()

    def policy_engine_class_capability(self):
        """
        Return PolicyEngine class for direct instantiation (PIN-L2-PURITY).

        Used by workers.py which instantiates PolicyEngine directly.
        """
        from app.hoc.cus.policies.L5_engines.engine import PolicyEngine

        return PolicyEngine

    def governance_runtime_capability(self):
        """
        Return runtime_switch module for governance state management (PIN-520).

        Used by governance_facade.py for kill switch, degraded mode, etc.
        L4 authority owns these decisions; L5 receives via injection.
        """
        from app.hoc.cus.hoc_spine.authority import runtime_switch

        return runtime_switch

    def governance_config_capability(self):
        """
        Return get_governance_config function for failure mode config (PIN-520).

        Used by failure_mode_handler.py to get governance configuration.
        """
        from app.hoc.cus.hoc_spine.authority.profile_policy_mode import (
            get_governance_config,
        )

        return get_governance_config

    def sandbox_engine_capability(self):
        """
        Return sandbox engine module (GAP-174).

        Exposes SandboxService + policy constructs for live execution sandboxing.
        """
        from app.hoc.cus.policies.L5_engines import sandbox_engine

        return sandbox_engine

    @contextmanager
    def policy_engine_write_context(self):
        """L4 managed write context for PolicyEngine operations.

        All writes within this context share a single connection.
        Commits on clean exit. PIN-520: L4 owns transaction boundaries.

        PIN-520 Phase 3 NOTE: Currently ZERO callers. PolicyEngine writes
        use _write_conn() standalone mode (auto-commit per write).
        Wiring all call-sites through this context is a future refactor.
        """
        from app.hoc.cus.policies.L5_engines.engine import get_policy_engine

        engine = get_policy_engine()
        with engine.driver.managed_connection() as conn:
            yield engine
            conn.commit()


_engine_bridge_instance = None


def get_policies_engine_bridge() -> PoliciesEngineBridge:
    """Get the singleton PoliciesEngineBridge instance."""
    global _engine_bridge_instance
    if _engine_bridge_instance is None:
        _engine_bridge_instance = PoliciesEngineBridge()
    return _engine_bridge_instance


# Singleton
_instance = None


def get_policies_bridge() -> PoliciesBridge:
    """Get the singleton PoliciesBridge instance."""
    global _instance
    if _instance is None:
        _instance = PoliciesBridge()
    return _instance


__all__ = [
    "PoliciesBridge",
    "get_policies_bridge",
    "PoliciesEngineBridge",
    "get_policies_engine_bridge",
]
