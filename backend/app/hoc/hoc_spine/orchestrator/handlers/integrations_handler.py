# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Integrations domain handler — routes integrations operations to L5 facades via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.integrations.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.1
# artifact_class: CODE

"""
Integrations Handler (L4 Orchestrator)

Routes integrations domain operations to L5 facades.
Registers three operations:
  - integrations.query → IntegrationsFacade
  - integrations.connectors → ConnectorsFacade
  - integrations.datasources → DataSourcesFacade
"""

from app.hoc.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class IntegrationsQueryHandler:
    """
    Handler for integrations.query operations.

    Dispatches to IntegrationsFacade methods (list_integrations, get_integration,
    create_integration, update_integration, delete_integration, etc.).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.integrations.L5_engines.integrations_facade import (
            get_integrations_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_integrations_facade()
        method = getattr(facade, method_name, None)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class IntegrationsConnectorsHandler:
    """
    Handler for integrations.connectors operations.

    Dispatches to ConnectorsFacade methods (list_connectors, register_connector,
    get_connector, update_connector, delete_connector, test_connector).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.integrations.L5_engines.connectors_facade import (
            get_connectors_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_connectors_facade()
        method = getattr(facade, method_name, None)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class IntegrationsDataSourcesHandler:
    """
    Handler for integrations.datasources operations.

    Dispatches to DataSourcesFacade methods (register_source, list_sources,
    get_source, update_source, delete_source, test_connection, etc.).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.integrations.L5_engines.datasources_facade import (
            get_datasources_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_datasources_facade()
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
    """Register integrations operations with the registry."""
    registry.register("integrations.query", IntegrationsQueryHandler())
    registry.register("integrations.connectors", IntegrationsConnectorsHandler())
    registry.register("integrations.datasources", IntegrationsDataSourcesHandler())
