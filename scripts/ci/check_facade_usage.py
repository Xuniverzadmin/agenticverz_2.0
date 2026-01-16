#!/usr/bin/env python3
"""
GUARDRAIL: API-001 - Domain Facade Required
Rule: External code must use domain facades, not direct service imports.

This script validates that code outside a domain uses facades.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set

# Domain services that MUST be accessed via facade
DOMAIN_SERVICES = {
    'Activity': {
        'services': [
            'run_service',
            'activity_service',
            'execution_service',
            'runner_service',
        ],
        'facade': 'activity_facade',
        'allowed_direct_callers': ['activity.py', 'runs.py'],
    },
    'Incidents': {
        'services': [
            'incident_service',
            'incident_engine',
        ],
        'facade': 'incident_facade',
        'allowed_direct_callers': ['incidents.py', 'incident_engine.py'],
    },
    'Policies': {
        'services': [
            'policy_service',
            'policy_engine',
            'policy_proposal_engine',
        ],
        'facade': 'policy_facade',
        'allowed_direct_callers': ['policies.py', 'policy_engine.py'],
    },
    'Analytics': {
        'services': [
            'cost_service',
            'analytics_service',
            'cost_recording_service',
            'anomaly_detector',
        ],
        'facade': 'analytics_facade',
        'allowed_direct_callers': ['analytics.py', 'cost.py', 'cost_intelligence.py'],
    },
    'Limits': {
        'services': [
            'limits_service',
            'limit_service',
            'quota_service',
        ],
        'facade': 'limits_facade',
        'allowed_direct_callers': ['limits.py', 'policy.py'],
    },
}


def find_service_imports(file_path: Path) -> List[tuple]:
    """Find all service imports in a file."""
    imports = []

    with open(file_path, 'r') as f:
        content = f.read()

    # Find from imports
    pattern = r'from\s+(?:app\.)?(?:services\.)?(\w+)\s+import\s+([^#\n]+)'
    matches = re.finditer(pattern, content, re.IGNORECASE)

    for match in matches:
        module = match.group(1)
        imported = match.group(2).strip()
        imports.append((module, imported, match.start()))

    # Find direct imports
    pattern = r'import\s+(?:app\.)?(?:services\.)?(\w+)'
    matches = re.finditer(pattern, content, re.IGNORECASE)

    for match in matches:
        module = match.group(1)
        imports.append((module, module, match.start()))

    return imports


def check_file(file_path: Path, base_path: Path) -> List[str]:
    """Check a file for direct service imports that should use facade."""
    violations = []

    file_name = file_path.name
    relative_path = str(file_path.relative_to(base_path))

    imports = find_service_imports(file_path)

    for module, imported, _ in imports:
        # Check each domain
        for domain, config in DOMAIN_SERVICES.items():
            services = config['services']
            facade = config['facade']
            allowed = config['allowed_direct_callers']

            # Check if this is a service import
            for service in services:
                if service.lower() in module.lower() or service.lower() in imported.lower():
                    # Check if caller is allowed direct access
                    if file_name not in allowed:
                        violations.append(
                            f"File: {relative_path}\n"
                            f"  Import: {module}.{imported}\n"
                            f"  Domain: {domain}\n"
                            f"  → DIRECT service import from outside domain\n"
                            f"  → Must use {facade} instead\n"
                            f"  → Only {allowed} may import directly"
                        )

    return violations


def main():
    """Main entry point."""
    base_path = Path(__file__).parent.parent.parent
    app_path = base_path / "backend" / "app"

    print("API-001: Domain Facade Usage Check")
    print("=" * 50)

    all_violations = []
    files_checked = 0

    # Check API routes
    api_path = app_path / "api"
    if api_path.exists():
        for py_file in api_path.glob("*.py"):
            files_checked += 1
            violations = check_file(py_file, base_path)
            all_violations.extend(violations)

    # Check services (for cross-domain calls)
    services_path = app_path / "services"
    if services_path.exists():
        for py_file in services_path.glob("*.py"):
            files_checked += 1
            violations = check_file(py_file, base_path)
            all_violations.extend(violations)

    # Check worker
    worker_path = app_path / "worker"
    if worker_path.exists():
        for py_file in worker_path.glob("*.py"):
            files_checked += 1
            violations = check_file(py_file, base_path)
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

        print("\nDomain services must be accessed via facades!")
        print("Direct imports:")
        print("  - Bypass authorization checks")
        print("  - Skip audit logging")
        print("  - Break domain encapsulation")
        print()
        print("Use the domain facade for external access.")
        sys.exit(1)
    else:
        print("✓ All external code uses domain facades")
        sys.exit(0)


if __name__ == "__main__":
    main()
