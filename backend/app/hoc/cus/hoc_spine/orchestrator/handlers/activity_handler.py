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

import logging
import uuid

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)

logger = logging.getLogger("nova.hoc_spine.handlers.activity_handler")


def _emit_feedback_event(
    event_type: str,
    tenant_id: str,
    signal_id: str,
    actor_id: str,
    extra: dict | None = None,
) -> None:
    """Emit a validated feedback event (UC-MON activity events)."""
    try:
        from app.hoc.cus.hoc_spine.authority.event_schema_contract import (
            CURRENT_SCHEMA_VERSION,
            validate_event_payload,
        )

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "tenant_id": tenant_id,
            "project_id": "__system__",
            "actor_type": "user" if actor_id != "system" else "system",
            "actor_id": actor_id,
            "decision_owner": "activity",
            "sequence_no": 0,
            "schema_version": CURRENT_SCHEMA_VERSION,
            "signal_id": signal_id,
        }
        if extra:
            event.update(extra)
        validate_event_payload(event)
        logger.info("activity_feedback_event", extra=event)
    except Exception as e:
        logger.warning(f"Failed to emit activity feedback event: {e}")


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
        _STRIP_PARAMS = {"method", "sync_session"}

        if method_name == "get_bulk_feedback":
            signal_ids = ctx.params.get("signal_ids", [])
            result = await service.get_bulk_signal_feedback(
                ctx.session, ctx.tenant_id, signal_ids
            )
            return OperationResult.ok(result)

        if method_name == "acknowledge":
            async with ctx.session.begin():
                result = await service.acknowledge_signal(
                    ctx.session,
                    ctx.tenant_id,
                    ctx.params.get("signal_fingerprint", ""),
                    acknowledged_by=ctx.params.get("acknowledged_by"),
                    as_of=ctx.params.get("as_of"),
                )
            _emit_feedback_event(
                "activity.SignalAcknowledged",
                ctx.tenant_id,
                result.signal_id,
                ctx.params.get("acknowledged_by") or "system",
                {"feedback_state": "ACKNOWLEDGED", "as_of": ctx.params.get("as_of")},
            )
            return OperationResult.ok({
                "signal_id": result.signal_id,
                "acknowledged": result.acknowledged,
                "acknowledged_at": str(result.acknowledged_at),
                "acknowledged_by": result.acknowledged_by,
                "message": result.message,
            })

        if method_name == "suppress":
            async with ctx.session.begin():
                result = await service.suppress_signal(
                    ctx.session,
                    ctx.tenant_id,
                    ctx.params.get("signal_fingerprint", ""),
                    suppressed_by=ctx.params.get("suppressed_by"),
                    duration_minutes=ctx.params.get("duration_minutes", 1440),
                    reason=ctx.params.get("reason"),
                    as_of=ctx.params.get("as_of"),
                    bulk_action_id=ctx.params.get("bulk_action_id"),
                    target_set_hash=ctx.params.get("target_set_hash"),
                    target_count=ctx.params.get("target_count"),
                )
            event_extra = {
                "feedback_state": "SUPPRESSED",
                "as_of": ctx.params.get("as_of"),
                "ttl_seconds": ctx.params.get("duration_minutes", 1440) * 60,
                "expires_at": str(result.suppressed_until) if result.suppressed_until else None,
            }
            if ctx.params.get("bulk_action_id"):
                event_extra["bulk_action_id"] = ctx.params["bulk_action_id"]
                event_extra["target_set_hash"] = ctx.params.get("target_set_hash")
                event_extra["target_count"] = ctx.params.get("target_count")
            _emit_feedback_event(
                "activity.SignalSuppressed",
                ctx.tenant_id,
                result.signal_id,
                ctx.params.get("suppressed_by") or "system",
                event_extra,
            )
            return OperationResult.ok({
                "signal_id": result.signal_id,
                "suppressed": result.suppressed,
                "suppressed_until": str(result.suppressed_until) if result.suppressed_until else None,
                "reason": result.reason,
                "message": result.message,
            })

        if method_name == "reopen":
            signal_fp = ctx.params.get("signal_fingerprint", "")
            async with ctx.session.begin():
                result = await service.reopen_signal(
                    ctx.session,
                    ctx.tenant_id,
                    signal_fp,
                    reopened_by=ctx.params.get("reopened_by"),
                    as_of=ctx.params.get("as_of"),
                )
            _emit_feedback_event(
                "activity.SignalReopened",
                ctx.tenant_id,
                signal_fp,
                ctx.params.get("reopened_by") or "system",
                {"feedback_state": "REOPENED", "as_of": ctx.params.get("as_of")},
            )
            return OperationResult.ok(result)

        if method_name == "get_feedback_status":
            result = await service.get_signal_feedback_status(
                ctx.session,
                ctx.tenant_id,
                ctx.params.get("signal_fingerprint", ""),
            )
            return OperationResult.ok(result)

        if method_name == "evaluate_expired":
            async with ctx.session.begin():
                count = await service.evaluate_expired(
                    ctx.session,
                    as_of=ctx.params.get("as_of"),
                )
            if count > 0:
                _emit_feedback_event(
                    "activity.SignalFeedbackEvaluated",
                    ctx.tenant_id,
                    "__batch__",
                    "system",
                    {
                        "feedback_state": "EVALUATED",
                        "as_of": ctx.params.get("as_of"),
                        "evaluated_count": count,
                    },
                )
            return OperationResult.ok({"evaluated_count": count})

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
