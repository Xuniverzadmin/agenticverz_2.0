#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL: DOMAIN-002 - No Domain Data in Account Section
# artifact_class: CODE
"""
GUARDRAIL: DOMAIN-002 - No Domain Data in Account Section
Rule: Account pages must NOT display Activity, Incidents, Policies, or Logs data.

This script checks that accounts.py does not import domain models.
"""

import re
import sys
from pathlib import Path

# Forbidden imports in accounts module
FORBIDDEN_IMPORTS = [
    r'from\s+app\.models\.incident',
    r'from\s+app\.models\.policy',
    r'from\s+app\.models\.worker_runs',
    r'from\s+app\.models\.runs',
    r'from\s+app\.models\.audit_ledger',
    r'from\s+app\.models\.aos_traces',
    r'from\s+app\.models\.cost_records',
    r'from\s+app\.models\.cost_anomalies',
    r'import\s+Incident',
    r'import\s+PolicyRule',
    r'import\s+WorkerRun',
    r'import\s+AuditLedger',
]

# Forbidden table references
FORBIDDEN_TABLES = [
    'incidents',
    'policy_rules',
    'policy_proposals',
    'worker_runs',
    'runs',
    'audit_ledger',
    'aos_traces',
    'cost_records',
]


def check_accounts_file(file_path: str) -> list:
    """Check accounts.py for forbidden imports."""
    violations = []

    with open(file_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')

    # Check for forbidden imports
    for i, line in enumerate(lines, 1):
        for pattern in FORBIDDEN_IMPORTS:
            if re.search(pattern, line):
                violations.append(
                    f"Line {i}: Forbidden import detected\n"
                    f"  {line.strip()}\n"
                    f"  → Account section must not import domain models"
                )

    # Check for forbidden table references
    for i, line in enumerate(lines, 1):
        for table in FORBIDDEN_TABLES:
            if re.search(rf'\b{table}\b', line, re.IGNORECASE):
                # Skip if it's a comment
                if line.strip().startswith('#'):
                    continue
                violations.append(
                    f"Line {i}: Forbidden table reference detected\n"
                    f"  {line.strip()}\n"
                    f"  → Account section must not reference '{table}' table"
                )

    return violations


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app" / "api"
    accounts_file = backend_path / "accounts.py"

    print("DOMAIN-002: Account Boundary Check")
    print("=" * 50)

    if not accounts_file.exists():
        print(f"accounts.py not found at {accounts_file}")
        print("✓ No accounts.py file (boundary respected by absence)")
        sys.exit(0)

    violations = check_accounts_file(str(accounts_file))

    print(f"File checked: {accounts_file}")
    print(f"Violations found: {len(violations)}")
    print()

    if violations:
        print("VIOLATIONS:")
        print("-" * 50)
        for v in violations:
            print(v)
            print()
        sys.exit(1)
    else:
        print("✓ Account boundaries respected - no domain data imports")
        sys.exit(0)


if __name__ == "__main__":
    main()
