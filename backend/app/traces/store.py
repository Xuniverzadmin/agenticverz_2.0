# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Trace store abstraction
# Callers: services, workers
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Trace System

"""
Trace Storage for AOS
M6 Deliverable: Run traces with correlation IDs

Provides persistent storage for execution traces used in:
- Debugging and inspection
- Replay verification
- Determinism testing
"""

import asyncio
import json
import sqlite3
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import TraceRecord, TraceStatus, TraceStep, TraceSummary


class TraceStore(ABC):
    """Abstract base class for trace storage."""

    @abstractmethod
    async def start_trace(
        self,
        run_id: str,
        correlation_id: str,
        tenant_id: str,
        agent_id: str | None,
        plan: list[dict[str, Any]],
    ) -> None:
        """Start a new trace record."""
        ...

    @abstractmethod
    async def record_step(
        self,
        run_id: str,
        step_index: int,
        skill_name: str,
        params: dict[str, Any],
        status: TraceStatus,
        outcome_category: str,
        outcome_code: str | None,
        outcome_data: dict[str, Any] | None,
        cost_cents: float,
        duration_ms: float,
        retry_count: int,
    ) -> None:
        """Record a step in the trace."""
        ...

    @abstractmethod
    async def complete_trace(
        self,
        run_id: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark a trace as completed."""
        ...

    @abstractmethod
    async def get_trace(self, run_id: str) -> TraceRecord | None:
        """Get a complete trace by run_id."""
        ...

    @abstractmethod
    async def list_traces(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TraceSummary]:
        """List traces, optionally filtered by tenant."""
        ...

    @abstractmethod
    async def delete_trace(self, run_id: str) -> bool:
        """Delete a trace by run_id."""
        ...


class SQLiteTraceStore(TraceStore):
    """
    SQLite-based trace storage.

    Default storage for v1. Simple, local, and sufficient for
    single-instance deployments.
    """

    def __init__(self, db_path: str | Path = "/var/lib/aos/traces.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    run_id TEXT PRIMARY KEY,
                    correlation_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    agent_id TEXT,
                    plan TEXT NOT NULL,
                    plan_hash TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL DEFAULT 'running',
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    -- v1.1 determinism fields
                    seed INTEGER DEFAULT 42,
                    frozen_timestamp TEXT,
                    root_hash TEXT
                );

                CREATE TABLE IF NOT EXISTS trace_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    skill_name TEXT NOT NULL,
                    params TEXT NOT NULL,
                    status TEXT NOT NULL,
                    outcome_category TEXT NOT NULL,
                    outcome_code TEXT,
                    outcome_data TEXT,
                    cost_cents REAL NOT NULL,
                    duration_ms REAL NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    timestamp TEXT NOT NULL,
                    -- v1.1 idempotency fields
                    idempotency_key TEXT,
                    replay_behavior TEXT DEFAULT 'execute',
                    input_hash TEXT,
                    output_hash TEXT,
                    rng_state_before TEXT,
                    FOREIGN KEY (run_id) REFERENCES traces(run_id) ON DELETE CASCADE,
                    UNIQUE(run_id, step_index)
                );

                -- Existing indexes
                CREATE INDEX IF NOT EXISTS idx_traces_tenant ON traces(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_traces_correlation ON traces(correlation_id);
                CREATE INDEX IF NOT EXISTS idx_traces_started ON traces(started_at DESC);
                CREATE INDEX IF NOT EXISTS idx_steps_run ON trace_steps(run_id);

                -- v1.1 indexes for query API
                CREATE INDEX IF NOT EXISTS idx_traces_plan_hash ON traces(plan_hash);
                CREATE INDEX IF NOT EXISTS idx_traces_root_hash ON traces(root_hash);
                CREATE INDEX IF NOT EXISTS idx_traces_seed ON traces(seed);
                CREATE INDEX IF NOT EXISTS idx_traces_agent ON traces(agent_id);
                CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
                CREATE INDEX IF NOT EXISTS idx_steps_idempotency ON trace_steps(idempotency_key);
            """
            )
            conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def start_trace(
        self,
        run_id: str,
        correlation_id: str,
        tenant_id: str,
        agent_id: str | None,
        plan: list[dict[str, Any]],
    ) -> None:
        """Start a new trace record."""

        def _insert():
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO traces (run_id, correlation_id, tenant_id, agent_id, plan, started_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'running')
                    """,
                    (
                        run_id,
                        correlation_id,
                        tenant_id,
                        agent_id,
                        json.dumps(plan),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()

        await asyncio.to_thread(_insert)

    async def record_step(
        self,
        run_id: str,
        step_index: int,
        skill_name: str,
        params: dict[str, Any],
        status: TraceStatus,
        outcome_category: str,
        outcome_code: str | None,
        outcome_data: dict[str, Any] | None,
        cost_cents: float,
        duration_ms: float,
        retry_count: int,
    ) -> None:
        """Record a step in the trace."""

        def _insert():
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO trace_steps
                    (run_id, step_index, skill_name, params, status, outcome_category,
                     outcome_code, outcome_data, cost_cents, duration_ms, retry_count, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        step_index,
                        skill_name,
                        json.dumps(params),
                        status.value,
                        outcome_category,
                        outcome_code,
                        json.dumps(outcome_data) if outcome_data else None,
                        cost_cents,
                        duration_ms,
                        retry_count,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()

        await asyncio.to_thread(_insert)

    async def complete_trace(
        self,
        run_id: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark a trace as completed."""

        def _update():
            with self._get_conn() as conn:
                conn.execute(
                    """
                    UPDATE traces
                    SET completed_at = ?, status = ?, metadata = ?
                    WHERE run_id = ?
                    """,
                    (datetime.now(timezone.utc).isoformat(), status, json.dumps(metadata or {}), run_id),
                )
                conn.commit()

        await asyncio.to_thread(_update)

    async def get_trace(self, run_id: str) -> TraceRecord | None:
        """Get a complete trace by run_id."""

        def _fetch():
            with self._get_conn() as conn:
                # Get trace record
                row = conn.execute("SELECT * FROM traces WHERE run_id = ?", (run_id,)).fetchone()

                if not row:
                    return None

                # Get steps
                steps_rows = conn.execute(
                    "SELECT * FROM trace_steps WHERE run_id = ? ORDER BY step_index", (run_id,)
                ).fetchall()

                steps = [
                    TraceStep(
                        step_index=s["step_index"],
                        skill_name=s["skill_name"],
                        params=json.loads(s["params"]),
                        status=TraceStatus(s["status"]),
                        outcome_category=s["outcome_category"],
                        outcome_code=s["outcome_code"],
                        outcome_data=json.loads(s["outcome_data"]) if s["outcome_data"] else None,
                        cost_cents=s["cost_cents"],
                        duration_ms=s["duration_ms"],
                        retry_count=s["retry_count"],
                        timestamp=datetime.fromisoformat(s["timestamp"]),
                    )
                    for s in steps_rows
                ]

                return TraceRecord(
                    run_id=row["run_id"],
                    correlation_id=row["correlation_id"],
                    tenant_id=row["tenant_id"],
                    agent_id=row["agent_id"],
                    plan=json.loads(row["plan"]),
                    steps=steps,
                    started_at=datetime.fromisoformat(row["started_at"]),
                    completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                    status=row["status"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )

        return await asyncio.to_thread(_fetch)

    async def list_traces(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TraceSummary]:
        """List traces, optionally filtered by tenant."""

        def _fetch():
            with self._get_conn() as conn:
                if tenant_id:
                    rows = conn.execute(
                        """
                        SELECT t.*,
                               COUNT(s.id) as total_steps,
                               SUM(CASE WHEN s.status = 'success' THEN 1 ELSE 0 END) as success_count,
                               SUM(CASE WHEN s.status = 'failure' THEN 1 ELSE 0 END) as failure_count,
                               SUM(s.cost_cents) as total_cost_cents,
                               SUM(s.duration_ms) as total_duration_ms
                        FROM traces t
                        LEFT JOIN trace_steps s ON t.run_id = s.run_id
                        WHERE t.tenant_id = ?
                        GROUP BY t.run_id
                        ORDER BY t.started_at DESC
                        LIMIT ? OFFSET ?
                        """,
                        (tenant_id, limit, offset),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT t.*,
                               COUNT(s.id) as total_steps,
                               SUM(CASE WHEN s.status = 'success' THEN 1 ELSE 0 END) as success_count,
                               SUM(CASE WHEN s.status = 'failure' THEN 1 ELSE 0 END) as failure_count,
                               SUM(s.cost_cents) as total_cost_cents,
                               SUM(s.duration_ms) as total_duration_ms
                        FROM traces t
                        LEFT JOIN trace_steps s ON t.run_id = s.run_id
                        GROUP BY t.run_id
                        ORDER BY t.started_at DESC
                        LIMIT ? OFFSET ?
                        """,
                        (limit, offset),
                    ).fetchall()

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
                        started_at=datetime.fromisoformat(row["started_at"]),
                        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                        status=row["status"],
                    )
                    for row in rows
                ]

        return await asyncio.to_thread(_fetch)

    async def delete_trace(self, run_id: str) -> bool:
        """Delete a trace by run_id."""

        def _delete():
            with self._get_conn() as conn:
                cursor = conn.execute("DELETE FROM traces WHERE run_id = ?", (run_id,))
                conn.commit()
                return cursor.rowcount > 0

        return await asyncio.to_thread(_delete)

    async def get_trace_count(self, tenant_id: str | None = None) -> int:
        """Get total trace count."""

        def _count():
            with self._get_conn() as conn:
                if tenant_id:
                    row = conn.execute("SELECT COUNT(*) FROM traces WHERE tenant_id = ?", (tenant_id,)).fetchone()
                else:
                    row = conn.execute("SELECT COUNT(*) FROM traces").fetchone()
                return row[0]

        return await asyncio.to_thread(_count)

    async def cleanup_old_traces(self, days: int = 30) -> int:
        """Delete traces older than specified days."""

        def _cleanup():
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM traces
                    WHERE started_at < datetime('now', ?)
                    """,
                    (f"-{days} days",),
                )
                conn.commit()
                return cursor.rowcount

        return await asyncio.to_thread(_cleanup)

    # =========================================================================
    # v1.1 Query API Methods
    # =========================================================================

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
        """
        Search traces with multiple filter criteria.

        Args:
            tenant_id: Filter by tenant
            agent_id: Filter by agent
            root_hash: Filter by deterministic root hash
            plan_hash: Filter by plan hash
            seed: Filter by random seed
            status: Filter by status (running, completed, failed)
            from_date: Filter by start date (ISO8601)
            to_date: Filter by end date (ISO8601)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of matching trace summaries
        """

        def _search():
            conditions = []
            params = []

            if tenant_id:
                conditions.append("t.tenant_id = ?")
                params.append(tenant_id)

            if agent_id:
                conditions.append("t.agent_id = ?")
                params.append(agent_id)

            if root_hash:
                conditions.append("t.root_hash = ?")
                params.append(root_hash)

            if plan_hash:
                conditions.append("t.plan_hash = ?")
                params.append(plan_hash)

            if seed is not None:
                conditions.append("t.seed = ?")
                params.append(seed)

            if status:
                conditions.append("t.status = ?")
                params.append(status)

            if from_date:
                conditions.append("t.started_at >= ?")
                params.append(from_date)

            if to_date:
                conditions.append("t.started_at <= ?")
                params.append(to_date)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            with self._get_conn() as conn:
                rows = conn.execute(
                    f"""
                    SELECT t.*,
                           COUNT(s.id) as total_steps,
                           SUM(CASE WHEN s.status = 'success' THEN 1 ELSE 0 END) as success_count,
                           SUM(CASE WHEN s.status = 'failure' THEN 1 ELSE 0 END) as failure_count,
                           SUM(s.cost_cents) as total_cost_cents,
                           SUM(s.duration_ms) as total_duration_ms
                    FROM traces t
                    LEFT JOIN trace_steps s ON t.run_id = s.run_id
                    WHERE {where_clause}
                    GROUP BY t.run_id
                    ORDER BY t.started_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    params + [limit, offset],
                ).fetchall()

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
                        started_at=datetime.fromisoformat(row["started_at"]),
                        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                        status=row["status"],
                    )
                    for row in rows
                ]

        return await asyncio.to_thread(_search)

    async def get_trace_by_root_hash(self, root_hash: str) -> TraceRecord | None:
        """Get a trace by its deterministic root hash."""

        def _fetch():
            with self._get_conn() as conn:
                row = conn.execute("SELECT run_id FROM traces WHERE root_hash = ? LIMIT 1", (root_hash,)).fetchone()
                return row["run_id"] if row else None

        run_id = await asyncio.to_thread(_fetch)
        if run_id:
            return await self.get_trace(run_id)
        return None

    async def find_matching_traces(
        self,
        plan_hash: str,
        seed: int,
    ) -> list[TraceSummary]:
        """
        Find traces with matching plan and seed (for replay verification).

        Two traces with same plan_hash and seed should produce identical root_hash.
        """
        return await self.search_traces(plan_hash=plan_hash, seed=seed)

    async def update_trace_determinism(
        self,
        run_id: str,
        seed: int,
        frozen_timestamp: str | None,
        root_hash: str,
        plan_hash: str,
    ) -> None:
        """Update determinism fields after trace finalization."""

        def _update():
            with self._get_conn() as conn:
                conn.execute(
                    """
                    UPDATE traces
                    SET seed = ?, frozen_timestamp = ?, root_hash = ?, plan_hash = ?
                    WHERE run_id = ?
                    """,
                    (seed, frozen_timestamp, root_hash, plan_hash, run_id),
                )
                conn.commit()

        await asyncio.to_thread(_update)


class InMemoryTraceStore(TraceStore):
    """
    In-memory trace storage for testing.

    All data is lost when the process exits.
    """

    def __init__(self):
        self._traces: dict[str, TraceRecord] = {}
        self._steps: dict[str, list[TraceStep]] = {}

    async def start_trace(
        self,
        run_id: str,
        correlation_id: str,
        tenant_id: str,
        agent_id: str | None,
        plan: list[dict[str, Any]],
    ) -> None:
        self._traces[run_id] = TraceRecord(
            run_id=run_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            plan=plan,
            steps=[],
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            status="running",
        )
        self._steps[run_id] = []

    async def record_step(
        self,
        run_id: str,
        step_index: int,
        skill_name: str,
        params: dict[str, Any],
        status: TraceStatus,
        outcome_category: str,
        outcome_code: str | None,
        outcome_data: dict[str, Any] | None,
        cost_cents: float,
        duration_ms: float,
        retry_count: int,
    ) -> None:
        step = TraceStep(
            step_index=step_index,
            skill_name=skill_name,
            params=params,
            status=status,
            outcome_category=outcome_category,
            outcome_code=outcome_code,
            outcome_data=outcome_data,
            cost_cents=cost_cents,
            duration_ms=duration_ms,
            retry_count=retry_count,
        )

        if run_id in self._steps:
            # Replace if exists, append otherwise
            existing = [s for s in self._steps[run_id] if s.step_index != step_index]
            existing.append(step)
            existing.sort(key=lambda s: s.step_index)
            self._steps[run_id] = existing

    async def complete_trace(
        self,
        run_id: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if run_id in self._traces:
            trace = self._traces[run_id]
            self._traces[run_id] = TraceRecord(
                run_id=trace.run_id,
                correlation_id=trace.correlation_id,
                tenant_id=trace.tenant_id,
                agent_id=trace.agent_id,
                plan=trace.plan,
                steps=self._steps.get(run_id, []),
                started_at=trace.started_at,
                completed_at=datetime.now(timezone.utc),
                status=status,
                metadata=metadata or {},
            )

    async def get_trace(self, run_id: str) -> TraceRecord | None:
        trace = self._traces.get(run_id)
        if trace:
            # Update steps
            return TraceRecord(
                run_id=trace.run_id,
                correlation_id=trace.correlation_id,
                tenant_id=trace.tenant_id,
                agent_id=trace.agent_id,
                plan=trace.plan,
                steps=self._steps.get(run_id, []),
                started_at=trace.started_at,
                completed_at=trace.completed_at,
                status=trace.status,
                metadata=trace.metadata,
            )
        return None

    async def list_traces(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TraceSummary]:
        traces = list(self._traces.values())
        if tenant_id:
            traces = [t for t in traces if t.tenant_id == tenant_id]

        traces.sort(key=lambda t: t.started_at, reverse=True)
        traces = traces[offset : offset + limit]

        summaries = []
        for t in traces:
            steps = self._steps.get(t.run_id, [])
            summaries.append(
                TraceSummary(
                    run_id=t.run_id,
                    correlation_id=t.correlation_id,
                    tenant_id=t.tenant_id,
                    agent_id=t.agent_id,
                    total_steps=len(steps),
                    success_count=sum(1 for s in steps if s.status == TraceStatus.SUCCESS),
                    failure_count=sum(1 for s in steps if s.status == TraceStatus.FAILURE),
                    total_cost_cents=sum(s.cost_cents for s in steps),
                    total_duration_ms=sum(s.duration_ms for s in steps),
                    started_at=t.started_at,
                    completed_at=t.completed_at,
                    status=t.status,
                )
            )
        return summaries

    async def delete_trace(self, run_id: str) -> bool:
        if run_id in self._traces:
            del self._traces[run_id]
            self._steps.pop(run_id, None)
            return True
        return False


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for tracing."""
    return str(uuid.uuid4())


def generate_run_id() -> str:
    """Generate a unique run ID."""
    return f"run_{uuid.uuid4().hex[:16]}"
