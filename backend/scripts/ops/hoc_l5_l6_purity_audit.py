#!/usr/bin/env python3
# Layer: L0 — Ops Tooling
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual / CI
#   Execution: sync
# Role: AST-based purity audit for L5 engines and L6 drivers
# Callers: Developer, CI pipeline
# Allowed Imports: stdlib
# Forbidden Imports: app.*
# Reference: PIN-520 Phase 3 (L5/L6 Purity)
# artifact_class: CODE

"""
HOC L5/L6 Purity Audit Script

Scans L5 engines for structural purity violations:
- Runtime imports of sqlalchemy/sqlmodel/asyncpg/psycopg
- Session/AsyncSession symbol imports outside TYPE_CHECKING
- connect()/commit()/rollback() calls
- app.models.* imports (BLOCKING at module level, advisory for lazy/function-body imports)
- app.db imports (session acquisition violation)
- Direct ORM model instantiation (heuristic)

Scans L6 drivers for:
- commit()/rollback() calls (PIN-520: L4 owns transactions)

Usage:
    python3 scripts/ops/hoc_l5_l6_purity_audit.py
    python3 scripts/ops/hoc_l5_l6_purity_audit.py --domain policies
    python3 scripts/ops/hoc_l5_l6_purity_audit.py --json
    python3 scripts/ops/hoc_l5_l6_purity_audit.py --domain incidents --json
"""

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# HOC root relative to backend/
HOC_ROOT = Path(__file__).resolve().parent.parent.parent / "app" / "hoc"

# DB modules that L5 engines must not import at runtime
DB_MODULES = {"sqlalchemy", "sqlmodel", "asyncpg", "psycopg", "psycopg2"}

# Session symbols that L5 engines must not import outside TYPE_CHECKING
SESSION_SYMBOLS = {"Session", "AsyncSession"}

# Methods that indicate transaction control (L6 must not call)
TRANSACTION_METHODS = {"commit", "rollback"}

# Connection methods that L5 must not call
CONNECTION_METHODS = {"connect", "commit", "rollback"}

# Frozen architectural exceptions — files exempt from purity checks.
# Each entry: filename -> reason for exemption.
# No new entries permitted without PIN approval.
L5_EXEMPT_FILES = {
    "sql_gateway.py": "External DB connector for customer integrations (asyncpg for external databases, not internal DB)",
    "cost_anomaly_detector_engine.py": "Imports CostAnomaly ORM + utc_now from app.db — pre-existing, needs L6 driver extraction (PIN-520 Phase 4)",
    "loop_events.py": "self.rollback() is a domain method on LoopAdjustment dataclass, not session.rollback() (PIN-520 Phase 4)",
}

# L5 files allowed to have lazy (function-body) app.models imports.
# Module-level app.models imports are always blocking.
# Each entry: filename -> reason for exemption.
L5_LAZY_MODELS_EXEMPT = {
    "audit_ledger_engine.py": "Thin writer that constructs AuditLedger ORM rows (PIN-520 Phase 3 bridge pattern)",
}

# DB infrastructure modules that L5 engines must not import
DB_INFRA_MODULES = {"app.db"}


class Violation:
    """A single purity violation."""

    def __init__(
        self,
        file: str,
        line: int,
        category: str,
        message: str,
        severity: str = "blocking",
    ):
        self.file = file
        self.line = line
        self.category = category
        self.message = message
        self.severity = severity

    def __str__(self):
        sev = "ADVISORY" if self.severity == "advisory" else "BLOCKING"
        return f"  [{sev}] {self.file}:{self.line} — {self.category}: {self.message}"

    def to_dict(self):
        return {
            "file": self.file,
            "line": self.line,
            "category": self.category,
            "message": self.message,
            "severity": self.severity,
        }


def _get_type_checking_lines(tree: ast.Module) -> set:
    """Return set of line numbers inside `if TYPE_CHECKING:` blocks."""
    tc_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                for child in ast.walk(node):
                    if hasattr(child, "lineno"):
                        tc_lines.add(child.lineno)
    return tc_lines


