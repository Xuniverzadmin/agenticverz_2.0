#!/usr/bin/env python3
"""
GUARDRAIL: DATA-001 - Foreign Key Enforcement
Rule: All cross-domain references MUST use foreign keys.

This script validates that required cross-domain FKs exist in migrations.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Required cross-domain foreign keys
# Format: (from_table, from_column, to_table, required)
REQUIRED_FKS: List[Tuple[str, str, str, bool]] = [
    # Incidents ↔ Activity
    ("incidents", "source_run_id", "runs", True),

    # Analytics ↔ Incidents
    ("cost_records", "incident_id", "incidents", True),
    ("cost_anomalies", "incident_id", "incidents", True),

    # Analytics ↔ Connectivity
    ("cost_records", "api_key_id", "api_keys", True),

    # Logs ↔ Activity
    ("aos_traces", "run_id", "runs", True),
    ("system_records", "run_id", "runs", False),  # Recommended

    # Logs ↔ Incidents
    ("aos_traces", "incident_id", "incidents", True),
    ("llm_run_records", "incident_id", "incidents", False),  # Recommended
    ("system_records", "incident_id", "incidents", False),  # Recommended

    # Tenant isolation (all tables)
    ("runs", "tenant_id", "tenants", True),
    ("incidents", "tenant_id", "tenants", True),
    ("policy_rules", "tenant_id", "tenants", True),
    ("cost_records", "tenant_id", "tenants", True),
    ("api_keys", "tenant_id", "tenants", True),
]


def find_fk_in_migrations(migrations_path: Path, from_table: str, from_column: str, to_table: str) -> bool:
    """Search migration files for a FK definition."""

    # Patterns that indicate FK exists
    fk_patterns = [
        # SQLAlchemy Column with ForeignKey
        rf'ForeignKey\s*\(\s*["\']?{to_table}\.id["\']?\s*\)',
        # Column definition with FK
        rf'{from_column}.*ForeignKey.*{to_table}',
        # Alembic add_foreign_key_constraint
        rf'add_foreign_key_constraint.*{from_table}.*{to_table}',
        # Raw SQL ALTER TABLE ADD CONSTRAINT
        rf'ALTER\s+TABLE\s+{from_table}.*FOREIGN\s+KEY.*{to_table}',
        rf'REFERENCES\s+{to_table}',
    ]

    for migration_file in migrations_path.glob("*.py"):
        with open(migration_file, 'r') as f:
            content = f.read()

        for pattern in fk_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Additional check: ensure it's for the right column
                if from_column in content:
                    return True

    return False


def find_fk_in_models(models_path: Path, from_table: str, from_column: str, to_table: str) -> bool:
    """Search model files for FK definition."""

    for model_file in models_path.glob("*.py"):
        with open(model_file, 'r') as f:
            content = f.read()

        # Check for ForeignKey annotation
        pattern = rf'{from_column}.*ForeignKey\s*\(\s*["\']?{to_table}\.id["\']?\s*\)'
        if re.search(pattern, content, re.IGNORECASE):
            return True

        # Check for foreign_key parameter in Field
        pattern = rf'{from_column}.*foreign_key\s*=\s*["\']?{to_table}\.id["\']?'
        if re.search(pattern, content, re.IGNORECASE):
            return True

    return False


def main():
    """Main entry point."""
    base_path = Path(__file__).parent.parent.parent / "backend"
    migrations_path = base_path / "alembic" / "versions"
    models_path = base_path / "app" / "models"

    print("DATA-001: Foreign Key Enforcement Check")
    print("=" * 50)

    missing_required = []
    missing_recommended = []
    found = []

    for from_table, from_column, to_table, required in REQUIRED_FKS:
        fk_exists = False

        # Check migrations
        if migrations_path.exists():
            if find_fk_in_migrations(migrations_path, from_table, from_column, to_table):
                fk_exists = True

        # Check models
        if models_path.exists() and not fk_exists:
            if find_fk_in_models(models_path, from_table, from_column, to_table):
                fk_exists = True

        fk_name = f"{from_table}.{from_column} → {to_table}"

        if fk_exists:
            found.append(fk_name)
        elif required:
            missing_required.append(fk_name)
        else:
            missing_recommended.append(fk_name)

    # Report results
    print(f"\nForeign Keys Found: {len(found)}")
    for fk in found:
        print(f"  ✓ {fk}")

    print(f"\nMissing Required FKs: {len(missing_required)}")
    for fk in missing_required:
        print(f"  ✗ {fk}")

    print(f"\nMissing Recommended FKs: {len(missing_recommended)}")
    for fk in missing_recommended:
        print(f"  ⚠ {fk}")

    print()

    if missing_required:
        print("=" * 50)
        print("FAILURE: Required foreign keys are missing!")
        print("Cross-domain references MUST use foreign keys.")
        print()
        print("To fix, create a migration that adds:")
        for fk in missing_required:
            parts = fk.split(" → ")
            table_col = parts[0].split(".")
            print(f"  ALTER TABLE {table_col[0]} ADD FOREIGN KEY ({table_col[1]}) REFERENCES {parts[1]}(id);")
        sys.exit(1)
    else:
        print("✓ All required foreign keys present")
        sys.exit(0)


if __name__ == "__main__":
    main()
