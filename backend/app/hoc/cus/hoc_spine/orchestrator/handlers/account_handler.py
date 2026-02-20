# capability_id: CAP-012
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
            "create_project": facade.create_project,
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


class AccountMemoryPinsHandler:
    """
    Handler for account.memory_pins operations.

    Dispatches to MemoryPinsEngine methods (upsert_pin, get_pin,
    list_pins, delete_pin, cleanup_expired).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.account.L5_engines.memory_pins_engine import (
            MemoryPinsDisabledError,
            get_memory_pins_engine,
        )
        from app.hoc.cus.account.L6_drivers.memory_pins_driver import (
            get_memory_pins_driver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        if ctx.session is None:
            return OperationResult.fail(
                "Missing session in context", "MISSING_SESSION"
            )

        engine = get_memory_pins_engine()
        driver = get_memory_pins_driver(ctx.session)

        try:
            kwargs = dict(ctx.params)
            kwargs.pop("method", None)
            dispatch = {
                "upsert_pin": engine.upsert_pin,
                "get_pin": engine.get_pin,
                "list_pins": engine.list_pins,
                "delete_pin": engine.delete_pin,
                "cleanup_expired": engine.cleanup_expired,
            }
            method = dispatch.get(method_name)
            if method is None:
                return OperationResult.fail(
                    f"Unknown memory pins method: {method_name}", "UNKNOWN_METHOD"
                )

            data = await method(driver=driver, tenant_id=ctx.tenant_id, **kwargs)
            await ctx.session.commit()
            return OperationResult.ok(data)
        except MemoryPinsDisabledError as e:
            return OperationResult.fail(str(e), "FEATURE_DISABLED")
        except Exception as e:
            try:
                await ctx.session.rollback()
            except Exception:
                pass
            return OperationResult.fail(str(e), "MEMORY_PINS_ERROR")


class AccountTenantHandler:
    """
    Handler for account.tenant operations.

    PIN-520 ITER3.5: Routes tenant read operations to TenantEngine (L5).
    Dispatches to TenantEngine methods (get_tenant, get_usage_summary,
    check_run_quota, check_token_quota, list_runs).

    Sync session pattern: TenantEngine is sync, so L2 passes the sync
    session via params["sync_session"] (ctx.session is for async only).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.account.L5_engines.tenant_engine import (
            QuotaExceededError,
            get_tenant_engine,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        sync_session = ctx.params.get("sync_session")
        if not sync_session:
            return OperationResult.fail(
                "Missing 'sync_session' in params", "MISSING_SESSION"
            )

        engine = get_tenant_engine(sync_session)
        dispatch = {
            "get_tenant": engine.get_tenant,
            "get_usage_summary": engine.get_usage_summary,
            "check_run_quota": engine.check_run_quota,
            "check_token_quota": engine.check_token_quota,
            "list_runs": engine.list_runs,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown tenant method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        kwargs.pop("sync_session", None)
        if "tenant_id" not in kwargs and ctx.tenant_id:
            kwargs["tenant_id"] = ctx.tenant_id

        try:
            data = method(**kwargs)
            return OperationResult.ok(data)
        except QuotaExceededError as e:
            return OperationResult.fail(str(e), "QUOTA_EXCEEDED")
        except Exception as e:
            return OperationResult.fail(str(e), "TENANT_ERROR")


class AccountSdkAttestationHandler:
    """
    Handler for account.sdk_attestation operations.

    Provides SDK attestation persistence and query via L6 driver.
    Methods:
      - write: Persist an SDK attestation record
      - query: Fetch latest attestation for a tenant
      - has_attestation: Check if tenant has any attestation
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        sync_session = ctx.params.get("sync_session")
        if not sync_session:
            return OperationResult.fail("Missing 'sync_session' in params", "MISSING_SESSION")

        try:
            from app.hoc.cus.account.L6_drivers.sdk_attestation_driver import (
                write_attestation,
                fetch_attestation,
                has_attestation,
                compute_attestation_hash,
            )
            from app.hoc.cus.account.L5_schemas.sdk_attestation import SDKAttestationRecord
            from datetime import datetime, timezone

            if method_name == "write":
                record = SDKAttestationRecord(
                    tenant_id=ctx.tenant_id,
                    sdk_version=ctx.params.get("sdk_version", ""),
                    sdk_language=ctx.params.get("sdk_language", ""),
                    client_id=ctx.params.get("client_id"),
                    attested_at=datetime.now(timezone.utc),
                    attestation_hash=compute_attestation_hash(
                        ctx.tenant_id,
                        ctx.params.get("sdk_version", ""),
                        ctx.params.get("sdk_language", ""),
                        ctx.params.get("client_id"),
                    ),
                )
                write_attestation(sync_session, record)
                return OperationResult.ok({"attested": True, "hash": record.attestation_hash})

            elif method_name == "query":
                record = fetch_attestation(sync_session, ctx.tenant_id)
                if record is None:
                    return OperationResult.ok(None)
                return OperationResult.ok({
                    "tenant_id": record.tenant_id,
                    "sdk_version": record.sdk_version,
                    "sdk_language": record.sdk_language,
                    "client_id": record.client_id,
                    "attested_at": record.attested_at.isoformat() if record.attested_at else None,
                    "attestation_hash": record.attestation_hash,
                })

            elif method_name == "has_attestation":
                result = has_attestation(sync_session, ctx.tenant_id)
                return OperationResult.ok({"has_attestation": result})

            else:
                return OperationResult.fail(f"Unknown method: {method_name}", "UNKNOWN_METHOD")

        except Exception as e:
            return OperationResult.fail(str(e), "SDK_ATTESTATION_ERROR")


def register(registry: OperationRegistry) -> None:
    """Register account operations with the registry."""
    registry.register("account.query", AccountQueryHandler())
    registry.register("account.notifications", AccountNotificationsHandler())
    # PIN-520 Phase 1: Billing provider access
    registry.register("account.billing.provider", AccountBillingProviderHandler())
    registry.register("account.memory_pins", AccountMemoryPinsHandler())
    # PIN-520 ITER3.5: Tenant operations
    registry.register("account.tenant", AccountTenantHandler())
    # UC-002: SDK attestation persistence
    registry.register("account.sdk_attestation", AccountSdkAttestationHandler())