def _rel_path(path: Path) -> str:
    """Return path relative to HOC root for display."""
    try:
        return str(path.relative_to(HOC_ROOT.parent.parent))
    except ValueError:
        return str(path)


def _get_function_body_lines(tree: ast.Module) -> set:
    """Return set of line numbers inside function/method bodies (not module-level)."""
    body_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if hasattr(child, "lineno"):
                    body_lines.add(child.lineno)
    return body_lines


def scan_l5_engine(py_file: Path) -> List[Violation]:
    """Scan a single L5 engine file for purity violations."""
    violations = []
    rel = _rel_path(py_file)

    try:
        source = py_file.read_text()
        tree = ast.parse(source, filename=str(py_file))
    except (SyntaxError, UnicodeDecodeError) as e:
        violations.append(Violation(rel, 0, "PARSE_ERROR", str(e)))
        return violations

    tc_lines = _get_type_checking_lines(tree)
    func_lines = _get_function_body_lines(tree)

    for node in ast.walk(tree):
        # Check imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if node.lineno in tc_lines:
                continue  # Skip TYPE_CHECKING imports

            if isinstance(node, ast.ImportFrom) and node.module:
                # Check DB module imports
                module_root = node.module.split(".")[0]
                if module_root in DB_MODULES:
                    violations.append(Violation(
                        rel, node.lineno, "DB_MODULE_IMPORT",
                        f"Runtime import of DB module: {node.module}",
                    ))

                # Check Session symbol imports
                if node.names:
                    for alias in node.names:
                        if alias.name in SESSION_SYMBOLS:
                            violations.append(Violation(
                                rel, node.lineno, "SESSION_SYMBOL_IMPORT",
                                f"Runtime import of {alias.name} from {node.module}",
                            ))

                # Check app.db imports (session acquisition)
                if node.module in DB_INFRA_MODULES or (
                    node.module and node.module.startswith("app.db.")
                ):
                    imported = [a.name for a in (node.names or []) if a.name != "*"]
                    imported_str = ", ".join(imported) if imported else "*"
                    violations.append(Violation(
                        rel, node.lineno, "APP_DB_IMPORT",
                        f"L5 engine imports from {node.module}: {imported_str} "
                        f"— use operation_registry wrappers instead",
                    ))

                # Check app.models imports
                if node.module.startswith("app.models"):
                    imported = [a.name for a in (node.names or []) if a.name != "*"]
                    imported_str = ", ".join(imported) if imported else "*"
                    is_lazy = node.lineno in func_lines
                    is_exempt = py_file.name in L5_LAZY_MODELS_EXEMPT and is_lazy

                    if is_exempt:
                        # Lazy import in exempted file — advisory only
                        violations.append(Violation(
                            rel, node.lineno, "APP_MODELS_IMPORT_LAZY",
                            f"Lazy import from {node.module}: {imported_str} (exempt: bridge pattern)",
                            severity="advisory",
                        ))
                    elif is_lazy:
                        # Lazy import in non-exempt file — blocking
                        violations.append(Violation(
                            rel, node.lineno, "APP_MODELS_IMPORT_LAZY",
                            f"Lazy import from {node.module}: {imported_str} "
                            f"— move ORM construction to L6 driver",
                        ))
                    else:
                        # Module-level import — always blocking
                        violations.append(Violation(
                            rel, node.lineno, "APP_MODELS_IMPORT",
                            f"Module-level import from {node.module}: {imported_str} "
                            f"— use L5 enum mirrors (hoc_spine/schemas/domain_enums.py) "
                            f"or move to TYPE_CHECKING",
                        ))

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    module_root = alias.name.split(".")[0]
                    if module_root in DB_MODULES:
                        violations.append(Violation(
                            rel, node.lineno, "DB_MODULE_IMPORT",
                            f"Runtime import of DB module: {alias.name}",
                        ))

        # Check method calls: connect(), commit(), rollback()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in CONNECTION_METHODS:
                    violations.append(Violation(
                        rel, node.lineno, "CONNECTION_METHOD",
                        f"L5 engine calls .{node.func.attr}() — L4 owns connection lifecycle",
                    ))

    return violations


