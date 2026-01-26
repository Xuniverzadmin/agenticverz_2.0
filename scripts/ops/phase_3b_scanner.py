#!/usr/bin/env python3
"""
Phase 3B SQLAlchemy Extraction Scanner

Deterministic scanner for L5 sqlalchemy violations.
Scans domain by domain and reports extraction status.

Usage:
    python3 scripts/ops/phase_3b_scanner.py [--domain DOMAIN]

Reference: PIN-470, Phase-3B SQLAlchemy Extraction
"""

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Violation:
    file: str
    line: int
    import_name: str
    category: str  # BLOCKING, TYPE_CHECKING, FROZEN


@dataclass
class DomainReport:
    domain: str
    total_files: int = 0
    clean_files: int = 0
    violations: list[Violation] = field(default_factory=list)
    frozen_files: list[str] = field(default_factory=list)
    type_checking_only: list[str] = field(default_factory=list)


# SQLAlchemy imports that violate L5 layer rules
SQLALCHEMY_IMPORTS = {
    "sqlalchemy",
    "text",
    "select",
    "and_",
    "or_",
    "func",
    "create_engine",
    "Column",
    "insert",
    "update",
    "delete",
}

# Acceptable exception handling imports (Phase-2.5A pattern)
ACCEPTABLE_EXCEPTION_IMPORTS = {
    "sqlalchemy.exc.SQLAlchemyError",
    "sqlalchemy.exc.IntegrityError",
    "sqlalchemy.exc.OperationalError",
}

# Files explicitly frozen (M25_FROZEN)
FROZEN_FILES = {
    "bridges.py",
    "dispatcher.py",
    "cost_snapshots.py",
}

# P3 deferred files (design-first required)
DEFERRED_FILES: set[str] = set()
# All P3 extractions complete (2026-01-25):
# - policy_proposal.py → EXTRACTED to policy_proposal_engine.py
# - policies_facade.py → EXTRACTED to:
#     - policies_rules_query_engine.py + policy_rules_read_driver.py
#     - policies_limits_query_engine.py + limits_read_driver.py
#     - policies_proposals_query_engine.py + proposals_read_driver.py

HOC_BASE = Path("/root/agenticverz2.0/backend/app/hoc/cus")


def get_type_checking_imports(file_path: Path) -> set[str]:
    """Get all imports that are inside TYPE_CHECKING blocks."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except Exception:
        return set()

    type_checking_imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # Check if this is a TYPE_CHECKING block
            test = node.test
            is_type_checking = False

            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                is_type_checking = True
            elif isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
                is_type_checking = True

            if is_type_checking:
                # Collect all imports in this block
                for child in ast.walk(node):
                    if isinstance(child, ast.Import):
                        for alias in child.names:
                            type_checking_imports.add((child.lineno, alias.name))
                    elif isinstance(child, ast.ImportFrom):
                        if child.module:
                            for alias in child.names:
                                type_checking_imports.add((child.lineno, f"{child.module}.{alias.name}"))

    return type_checking_imports


def is_lazy_import(file_path: Path, lineno: int) -> bool:
    """Check if an import is inside a function (lazy import pattern)."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except Exception:
        return False

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check if the import line is within this function
            end_lineno = node.end_lineno or node.lineno + 100
            if node.lineno <= lineno <= end_lineno:
                return True
    return False


def scan_file(file_path: Path) -> list[Violation]:
    """Scan a single file for sqlalchemy violations."""
    violations = []
    filename = file_path.name

    # Check for frozen files
    if filename in FROZEN_FILES:
        violations.append(Violation(
            file=str(file_path),
            line=0,
            import_name="M25_FROZEN",
            category="FROZEN"
        ))
        return violations

    try:
        content = file_path.read_text()
    except Exception as e:
        print(f"  Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return violations

    # Parse AST for imports
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return violations

    # Get imports that are inside TYPE_CHECKING blocks
    type_checking_imports = get_type_checking_imports(file_path)
    type_checking_lines = {line for line, _ in type_checking_imports}

    has_runtime_sqlalchemy = False
    has_type_checking_sqlalchemy = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "sqlalchemy" or alias.name.startswith("sqlalchemy."):
                    # Check if this import is in TYPE_CHECKING or is a lazy import
                    if node.lineno in type_checking_lines:
                        has_type_checking_sqlalchemy = True
                    elif is_lazy_import(file_path, node.lineno):
                        # Lazy imports inside functions are acceptable
                        pass
                    else:
                        has_runtime_sqlalchemy = True
                        violations.append(Violation(
                            file=str(file_path),
                            line=node.lineno,
                            import_name=alias.name,
                            category="DEFERRED" if filename in DEFERRED_FILES else "BLOCKING"
                        ))
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "sqlalchemy" or node.module.startswith("sqlalchemy.")):
                for alias in node.names:
                    import_name = f"{node.module}.{alias.name}"
                    # Check if this is an acceptable exception import
                    if import_name in ACCEPTABLE_EXCEPTION_IMPORTS:
                        # Exception handling imports are acceptable (Phase-2.5A)
                        continue
                    # Check if this import is in TYPE_CHECKING or is a lazy import
                    if node.lineno in type_checking_lines:
                        has_type_checking_sqlalchemy = True
                    elif is_lazy_import(file_path, node.lineno):
                        # Lazy imports inside functions are acceptable
                        pass
                    else:
                        has_runtime_sqlalchemy = True
                        violations.append(Violation(
                            file=str(file_path),
                            line=node.lineno,
                            import_name=import_name,
                            category="DEFERRED" if filename in DEFERRED_FILES else "BLOCKING"
                        ))

    # If only TYPE_CHECKING imports (no runtime), mark as such
    if has_type_checking_sqlalchemy and not has_runtime_sqlalchemy:
        violations.append(Violation(
            file=str(file_path),
            line=0,
            import_name="TYPE_CHECKING_ONLY",
            category="TYPE_CHECKING"
        ))

    return violations


