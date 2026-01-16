#!/usr/bin/env python3
"""
GUARDRAIL: LIMITS-001 - Single Source of Truth
Rule: There is ONE limits system. No parallel limit tables.

This script ensures no parallel limit/quota/budget tables are created.
"""

import re
import sys
from pathlib import Path
from typing import List, Set

# Allowed limit-related tables
ALLOWED_LIMIT_TABLES: Set[str] = {
    "limits",
    "limit_breaches",
    "limit_integrity",
}

# Forbidden table name patterns (would indicate parallel systems)
FORBIDDEN_PATTERNS: List[str] = [
    r'cost_budgets',      # Should be migrated to limits
    r'tenant_quotas',     # Should be in limits
    r'rate_limits',       # Should be in limits
    r'usage_limits',      # Should be in limits
    r'budget_limits',     # Should be in limits
    r'quota_limits',      # Should be in limits
    r'spending_limits',   # Should be in limits
    r'\w+_budget\b',      # Any *_budget table
    r'\w+_quota\b',       # Any *_quota table
]


def find_tables_in_migrations(migrations_path: Path) -> List[str]:
    """Find all table names defined in migrations."""
    tables = []

    for migration_file in migrations_path.glob("*.py"):
        with open(migration_file, 'r') as f:
            content = f.read()

        # Find CREATE TABLE statements
        create_patterns = [
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["\']?(\w+)["\']?',
            r'op\.create_table\s*\(\s*["\'](\w+)["\']',
            r'sa\.Table\s*\(\s*["\'](\w+)["\']',
        ]

        for pattern in create_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                tables.append(match.group(1))

    return tables


def find_tables_in_models(models_path: Path) -> List[str]:
    """Find all table names defined in models."""
    tables = []

    for model_file in models_path.glob("*.py"):
        with open(model_file, 'r') as f:
            content = f.read()

        # Find __tablename__ definitions
        pattern = r'__tablename__\s*=\s*["\'](\w+)["\']'
        for match in re.finditer(pattern, content):
            tables.append(match.group(1))

        # Find table= in SQLModel
        pattern = r'table\s*=\s*True.*class\s+(\w+)'
        for match in re.finditer(pattern, content, re.DOTALL):
            # Convert class name to snake_case for table name
            class_name = match.group(1)
            table_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', class_name)
            table_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', table_name).lower()
            tables.append(table_name)

    return tables


def check_for_parallel_limits(tables: List[str]) -> List[str]:
    """Check if any tables indicate parallel limit systems."""
    violations = []

    for table in tables:
        table_lower = table.lower()

        # Skip allowed tables
        if table_lower in ALLOWED_LIMIT_TABLES:
            continue

        # Check forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            if re.match(pattern, table_lower):
                violations.append(
                    f"Table: {table}\n"
                    f"  Pattern: {pattern}\n"
                    f"  → Parallel limit table detected!\n"
                    f"  → Use unified 'limits' table instead"
                )

    return violations


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend"
    migrations_path = backend_path / "alembic" / "versions"
    models_path = backend_path / "app" / "models"

    print("LIMITS-001: Single Source of Truth Check")
    print("=" * 50)

    all_tables = []

    # Collect tables from migrations
    if migrations_path.exists():
        all_tables.extend(find_tables_in_migrations(migrations_path))

    # Collect tables from models
    if models_path.exists():
        all_tables.extend(find_tables_in_models(models_path))

    # Deduplicate
    all_tables = list(set(all_tables))

    print(f"Tables found: {len(all_tables)}")

    # Check for violations
    violations = check_for_parallel_limits(all_tables)

    # Report limit-related tables
    limit_tables = [t for t in all_tables if any(
        kw in t.lower() for kw in ['limit', 'budget', 'quota']
    )]

    print(f"\nLimit-related tables:")
    for t in sorted(limit_tables):
        status = "✓" if t.lower() in ALLOWED_LIMIT_TABLES else "✗"
        print(f"  {status} {t}")

    if violations:
        print("\n" + "=" * 50)
        print("VIOLATIONS:")
        print("-" * 50)
        for v in violations:
            print(v)
            print()

        print("\nThere must be ONE limits system.")
        print("All limit types should use the unified 'limits' table:")
        print("  - Cost limits")
        print("  - Token limits")
        print("  - Rate limits")
        print("  - Run limits")
        print()
        print("Migrate parallel tables to the unified system.")
        sys.exit(1)
    else:
        print("\n✓ No parallel limit tables detected")
        sys.exit(0)


if __name__ == "__main__":
    main()
