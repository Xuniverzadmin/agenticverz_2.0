#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CLI invocation
#   Execution: sync
# Role: SDSR Synthetic Data Injection Script (Keystone)
# Reference: PIN-370 (Scenario-Driven System Realization)

"""
SDSR inject_synthetic.py - Scenario Realization Engine

PURPOSE:
    Materializes YAML scenario specifications into real database state.
    This is the KEYSTONE that enables SDSR pipeline validation.

FOUR NON-NEGOTIABLE RULES (PIN-370):
    1. NO INTELLIGENCE
       - Purely mechanical. No inference, no guessing, no helpful defaults.
       - Incomplete spec → fail loudly.
       - If a field is missing, STOP.

    2. WRITES ONLY WHAT REAL FLOWS WRITE
       - Synthetic ≠ fake. Use same data structures as real flows.
       - Don't invent fields or skip required fields.

    3. EVERY ROW TRACEABLE
       - is_synthetic=true on every write. No exceptions.
       - synthetic_scenario_id set on every row.

    4. ONE SCENARIO = ONE TRANSACTION
       - Atomic, repeatable, idempotent when cleaned.
       - If anything fails, nothing is written.

WHAT THIS IS:
    - A scenario materializer
    - A DB + capability seeder
    - A realization engine

WHAT THIS IS NOT:
    - NOT a test runner
    - NOT a UI helper
    - NOT a mock generator
    - NOT a data faker

USAGE:
    python inject_synthetic.py --scenario scenarios/ONBOARDING-001.yaml
    python inject_synthetic.py --scenario scenarios/ACTIVITY-RETRY-001.yaml --cleanup
    python inject_synthetic.py --scenario scenarios/ACTIVITY-RETRY-001.yaml --dry-run
"""

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sdsr.inject")


# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================
# These define the required fields for each table write.
# If a scenario spec is missing a required field, we fail loudly.

REQUIRED_FIELDS = {
    "tenants": ["id", "name", "slug"],
    "api_keys": ["id", "tenant_id", "name", "key_prefix", "key_hash"],
    "agents": ["id", "name"],
    "runs": ["id", "agent_id", "goal"],
    "worker_runs": ["id", "tenant_id", "worker_id", "task"],
}

OPTIONAL_FIELDS = {
    "tenants": ["plan", "status", "max_workers", "max_runs_per_day"],
    "api_keys": ["status", "permissions_json", "allowed_workers_json"],
    "agents": ["description", "status", "tenant_id", "owner_id"],
    "runs": ["status", "tenant_id", "parent_run_id", "priority", "max_attempts"],
    "worker_runs": ["status", "input_json", "api_key_id", "user_id", "parent_run_id"],
}


# =============================================================================
# VALIDATION
# =============================================================================


class ScenarioValidationError(Exception):
    """Raised when scenario spec is incomplete or invalid."""

    pass


def validate_scenario_spec(spec: dict) -> None:
    """
    Validate scenario specification has all required fields.

    Rule 1: NO INTELLIGENCE - fail loudly on missing fields.
    """
    # Top-level required fields
    if "scenario_id" not in spec:
        raise ScenarioValidationError("Missing required field: scenario_id")

    if "domain" not in spec:
        raise ScenarioValidationError("Missing required field: domain")

    if "backend" not in spec:
        raise ScenarioValidationError("Missing required field: backend")

    backend = spec["backend"]
    if "tables" not in backend:
        raise ScenarioValidationError("Missing required field: backend.tables")

    if "writes" not in backend:
        raise ScenarioValidationError("Missing required field: backend.writes")

    # Validate each write has required fields for its table
    for write in backend["writes"]:
        for operation, data in write.items():
            # Extract table name from operation (e.g., "create_tenant" -> "tenants")
            table = _operation_to_table(operation)
            if table not in REQUIRED_FIELDS:
                raise ScenarioValidationError(f"Unknown table for operation: {operation}")

            required = REQUIRED_FIELDS[table]
            for field in required:
                if field not in data:
                    raise ScenarioValidationError(
                        f"Missing required field '{field}' in operation '{operation}'. "
                        f"Required fields for {table}: {required}"
                    )


def _operation_to_table(operation: str) -> str:
    """Map operation name to table name."""
    mapping = {
        "create_tenant": "tenants",
        "create_api_key": "api_keys",
        "create_agent": "agents",
        "create_run": "runs",
        "create_worker_run": "worker_runs",
    }
    if operation not in mapping:
        raise ScenarioValidationError(f"Unknown operation: {operation}")
    return mapping[operation]


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================


def get_db_connection():
    """
    Get database connection using DATABASE_URL.

    Per database_contract.yaml: Scripts use psycopg2 + explicit DATABASE_URL.
    """
    import psycopg2

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    return psycopg2.connect(database_url)


