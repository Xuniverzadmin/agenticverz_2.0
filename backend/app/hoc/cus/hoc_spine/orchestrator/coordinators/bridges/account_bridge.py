# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Role: Per-domain bridge for account capabilities
# Reference: PIN-513 Phase 2 (account bridge gap fill)
# artifact_class: CODE

"""
Account Bridge (PIN-513)

Domain-scoped capability accessor for account domain.
"""


class AccountBridge:
    """Capabilities for account domain. Max 5 methods."""

    def account_query_capability(self, session):
        """Return account query capability for the given session."""
        from app.hoc.cus.account.L5_engines.accounts_facade import AccountsFacade
        return AccountsFacade()

    def notifications_capability(self, session):
        """Return notifications capability for the given session."""
        from app.hoc.cus.account.L5_engines.notifications_facade import NotificationsFacade
        return NotificationsFacade()

    def tenant_capability(self, session):
        """Return tenant capability for the given session."""
        from app.hoc.cus.account.L5_engines.tenant_engine import TenantEngine
        return TenantEngine(session)


# Singleton
_instance = None


def get_account_bridge() -> AccountBridge:
    """Get the singleton AccountBridge instance."""
    global _instance
    if _instance is None:
        _instance = AccountBridge()
    return _instance


__all__ = ["AccountBridge", "get_account_bridge"]
