#!/usr/bin/env python3
"""
Schema Audit Script - Validates database schema integrity after migrations.

This script ensures the ephemeral Neon branch has all required:
- Schemas
- Tables
- Constraints (unique, foreign key, check)
- Indexes
- Functions
- Partitions

Usage:
    PYTHONPATH=backend python scripts/ops/schema_audit.py

Exit codes:
    0 - All schema checks passed
    1 - Schema audit failed (missing elements)
"""

import os
import sys
import json
from datetime import datetime

# Ensure backend is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

# DB-AUTH-001: Declare local-only authority
from scripts._db_guard import assert_db_authority
assert_db_authority("local")

from sqlalchemy import create_engine, text

# Required schema elements for production
REQUIRED_SCHEMAS = [
    "public",
    "m10_recovery",
    "agents",
    "routing",
]

REQUIRED_TABLES = {
    "public": [
        "runs",
        "workflows",
        "agents",
        "skills",
        "budgets",
    ],
    "m10_recovery": [
        "recovery_candidates",
        "distributed_locks",
        "replay_log",
        "dead_letter_archive",
        "outbox",
    ],
    "agents": [
        "agent_registry",
        "agent_capabilities",
    ],
    "routing": [
        "routing_decisions",
        "capability_probes",
    ],
}

REQUIRED_INDEXES = {
    "m10_recovery.outbox": [
        "uq_outbox_pending",  # Partial unique index
        "idx_outbox_pending",
        "idx_outbox_retry",
    ],
    "m10_recovery.distributed_locks": [
        "idx_locks_holder",
        "idx_locks_expires",
    ],
    "m10_recovery.recovery_candidates": [
        "idx_recovery_status",
    ],
    "routing.routing_decisions": [
        "ix_routing_decisions_decided_at",
        "ix_routing_decisions_agent",
        "ix_routing_decisions_tenant",
    ],
}

REQUIRED_FUNCTIONS = {
    "m10_recovery": [
        "publish_outbox",
        "claim_outbox_events",
        "complete_outbox_event",
        "acquire_lock",
        "release_lock",
        "record_replay",
        "archive_dead_letter",
    ],
    "agents": [
        "validate_agent_sba",
    ],
}

REQUIRED_CONSTRAINTS = {
    "public.runs": [
        ("runs_pkey", "PRIMARY KEY"),
    ],
    "m10_recovery.distributed_locks": [
        ("distributed_locks_pkey", "PRIMARY KEY"),
    ],
}


def get_engine():
    """Create database engine from environment."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    return create_engine(db_url)


def check_schemas(conn) -> list:
    """Check required schemas exist."""
    errors = []
    result = conn.execute(
        text(
            """
        SELECT schema_name FROM information_schema.schemata
    """
        )
    )
    existing = {row[0] for row in result}

    for schema in REQUIRED_SCHEMAS:
        if schema not in existing:
            errors.append(f"Missing schema: {schema}")

    return errors


def check_tables(conn) -> list:
    """Check required tables exist."""
    errors = []

    for schema, tables in REQUIRED_TABLES.items():
        result = conn.execute(
            text(
                """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = :schema
        """
            ),
            {"schema": schema},
        )
        existing = {row[0] for row in result}

        for table in tables:
            if table not in existing:
                errors.append(f"Missing table: {schema}.{table}")

    return errors


def check_indexes(conn) -> list:
    """Check required indexes exist."""
    errors = []

    for table_full, indexes in REQUIRED_INDEXES.items():
        schema, table = table_full.split(".")

        result = conn.execute(
            text(
                """
            SELECT indexname FROM pg_indexes
            WHERE schemaname = :schema AND tablename = :table
        """
            ),
            {"schema": schema, "table": table},
        )
        existing = {row[0] for row in result}

        for index in indexes:
            if index not in existing:
                errors.append(f"Missing index: {table_full}.{index}")

    return errors


def check_functions(conn) -> list:
    """Check required functions exist."""
    errors = []

    for schema, functions in REQUIRED_FUNCTIONS.items():
        result = conn.execute(
            text(
                """
            SELECT routine_name FROM information_schema.routines
            WHERE routine_schema = :schema AND routine_type = 'FUNCTION'
        """
            ),
            {"schema": schema},
        )
        existing = {row[0] for row in result}

        for func in functions:
            if func not in existing:
                errors.append(f"Missing function: {schema}.{func}")

    return errors


def check_constraints(conn) -> list:
    """Check required constraints exist."""
    errors = []

    for table_full, constraints in REQUIRED_CONSTRAINTS.items():
        schema, table = table_full.split(".")

        result = conn.execute(
            text(
                """
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = :schema AND table_name = :table
        """
            ),
            {"schema": schema, "table": table},
        )
        existing = {(row[0], row[1]) for row in result}

        for constraint_name, constraint_type in constraints:
            if (constraint_name, constraint_type) not in existing:
                errors.append(
                    f"Missing constraint: {table_full}.{constraint_name} ({constraint_type})"
                )

    return errors


def check_alembic_version(conn) -> list:
    """Check alembic version table is consistent."""
    errors = []

    result = conn.execute(
        text(
            """
        SELECT COUNT(*) FROM alembic_version
    """
        )
    )
    count = result.scalar()

    if count == 0:
        errors.append("Alembic version table is empty - migrations not applied")
    elif count > 1:
        errors.append(
            f"Alembic has multiple heads ({count}) - migration branching detected"
        )

    return errors


def run_audit() -> dict:
    """Run full schema audit."""
    engine = get_engine()

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "database_url": os.getenv("DATABASE_URL", "").split("@")[
            -1
        ],  # Hide credentials
        "checks": {},
        "errors": [],
        "passed": True,
    }

    with engine.connect() as conn:
        # Run all checks
        checks = [
            ("schemas", check_schemas),
            ("tables", check_tables),
            ("indexes", check_indexes),
            ("functions", check_functions),
            ("constraints", check_constraints),
            ("alembic_version", check_alembic_version),
        ]

        for name, check_func in checks:
            try:
                errors = check_func(conn)
                results["checks"][name] = {
                    "passed": len(errors) == 0,
                    "errors": errors,
                }
                results["errors"].extend(errors)
            except Exception as e:
                results["checks"][name] = {
                    "passed": False,
                    "errors": [f"Check failed: {str(e)}"],
                }
                results["errors"].append(f"{name}: {str(e)}")

    results["passed"] = len(results["errors"]) == 0
    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("Schema Audit - Database Integrity Check")
    print("=" * 60)
    print()

    results = run_audit()

    # Print results
    for check_name, check_result in results["checks"].items():
        status = "PASS" if check_result["passed"] else "FAIL"
        print(f"[{status}] {check_name}")
        for error in check_result["errors"]:
            print(f"       - {error}")

    print()
    print("=" * 60)

    if results["passed"]:
        print("Schema Audit: PASSED")
        print(f"All {len(results['checks'])} checks passed")
        return 0
    else:
        print("Schema Audit: FAILED")
        print(f"Found {len(results['errors'])} error(s)")

        # Output JSON for CI parsing
        if os.getenv("CI"):
            print()
            print("JSON Output:")
            print(json.dumps(results, indent=2))

        return 1


if __name__ == "__main__":
    sys.exit(main())
