#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: CI guard for L2→L3→L4 import chain compliance (GATE-7)
# Callers: GitHub Actions workflow
# Allowed Imports: L8 (stdlib only)
# Forbidden Imports: L1-L7 (must be self-contained)
# Reference: PIN-280 (L2 Promotion Governance), PIN-281 (L3 Adapter Closure)
#
# GOVERNANCE NOTE:
# This script enforces GATE-7 from CAPABILITY_LIFECYCLE.yaml.
# It validates that customer-facing L2 endpoints follow the
# L2→L3→L4 import chain without bypassing layers.

"""
L2→L3→L4 Layer Guard (GATE-7)

This CI guard validates that customer-facing L2 endpoints:
1. Import exactly one L3 adapter (no L4/L6 bypasses)
2. L3 adapters import only L4 services (no L6 direct access)

Exit codes:
  0 - All checks pass
  1 - Violations found
  2 - Script error

Usage:
  python scripts/ci/l2_l3_l4_guard.py           # Check all customer L2s
  python scripts/ci/l2_l3_l4_guard.py --verbose # Show detailed analysis
  python scripts/ci/l2_l3_l4_guard.py --fix     # Suggest fixes (no auto-apply)
"""

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

# DB-AUTH-001: Declare local-only authority
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from scripts._db_guard import assert_db_authority  # noqa: E402
assert_db_authority("local")

# =============================================================================
# CONFIGURATION - Customer-Facing L2→L3 Mappings
# =============================================================================

# L2 files that serve customer-facing capabilities
# NOTE: guard.py has mixed responsibilities (customer + internal operations).
#       The guard validates that L3 adapters are imported for customer ops,
#       not that ALL imports are via L3 (which would break internal ops).
CUSTOMER_L2_FILES = {
    # guard.py has mixed responsibilities - some endpoints are internal/admin
    # We verify L3 adapters are imported, not that ALL imports are via L3
    "backend/app/api/guard.py": {
        "expected_l3": [
            "customer_keys_adapter",
            "customer_incidents_adapter",
            "customer_killswitch_adapter",
        ],
        "capabilities": [
            "KEYS_LIST",
            "KEYS_DETAIL",
            "KEYS_FREEZE",
            "KEYS_UNFREEZE",
            "INCIDENTS_LIST",
            "INCIDENTS_DETAIL",
            "INCIDENT_ACK",
            "INCIDENT_RESOLVE",
            "KILLSWITCH_ACTIVATE",
            "KILLSWITCH_DEACTIVATE",
        ],
        "allow_mixed_imports": True,
    },
    "backend/app/api/guard_logs.py": {
        "expected_l3": ["customer_logs_adapter"],
        "capabilities": ["LOGS_LIST", "LOGS_DETAIL", "LOGS_EXPORT"],
        "allow_mixed_imports": False,  # Pure customer file
    },
    # ACTIVITY Domain Qualification (PIN-281)
    "backend/app/api/customer_activity.py": {
        "expected_l3": ["customer_activity_adapter"],
        "capabilities": ["ACTIVITY_LIST", "ACTIVITY_DETAIL"],
        "allow_mixed_imports": False,  # Pure customer file
    },
    # POLICY Domain Qualification (PIN-281)
    "backend/app/api/guard_policies.py": {
        "expected_l3": ["customer_policies_adapter"],
        "capabilities": ["POLICY_LIST", "POLICY_DETAIL"],
        "allow_mixed_imports": False,  # Pure customer file
    },
}

# L3 adapters and their expected L4 imports
# Only adapters that have been fully refactored to L4 pattern are included here.
CUSTOMER_L3_ADAPTERS = {
    "backend/app/adapters/customer_keys_adapter.py": {
        "expected_l4": ["keys_service"],
        "forbidden_imports": [
            "app.db",
            "sqlalchemy",
        ],  # app.models OK for type hints only
    },
    "backend/app/adapters/customer_incidents_adapter.py": {
        "expected_l4": ["incident_read_service", "incident_write_service"],
        "forbidden_imports": ["app.db", "sqlalchemy"],
    },
    "backend/app/adapters/customer_logs_adapter.py": {
        "expected_l4": ["logs_read_service"],
        "forbidden_imports": ["app.db", "sqlalchemy"],
    },
    # ACTIVITY Domain Qualification (PIN-281)
    "backend/app/adapters/customer_activity_adapter.py": {
        "expected_l4": ["customer_activity_read_service"],
        "forbidden_imports": ["app.db", "sqlalchemy"],
    },
    # POLICY Domain Qualification (PIN-281)
    "backend/app/adapters/customer_policies_adapter.py": {
        "expected_l4": ["customer_policy_read_service"],
        "forbidden_imports": ["app.db", "sqlalchemy"],
    },
    # KILLSWITCH Domain Qualification (PIN-281)
    "backend/app/adapters/customer_killswitch_adapter.py": {
        "expected_l4": ["customer_killswitch_read_service", "guard_write_service"],
        "forbidden_imports": ["app.db", "sqlalchemy"],
    },
}

