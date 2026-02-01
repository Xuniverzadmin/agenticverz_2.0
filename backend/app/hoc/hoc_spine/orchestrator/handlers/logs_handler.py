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

Routes logs domain operations to L5 engines.
Registers six operations:
  - logs.query → LogsFacade (27 async endpoints)
  - logs.evidence → EvidenceFacade (8 async endpoints)
  - logs.certificate → CertificateService (1 sync endpoint)
  - logs.replay → ReplayValidator + ReplayContextBuilder (1 sync endpoint)
  - logs.evidence_report → generate_evidence_report (1 sync function)
  - logs.pdf → PDFRenderer (3 sync endpoints, cross-domain: incidents L2 → logs L5)
"""

from app.hoc.hoc_spine.orchestrator.operation_registry import (
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

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

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

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
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

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = method(**kwargs)
        return OperationResult.ok(data)


class LogsReplayHandler:
    """
    Handler for logs.replay operations.

    Dispatches to ReplayValidator and ReplayContextBuilder.
    Sync — pure validation logic, no DB access.

    Methods:
      - build_call_record → ReplayContextBuilder.build_call_record()
      - validate_replay → ReplayValidator.validate_replay()
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.replay_determinism import (
            ReplayContextBuilder,
            ReplayValidator,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        if method_name == "build_call_record":
            builder = ReplayContextBuilder()
            data = builder.build_call_record(**kwargs)
        elif method_name == "validate_replay":
            validator = ReplayValidator()
            data = validator.validate_replay(**kwargs)
        else:
            return OperationResult.fail(
                f"Unknown replay method: {method_name}", "UNKNOWN_METHOD"
            )

        return OperationResult.ok(data)


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

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
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

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = method(**kwargs)
        return OperationResult.ok(data)


def register(registry: OperationRegistry) -> None:
    """Register logs operations with the registry."""
    registry.register("logs.query", LogsQueryHandler())
    registry.register("logs.evidence", LogsEvidenceHandler())
    registry.register("logs.certificate", LogsCertificateHandler())
    registry.register("logs.replay", LogsReplayHandler())
    registry.register("logs.evidence_report", LogsEvidenceReportHandler())
    registry.register("logs.pdf", LogsPdfHandler())
