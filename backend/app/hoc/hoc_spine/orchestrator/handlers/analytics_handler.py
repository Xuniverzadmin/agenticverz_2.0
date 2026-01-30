# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Analytics domain handler — routes analytics operations to L5 facades via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.analytics.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.1
# artifact_class: CODE

"""
Analytics Handler (L4 Orchestrator)

Routes analytics domain operations to L5 facades.
Registers two operations:
  - analytics.query → AnalyticsFacade
  - analytics.detection → DetectionFacade
"""

from app.hoc.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class AnalyticsQueryHandler:
    """
    Handler for analytics.query operations.

    Dispatches to AnalyticsFacade methods (get_usage_statistics,
    get_cost_statistics, get_status).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L5_engines.analytics_facade import (
            get_analytics_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_analytics_facade()
        method = getattr(facade, method_name, None)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class AnalyticsDetectionHandler:
    """
    Handler for analytics.detection operations.

    Dispatches to DetectionFacade methods (run_detection, list_anomalies,
    get_anomaly, resolve_anomaly, acknowledge_anomaly, get_detection_status).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L5_engines.detection_facade import (
            get_detection_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_detection_facade()
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
    """Register analytics operations with the registry."""
    registry.register("analytics.query", AnalyticsQueryHandler())
    registry.register("analytics.detection", AnalyticsDetectionHandler())
