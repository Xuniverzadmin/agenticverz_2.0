#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CLI invocation
#   Execution: sync
# Role: SDSR Scenario Realization Engine (Keystone)
# Reference: PIN-370 (Scenario-Driven System Realization), PIN-379 (E2E Pipeline)

"""
SDSR inject_synthetic.py - Scenario Realization Engine

CONTRACT v1.0 (LOCKED - PIN-379)

PURPOSE:
    Realizes YAML scenario specifications into the system by creating
    ONLY canonical inputs and then handing control to the real system.

    If the scenario succeeds or fails, it must be because:
    - Backend engines behaved correctly, OR
    - Backend engines are missing or broken

    NOT because this script helped them.

WHAT THIS IS:
    - A Scenario → System bridge
    - A repeatable realization tool
    - A controlled entry point into real execution paths
    - A cleanup-capable realization executor

WHAT THIS IS NOT:
    - NOT a test runner
    - NOT a fixture loader
    - NOT a data seeder
    - NOT allowed to "complete" scenarios
    - NOT allowed to fabricate downstream state

EXIT CODES:
    0 → Inputs created + execution triggered
    1 → Validation failure (schema, missing fields)
    2 → Partial write (transaction rolled back)
    3 → Forbidden write attempted (guardrail violation)

FOUR NON-NEGOTIABLE RULES (PIN-370):
    1. NO INTELLIGENCE
       - Purely mechanical. No inference, no guessing, no helpful defaults.
       - Incomplete spec → fail loudly.

    2. WRITES ONLY WHAT REAL FLOWS WRITE
       - Synthetic ≠ fake. Use same data structures as real flows.

    3. EVERY ROW TRACEABLE
       - is_synthetic=true on every write. No exceptions.
       - synthetic_scenario_id set on every row.

    4. ONE SCENARIO = ONE TRANSACTION
       - Atomic, repeatable, idempotent when cleaned.

USAGE:
    python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml
    python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml --dry-run
    python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml --cleanup
    python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml --wait
"""

import argparse
import hashlib
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

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
# EXIT CODES (Contract v1.0)
# =============================================================================
EXIT_SUCCESS = 0  # Inputs created + execution triggered
EXIT_VALIDATION_FAILURE = 1  # Schema, missing fields
EXIT_PARTIAL_WRITE = 2  # Transaction rolled back
EXIT_FORBIDDEN_WRITE = 3  # Guardrail violation
EXIT_IDENTITY_REUSE = 4  # RG-SDSR-01: run_id already exists (LOCKED contract)


# =============================================================================
# FORBIDDEN TABLES (GUARDRAIL - Contract Section 6.2)
# =============================================================================
# These tables are created by backend engines, NOT by inject_synthetic.py
# Attempting to write → exit code 3 + abort

FORBIDDEN_TABLES = frozenset(
    [
        "aos_traces",
        "aos_trace_steps",
        "incidents",
        "policy_proposals",
        "prevention_records",
        "policy_rules",
    ]
)

# Tables we ARE allowed to write (Contract Section 6.1)
ALLOWED_TABLES = frozenset(
    [
        "tenants",
        "api_keys",
        "agents",
        "runs",
    ]
)


# =============================================================================
# CLEANUP ORDER (Contract Section 8.1)
# =============================================================================
# Topologically safe: children before parents
# Includes engine-generated tables for cleanup ONLY

CLEANUP_ORDER = [
    # Engine-generated tables (we clean these, but never write)
    "policy_proposals",
    "prevention_records",
    "incidents",
    "aos_trace_steps",
    "aos_traces",
    # Canonical input tables (we write and clean these)
    "runs",
    "worker_runs",
    "agents",
    "api_keys",
    "tenants",
]

# =============================================================================
# ARCHIVE-ONLY TABLES (S6 Immutability Contract)
# =============================================================================
# These tables are protected by S6 immutability triggers.
# DELETE is forbidden. SDSR cleanup uses soft-archive (UPDATE archived_at).
#
# Contract Resolution:
# - S6 Immutability: Prohibits DELETE, not archival state transitions
# - SDSR Cleanup: Archives synthetic trace data instead of deleting

