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
# Reference: PIN-520 (L5/L6 Purity), No-Exemptions Remediation Plan
# artifact_class: CODE

"""
HOC L5/L6 Purity Audit Script (No-Exemptions Edition)

Scans L5 engines/schemas/support for structural purity violations:
- Runtime imports of sqlalchemy/sqlmodel/asyncpg/psycopg
- Session/AsyncSession symbol imports outside TYPE_CHECKING
- connect()/commit()/rollback() calls on DB-ish receivers
- begin()/begin_nested() calls on DB-ish receivers (implicit commit)
- app.models.* imports (BLOCKING at module level AND lazy)
- app.db imports (session acquisition violation)

Scans L6 drivers for:
- commit()/rollback() calls (PIN-520: L4 owns transactions)
- begin()/begin_nested() calls (implicit commit on context exit)

NO EXEMPTIONS. Every violation is visible until fixed in code.

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

# Transaction boundary methods — begin()/begin_nested() implicitly commit on context exit
# L6 must not call these (always); L5 must not call on DB-ish receivers
TRANSACTION_BOUNDARY_METHODS = {"begin", "begin_nested"}

# Connection methods that L5 must not call
CONNECTION_METHODS = {"connect", "commit", "rollback"}

# Receiver names that indicate a DB object (for commit/rollback false-positive filtering).
# If the receiver is NOT one of these, the call is not flagged (e.g. self.rollback() is safe).
DB_RECEIVER_NAMES = {"session", "conn", "connection", "tx", "txn", "db", "engine", "cursor"}

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


def _is_db_receiver(node: ast.Attribute) -> bool:
    """Check if the receiver of .commit()/.rollback()/.connect() looks DB-ish.

    Returns True for: session.commit(), conn.rollback(), self._conn.commit()
    Returns False for: self.rollback() (domain method on a dataclass)
    """
    value = node.value

    # Direct name: session.commit(), conn.rollback()
    if isinstance(value, ast.Name):
        return value.id.lower() in DB_RECEIVER_NAMES

    # Attribute access: self._session.commit(), self._conn.commit()
    if isinstance(value, ast.Attribute):
        attr_lower = value.attr.lower()
        # Check if the attribute name contains a DB-ish substring
        for db_name in DB_RECEIVER_NAMES:
            if db_name in attr_lower:
                return True
        return False

    # self.commit() — "self" is NOT a DB receiver
    # (catches self.rollback() domain methods)
    if isinstance(value, ast.Name) and value.id == "self":
        return False

    # Unknown receiver — flag it to be safe
    return True


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

                # Check app.models imports — ALL are blocking (no exemptions)
                if node.module.startswith("app.models"):
                    imported = [a.name for a in (node.names or []) if a.name != "*"]
                    imported_str = ", ".join(imported) if imported else "*"
                    is_lazy = node.lineno in func_lines

                    if is_lazy:
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
        # Only flag when receiver looks DB-ish (avoids false positives like self.rollback())
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in CONNECTION_METHODS:
                    if _is_db_receiver(node.func):
                        violations.append(Violation(
                            rel, node.lineno, "CONNECTION_METHOD",
                            f"L5 engine calls .{node.func.attr}() — L4 owns connection lifecycle",
                        ))

                # Check transaction boundary calls: begin(), begin_nested()
                # These implicitly commit on context exit — L5 must not own transaction boundaries
                if node.func.attr in TRANSACTION_BOUNDARY_METHODS:
                    if _is_db_receiver(node.func):
                        violations.append(Violation(
                            rel, node.lineno, "TRANSACTION_BOUNDARY",
                            f"L5 engine calls .{node.func.attr}() — "
                            f"implicit commit on context exit; L4 owns transaction boundaries",
                        ))

    return violations


def scan_l6_driver(py_file: Path) -> List[Violation]:
    """Scan a single L6 driver file for transaction violations.

    All commit()/rollback() calls in L6 are violations — no exceptions.
    """
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
                    violations.append(Violation(
                        rel, node.lineno, "L6_TRANSACTION_CONTROL",
                        f"L6 driver calls .{node.func.attr}() — "
                        f"L4 owns transaction boundaries (PIN-520)",
                    ))

                # Transaction boundary calls: begin(), begin_nested()
                # These implicitly commit on context exit — always a violation in L6
                if node.func.attr in TRANSACTION_BOUNDARY_METHODS:
                    violations.append(Violation(
                        rel, node.lineno, "L6_TRANSACTION_BOUNDARY",
                        f"L6 driver calls .{node.func.attr}() — "
                        f"implicit commit on context exit; L4 owns transaction boundaries",
                    ))

    return violations


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
                violations = scan_l5_engine(py_file)
                if violations:
                    results[_rel_path(py_file)] = violations

        # Scan L5 schemas
        l5_schemas_dir = domain_dir / "L5_schemas"
        if l5_schemas_dir.is_dir():
            for py_file in sorted(l5_schemas_dir.glob("*.py")):
                if py_file.name == "__init__.py":
                    continue
                if "_frozen" in str(py_file):
                    continue
                violations = scan_l5_engine(py_file)
                if violations:
                    results[_rel_path(py_file)] = violations

        # Scan L5 support (recursive)
        l5_support_dir = domain_dir / "L5_support"
        if l5_support_dir.is_dir():
            for py_file in sorted(l5_support_dir.rglob("*.py")):
                if py_file.name == "__init__.py":
                    continue
                if "_frozen" in str(py_file):
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
    parser.add_argument(
        "--all-domains",
        action="store_true",
        help="In JSON output, include empty per-domain entries",
    )
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
            "domains_scanned_list": domains,
            "note": "Pass --advisory to include advisory entries. Pass --all-domains to include empty domains.",
        }

        if args.all_domains:
            for domain in domains:
                output["domains"][domain] = {}

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
