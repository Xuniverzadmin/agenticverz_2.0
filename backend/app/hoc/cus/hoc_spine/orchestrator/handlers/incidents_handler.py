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

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


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
            "list_active_incidents": facade.list_active_incidents,
            "list_resolved_incidents": facade.list_resolved_incidents,
            "list_historical_incidents": facade.list_historical_incidents,
            "get_incident_detail": facade.get_incident_detail,
            "get_incidents_for_run": facade.get_incidents_for_run,
            "get_metrics": facade.get_metrics,
            "analyze_cost_impact": facade.analyze_cost_impact,
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
        from app.hoc.cus.logs.L5_engines.audit_ledger_service import (
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
        data = method(**kwargs)
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


def register(registry: OperationRegistry) -> None:
    """Register incidents operations with the registry."""
    registry.register("incidents.query", IncidentsQueryHandler())
    registry.register("incidents.export", IncidentsExportHandler())
    registry.register("incidents.write", IncidentsWriteHandler())
    # PIN-520 Phase 1: Recovery rule engine
    registry.register("incidents.recovery_rules", IncidentsRecoveryRuleHandler())
