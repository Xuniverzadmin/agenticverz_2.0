#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI | preflight
#   Execution: sync
# Role: Enforce deprecation of generic /incidents endpoint
# Reference: INCIDENTS_DOMAIN_MIGRATION_PLAN.md Phase 5
"""
Incidents Domain Deprecation Guard

This script enforces the deprecation of the generic /incidents endpoint.
It fails CI if:
1. Any frontend file calls fetchIncidents()
2. Any frontend file references /api/v1/incidents without a topic suffix
3. Any capability file binds to /incidents (without topic suffix)

Exit codes:
- 0: No violations found
- 1: Violations found
- 2: Script error

Usage:
    python scripts/preflight/check_incidents_deprecation.py
    python scripts/preflight/check_incidents_deprecation.py --verbose
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).parent.parent.parent

# Paths to check
FRONTEND_SRC = REPO_ROOT / "website" / "app-shell" / "src"
CAPABILITY_REGISTRY = REPO_ROOT / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"
INTENT_LEDGER = REPO_ROOT / "design" / "l2_1" / "INTENT_LEDGER.md"

# Patterns that indicate deprecated usage
DEPRECATED_PATTERNS = [
    # Frontend: fetchIncidents() call (but not the function definition)
    (r'fetchIncidents\s*\(', 'fetchIncidents() call'),
    # Frontend: direct /api/v1/incidents without topic suffix
    (r'["\']\/api\/v1\/incidents["\']', 'Direct /api/v1/incidents reference'),
    (r'["\']\/api\/v1\/incidents\?', '/api/v1/incidents with query params'),
]

# Allowed patterns (topic-scoped endpoints and valid suffixes)
ALLOWED_PATTERNS = [
    r'/api/v1/incidents/active',
    r'/api/v1/incidents/resolved',
    r'/api/v1/incidents/historical',
    r'/api/v1/incidents/metrics',
    r'/api/v1/incidents/summary',  # HIL v1 endpoint
    r'/api/v1/incidents/by-run/',
    r'/api/v1/incidents/\{',  # Parameterized routes like /{id}
    r'/api/v1/incidents/cost-impact',  # Valid endpoint (not the deprecated generic one)
    r'/api/v1/incidents/patterns',  # Valid endpoint
    r'/api/v1/incidents/recurring',  # Valid endpoint
    r'/api/v1/incidents/learnings',  # Valid endpoint
]

# Files to exclude (definitions, not usages)
EXCLUDED_FILES = [
    'incidents.ts',  # Contains function definitions (allowed to define fetchIncidents)
    'check_incidents_deprecation.py',  # This script
]


def is_allowed_reference(line: str) -> bool:
    """Check if the line contains an allowed topic-scoped endpoint reference."""
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, line):
            return True
    return False


def check_frontend_files() -> List[Tuple[str, int, str, str]]:
    """Check frontend files for deprecated incident endpoint usage."""
    violations = []

    if not FRONTEND_SRC.exists():
        return violations

    for file_path in FRONTEND_SRC.rglob("*.ts"):
        if file_path.name in EXCLUDED_FILES:
            continue

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                # Skip if line contains an allowed pattern
                if is_allowed_reference(line):
                    continue

                # Check for deprecated patterns
                for pattern, description in DEPRECATED_PATTERNS:
                    if re.search(pattern, line):
                        # Double-check it's not in a comment
                        stripped = line.strip()
                        if stripped.startswith('//') or stripped.startswith('*'):
                            continue

                        rel_path = file_path.relative_to(REPO_ROOT)
                        violations.append((str(rel_path), line_num, description, line.strip()[:80]))

        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    # Also check TSX files
    for file_path in FRONTEND_SRC.rglob("*.tsx"):
        if file_path.name in EXCLUDED_FILES:
            continue

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                if is_allowed_reference(line):
                    continue

                for pattern, description in DEPRECATED_PATTERNS:
                    if re.search(pattern, line):
                        stripped = line.strip()
                        if stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('{/*'):
                            continue

                        rel_path = file_path.relative_to(REPO_ROOT)
                        violations.append((str(rel_path), line_num, description, line.strip()[:80]))

        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return violations


def check_capability_registry() -> List[Tuple[str, int, str, str]]:
    """Check capability registry for non-deprecated capabilities binding to /incidents."""
    violations = []

    if not CAPABILITY_REGISTRY.exists():
        return violations

    for file_path in CAPABILITY_REGISTRY.glob("AURORA_L2_CAPABILITY_incidents.*.yaml"):
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Check if this is a DEPRECATED capability (those are allowed to reference /incidents)
            is_deprecated = 'status: DEPRECATED' in content

            if is_deprecated:
                continue  # Skip deprecated capabilities

            for line_num, line in enumerate(lines, 1):
                # Check for binding to generic /incidents
                if 'observed_endpoint:' in line or 'endpoint:' in line:
                    if '/api/v1/incidents' in line:
                        # Check if it's a topic-scoped endpoint
                        if not any(allowed in line for allowed in ['/active', '/resolved', '/historical', '/metrics', '/summary', '/by-run', '/cost-impact', '/patterns', '/recurring', '/learnings']):
                            rel_path = file_path.relative_to(REPO_ROOT)
                            violations.append((str(rel_path), line_num, 'Capability binds to deprecated /incidents', line.strip()[:80]))

        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return violations


def main():
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    print("=" * 70)
    print("INCIDENTS DOMAIN DEPRECATION GUARD")
    print("Reference: INCIDENTS_DOMAIN_MIGRATION_PLAN.md Phase 5")
    print("=" * 70)
    print()

    all_violations = []

    # Check frontend
    print("Checking frontend files...")
    frontend_violations = check_frontend_files()
    all_violations.extend(frontend_violations)
    print(f"  Found {len(frontend_violations)} violation(s)")

    # Check capability registry
    print("Checking capability registry...")
    capability_violations = check_capability_registry()
    all_violations.extend(capability_violations)
    print(f"  Found {len(capability_violations)} violation(s)")

    print()

    if all_violations:
        print("=" * 70)
        print("VIOLATIONS FOUND")
        print("=" * 70)
        print()
        print("The generic /api/v1/incidents endpoint is DEPRECATED.")
        print("Use topic-scoped endpoints instead:")
        print("  - /api/v1/incidents/active")
        print("  - /api/v1/incidents/resolved")
        print("  - /api/v1/incidents/historical")
        print()

        for file_path, line_num, description, line in all_violations:
            print(f"  {file_path}:{line_num}")
            print(f"    {description}")
            if verbose:
                print(f"    > {line}")
            print()

        print(f"Total violations: {len(all_violations)}")
        print()
        print("Fix: Update code to use topic-scoped endpoints.")
        print("Reference: docs/architecture/incidents/INCIDENTS_DOMAIN_MIGRATION_PLAN.md")
        return 1

    print("=" * 70)
    print("NO VIOLATIONS FOUND")
    print("=" * 70)
    print()
    print("All incident endpoint usages are correctly topic-scoped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
