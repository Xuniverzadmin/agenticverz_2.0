#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: PIN-399 Phase-5 Test Terminology Lint
# Callers: CI pipeline, pre-commit hooks
# Allowed Imports: None (static analysis only)
# Forbidden Imports: L1, L2, L3, L4, L5, L6
# Reference: PIN-399 Phase-5 (Post-Onboarding Permissions & Roles)

"""
Phase-5 Test Terminology Lint

This script WARNS (or FAILS in strict mode) if tests use deprecated terminology
that could confuse future contributors or LLMs about the auth model.

PIN-399 HYGIENE-001:
> No test may assert behavior that the architecture already forbids structurally.

BANNED TERMS (in test names/docstrings):
- "permission" (use "role-derived permission" or just "role")
- "admin user" (use "user with ADMIN role")
- "superuser" (use "founder" - separate auth)
- "console access" (use "UI surface")
- "bypass" in role context (use "explicit exception")
- "has_access" (use "has_role")

ALLOWED EXCEPTIONS:
- PERMISSION_DENIED as an error code
- ErrorCategory.PERMISSION
- permission_gaps (skill/capability context)
- operator_bypass (RBAC system, not Phase-5)

USAGE
-----
    python scripts/ci/check_test_terminology.py [--strict] [--verbose]

EXIT CODES
----------
    0 = No violations (or warnings only in non-strict mode)
    1 = Violations found (strict mode)
    2 = Script error
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Violation:
    """A terminology violation."""

    file: Path
    line_num: int
    term: str
    context: str
    suggestion: str
    is_name: bool  # True if in function/class name, False if in docstring


# Banned terms with context-aware rules
BANNED_PATTERNS = [
    {
        "pattern": r"\bpermission\b",
        "in_names": True,
        "in_docstrings": True,
        "suggestion": "Use 'role' or 'role-derived permission'",
        "exceptions": [
            r"PERMISSION_DENIED",
            r"permission_gaps",
            r"ErrorCategory\.PERMISSION",
            r"role_has_permission",  # Phase-5 function name
            r"has_permission",  # RBAC Actor method (legitimate)
            r"check_permission",  # RBAC function (legitimate)
            r"compute_permissions",  # RBAC function (legitimate)
            r"insufficient.permission",  # RBAC error message
            r"no_permission",  # RBAC reason code
            r"map_policy_to_permission",  # RBAC mapping
            r"TestPermissionDerivation",  # Phase-5 test class
            r"test_.*permission.*",  # Allow permission in test names (RBAC tests)
        ],
    },
    {
        "pattern": r"\badmin[_\s]user\b",
        "in_names": True,
        "in_docstrings": True,
        "suggestion": "Use 'user with ADMIN role'",
        "exceptions": [],
    },
    {
        "pattern": r"\bsuperuser\b",
        "in_names": True,
        "in_docstrings": True,
        "suggestion": "Use 'founder' (separate auth system)",
        "exceptions": [],
    },
    {
        "pattern": r"\bconsole[_\s]access\b",
        "in_names": True,
        "in_docstrings": True,
        "suggestion": "Use 'UI surface'",
        "exceptions": [],
    },
    {
        "pattern": r"\bhas[_\s]access\b",
        "in_names": True,
        "in_docstrings": False,  # Only ban in names
        "suggestion": "Use 'has_role' for Phase-5 checks",
        "exceptions": [
            r"has_access",  # Allow the method name itself
        ],
    },
    {
        "pattern": r"\badmin[_\s]can[_\s]do\b",
        "in_names": True,
        "in_docstrings": True,
        "suggestion": "Be specific about role: 'ADMIN role can...'",
        "exceptions": [],
    },
    {
        "pattern": r"\buser[_\s]has[_\s]permission\b",
        "in_names": True,
        "in_docstrings": True,
        "suggestion": "Use 'role has permission' or 'user with role can...'",
        "exceptions": [],
    },
]

# File patterns to check
TEST_FILE_PATTERNS = [
    "tests/**/*.py",
]

# Files to skip (legacy RBAC tests that use correct terminology for their layer)
SKIP_FILES = [
    # These test the RBAC layer, not Phase-5
    # "test_rbac_engine.py",
    # "test_authorization.py",
]


def matches_exception(line: str, exceptions: list[str]) -> bool:
    """Check if line matches any exception pattern."""
    for exc in exceptions:
        if re.search(exc, line, re.IGNORECASE):
            return True
    return False


def is_in_name(line: str) -> bool:
    """Check if match is in a function/class name."""
    # Look for def/class before the match
    stripped = line.lstrip()
    if stripped.startswith("def ") or stripped.startswith("class "):
        return True
    return False


def is_in_docstring(lines: list[str], line_idx: int) -> bool:
    """Check if line is inside a docstring."""
    in_docstring = False
    docstring_char: Optional[str] = None

    for i in range(line_idx + 1):
        line = lines[i]
        for marker in ['"""', "'''"]:
            count = line.count(marker)
            if count > 0:
                if not in_docstring:
                    in_docstring = True
                    docstring_char = marker
                    if count >= 2:
                        in_docstring = False
                elif docstring_char == marker:
                    in_docstring = False
                    docstring_char = None

    return in_docstring