# Forbidden import patterns at L2 (bypassing L3) - only for pure customer files
L2_FORBIDDEN_PATTERNS = [
    r"from app\.models\.",  # Direct L6 model access
    r"from app\.db import",  # Direct database access
    r"from sqlmodel import",  # Direct ORM access
    r"from sqlalchemy import",  # Direct ORM access
]

# Forbidden import patterns at L3 (bypassing L4)
L3_FORBIDDEN_PATTERNS = [
    r"from app\.db import",  # Direct database access
    r"from sqlalchemy import",  # Direct ORM access (Session OK via SQLModel)
]


# =============================================================================
# VIOLATION TYPES
# =============================================================================


@dataclass
class Violation:
    """Represents a layer violation."""

    file: str
    line: int
    violation_type: str
    message: str
    severity: str  # BLOCKING, WARNING

    def __str__(self) -> str:
        return f"{self.file}:{self.line} [{self.severity}] {self.violation_type}: {self.message}"


# =============================================================================
# AST ANALYSIS
# =============================================================================


def extract_imports(file_path: Path) -> List[Tuple[int, str, str]]:
    """Extract all imports from a Python file.

    Returns list of (line_number, module, full_import_statement).
    """
    imports = []
    try:
        content = file_path.read_text()
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((node.lineno, alias.name, f"import {alias.name}"))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_import = f"from {module} import {alias.name}"
                    imports.append((node.lineno, module, full_import))
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

    return imports


def check_l2_imports(
    file_path: Path, config: dict, verbose: bool = False
) -> List[Violation]:
    """Check L2 file imports for layer violations."""
    violations = []
    imports = extract_imports(file_path)

    expected_l3 = set(config.get("expected_l3", []))
    allow_mixed = config.get("allow_mixed_imports", False)
    found_l3 = set()

    for line_no, module, full_import in imports:
        # Check for forbidden direct imports (only for pure customer files)
        if not allow_mixed:
            for pattern in L2_FORBIDDEN_PATTERNS:
                if re.search(pattern, full_import):
                    violations.append(
                        Violation(
                            file=str(file_path),
                            line=line_no,
                            violation_type="L2_BYPASSES_L3",
                            message=f"L2 directly imports L6: {full_import}",
                            severity="BLOCKING",
                        )
                    )

        # Track L3 adapter imports
        for l3_name in expected_l3:
            if l3_name in module or l3_name in full_import:
                found_l3.add(l3_name)

    # Check for missing L3 imports - BLOCKING for customer capabilities
    missing_l3 = expected_l3 - found_l3
    if missing_l3:
        for l3 in missing_l3:
            violations.append(
                Violation(
                    file=str(file_path),
                    line=0,
                    violation_type="L2_MISSING_L3",
                    message=f"L2 does not import expected L3 adapter: {l3}",
                    severity="BLOCKING",  # Changed from WARNING - missing L3 is blocking
                )
            )

    # For mixed files with L3 adapters imported, clear violations and report success
    if allow_mixed and not missing_l3 and found_l3:
        if verbose:
            print(
                f"  ✓ {file_path}: L3 adapters imported ({', '.join(found_l3)}) [mixed file]"
            )
        return []  # Clear violations for mixed files that have proper L3 imports

    if verbose and not violations:
        print(f"  ✓ {file_path}: L2 imports L3 correctly ({', '.join(found_l3)})")

    return violations


