# Layer: L5 — Domain Engine
# Product: system-wide
# Role: Invoke audit compatibility surface
# Callers: HOC internal agent runtime
# capability_id: CAP-008

"""Compatibility wrapper for invoke audit.

The canonical implementation lives in `app.agents.services.invoke_audit_driver`
(L6 data-access shape). This module preserves the historical names used by HOC
callers.
"""

from app.agents.services.invoke_audit_driver import (
    InvokeAuditEntry,
    InvokeAuditDriver,
    get_invoke_audit_driver,
)

InvokeAuditService = InvokeAuditDriver


def get_invoke_audit_service() -> InvokeAuditService:
    return get_invoke_audit_driver()


__all__ = [
    "InvokeAuditEntry",
    "InvokeAuditService",
    "get_invoke_audit_service",
]
