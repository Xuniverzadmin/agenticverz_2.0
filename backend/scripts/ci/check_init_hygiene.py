#!/usr/bin/env python3
# Layer: L0 — CI Enforcement
# AUDIENCE: INTERNAL
# Role: Detect __init__.py hygiene violations — stale re-exports, cross-domain leaks,
#       and L6→L7 imports via app.db
# Reference: PIN-507 Law 0
#
# Enforces four invariants:
#   1. __init__.py re-exports must reference modules that exist on disk
#   2. L6 drivers must not import L7 models via app.db (must use app.models.*)
#   3. Migration exhaustiveness: no imports from abolished paths
#   4. L6 cross-domain import ban: L6 drivers must not import sibling domains (PIN-507 Law 4)
#   5. L6→L5 engine import ban: L6 drivers must not import L5_engines (PIN-507 Law 1)
#   6. Schema purity: hoc_spine/schemas/ must not contain standalone functions (PIN-507 Law 6)
#   7. Utilities purity: hoc_spine/utilities/ must not import L5_engines, L6_drivers, or app.db (PIN-507 Law 1+6)
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
import sys
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


def main():
    ci_mode = "--ci" in sys.argv
    violations: list[Violation] = []

    print("Init Hygiene Check (PIN-507 Law 0 + Law 1 + Law 4 + Law 6)")
    print("=" * 60)

    check_init_stale_reexports(violations)
    check_l6_imports_l7_via_db(violations)
    check_abolished_imports(violations)
    check_l6_cross_domain_imports(violations)
    check_l6_no_l5_engine_imports(violations)
    check_schemas_no_standalone_funcs(violations)
    check_utilities_purity(violations)

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
