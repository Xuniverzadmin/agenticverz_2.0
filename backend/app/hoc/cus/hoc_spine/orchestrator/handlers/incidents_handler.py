# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Incidents domain handler — routes incidents operations to L5 facade via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.incidents.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.1
# artifact_class: CODE

"""
Incidents Handler (L4 Orchestrator)

Routes incidents domain operations to the L5 IncidentsFacade.
Registered as "incidents.query" in the OperationRegistry.
"""

import logging
import uuid as _uuid

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)

logger = logging.getLogger(__name__)


def _emit_incident_event(
    event_type: str,
    tenant_id: str,
    incident_id: str,
    actor_id: str,
    extra: dict | None = None,
) -> None:
    """Emit a validated incident domain event."""
    from app.hoc.cus.hoc_spine.authority.event_schema_contract import (
        CURRENT_SCHEMA_VERSION,
        validate_event_payload,
    )

    event = {
        "event_id": str(_uuid.uuid4()),
        "event_type": event_type,
        "tenant_id": tenant_id,
        "project_id": "__system__",
        "actor_type": "user" if actor_id != "system" else "system",
        "actor_id": actor_id,
        "decision_owner": "incidents",
        "sequence_no": 0,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "incident_id": incident_id,
    }
    if extra:
        event.update(extra)
    validate_event_payload(event)
    logger.info("incident_lifecycle_event", extra=event)


