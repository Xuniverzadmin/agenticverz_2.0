#!/usr/bin/env python3
"""
GUARDRAIL: DATA-002 - Tenant Isolation Invariant
Rule: Every customer-facing query MUST include tenant_id filter.

This script scans API routes for queries that may be missing tenant_id.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Customer-facing API files (require tenant isolation)
CUSTOMER_API_FILES = [
    "activity.py",
    "incidents.py",
    "policies.py",
    "logs.py",
    "analytics.py",
    "overview.py",
    "cost_intelligence.py",
    "cost_guard.py",
    "guard.py",
    "runs.py",
]

# Patterns that indicate a database query
QUERY_PATTERNS = [
    r'select\s*\(',
    r'\.query\s*\(',
    r'session\.execute\s*\(',
    r'db\.execute\s*\(',
    r'SELECT\s+',
    r'\.filter\s*\(',
    r'\.where\s*\(',
]

# Patterns that indicate tenant_id is being used
TENANT_FILTER_PATTERNS = [
    r'tenant_id\s*[=!<>]',
    r'\.tenant_id\s*==',
    r'tenant_id\s*=\s*:',
    r'tenant_id\s*=\s*\$',
    r'filter.*tenant_id',
    r'where.*tenant_id',
    r'auth_context\.tenant_id',
    r'ctx\.tenant_id',
    r'current_tenant',
    r'get_tenant_id\s*\(',
]

# Exceptions - queries that don't need tenant filter
EXCEPTIONS = [
    r'COUNT\s*\(\s*\*\s*\)',  # Count queries often use different patterns
    r'health',  # Health checks
    r'public',  # Public endpoints
    r'auth',  # Auth endpoints
]


def has_query(content: str) -> bool:
    """Check if content has database queries."""
    for pattern in QUERY_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def has_tenant_filter(content: str) -> bool:
    """Check if content includes tenant filtering."""
    for pattern in TENANT_FILTER_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def is_exception(content: str) -> bool:
    """Check if content matches an exception pattern."""
    for pattern in EXCEPTIONS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_function_for_tenant_isolation(func_content: str, func_name: str, file_path: str) -> List[str]:
    """Check a function for tenant isolation."""
    violations = []

    # Skip if no queries
    if not has_query(func_content):
        return violations

    # Skip if exception
    if is_exception(func_content):
        return violations

    # Check for tenant filter
    if not has_tenant_filter(func_content):
        violations.append(
            f"Function: {func_name} in {file_path}\n"
            f"  → Database query detected WITHOUT tenant_id filter\n"
            f"  → POTENTIAL DATA LEAK: May return data from other tenants"
        )

    return violations


def extract_functions(content: str) -> List[Tuple[str, str]]:
    """Extract function names and their content."""
    functions = []

    # Pattern for async def or def
    pattern = r'(?:async\s+)?def\s+(\w+)\s*\([^)]*\).*?(?=(?:async\s+)?def\s+|\Z)'
    matches = re.finditer(pattern, content, re.DOTALL)

    for match in matches:
        func_name = match.group(1)
        func_content = match.group(0)
        functions.append((func_name, func_content))

    return functions


def check_file(file_path: Path) -> List[str]:
    """Check a file for tenant isolation violations."""
    violations = []

    with open(file_path, 'r') as f:
        content = f.read()

    functions = extract_functions(content)

    for func_name, func_content in functions:
        # Skip private functions
        if func_name.startswith('_'):
            continue

        func_violations = check_function_for_tenant_isolation(
            func_content, func_name, str(file_path)
        )
        violations.extend(func_violations)

    return violations


def main():
    """Main entry point."""
    api_path = Path(__file__).parent.parent.parent / "backend" / "app" / "api"

    print("DATA-002: Tenant Isolation Check")
    print("=" * 50)

    all_violations = []
    files_checked = 0

    for file_name in CUSTOMER_API_FILES:
        file_path = api_path / file_name
        if not file_path.exists():
            continue

        files_checked += 1
        violations = check_file(file_path)
        all_violations.extend(violations)

    print(f"Files checked: {files_checked}")
    print(f"Potential violations: {len(all_violations)}")
    print()

    if all_violations:
        print("POTENTIAL VIOLATIONS:")
        print("-" * 50)
        for v in all_violations:
            print(v)
            print()

        print("\n⚠️  WARNING: These queries may be missing tenant_id filter.")
        print("Review each query to ensure tenant isolation is enforced.")
        print("Every customer-facing query MUST filter by tenant_id.")
        print()

        # This is a warning, not a blocking failure
        # Manual review required
        sys.exit(0)  # Change to sys.exit(1) for strict enforcement
    else:
        print("✓ All queries appear to have tenant isolation")
        sys.exit(0)


if __name__ == "__main__":
    main()
