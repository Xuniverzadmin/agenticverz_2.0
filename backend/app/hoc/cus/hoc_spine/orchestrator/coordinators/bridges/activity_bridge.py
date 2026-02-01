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


__all__ = ["ActivityBridge", "get_activity_bridge"]
