# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: FOUNDER
# Product: ops-console
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Ops domain handler — routes cost intelligence operations to L5 engine
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.ops.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# artifact_class: CODE

"""
Ops Handler (L4 Orchestrator)

Routes ops domain operations to L5 cost ops engine.
Registers one operation:
  - ops.cost → CostOpsEngine (overview, anomalies, tenants, customer_drilldown)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class CostOpsHandler:
    """
    Handler for ops.cost operations.

    Dispatches to CostOpsEngine methods:
      - get_overview: Global cost overview
      - get_anomalies: Cross-tenant anomaly aggregation
      - get_tenants: Per-tenant cost drilldown
      - get_customer_drilldown: Single customer deep-dive
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.ops.L5_engines.cost_ops_engine import get_cost_ops_engine
        from app.hoc.cus.ops.L6_drivers.cost_read_driver import get_cost_read_driver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        if ctx.session is None:
            return OperationResult.fail(
                "Session required for ops cost operations", "SESSION_REQUIRED"
            )

        engine = get_cost_ops_engine()
        driver = get_cost_read_driver(ctx.session)

        if method_name == "get_overview":
            data = await engine.get_overview(driver)
            return OperationResult.ok(data)

        elif method_name == "get_anomalies":
            data = await engine.get_anomalies(
                driver,
                include_resolved=ctx.params.get("include_resolved", False),
                limit=ctx.params.get("limit", 50),
            )
            return OperationResult.ok(data)

        elif method_name == "get_tenants":
            data = await engine.get_tenants(
                driver,
                page=ctx.params.get("page", 1),
                page_size=ctx.params.get("page_size", 20),
                sort_by=ctx.params.get("sort_by", "spend_today"),
            )
            return OperationResult.ok(data)

        elif method_name == "get_customer_drilldown":
            tenant_id = ctx.params.get("tenant_id")
            if not tenant_id:
                return OperationResult.fail(
                    "Missing 'tenant_id' in params", "MISSING_TENANT_ID"
                )
            data = await engine.get_customer_drilldown(
                driver,
                tenant_id=tenant_id,
            )
            if data is None:
                return OperationResult.fail(
                    f"Tenant {tenant_id} not found or has no cost data",
                    "TENANT_NOT_FOUND",
                )
            return OperationResult.ok(data)

        return OperationResult.fail(
            f"Unknown cost ops method: {method_name}", "UNKNOWN_METHOD"
        )


def register(registry: OperationRegistry) -> None:
    """Register ops domain handlers."""
    registry.register("ops.cost", CostOpsHandler())
