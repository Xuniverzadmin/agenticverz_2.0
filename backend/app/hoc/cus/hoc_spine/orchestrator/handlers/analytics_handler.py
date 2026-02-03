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

Routes analytics domain operations to L5 facades and coordinators.
Registers four operations:
  - analytics.query → AnalyticsFacade
  - analytics.detection → DetectionFacade
  - analytics.canary_reports → CanaryReportDriver (L6 queries)
  - analytics.canary → CanaryCoordinator (scheduled validation runs)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
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
        dispatch = {
            "get_usage_statistics": facade.get_usage_statistics,
            "get_cost_statistics": facade.get_cost_statistics,
            "get_status": facade.get_status,
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
        dispatch = {
            "run_detection": facade.run_detection,
            "list_anomalies": facade.list_anomalies,
            "get_anomaly": facade.get_anomaly,
            "resolve_anomaly": facade.resolve_anomaly,
            "acknowledge_anomaly": facade.acknowledge_anomaly,
            "get_detection_status": facade.get_detection_status,
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


class CanaryReportHandler:
    """
    Handler for analytics.canary_reports operations.

    Routes canary report queries through L4 to L6.
    Ensures policy/audit hooks can be added later.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L6_drivers.canary_report_driver import (
            query_canary_reports,
            get_canary_report_by_run_id,
        )

        method_name = ctx.params.get("method", "list")

        if method_name == "list":
            reports = await query_canary_reports(
                status=ctx.params.get("status"),
                passed=ctx.params.get("passed"),
                limit=ctx.params.get("limit", 10),
                offset=ctx.params.get("offset", 0),
            )
            return OperationResult.ok({
                "reports": reports,
                "total": len(reports),
            })

        elif method_name == "get":
            run_id = ctx.params.get("run_id")
            if not run_id:
                return OperationResult.fail("Missing 'run_id'", "MISSING_RUN_ID")
            report = await get_canary_report_by_run_id(run_id)
            if report is None:
                return OperationResult.fail(
                    f"Canary report not found: {run_id}", "NOT_FOUND"
                )
            return OperationResult.ok(report)

        else:
            return OperationResult.fail(
                f"Unknown canary method: {method_name}", "UNKNOWN_METHOD"
            )


class CanaryRunHandler:
    """
    Handler for analytics.canary operations.

    Dispatches to CanaryCoordinator for scheduled canary validation runs.
    This is the L4 entry point for scheduler/cron invocations.

    Methods:
      - run: Execute canary validation (sample_count, drift_threshold)

    Reference: PIN-520 Wiring Audit
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.hoc_spine.orchestrator.coordinators import CanaryCoordinator

        method_name = ctx.params.get("method", "run")

        if method_name == "run":
            coordinator = CanaryCoordinator()
            result = await coordinator.run(
                sample_count=ctx.params.get("sample_count", 100),
                drift_threshold=ctx.params.get("drift_threshold", 0.2),
            )
            return OperationResult.ok(result)

        else:
            return OperationResult.fail(
                f"Unknown canary method: {method_name}", "UNKNOWN_METHOD"
            )


def register(registry: OperationRegistry) -> None:
    """Register analytics operations with the registry."""
    registry.register("analytics.query", AnalyticsQueryHandler())
    registry.register("analytics.detection", AnalyticsDetectionHandler())
    registry.register("analytics.canary_reports", CanaryReportHandler())
    registry.register("analytics.canary", CanaryRunHandler())  # PIN-520: Scheduler integration
