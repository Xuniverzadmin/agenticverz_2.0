"""
PostgreSQL Trace Store for AOS
M8 Deliverable: Production-grade trace storage with PostgreSQL

Provides:
- Async PostgreSQL storage with connection pooling
- RBAC-aware trace access
- PII redaction before storage
- Efficient indexing for query API
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from .models import TraceRecord, TraceStatus, TraceStep, TraceSummary
from .redact import redact_trace_data


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
    ) -> None:
        """Start a new trace record (for replay compatibility)."""
        pool = await self._get_pool()
        now = datetime.now(timezone.utc)
        # Use run_id as base for trace_id for easier correlation
        trace_id = f"trace_{run_id.replace('run_', '')}" if run_id.startswith("run_") else f"trace_{run_id}"

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO aos_traces (
                    trace_id, run_id, correlation_id, tenant_id, agent_id,
                    root_hash, plan, trace, schema_version, status, started_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (trace_id) DO UPDATE SET
                    status = 'running',
                    started_at = EXCLUDED.started_at
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
            )

    async def record_step(
        self,
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
    ) -> None:
        """Record a step in the trace (for replay compatibility)."""
        pool = await self._get_pool()
        now = datetime.now(timezone.utc)

        # Convert status if it's an enum
        status_val = status.value if hasattr(status, "value") else status

        # Derive trace_id from run_id
        trace_id = f"trace_{run_id.replace('run_', '')}" if run_id.startswith("run_") else f"trace_{run_id}"

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO aos_trace_steps (
                    trace_id, step_index, skill_id, skill_name, params,
                    status, outcome_category, outcome_code, outcome_data,
                    cost_cents, duration_ms, retry_count, replay_behavior, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (trace_id, step_index) DO UPDATE SET
                    status = EXCLUDED.status,
                    outcome_data = EXCLUDED.outcome_data,
                    cost_cents = EXCLUDED.cost_cents,
                    duration_ms = EXCLUDED.duration_ms
                """,
                trace_id,  # trace_id
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

    async def store_trace(
        self,
        trace: dict[str, Any],
        tenant_id: str,
        stored_by: str | None = None,
        redact_pii: bool = True,
    ) -> str:
        """
        Store a trace from SDK or simulation.

        Args:
            trace: Complete trace object
            tenant_id: Tenant for isolation
            stored_by: User ID who stored the trace
            redact_pii: Apply PII redaction before storage

        Returns:
            trace_id
        """
        pool = await self._get_pool()

        # Generate trace_id if not present
        trace_id = trace.get("trace_id") or f"trace_{uuid.uuid4().hex[:16]}"
        run_id = trace.get("run_id") or trace.get("trace_id") or trace_id

        # Redact PII before storage
        if redact_pii:
            trace = redact_trace_data(trace)

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO aos_traces (
                    trace_id, run_id, correlation_id, tenant_id, agent_id,
                    plan_id, seed, frozen_timestamp, root_hash, plan_hash,
                    schema_version, plan, trace, metadata, status,
                    started_at, completed_at, stored_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                ON CONFLICT (trace_id) DO UPDATE SET
                    trace = EXCLUDED.trace,
                    metadata = EXCLUDED.metadata,
                    status = EXCLUDED.status,
                    completed_at = EXCLUDED.completed_at,
                    root_hash = EXCLUDED.root_hash
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
            )

            # Store steps separately for efficient querying
            steps = trace.get("steps", [])
            for step in steps:
                await conn.execute(
                    """
                    INSERT INTO aos_trace_steps (
                        trace_id, step_index, skill_id, skill_name, params,
                        status, outcome_category, outcome_code, outcome_data,
                        cost_cents, duration_ms, retry_count,
                        input_hash, output_hash, rng_state_before,
                        idempotency_key, replay_behavior, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                    ON CONFLICT (trace_id, step_index) DO UPDATE SET
                        status = EXCLUDED.status,
                        outcome_data = EXCLUDED.outcome_data,
                        output_hash = EXCLUDED.output_hash
                    """,
                    trace_id,
                    step.get("step_index", 0),
                    step.get("skill_id", step.get("skill_name", "unknown")),
                    step.get("skill_name", "unknown"),
                    json.dumps(step.get("params", {})),
                    step.get("status", "success"),
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
        """Delete trace by ID."""
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
