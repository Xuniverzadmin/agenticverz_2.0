#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL: LIMITS-002 - Pre-Execution Check Required
# artifact_class: CODE
"""
GUARDRAIL: LIMITS-002 - Pre-Execution Check Required
Rule: Every run creation MUST check limits BEFORE execution.

This script validates that run creation includes limit checks.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Files that create runs (need limit checks)
RUN_CREATION_FILES = [
    "runs.py",
    "activity.py",
    "execute.py",
    "runner.py",
    "worker_runner.py",
]

# Patterns indicating run creation
RUN_CREATION_PATTERNS = [
    r'create_run\s*\(',
    r'WorkerRun\s*\(',
    r'Run\s*\(',
    r'start_execution\s*\(',
    r'execute_run\s*\(',
    r'POST.*\/runs',
    r'@router\.post.*runs',
]

# Patterns indicating limit check
LIMIT_CHECK_PATTERNS = [
    r'check.*limit',
    r'limit.*check',
    r'can_create_run',
    r'can_use_tokens',
    r'check_all_limits',
    r'verify_limits',
    r'enforce_limits',
    r'LimitService',
    r'LimitsService',
    r'quota_check',
    r'check_quota',
    r'budget_check',
]


def find_run_creation_functions(content: str) -> List[Tuple[str, str]]:
    """Find functions that create runs."""
    functions = []

    # Extract all functions
    func_pattern = r'(?:async\s+)?def\s+(\w+)\s*\([^)]*\).*?(?=(?:async\s+)?def\s+|\Z)'
    matches = re.finditer(func_pattern, content, re.DOTALL)

    for match in matches:
        func_name = match.group(1)
        func_content = match.group(0)

        # Check if this function creates runs
        for pattern in RUN_CREATION_PATTERNS:
            if re.search(pattern, func_content, re.IGNORECASE):
                functions.append((func_name, func_content))
                break

    return functions


def has_limit_check(func_content: str) -> bool:
    """Check if function includes limit checking."""
    for pattern in LIMIT_CHECK_PATTERNS:
        if re.search(pattern, func_content, re.IGNORECASE):
            return True
    return False


def check_file(file_path: Path) -> List[str]:
    """Check a file for run creation without limit checks."""
    violations = []

    with open(file_path, 'r') as f:
        content = f.read()

    run_creators = find_run_creation_functions(content)

    for func_name, func_content in run_creators:
        if not has_limit_check(func_content):
            violations.append(
                f"Function: {func_name} in {file_path.name}\n"
                f"  → Creates runs WITHOUT limit check\n"
                f"  → Must call check_all_limits() BEFORE run creation"
            )

    return violations


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app"

    print("LIMITS-002: Pre-Execution Limit Check")
    print("=" * 50)

    all_violations = []
    files_checked = 0

    # Check API routes
    api_path = backend_path / "api"
    if api_path.exists():
        for file_name in RUN_CREATION_FILES:
            file_path = api_path / file_name
            if file_path.exists():
                files_checked += 1
                violations = check_file(file_path)
                all_violations.extend(violations)

    # Check services
    services_path = backend_path / "services"
    if services_path.exists():
        for file_name in RUN_CREATION_FILES:
            file_path = services_path / file_name
            if file_path.exists():
                files_checked += 1
                violations = check_file(file_path)
                all_violations.extend(violations)

    # Check worker
    worker_path = backend_path / "worker"
    if worker_path.exists():
        for py_file in worker_path.glob("*.py"):
            if py_file.name in RUN_CREATION_FILES or "runner" in py_file.name:
                files_checked += 1
                violations = check_file(py_file)
                all_violations.extend(violations)

    print(f"Files checked: {files_checked}")
    print(f"Violations found: {len(all_violations)}")
    print()

    if all_violations:
        print("VIOLATIONS:")
        print("-" * 50)
        for v in all_violations:
            print(v)
            print()

        print("\nPre-execution limit checking is MANDATORY.")
        print("Every run creation path must:")
        print("  1. Call limits_service.check_all_limits()")
        print("  2. Block if any limit exceeded")
        print("  3. Return clear error with limit details")
        sys.exit(1)
    else:
        print("✓ All run creation includes limit checks")
        sys.exit(0)


if __name__ == "__main__":
    main()
