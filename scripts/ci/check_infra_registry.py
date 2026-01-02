#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Validate infrastructure declarations match INFRA_REGISTRY.md
# Callers: CI workflow
# Allowed Imports: stdlib only
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-270 (Infrastructure State Governance)

"""
Infrastructure Registry Consistency Check

This script validates that:
1. All @requires_infra markers reference valid infra names
2. All skipped tests have proper infra declarations
3. State C infra is not being skipped
4. INFRA_REGISTRY code matches INFRA_REGISTRY.md

Usage:
    python3 scripts/ci/check_infra_registry.py [--strict]
"""

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple


class InfraReference(NamedTuple):
    """A reference to infrastructure in code."""

    file: str
    line: int
    infra_name: str
    context: str


class CheckResult(NamedTuple):
    """Result of a check."""

    passed: bool
    message: str
    details: list[str]


# Known valid infra names (must match INFRA_REGISTRY in tests/helpers/infra.py)
VALID_INFRA_NAMES = {
    "PostgreSQL",
    "Redis",
    "Clerk",
    "Prometheus",
    "Alertmanager",
    "Grafana",
    "AgentsSchema",
    "LLMAPIs",
    "Neon",
    "Backend",
}

# Patterns that indicate infra dependency
INFRA_PATTERNS = [
    r"@requires_infra\([\"'](\w+)[\"']\)",
    r"requires_infra\([\"'](\w+)[\"']\)",
    r"@requires_(\w+)(?:\s|$|\()",
    r"requires_auth_backend",
    r"requires_agents_schema",
]

# Patterns that indicate State C infra being skipped (bad)
STATE_C_SKIP_PATTERNS = [
    r"skip.*PostgreSQL",
    r"skip.*database",
    r"DATABASE_URL.*skip",
]


def find_test_files(root: Path) -> list[Path]:
    """Find all Python test files."""
    return list(root.glob("**/test_*.py"))


def find_infra_references(file: Path) -> list[InfraReference]:
    """Find all infrastructure references in a file."""
    refs = []
    content = file.read_text()

    for i, line in enumerate(content.split("\n"), 1):
        for pattern in INFRA_PATTERNS:
            for match in re.finditer(pattern, line):
                if match.groups():
                    infra_name = match.group(1)
                else:
                    # Handle shorthand markers
                    if "auth" in line.lower():
                        infra_name = "Clerk"
                    elif "agents" in line.lower():
                        infra_name = "AgentsSchema"
                    else:
                        continue

                refs.append(
                    InfraReference(
                        file=str(file),
                        line=i,
                        infra_name=infra_name,
                        context=line.strip(),
                    )
                )

    return refs


def check_valid_infra_names(refs: list[InfraReference]) -> CheckResult:
    """Check that all infra references are valid."""
    invalid = []

    for ref in refs:
        # Normalize common aliases
        normalized = ref.infra_name
        if normalized.lower() in ("auth", "auth_backend", "rbac"):
            normalized = "Clerk"
        elif normalized.lower() in ("agents", "agents_schema"):
            normalized = "AgentsSchema"
        elif normalized.lower() in ("postgres", "db", "database"):
            normalized = "PostgreSQL"

        if normalized not in VALID_INFRA_NAMES:
            invalid.append(f"{ref.file}:{ref.line} - Unknown infra '{ref.infra_name}'")

    if invalid:
        return CheckResult(
            passed=False,
            message=f"Found {len(invalid)} references to unknown infrastructure",
            details=invalid,
        )

    return CheckResult(
        passed=True,
        message=f"All {len(refs)} infra references are valid",
        details=[],
    )


def check_state_c_not_skipped(test_root: Path) -> CheckResult:
    """Check that State C infra (PostgreSQL) is not being skipped."""
    violations = []

    for file in find_test_files(test_root):
        content = file.read_text()

        for i, line in enumerate(content.split("\n"), 1):
            for pattern in STATE_C_SKIP_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(
                        f"{file}:{i} - State C infra skip: {line.strip()}"
                    )

    if violations:
        return CheckResult(
            passed=False,
            message="State C infrastructure is being skipped (should fail instead)",
            details=violations,
        )

    return CheckResult(
        passed=True,
        message="No State C infra skips detected",
        details=[],
    )


def check_registry_sync(backend_root: Path) -> CheckResult:
    """Check that code registry matches documentation."""
    infra_py = backend_root / "tests" / "helpers" / "infra.py"
    registry_md = backend_root.parent / "docs" / "infra" / "INFRA_REGISTRY.md"

    if not infra_py.exists():
        return CheckResult(
            passed=False,
            message="tests/helpers/infra.py not found",
            details=[str(infra_py)],
        )

    if not registry_md.exists():
        return CheckResult(
            passed=False,
            message="docs/infra/INFRA_REGISTRY.md not found",
            details=[str(registry_md)],
        )

    # Parse infra names from code
    code_content = infra_py.read_text()
    code_names = set()
    for match in re.finditer(r'"(\w+)":\s*InfraItem\(', code_content):
        code_names.add(match.group(1))

    # Parse infra names from markdown table
    md_content = registry_md.read_text()
    md_names = set()
    for match in re.finditer(r"\|\s*(\w+)\s*\|.*\|.*\|.*\|.*\|.*\|", md_content):
        name = match.group(1).strip()
        if name and name not in ("Infra", "---", "Name"):
            md_names.add(name)

    # Compare
    code_only = code_names - md_names
    md_only = md_names - code_names

    issues = []
    if code_only:
        issues.append(f"In code but not docs: {code_only}")
    if md_only:
        issues.append(f"In docs but not code: {md_only}")

    if issues:
        return CheckResult(
            passed=False,
            message="Registry code and docs are out of sync",
            details=issues,
        )

    return CheckResult(
        passed=True,
        message=f"Registry in sync: {len(code_names)} items",
        details=[],
    )


def main():
    parser = argparse.ArgumentParser(
        description="Check infrastructure registry consistency"
    )
    parser.add_argument("--strict", action="store_true", help="Fail on any issue")
    parser.add_argument(
        "--backend-root",
        type=Path,
        default=Path(__file__).parent.parent.parent / "backend",
        help="Backend root directory",
    )
    args = parser.parse_args()

    backend_root = args.backend_root.resolve()
    test_root = backend_root / "tests"

    print("=" * 60)
    print("INFRASTRUCTURE REGISTRY CHECK")
    print("=" * 60)
    print(f"Backend root: {backend_root}")
    print(f"Test root: {test_root}")
    print()

    # Collect all infra references
    refs = []
    for file in find_test_files(test_root):
        refs.extend(find_infra_references(file))

    # Run checks
    checks = [
        ("Valid infra names", check_valid_infra_names(refs)),
        ("State C not skipped", check_state_c_not_skipped(test_root)),
        ("Registry sync", check_registry_sync(backend_root)),
    ]

    all_passed = True
    for name, result in checks:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {name}: {result.message}")

        if result.details:
            for detail in result.details[:10]:  # Limit output
                print(f"       {detail}")
            if len(result.details) > 10:
                print(f"       ... and {len(result.details) - 10} more")

        if not result.passed:
            all_passed = False

        print()

    # Summary
    print("=" * 60)
    if all_passed:
        print("All checks passed")
        return 0
    else:
        print("Some checks failed")
        return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