def check_file(file_path: Path, verbose: bool = False) -> list[Violation]:
    """Check a single test file for terminology violations."""
    violations = []

    # Skip certain files
    if file_path.name in SKIP_FILES:
        if verbose:
            print(f"  [SKIP] {file_path.name}")
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        if verbose:
            print(f"  [ERROR] Could not read {file_path}: {e}")
        return []

    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        for pattern_def in BANNED_PATTERNS:
            regex = re.compile(pattern_def["pattern"], re.IGNORECASE)
            match = regex.search(line)

            if not match:
                continue

            # Check exceptions
            if matches_exception(line, pattern_def.get("exceptions", [])):
                continue

            # Check if in name vs docstring
            in_name = is_in_name(line)
            in_docstring = is_in_docstring(lines, line_num - 1)

            # Apply context rules
            if in_name and not pattern_def.get("in_names", True):
                continue
            if in_docstring and not pattern_def.get("in_docstrings", True):
                continue
            if not in_name and not in_docstring:
                continue  # Only check names and docstrings

            violations.append(
                Violation(
                    file=file_path,
                    line_num=line_num,
                    term=match.group(),
                    context=line.strip()[:80],
                    suggestion=pattern_def["suggestion"],
                    is_name=in_name,
                )
            )

    return violations


def find_test_files(root: Path) -> list[Path]:
    """Find all test files."""
    test_dir = root / "tests"
    if not test_dir.exists():
        return []

    files = list(test_dir.rglob("*.py"))
    return [f for f in files if f.name.startswith("test_")]


def print_violation(v: Violation) -> None:
    """Print a single violation."""
    location = "name" if v.is_name else "docstring"
    print(f"\n  {v.file.name}:{v.line_num} [{location}]")
    print(f"    Term: '{v.term}'")
    print(f"    Context: {v.context}")
    print(f"    Suggestion: {v.suggestion}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check tests for deprecated terminology (PIN-399)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show files being checked"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Fail on any violation (default: warn)"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to backend directory (default: current directory)",
    )

    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"ERROR: Path does not exist: {root}")
        return 2

    # Find root
    if (root / "tests").exists():
        pass
    elif (root / "backend" / "tests").exists():
        root = root / "backend"
    else:
        print(f"ERROR: Could not find tests directory in: {root}")
        return 2

    print("PIN-399 Phase-5 Test Terminology Lint")
    print(f"Scanning: {root}/tests/")
    print()

    test_files = find_test_files(root)
    all_violations = []

    if args.verbose:
        print(f"Found {len(test_files)} test files")

    for file_path in test_files:
        if args.verbose:
            print(f"  Checking: {file_path.name}")
        violations = check_file(file_path, args.verbose)
        all_violations.extend(violations)

    if all_violations:
        # Group by file
        by_file: dict[str, list[Violation]] = {}
        for v in all_violations:
            key = str(v.file)
            if key not in by_file:
                by_file[key] = []
            by_file[key].append(v)

        print(f"{'#' * 60}")
        print(f"# TERMINOLOGY WARNINGS: {len(all_violations)}")
        print(f"{'#' * 60}")

        for file_path, violations in by_file.items():
            print(f"\n{Path(file_path).name}: {len(violations)} warnings")
            for v in violations:
                print_violation(v)

        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total warnings: {len(all_violations)}")
        print()
        print("PIN-399 Phase-5 HYGIENE-001:")
        print("- Test names should use 'role' not 'permission' (for Phase-5)")
        print("- Use 'user with ADMIN role' not 'admin user'")
        print("- Use 'founder' not 'superuser'")
        print()

        if args.strict:
            print("STRICT MODE: Failing due to terminology violations")
            return 1
        else:
            print("Non-strict mode: Warnings only (use --strict to fail)")
            return 0

    print(f"{'=' * 60}")
    print("All test terminology is compliant")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
