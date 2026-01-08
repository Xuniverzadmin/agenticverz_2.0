#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: CI guard to prevent new M7 (rbac_engine) imports
# Reference: docs/invariants/AUTHZ_AUTHORITY.md

"""
M7 Import Guard

=============================================================================
INVARIANT: NO NEW M7 DEPENDENCIES (I-AUTH-003)
=============================================================================

This CI guard checks that no new files import from M7 (rbac_engine.py).
Only files in the ALLOWED_M7_IMPORTERS list may import from M7.

Usage:
    python scripts/ci/m7_import_guard.py [--fix]

Returns:
    0 if no violations
    1 if violations found
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

# Files that are ALLOWED to import from M7 (legacy, scheduled for removal)
ALLOWED_M7_IMPORTERS: Set[str] = {
    # M7 implementation itself (will be deleted in T8)
    "backend/app/auth/rbac_engine.py",
    # Integration/translation layers
    "backend/app/auth/rbac_integration.py",
    "backend/app/auth/rbac_middleware.py",
    "backend/app/main.py",  # Startup initialization
    # API endpoints (scheduled for migration)
    "backend/app/api/rbac_api.py",
    # Auth providers (role translation)
    "backend/app/auth/oidc_provider.py",
    "backend/app/auth/clerk_provider.py",
    # RBAC module exports
    "backend/app/auth/rbac.py",
    "backend/app/auth/__init__.py",
    # Approval flows
    "backend/app/api/policy.py",
    # Tests (allowed for now)
    "backend/tests/auth/test_rbac_engine.py",
    "backend/tests/auth/test_rbac_middleware.py",
    "backend/tests/auth/test_rbac_integration.py",
    "backend/tests/auth/test_rbac_path_mapping.py",
}

# M7 import patterns to detect
M7_IMPORT_PATTERNS = [
    r"from\s+app\.auth\.rbac_engine\s+import",
    r"from\s+app\.auth\s+import.*\bRBACEngine\b",
    r"from\s+app\.auth\s+import.*\bget_rbac_engine\b",
    r"from\s+app\.auth\s+import.*\binit_rbac_engine\b",
    r"from\s+app\.auth\s+import.*\bcheck_permission\b",
    r"from\s+app\.auth\s+import.*\bPolicyObject\b",
    r"import\s+app\.auth\.rbac_engine",
    # Direct usage patterns
    r"RBACEngine\(\)",
    r"get_rbac_engine\(\)",
]


def find_python_files(root: Path) -> List[Path]:
    """Find all Python files in the backend directory."""
    backend_dir = root / "backend"
    if not backend_dir.exists():
        print(f"Error: {backend_dir} does not exist")
        sys.exit(1)
    return list(backend_dir.rglob("*.py"))


def check_file_for_m7_imports(file_path: Path, root: Path) -> List[Tuple[int, str]]:
    """Check a file for M7 imports. Returns list of (line_number, line_content)."""
    violations = []
    relative_path = str(file_path.relative_to(root))

    # Skip allowed files
    if relative_path in ALLOWED_M7_IMPORTERS:
        return []

    # Skip __pycache__ and other generated files
    if "__pycache__" in str(file_path) or ".pyc" in str(file_path):
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return []

    for line_num, line in enumerate(content.splitlines(), 1):
        for pattern in M7_IMPORT_PATTERNS:
            if re.search(pattern, line):
                violations.append((line_num, line.strip()))
                break  # One violation per line is enough

    return violations


def main():
    parser = argparse.ArgumentParser(description="Check for unauthorized M7 imports")
    parser.add_argument("--fix", action="store_true", help="Show fix suggestions")
    parser.add_argument("--root", default="/root/agenticverz2.0", help="Project root")
    args = parser.parse_args()

    root = Path(args.root)
    python_files = find_python_files(root)

    total_violations = 0
    violation_files = []

    print("=" * 70)
    print("M7 Import Guard - Checking for unauthorized M7 (rbac_engine) imports")
    print("=" * 70)
    print("Reference: docs/invariants/AUTHZ_AUTHORITY.md (I-AUTH-003)")
    print(f"Checking {len(python_files)} Python files...")
    print()

    for file_path in sorted(python_files):
        violations = check_file_for_m7_imports(file_path, root)
        if violations:
            relative_path = str(file_path.relative_to(root))
            violation_files.append(relative_path)
            print(f"VIOLATION: {relative_path}")
            for line_num, line in violations:
                print(f"  Line {line_num}: {line}")
                total_violations += 1
            print()

    print("=" * 70)
    if total_violations == 0:
        print("PASS: No unauthorized M7 imports found")
        print("=" * 70)
        return 0
    else:
        print(
            f"FAIL: Found {total_violations} violation(s) in {len(violation_files)} file(s)"
        )
        print()
        print("Allowed M7 importers (legacy, scheduled for removal):")
        for allowed in sorted(ALLOWED_M7_IMPORTERS):
            print(f"  - {allowed}")
        print()
        if args.fix:
            print("FIX SUGGESTIONS:")
            print(
                "  1. Use authorize_action() from app.auth.authorization_choke instead"
            )
            print("  2. Add resource to m7_to_m28.py mapping if needed")
            print(
                "  3. If file MUST use M7, add to ALLOWED_M7_IMPORTERS (requires approval)"
            )
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
