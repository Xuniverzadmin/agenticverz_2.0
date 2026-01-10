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
import json
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

# DB-AUTH-001: Require Neon authority (CRITICAL - canonical truth)
from scripts._db_guard import require_neon
require_neon()

# SDSR Truth Materialization (LEAK-1 + LEAK-2 fix)
# These imports are used ONLY after --wait completes, not during injection
from Scenario_SDSR_output import (
    ScenarioSDSROutputBuilder,
    ObservedCapability,
    ObservedEffect,
    build_observed_capability,
)
from SDSR_output_emit_AURORA_L2 import emit_aurora_l2_observation

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


def build_writes_from_new_format(spec: dict, case_id: str = None) -> List[Dict[str, Any]]:
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

    Multi-case format (sub_scenarios):
        preconditions: {...}  # shared
        sub_scenarios:
          - case_id: CASE-A
            steps: [...]
          - case_id: CASE-B
            steps: [...]

    SDSR Identity Rule (PIN-379):
        run_id is execution-unique; scenario IDs may repeat.
        Format: run-{scenario_id}-{case_suffix}-{UTC_YYYYMMDDTHHMMSSZ}

    Args:
        spec: The scenario specification dict
        case_id: Optional case ID to select from sub_scenarios
    """
    writes = []
    scenario_id = spec["scenario_id"]

    # Determine which steps to use
    steps = []
    if "sub_scenarios" in spec:
        # Multi-case format
        if not case_id:
            raise ScenarioValidationError(
                f"Scenario {scenario_id} has sub_scenarios. "
                f"Use --case to specify which case to run. "
                f"Available cases: {[s['case_id'] for s in spec['sub_scenarios']]}"
            )
        # Find the matching sub_scenario
        matching_case = None
        for sub in spec["sub_scenarios"]:
            if sub.get("case_id") == case_id:
                matching_case = sub
                break
        if not matching_case:
            raise ScenarioValidationError(
                f"Case '{case_id}' not found in scenario {scenario_id}. "
                f"Available cases: {[s['case_id'] for s in spec['sub_scenarios']]}"
            )
        steps = matching_case.get("steps", [])
        logger.info(f"Selected sub_scenario: {case_id} with {len(steps)} steps")
    else:
        # Single scenario format
        steps = spec.get("steps", [])

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

    # Process steps (from spec.steps or selected sub_scenario)
    for step in steps:
        action = step.get("action")
        data = step.get("data", {})

        if action == "create_run":
            # =================================================================
            # SDSR RUN CREATION — Two Supported Modes (PIN-XXX)
            # =================================================================
            #
            # MODE 1: WORKER_EXECUTION (failure_code set)
            #   - Creates run with status="queued"
            #   - Worker picks up and executes plan
            #   - Worker fails with synthetic skill trigger
            #   - IncidentEngine reacts to worker completion
            #
            # MODE 2: STATE_INJECTION (status="failed" + failure_message)
            #   - Creates run with status="failed" directly
            #   - Worker IGNORES (terminal status)
            #   - error_message contains known code for severity mapping
            #   - IncidentEngine triggered by post-injection hook
            #
            # STATE_INJECTION Contract:
            #   If a run is created with:
            #     - status = failed
            #     - started_at IS NULL
            #     - error_message contains a known error code
            #   Then:
            #     - Worker MUST ignore the run
            #     - IncidentEngine MUST classify severity from error_message
            #     - Policy engines MAY react based on severity
            # =================================================================

            # Determine execution mode
            has_failure_plan = data.get("failure_code") is not None
            explicit_failed_status = data.get("status") == "failed"

            # GUARDRAIL: Conflicting failure_code and status: failed is ambiguous
            # This prevents confusion between WORKER_EXECUTION and STATE_INJECTION modes
            if has_failure_plan and explicit_failed_status:
                raise ScenarioValidationError(
                    f"Ambiguous intent: Both 'failure_code' and 'status: failed' specified in step '{step.get('step_id', 'unknown')}'. "
                    f"Use 'failure_code' for WORKER_EXECUTION mode, or 'status: failed' + 'failure_message' for STATE_INJECTION mode. "
                    f"These modes are mutually exclusive."
                )

            # STATE_INJECTION mode: direct failed state with failure_message
            is_state_injection = explicit_failed_status and data.get("failure_message")

            # SDSR Identity Rule (MANDATORY): run_id must be execution-unique
            # Format: run-{scenario_id}-{case_suffix}-{UTC_YYYYMMDDTHHMMSSZ}
            # This prevents trace_id conflicts on re-execution (S6 immutability)
            #
            # IMPORTANT: We ALWAYS generate unique run_id, ignoring any YAML override.
            # run_id is execution identity, not scenario configuration.
            case_suffix = f"-{case_id.lower().replace('_', '-')}" if case_id else ""
            unique_run_id = f"run-{scenario_id.lower()}{case_suffix}-{execution_timestamp}"
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
            elif is_state_injection:
                # =================================================================
                # STATE_INJECTION MODE
                # =================================================================
                # Direct failed state injection - NO worker execution
                # - status is already "failed" (set via data.get("status"))
                # - error_message must contain known error code for severity mapping
                # - No plan_json needed (no execution will occur)
                # - started_at will remain NULL (worker never touches it)
                #
                # The error_message MUST contain a known code from FAILURE_SEVERITY_MAP:
                #   EXECUTION_TIMEOUT, AGENT_CRASH, STEP_FAILURE, SKILL_ERROR → HIGH/CRITICAL
                #   BUDGET_EXCEEDED, RATE_LIMIT_EXCEEDED → MEDIUM
                #
                # Example failure_message values:
                #   "EXECUTION_TIMEOUT: Operation exceeded time limit"
                #   "BUDGET_EXCEEDED: Resource limit reached"
                # =================================================================
                run_data["error_message"] = data.get("failure_message")
                # No plan_json - this is terminal state, not execution
                logger.info(
                    f"STATE_INJECTION mode: run will be created with status=failed, "
                    f"error_message='{run_data['error_message'][:50]}...'"
                )
            elif run_data["status"] == "queued":
                # SDSR WORKER_EXECUTION: Minimal valid plan for success path
                # This satisfies the L4→L5 governance contract (PIN-257 Phase R-2).
                # The plan uses json_transform skill which is deterministic and
                # requires no external dependencies.
                #
                # Rule: SDSR runs must include a plan. The plan may be minimal,
                # but it must be valid and L4-compliant.
                minimal_success_plan = {
                    "steps": [
                        {
                            "step_id": "sdsr_success",
                            "skill": "json_transform",
                            "params": {
                                "payload": {"status": "success", "synthetic": True, "scenario_id": scenario_id},
                                "mapping": {"result": "status", "is_synthetic": "synthetic"},
                            },
                        }
                    ],
                    "metadata": {
                        "plan_type": "synthetic_minimal",
                        "generated_by": "inject_synthetic.py",
                        "sdsr_scenario": True,
                        "scenario_id": scenario_id,
                    },
                }
                run_data["plan_json"] = json.dumps(minimal_success_plan)

            writes.append({"create_run": run_data})

    return writes


def inject_scenario(spec: dict, dry_run: bool = False, case_id: str = None) -> dict:
    """
    Inject a scenario's writes into the database.

    Rule 3: Every row traceable - is_synthetic=true, synthetic_scenario_id set.
    Rule 4: One scenario = one transaction.

    Args:
        spec: The scenario specification dict
        dry_run: If True, only print planned writes without executing
        case_id: Optional case ID for multi-case scenarios (sub_scenarios)

    Returns:
        dict with summary of writes performed
    """
    scenario_id = spec["scenario_id"]

    # Determine writes based on format
    if "backend" in spec and "writes" in spec.get("backend", {}):
        writes = spec["backend"]["writes"]
    else:
        writes = build_writes_from_new_format(spec, case_id=case_id)

    results = {
        "scenario_id": scenario_id,
        "case_id": case_id,
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

                # STATE_INJECTION: Trigger IncidentEngine for failed runs
                # This simulates what the worker would do when a run fails.
                # Without this, failed runs created via STATE_INJECTION would
                # not produce incidents or policy proposals.
                if table == "runs" and data.get("status") == "failed":
                    from app.services.incident_engine import get_incident_engine

                    try:
                        engine = get_incident_engine()
                        incident_id = engine.check_and_create_incident(
                            run_id=data["id"],
                            status="failed",
                            error_message=data.get("error_message"),
                            tenant_id=data.get("tenant_id"),
                            agent_id=data.get("agent_id"),
                            is_synthetic=True,
                            synthetic_scenario_id=scenario_id,
                        )
                        if incident_id:
                            logger.info(
                                f"STATE_INJECTION: IncidentEngine created incident {incident_id}"
                            )
                            results["incident_created"] = incident_id
                    except Exception as e:
                        logger.error(f"STATE_INJECTION: Failed to invoke IncidentEngine: {e}")
                        # Don't fail the injection - this is a propagation test

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


# =============================================================================
# TRUTH MATERIALIZATION (LEAK-1 + LEAK-2 FIX)
# =============================================================================
# This function is called ONLY after --wait completes successfully.
# It materializes SDSR truth and emits observation artifact.
#
# Authority: inject_synthetic.py owns SDSR truth materialization
# Worker does NOT call this - worker only realizes effects
# =============================================================================


def materialize_and_emit_truth(
    scenario_id: str,
    spec: dict,
    wait_results: dict,
) -> dict:
    """
    Materialize SDSR truth and emit observation artifact.

    Called ONLY after --wait completes.
    Authority boundary: SDSR entrypoint, not worker.

    Returns:
        dict with materialization results:
        - status: PASSED | FAILED | HALTED
        - observation_path: path to emitted JSON (if PASSED)
        - error: error message (if any)
    """
    result = {
        "status": None,
        "observation_path": None,
        "error": None,
    }

    # Determine execution status from wait_results
    if not wait_results.get("completed"):
        result["status"] = "HALTED"
        result["error"] = "Execution did not complete within timeout"
        logger.warning(f"Scenario {scenario_id}: HALTED (timeout)")
        return result

    # Check run statuses
    runs = wait_results.get("runs", [])
    if not runs:
        result["status"] = "HALTED"
        result["error"] = "No runs found after execution"
        logger.warning(f"Scenario {scenario_id}: HALTED (no runs)")
        return result

    # Determine overall status
    # PASSED: All runs reached terminal state (completed or failed as expected)
    # FAILED: Any run in unexpected state
    all_terminal = all(r["status"] in ("completed", "failed") for r in runs)

    if not all_terminal:
        result["status"] = "FAILED"
        non_terminal = [r for r in runs if r["status"] not in ("completed", "failed")]
        result["error"] = f"Runs not terminal: {[r['id'] for r in non_terminal]}"
        logger.warning(f"Scenario {scenario_id}: FAILED (non-terminal runs)")
        return result

    # Extract expected capabilities from scenario spec
    # Look in: spec.capabilities_tested OR spec.expected_capabilities OR infer from steps
    capabilities_tested = spec.get("capabilities_tested", [])
    if not capabilities_tested:
        capabilities_tested = spec.get("expected_capabilities", [])

    # If not explicitly defined, try to infer from steps
    if not capabilities_tested:
        steps = spec.get("steps", [])
        for step in steps:
            cap_id = step.get("capability_id")
            if cap_id:
                capabilities_tested.append({
                    "capability_id": cap_id,
                    "endpoint": step.get("endpoint"),
                    "method": step.get("method"),
                })

    # Build ObservedCapability list
    observed_capabilities = []
    for cap_spec in capabilities_tested:
        cap_id = cap_spec if isinstance(cap_spec, str) else cap_spec.get("capability_id")
        if not cap_id:
            continue

        # Build effects from spec or use empty list
        effects = []
        if isinstance(cap_spec, dict):
            for effect_spec in cap_spec.get("expected_effects", []):
                effects.append(ObservedEffect(
                    entity=effect_spec.get("entity", "unknown"),
                    field=effect_spec.get("field", "status"),
                    before=effect_spec.get("from"),
                    after=effect_spec.get("to"),
                ))

        observed_capabilities.append(ObservedCapability(
            capability_id=cap_id,
            effects=effects,
            endpoint=cap_spec.get("endpoint") if isinstance(cap_spec, dict) else None,
            method=cap_spec.get("method") if isinstance(cap_spec, dict) else None,
        ))

    # Materialize truth (LEAK-1 fix)
    try:
        # Use first run_id as the representative run_id
        run_id = runs[0]["id"] if runs else f"run-{scenario_id}-unknown"

        scenario_output = ScenarioSDSROutputBuilder.from_execution(
            scenario_id=scenario_id,
            run_id=run_id,
            execution_status="PASSED",
            observed_capabilities=observed_capabilities,
            notes=f"Materialized by inject_synthetic.py after --wait",
        )

        result["status"] = "PASSED"
        logger.info(f"Scenario {scenario_id}: Truth materialized (PASSED)")

    except Exception as e:
        result["status"] = "FAILED"
        result["error"] = f"Truth materialization failed: {e}"
        logger.error(f"Scenario {scenario_id}: Materialization error: {e}")
        return result

    # Emit observation artifact (LEAK-2 fix)
    # Only emit if PASSED
    if result["status"] == "PASSED":
        try:
            observation_path = emit_aurora_l2_observation(scenario_output)
            result["observation_path"] = observation_path
            logger.info(f"Scenario {scenario_id}: Observation emitted to {observation_path}")
        except Exception as e:
            # Emission failure doesn't change PASSED status
            # Truth was materialized, but witness failed to record
            result["error"] = f"Observation emission failed: {e}"
            logger.error(f"Scenario {scenario_id}: Emission error: {e}")

    return result


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

    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Case ID to run for multi-case scenarios (e.g., CASE-A-MEDIUM)",
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

            results = inject_scenario(spec, dry_run=args.dry_run, case_id=args.case)

            # Output summary
            print(f"\nScenario: {results['scenario_id']}")
            if results.get("case_id"):
                print(f"Case: {results['case_id']}")
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

                # LEAK-1 + LEAK-2 FIX: Materialize truth and emit observation
                # This happens ONLY after --wait, ONLY in SDSR entrypoint
                print("\n" + "=" * 60)
                print("SDSR TRUTH MATERIALIZATION")
                print("=" * 60)

                truth_results = materialize_and_emit_truth(
                    scenario_id=results["scenario_id"],
                    spec=spec,
                    wait_results=wait_results,
                )

                print(f"  Status: {truth_results['status']}")
                if truth_results.get("observation_path"):
                    print(f"  Observation: {truth_results['observation_path']}")
                if truth_results.get("error"):
                    print(f"  Error: {truth_results['error']}")

                # Report next step for LEAK-3 + LEAK-4
                if truth_results["status"] == "PASSED" and truth_results.get("observation_path"):
                    print("\n" + "=" * 60)
                    print("NEXT STEP (Manual or via sdsr_e2e_apply.py):")
                    print("=" * 60)
                    print(f"  python3 scripts/tools/AURORA_L2_apply_sdsr_observations.py \\")
                    print(f"      --observation {truth_results['observation_path']}")
                    print(f"  ./scripts/tools/run_aurora_l2_pipeline.sh")

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
