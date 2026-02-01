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


def register(registry: OperationRegistry) -> None:
    """Register api_keys operations with the registry."""
    registry.register("api_keys.query", ApiKeysQueryHandler())