ARCHIVE_ONLY_TABLES = frozenset(
    [
        "aos_traces",
        "aos_trace_steps",
    ]
)


# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

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
    "runs": ["status", "tenant_id", "parent_run_id", "priority", "max_attempts", "plan_json"],
    "worker_runs": ["status", "input_json", "api_key_id", "user_id", "parent_run_id"],
}


# =============================================================================
# EXCEPTIONS
# =============================================================================


class ScenarioValidationError(Exception):
    """Raised when scenario spec is incomplete or invalid."""

    pass


class ForbiddenWriteError(Exception):
    """Raised when attempting to write to a forbidden table."""

    pass


class IdempotencyError(Exception):
    """Raised when scenario data already exists without cleanup."""

    pass


class IdentityReuseError(Exception):
    """RG-SDSR-01: Raised when run_id already exists (active or archived).

    LOCKED CONTRACT: run_id must be execution-unique.
    No auto-fix, no suffixing, no bypass.
    """

    pass


# =============================================================================
# GUARDRAIL ENFORCEMENT
# =============================================================================


def enforce_run_id_uniqueness(run_id: str, conn) -> None:
    """RG-SDSR-01: Preflight guard for run_id uniqueness.

    LOCKED CONTRACT:
    - run_id must be execution-unique
    - Fails hard if run_id already exists (active OR archived)
    - No auto-fix, no suffixing, no bypass
    - Exit code 4 blocks injection

    This guard prevents identity reuse which causes silent trace collisions
    due to S6 immutability's ON CONFLICT DO NOTHING behavior.
    """
    cursor = conn.cursor()
    try:
        # Check if run_id exists in runs table (any state)
        cursor.execute("SELECT id FROM runs WHERE id = %s", (run_id,))
        existing = cursor.fetchone()
        if existing:
            raise IdentityReuseError(
                f"RG-SDSR-01 VIOLATION: run_id '{run_id}' already exists.\n"
                f"LOCKED CONTRACT: run_id must be execution-unique.\n"
                f"This is a HARD FAIL. No auto-fix, no bypass.\n"
                f"Possible causes:\n"
                f"  - Clock skew (two executions in same second)\n"
                f"  - Incomplete cleanup\n"
                f"  - Manual database insertion\n"
                f"Resolution: Wait 1 second and retry, or investigate the duplicate."
            )

        # Also check aos_traces for archived traces with matching run_id
        # (belt-and-suspenders: trace might exist even if run was deleted)
        cursor.execute("SELECT run_id FROM aos_traces WHERE run_id = %s", (run_id,))
        existing_trace = cursor.fetchone()
        if existing_trace:
            raise IdentityReuseError(
                f"RG-SDSR-01 VIOLATION: Trace for run_id '{run_id}' already exists.\n"
                f"LOCKED CONTRACT: run_id must be execution-unique.\n"
                f"A trace (active or archived) exists with this run_id.\n"
                f"This would cause silent trace creation failure due to S6 immutability.\n"
                f"Resolution: Use a different run_id or wait and retry."
            )
    finally:
        cursor.close()


def enforce_guardrail(table: str) -> None:
    """
    Check if table write is allowed.

    Contract Section 6.2: Attempting to write to forbidden tables → exit code 3
    """
    if table in FORBIDDEN_TABLES:
        raise ForbiddenWriteError(
            f"GUARDRAIL VIOLATION: Cannot write to '{table}'. "
            f"This table is created by backend engines, not by inject_synthetic.py. "
            f"Allowed tables: {sorted(ALLOWED_TABLES)}"
        )


# =============================================================================
# VALIDATION
# =============================================================================


