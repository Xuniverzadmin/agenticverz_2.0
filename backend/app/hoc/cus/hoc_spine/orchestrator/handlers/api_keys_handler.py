# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: API Keys domain handler — routes api_keys operations to L5 facade via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.api_keys.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.1
# artifact_class: CODE

"""
API Keys Handler (L4 Orchestrator)

Routes api_keys domain operations to the L5 ApiKeysFacade.
Registered as "api_keys.query" in the OperationRegistry.
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class ApiKeysQueryHandler:
    """
    Handler for api_keys.query operations.

    Dispatches to ApiKeysFacade methods (list_api_keys, get_api_key_detail).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.api_keys.L5_engines.api_keys_facade import (
            get_api_keys_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_api_keys_facade()
        dispatch = {
            "list_api_keys": facade.list_api_keys,
            "get_api_key_detail": facade.get_api_key_detail,
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


class ApiKeysWriteHandler:
    """
    Handler for api_keys.write operations.

    PIN-520 ITER3.5: Routes API key write operations to TenantEngine (L5).
    Dispatches to TenantEngine methods (create_api_key, revoke_api_key,
    list_api_keys).

    L4 owns transaction boundary: commits after write methods.
    Sync session pattern: TenantEngine is sync, so L2 passes the sync
    session via params["sync_session"].
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

        try:
            if method_name == "create_api_key":
                full_key, api_key = engine.create_api_key(
                    tenant_id=ctx.params["tenant_id"],
                    name=ctx.params["name"],
                    user_id=ctx.params["user_id"],
                    permissions=ctx.params.get("permissions"),
                    allowed_workers=ctx.params.get("allowed_workers"),
                    expires_in_days=ctx.params.get("expires_in_days"),
                    rate_limit_rpm=ctx.params.get("rate_limit_rpm"),
                    max_concurrent_runs=ctx.params.get("max_concurrent_runs"),
                )
                # L4 transaction boundary: commit after write
                sync_session.commit()
                return OperationResult.ok({"full_key": full_key, "api_key": api_key})

            elif method_name == "revoke_api_key":
                api_key = engine.revoke_api_key(
                    key_id=ctx.params["key_id"],
                    reason=ctx.params.get("reason", "Manual revocation"),
                    user_id=ctx.params.get("user_id"),
                )
                # L4 transaction boundary: commit after write
                sync_session.commit()
                return OperationResult.ok(api_key)

            elif method_name == "list_api_keys":
                keys = engine.list_api_keys(
                    tenant_id=ctx.params["tenant_id"],
                    include_revoked=ctx.params.get("include_revoked", False),
                )
                return OperationResult.ok(keys)

            else:
                return OperationResult.fail(
                    f"Unknown api_keys write method: {method_name}", "UNKNOWN_METHOD"
                )
        except QuotaExceededError as e:
            return OperationResult.fail(str(e), "QUOTA_EXCEEDED")
        except Exception as e:
            return OperationResult.fail(str(e), "API_KEYS_WRITE_ERROR")


def register(registry: OperationRegistry) -> None:
    """Register api_keys operations with the registry."""
    registry.register("api_keys.query", ApiKeysQueryHandler())
    # PIN-520 ITER3.5: API key write operations
    registry.register("api_keys.write", ApiKeysWriteHandler())
