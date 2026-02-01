#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL: AUDIT-002 - Audit Entry Completeness
# artifact_class: CODE
"""
GUARDRAIL: AUDIT-002 - Audit Entry Completeness
Rule: Every audit entry MUST have required fields.

This script validates that audit entry creation includes all required fields.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Required fields for audit entries
REQUIRED_AUDIT_FIELDS = [
    'actor',           # Who performed the action
    'action',          # What action was taken
    'target',          # What was acted upon
    'timestamp',       # When it happened
    'tenant_id',       # Tenant context
]

# Optional but recommended fields
RECOMMENDED_AUDIT_FIELDS = [
    'before_state',    # State before change
    'after_state',     # State after change
    'reason',          # Why the action was taken
    'source',          # Where the action originated
]

# Patterns indicating audit entry creation
AUDIT_CREATION_PATTERNS = [
    r'AuditEntry\s*\(',
    r'create_audit_entry\s*\(',
    r'emit_governance_event\s*\(',
    r'audit_ledger.*\.emit\s*\(',
    r'audit_service\.create\s*\(',
]


def find_audit_creations(content: str, file_path: str) -> List[Tuple[int, str]]:
    """Find all audit entry creation calls."""
    creations = []

    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for pattern in AUDIT_CREATION_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Get the context (next 10 lines or until closing paren)
                context_lines = lines[i-1:i+20]
                context = '\n'.join(context_lines)

                # Find the full call (until balanced parens)
                paren_count = 0
                full_call = []
                started = False
                for ctx_line in context_lines:
                    for char in ctx_line:
                        if char == '(':
                            started = True
                            paren_count += 1
                        elif char == ')':
                            paren_count -= 1
                    full_call.append(ctx_line)
                    if started and paren_count == 0:
                        break

                creations.append((i, '\n'.join(full_call)))

    return creations


def check_required_fields(call_content: str) -> List[str]:
    """Check if an audit creation includes required fields."""
    missing = []

    for field in REQUIRED_AUDIT_FIELDS:
        # Check for field as named parameter or dict key
        patterns = [
            rf'{field}\s*=',         # named parameter
            rf'["\']?{field}["\']?\s*:',  # dict key
            rf'\.{field}\s*=',       # attribute assignment
        ]
        found = False
        for pattern in patterns:
            if re.search(pattern, call_content, re.IGNORECASE):
                found = True
                break
        if not found:
            missing.append(field)

    return missing


def check_recommended_fields(call_content: str) -> List[str]:
    """Check for recommended but missing fields."""
    missing = []

    for field in RECOMMENDED_AUDIT_FIELDS:
        patterns = [
            rf'{field}\s*=',
            rf'["\']?{field}["\']?\s*:',
            rf'\.{field}\s*=',
        ]
        found = False
        for pattern in patterns:
            if re.search(pattern, call_content, re.IGNORECASE):
                found = True
                break
        if not found:
            missing.append(field)

    return missing


def check_file(file_path: Path) -> Tuple[List[str], List[str]]:
    """Check a file for incomplete audit entries."""
    violations = []
    warnings = []

    with open(file_path, 'r') as f:
        content = f.read()

    audit_creations = find_audit_creations(content, str(file_path))

    for line_num, call_content in audit_creations:
        missing_required = check_required_fields(call_content)
        missing_recommended = check_recommended_fields(call_content)

        if missing_required:
            violations.append(
                f"File: {file_path.name}:{line_num}\n"
                f"  → Missing REQUIRED fields: {', '.join(missing_required)}\n"
                f"  → All audit entries must include: {', '.join(REQUIRED_AUDIT_FIELDS)}"
            )

        if missing_recommended and not missing_required:
            warnings.append(
                f"File: {file_path.name}:{line_num}\n"
                f"  → Missing recommended fields: {', '.join(missing_recommended)}\n"
                f"  → Consider adding: {', '.join(missing_recommended)}"
            )

    return violations, warnings


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app"

    print("AUDIT-002: Audit Entry Completeness Check")
    print("=" * 50)

    all_violations = []
    all_warnings = []
    files_checked = 0

    # Check services
    services_path = backend_path / "services"
    if services_path.exists():
        for py_file in services_path.glob("*.py"):
            files_checked += 1
            violations, warnings = check_file(py_file)
            all_violations.extend(violations)
            all_warnings.extend(warnings)

    # Check API routes
    api_path = backend_path / "api"
    if api_path.exists():
        for py_file in api_path.glob("*.py"):
            files_checked += 1
            violations, warnings = check_file(py_file)
            all_violations.extend(violations)
            all_warnings.extend(warnings)

    # Check models (for AuditEntry class definition)
    models_path = backend_path / "models"
    if models_path.exists():
        for py_file in models_path.glob("*.py"):
            files_checked += 1
            violations, warnings = check_file(py_file)
            all_violations.extend(violations)
            all_warnings.extend(warnings)

    print(f"Files checked: {files_checked}")
    print(f"Violations (missing required): {len(all_violations)}")
    print(f"Warnings (missing recommended): {len(all_warnings)}")
    print()

    if all_warnings:
        print("WARNINGS (recommended fields):")
        print("-" * 50)
        for w in all_warnings[:5]:  # Show first 5
            print(w)
            print()
        if len(all_warnings) > 5:
            print(f"  ... and {len(all_warnings) - 5} more warnings")
            print()

    if all_violations:
        print("VIOLATIONS (missing required fields):")
        print("-" * 50)
        for v in all_violations:
            print(v)
            print()

        print("\nAudit entries MUST be complete!")
        print("Required fields: " + ", ".join(REQUIRED_AUDIT_FIELDS))
        print("\nIncomplete audit entries compromise:")
        print("  - Incident investigation")
        print("  - Compliance reporting")
        print("  - Root cause analysis")
        sys.exit(1)
    else:
        print("✓ All audit entries include required fields")
        sys.exit(0)


if __name__ == "__main__":
    main()
