# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Logs domain handler — routes logs operations to L5 engines via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.logs.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.2
# artifact_class: CODE

"""
Logs Handler (L4 Orchestrator)

Routes logs domain operations to L5 engines and L4 coordinators.
Registers six operations:
  - logs.query → LogsFacade (27 async endpoints)
  - logs.evidence → EvidenceFacade (8 async endpoints)
  - logs.certificate → CertificateService (4 sync endpoints)
  - logs.replay → ReplayValidator + ReplayContextBuilder (2 sync) + ReplayCoordinator (2 async, PIN-520)
  - logs.evidence_report → generate_evidence_report (1 sync function)
  - logs.pdf → PDFRenderer (3 sync endpoints, cross-domain: incidents L2 → logs L5)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class LogsQueryHandler:
    """
    Handler for logs.query operations.

    Dispatches to LogsFacade methods (list_llm_run_records, get_llm_run_envelope,
    get_llm_run_trace, get_llm_run_governance, get_llm_run_replay,
    get_llm_run_export, list_system_records, get_system_snapshot,
    get_system_telemetry, get_system_events, get_system_replay,
    get_system_audit, list_audit_entries, get_audit_entry, etc.).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.logs_facade import get_logs_facade

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_logs_facade()
        async_dispatch = {
            "list_llm_run_records": facade.list_llm_run_records,
            "get_llm_run_envelope": facade.get_llm_run_envelope,
            "get_llm_run_trace": facade.get_llm_run_trace,
            "get_llm_run_governance": facade.get_llm_run_governance,
            "get_llm_run_replay": facade.get_llm_run_replay,
            "get_llm_run_export": facade.get_llm_run_export,
            "list_system_records": facade.list_system_records,
            "get_system_snapshot": facade.get_system_snapshot,
            "get_system_events": facade.get_system_events,
            "get_system_replay": facade.get_system_replay,
            "get_system_audit": facade.get_system_audit,
            "list_audit_entries": facade.list_audit_entries,
            "get_audit_entry": facade.get_audit_entry,
            "get_audit_identity": facade.get_audit_identity,
            "get_audit_authorization": facade.get_audit_authorization,
            "get_audit_access": facade.get_audit_access,
            "get_audit_exports": facade.get_audit_exports,
        }
        sync_dispatch = {
            "get_system_telemetry": facade.get_system_telemetry,
            "get_audit_integrity": facade.get_audit_integrity,
        }

        kwargs = {
            k: v for k, v in ctx.params.items()
            if k != "method" and not k.startswith("_")
        }

        method = async_dispatch.get(method_name)
        if method:
            data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)
        elif method_name in sync_dispatch:
            data = sync_dispatch[method_name](tenant_id=ctx.tenant_id, **kwargs)
        else:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )
        return OperationResult.ok(data)