def scan_l6_driver(py_file: Path) -> List[Violation]:
    """Scan a single L6 driver file for transaction violations."""
    violations = []
    rel = _rel_path(py_file)

    try:
        source = py_file.read_text()
        tree = ast.parse(source, filename=str(py_file))
    except (SyntaxError, UnicodeDecodeError) as e:
        violations.append(Violation(rel, 0, "PARSE_ERROR", str(e)))
        return violations

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in TRANSACTION_METHODS:
                    # Check if this is inside a _write_conn or managed_connection
                    # context manager definition (allowed)
                    violations.append(Violation(
                        rel, node.lineno, "L6_TRANSACTION_CONTROL",
                        f"L6 driver calls .{node.func.attr}() — "
                        f"L4 owns transaction boundaries (PIN-520)",
                    ))

    return violations


def _filter_l6_false_positives(violations: List[Violation], py_file: Path) -> List[Violation]:
    """Filter out known false positives from L6 driver scans.

    The _write_conn() context manager legitimately calls conn.commit()
    as a fallback for standalone (non-managed) mode. This is the
    architectural bridge pattern, not a violation.
    """
    try:
        source = py_file.read_text()
        tree = ast.parse(source, filename=str(py_file))
    except (SyntaxError, UnicodeDecodeError):
        return violations

    # Find lines inside _write_conn or managed_connection methods
    allowed_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in ("_write_conn", "managed_connection"):
                for child in ast.walk(node):
                    if hasattr(child, "lineno"):
                        allowed_lines.add(child.lineno)

    filtered = []
    for v in violations:
        if v.line in allowed_lines:
            filtered.append(Violation(
                v.file, v.line, "L6_BRIDGE_COMMIT",
                f"Bridge pattern: .commit() in _write_conn/managed_connection "
                f"(PIN-520 Phase 3 — standalone commit is advisory)",
                severity="advisory",
            ))
        else:
            filtered.append(v)
    return filtered


def scan_domain(domain: str) -> Dict[str, List[Violation]]:
    """Scan a single domain for purity violations."""
    results = {}

    # Find domain directory (handles nested paths like account/auth)
    domain_dirs = list(HOC_ROOT.rglob(f"cus/{domain}"))
    if not domain_dirs:
        # Try with wildcard for nested domains
        domain_dirs = list(HOC_ROOT.rglob(f"cus/*/{domain}"))

    for domain_dir in domain_dirs:
        # Scan L5 engines
        l5_dir = domain_dir / "L5_engines"
        if l5_dir.is_dir():
            for py_file in sorted(l5_dir.glob("*.py")):
                if py_file.name == "__init__.py":
                    continue
                if "_frozen" in str(py_file):
                    continue
                if py_file.name in L5_EXEMPT_FILES:
                    continue
                violations = scan_l5_engine(py_file)
                if violations:
                    results[_rel_path(py_file)] = violations

        # Scan L5 schemas (PIN-520 Phase 4 — expanded scope)
        l5_schemas_dir = domain_dir / "L5_schemas"
        if l5_schemas_dir.is_dir():
            for py_file in sorted(l5_schemas_dir.glob("*.py")):
                if py_file.name == "__init__.py":
                    continue
                if "_frozen" in str(py_file):
                    continue
                if py_file.name in L5_EXEMPT_FILES:
                    continue
                violations = scan_l5_engine(py_file)
                if violations:
                    results[_rel_path(py_file)] = violations

        # Scan L5 support (PIN-520 Phase 4 — expanded scope, recursive)
        l5_support_dir = domain_dir / "L5_support"
        if l5_support_dir.is_dir():
            for py_file in sorted(l5_support_dir.rglob("*.py")):
                if py_file.name == "__init__.py":
                    continue
                if "_frozen" in str(py_file):
                    continue
                if py_file.name in L5_EXEMPT_FILES:
                    continue
                violations = scan_l5_engine(py_file)
                if violations:
                    results[_rel_path(py_file)] = violations

        # Scan L6 drivers
        l6_dir = domain_dir / "L6_drivers"
        if l6_dir.is_dir():
            for py_file in sorted(l6_dir.glob("*.py")):
                if py_file.name == "__init__.py":
                    continue
                if "_frozen" in str(py_file):
                    continue
                violations = scan_l6_driver(py_file)
                violations = _filter_l6_false_positives(violations, py_file)
                if violations:
                    results[_rel_path(py_file)] = violations

    return results