def check_l3_imports(
    file_path: Path, config: dict, verbose: bool = False
) -> List[Violation]:
    """Check L3 adapter imports for layer violations."""
    violations = []
    imports = extract_imports(file_path)

    expected_l4 = set(config.get("expected_l4", []))
    forbidden = config.get("forbidden_imports", [])
    found_l4 = set()

    for line_no, module, full_import in imports:
        # Check for forbidden direct imports (L6 bypass)
        for pattern in L3_FORBIDDEN_PATTERNS:
            if re.search(pattern, full_import):
                violations.append(
                    Violation(
                        file=str(file_path),
                        line=line_no,
                        violation_type="L3_BYPASSES_L4",
                        message=f"L3 directly imports L6: {full_import}",
                        severity="BLOCKING",
                    )
                )

        # Check for other forbidden imports
        for forbidden_module in forbidden:
            if forbidden_module in full_import:
                violations.append(
                    Violation(
                        file=str(file_path),
                        line=line_no,
                        violation_type="L3_FORBIDDEN_IMPORT",
                        message=f"L3 imports forbidden module: {full_import}",
                        severity="BLOCKING",
                    )
                )

        # Track L4 service imports
        for l4_name in expected_l4:
            if l4_name in module or l4_name in full_import:
                found_l4.add(l4_name)

    # Check for missing L4 imports
    missing_l4 = expected_l4 - found_l4
    if missing_l4:
        for l4 in missing_l4:
            violations.append(
                Violation(
                    file=str(file_path),
                    line=0,
                    violation_type="L3_MISSING_L4",
                    message=f"L3 does not import expected L4 service: {l4}",
                    severity="WARNING",
                )
            )

    if verbose and not violations:
        print(f"  ✓ {file_path}: L3 imports L4 correctly ({', '.join(found_l4)})")

    return violations


# =============================================================================
# MAIN GUARD
# =============================================================================


def run_guard(verbose: bool = False, fix: bool = False) -> Tuple[int, List[Violation]]:
    """Run the L2→L3→L4 guard and return (exit_code, violations)."""
    all_violations: List[Violation] = []
    repo_root = Path(__file__).parent.parent.parent

    print("=" * 70)
    print("L2→L3→L4 LAYER GUARD (GATE-7)")
    print("=" * 70)
    print()

    # Check L2 files
    print("Checking L2 (Customer APIs)...")
    for l2_path, config in CUSTOMER_L2_FILES.items():
        file_path = repo_root / l2_path
        if file_path.exists():
            violations = check_l2_imports(file_path, config, verbose)
            all_violations.extend(violations)
        else:
            if verbose:
                print(f"  ⚠ {l2_path}: File not found (may not be wired yet)")

    print()

    # Check L3 files
    print("Checking L3 (Boundary Adapters)...")
    for l3_path, config in CUSTOMER_L3_ADAPTERS.items():
        file_path = repo_root / l3_path
        if file_path.exists():
            violations = check_l3_imports(file_path, config, verbose)
            all_violations.extend(violations)
        else:
            all_violations.append(
                Violation(
                    file=l3_path,
                    line=0,
                    violation_type="L3_MISSING",
                    message=f"Expected L3 adapter not found: {l3_path}",
                    severity="BLOCKING",
                )
            )

    print()

    # Report results
    blocking = [v for v in all_violations if v.severity == "BLOCKING"]
    warnings = [v for v in all_violations if v.severity == "WARNING"]

    if blocking:
        print("=" * 70)
        print(f"BLOCKING VIOLATIONS ({len(blocking)}):")
        print("=" * 70)
        for v in blocking:
            print(f"  ✗ {v}")
        print()

    if warnings:
        print("-" * 70)
        print(f"WARNINGS ({len(warnings)}):")
        print("-" * 70)
        for v in warnings:
            print(f"  ⚠ {v}")
        print()

    # Summary
    print("=" * 70)
    if blocking:
        print(f"GATE-7: FAIL ({len(blocking)} blocking, {len(warnings)} warnings)")
        print()
        print("Layer compliance check FAILED.")
        print("Fix all BLOCKING violations before merge.")
        return 1, all_violations
    elif warnings:
        print(f"GATE-7: PASS with warnings ({len(warnings)} warnings)")
        print()
        print("Layer compliance check PASSED (warnings are advisory).")
        return 0, all_violations
    else:
        print("GATE-7: PASS")
        print()
        print("Layer compliance check PASSED. All L2→L3→L4 chains are valid.")
        return 0, all_violations


def main():
    parser = argparse.ArgumentParser(
        description="L2→L3→L4 Layer Guard (GATE-7) - CI enforcement for layer compliance"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed analysis"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Suggest fixes (no auto-apply)"
    )
    args = parser.parse_args()

    exit_code, _ = run_guard(verbose=args.verbose, fix=args.fix)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