class IncidentsQueryHandler:
    """
    Handler for incidents.query operations.

    Dispatches to IncidentsFacade methods (list_active_incidents,
    list_resolved_incidents, list_historical_incidents, detect_patterns,
    analyze_recurrence, get_incident_learnings, etc.).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.incidents.L5_engines.incidents_facade import (
            get_incidents_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_incidents_facade()
        dispatch = {
            "list_incidents": facade.list_incidents,
            "list_active_incidents": facade.list_active_incidents,
            "list_resolved_incidents": facade.list_resolved_incidents,
            "list_historical_incidents": facade.list_historical_incidents,
            "get_incident_detail": facade.get_incident_detail,
            "get_incidents_for_run": facade.get_incidents_for_run,
            "get_metrics": facade.get_metrics,
            "analyze_cost_impact": facade.analyze_cost_impact,
            "get_historical_trend": facade.get_historical_trend,
            "get_historical_distribution": facade.get_historical_distribution,
            "get_historical_cost_trend": facade.get_historical_cost_trend,
            "detect_patterns": facade.detect_patterns,
            "analyze_recurrence": facade.analyze_recurrence,
            "get_incident_learnings": facade.get_incident_learnings,
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


class IncidentsExportHandler:
    """
    Handler for incidents.export operations.

    Dispatches to ExportBundleDriver methods (PIN-504: L2 must not import L6 directly).
    Routes export_evidence, export_soc2, export_executive_debrief through L4.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.incidents.L6_drivers.export_bundle_driver import (
            get_export_bundle_driver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        driver = get_export_bundle_driver()
        dispatch = {
            "create_evidence_bundle": driver.create_evidence_bundle,
            "create_soc2_bundle": driver.create_soc2_bundle,
            "create_executive_debrief": driver.create_executive_debrief,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown export method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        try:
            data = await method(**kwargs)
            return OperationResult.ok(data)
        except ValueError as e:
            return OperationResult.fail(str(e), "NOT_FOUND")
        except Exception as e:
            return OperationResult.fail(str(e), "EXPORT_ERROR")


class IncidentsWriteHandler:
    """
    Handler for incidents.write operations.

    Dispatches to IncidentWriteService with audit service injection (PIN-504).
    The L4 handler creates the audit service via lazy import (legal: L4→L5/L6)
    and injects it into the L5 engine, avoiding cross-domain L5→L5 imports.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.incidents.L5_engines.incident_write_engine import (
            get_incident_write_service,
        )
        from app.hoc.cus.logs.L5_engines.audit_ledger_engine import (
            AuditLedgerService,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        # L4 creates audit service and injects into L5 engine (PIN-504)
        audit = AuditLedgerService(ctx.session)
        service = get_incident_write_service(ctx.session, audit=audit)

        dispatch = {
            "acknowledge_incident": service.acknowledge_incident,
            "resolve_incident": service.resolve_incident,
            "manual_close_incident": service.manual_close_incident,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown write method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        # L4 owns transaction boundary (PIN-520)
        with ctx.session.begin():
            data = method(**kwargs)

        # Emit incident lifecycle events (UC-MON-05)
        incident_id = str(kwargs.get("incident", {}).id) if hasattr(kwargs.get("incident"), "id") else kwargs.get("incident_id", "unknown")
        actor_id = kwargs.get("acknowledged_by") or kwargs.get("resolved_by") or kwargs.get("closed_by", "system")
        if method_name == "acknowledge_incident":
            _emit_incident_event(
                "incidents.IncidentAcknowledged",
                ctx.tenant_id,
                incident_id,
                actor_id,
                extra={"incident_state": "ACKNOWLEDGED"},
            )
        elif method_name == "resolve_incident":
            _emit_incident_event(
                "incidents.IncidentResolved",
                ctx.tenant_id,
                incident_id,
                actor_id,
                extra={
                    "incident_state": "RESOLVED",
                    "resolution_type": kwargs.get("resolution_type"),
                },
            )
        elif method_name == "manual_close_incident":
            _emit_incident_event(
                "incidents.IncidentManuallyClosed",
                ctx.tenant_id,
                incident_id,
                actor_id,
                extra={"incident_state": "RESOLVED", "resolution_method": "manual_closure"},
            )

        return OperationResult.ok(data)


class IncidentsRecoveryRuleHandler:
    """
    Handler for incidents.recovery_rules operations.

    PIN-520 Phase 1: Routes recovery rule engine through L4 registry.
    Dispatches to RecoveryRuleEngine methods.

    Methods:
      - evaluate: Evaluate recovery rules for a failure
      - get_rules: List available recovery rules
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.incidents.L5_engines.recovery_rule_engine import (
            RecoveryRuleEngine,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        engine = RecoveryRuleEngine()

        if method_name == "evaluate":
            failure_payload = ctx.params.get("failure_payload")
            context = ctx.params.get("context", {})
            if not failure_payload:
                return OperationResult.fail(
                    "Missing 'failure_payload'", "MISSING_PAYLOAD"
                )
            result = engine.evaluate(failure_payload, context)
            return OperationResult.ok(result)

        elif method_name == "get_rules":
            rules = engine.get_rules()
            return OperationResult.ok({"rules": rules})

        return OperationResult.fail(
            f"Unknown recovery rule method: {method_name}", "UNKNOWN_METHOD"
        )


class CostGuardQueryHandler:
    """
    Handler for incidents.cost_guard operations.

    Dispatches to CostGuardDriver methods for cost visibility queries.
    Extracted from cost_guard.py L2 to comply with L2 no-execute rule.

    Methods:
      - get_spend_totals: Get spend today/mtd/week
      - get_budget: Get budget limits
      - get_baseline: Get baseline for trend
      - get_last_snapshot: Get last snapshot time
      - get_total_spend: Get total spend for period
      - get_baselines: Get all baselines
      - get_spend_by_feature: Breakdown by feature
      - get_spend_by_model: Breakdown by model
      - get_spend_by_user: Breakdown by user
      - get_cost_anomalies: Get cost anomalies
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.incidents.L6_drivers.cost_guard_driver import (
            get_cost_guard_driver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        driver = get_cost_guard_driver(ctx.session)

        try:
            if method_name == "get_spend_totals":
                result = driver.get_spend_totals(
                    tenant_id=ctx.tenant_id,
                    today_start=ctx.params["today_start"],
                    month_start=ctx.params["month_start"],
                    week_ago=ctx.params["week_ago"],
                )
                return OperationResult.ok({
                    "today": result.today,
                    "mtd": result.mtd,
                    "week": result.week,
                })

            elif method_name == "get_budget":
                result = driver.get_budget(tenant_id=ctx.tenant_id)
                return OperationResult.ok({
                    "daily_limit_cents": result.daily_limit_cents,
                    "monthly_limit_cents": result.monthly_limit_cents,
                })

            elif method_name == "get_baseline":
                result = driver.get_baseline(tenant_id=ctx.tenant_id)
                return OperationResult.ok({"baseline": result})

            elif method_name == "get_last_snapshot":
                result = driver.get_last_snapshot(tenant_id=ctx.tenant_id)
                return OperationResult.ok({"completed_at": result})

            elif method_name == "get_total_spend":
                result = driver.get_total_spend(
                    tenant_id=ctx.tenant_id,
                    period_start=ctx.params["period_start"],
                )
                return OperationResult.ok({"total": result})

            elif method_name == "get_baselines":
                result = driver.get_baselines(tenant_id=ctx.tenant_id)
                return OperationResult.ok({"baselines": result})

            elif method_name == "get_spend_by_feature":
                result = driver.get_spend_by_feature(
                    tenant_id=ctx.tenant_id,
                    period_start=ctx.params["period_start"],
                    limit=ctx.params.get("limit", 10),
                )
                return OperationResult.ok({
                    "rows": [
                        {
                            "name": r.name,
                            "display_name": r.display_name,
                            "spend_cents": r.spend_cents,
                            "request_count": r.request_count,
                        }
                        for r in result
                    ]
                })

            elif method_name == "get_spend_by_model":
                result = driver.get_spend_by_model(
                    tenant_id=ctx.tenant_id,
                    period_start=ctx.params["period_start"],
                    limit=ctx.params.get("limit", 10),
                )
                return OperationResult.ok({
                    "rows": [
                        {
                            "name": r.name,
                            "display_name": r.display_name,
                            "spend_cents": r.spend_cents,
                            "request_count": r.request_count,
                        }
                        for r in result
                    ]
                })

            elif method_name == "get_spend_by_user":
                result = driver.get_spend_by_user(
                    tenant_id=ctx.tenant_id,
                    period_start=ctx.params["period_start"],
                    limit=ctx.params.get("limit", 10),
                )
                return OperationResult.ok({
                    "rows": [
                        {
                            "name": r.name,
                            "display_name": r.display_name,
                            "spend_cents": r.spend_cents,
                            "request_count": r.request_count,
                        }
                        for r in result
                    ]
                })

            elif method_name == "get_cost_anomalies":
                anomalies, has_more = driver.get_cost_anomalies(
                    tenant_id=ctx.tenant_id,
                    cutoff=ctx.params["cutoff"],
                    include_resolved=ctx.params.get("include_resolved", False),
                    limit=ctx.params.get("limit", 20),
                )
                return OperationResult.ok({
                    "anomalies": [
                        {
                            "id": a.id,
                            "anomaly_type": a.anomaly_type,
                            "severity": a.severity,
                            "current_value_cents": a.current_value_cents,
                            "expected_value_cents": a.expected_value_cents,
                            "threshold_pct": a.threshold_pct,
                            "message": a.message,
                            "incident_id": a.incident_id,
                            "action_taken": a.action_taken,
                            "resolved": a.resolved,
                            "detected_at": a.detected_at,
                            "resolved_at": a.resolved_at,
                        }
                        for a in anomalies
                    ],
                    "has_more": has_more,
                })

            return OperationResult.fail(
                f"Unknown cost_guard method: {method_name}", "UNKNOWN_METHOD"
            )

        except KeyError as e:
            return OperationResult.fail(
                f"Missing required parameter: {e}", "MISSING_PARAM"
            )
        except Exception as e:
            return OperationResult.fail(str(e), "QUERY_ERROR")


class IncidentsRecurrenceHandler:
    """
    Handler for incidents.recurrence operations (UC-MON-05).

    Dispatches recurrence group queries to IncidentWriteDriver (L6).
    Supports deterministic recurrence linking via versioned signatures.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.incidents.L6_drivers.incident_write_driver import (
            get_incident_write_driver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        if method_name == "get_recurrence_group":
            recurrence_signature = ctx.params.get("recurrence_signature")
            if not recurrence_signature:
                return OperationResult.fail(
                    "Missing 'recurrence_signature'", "MISSING_SIGNATURE"
                )
            driver = get_incident_write_driver(ctx.session)
            data = driver.fetch_recurrence_group(
                tenant_id=ctx.tenant_id,
                recurrence_signature=recurrence_signature,
                limit=ctx.params.get("limit", 50),
            )
            return OperationResult.ok({"incidents": data, "count": len(data)})

        elif method_name == "create_postmortem_stub":
            incident_id = ctx.params.get("incident_id")
            if not incident_id:
                return OperationResult.fail(
                    "Missing 'incident_id'", "MISSING_INCIDENT_ID"
                )
            from datetime import datetime, timezone
            driver = get_incident_write_driver(ctx.session)
            with ctx.session.begin():
                artifact_id = driver.create_postmortem_stub(
                    incident_id=incident_id,
                    tenant_id=ctx.tenant_id,
                    now=datetime.now(timezone.utc),
                )
            _emit_incident_event(
                "incidents.PostmortemCreated",
                ctx.tenant_id,
                incident_id,
                "system",
                extra={"postmortem_artifact_id": artifact_id},
            )
            return OperationResult.ok({"postmortem_artifact_id": artifact_id})

        return OperationResult.fail(
            f"Unknown recurrence method: {method_name}", "UNKNOWN_METHOD"
        )


def register(registry: OperationRegistry) -> None:
    """Register incidents operations with the registry."""
    registry.register("incidents.query", IncidentsQueryHandler())
    registry.register("incidents.export", IncidentsExportHandler())
    registry.register("incidents.write", IncidentsWriteHandler())
    # PIN-520 Phase 1: Recovery rule engine
    registry.register("incidents.recovery_rules", IncidentsRecoveryRuleHandler())
    # Cost guard queries (extracted from L2 cost_guard.py)
    registry.register("incidents.cost_guard", CostGuardQueryHandler())
    # UC-MON-05: Recurrence grouping + postmortem stubs
    registry.register("incidents.recurrence", IncidentsRecurrenceHandler())
