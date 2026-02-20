# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Role: Domain operation handlers — one module per domain, registered at import time
# Reference: PIN-491 (L2-L4-L5 Construction Plan)
# artifact_class: CODE

"""
Operation Handlers Package

Each module in this package implements OperationHandler for a specific domain.
Handlers are registered with the OperationRegistry at import time.

Structure:
    handlers/
    ├── __init__.py          # This file — imports all domain handlers
    ├── overview_handler.py  # Phase A.1
    ├── account_handler.py   # Phase A.1
    ├── ...                  # One per domain
    └── policies_handler.py  # Phase A.5

Registration happens via register_all_handlers() called from app startup.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import OperationRegistry


def register_all_handlers(registry: "OperationRegistry") -> None:
    """
    Register all domain operation handlers.

    Called once at application startup. Each domain handler module
    provides a register() function that registers its operations.

    Import is lazy (inside this function) so handler modules are only
    loaded when explicitly wired.
    """
    # Phase A.1 — Facade-pattern domains (10 operations)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import overview_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import account_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import analytics_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import api_keys_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import incidents_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import integrations_handler

    overview_handler.register(registry)      # overview.query
    account_handler.register(registry)       # account.query, account.notifications
    analytics_handler.register(registry)     # analytics.query, analytics.detection, analytics.canary_reports, analytics.canary
    api_keys_handler.register(registry)      # api_keys.query
    incidents_handler.register(registry)     # incidents.query
    integrations_handler.register(registry)  # integrations.query, .connectors, .datasources

    # Phase A.2 — Compound facade domains (6 operations: logs)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import logs_handler

    logs_handler.register(registry)  # logs.query, .evidence, .certificate, .replay, .evidence_report, .pdf

    # Phase A.3 — Controls domain (2 operations: controls)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import controls_handler

    controls_handler.register(registry)  # controls.query, .thresholds

    # Phase A.4 — Activity domain (4 operations: activity)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import activity_handler

    activity_handler.register(registry)  # activity.query, .signal_fingerprint, .signal_feedback, .telemetry, .discovery

    # Phase A.5 — Policies domain (9 operations: policies)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import policies_handler

    policies_handler.register(registry)  # policies.query, .enforcement, .governance, .lessons, .policy_facade, .limits, .rules, .rate_limits, .simulate

    # GAP-174 — Policies sandbox execution (1 operation: policies.sandbox_execute)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import policies_sandbox_handler

    policies_sandbox_handler.register(registry)  # policies.sandbox_execute

    # Part-2 CRM — Governance audit execution (1 operation: governance.audit_job)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import governance_audit_handler

    governance_audit_handler.register(registry)  # governance.audit_job

    # PIN-516 Phase 3 — MCP Servers (1 operation: integrations.mcp_servers)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import mcp_handler

    mcp_handler.register(registry)  # integrations.mcp_servers

    # Phase A.6 — Analytics scheduled operations (PIN-520 Wiring Audit)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import analytics_prediction_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import analytics_snapshot_handler

    analytics_prediction_handler.register(registry)  # analytics.prediction
    analytics_snapshot_handler.register(registry)    # analytics.snapshot

    # Phase B4 — Ops domain (1 operation: ops.cost)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import ops_handler

    ops_handler.register(registry)  # ops.cost

    # Agent domain — Platform health, discovery stats, routing, and strategy
    from app.hoc.cus.hoc_spine.orchestrator.handlers import agent_handler

    agent_handler.register(registry)  # agent.discovery_stats, agent.routing, agent.strategy

    # M25 Integration domain — L2 first-principles purity extraction
    from app.hoc.cus.hoc_spine.orchestrator.handlers import m25_integration_handler

    m25_integration_handler.register(registry)  # m25.read_*, m25.write_*, m25.update_*

    # Proxy domain — L2→L6 elimination (v1_proxy.py)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import proxy_handler

    proxy_handler.register(registry)  # proxy.ops

    # Platform domain — L2→L6 elimination (platform.py)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import platform_handler

    platform_handler.register(registry)  # platform.health

    # Killswitch domain — L2→L6 elimination (v1_killswitch.py)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import killswitch_handler

    killswitch_handler.register(registry)  # killswitch.read, killswitch.write

    # System runtime — health + diagnostics (no L2 ownership beyond translation)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import system_handler

    system_handler.register(registry)  # system.health

    # Tenant lifecycle — DB-backed lifecycle state (Phase A: Tenant Lifecycle SSOT)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import lifecycle_handler

    lifecycle_handler.register(registry)  # account.lifecycle.query, account.lifecycle.transition

    # Onboarding SSOT — DB-backed onboarding state (Phase A2: Onboarding SSOT)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import onboarding_handler

    onboarding_handler.register(registry)  # account.onboarding.query, account.onboarding.advance

    # Knowledge planes — persisted SSOT + evidence query (Phase 3)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import knowledge_planes_handler

    knowledge_planes_handler.register(registry)  # knowledge.planes.*, knowledge.evidence.*


def bootstrap_hoc_spine() -> None:
    """
    Bootstrap the HOC Spine runtime system (ITER3.3).

    This function:
    1. Validates all hoc_spine modules import successfully (fail-fast on NameError/ModuleNotFoundError)
    2. Registers all operation handlers with the OperationRegistry
    3. Freezes the registry to prevent runtime registration

    Must be called at application startup before serving requests.

    Raises:
        RuntimeError: If any hoc_spine module fails to import
    """
    import logging
    import importlib
    import pkgutil

    logger = logging.getLogger("nova.hoc_spine.bootstrap")

    # Step 1: Validate all hoc_spine modules import successfully
    logger.info("hoc_spine.bootstrap: validating module imports...")

    package_path = "app/hoc/cus/hoc_spine"
    package_name = "app.hoc.cus.hoc_spine"
    import_failures = []

    for importer, modname, ispkg in pkgutil.walk_packages(
        path=[package_path], prefix=package_name + "."
    ):
        if "__pycache__" in modname or modname.endswith("_test"):
            continue
        try:
            importlib.import_module(modname)
        except Exception as e:
            import_failures.append((modname, type(e).__name__, str(e)[:200]))

    if import_failures:
        failure_details = "\n".join(
            f"  - {mod}: {etype}: {emsg}" for mod, etype, emsg in import_failures
        )
        raise RuntimeError(
            f"HOC Spine bootstrap failed: {len(import_failures)} module(s) failed to import:\n{failure_details}"
        )

    logger.info("hoc_spine.bootstrap: all modules import successfully")

    # Step 2: Register all operation handlers
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_operation_registry

    registry = get_operation_registry()
    register_all_handlers(registry)

    logger.info(
        "hoc_spine.bootstrap: handlers registered",
        extra={"operation_count": len(registry._handlers)},
    )

    # Step 3: Wire RunGovernanceFacade with real L5 engines (G1 gap closure)
    from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import wire_run_governance_facade

    wire_run_governance_facade()
    logger.info("hoc_spine.bootstrap: RunGovernanceFacade wired")

    # Step 4: Wire consequence pipeline with adapters (G4 consequences expansion)
    from app.hoc.cus.hoc_spine.consequences.pipeline import get_consequence_pipeline
    from app.hoc.cus.hoc_spine.consequences.adapters.dispatch_metrics_adapter import (
        get_dispatch_metrics_adapter,
    )

    pipeline = get_consequence_pipeline()
    pipeline.register(get_dispatch_metrics_adapter())
    pipeline.freeze()
    logger.info(
        "hoc_spine.bootstrap: consequence pipeline wired",
        extra={"adapter_count": pipeline.adapter_count},
    )

    # Step 5: Freeze the registry to prevent runtime registration
    registry.freeze()

    logger.info("hoc_spine.bootstrap: registry frozen — HOC Spine runtime ready")
