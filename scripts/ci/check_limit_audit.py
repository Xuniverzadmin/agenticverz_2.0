#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL: LIMITS-003 - Audit on Limit Change
# artifact_class: CODE
"""
GUARDRAIL: LIMITS-003 - Audit on Limit Change
Rule: Every limit change MUST emit an audit entry.

This script validates that limit modification code includes audit logging.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Files that modify limits
LIMIT_MODIFICATION_FILES = [
    "limit*.py",
    "policy*.py",
    "budget*.py",
    "quota*.py",
]

# Patterns indicating limit modification
LIMIT_MODIFICATION_PATTERNS = [
    r'update.*limit',
    r'set.*limit',
    r'create.*limit',
    r'delete.*limit',
    r'modify.*limit',
    r'change.*limit',
    r'limit\s*=',
    r'max_.*\s*=',
    r'threshold.*=',
    r'budget.*=',
    r'quota.*=',
    r'\.update\s*\([^)]*limit',
    r'\.add\s*\([^)]*Limit',
    r'INSERT.*limit',
    r'UPDATE.*limit',
]

# Patterns indicating audit logging
AUDIT_PATTERNS = [
    r'audit.*ledger',
    r'emit.*audit',
    r'log.*audit',
    r'AuditLedgerService',
    r'create_audit_entry',
    r'audit_service',
    r'record_change',
    r'emit_governance_event',
    r'governance_audit',
]


def find_limit_modifying_functions(content: str) -> List[Tuple[str, str]]:
    """Find functions that modify limits."""
    functions = []

    # Extract all functions
    func_pattern = r'(?:async\s+)?def\s+(\w+)\s*\([^)]*\).*?(?=(?:async\s+)?def\s+|\Z)'
    matches = re.finditer(func_pattern, content, re.DOTALL)

    for match in matches:
        func_name = match.group(1)
        func_content = match.group(0)

        # Check if this function modifies limits
        for pattern in LIMIT_MODIFICATION_PATTERNS:
            if re.search(pattern, func_content, re.IGNORECASE):
                # Skip getter functions
                if func_name.startswith('get_') or func_name.startswith('_'):
                    continue
                functions.append((func_name, func_content))
                break

    return functions


def has_audit_logging(func_content: str) -> bool:
    """Check if function includes audit logging."""
    for pattern in AUDIT_PATTERNS:
        if re.search(pattern, func_content, re.IGNORECASE):
            return True
    return False


def check_file(file_path: Path) -> List[str]:
    """Check a file for limit modifications without audit logging."""
    violations = []

    with open(file_path, 'r') as f:
        content = f.read()

    limit_modifiers = find_limit_modifying_functions(content)

    for func_name, func_content in limit_modifiers:
        if not has_audit_logging(func_content):
            violations.append(
                f"Function: {func_name} in {file_path.name}\n"
                f"  → Modifies limits WITHOUT audit logging\n"
                f"  → Must emit audit entry on limit changes"
            )

    return violations


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app"

    print("LIMITS-003: Audit on Limit Change")
    print("=" * 50)

    all_violations = []
    files_checked = 0

    # Check services
    services_path = backend_path / "services"
    if services_path.exists():
        for pattern in LIMIT_MODIFICATION_FILES:
            for py_file in services_path.glob(pattern):
                files_checked += 1
                violations = check_file(py_file)
                all_violations.extend(violations)

    # Check API routes
    api_path = backend_path / "api"
    if api_path.exists():
        for pattern in LIMIT_MODIFICATION_FILES:
            for py_file in api_path.glob(pattern):
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

        print("\nLimit changes MUST be audited!")
        print("Every limit modification must:")
        print("  1. Call audit_ledger_service.emit_governance_event()")
        print("  2. Include: who changed, what changed, old value, new value")
        print("  3. Be immutable and timestamped")
        sys.exit(1)
    else:
        print("✓ All limit modifications include audit logging")
        sys.exit(0)


if __name__ == "__main__":
    main()
