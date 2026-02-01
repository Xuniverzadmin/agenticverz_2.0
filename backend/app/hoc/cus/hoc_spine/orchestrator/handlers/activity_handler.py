# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Activity domain handler — routes activity operations to L5 engines via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.activity.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.4
# artifact_class: CODE

"""
Activity Handler (L4 Orchestrator)

Routes activity domain operations to L5 engines.
Registers four operations:
  - activity.query → ActivityFacade (15+ async methods)
  - activity.signal_fingerprint → signal_identity (pure computation)
  - activity.signal_feedback → SignalFeedbackService (feedback operations)
  - activity.telemetry → CusTelemetryService (telemetry ingestion/query)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class ActivityQueryHandler:
    """
    Handler for activity.query operations.

    Dispatches to ActivityFacade methods (get_run_detail, get_patterns,
    get_cost_analysis, get_attention_queue, acknowledge_signal,
    suppress_signal, etc.).

    Facade methods require session as first kwarg.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.activity.L5_engines.activity_facade import get_activity_facade

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_activity_facade()
        dispatch = {
            "get_runs": facade.get_runs,
            "get_run_detail": facade.get_run_detail,
            "get_run_evidence": facade.get_run_evidence,
            "get_run_proof": facade.get_run_proof,
            "get_status_summary": facade.get_status_summary,
            "get_live_runs": facade.get_live_runs,
            "get_completed_runs": facade.get_completed_runs,
            "get_signals": facade.get_signals,
            "get_metrics": facade.get_metrics,
            "get_threshold_signals": facade.get_threshold_signals,
            "get_risk_signals": facade.get_risk_signals,
            "get_patterns": facade.get_patterns,
            "get_cost_analysis": facade.get_cost_analysis,
            "get_attention_queue": facade.get_attention_queue,
            "acknowledge_signal": facade.acknowledge_signal,
            "suppress_signal": facade.suppress_signal,
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


class ActivitySignalFingerprintHandler:
    """
    Handler for activity.signal_fingerprint operations.

    Wraps pure computation from signal_identity module.
    Methods:
      - compute_from_row → compute_signal_fingerprint_from_row(row)
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.activity.L5_engines.signal_identity import (
            compute_signal_fingerprint_from_row,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        if method_name == "compute_from_row":
            row = ctx.params.get("row")
            if row is None:
                return OperationResult.fail(
                    "Missing 'row' in params", "MISSING_ROW"
                )
            fingerprint = compute_signal_fingerprint_from_row(row)
            return OperationResult.ok(fingerprint)

        if method_name == "compute_batch":
            rows = ctx.params.get("rows")
            if rows is None:
                return OperationResult.fail(
                    "Missing 'rows' in params", "MISSING_ROWS"
                )
            fingerprints = [compute_signal_fingerprint_from_row(r) for r in rows]
            return OperationResult.ok(fingerprints)

        return OperationResult.fail(
            f"Unknown method: {method_name}", "UNKNOWN_METHOD"
        )


class ActivitySignalFeedbackHandler:
    """
    Handler for activity.signal_feedback operations.

    Wraps SignalFeedbackService methods:
      - get_bulk_feedback → get_bulk_signal_feedback(tenant_id, signal_ids)
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.activity.L5_engines.signal_feedback_engine import (
            SignalFeedbackService,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        service = SignalFeedbackService()

        if method_name == "get_bulk_feedback":
            signal_ids = ctx.params.get("signal_ids", [])
            result = await service.get_bulk_signal_feedback(
                ctx.tenant_id, signal_ids
            )
            return OperationResult.ok(result)

        return OperationResult.fail(
            f"Unknown method: {method_name}", "UNKNOWN_METHOD"
        )


class ActivityTelemetryHandler:
    """
    Handler for activity.telemetry operations.

    Wraps CusTelemetryService methods:
      - ingest_usage, ingest_batch, get_usage_summary,
        get_usage_history, get_daily_aggregates
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.activity.L5_engines.cus_telemetry_engine import (
            get_cus_telemetry_service,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        service = get_cus_telemetry_service()
        dispatch = {
            "ingest_usage": service.ingest_usage,
            "ingest_batch": service.ingest_batch,
            "get_usage": service.get_usage,
            "get_usage_summary": service.get_usage_summary,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown telemetry method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        # Telemetry methods use tenant_id as explicit kwarg
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id
        data = await method(**kwargs)
        return OperationResult.ok(data)


def register(registry: OperationRegistry) -> None:
    """Register activity domain handlers."""
    registry.register("activity.query", ActivityQueryHandler())
    registry.register("activity.signal_fingerprint", ActivitySignalFingerprintHandler())
    registry.register("activity.signal_feedback", ActivitySignalFeedbackHandler())
    registry.register("activity.telemetry", ActivityTelemetryHandler())
