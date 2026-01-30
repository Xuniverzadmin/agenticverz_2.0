# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Account domain handler — routes account operations to L5 facades via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.account.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.1
# artifact_class: CODE

"""
Account Handler (L4 Orchestrator)

Routes account domain operations to L5 facades.
Registers two operations:
  - account.query → AccountsFacade
  - account.notifications → NotificationsFacade
"""

from app.hoc.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class AccountQueryHandler:
    """
    Handler for account.query operations.

    Dispatches to AccountsFacade methods (list_projects, get_project_detail,
    list_users, get_user_detail, get_profile, get_billing_summary, etc.).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.account.L5_engines.accounts_facade import get_accounts_facade

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_accounts_facade()
        method = getattr(facade, method_name, None)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class AccountNotificationsHandler:
    """
    Handler for account.notifications operations.

    Dispatches to NotificationsFacade methods (send_notification,
    list_notifications, get_notification, mark_as_read, etc.).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.account.L5_engines.notifications_facade import (
            get_notifications_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_notifications_facade()
        method = getattr(facade, method_name, None)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


def register(registry: OperationRegistry) -> None:
    """Register account operations with the registry."""
    registry.register("account.query", AccountQueryHandler())
    registry.register("account.notifications", AccountNotificationsHandler())