def inject_scenario(spec: dict, dry_run: bool = False) -> dict:
    """
    Inject a scenario's writes into the database.

    Rule 3: Every row traceable - is_synthetic=true, synthetic_scenario_id set.
    Rule 4: One scenario = one transaction.

    Returns:
        dict with summary of writes performed
    """
    scenario_id = spec["scenario_id"]
    writes = spec["backend"]["writes"]

    results = {
        "scenario_id": scenario_id,
        "rows_written": 0,
        "tables_touched": set(),
        "operations": [],
    }

    if dry_run:
        logger.info(f"DRY RUN - Scenario: {scenario_id}")
        for write in writes:
            for operation, data in write.items():
                table = _operation_to_table(operation)
                results["operations"].append({
                    "operation": operation,
                    "table": table,
                    "data": data,
                })
                results["tables_touched"].add(table)
                logger.info(f"  [DRY] Would {operation}: {data.get('id', 'auto')}")
        results["tables_touched"] = list(results["tables_touched"])
        return results

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for write in writes:
            for operation, data in write.items():
                table = _operation_to_table(operation)

                # Rule 3: Inject synthetic markers
                data["is_synthetic"] = True
                data["synthetic_scenario_id"] = scenario_id

                # Generate ID if not provided
                if "id" not in data or data["id"] is None:
                    data["id"] = str(uuid.uuid4())

                # Handle timestamps
                now = datetime.utcnow()
                if "created_at" not in data:
                    data["created_at"] = now
                # Only add updated_at for tables that have it
                tables_with_updated_at = ["tenants", "agents", "worker_runs"]
                if table in tables_with_updated_at and "updated_at" not in data:
                    data["updated_at"] = now

                # Build and execute INSERT
                columns = list(data.keys())
                placeholders = ["%s"] * len(columns)
                values = [data[col] for col in columns]

                sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

                logger.info(f"Executing: {operation} on {table} (id={data['id']})")
                cursor.execute(sql, values)

                results["operations"].append({
                    "operation": operation,
                    "table": table,
                    "id": data["id"],
                })
                results["tables_touched"].add(table)
                results["rows_written"] += 1

        # Rule 4: Commit as single transaction
        conn.commit()
        logger.info(f"Committed {results['rows_written']} rows for scenario {scenario_id}")

    except Exception as e:
        conn.rollback()
        logger.error(f"ROLLBACK - Error during injection: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

    results["tables_touched"] = list(results["tables_touched"])
    return results


def cleanup_scenario(scenario_id: str, dry_run: bool = False) -> dict:
    """
    Clean up all synthetic data for a scenario.

    Uses is_synthetic + synthetic_scenario_id for targeted deletion.
    """
    tables = ["runs", "worker_runs", "agents", "api_keys", "tenants"]

    results = {
        "scenario_id": scenario_id,
        "rows_deleted": 0,
        "tables_cleaned": [],
    }

    if dry_run:
        logger.info(f"DRY RUN - Would cleanup scenario: {scenario_id}")
        for table in tables:
            logger.info(f"  [DRY] Would DELETE FROM {table} WHERE is_synthetic=true AND synthetic_scenario_id='{scenario_id}'")
        return results

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete in reverse dependency order
        for table in tables:
            sql = f"""
                DELETE FROM {table}
                WHERE is_synthetic = true
                AND synthetic_scenario_id = %s
            """
            cursor.execute(sql, (scenario_id,))
            deleted = cursor.rowcount
            if deleted > 0:
                results["tables_cleaned"].append(table)
                results["rows_deleted"] += deleted
                logger.info(f"Deleted {deleted} rows from {table}")

        conn.commit()
        logger.info(f"Cleanup complete: {results['rows_deleted']} rows deleted for scenario {scenario_id}")

    except Exception as e:
        conn.rollback()
        logger.error(f"ROLLBACK - Error during cleanup: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

    return results


# =============================================================================
# SCENARIO LOADING
# =============================================================================


def load_scenario(path: str) -> dict:
    """Load and parse YAML scenario file."""
    scenario_path = Path(path)
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")

    with open(scenario_path) as f:
        spec = yaml.safe_load(f)

    if spec is None:
        raise ScenarioValidationError(f"Empty scenario file: {path}")

    return spec


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="SDSR Synthetic Data Injection Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python inject_synthetic.py --scenario scenarios/ONBOARDING-001.yaml
  python inject_synthetic.py --scenario scenarios/ACTIVITY-RETRY-001.yaml --dry-run
  python inject_synthetic.py --scenario scenarios/ACTIVITY-RETRY-001.yaml --cleanup
        """,
    )

    parser.add_argument(
        "--scenario",
        required=True,
        help="Path to YAML scenario file",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up synthetic data for this scenario instead of injecting",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned writes without executing",
    )

    args = parser.parse_args()

    try:
        # Load scenario
        logger.info(f"Loading scenario: {args.scenario}")
        spec = load_scenario(args.scenario)

        if args.cleanup:
            # Cleanup mode
            scenario_id = spec.get("scenario_id")
            if not scenario_id:
                raise ScenarioValidationError("Missing scenario_id in spec")

            results = cleanup_scenario(scenario_id, dry_run=args.dry_run)
            print(f"\nScenario: {results['scenario_id']}")
            print(f"Rows deleted: {results['rows_deleted']}")
            if results.get("tables_cleaned"):
                print(f"Tables cleaned: {', '.join(results['tables_cleaned'])}")
        else:
            # Injection mode
            # Rule 1: Validate completely before any writes
            logger.info("Validating scenario spec...")
            validate_scenario_spec(spec)
            logger.info("Validation passed")

            results = inject_scenario(spec, dry_run=args.dry_run)

            # Output summary
            print(f"\nScenario: {results['scenario_id']}")
            if args.dry_run:
                print("[DRY RUN - No changes made]")
            print(f"Rows written: {results['rows_written']}")
            print(f"Tables touched: {', '.join(results['tables_touched'])}")
            for op in results["operations"]:
                status = "planned" if args.dry_run else "created"
                print(f"  {op['operation']}: {op.get('id', 'N/A')} ({status})")

    except ScenarioValidationError as e:
        logger.error(f"VALIDATION FAILED: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"FILE NOT FOUND: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"INJECTION FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
