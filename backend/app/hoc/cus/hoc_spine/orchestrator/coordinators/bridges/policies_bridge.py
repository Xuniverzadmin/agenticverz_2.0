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


# Singleton
_instance = None


def get_policies_bridge() -> PoliciesBridge:
    """Get the singleton PoliciesBridge instance."""
    global _instance
    if _instance is None:
        _instance = PoliciesBridge()
    return _instance


__all__ = ["PoliciesBridge", "get_policies_bridge"]
