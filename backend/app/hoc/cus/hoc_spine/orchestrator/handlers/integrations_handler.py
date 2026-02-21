# capability_id: CAP-012
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
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.1, PIN-513 Wiring Plan #9
# artifact_class: CODE

"""
Integrations Handler (L4 Orchestrator)

Routes integrations domain operations to L5 facades and L6 drivers.
Registers four operations:
  - integrations.query → IntegrationsFacade
  - integrations.connectors → ConnectorsFacade
  - integrations.datasources → DataSourcesFacade
  - integrations.workers → WorkerRegistryService (L6 driver)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class IntegrationsQueryHandler:
    """
    Handler for integrations.query operations.

    Dispatches to IntegrationsFacade methods (list_integrations, get_integration,
    create_integration, update_integration, delete_integration, etc.).

    Sub-operation invariant evaluation (INT-DELTA audit fix):
        Write methods that have dedicated business invariants (BI-INTEG-001,
        BI-INTEG-002) are evaluated BEFORE facade dispatch via
        _METHOD_INVARIANT_MAP. This ensures invariants fire on the real
        production path (integrations.query + method dispatch), not only
        on synthetic operation names.
    """

    # Transport-level params that must NOT leak to facade method kwargs
    _STRIP_PARAMS = {"method", "sync_session", "_invariant_mode"}

    # Method-to-sub-operation mapping for invariant evaluation.
    # Only write methods with dedicated invariants are listed here.
    _METHOD_INVARIANT_MAP = {
        "enable_integration": "integration.enable",
        "disable_integration": "integration.disable",
    }

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.integrations.L5_engines.integrations_facade import (
            get_integrations_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        # --- Sub-operation invariant evaluation (INT-DELTA audit fix) ---
        # The registry evaluates invariants for "integrations.query" (BI-INTEG-003).
        # Write methods with dedicated invariants need ADDITIONAL evaluation
        # under their sub-operation name so BI-INTEG-001/002 fire on the
        # real production path.
        sub_operation = self._METHOD_INVARIANT_MAP.get(method_name)
        if sub_operation:
            self._evaluate_sub_operation_invariants(sub_operation, ctx)

        # L4 handler passes session to L5 facade (PIN-520 transaction ownership)
        facade = get_integrations_facade(session=ctx.params.get("sync_session") or ctx.session)
        dispatch = {
            "list_integrations": facade.list_integrations,
            "get_integration": facade.get_integration,
            "create_integration": facade.create_integration,
            "update_integration": facade.update_integration,
            "delete_integration": facade.delete_integration,
            "enable_integration": facade.enable_integration,
            "disable_integration": facade.disable_integration,
            "get_health_status": facade.get_health_status,
            "test_credentials": facade.test_credentials,
            "get_limits_status": facade.get_limits_status,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        # Exclude tenant_id from kwargs since handler passes it explicitly
        exclude = self._STRIP_PARAMS | {"tenant_id"}
        kwargs = {k: v for k, v in ctx.params.items()
                  if k not in exclude and not k.startswith("_")}
        data = await method(tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)

    @staticmethod
    def _evaluate_sub_operation_invariants(
        sub_operation: str, ctx: OperationContext
    ) -> None:
        """
        Evaluate business invariants for a sub-operation (e.g., integration.disable).

        Reads the invariant mode from ctx.params["_invariant_mode"] (injected
        by the registry at dispatch time). Raises BusinessInvariantViolation
        in ENFORCE/STRICT mode on failure. In MONITOR mode, logs only.
        """
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        mode_value = ctx.params.get("_invariant_mode")
        if isinstance(mode_value, InvariantMode):
            mode = mode_value
        else:
            mode = InvariantMode.MONITOR

        invariant_context = {
            "tenant_id": ctx.tenant_id,
            "operation": sub_operation,
            **{k: v for k, v in ctx.params.items()
               if not k.startswith("_") and k not in ("method", "sync_session")},
        }

        evaluate_invariants(sub_operation, invariant_context, mode)


class IntegrationsConnectorsHandler:
    """
    Handler for integrations.connectors operations.

    Dispatches to ConnectorsFacade methods (list_connectors, register_connector,
    get_connector, update_connector, delete_connector, test_connector).
    """

    # Transport-level params that must NOT leak to facade method kwargs
    _STRIP_PARAMS = {"method", "sync_session"}

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.integrations.L5_engines.connectors_facade import (
            get_connectors_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_connectors_facade(session=ctx.params.get("sync_session") or ctx.session)
        dispatch = {
            "list_connectors": facade.list_connectors,
            "get_connector": facade.get_connector,
            "register_connector": facade.register_connector,
            "update_connector": facade.update_connector,
            "delete_connector": facade.delete_connector,
            "test_connector": facade.test_connector,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        exclude = self._STRIP_PARAMS | {"tenant_id"}
        kwargs = {k: v for k, v in ctx.params.items()
                  if k not in exclude and not k.startswith("_")}
        data = await method(tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class IntegrationsDataSourcesHandler:
    """
    Handler for integrations.datasources operations.

    Dispatches to DataSourcesFacade methods (register_source, list_sources,
    get_source, update_source, delete_source, test_connection, etc.).
    """

    # Transport-level params that must NOT leak to facade method kwargs
    _STRIP_PARAMS = {"method", "sync_session"}

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.integrations.L5_engines.datasources_facade import (
            get_datasources_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_datasources_facade(session=ctx.params.get("sync_session") or ctx.session)
        dispatch = {
            "register_source": facade.register_source,
            "list_sources": facade.list_sources,
            "get_source": facade.get_source,
            "update_source": facade.update_source,
            "delete_source": facade.delete_source,
            "test_connection": facade.test_connection,
            "activate_source": facade.activate_source,
            "deactivate_source": facade.deactivate_source,
            "get_statistics": facade.get_statistics,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        exclude = self._STRIP_PARAMS | {"tenant_id"}
        kwargs = {k: v for k, v in ctx.params.items()
                  if k not in exclude and not k.startswith("_")}
        data = await method(tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class IntegrationsWorkersHandler:
    """
    Handler for integrations.workers operations.

    Dispatches to WorkerRegistryService (L6 driver) for worker discovery,
    registration, and per-tenant configuration.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.integrations.L6_drivers.worker_registry_driver import (
            get_worker_registry_service,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        svc = get_worker_registry_service(session=ctx.session)
        dispatch = {
            "list_workers": lambda: svc.list_worker_summaries(
                status=ctx.params.get("status"),
                public_only=ctx.params.get("public_only", True),
            ),
            "get_worker": lambda: svc.get_worker_details(
                worker_id=ctx.params["worker_id"],
            ),
            "get_workers_for_tenant": lambda: svc.get_workers_for_tenant(
                tenant_id=ctx.tenant_id,
                include_disabled=ctx.params.get("include_disabled", False),
            ),
            "is_available": lambda: {
                "available": svc.is_worker_available(ctx.params["worker_id"])
            },
            "get_effective_config": lambda: svc.get_effective_worker_config(
                tenant_id=ctx.tenant_id,
                worker_id=ctx.params["worker_id"],
            ),
            "register_worker": lambda: {
                "worker_id": svc.register_worker(
                    worker_id=ctx.params["worker_id"],
                    name=ctx.params["name"],
                    description=ctx.params.get("description"),
                    version=ctx.params.get("version", "1.0.0"),
                ).id
            },
            "update_status": lambda: {
                "worker_id": svc.update_worker_status(
                    worker_id=ctx.params["worker_id"],
                    status=ctx.params["status"],
                ).id
            },
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown workers method: {method_name}", "UNKNOWN_METHOD"
            )

        data = method()
        return OperationResult.ok(data)


def register(registry: OperationRegistry) -> None:
    """Register integrations operations with the registry."""
    registry.register("integrations.query", IntegrationsQueryHandler())
    registry.register("integrations.connectors", IntegrationsConnectorsHandler())
    registry.register("integrations.datasources", IntegrationsDataSourcesHandler())
    registry.register("integrations.workers", IntegrationsWorkersHandler())
