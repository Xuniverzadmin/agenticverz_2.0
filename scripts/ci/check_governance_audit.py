#!/usr/bin/env python3
"""
GUARDRAIL: AUDIT-001 - Governance Actions Must Emit Audit
Rule: Every governance action MUST create an audit entry.

This script validates that governance operations include audit logging.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Governance operations that MUST emit audit
GOVERNANCE_OPERATIONS = [
    # Limit operations
    (r'create.*limit|set.*limit', 'limit_created'),
    (r'update.*limit|modify.*limit|change.*limit', 'limit_modified'),
    (r'delete.*limit|remove.*limit', 'limit_removed'),

    # Policy operations
    (r'create.*policy|add.*policy|new.*policy', 'policy_created'),
    (r'update.*policy|modify.*policy', 'policy_modified'),
    (r'approve.*policy|reject.*policy', 'policy_decision'),
    (r'delete.*policy|remove.*policy', 'policy_removed'),

    # Incident operations
    (r'resolve.*incident|close.*incident', 'incident_resolved'),
    (r'escalate.*incident', 'incident_escalated'),
    (r'assign.*incident', 'incident_assigned'),

    # Access operations
    (r'grant.*access|revoke.*access', 'access_changed'),
    (r'create.*api.*key|revoke.*api.*key', 'api_key_changed'),
]

# Audit emission patterns
AUDIT_PATTERNS = [
    r'audit.*ledger',
    r'emit.*audit',
    r'AuditLedgerService',
    r'create_audit_entry',
    r'log_governance',
    r'emit_governance_event',
    r'audit_service\.emit',
    r'record_governance',
]


def find_governance_functions(content: str) -> List[Tuple[str, str, str]]:
    """Find functions that perform governance operations."""
    functions = []

    # Extract all functions
    func_pattern = r'(?:async\s+)?def\s+(\w+)\s*\([^)]*\).*?(?=(?:async\s+)?def\s+|\Z)'
    matches = re.finditer(func_pattern, content, re.DOTALL)

    for match in matches:
        func_name = match.group(1)
        func_content = match.group(0)

        # Check if this function performs governance operations
        for op_pattern, op_type in GOVERNANCE_OPERATIONS:
            if re.search(op_pattern, func_content, re.IGNORECASE):
                # Skip getter functions
                if func_name.startswith('get_') or func_name.startswith('_'):
                    continue
                functions.append((func_name, func_content, op_type))
                break

    return functions


def has_audit_emission(func_content: str) -> bool:
    """Check if function emits audit entry."""
    for pattern in AUDIT_PATTERNS:
        if re.search(pattern, func_content, re.IGNORECASE):
            return True
    return False


def check_file(file_path: Path) -> List[str]:
    """Check a file for governance operations without audit emission."""
    violations = []

    with open(file_path, 'r') as f:
        content = f.read()

    governance_funcs = find_governance_functions(content)

    for func_name, func_content, op_type in governance_funcs:
        if not has_audit_emission(func_content):
            violations.append(
                f"Function: {func_name} in {file_path.name}\n"
                f"  Operation type: {op_type}\n"
                f"  → Governance action WITHOUT audit emission\n"
                f"  → Must emit audit entry for {op_type}"
            )

    return violations


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app"

    print("AUDIT-001: Governance Actions Audit Check")
    print("=" * 50)

    all_violations = []
    files_checked = 0

    # Check services
    services_path = backend_path / "services"
    if services_path.exists():
        for py_file in services_path.glob("*.py"):
            files_checked += 1
            violations = check_file(py_file)
            all_violations.extend(violations)

    # Check API routes
    api_path = backend_path / "api"
    if api_path.exists():
        for py_file in api_path.glob("*.py"):
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

        print("\nGovernance actions MUST emit audit entries!")
        print("Every governance operation requires:")
        print("  1. Call audit_ledger_service.emit_governance_event()")
        print("  2. Include: actor, action, target, before_state, after_state")
        print("  3. Be timestamped and immutable")
        sys.exit(1)
    else:
        print("✓ All governance actions include audit emission")
        sys.exit(0)


if __name__ == "__main__":
    main()