def validate_scenario_spec(spec: dict) -> None:
    """
    Validate scenario specification has all required fields.

    Rule 1: NO INTELLIGENCE - fail loudly on missing fields.
    """
    if "scenario_id" not in spec:
        raise ScenarioValidationError("Missing required field: scenario_id")

    # Support both old format (backend.writes) and new format (preconditions/steps)
    has_old_format = "backend" in spec and "writes" in spec.get("backend", {})
    has_new_format = "preconditions" in spec or "steps" in spec

    if not has_old_format and not has_new_format:
        raise ScenarioValidationError(
            "Missing scenario structure. Expected 'backend.writes' (old format) or 'preconditions/steps' (new format)"
        )


def _operation_to_table(operation: str) -> str:
    """Map operation name to table name."""
    mapping = {
        "create_tenant": "tenants",
        "create_api_key": "api_keys",  # pragma: allowlist secret
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


def check_idempotency(scenario_id: str, conn) -> bool:
    """
    Check if scenario data already exists.

    Contract Section 9: Running inject twice without cleanup → error
    """
    cursor = conn.cursor()

    # Check if any synthetic data exists for this scenario
    for table in ALLOWED_TABLES:
        cursor.execute(
            f"SELECT COUNT(*) FROM {table} WHERE is_synthetic = true AND synthetic_scenario_id = %s", (scenario_id,)
        )
        count = cursor.fetchone()[0]
        if count > 0:
            cursor.close()
            return True

    cursor.close()
    return False


def build_writes_from_new_format(spec: dict) -> List[Dict[str, Any]]:
    """
    Convert new format (preconditions/steps) to writes list.

    New format structure:
        preconditions:
          tenant: {create: true, tenant_id: ...}
          api_key: {create: true, ...}
          agent: {create: true, agent_id: ...}
        steps:
          - step_id: ACTIVITY-FAIL
            action: create_run
            data: {...}

    SDSR Identity Rule (PIN-379):
        run_id is execution-unique; scenario IDs may repeat.
        Format: run-{scenario_id}-{UTC_YYYYMMDDTHHMMSSZ}
    """
    writes = []
    scenario_id = spec["scenario_id"]

    # Generate execution timestamp for unique run_id (SDSR Identity Rule)
    execution_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Process preconditions
    preconditions = spec.get("preconditions", {})

    # Tenant
    if preconditions.get("tenant", {}).get("create"):
        tenant_data = preconditions["tenant"]
        tenant_id = tenant_data.get("tenant_id", f"sdsr-tenant-{scenario_id}")
        writes.append(
            {
                "create_tenant": {
                    "id": tenant_id,
                    "name": tenant_data.get("name", f"SDSR Tenant {scenario_id}"),
                    "slug": tenant_data.get("slug", tenant_id),
                    "plan": tenant_data.get("plan", "enterprise"),
                    "status": "active",
                }
            }
        )

    # API Key
    if preconditions.get("api_key", {}).get("create"):
        api_key_data = preconditions["api_key"]
        tenant_id = preconditions.get("tenant", {}).get("tenant_id", f"sdsr-tenant-{scenario_id}")
        api_key_id = api_key_data.get("api_key_id", f"sdsr-key-{scenario_id}")
        # Generate a deterministic key hash for synthetic keys
        key_hash = hashlib.sha256(f"{scenario_id}:{api_key_id}".encode()).hexdigest()
        writes.append(
            {
                "create_api_key": {
                    "id": api_key_id,
                    "tenant_id": tenant_id,
                    "name": api_key_data.get("name", f"SDSR Key {scenario_id}"),
                    "key_prefix": "sdsr_",
                    "key_hash": key_hash,
                    "status": "active",
                }
            }
        )

    # Agent
    if preconditions.get("agent", {}).get("create"):
        agent_data = preconditions["agent"]
        agent_id = agent_data.get("agent_id", f"sdsr-agent-{scenario_id}")
        tenant_id = preconditions.get("tenant", {}).get("tenant_id", f"sdsr-tenant-{scenario_id}")
        writes.append(
            {
                "create_agent": {
                    "id": agent_id,
                    "name": agent_data.get("name", f"SDSR Agent {scenario_id}"),
                    "description": agent_data.get("description", f"Synthetic agent for {scenario_id}"),
                    "status": "active",
                    "tenant_id": tenant_id,
                    # Required NOT NULL fields with defaults (from Agent model)
                    "rate_limit_rpm": agent_data.get("rate_limit_rpm", 60),
                    "concurrent_runs_limit": agent_data.get("concurrent_runs_limit", 5),
                    "spent_cents": agent_data.get("spent_cents", 0),
                    "budget_alert_threshold": agent_data.get("budget_alert_threshold", 80),
                }
            }
        )

    # Process steps
    for step in spec.get("steps", []):
        action = step.get("action")
        data = step.get("data", {})

        if action == "create_run":
            # For E2E testing, we create runs with status="queued" so the worker picks them up
            # SDSR Contract: Scenarios inject CAUSES, engines create EFFECTS
            # A failed run is an EFFECT - we must create a queued run that will fail during execution

            # Determine if this run should fail during execution
            has_failure_plan = data.get("failure_code") is not None

            # SDSR Identity Rule (MANDATORY): run_id must be execution-unique
            # Format: run-{scenario_id}-{UTC_YYYYMMDDTHHMMSSZ}
            # This prevents trace_id conflicts on re-execution (S6 immutability)
            #
            # IMPORTANT: We ALWAYS generate unique run_id, ignoring any YAML override.
            # run_id is execution identity, not scenario configuration.
            unique_run_id = f"run-{scenario_id.lower()}-{execution_timestamp}"
            run_data = {
                "id": unique_run_id,  # Always unique per execution (SDSR Identity Rule)
                "agent_id": data.get(
                    "agent_id", preconditions.get("agent", {}).get("agent_id", f"sdsr-agent-{scenario_id}")
                ),
                "goal": data.get("goal", f"SDSR E2E Test: {step.get('description', scenario_id)}"),
                "tenant_id": data.get(
                    "tenant_id", preconditions.get("tenant", {}).get("tenant_id", f"sdsr-tenant-{scenario_id}")
                ),
                # SDSR: Always "queued" if we have a failure plan - let the worker execute and fail
                # This ensures engines fire (IncidentEngine, TraceStore, etc.)
                "status": "queued" if has_failure_plan else data.get("status", "queued"),
                "priority": data.get("priority", 5),
                "max_attempts": data.get("max_attempts", 1),
                # Required NOT NULL fields with defaults (from Run model)
                "attempts": data.get("attempts", 0),
            }

            # If the scenario expects failure, we need a plan that will fail
            # For EXECUTION_TIMEOUT scenarios, we use a special marker
            if data.get("failure_code") == "EXECUTION_TIMEOUT":
                # Create a plan that triggers timeout handling
                run_data["plan_json"] = '{"steps": [{"skill": "__sdsr_timeout_trigger__", "params": {}}]}'
                run_data["error_message"] = data.get("failure_message", "SDSR: Execution timeout triggered")
            elif data.get("failure_code"):
                # Other failure types - use a plan that will fail with the specified code
                run_data["plan_json"] = (
                    f'{{"steps": [{{"skill": "__sdsr_fail_trigger__", "params": {{"error_code": "{data.get("failure_code")}", "error_message": "{data.get("failure_message", "SDSR injected failure")}"}}}}]}}'
                )
                run_data["error_message"] = data.get("failure_message", f"SDSR: {data.get('failure_code')}")

            writes.append({"create_run": run_data})

    return writes


def inject_scenario(spec: dict, dry_run: bool = False) -> dict:
    """
    Inject a scenario's writes into the database.

    Rule 3: Every row traceable - is_synthetic=true, synthetic_scenario_id set.
    Rule 4: One scenario = one transaction.

    Returns:
        dict with summary of writes performed
    """
    scenario_id = spec["scenario_id"]

    # Determine writes based on format
    if "backend" in spec and "writes" in spec.get("backend", {}):
        writes = spec["backend"]["writes"]
    else:
        writes = build_writes_from_new_format(spec)

    results = {
        "scenario_id": scenario_id,
        "rows_written": 0,
        "tables_touched": set(),
        "operations": [],
        "execution_triggered": False,
    }

    if dry_run:
        logger.info(f"DRY RUN - Scenario: {scenario_id}")
        for write in writes:
            for operation, data in write.items():
                table = _operation_to_table(operation)

                # Guardrail check even in dry-run
                enforce_guardrail(table)

                results["operations"].append(
                    {
                        "operation": operation,
                        "table": table,
                        "data": data,
                    }
                )
                results["tables_touched"].add(table)
                logger.info(f"  [DRY] Would {operation}: {data.get('id', 'auto')}")
        results["tables_touched"] = list(results["tables_touched"])
        return results

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Contract Section 9: Idempotency check
        if check_idempotency(scenario_id, conn):
            raise IdempotencyError(
                f"Scenario {scenario_id} data already exists. Run with --cleanup first or use a different scenario_id."
            )

        for write in writes:
            for operation, data in write.items():
                table = _operation_to_table(operation)

                # Contract Section 6.2: Guardrail enforcement
                enforce_guardrail(table)

                # RG-SDSR-01: Execution identity guard (runs table only)
                # LOCKED CONTRACT: run_id must be execution-unique
                # Must check BEFORE insert, fails hard on reuse
                if table == "runs":
                    enforce_run_id_uniqueness(data["id"], conn)

                # Rule 3: Inject synthetic markers
                data["is_synthetic"] = True
                data["synthetic_scenario_id"] = scenario_id

                # Generate ID if not provided
                if "id" not in data or data["id"] is None:
                    data["id"] = str(uuid.uuid4())

                # Handle timestamps
                now = datetime.now(timezone.utc)
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

                results["operations"].append(
                    {
                        "operation": operation,
                        "table": table,
                        "id": data["id"],
                    }
                )
                results["tables_touched"].add(table)
                results["rows_written"] += 1

                # Track if we created a run (execution trigger)
                if table == "runs" and data.get("status") == "queued":
                    results["execution_triggered"] = True

        # Rule 4: Commit as single transaction
        conn.commit()
        logger.info(f"Committed {results['rows_written']} rows for scenario {scenario_id}")

        if results["execution_triggered"]:
            logger.info("Execution triggered: Worker pool will pick up queued run(s)")

    except ForbiddenWriteError:
        conn.rollback()
        raise  # Re-raise for exit code 3

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

    Contract Section 8: Uses is_synthetic + synthetic_scenario_id for targeted deletion.
    Operates topologically safe - children before parents.
    """
    results = {
        "scenario_id": scenario_id,
        "rows_deleted": 0,
        "tables_cleaned": [],
    }

    if dry_run:
        logger.info(f"DRY RUN - Would cleanup scenario: {scenario_id}")
        for table in CLEANUP_ORDER:
            if table in ARCHIVE_ONLY_TABLES:
                logger.info(
                    f"  [DRY] Would ARCHIVE {table} SET archived_at=NOW() WHERE is_synthetic=true AND synthetic_scenario_id='{scenario_id}' (S6 immutability)"
                )
            else:
                logger.info(
                    f"  [DRY] Would DELETE FROM {table} WHERE is_synthetic=true AND synthetic_scenario_id='{scenario_id}'"
                )
        return results

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Clean in topological order (children before parents)
        for table in CLEANUP_ORDER:
            try:
                if table in ARCHIVE_ONLY_TABLES:
                    # S6 Immutability: Use soft-archive (UPDATE) instead of DELETE
                    # This preserves trace integrity while satisfying SDSR cleanup
                    sql = f"""
                        UPDATE {table}
                        SET archived_at = NOW()
                        WHERE is_synthetic = true
                        AND synthetic_scenario_id = %s
                        AND archived_at IS NULL
                    """
                    cursor.execute(sql, (scenario_id,))
                    affected = cursor.rowcount
                    if affected > 0:
                        results["tables_cleaned"].append(table)
                        results["rows_deleted"] += affected  # Count as "cleaned" for reporting
                        logger.info(f"Archived {affected} rows from {table} (S6 immutability)")
                else:
                    # Standard DELETE for non-trace tables
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
            except Exception as e:
                # Fail loudly - do not swallow errors
                logger.error(f"CLEANUP FAILED on {table}: {e}")
                raise

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


def wait_for_execution(scenario_id: str, timeout_seconds: int = 60) -> dict:
    """
    Wait for scenario execution to complete.

    Polls the runs table until all synthetic runs are in terminal state.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    start_time = time.time()
    results = {"completed": False, "runs": []}

    try:
        while time.time() - start_time < timeout_seconds:
            cursor.execute(
                """
                SELECT id, status, error_message
                FROM runs
                WHERE is_synthetic = true AND synthetic_scenario_id = %s
                """,
                (scenario_id,),
            )
            runs = cursor.fetchall()

            if not runs:
                logger.warning(f"No runs found for scenario {scenario_id}")
                break

            all_terminal = True
            results["runs"] = []
            for run_id, status, error_message in runs:
                results["runs"].append(
                    {
                        "id": run_id,
                        "status": status,
                        "error_message": error_message,
                    }
                )
                if status not in ("completed", "failed", "cancelled"):
                    all_terminal = False

            if all_terminal:
                results["completed"] = True
                logger.info(f"All runs completed for scenario {scenario_id}")
                break

            logger.info(f"Waiting for execution... ({int(time.time() - start_time)}s)")
            time.sleep(2)

        if not results["completed"]:
            logger.warning(f"Timeout waiting for scenario {scenario_id} execution")

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
        description="SDSR Scenario Realization Engine (Contract v1.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit Codes:
  0  Inputs created + execution triggered
  1  Validation failure (schema, missing fields)
  2  Partial write (transaction rolled back)
  3  Forbidden write attempted (guardrail violation)

Examples:
  python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml
  python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml --dry-run
  python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml --cleanup
  python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml --wait
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

    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for execution to complete after injection",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds when using --wait (default: 60)",
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
            sys.exit(EXIT_SUCCESS)

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
            print(f"Execution triggered: {results['execution_triggered']}")
            for op in results["operations"]:
                status = "planned" if args.dry_run else "created"
                print(f"  {op['operation']}: {op.get('id', 'N/A')} ({status})")

            # Wait for execution if requested
            if args.wait and not args.dry_run and results["execution_triggered"]:
                logger.info(f"Waiting for execution (timeout: {args.timeout}s)...")
                wait_results = wait_for_execution(results["scenario_id"], args.timeout)
                print(f"\nExecution completed: {wait_results['completed']}")
                for run in wait_results.get("runs", []):
                    print(f"  Run {run['id']}: {run['status']}")
                    if run.get("error_message"):
                        print(f"    Error: {run['error_message']}")

            sys.exit(EXIT_SUCCESS)

    except ScenarioValidationError as e:
        logger.error(f"VALIDATION FAILED: {e}")
        sys.exit(EXIT_VALIDATION_FAILURE)

    except IdempotencyError as e:
        logger.error(f"IDEMPOTENCY ERROR: {e}")
        sys.exit(EXIT_VALIDATION_FAILURE)

    except ForbiddenWriteError as e:
        logger.error(f"GUARDRAIL VIOLATION: {e}")
        sys.exit(EXIT_FORBIDDEN_WRITE)

    except IdentityReuseError as e:
        logger.error(f"IDENTITY REUSE BLOCKED: {e}")
        sys.exit(EXIT_IDENTITY_REUSE)

    except FileNotFoundError as e:
        logger.error(f"FILE NOT FOUND: {e}")
        sys.exit(EXIT_VALIDATION_FAILURE)

    except Exception as e:
        logger.error(f"INJECTION FAILED: {e}")
        sys.exit(EXIT_PARTIAL_WRITE)


if __name__ == "__main__":
    main()
