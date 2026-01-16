#!/usr/bin/env python3
"""
GUARDRAIL: DOMAIN-001 - Domain Ownership Enforcement
Rule: Each table belongs to exactly ONE domain. No cross-domain writes.

This script scans all service files and validates that services only write
to tables owned by their domain.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

# Domain → Tables ownership map
DOMAIN_TABLE_OWNERSHIP: Dict[str, List[str]] = {
    "Activity": [
        "runs", "worker_runs", "agents", "agent_configs",
        "run_steps", "run_artifacts"
    ],
    "Incidents": [
        "incidents", "incident_notes", "incident_attachments",
        "incident_timeline"
    ],
    "Policies": [
        "policy_rules", "policy_proposals", "limits", "limit_breaches",
        "prevention_records", "policy_rule_integrity", "limit_integrity"
    ],
    "Analytics": [
        "cost_records", "cost_budgets", "cost_anomalies", "feature_tags",
        "cost_snapshots", "usage_records"
    ],
    "Logs": [
        "audit_ledger", "aos_traces", "aos_trace_steps",
        "llm_run_records", "system_records", "domain_events"
    ],
    "Accounts": [
        "tenants", "users", "tenant_memberships", "api_keys",
        "subscriptions", "usage_records", "invitations"
    ],
    "Connectivity": [
        "worker_registry", "worker_configs", "integrations"
    ],
}

# Service file → Domain mapping (based on directory/naming)
SERVICE_DOMAIN_MAP: Dict[str, str] = {
    "activity": "Activity",
    "incident": "Incidents",
    "policy": "Policies",
    "cost": "Analytics",
    "analytics": "Analytics",
    "audit": "Logs",
    "trace": "Logs",
    "log": "Logs",
    "tenant": "Accounts",
    "user": "Accounts",
    "account": "Accounts",
    "key": "Connectivity",
    "worker": "Connectivity",
    "integration": "Connectivity",
}

# Write operation patterns to detect
WRITE_PATTERNS = [
    r'session\.add\s*\(',
    r'session\.commit\s*\(',
    r'\.create\s*\(',
    r'\.update\s*\(',
    r'\.delete\s*\(',
    r'INSERT\s+INTO\s+(\w+)',
    r'UPDATE\s+(\w+)\s+SET',
    r'DELETE\s+FROM\s+(\w+)',
]

# Model import patterns
MODEL_IMPORT_PATTERN = r'from\s+app\.models\.(\w+)\s+import\s+(\w+)'


def get_table_owner(table: str) -> str:
    """Get the domain that owns a table."""
    for domain, tables in DOMAIN_TABLE_OWNERSHIP.items():
        if table.lower() in [t.lower() for t in tables]:
            return domain
    return "Unknown"


def get_service_domain(file_path: str) -> str:
    """Determine domain from service file path/name."""
    file_name = Path(file_path).stem.lower()

    for keyword, domain in SERVICE_DOMAIN_MAP.items():
        if keyword in file_name:
            return domain

    # Check directory path
    path_str = str(file_path).lower()
    for keyword, domain in SERVICE_DOMAIN_MAP.items():
        if f"/{keyword}" in path_str:
            return domain

    return "Unknown"


def extract_model_imports(content: str) -> Set[str]:
    """Extract model class names from imports."""
    models = set()
    for match in re.finditer(MODEL_IMPORT_PATTERN, content):
        models.add(match.group(2))
    return models


def model_to_table(model_name: str) -> str:
    """Convert model class name to table name (CamelCase → snake_case)."""
    # Simple conversion: CamelCase to snake_case
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', model_name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def has_write_operations(content: str) -> bool:
    """Check if content contains write operations."""
    for pattern in WRITE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_file(file_path: str) -> List[str]:
    """Check a single file for domain violations."""
    violations = []

    with open(file_path, 'r') as f:
        content = f.read()

    # Get this service's domain
    service_domain = get_service_domain(file_path)
    if service_domain == "Unknown":
        return []  # Can't determine domain, skip

    # Check if file has write operations
    if not has_write_operations(content):
        return []  # No writes, no violations possible

    # Extract imported models
    imported_models = extract_model_imports(content)

    for model in imported_models:
        table = model_to_table(model)
        table_owner = get_table_owner(table)

        if table_owner != "Unknown" and table_owner != service_domain:
            violations.append(
                f"DOMAIN-001 VIOLATION: {file_path}\n"
                f"  Service domain: {service_domain}\n"
                f"  Writes to model: {model} (table: {table})\n"
                f"  Table owner: {table_owner}\n"
                f"  → Cross-domain write detected!"
            )

    return violations


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app"

    if not backend_path.exists():
        print(f"Backend path not found: {backend_path}")
        sys.exit(1)

    # Directories to scan
    scan_dirs = ["services", "api", "engines"]

    all_violations = []
    files_checked = 0

    for scan_dir in scan_dirs:
        dir_path = backend_path / scan_dir
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            files_checked += 1
            violations = check_file(str(py_file))
            all_violations.extend(violations)

    # Report results
    print(f"DOMAIN-001: Domain Ownership Check")
    print(f"=" * 50)
    print(f"Files checked: {files_checked}")
    print(f"Violations found: {len(all_violations)}")
    print()

    if all_violations:
        print("VIOLATIONS:")
        print("-" * 50)
        for v in all_violations:
            print(v)
            print()
        sys.exit(1)
    else:
        print("✓ All domain boundaries respected")
        sys.exit(0)


if __name__ == "__main__":
    main()