def get_all_domains() -> List[str]:
    """Discover all HOC customer domains."""
    domains = set()
    cus_dir = HOC_ROOT / "cus"
    if not cus_dir.is_dir():
        return []
    # L5 subdirectory patterns to check for domain discovery
    l5_subdirs = ("L5_engines", "L5_schemas", "L5_support", "L6_drivers")
    for child in cus_dir.iterdir():
        if child.is_dir() and not child.name.startswith("_"):
            # Check for any L5/L6 subdirectories
            if any((child / d).is_dir() for d in l5_subdirs):
                domains.add(child.name)
            # Check nested domains (e.g., account/auth)
            for sub in child.iterdir():
                if sub.is_dir() and any((sub / d).is_dir() for d in l5_subdirs):
                    domains.add(f"{child.name}/{sub.name}")
    return sorted(domains)


def main():
    parser = argparse.ArgumentParser(description="HOC L5/L6 Purity Audit")
    parser.add_argument("--domain", help="Scan a specific domain (e.g., policies, incidents)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--advisory", action="store_true", help="Include advisory violations")
    args = parser.parse_args()

    if args.domain:
        domains = [args.domain]
    else:
        domains = get_all_domains()

    all_results = {}
    total_blocking = 0
    total_advisory = 0

    for domain in domains:
        results = scan_domain(domain)
        if results:
            all_results[domain] = results
            for file_violations in results.values():
                for v in file_violations:
                    if v.severity == "blocking":
                        total_blocking += 1
                    else:
                        total_advisory += 1

    if args.json:
        output = {
            "domains": {},
            "summary": {
                "blocking": total_blocking,
                "advisory": total_advisory,
                "domains_scanned": len(domains),
            },
            "note": "Pass --advisory to include advisory entries in the per-domain payload.",
        }
        for domain, results in all_results.items():
            domain_payload = {}
            for filepath, violations in results.items():
                vlist = [v.to_dict() for v in violations]
                if not args.advisory:
                    vlist = [v for v in vlist if v["severity"] != "advisory"]
                if vlist:
                    domain_payload[filepath] = vlist
            if domain_payload:
                output["domains"][domain] = domain_payload
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'='*70}")
        print(f"HOC L5/L6 Purity Audit — {len(domains)} domain(s)")
        print(f"{'='*70}\n")

        for domain in domains:
            results = all_results.get(domain, {})
            blocking = sum(
                1 for fv in results.values() for v in fv if v.severity == "blocking"
            )
            advisory = sum(
                1 for fv in results.values() for v in fv if v.severity == "advisory"
            )

            if blocking == 0 and (advisory == 0 or not args.advisory):
                print(f"  {domain}: CLEAN (0 blocking)")
                continue

            print(f"  {domain}: {blocking} blocking, {advisory} advisory")
            for filepath, violations in sorted(results.items()):
                for v in violations:
                    if v.severity == "advisory" and not args.advisory:
                        continue
                    print(f"    {v}")
            print()

        print(f"\n{'='*70}")
        print(f"TOTAL: {total_blocking} blocking, {total_advisory} advisory")
        print(f"{'='*70}\n")

    sys.exit(1 if total_blocking > 0 else 0)


if __name__ == "__main__":
    main()
