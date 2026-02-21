# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Role: Per-domain bridge for api_keys capabilities
# Reference: PIN-510 Phase 0A (G1 mitigation — no god object)
# artifact_class: CODE

"""
API Keys Bridge (PIN-510)

Domain-scoped capability accessor for api_keys domain.
"""


class ApiKeysBridge:
    """Capabilities for api_keys domain. Max 5 methods."""

    def keys_read_capability(self, session):
        """Return keys read capability for the given session."""
        from app.hoc.cus.api_keys.L5_engines.keys_engine import KeysReadEngine
        return KeysReadEngine(session)

    def keys_write_capability(self, session):
        """Return keys write capability for the given session."""
        from app.hoc.cus.api_keys.L5_engines.keys_engine import KeysWriteEngine
        return KeysWriteEngine(session)


# Singleton
_instance = None


def get_api_keys_bridge() -> ApiKeysBridge:
    """Get the singleton ApiKeysBridge instance."""
    global _instance
    if _instance is None:
        _instance = ApiKeysBridge()
    return _instance


__all__ = ["ApiKeysBridge", "get_api_keys_bridge"]
