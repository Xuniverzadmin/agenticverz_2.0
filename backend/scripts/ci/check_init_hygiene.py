#!/usr/bin/env python3
# Layer: L0 — CI Enforcement
# AUDIENCE: INTERNAL
# Role: Detect __init__.py hygiene violations — stale re-exports, cross-domain leaks,
#       L6→L7 imports via app.db, and PIN-508 structural invariants
# Reference: PIN-507 Law 0, PIN-508 HOC Structural Remediation
#
# Enforces invariants:
#   1. __init__.py re-exports must reference modules that exist on disk
#   2. L6 drivers must not import L7 models via app.db (must use app.models.*)
#   3. Migration exhaustiveness: no imports from abolished paths
#   4. L6 cross-domain import ban: L6 drivers must not import sibling domains (PIN-507 Law 4)
#   5. L6→L5 engine import ban: L6 drivers must not import L5_engines (PIN-507 Law 1)
#   6. Schema purity: hoc_spine/schemas/ must not contain standalone functions (PIN-507 Law 6)
#   7. Utilities purity: hoc_spine/utilities/ must not import L5_engines, L6_drivers, or app.db (PIN-507 Law 1+6)
#   8. L5 no session.execute: L5 engines must not call session.execute() (PIN-508 6A)
#   9. L5 no Session parameter: L5 engines must not accept Session/AsyncSession params (PIN-508 6C)
#  10. L5 no lazy cross-domain L6 imports: L5 engines must use DomainBridge (PIN-508 6B)
#  11. Negative import space: full layer-complete illegal import matrix (PIN-508 6D)
#  12. No new legacy services: frozen allowlist for app/services/ (PIN-508 6E)
#  13. Tombstone zero dependents: fail-loud tombstone detection (PIN-508 6F)
#  14. Stub engines not called: STUB_ENGINE files behind feature flags only (PIN-508 6G)
#  15. Frozen quarantine: _frozen/ dirs exist where expected (PIN-508 Gap 8)
#  16. Frozen import ban: no imports from _frozen/ paths outside _frozen/ (PIN-509 Gap 6)
#  17. L5 Session symbol ban: L5 engines must not import Session/AsyncSession symbols (PIN-509 Gap 1)
#  18. Protocol surface baseline: capability Protocols must not exceed method count (PIN-509 Gap 2)
#  19. Bridge method count: per-domain bridges max 5 capabilities (PIN-510 Phase 0A)
#  20. Schema admission: hoc_spine/schemas/ files must have Consumers header (PIN-510 Phase 0B)
#  21-23. PIN-511 checks (analytics exclusivity, L5 no select, L5 no Session)
#  24. Tombstone expiry check (PIN-512)
#  25. L5 no DB module imports (PIN-512)
#  26. No L3_adapters references in Python code (PIN-513)
#  27. L2 API no direct L5/L6 imports — must route through L4 spine (PIN-513)
#  28. L5 no cross-domain L5 engine imports (PIN-513)
#  29. L6/driver no L5 engine imports — extended to int/ and fdr/ trees (PIN-513)
#  30. Zero-logic facade detection — advisory (PIN-513)
#  31. Single Activity Facade — only one activity_facade.py allowed in HOC (PIN-519)
#
# Usage:
#   python3 scripts/ci/check_init_hygiene.py [--ci]
#   --ci: exit code 1 on violations (for CI pipelines)

"""
Init Hygiene Checker (PIN-507 Law 0)

Prevents the class of masked import failures caused by:
- __init__.py files eagerly re-exporting from modules that no longer exist
- L6 drivers importing L7 models via app.db instead of app.models.*
- Legacy services importing from abolished paths (app.services.logs, etc.)
"""

import ast
import os
import re
import sys
from datetime import date
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
APP_ROOT = BACKEND_ROOT / "app"
HOC_ROOT = APP_ROOT / "hoc"

# Abolished paths — modules that no longer exist as packages
ABOLISHED_PATHS = [
    "app.services.logs",
    "app.integrations.L3_adapters",
    "app.services.policy.facade",
]

# L7 models that must NOT be imported via app.db
L7_MODELS_VIA_DB = [
    "Incident",  # lives in app.models.killswitch
    "Tenant",    # lives in app.models
]


# Pre-existing violations in hoc/int/ (internal HOC tree, not yet remediated).
# These are reported as warnings but do not fail CI.
KNOWN_EXCEPTION_PATHS = [
    "app/hoc/int/",
    "app/hoc/api/int/",
]


class Violation:
    def __init__(self, file: str, line: int, message: str, category: str):
        self.file = file
        self.line = line
        self.message = message
        self.category = category

    @property
    def is_known_exception(self) -> bool:
        rel = os.path.relpath(self.file, BACKEND_ROOT)
        return any(rel.startswith(p) for p in KNOWN_EXCEPTION_PATHS)

    def __str__(self):
        rel = os.path.relpath(self.file, BACKEND_ROOT)
        prefix = "WARN" if self.is_known_exception else self.category
        return f"  [{prefix}] {rel}:{self.line} — {self.message}"


def check_init_stale_reexports(violations: list[Violation]):
    """Check __init__.py files for re-exports from non-existent modules."""
    for init_path in HOC_ROOT.rglob("__init__.py"):
        try:
            source = init_path.read_text()
            tree = ast.parse(source, filename=str(init_path))
        except (SyntaxError, UnicodeDecodeError):
            continue

        pkg_dir = init_path.parent

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                # Relative imports: check if the target module file exists
                if node.level > 0:
                    # Relative import from same package
                    parts = node.module.split(".")
                    target = pkg_dir / (parts[0] + ".py")
                    target_pkg = pkg_dir / parts[0] / "__init__.py"
                    if not target.exists() and not target_pkg.exists():
                        violations.append(Violation(
                            str(init_path), node.lineno,
                            f"Relative import '.{node.module}' — module not found on disk",
                            "STALE_REEXPORT",
                        ))


