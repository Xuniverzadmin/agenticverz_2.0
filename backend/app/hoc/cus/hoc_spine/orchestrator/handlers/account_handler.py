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

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
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
        dispatch = {
            "list_projects": facade.list_projects,
            "get_project_detail": facade.get_project_detail,
            "list_users": facade.list_users,
            "get_user_detail": facade.get_user_detail,
            "get_profile": facade.get_profile,
            "get_billing_summary": facade.get_billing_summary,
        }
        method = dispatch.get(method_name)
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
        dispatch = {
            "send_notification": facade.send_notification,
            "list_notifications": facade.list_notifications,
            "get_notification": facade.get_notification,
            "mark_as_read": facade.mark_as_read,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class AccountBillingProviderHandler:
    """
    Handler for account.billing.provider operations.

    PIN-520 Phase 1: Routes billing provider access through L4 registry.
    Dispatches to billing_provider_engine (get_billing_provider).

    Methods:
      - get_provider: Get billing provider for tenant
      - get_state: Get billing state for tenant
      - get_plan: Get current plan for tenant
      - get_limits: Get limits for tenant
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.account.L5_engines.billing_provider_engine import (
            get_billing_provider,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        try:
            provider = get_billing_provider()

            if method_name == "get_provider":
                # Return provider instance indicator
                return OperationResult.ok({"available": True})

            elif method_name == "get_state":
                state = provider.get_billing_state(ctx.tenant_id)
                return OperationResult.ok({"state": state.value if hasattr(state, "value") else str(state)})

            elif method_name == "get_plan":
                plan = provider.get_plan(ctx.tenant_id)
                return OperationResult.ok({"plan": plan.value if hasattr(plan, "value") else str(plan)})

            elif method_name == "get_limits":
                limits = provider.get_limits(ctx.tenant_id)
                return OperationResult.ok({"limits": limits.__dict__ if hasattr(limits, "__dict__") else limits})

            elif method_name == "allows_usage":
                state = provider.get_billing_state(ctx.tenant_id)
                allows = state.allows_usage() if hasattr(state, "allows_usage") else True
                return OperationResult.ok({"allows_usage": allows})

            else:
                return OperationResult.fail(
                    f"Unknown billing provider method: {method_name}", "UNKNOWN_METHOD"
                )
        except Exception as e:
            return OperationResult.fail(str(e), "BILLING_ERROR")


def register(registry: OperationRegistry) -> None:
    """Register account operations with the registry."""
    registry.register("account.query", AccountQueryHandler())
    registry.register("account.notifications", AccountNotificationsHandler())
    # PIN-520 Phase 1: Billing provider access
    registry.register("account.billing.provider", AccountBillingProviderHandler())