class LogsEvidenceHandler:
    """
    Handler for logs.evidence operations.

    Dispatches to EvidenceFacade methods (list_chains, get_chain,
    create_chain, add_evidence, verify_chain, create_export, etc.).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.evidence_facade import get_evidence_facade

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_evidence_facade()
        dispatch = {
            "list_chains": facade.list_chains,
            "get_chain": facade.get_chain,
            "create_chain": facade.create_chain,
            "add_evidence": facade.add_evidence,
            "verify_chain": facade.verify_chain,
            "create_export": facade.create_export,
            "get_export": facade.get_export,
            "list_exports": facade.list_exports,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = {
            k: v for k, v in ctx.params.items()
            if k != "method" and not k.startswith("_")
        }
        data = await method(tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class LogsCertificateHandler:
    """
    Handler for logs.certificate operations.

    Dispatches to CertificateService.create_replay_certificate().
    Sync — no DB access.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.certificate import CertificateService

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        service = CertificateService()
        dispatch = {
            "create_replay_certificate": service.create_replay_certificate,
            "create_policy_audit_certificate": service.create_policy_audit_certificate,
            "verify_certificate": service.verify_certificate,
            "export_certificate": service.export_certificate,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = {
            k: v for k, v in ctx.params.items()
            if k != "method" and not k.startswith("_")
        }
        data = method(**kwargs)
        return OperationResult.ok(data)


class LogsReplayHandler:
    """
    Handler for logs.replay operations.

    Dispatches to ReplayValidator, ReplayContextBuilder, and ReplayCoordinator.

    Validation methods (sync, L5):
      - build_call_record → ReplayContextBuilder.build_call_record()
      - validate_replay → ReplayValidator.validate_replay()

    Enforcement methods (async, L4 coordinator - PIN-520):
      - enforce_step → ReplayCoordinator.enforce_step()
      - enforce_trace → ReplayCoordinator.enforce_trace()
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        kwargs = {
            k: v for k, v in ctx.params.items()
            if k != "method" and not k.startswith("_")
        }

        # Validation methods (sync, L5)
        if method_name == "build_call_record":
            from app.hoc.cus.logs.L5_engines.replay_determinism import (
                ReplayContextBuilder,
            )
            builder = ReplayContextBuilder()
            data = builder.build_call_record(**kwargs)
            return OperationResult.ok(data)

        elif method_name == "validate_replay":
            from app.hoc.cus.logs.L5_engines.replay_determinism import (
                ReplayValidator,
            )
            validator = ReplayValidator()
            data = validator.validate_replay(**kwargs)
            return OperationResult.ok(data)

        # Enforcement methods (async, L4 coordinator - PIN-520)
        elif method_name == "enforce_step":
            from app.hoc.cus.hoc_spine.orchestrator.coordinators import (
                ReplayCoordinator,
            )
            coordinator = ReplayCoordinator()
            # Extract required params
            step = kwargs.get("step")
            execute_fn = kwargs.get("execute_fn")
            tenant_id = kwargs.get("tenant_id", ctx.tenant_id)
            if not step:
                return OperationResult.fail("Missing 'step' param", "MISSING_STEP")
            if not execute_fn:
                return OperationResult.fail("Missing 'execute_fn' param", "MISSING_EXECUTE_FN")
            data = await coordinator.enforce_step(
                step=step,
                execute_fn=execute_fn,
                tenant_id=tenant_id,
            )
            return OperationResult.ok(data)

        elif method_name == "enforce_trace":
            from app.hoc.cus.hoc_spine.orchestrator.coordinators import (
                ReplayCoordinator,
            )
            coordinator = ReplayCoordinator()
            # Extract required params
            trace = kwargs.get("trace")
            step_executor = kwargs.get("step_executor")
            tenant_id = kwargs.get("tenant_id", ctx.tenant_id)
            if not trace:
                return OperationResult.fail("Missing 'trace' param", "MISSING_TRACE")
            if not step_executor:
                return OperationResult.fail("Missing 'step_executor' param", "MISSING_STEP_EXECUTOR")
            data = await coordinator.enforce_trace(
                trace=trace,
                step_executor=step_executor,
                tenant_id=tenant_id,
            )
            return OperationResult.ok(data)

        else:
            return OperationResult.fail(
                f"Unknown replay method: {method_name}", "UNKNOWN_METHOD"
            )


class LogsEvidenceReportHandler:
    """
    Handler for logs.evidence_report operations.

    Dispatches to generate_evidence_report() function.
    Sync — returns PDF bytes.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.evidence_report import (
            generate_evidence_report,
        )

        kwargs = {
            k: v for k, v in ctx.params.items()
            if k != "method" and not k.startswith("_")
        }
        data = generate_evidence_report(**kwargs)
        return OperationResult.ok(data)


class LogsPdfHandler:
    """
    Handler for logs.pdf operations.

    Dispatches to PDFRenderer methods (render_evidence_pdf,
    render_soc2_pdf, render_executive_debrief_pdf).
    Sync — returns PDF bytes.

    Note: This is a cross-domain operation — incidents L2 → logs L5.
    The L4 registry is the correct mediator for cross-domain calls.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.pdf_renderer import get_pdf_renderer

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        renderer = get_pdf_renderer()
        dispatch = {
            "render_evidence_pdf": renderer.render_evidence_pdf,
            "render_soc2_pdf": renderer.render_soc2_pdf,
            "render_executive_debrief_pdf": renderer.render_executive_debrief_pdf,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown renderer method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = {
            k: v for k, v in ctx.params.items()
            if k != "method" and not k.startswith("_")
        }
        data = method(**kwargs)
        return OperationResult.ok(data)


class LogsCaptureHandler:
    """
    Handler for logs.capture operations.

    Dispatches to capture_driver for evidence capture (PIN-520 Phase 1).
    Used by workers.py for Evidence Architecture v1.0.

    Methods:
      - capture_environment: Capture environment evidence at run creation
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L6_drivers.capture_driver import (
            capture_environment_evidence,
        )
        from app.core.execution_context import ExecutionContext, EvidenceSource

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        if method_name == "capture_environment":
            # Rebuild ExecutionContext from params
            run_id = ctx.params.get("run_id")
            trace_id = ctx.params.get("trace_id")
            source = ctx.params.get("source", "SDK")
            is_synthetic = ctx.params.get("is_synthetic", False)
            synthetic_scenario_id = ctx.params.get("synthetic_scenario_id")

            if not run_id or not trace_id:
                return OperationResult.fail(
                    "Missing 'run_id' or 'trace_id'", "MISSING_CONTEXT"
                )

            # Create ExecutionContext
            evidence_source = EvidenceSource[source] if isinstance(source, str) else source
            execution_ctx = ExecutionContext.create(
                run_id=run_id,
                trace_id=trace_id,
                source=evidence_source,
                is_synthetic=is_synthetic,
                synthetic_scenario_id=synthetic_scenario_id,
            )

            # Capture environment evidence
            capture_environment_evidence(
                execution_ctx,
                sdk_mode=ctx.params.get("sdk_mode", "api"),
                execution_environment=ctx.params.get("execution_environment", "prod"),
                telemetry_delivery_status=ctx.params.get("telemetry_delivery_status", "connected"),
                capture_confidence_score=ctx.params.get("capture_confidence_score", 1.0),
            )

            return OperationResult.ok({"captured": True, "run_id": run_id})

        else:
            return OperationResult.fail(
                f"Unknown capture method: {method_name}", "UNKNOWN_METHOD"
            )


class LogsTracesApiHandler:
    """
    Handler for logs.traces_api operations.

    Dispatches to TraceApiEngine over trace store capability.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge import (
            get_logs_bridge,
        )
        from app.hoc.cus.logs.L5_engines.trace_api_engine import get_trace_api_engine

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        trace_store = get_logs_bridge().traces_store_capability()
        engine = get_trace_api_engine(trace_store)

        dispatch = {
            "list_traces": engine.list_traces,
            "store_trace": engine.store_trace,
            "get_trace": engine.get_trace,
            "get_trace_by_root_hash": engine.get_trace_by_root_hash,
            "compare_traces": engine.compare_traces,
            "delete_trace": engine.delete_trace,
            "cleanup_old_traces": engine.cleanup_old_traces,
            "check_idempotency": engine.check_idempotency,
        }

        method = dispatch.get(method_name)
        if not method:
            return OperationResult.fail(f"Unknown traces method: {method_name}", "UNKNOWN_METHOD")

        kwargs = {
            k: v for k, v in ctx.params.items()
            if k != "method" and not k.startswith("_")
        }
        data = await method(**kwargs)
        return OperationResult.ok(data)


def register(registry: OperationRegistry) -> None:
    """Register logs operations with the registry."""
    registry.register("logs.query", LogsQueryHandler())
    registry.register("logs.evidence", LogsEvidenceHandler())
    registry.register("logs.certificate", LogsCertificateHandler())
    registry.register("logs.replay", LogsReplayHandler())
    registry.register("logs.evidence_report", LogsEvidenceReportHandler())
    registry.register("logs.pdf", LogsPdfHandler())
    # PIN-520 Phase 1: Capture handler for workers.py migration
    registry.register("logs.capture", LogsCaptureHandler())
    registry.register("logs.traces_api", LogsTracesApiHandler())
