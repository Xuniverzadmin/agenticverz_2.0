# Layer: L7 — Legacy Shim (PIN-513)
# AUDIENCE: INTERNAL
# Role: No-op audit shim to sever services→HOC dependency (PIN-511, PIN-513)

"""
No-op audit shim for legacy services scheduled for deletion (PIN-511).

Replaces AuditLedgerServiceAsync / AuditLedgerService imports from HOC.
All audit methods return silently. Production audit is handled by HOC paths.
"""


class AuditLedgerShim:
    """No-op audit shim. Legacy services scheduled for deletion (PIN-511)."""

    def __init__(self, session=None):
        pass

    def __getattr__(self, name):
        async def noop(*args, **kwargs):
            pass
        return noop
