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

Routes activity domain operations to L5 engines and hoc_spine drivers.
Registers five operations:
  - activity.query → ActivityFacade (15+ async methods)
  - activity.signal_fingerprint → signal_identity (pure computation)
  - activity.signal_feedback → SignalFeedbackService (feedback operations)
  - activity.telemetry → CusTelemetryEngine (telemetry ingestion/query)
  - activity.discovery → Discovery Ledger (emit_signal, get_signals) — PIN-520
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
            "get_dimension_breakdown": facade.get_dimension_breakdown,
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

    Wraps CusTelemetryEngine methods:
      - ingest_usage, ingest_batch, get_usage_summary,
        get_usage_history, get_daily_aggregates
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.activity.L5_engines.cus_telemetry_engine import (
            get_cus_telemetry_engine,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        service = get_cus_telemetry_engine()
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


class ActivityDiscoveryHandler:
    """
    Handler for activity.discovery operations.

    Wraps discovery ledger functions (PIN-520):
      - emit_signal → Record a discovery signal (aggregating duplicates)
      - get_signals → Query discovery signals from the ledger

    Discovery Ledger records curiosity, not decisions. Signals are
    aggregated: same (artifact, field, signal_type) updates seen_count.

    L4 handler owns transaction boundaries — creates connection, passes
    to driver, commits writes.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.db import get_engine
        from app.hoc.cus.hoc_spine.drivers import emit_signal, get_signals

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        engine = get_engine()

        if method_name == "emit_signal":
            # Required: artifact, signal_type, evidence, detected_by
            artifact = kwargs.get("artifact")
            signal_type = kwargs.get("signal_type")
            evidence = kwargs.get("evidence")
            detected_by = kwargs.get("detected_by")

            if not artifact:
                return OperationResult.fail("Missing 'artifact'", "MISSING_ARTIFACT")
            if not signal_type:
                return OperationResult.fail("Missing 'signal_type'", "MISSING_SIGNAL_TYPE")
            if not evidence:
                return OperationResult.fail("Missing 'evidence'", "MISSING_EVIDENCE")
            if not detected_by:
                return OperationResult.fail("Missing 'detected_by'", "MISSING_DETECTED_BY")

            # L4 owns connection lifecycle and commit
            with engine.connect() as conn:
                signal_id = emit_signal(
                    conn,
                    artifact=artifact,
                    signal_type=signal_type,
                    evidence=evidence,
                    detected_by=detected_by,
                    field=kwargs.get("field"),
                    confidence=kwargs.get("confidence"),
                    notes=kwargs.get("notes"),
                    phase=kwargs.get("phase"),
                    environment=kwargs.get("environment"),
                )
                conn.commit()
            return OperationResult.ok({"signal_id": str(signal_id) if signal_id else None})

        elif method_name == "get_signals":
            # Read-only — no commit needed
            with engine.connect() as conn:
                signals = get_signals(
                    conn,
                    artifact=kwargs.get("artifact"),
                    signal_type=kwargs.get("signal_type"),
                    status=kwargs.get("status"),
                    limit=kwargs.get("limit", 100),
                )
            return OperationResult.ok({"signals": signals, "count": len(signals)})

        else:
            return OperationResult.fail(
                f"Unknown discovery method: {method_name}", "UNKNOWN_METHOD"
            )


class ActivityOrphanRecoveryHandler:
    """
    Handler for activity.orphan_recovery operations.

    PIN-520 Phase 1: Routes orphan recovery through L4 registry.
    Dispatches to orphan_recovery_driver (recover_orphaned_runs).

    Methods:
      - recover: Detect and mark runs orphaned due to system crash
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.activity.L6_drivers.orphan_recovery_driver import (
            recover_orphaned_runs,
        )

        method_name = ctx.params.get("method", "recover")

        if method_name == "recover":
            try:
                result = await recover_orphaned_runs()
                return OperationResult.ok(result)
            except Exception as e:
                return OperationResult.fail(str(e), "ORPHAN_RECOVERY_ERROR")

        return OperationResult.fail(
            f"Unknown orphan recovery method: {method_name}", "UNKNOWN_METHOD"
        )


def register(registry: OperationRegistry) -> None:
    """Register activity domain handlers."""
    registry.register("activity.query", ActivityQueryHandler())
    registry.register("activity.signal_fingerprint", ActivitySignalFingerprintHandler())
    registry.register("activity.signal_feedback", ActivitySignalFeedbackHandler())
    registry.register("activity.telemetry", ActivityTelemetryHandler())
    registry.register("activity.discovery", ActivityDiscoveryHandler())  # PIN-520: Discovery ledger
    # PIN-520 Phase 1: Orphan recovery
    registry.register("activity.orphan_recovery", ActivityOrphanRecoveryHandler())
