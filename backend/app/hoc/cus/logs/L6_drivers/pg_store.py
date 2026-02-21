# capability_id: CAP-001
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api/worker (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: aos_traces, aos_trace_steps
#   Writes: aos_traces, aos_trace_steps (INSERT, UPDATE status)
# Database:
#   Scope: domain (logs)
#   Models: aos_traces, aos_trace_steps
# Role: PostgreSQL trace storage
# Callers: trace store abstraction
# Allowed Imports: L6, L7 (models), L5_schemas (PIN-521)
# Reference: PIN-470, Trace System
#
# INTENT FREEZE (2026-01-24):
# This file implements TRACE STORAGE with PostgreSQL using asyncpg.
# The `_status_to_level()` function is a FIXED MAPPING, not a business decision.
# It maps status strings (success, failure, retry) to log levels (INFO, ERROR, WARN)
# per PIN-378 (Canonical Logs System). The mapping is deterministic and policy-free.
# Layer L6 compliance: Pure data access and fixed transformation, no policy evaluation.

"""
PostgreSQL Trace Store for AOS
M8 Deliverable: Production-grade trace storage with PostgreSQL

Provides:
- Async PostgreSQL storage with connection pooling
- RBAC-aware trace access
- PII redaction before storage
- Efficient indexing for query API

FROZEN SEMANTICS (PIN-198, S6 Trace Integrity Truth):
- All trace INSERTs use ON CONFLICT DO NOTHING (Invariant #15: First Truth Wins)
- No UPDATE on aos_trace_steps (Invariant #13: Trace Ledger Semantics)
- Only status/completed_at UPDATE allowed on aos_traces
- DELETE requires archive-first (Invariant #13)
See LESSONS_ENFORCED.md Invariants #13, #15
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from app.hoc.cus.logs.L5_schemas import (
    TraceRecord,
    TraceStatus,
    TraceStep,
    TraceSummary,
)
from app.hoc.cus.logs.L6_drivers.redact import redact_trace_data


def _status_to_level(status: str) -> str:
    """
    Derive log level from step status.

    Mapping per PIN-378 (Canonical Logs System):
    - success → INFO
    - skipped → INFO
    - retry → WARN
    - failure → ERROR
    """
    status_lower = status.lower() if isinstance(status, str) else str(status).lower()
    if status_lower in ("failure", "error"):
        return "ERROR"
    elif status_lower in ("retry", "retrying"):
        return "WARN"
    else:
        return "INFO"


class PostgresTraceStore:
    """
    PostgreSQL-based trace storage for production.

    Uses asyncpg for async database operations.
    Supports multi-tenant isolation and RBAC.
    """

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", "postgresql://nova:novapass@localhost:6432/nova_aos"
        )
        self._pool = None

    async def _get_pool(self):
        """Get or create connection pool."""
        if self._pool is None:
            import asyncpg

            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                # Disable prepared statements for PgBouncer compatibility
                statement_cache_size=0,
            )
        return self._pool

    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    # =========================================================================
    # Core CRUD Operations
    # =========================================================================

    async def start_trace(
        self,
        run_id: str,
        correlation_id: str,
        tenant_id: str,
        agent_id: str | None,
        plan: list[dict[str, Any]],
        *,
        # SDSR columns (PIN-378)
        is_synthetic: bool = False,
        synthetic_scenario_id: str | None = None,
        incident_id: str | None = None,
        # Replay mode columns (migration 132, UC-MON)
        replay_mode: str | None = None,
        replay_attempt_id: str | None = None,
        replay_artifact_version: str | None = None,
        trace_completeness_status: str | None = None,
    ) -> str:
        """Start a new trace record (for replay compatibility).

        S6 IMMUTABILITY: Traces are append-only. If a trace already exists
        for this run_id, the insert is ignored (idempotent).

        SDSR Inheritance (PIN-378):
        - is_synthetic and synthetic_scenario_id should be passed from run
        - incident_id links trace to an incident for cross-domain correlation

        Returns:
            trace_id: The canonical trace identifier for this run.
                      MUST be used for all subsequent record_step calls.
        """
        pool = await self._get_pool()
        now = datetime.now(timezone.utc)
        # PIN-404: trace_id is derived HERE and returned for consistent use
        # This is the ONLY place trace_id derivation should happen
        trace_id = f"trace_{run_id}"  # Simple, predictable derivation

        async with pool.acquire() as conn:
            # S6: Append-only - ignore if trace already exists
            await conn.execute(
                """
                INSERT INTO aos_traces (
                    trace_id, run_id, correlation_id, tenant_id, agent_id,
                    root_hash, plan, trace, schema_version, status, started_at, created_at,
                    is_synthetic, synthetic_scenario_id, incident_id,
                    replay_mode, replay_attempt_id, replay_artifact_version, trace_completeness_status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                ON CONFLICT (trace_id) DO NOTHING
                """,
                trace_id,  # trace_id
                run_id,  # run_id
                correlation_id,  # correlation_id
                tenant_id,  # tenant_id
                agent_id,  # agent_id
                "pending",  # root_hash (placeholder, computed later)
                json.dumps(plan),  # plan
                json.dumps({"steps": []}),  # trace (empty initially)
                "1.0",  # schema_version
                "running",  # status
                now,  # started_at
                now,  # created_at
                is_synthetic,  # is_synthetic (SDSR)
                synthetic_scenario_id,  # synthetic_scenario_id (SDSR)
                incident_id,  # incident_id (cross-domain correlation)
                replay_mode,  # replay_mode (UC-MON)
                replay_attempt_id,  # replay_attempt_id (UC-MON)
                replay_artifact_version,  # replay_artifact_version (UC-MON)
                trace_completeness_status,  # trace_completeness_status (UC-MON)
            )

        return trace_id  # PIN-404: Return for consistent use in record_step

    async def record_step(
        self,
        trace_id: str,  # REQUIRED - never derived (PIN-404 fix)
        run_id: str,
        step_index: int,
        skill_name: str,
        params: dict[str, Any],
        status: str,  # or TraceStatus
        outcome_category: str,
        outcome_code: str | None,
        outcome_data: dict[str, Any] | None,
        cost_cents: float,
        duration_ms: float,
        retry_count: int,
        *,
        # SDSR columns (PIN-378, PIN-404)
        source: str = "engine",
        is_synthetic: bool = False,
        synthetic_scenario_id: str | None = None,
    ) -> None:
        """Record a step in the trace (for replay compatibility).

        S6 IMMUTABILITY: Steps are append-only. Duplicate inserts are ignored.

        PIN-404 INVARIANT: trace_id is ALWAYS passed, NEVER derived.
        Identity is propagated, not recomputed.

        SDSR (PIN-378, PIN-404):
        - trace_id: Authoritative trace identity (required)
        - source: Origin of step (engine, external, replay)
        - level: Derived from status (INFO/WARN/ERROR)
        - is_synthetic: SDSR marker for cleanup
        - synthetic_scenario_id: Scenario lineage for integrity
        """
        pool = await self._get_pool()
        now = datetime.now(timezone.utc)

        # PIN-404 GUARDRAIL: trace_id must not be empty
        if not trace_id:
            raise ValueError("trace_id is required - identity must be passed, not derived")

        # PIN-404 GUARDRAIL: synthetic consistency
        if is_synthetic and not synthetic_scenario_id:
            raise ValueError("synthetic_scenario_id required when is_synthetic=True")

        # Convert status if it's an enum
        status_val = status.value if hasattr(status, "value") else status

        # Derive level from status (PIN-378)
        level = _status_to_level(status_val)

        async with pool.acquire() as conn:
            # PIN-404 GUARDRAIL: Verify parent trace exists by trace_id (canonical identifier)
            parent_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM aos_traces WHERE trace_id = $1)",
                trace_id,
            )
            if not parent_exists:
                raise ValueError(f"Parent trace {trace_id} does not exist - orphan steps forbidden")

            # S6: Append-only - ignore duplicates, never update
            await conn.execute(
                """
                INSERT INTO aos_trace_steps (
                    trace_id, step_index, skill_id, skill_name, params,
                    status, outcome_category, outcome_code, outcome_data,
                    cost_cents, duration_ms, retry_count, replay_behavior, timestamp,
                    source, level, is_synthetic, synthetic_scenario_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                ON CONFLICT (trace_id, step_index) DO NOTHING
                """,
                trace_id,  # trace_id (PASSED, not derived)
                step_index,  # step_index
                skill_name,  # skill_id (use skill_name as id)
                skill_name,  # skill_name
                json.dumps(params),  # params (jsonb)
                status_val,  # status
                outcome_category,  # outcome_category
                outcome_code,  # outcome_code
                json.dumps(outcome_data) if outcome_data else None,  # outcome_data (jsonb)
                cost_cents,  # cost_cents
                duration_ms,  # duration_ms
                retry_count,  # retry_count
                "execute",  # replay_behavior (default)
                now,  # timestamp
                source,  # source (SDSR)
                level,  # level (derived from status)
                is_synthetic,  # is_synthetic (PIN-404)
                synthetic_scenario_id,  # synthetic_scenario_id (PIN-404)
            )

    async def complete_trace(
        self,
        run_id: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark a trace as completed (for replay compatibility)."""
        pool = await self._get_pool()
        now = datetime.now(timezone.utc)

        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE aos_traces
                SET status = $1, completed_at = $2, metadata = COALESCE($3, metadata)
                WHERE run_id = $4
                """,
                status,
                now,
                json.dumps(metadata) if metadata else None,
                run_id,
            )

    async def mark_trace_aborted(
        self,
        run_id: str,
        reason: str,
    ) -> None:
        """
        Mark a trace as ABORTED due to finalization failure.

        FAIL-CLOSED TRACE SEMANTICS (PIN-406):
        A trace is either COMPLETE or ABORTED. There is no "dangling".

        When trace finalization fails (e.g., complete_trace() throws):
        - The trace MUST be marked ABORTED
        - This is a terminal state (no retry)
        - Integrity treats ABORTED as sealed-but-failed

        Args:
            run_id: The run whose trace failed to complete
            reason: Why finalization failed (for audit)
        """
        pool = await self._get_pool()
        now = datetime.now(timezone.utc)

        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE aos_traces
                SET status = 'aborted',
                    completed_at = $1,
                    metadata = jsonb_set(
                        COALESCE(metadata, '{}'::jsonb),
                        '{abort_reason}',
                        $2::jsonb
                    )
                WHERE run_id = $3 AND status = 'running'
                """,
                now,
                json.dumps(reason),
                run_id,
            )

    async def store_trace(
        self,
        trace: dict[str, Any],
        tenant_id: str,
        stored_by: str | None = None,
        redact_pii: bool = True,
        *,
        # SDSR columns (PIN-378)
        is_synthetic: bool = False,
        synthetic_scenario_id: str | None = None,
        incident_id: str | None = None,
        # Replay mode columns (migration 132, UC-MON)
        replay_mode: str | None = None,
        replay_attempt_id: str | None = None,
        replay_artifact_version: str | None = None,
        trace_completeness_status: str | None = None,
    ) -> str:
        """
        Store a trace from SDK or simulation.

        S6 IMMUTABILITY: Traces are append-only. Duplicate trace_ids are ignored.
        If you need to store a modified trace, use a new trace_id.

        Args:
            trace: Complete trace object
            tenant_id: Tenant for isolation
            stored_by: User ID who stored the trace
            redact_pii: Apply PII redaction before storage
            is_synthetic: SDSR marker (inherited from run)
            synthetic_scenario_id: Scenario ID for traceability
            incident_id: Cross-domain correlation to incidents

        Returns:
            trace_id
        """
        pool = await self._get_pool()

        # Generate trace_id if not present
        trace_id = trace.get("trace_id") or f"trace_{uuid.uuid4().hex[:16]}"
        run_id = trace.get("run_id") or trace.get("trace_id") or trace_id

        # SDSR: Allow trace dict to override parameters
        is_synthetic = trace.get("is_synthetic", is_synthetic)
        synthetic_scenario_id = trace.get("synthetic_scenario_id", synthetic_scenario_id)
        incident_id = trace.get("incident_id", incident_id)

        # Replay: Allow trace dict to override parameters
        replay_mode = trace.get("replay_mode", replay_mode)
        replay_attempt_id = trace.get("replay_attempt_id", replay_attempt_id)
        replay_artifact_version = trace.get("replay_artifact_version", replay_artifact_version)
        trace_completeness_status = trace.get("trace_completeness_status", trace_completeness_status)

        # Redact PII before storage
        if redact_pii:
            trace = redact_trace_data(trace)

        async with pool.acquire() as conn:
            # S6: Append-only - ignore duplicates, never update trace content
            await conn.execute(
                """
                INSERT INTO aos_traces (
                    trace_id, run_id, correlation_id, tenant_id, agent_id,
                    plan_id, seed, frozen_timestamp, root_hash, plan_hash,
                    schema_version, plan, trace, metadata, status,
                    started_at, completed_at, stored_by,
                    is_synthetic, synthetic_scenario_id, incident_id,
                    replay_mode, replay_attempt_id, replay_artifact_version, trace_completeness_status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25)
                ON CONFLICT (trace_id) DO NOTHING
                """,
                trace_id,
                run_id,
                trace.get("correlation_id", run_id),
                tenant_id,
                trace.get("agent_id"),
                trace.get("plan_id"),
                trace.get("seed", 42),
                trace.get("frozen_timestamp") or trace.get("timestamp"),
                trace.get("root_hash"),
                trace.get("plan_hash"),
                trace.get("schema_version", "1.1"),
                json.dumps(trace.get("plan", [])),
                json.dumps(trace),
                json.dumps(trace.get("metadata", {})),
                trace.get("status", "completed"),
                datetime.fromisoformat(trace["started_at"]) if trace.get("started_at") else datetime.now(timezone.utc),
                datetime.fromisoformat(trace["completed_at"]) if trace.get("completed_at") else None,
                stored_by,
                is_synthetic,  # SDSR
                synthetic_scenario_id,  # SDSR
                incident_id,  # Cross-domain correlation
                replay_mode,  # UC-MON replay determinism
                replay_attempt_id,  # UC-MON replay determinism
                replay_artifact_version,  # UC-MON replay determinism
                trace_completeness_status,  # UC-MON replay determinism
            )

            # Store steps separately for efficient querying
            # S6 IMMUTABILITY: Steps are append-only. Duplicate inserts are ignored.
            steps = trace.get("steps", [])
            for step in steps:
                step_status = step.get("status", "success")
                step_level = _status_to_level(step_status)
                step_source = step.get("source", "engine")

                await conn.execute(
                    """
                    INSERT INTO aos_trace_steps (
                        trace_id, step_index, skill_id, skill_name, params,
                        status, outcome_category, outcome_code, outcome_data,
                        cost_cents, duration_ms, retry_count,
                        input_hash, output_hash, rng_state_before,
                        idempotency_key, replay_behavior, timestamp,
                        source, level
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                    ON CONFLICT (trace_id, step_index) DO NOTHING
                    """,
                    trace_id,
                    step.get("step_index", 0),
                    step.get("skill_id", step.get("skill_name", "unknown")),
                    step.get("skill_name", "unknown"),
                    json.dumps(step.get("params", {})),
                    step_status,
                    step.get("outcome_category", "SUCCESS"),
                    step.get("outcome_code"),
                    json.dumps(step.get("outcome_data")) if step.get("outcome_data") else None,
                    step.get("cost_cents", 0.0),
                    step.get("duration_ms", 0.0),
                    step.get("retry_count", 0),
                    step.get("input_hash"),
                    step.get("output_hash"),
                    step.get("rng_state_before") or step.get("rng_state"),
                    step.get("idempotency_key"),
                    step.get("replay_behavior", "execute"),
                    datetime.fromisoformat(step["timestamp"]) if step.get("timestamp") else datetime.now(timezone.utc),
                    step_source,  # source (SDSR)
                    step_level,  # level (derived from status)
                )

        return trace_id

    async def get_trace(
        self,
        trace_id: str,
        tenant_id: str | None = None,
    ) -> TraceRecord | None:
        """Get trace by ID with optional tenant check."""
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            # Build query with optional tenant filter
            if tenant_id:
                row = await conn.fetchrow(
                    "SELECT * FROM aos_traces WHERE trace_id = $1 AND tenant_id = $2", trace_id, tenant_id
                )
            else:
                row = await conn.fetchrow("SELECT * FROM aos_traces WHERE trace_id = $1", trace_id)

            if not row:
                # Try by run_id
                if tenant_id:
                    row = await conn.fetchrow(
                        "SELECT * FROM aos_traces WHERE run_id = $1 AND tenant_id = $2", trace_id, tenant_id
                    )
                else:
                    row = await conn.fetchrow("SELECT * FROM aos_traces WHERE run_id = $1", trace_id)

            if not row:
                return None

            # Get steps
            steps_rows = await conn.fetch(
                "SELECT * FROM aos_trace_steps WHERE trace_id = $1 ORDER BY step_index", row["trace_id"]
            )

            steps = [
                TraceStep(
                    step_index=s["step_index"],
                    skill_name=s["skill_name"],
                    params=json.loads(s["params"]) if s["params"] else {},
                    status=TraceStatus(s["status"])
                    if s["status"] in [e.value for e in TraceStatus]
                    else TraceStatus.SUCCESS,
                    outcome_category=s["outcome_category"],
                    outcome_code=s["outcome_code"],
                    outcome_data=json.loads(s["outcome_data"]) if s["outcome_data"] else None,
                    cost_cents=s["cost_cents"] or 0.0,
                    duration_ms=s["duration_ms"] or 0.0,
                    retry_count=s["retry_count"] or 0,
                    timestamp=s["timestamp"] or datetime.now(timezone.utc),
                )
                for s in steps_rows
            ]

            return TraceRecord(
                run_id=row["run_id"],
                correlation_id=row["correlation_id"],
                tenant_id=row["tenant_id"],
                agent_id=row["agent_id"],
                plan=json.loads(row["plan"]) if row["plan"] else [],
                steps=steps,
                started_at=row["started_at"] or datetime.now(timezone.utc),
                completed_at=row["completed_at"],
                status=row["status"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                seed=row["seed"] or 42,
                frozen_timestamp=row["frozen_timestamp"],
                root_hash=row["root_hash"],
                # Replay mode fields (migration 132, UC-MON)
                replay_mode=row.get("replay_mode"),
                replay_attempt_id=row.get("replay_attempt_id"),
                replay_artifact_version=row.get("replay_artifact_version"),
                trace_completeness_status=row.get("trace_completeness_status"),
            )

    async def get_trace_by_root_hash(
        self,
        root_hash: str,
        tenant_id: str | None = None,
    ) -> TraceRecord | None:
        """Get trace by deterministic root hash."""
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            if tenant_id:
                row = await conn.fetchrow(
                    "SELECT trace_id FROM aos_traces WHERE root_hash = $1 AND tenant_id = $2 LIMIT 1",
                    root_hash,
                    tenant_id,
                )
            else:
                row = await conn.fetchrow("SELECT trace_id FROM aos_traces WHERE root_hash = $1 LIMIT 1", root_hash)

            if row:
                return await self.get_trace(row["trace_id"], tenant_id)
            return None

    async def search_traces(
        self,
        tenant_id: str | None = None,
        agent_id: str | None = None,
        root_hash: str | None = None,
        plan_hash: str | None = None,
        seed: int | None = None,
        status: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TraceSummary]:
        """Search traces with multiple filters."""
        pool = await self._get_pool()

        conditions = []
        params = []
        param_idx = 1

        if tenant_id:
            conditions.append(f"tenant_id = ${param_idx}")
            params.append(tenant_id)
            param_idx += 1

        if agent_id:
            conditions.append(f"agent_id = ${param_idx}")
            params.append(agent_id)
            param_idx += 1

        if root_hash:
            conditions.append(f"root_hash = ${param_idx}")
            params.append(root_hash)
            param_idx += 1

        if plan_hash:
            conditions.append(f"plan_hash = ${param_idx}")
            params.append(plan_hash)
            param_idx += 1

        if seed is not None:
            conditions.append(f"seed = ${param_idx}")
            params.append(seed)
            param_idx += 1

        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        if from_date:
            conditions.append(f"started_at >= ${param_idx}")
            params.append(datetime.fromisoformat(from_date))
            param_idx += 1

        if to_date:
            conditions.append(f"started_at <= ${param_idx}")
            params.append(datetime.fromisoformat(to_date))
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT t.*,
                       COUNT(s.id) as total_steps,
                       SUM(CASE WHEN s.status = 'success' THEN 1 ELSE 0 END) as success_count,
                       SUM(CASE WHEN s.status = 'failure' THEN 1 ELSE 0 END) as failure_count,
                       COALESCE(SUM(s.cost_cents), 0) as total_cost_cents,
                       COALESCE(SUM(s.duration_ms), 0) as total_duration_ms
                FROM aos_traces t
                LEFT JOIN aos_trace_steps s ON t.trace_id = s.trace_id
                WHERE {where_clause}
                GROUP BY t.id
                ORDER BY t.created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
                """,
                *params,
                limit,
                offset,
            )

            return [
                TraceSummary(
                    run_id=row["run_id"],
                    correlation_id=row["correlation_id"],
                    tenant_id=row["tenant_id"],
                    agent_id=row["agent_id"],
                    total_steps=row["total_steps"] or 0,
                    success_count=row["success_count"] or 0,
                    failure_count=row["failure_count"] or 0,
                    total_cost_cents=row["total_cost_cents"] or 0.0,
                    total_duration_ms=row["total_duration_ms"] or 0.0,
                    started_at=row["started_at"] or datetime.now(timezone.utc),
                    completed_at=row["completed_at"],
                    status=row["status"],
                )
                for row in rows
            ]

    async def list_traces(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TraceSummary]:
        """List traces, optionally filtered by tenant (TraceStore interface)."""
        return await self.search_traces(tenant_id=tenant_id, limit=limit, offset=offset)

    async def delete_trace(
        self,
        trace_id: str,
        tenant_id: str | None = None,
    ) -> bool:
        """Delete trace by ID.

        S6 IMMUTABILITY WARNING: Direct deletion is blocked by database trigger.
        Use cleanup_old_traces() which archives first, then deletes.

        This method will raise an exception if the trace hasn't been archived.
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            if tenant_id:
                result = await conn.execute(
                    "DELETE FROM aos_traces WHERE trace_id = $1 AND tenant_id = $2", trace_id, tenant_id
                )
            else:
                result = await conn.execute("DELETE FROM aos_traces WHERE trace_id = $1", trace_id)

            return bool(result != "DELETE 0")

    async def get_trace_count(self, tenant_id: str | None = None) -> int:
        """Get total trace count."""
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            if tenant_id:
                row = await conn.fetchrow("SELECT COUNT(*) FROM aos_traces WHERE tenant_id = $1", tenant_id)
            else:
                row = await conn.fetchrow("SELECT COUNT(*) FROM aos_traces")
            return row[0] if row else 0

    async def cleanup_old_traces(self, days: int = 30) -> int:
        """Archive and delete traces older than specified days."""
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            # First archive to aos_traces_archive
            await conn.execute(
                """
                INSERT INTO aos_traces_archive
                SELECT * FROM aos_traces
                WHERE created_at < now() - interval '1 day' * $1
                ON CONFLICT (trace_id) DO NOTHING
                """,
                days,
            )

            # Then delete from main table
            result = await conn.execute(
                """
                DELETE FROM aos_traces
                WHERE created_at < now() - interval '1 day' * $1
                """,
                days,
            )

            # Extract count from result
            count = int(result.split()[-1]) if result else 0
            return count

    # =========================================================================
    # Idempotency Check
    # =========================================================================

    async def check_idempotency_key(
        self,
        idempotency_key: str,
        tenant_id: str,
    ) -> dict | None:
        """
        Check if an idempotency key has been executed.

        Returns the step data if found, None if not executed.
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT s.*, t.tenant_id
                FROM aos_trace_steps s
                JOIN aos_traces t ON s.trace_id = t.trace_id
                WHERE s.idempotency_key = $1 AND t.tenant_id = $2
                LIMIT 1
                """,
                idempotency_key,
                tenant_id,
            )

            if row:
                return {
                    "executed": True,
                    "trace_id": row["trace_id"],
                    "step_index": row["step_index"],
                    "status": row["status"],
                    "output_hash": row["output_hash"],
                    "outcome_data": json.loads(row["outcome_data"]) if row["outcome_data"] else None,
                }
            return None


# Singleton instance
_pg_store: PostgresTraceStore | None = None


def get_postgres_trace_store() -> PostgresTraceStore:
    """Get singleton PostgreSQL trace store."""
    global _pg_store
    if _pg_store is None:
        _pg_store = PostgresTraceStore()
    return _pg_store