def scan_domain(domain: str) -> DomainReport:
    """Scan a single domain's L5_engines folder."""
    report = DomainReport(domain=domain)
    engines_path = HOC_BASE / domain / "L5_engines"

    if not engines_path.exists():
        return report

    for py_file in sorted(engines_path.glob("*.py")):
        if py_file.name.startswith("__"):
            continue

        report.total_files += 1
        violations = scan_file(py_file)

        if not violations:
            report.clean_files += 1
        else:
            for v in violations:
                if v.category == "FROZEN":
                    report.frozen_files.append(py_file.name)
                elif v.category == "TYPE_CHECKING":
                    report.type_checking_only.append(py_file.name)
                else:
                    report.violations.append(v)

    return report


def get_domains() -> list[str]:
    """Get list of all domains."""
    if not HOC_BASE.exists():
        print(f"Error: HOC base path not found: {HOC_BASE}", file=sys.stderr)
        sys.exit(1)

    domains = []
    for path in sorted(HOC_BASE.iterdir()):
        if path.is_dir() and not path.name.startswith("_"):
            domains.append(path.name)
    return domains


def print_report(reports: list[DomainReport]) -> int:
    """Print summary report and return exit code."""
    print("=" * 70)
    print("PHASE 3B SQLALCHEMY EXTRACTION STATUS")
    print("=" * 70)
    print()

    total_blocking = 0
    total_deferred = 0
    total_frozen = 0
    total_clean = 0

    for report in reports:
        blocking = [v for v in report.violations if v.category == "BLOCKING"]
        deferred = [v for v in report.violations if v.category == "DEFERRED"]

        status = "✅ CLEAN"
        if blocking:
            status = "❌ BLOCKING"
        elif deferred:
            status = "⏸️ DEFERRED"
        elif report.frozen_files:
            status = "⛔ FROZEN"

        print(f"Domain: {report.domain}")
        print(f"  Status: {status}")
        print(f"  Files: {report.total_files} total, {report.clean_files} clean")

        if report.type_checking_only:
            print(f"  TYPE_CHECKING only: {', '.join(report.type_checking_only)}")

        if report.frozen_files:
            print(f"  Frozen (M25): {', '.join(report.frozen_files)}")
            total_frozen += len(report.frozen_files)

        if blocking:
            print(f"  BLOCKING violations ({len(blocking)}):")
            for v in blocking:
                print(f"    - {Path(v.file).name}:{v.line} → {v.import_name}")
            total_blocking += len(blocking)

        if deferred:
            print(f"  DEFERRED (P3):")
            for v in deferred:
                print(f"    - {Path(v.file).name}:{v.line} → {v.import_name}")
            total_deferred += len(deferred)

        if not blocking and not deferred and not report.frozen_files:
            total_clean += 1

        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Domains scanned: {len(reports)}")
    print(f"  Clean domains: {total_clean}")
    print(f"  BLOCKING violations: {total_blocking}")
    print(f"  DEFERRED (P3): {total_deferred}")
    print(f"  FROZEN (M25): {total_frozen}")
    print()

    if total_blocking > 0:
        print("❌ BLOCKING gaps found - extraction required")
        return 1
    elif total_deferred > 0:
        print("⏸️ P3 files deferred - design-first required")
        return 0
    else:
        print("✅ P1-P2 extraction complete - no blocking gaps")
        return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase 3B SQLAlchemy Scanner")
    parser.add_argument("--domain", help="Scan single domain only")
    args = parser.parse_args()

    if args.domain:
        domains = [args.domain]
    else:
        domains = get_domains()

    reports = []
    for domain in domains:
        report = scan_domain(domain)
        if report.total_files > 0:
            reports.append(report)

    exit_code = print_report(reports)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
