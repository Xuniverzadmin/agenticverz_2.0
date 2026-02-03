# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Role: Per-domain bridge for logs capabilities
# Reference: PIN-510 Phase 0A (G1 mitigation — no god object)
# artifact_class: CODE

"""
Logs Bridge (PIN-510)

Domain-scoped capability accessor for logs domain.
"""


class LogsBridge:
    """Capabilities for logs domain. Max 5 methods."""

    def logs_read_service(self):
        """Return LogsReadService singleton."""
        from app.hoc.cus.logs.L5_engines.logs_read_engine import get_logs_read_service
        return get_logs_read_service()

    def traces_store_capability(self):
        """Return TraceStore for run-scoped trace queries (PIN-519)."""
        from app.hoc.cus.logs.L6_drivers.traces_store import SQLiteTraceStore
        return SQLiteTraceStore()

    def audit_ledger_read_capability(self, session):
        """Return audit ledger read driver for signal feedback queries (PIN-519)."""
        from app.hoc.cus.logs.L6_drivers.audit_ledger_read_driver import (
            get_audit_ledger_read_driver,
        )
        return get_audit_ledger_read_driver(session)


# Singleton
_instance = None


def get_logs_bridge() -> LogsBridge:
    """Get the singleton LogsBridge instance."""
    global _instance
    if _instance is None:
        _instance = LogsBridge()
    return _instance


__all__ = ["LogsBridge", "get_logs_bridge"]