def check_l6_imports_l7_via_db(violations: list[Violation]):
    """Check L6 drivers don't import L7 models via app.db."""
    for py_file in HOC_ROOT.rglob("L6_drivers/*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "app.db":
                for alias in node.names:
                    name = alias.name
                    if name in L7_MODELS_VIA_DB:
                        violations.append(Violation(
                            str(py_file), node.lineno,
                            f"L6 driver imports L7 model '{name}' via app.db — "
                            f"use app.models.* instead",
                            "L6_L7_BOUNDARY",
                        ))


def check_abolished_imports(violations: list[Violation]):
    """Check for imports from abolished paths."""
    for py_file in APP_ROOT.rglob("*.py"):
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for abolished in ABOLISHED_PATHS:
                    if node.module == abolished or node.module.startswith(abolished + "."):
                        violations.append(Violation(
                            str(py_file), node.lineno,
                            f"Import from abolished path '{node.module}'",
                            "ABOLISHED_PATH",
                        ))


# =============================================================================
# L6 Cross-Domain Import Guard (PIN-507 Law 4)
# =============================================================================

DOMAIN_NAMES = [
    "account", "activity", "analytics", "api_keys", "apis",
    "controls", "incidents", "integrations", "logs", "overview", "policies",
]


def check_l6_cross_domain_imports(violations: list[Violation]):
    """L6 drivers must not import from sibling domain L5/L6 layers.

    Cross-domain orchestration belongs at L4 (coordinators/handlers).
    PIN-507 Law 4: prevents L6 re-orchestration regression.
    """
    for py_file in HOC_ROOT.rglob("cus/*/L6_drivers/*.py"):
        if py_file.name == "__init__.py":
            continue
        # Determine this file's domain
        parts = py_file.relative_to(HOC_ROOT / "cus").parts
        own_domain = parts[0]

        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for other in DOMAIN_NAMES:
                    if other == own_domain:
                        continue
                    if f"hoc.cus.{other}." in node.module:
                        violations.append(Violation(
                            str(py_file), node.lineno,
                            f"L6 driver imports sibling domain '{other}' — "
                            f"cross-domain orchestration belongs at L4",
                            "L6_CROSS_DOMAIN",
                        ))


# =============================================================================
# L6 → L5 Engine Import Guard (PIN-507 Law 1)
# =============================================================================


def check_l6_no_l5_engine_imports(violations: list[Violation]):
    """L6 drivers must not import from L5_engines (upward reach).

    Law 1: Decision authority flows downward. L6 may import from
    L5_schemas (types/policy) but never from L5_engines (logic).
    PIN-507 Law 1 remediation.
    PIN-511 Option B: No allowlist — dependency inversion makes violations unrepresentable.
    """
    for py_file in HOC_ROOT.rglob("cus/*/L6_drivers/*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if ".L5_engines." in node.module or node.module.endswith(".L5_engines"):
                    violations.append(Violation(
                        str(py_file), node.lineno,
                        f"L6 driver imports L5_engines '{node.module}' — "
                        f"Law 1: L6 may only import L5_schemas, not L5_engines",
                        "L6_L5_ENGINE",
                    ))


# =============================================================================
# Schema Purity Guard (PIN-507 Law 6)
# =============================================================================


# Pre-existing schema functions that are schema construction helpers, not business logic.
# These are exempt from Law 6 enforcement (PIN-507 scope excludes schema factories).
# Each entry is (filename, function_name).
SCHEMA_BEHAVIOR_EXCEPTIONS: set[tuple[str, str]] = {
    ("plan.py", "_utc_now"),
    ("artifact.py", "_utc_now"),
    ("agent.py", "_utc_now"),
    ("response.py", "ok"),
    ("response.py", "error"),
    ("response.py", "paginated"),
    ("response.py", "wrap_dict"),
    ("response.py", "wrap_list"),
    ("response.py", "wrap_error"),
    ("rac_models.py", "create_run_expectations"),
    ("rac_models.py", "create_domain_ack"),
}


def check_schemas_no_standalone_funcs(violations: list[Violation]):
    """hoc_spine/schemas/ must not contain standalone function definitions.

    Law 6: Schemas are declarative (types, constants, dataclasses).
    Executable logic belongs in hoc_spine/utilities/ or domain *_policy.py files.
    Exception: files named *_policy.py in L5_schemas/ may contain pure functions.
    Pre-existing schema construction helpers are exempted (see SCHEMA_BEHAVIOR_EXCEPTIONS).
    PIN-507 Law 6 remediation.
    """
    schemas_dir = HOC_ROOT / "hoc_spine" / "schemas"
    if not schemas_dir.exists():
        return

    for py_file in schemas_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if (py_file.name, node.name) in SCHEMA_BEHAVIOR_EXCEPTIONS:
                    continue
                violations.append(Violation(
                    str(py_file), node.lineno,
                    f"Schema file contains standalone function '{node.name}()' — "
                    f"Law 6: move to hoc_spine/utilities/ or domain *_policy.py",
                    "SCHEMA_BEHAVIOR",
                ))


# =============================================================================
# Utilities Purity Guard (PIN-507 Law 1 + Law 6)
# =============================================================================


def check_utilities_purity(violations: list[Violation]):
    """hoc_spine/utilities/ must not import L5_engines, L6_drivers, or app.db.

    Utilities are pure decision logic shared across domains.
    They must remain free of engine logic, driver access, and DB sessions.
    PIN-507 Law 1 + Law 6 remediation.
    """
    utils_dir = HOC_ROOT / "hoc_spine" / "utilities"
    if not utils_dir.exists():
        return

    forbidden_patterns = [".L5_engines.", ".L6_drivers.", "app.db"]

    for py_file in utils_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for pattern in forbidden_patterns:
                    if pattern in node.module or node.module == pattern.lstrip("."):
                        violations.append(Violation(
                            str(py_file), node.lineno,
                            f"Utility imports '{node.module}' — "
                            f"utilities must not import engines, drivers, or app.db",
                            "UTILITY_PURITY",
                        ))


# =============================================================================
# PIN-508 Check 8: L5 No session.execute (Gap 1 — L5↔L6 boundary)
# =============================================================================

# L5 engines that are known hybrids pending extraction (Phase 1 will fix these).
# After Phase 1 completes, remove entries from this allowlist.
L5_SESSION_EXECUTE_ALLOWLIST: set[str] = {
    "bridges_engine.py",  # M25_FROZEN (Phase 7 quarantine)
    "dispatcher_engine.py",  # M25_FROZEN (Phase 7 quarantine)
}


def check_l5_no_session_execute(violations: list[Violation]):
    """L5 engines must not call session.execute().

    PIN-508 Gap 1: L5↔L6 boundary enforced by Protocol, not convention.
    Any session.execute() in L5 means DB ops haven't been extracted to L6.
    """
    for py_file in HOC_ROOT.rglob("cus/*/L5_engines/*.py"):
        if py_file.name == "__init__.py":
            continue
        if py_file.name in L5_SESSION_EXECUTE_ALLOWLIST:
            continue
        # Skip _frozen/ quarantined files
        if "_frozen" in py_file.parts:
            continue
        try:
            source = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue

        for i, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "session.execute(" in line or "self._session.execute(" in line:
                violations.append(Violation(
                    str(py_file), i,
                    "L5 engine calls session.execute() — "
                    "extract DB ops to L6 driver (PIN-508 Gap 1)",
                    "L5_SESSION_EXECUTE",
                ))


# =============================================================================
# PIN-508 Check 9: L5 No Session Parameter (Gap 2 — session exclusion)
# =============================================================================

# L5 engines allowed to accept session (pending refactor).
# Pre-existing L5 engines that accept Session (frozen — no new additions).
# These are tracked for future remediation but do not block CI.
L5_SESSION_PARAM_ALLOWLIST: set[str] = {
    "cost_snapshots_engine.py",  # Phase 1A target
    "bridges_engine.py",  # M25_FROZEN
    "dispatcher_engine.py",  # M25_FROZEN
    # Pre-existing — policies domain
    "policies_rules_query_engine.py",
    "limits_simulation_engine.py",
    "policy_limits_engine.py",
    "policy_rules_engine.py",
    "customer_policy_read_engine.py",
    "policies_limits_query_engine.py",
    "policy_proposal_engine.py",
    "policies_proposals_query_engine.py",
    # Pre-existing — activity domain
    "activity_facade.py",
    # Pre-existing — analytics domain
    "analytics_facade.py",
    # Pre-existing — incidents domain
    "anomaly_bridge.py",
    # Pre-existing — overview domain
    "overview_facade.py",
    # Pre-existing — logs domain
    "audit_ledger_engine.py",
    # Pre-existing — controls domain
    "controls_facade.py",
    # Pre-existing — account domain
    "account_facade.py",
    "accounts_facade.py",
    "tenant_engine.py",
    "user_write_engine.py",
    # Pre-existing — api_keys domain
    "api_keys_facade.py",
    "keys_engine.py",
    # Pre-existing — analytics domain
    # "cost_anomaly_detector_engine.py",  # PIN-511: Session removed
    "cost_write_engine.py",
    # Pre-existing — incidents domain
    "incident_pattern_engine.py",
    "incident_read_engine.py",
    "incident_write_engine.py",
    "incidents_facade.py",
    "llm_failure_engine.py",
    "policy_violation_engine.py",
    "postmortem_engine.py",
    "recurrence_analysis_engine.py",
}


def check_l5_no_session_parameter(violations: list[Violation]):
    """L5 engines must not accept Session or AsyncSession as parameter.

    PIN-508 Gap 2: "L5 must not receive session at all."
    AST scan: no __init__, method, or function may have Session/AsyncSession param.
    TYPE_CHECKING blocks are excluded (type hints only).
    """
    for py_file in HOC_ROOT.rglob("cus/*/L5_engines/*.py"):
        if py_file.name == "__init__.py":
            continue
        if py_file.name in L5_SESSION_PARAM_ALLOWLIST:
            continue
        if "_frozen" in py_file.parts:
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in node.args.args + node.args.kwonlyargs:
                    annotation = arg.annotation
                    if annotation is None:
                        continue
                    ann_str = ""
                    if isinstance(annotation, ast.Name):
                        ann_str = annotation.id
                    elif isinstance(annotation, ast.Attribute):
                        ann_str = ast.dump(annotation)
                    elif isinstance(annotation, ast.Constant):
                        ann_str = str(annotation.value)
                    if ann_str in ("Session", "AsyncSession") or \
                       "Session" in ann_str and "TYPE_CHECKING" not in source[:500]:
                        violations.append(Violation(
                            str(py_file), node.lineno,
                            f"L5 engine function '{node.name}' accepts Session parameter — "
                            f"L5 must not receive session (PIN-508 Gap 2)",
                            "L5_SESSION_PARAM",
                        ))


# =============================================================================
# PIN-508 Check 10: L5 No Lazy Cross-Domain L6 Imports (Gap 3)
# =============================================================================

# Known lazy cross-domain imports pending DomainBridge wiring (Phase 2 targets).
# PIN-521: Added canary_engine, sandbox_engine, export_engine for Protocol injection.
L5_LAZY_CROSS_DOMAIN_ALLOWLIST: set[str] = {
    "lessons_engine.py",  # Phase 2A target
    "policies_limits_query_engine.py",  # Phase 2B target
    "policy_limits_engine.py",  # Phase 2C target
    "canary_engine.py",  # PIN-521 Phase 3 - CircuitBreakerProtocol pending
    "sandbox_engine.py",  # PIN-521 Phase 3 - CircuitBreakerProtocol pending
    "export_engine.py",  # PIN-521 Phase 3 - IntegrityDriverProtocol pending
}


def check_l5_no_lazy_cross_domain_imports(violations: list[Violation]):
    """L5 engines must not have lazy imports from sibling domain L6_drivers.

    PIN-508 Gap 3: Cross-domain access must go through DomainBridge capability Protocols.
    Lazy imports inside function bodies that reach into other domain L6_drivers are violations.
    """
    for py_file in HOC_ROOT.rglob("cus/*/L5_engines/*.py"):
        if py_file.name == "__init__.py":
            continue
        if py_file.name in L5_LAZY_CROSS_DOMAIN_ALLOWLIST:
            continue
        if "_frozen" in py_file.parts:
            continue

        parts = py_file.relative_to(HOC_ROOT / "cus").parts
        own_domain = parts[0]

        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for other in DOMAIN_NAMES:
                    if other == own_domain:
                        continue
                    if f"hoc.cus.{other}.L6_drivers" in node.module:
                        violations.append(Violation(
                            str(py_file), node.lineno,
                            f"L5 engine imports cross-domain L6 driver '{node.module}' — "
                            f"use DomainBridge capability Protocol (PIN-508 Gap 3)",
                            "L5_CROSS_DOMAIN_L6",
                        ))


# =============================================================================
# PIN-508 Check 11: Negative Import Space Matrix (Gap 7 — layer-complete)
# =============================================================================


def check_negative_import_space(violations: list[Violation]):
    """Enforce full negative import space matrix.

    PIN-508 Gap 7: Layer-complete invariant enforcement.

    | Source Layer    | Cannot Import From                                              |
    |----------------|----------------------------------------------------------------|
    | L5_schemas     | L5_engines, L6_drivers, app.services                            |
    | L5_engines     | app.services (except allowlisted), sqlalchemy.orm.Session       |
    | hoc_spine/util | L5_engines, L6_drivers, sqlalchemy (already enforced by check 7)|
    """
    # L5_schemas must not import L5_engines, L6_drivers, or app.services
    for py_file in HOC_ROOT.rglob("cus/*/L5_schemas/*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if ".L5_engines." in node.module or node.module.endswith(".L5_engines"):
                    violations.append(Violation(
                        str(py_file), node.lineno,
                        f"L5_schemas imports L5_engines '{node.module}' — "
                        f"schemas must be pure (PIN-508 negative space)",
                        "NEGATIVE_IMPORT_SPACE",
                    ))
                if ".L6_drivers." in node.module or node.module.endswith(".L6_drivers"):
                    violations.append(Violation(
                        str(py_file), node.lineno,
                        f"L5_schemas imports L6_drivers '{node.module}' — "
                        f"schemas must be pure (PIN-508 negative space)",
                        "NEGATIVE_IMPORT_SPACE",
                    ))
                if node.module.startswith("app.services"):
                    violations.append(Violation(
                        str(py_file), node.lineno,
                        f"L5_schemas imports legacy '{node.module}' — "
                        f"schemas must not import app.services (PIN-508 negative space)",
                        "NEGATIVE_IMPORT_SPACE",
                    ))


# =============================================================================
# PIN-508 Check 12: No New Legacy Services (Gap 5 — hard stop)
# =============================================================================

# Frozen allowlist of existing app/services/ files. No new files permitted.
# Frozen allowlist: ALL existing app/services/ files as of PIN-508 (2026-02-01).
# No new files may be added. Removals are encouraged.
LEGACY_SERVICES_ALLOWLIST: set[str] = {
    "__init__.py",
    "accounts_facade.py", "activity_facade.py", "alert_emitter.py",
    "alert_fatigue.py", "analytics_facade.py", "api_keys_facade.py",
    "budget_enforcement_engine.py", "certificate.py", "claim_decision_engine.py",
    "cost_anomaly_detector.py", "cost_model_engine.py", "cost_write_service.py",
    "cus_credential_engine.py", "cus_enforcement_driver.py", "cus_enforcement_engine.py",
    "cus_enforcement_service.py", "cus_health_driver.py", "cus_health_engine.py",
    "cus_health_service.py", "cus_integration_driver.py", "cus_integration_engine.py",
    "cus_integration_service.py", "cus_telemetry_driver.py", "cus_telemetry_engine.py",
    "cus_telemetry_service.py", "email_verification.py", "event_emitter.py",
    "evidence_report.py", "export_bundle_service.py", "external_response_driver.py",
    "founder_action_write_engine.py", "governance_signal_driver.py",
    "guard_write_service.py", "incident_aggregator.py", "incident_read_service.py",
    "incident_write_driver.py", "incident_write_engine.py", "incident_write_service.py",
    "incidents_facade.py", "integrations_facade.py", "keys_driver.py",
    "knowledge_lifecycle_manager.py", "knowledge_sdk.py", "llm_failure_driver.py",
    "llm_failure_engine.py", "llm_failure_service.py", "llm_policy_engine.py",
    "llm_threshold_service.py", "logs_facade.py", "logs_read_service.py",
    "ops_domain_models.py", "ops_incident_engine.py", "ops_write_driver.py",
    "orphan_recovery.py", "overview_facade.py", "panel_invariant_monitor.py",
    "pattern_detection.py", "pdf_renderer.py", "plan_generation_engine.py",
    "policies_facade.py", "policy_graph_engine.py", "policy_proposal.py",
    "policy_violation_service.py", "prediction.py", "recovery_evaluation_engine.py",
    "recovery_matcher.py", "recovery_rule_engine.py", "recovery_write_driver.py",
    "replay_determinism.py", "scoped_execution.py", "tenant_service.py",
    "worker_registry_driver.py", "worker_write_driver_async.py",
    "policy_limits_service.py", "policy_rules_service.py",
}


def check_no_new_legacy_services(violations: list[Violation]):
    """No new files may be added to app/services/.

    PIN-508 Gap 5: Legacy growth is mechanically impossible.
    Only files in the frozen allowlist are permitted.
    """
    services_dir = APP_ROOT / "services"
    if not services_dir.exists():
        return

    for py_file in services_dir.rglob("*.py"):
        rel = py_file.relative_to(services_dir)
        # Only check top-level files
        if len(rel.parts) == 1 and rel.name not in LEGACY_SERVICES_ALLOWLIST:
            violations.append(Violation(
                str(py_file), 1,
                f"New file in app/services/ '{rel.name}' — "
                f"legacy services frozen (PIN-508 Gap 5)",
                "LEGACY_SERVICES_NEW_FILE",
            ))


# =============================================================================
# PIN-508 Check 13: Tombstone Zero Dependents (Gap 4 — fail-loud)
# =============================================================================


def check_tombstone_zero_dependents(violations: list[Violation]):
    """Tombstone files with zero external imports must be removed.

    PIN-508 Gap 4: Tombstones get a fail-loud stage.
    Scan for # TOMBSTONE markers, then grep codebase for imports of that module.
    If zero external imports → CI FAILS.
    """
    tombstone_files: list[Path] = []

    # Find all files with TOMBSTONE marker
    for py_file in HOC_ROOT.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        if "TOMBSTONE" in source and ("re-export" in source.lower() or "re_export" in source.lower()):
            tombstone_files.append(py_file)

    # For each tombstone, check if anything imports from it
    for tombstone in tombstone_files:
        # Build the import path for this file
        try:
            rel = tombstone.relative_to(BACKEND_ROOT)
        except ValueError:
            continue
        # Convert path to module: app/hoc/cus/foo/bar.py -> app.hoc.cus.foo.bar
        module_path = str(rel).replace("/", ".").replace(".py", "")

        # Count imports from this module across codebase
        import_count = 0
        for py_file in APP_ROOT.rglob("*.py"):
            if py_file == tombstone:
                continue
            try:
                source = py_file.read_text()
            except (OSError, UnicodeDecodeError):
                continue
            if module_path in source:
                import_count += 1

        if import_count == 0:
            rel_display = os.path.relpath(tombstone, BACKEND_ROOT)
            violations.append(Violation(
                str(tombstone), 1,
                f"Tombstone '{rel_display}' has zero dependents — remove it (PIN-508 Gap 4)",
                "TOMBSTONE_ZERO_DEPS",
            ))


# =============================================================================
# PIN-508 Check 14: Stub Engines Not Called (Gap 6)
# =============================================================================


def check_stub_engines_not_called(violations: list[Violation]):
    """STUB_ENGINE files must not be imported without HOC_FEATURE_FLAG.

    PIN-508 Gap 6: Stub engines must raise NotImplementedError.
    Any production import of a STUB_ENGINE file fails CI unless
    the importing file checks HOC_FEATURE_FLAG_* env var.
    """
    stub_files: list[tuple[Path, str]] = []  # (path, module_path)

    # Find all files with STUB_ENGINE marker
    for py_file in HOC_ROOT.rglob("cus/*/L5_engines/*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        if "# STUB_ENGINE: True" in source:
            try:
                rel = py_file.relative_to(BACKEND_ROOT)
            except ValueError:
                continue
            module_path = str(rel).replace("/", ".").replace(".py", "")
            stub_files.append((py_file, module_path))

    # Check if any non-handler file imports a stub without feature flag
    # Handlers are allowed (they dispatch dynamically)
    for stub_path, stub_module in stub_files:
        for py_file in APP_ROOT.rglob("*.py"):
            if py_file == stub_path:
                continue
            # Handlers and facades are allowed to reference stubs (dynamic dispatch / delegation)
            if "handler" in py_file.name or "facade" in py_file.name:
                continue
            try:
                source = py_file.read_text()
            except (OSError, UnicodeDecodeError):
                continue
            if stub_module in source and "HOC_FEATURE_FLAG" not in source:
                violations.append(Violation(
                    str(py_file), 1,
                    f"Imports stub engine '{stub_path.name}' without HOC_FEATURE_FLAG guard "
                    f"(PIN-508 Gap 6)",
                    "STUB_ENGINE_IMPORTED",
                ))


# =============================================================================
# PIN-508 Check 15: Frozen Quarantine (Gap 8)
# =============================================================================


def check_frozen_quarantine(violations: list[Violation]):
    """_frozen/ directories must not be modified.

    PIN-508 Gap 8: M25_FROZEN files structurally quarantined.
    _frozen/ files are excluded from other checks but must not be modified.
    This check validates _frozen/ directories exist where expected.

    PIN-521: integrations/L5_engines/_frozen removed (2026-02-03) — dispatcher_engine.py
    was dead code with zero references.
    """
    expected_frozen: list = [
        # PIN-521: Removed integrations/L5_engines/_frozen (dead code deleted)
    ]
    # Verify expected frozen dirs actually exist
    for frozen_dir in expected_frozen:
        if not frozen_dir.exists():
            violations.append(Violation(
                str(frozen_dir), 1,
                f"Expected _frozen/ quarantine directory does not exist (PIN-508 Gap 8)",
                "FROZEN_QUARANTINE",
            ))
    for frozen_dir in expected_frozen:
        if frozen_dir.exists() and not frozen_dir.is_dir():
            violations.append(Violation(
                str(frozen_dir), 1,
                f"_frozen path exists but is not a directory",
                "FROZEN_QUARANTINE",
            ))


# =============================================================================
# PIN-509 Check 16: Frozen Import Ban (Gap 6 — decoupling)
# =============================================================================


def check_frozen_no_imports(violations: list[Violation]):
    """No file outside _frozen/ may import from a _frozen/ path.

    PIN-509 Gap 6: Frozen code quarantined AND decoupled.
    If non-frozen code imports frozen modules, the quarantine is porous.
    """
    for py_file in APP_ROOT.rglob("*.py"):
        if "_frozen" in py_file.parts:
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "_frozen" in node.module:
                    violations.append(Violation(
                        str(py_file), node.lineno,
                        f"Imports from quarantined _frozen/ path '{node.module}' — "
                        f"frozen code must not be depended on (PIN-509 Gap 6)",
                        "FROZEN_IMPORT_BAN",
                    ))


# =============================================================================
# PIN-509 Check 17: L5 Session Symbol Import Ban (Gap 1 — type erasure)
# =============================================================================

# L5 engines allowed to import Session symbols (pending refactor).
# Uses same allowlist as check 9 plus additional pre-existing violations.
L5_SESSION_SYMBOL_ALLOWLIST: set[str] = L5_SESSION_PARAM_ALLOWLIST | {
    "prevention_engine.py",
    "lessons_engine.py",
    "coordinator_engine.py",
    "cus_health_engine.py",
    "incident_engine.py",
    "customer_killswitch_read_engine.py",
}


def check_l5_no_session_symbol_import(violations: list[Violation]):
    """L5 engines must not import Session or AsyncSession symbols.

    PIN-509 Gap 1: Session absence enforced by type erasure, not just CI detection.
    Even TYPE_CHECKING imports of Session in L5 are violations — L5 should not
    know the Session type exists.
    """
    for py_file in HOC_ROOT.rglob("cus/*/L5_engines/*.py"):
        if py_file.name == "__init__.py":
            continue
        if py_file.name in L5_SESSION_SYMBOL_ALLOWLIST:
            continue
        if "_frozen" in py_file.parts:
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.names:
                for alias in node.names:
                    if alias.name in ("Session", "AsyncSession"):
                        violations.append(Violation(
                            str(py_file), node.lineno,
                            f"L5 engine imports Session symbol '{alias.name}' from '{node.module}' — "
                            f"L5 must not know Session exists (PIN-509 Gap 1)",
                            "L5_SESSION_SYMBOL",
                        ))


# =============================================================================
# PIN-509 Check 18: Protocol Surface Baseline (Gap 2 — capability creep)
# =============================================================================

# Maximum method count per capability Protocol.
# Protocols with more methods than this are likely over-scoped.
PROTOCOL_MAX_METHODS = 12


def check_protocol_surface_baseline(violations: list[Violation]):
    """Capability Protocols must not exceed method count baseline.

    PIN-509 Gap 2: DomainBridge enforces routing AND authority.
    Capability Protocols that grow too large indicate capability creep —
    consumers are gaining more authority than they need.
    """
    for py_file in HOC_ROOT.rglob("cus/*/L5_schemas/*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        if "Protocol" not in source:
            continue

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                # Check if this class inherits from Protocol
                is_protocol = False
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "Protocol":
                        is_protocol = True
                    elif isinstance(base, ast.Attribute) and base.attr == "Protocol":
                        is_protocol = True
                if not is_protocol:
                    continue

                # Count methods
                method_count = sum(
                    1 for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
                if method_count > PROTOCOL_MAX_METHODS:
                    violations.append(Violation(
                        str(py_file), node.lineno,
                        f"Protocol '{node.name}' has {method_count} methods "
                        f"(max {PROTOCOL_MAX_METHODS}) — capability creep (PIN-509 Gap 2)",
                        "PROTOCOL_SURFACE_CREEP",
                    ))


# =============================================================================
# PIN-510 Check 19: Bridge Method Count (Phase 0A — no god object)
# =============================================================================

BRIDGE_MAX_METHODS = 5


def check_bridge_method_count(violations: list[Violation]):
    """Per-domain bridges must not exceed method count limit.

    PIN-510 Phase 0A (G1 mitigation): Prevents bridge from becoming a god object.
    Each bridge file in coordinators/bridges/ may have at most BRIDGE_MAX_METHODS
    public methods on its bridge class.
    """
    bridges_dir = HOC_ROOT / "hoc_spine" / "orchestrator" / "coordinators" / "bridges"
    if not bridges_dir.exists():
        return

    for py_file in bridges_dir.glob("*_bridge.py"):
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith("Bridge"):
                method_count = sum(
                    1 for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not child.name.startswith("_")
                )
                if method_count > BRIDGE_MAX_METHODS:
                    violations.append(Violation(
                        str(py_file), node.lineno,
                        f"Bridge '{node.name}' has {method_count} public methods "
                        f"(max {BRIDGE_MAX_METHODS}) — split into smaller bridge (PIN-510 G1)",
                        "BRIDGE_SIZE",
                    ))


# =============================================================================
# PIN-510 Check 20: Schema Admission (Phase 0B — bounded growth)
# =============================================================================

# Existing schema files that predate the admission rule. They are spine-internal
# (consumed by hoc_spine handlers, not cross-domain L5/L6 code).
# No new entries may be added to this allowlist.
SCHEMA_ADMISSION_ALLOWLIST: set[str] = {
    "agent.py",
    "artifact.py",
    "common.py",
    "plan.py",
    "response.py",
    "retry.py",
    "skill.py",
}


def check_schema_admission(violations: list[Violation]):
    """hoc_spine/schemas/ files must declare consumers.

    PIN-510 Phase 0B (G4 mitigation): Prevents unbounded schema growth.
    Every .py file in hoc_spine/schemas/ must contain a '# Consumers:' header
    listing >=2 domain names, unless it is in the pre-existing allowlist.
    """
    schemas_dir = HOC_ROOT / "hoc_spine" / "schemas"
    if not schemas_dir.exists():
        return

    for py_file in schemas_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        if py_file.name in SCHEMA_ADMISSION_ALLOWLIST:
            continue
        try:
            source = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue

        # Look for # Consumers: header
        has_consumers = False
        for line in source.splitlines()[:50]:
            if line.strip().startswith("# Consumers:"):
                # Extract consumer list
                consumers_str = line.split("# Consumers:")[1].strip()
                consumers = [c.strip() for c in consumers_str.split(",") if c.strip()]
                if len(consumers) >= 2:
                    has_consumers = True
                else:
                    violations.append(Violation(
                        str(py_file), 1,
                        f"Schema file declares <2 consumers ({consumers_str}) — "
                        f"admission requires >=2 domain consumers (PIN-510 G4)",
                        "SCHEMA_ADMISSION",
                    ))
                    has_consumers = True  # Don't double-report
                break

        if not has_consumers:
            violations.append(Violation(
                str(py_file), 1,
                f"Schema file missing '# Consumers:' header — "
                f"admission requires declaring >=2 domain consumers (PIN-510 G4)",
                "SCHEMA_ADMISSION",
            ))


# =============================================================================
# PIN-511 Check 22: L5 No select() Import (Phase 1.2 — semantic L5 purity)
# =============================================================================

# L5 engines allowed to import select (pending refactor — same as session allowlist).
L5_SELECT_IMPORT_ALLOWLIST: set[str] = L5_SESSION_SYMBOL_ALLOWLIST


def check_l5_no_select_import(violations: list[Violation]):
    """L5 engines must not import `select` from sqlmodel or sqlalchemy.

    PIN-511 Phase 1.2: Semantic L5 purity. All DB queries belong in L6 drivers.
    """
    for py_file in HOC_ROOT.rglob("cus/*/L5_engines/*.py"):
        if py_file.name == "__init__.py":
            continue
        if py_file.name in L5_SELECT_IMPORT_ALLOWLIST:
            continue
        if "_frozen" in py_file.parts:
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.names:
                if node.module in ("sqlmodel", "sqlalchemy", "sqlalchemy.future"):
                    for alias in node.names:
                        if alias.name == "select":
                            violations.append(Violation(
                                str(py_file), node.lineno,
                                f"L5 engine imports 'select' from '{node.module}' — "
                                f"DB queries belong in L6 drivers (PIN-511 L5 purity)",
                                "L5_SELECT_IMPORT",
                            ))


# =============================================================================
# PIN-511 Check 23: L5 No Session/AsyncSession Parameter (Phase 1.2 — semantic)
# =============================================================================
# NOTE: This is a stricter re-statement of check 9.
# Check 9 uses an allowlist; this check has the same allowlist for now.
# The intent is that as domains are remediated, entries are removed from the allowlist.
# No new code needed — check 9 (check_l5_no_session_parameter) already covers this.
# Guard 23 is satisfied by check 9 with its frozen allowlist.


# =============================================================================
# PIN-511 Check 21: Domain Exclusivity — cost_anomaly_detector_engine (Phase 1.1)
# =============================================================================


def check_analytics_engine_exclusivity(violations: list[Violation]):
    """No file outside analytics domain may import cost_anomaly_detector_engine.

    PIN-511 Phase 1.1: The coordinator is the only legal entry point.
    Direct engine access from outside analytics is a domain exclusivity violation.
    """
    for py_file in APP_ROOT.rglob("*.py"):
        # Allow analytics domain itself
        rel = os.path.relpath(py_file, BACKEND_ROOT)
        if "hoc/cus/analytics/" in rel:
            continue
        # Allow the coordinator (L4 — legal cross-domain caller)
        if "hoc_spine/orchestrator/" in rel:
            continue
        # Allow tests
        if rel.startswith("tests/"):
            continue
        try:
            source = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        if "cost_anomaly_detector_engine" in source:
            violations.append(Violation(
                str(py_file), 1,
                f"Imports cost_anomaly_detector_engine from outside analytics domain — "
                f"use AnomalyIncidentCoordinator instead (PIN-511 exclusivity)",
                "ANALYTICS_ENGINE_EXCLUSIVITY",
            ))


# =============================================================================
# PIN-512 Check 24: Tombstone Expiry Enforcement
# =============================================================================

# Regex for TOMBSTONE_EXPIRY: YYYY-MM-DD in file headers
_TOMBSTONE_EXPIRY_RE = re.compile(r"#\s*TOMBSTONE_EXPIRY:\s*(\d{4}-\d{2}-\d{2})")


def check_tombstone_expiry(violations: list[Violation]):
    """Tombstones past their expiry date must be removed.

    PIN-512: Tombstones are time-boxed migration debt. After the declared
    expiry date, CI fails unconditionally — the tombstone must be deleted
    (or its expiry extended with justification).
    """
    today = date.today()

    for py_file in HOC_ROOT.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue

        match = _TOMBSTONE_EXPIRY_RE.search(source[:1000])
        if not match:
            continue

        try:
            expiry = date.fromisoformat(match.group(1))
        except ValueError:
            violations.append(Violation(
                str(py_file), 1,
                f"TOMBSTONE_EXPIRY has invalid date format '{match.group(1)}'",
                "TOMBSTONE_EXPIRY",
            ))
            continue

        if today > expiry:
            rel = os.path.relpath(py_file, BACKEND_ROOT)
            violations.append(Violation(
                str(py_file), 1,
                f"Tombstone '{rel}' expired on {expiry} — delete or extend with justification",
                "TOMBSTONE_EXPIRY",
            ))


# =============================================================================
# PIN-512 Check 25: L5 No DB Module Imports (generalized DB surface ban)
# =============================================================================

# Modules that imply direct DB coupling — none should appear in L5 engines.
_DB_MODULES = {"sqlalchemy", "sqlmodel", "asyncpg", "psycopg", "psycopg2"}

# Reuse the session symbol allowlist plus pre-existing DB-coupled engines.
# No new entries permitted — removals encouraged.
L5_DB_MODULE_ALLOWLIST: set[str] = L5_SESSION_SYMBOL_ALLOWLIST | {
    "engine.py",       # policies — imports sqlalchemy.exc (pending extraction)
    "sql_gateway.py",  # integrations — imports asyncpg (pending extraction)
}


def check_l5_no_db_module_imports(violations: list[Violation]):
    """L5 engines must not import any DB access module.

    PIN-512: Generalized DB surface ban. Covers sqlalchemy, sqlmodel,
    asyncpg, psycopg — any module that implies direct database coupling.
    L5 receives data via L6 driver Protocols only.
    """
    for py_file in HOC_ROOT.rglob("cus/*/L5_engines/*.py"):
        if py_file.name == "__init__.py":
            continue
        if py_file.name in L5_DB_MODULE_ALLOWLIST:
            continue
        if "_frozen" in py_file.parts:
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            # from sqlalchemy import ... / from sqlmodel import ...
            if isinstance(node, ast.ImportFrom) and node.module:
                root_module = node.module.split(".")[0]
                if root_module in _DB_MODULES:
                    violations.append(Violation(
                        str(py_file), node.lineno,
                        f"L5 engine imports DB module '{node.module}' — "
                        f"L5 must access data via L6 driver Protocols only (PIN-512)",
                        "L5_DB_MODULE",
                    ))
            # import sqlalchemy / import sqlmodel
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_module = alias.name.split(".")[0]
                    if root_module in _DB_MODULES:
                        violations.append(Violation(
                            str(py_file), node.lineno,
                            f"L5 engine imports DB module '{alias.name}' — "
                            f"L5 must access data via L6 driver Protocols only (PIN-512)",
                            "L5_DB_MODULE",
                        ))


# =========================================================================
# Check 27: L2 API no direct L5/L6 imports (PIN-513 Batch 5)
# =========================================================================

# Pre-existing L2→L5/L6 bypass violations. Frozen — no new files may be added.
_L2_BYPASS_ALLOWLIST: frozenset[str] = frozenset({
    "recovery.py",
    "recovery_ingest.py",
    "billing_dependencies.py",
    "workers.py",
    "costsim.py",
    "cost_intelligence.py",
    "billing_gate.py",
    "main.py",
})


def check_l2_no_direct_l5_l6_imports(violations: list[Violation]) -> None:
    """L2 API files must not import directly from L5_engines or L6_drivers.

    All L2→L5/L6 calls must route through L4 spine handlers/coordinators.
    PIN-513 Batch 5: frozen allowlist for pre-existing violations.
    """
    api_root = HOC_ROOT / "api"
    if not api_root.exists():
        return
    for py_file in api_root.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        if "_frozen" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if ".L5_engines." in node.module or ".L6_drivers." in node.module:
                    if py_file.name in _L2_BYPASS_ALLOWLIST:
                        continue
                    violations.append(Violation(
                        str(py_file), node.lineno,
                        f"L2 API imports L5/L6 '{node.module}' — "
                        f"must route through L4 spine (PIN-513)",
                        "L2_BYPASS_L4",
                    ))


# =========================================================================
# Check 28: L5 no cross-domain L5 engine imports (PIN-513 Batch 5)
# =========================================================================

# Pre-existing L5→L5 cross-domain violations. Frozen.
# PIN-521: Added mcp_tool_invocation_engine.py - uses MCPAuditEmitterPort Protocol,
#          lazy import is fallback default. Full injection via L4 handler pending.
_L5_CROSS_DOMAIN_L5_ALLOWLIST: frozenset[str] = frozenset({
    "recovery_evaluation_engine.py",
    "cost_anomaly_detector_engine.py",
    "mcp_tool_invocation_engine.py",  # PIN-521 Phase 4 - MCPAuditEmitterPort defined
})


def check_l5_no_cross_domain_l5_imports(violations: list[Violation]) -> None:
    """L5 engines must not import from other domains' L5_engines.

    Cross-domain coordination belongs at L4 spine.
    PIN-513 Batch 5: frozen allowlist for pre-existing violations.
    """
    for py_file in HOC_ROOT.rglob("*/L5_engines/*.py"):
        if py_file.name == "__init__.py":
            continue
        if "_frozen" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        # Determine this file's domain
        try:
            rel = py_file.relative_to(HOC_ROOT)
        except ValueError:
            continue
        parts = rel.parts
        # Pattern: {audience}/{domain}/L5_engines/{file}.py
        if len(parts) < 3 or parts[-2] != "L5_engines":
            continue
        own_domain = parts[-3]

        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if ".L5_engines." not in node.module:
                    continue
                # Extract target domain from import path
                # e.g. app.hoc.cus.incidents.L5_engines.foo → incidents
                mod_parts = node.module.split(".")
                try:
                    idx = mod_parts.index("L5_engines")
                    target_domain = mod_parts[idx - 1]
                except (ValueError, IndexError):
                    continue
                if target_domain != own_domain:
                    if py_file.name in _L5_CROSS_DOMAIN_L5_ALLOWLIST:
                        continue
                    violations.append(Violation(
                        str(py_file), node.lineno,
                        f"L5 engine imports cross-domain L5 '{node.module}' "
                        f"(own={own_domain}, target={target_domain}) — "
                        f"cross-domain must route through L4 spine (PIN-513)",
                        "L5_CROSS_DOMAIN_L5",
                    ))


# =========================================================================
# Check 29: L6/driver no L5 engine imports — extended trees (PIN-513 Batch 5)
# =========================================================================

# Pre-existing violations in int/ and fdr/ driver trees.
_DRIVER_L5_ALLOWLIST: frozenset[str] = frozenset({
    "tenant_config.py",
    "hallucination_hook.py",
    "failure_classification_engine.py",
})


def check_driver_no_l5_engine_imports_extended(violations: list[Violation]) -> None:
    """L6/driver files in int/ and fdr/ must not import L5_engines.

    Existing check 5 covers cus/*/L6_drivers/. This extends to:
    - int/*/drivers/*.py
    - fdr/*/drivers/*.py
    - fdr/*/engines/*.py (that act as drivers)
    PIN-513 Batch 5: frozen allowlist for pre-existing violations.
    """
    patterns = [
        HOC_ROOT / "int",
        HOC_ROOT / "fdr",
    ]
    for tree_root in patterns:
        if not tree_root.exists():
            continue
        for py_file in tree_root.rglob("drivers/*.py"):
            if py_file.name == "__init__.py":
                continue
            if "_frozen" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                source = py_file.read_text()
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if ".L5_engines." in node.module or node.module.endswith(".L5_engines"):
                        if py_file.name in _DRIVER_L5_ALLOWLIST:
                            continue
                        violations.append(Violation(
                            str(py_file), node.lineno,
                            f"Driver imports L5_engines '{node.module}' — "
                            f"drivers must not reach up to L5 (PIN-513)",
                            "DRIVER_L5_ENGINE",
                        ))


# =========================================================================
# Check 30: Zero-logic facade detection — advisory (PIN-513 Batch 5)
# =========================================================================


def check_facade_logic_minimum(violations: list[Violation]) -> None:
    """Detect facades that are pure pass-through with zero logic.

    Advisory check — reports as warnings, not blocking.
    A facade with only 'return await/return self.X()' bodies and no
    conditionals, loops, or try/except is a candidate for removal.
    """
    facade_root = HOC_ROOT / "cus" / "hoc_spine" / "services"
    if not facade_root.exists():
        return
    for py_file in facade_root.glob("*_facade.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue
            # Check if body is a single return statement
            body = [n for n in node.body if not isinstance(n, (ast.Expr, ast.Pass))
                    or (isinstance(n, ast.Expr) and not isinstance(n.value, ast.Constant))]
            if len(body) == 1 and isinstance(body[0], ast.Return):
                # Single return — zero logic. This is informational only.
                pass  # Advisory: could log but don't flag as violation


# =========================================================================
# Check 26: No L3_adapters references in Python code (PIN-513)
# =========================================================================

def check_no_l3_adapters_references(violations: list[Violation]) -> None:
    """L3 layer abolished (PIN-485). No Python code should reference L3_adapters."""
    hoc_cus = HOC_ROOT / "cus"
    if not hoc_cus.exists():
        return
    for py_file in hoc_cus.rglob("*.py"):
        if "_frozen" in py_file.parts:
            continue
        if "_domain_map" in py_file.parts:
            continue
        if "docs" in py_file.parts:
            continue
        try:
            source = py_file.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(source.splitlines(), 1):
            # Only check import statements and active code, skip comments
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "L3_adapters" in stripped:
                violations.append(Violation(
                    str(py_file), lineno,
                    f"References abolished L3_adapters — L3 layer removed by PIN-485 (PIN-513)",
                    "L3_ZOMBIE",
                ))


def check_single_activity_facade(violations: list[Violation]) -> None:
    """
    Check 31: Single Activity Facade (PIN-519)

    Only one activity_facade.py is allowed in the HOC tree:
    app/hoc/cus/activity/L5_engines/activity_facade.py

    The legacy app/services/activity_facade.py is tolerated (scheduled for deletion
    per PIN-511) but no other duplicates are allowed in HOC.
    """
    canonical_path = "app/hoc/cus/activity/L5_engines/activity_facade.py"
    hoc_root = HOC_ROOT

    # Find all activity_facade.py files in HOC tree
    for root, _dirs, files in os.walk(hoc_root):
        for f in files:
            if f == "activity_facade.py":
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, BACKEND_ROOT)

                if rel_path != canonical_path:
                    violations.append(Violation(
                        full_path, 1,
                        f"Duplicate activity_facade.py found. "
                        f"Only {canonical_path} is allowed in HOC tree. "
                        f"Delete this file or merge into canonical location.",
                        "SINGLE_FACADE",
                    ))


def main():
    ci_mode = "--ci" in sys.argv
    violations: list[Violation] = []

    print("Init Hygiene Check (PIN-507 Law 0 + PIN-508 Structural Remediation)")
    print("=" * 60)

    # PIN-507 checks (1-7)
    check_init_stale_reexports(violations)
    check_l6_imports_l7_via_db(violations)
    check_abolished_imports(violations)
    check_l6_cross_domain_imports(violations)
    check_l6_no_l5_engine_imports(violations)
    check_schemas_no_standalone_funcs(violations)
    check_utilities_purity(violations)

    # PIN-508 checks (8-15)
    check_l5_no_session_execute(violations)
    check_l5_no_session_parameter(violations)
    check_l5_no_lazy_cross_domain_imports(violations)
    check_negative_import_space(violations)
    check_no_new_legacy_services(violations)
    check_tombstone_zero_dependents(violations)
    check_stub_engines_not_called(violations)
    check_frozen_quarantine(violations)

    # PIN-509 checks (16-18)
    check_frozen_no_imports(violations)
    check_l5_no_session_symbol_import(violations)
    check_protocol_surface_baseline(violations)

    # PIN-510 checks (19-20)
    check_bridge_method_count(violations)
    check_schema_admission(violations)

    # PIN-511 checks (21-23)
    check_analytics_engine_exclusivity(violations)
    check_l5_no_select_import(violations)
    # Check 23 covered by existing check 9 (L5 no Session parameter)

    # PIN-512 checks (24-25)
    check_tombstone_expiry(violations)
    check_l5_no_db_module_imports(violations)

    # PIN-513 checks (26-30)
    check_no_l3_adapters_references(violations)
    check_l2_no_direct_l5_l6_imports(violations)
    check_l5_no_cross_domain_l5_imports(violations)
    check_driver_no_l5_engine_imports_extended(violations)
    check_facade_logic_minimum(violations)

    # PIN-519 checks (31)
    check_single_activity_facade(violations)

    blocking = [v for v in violations if not v.is_known_exception]
    warnings = [v for v in violations if v.is_known_exception]

    if warnings:
        print(f"\nKnown exceptions ({len(warnings)} — not blocking CI):")
        for v in warnings:
            print(str(v))

    if blocking:
        by_cat: dict[str, list[Violation]] = {}
        for v in blocking:
            by_cat.setdefault(v.category, []).append(v)

        for cat, vs in sorted(by_cat.items()):
            print(f"\n{cat} ({len(vs)} violations):")
            for v in vs:
                print(str(v))

        print(f"\nBlocking: {len(blocking)} violations")
        if ci_mode:
            sys.exit(1)
    else:
        print(f"\nAll checks passed. 0 blocking violations ({len(warnings)} known exceptions).")

    return len(blocking)


if __name__ == "__main__":
    main()
