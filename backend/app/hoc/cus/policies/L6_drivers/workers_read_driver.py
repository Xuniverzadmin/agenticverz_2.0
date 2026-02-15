# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: L4 handler call
#   Execution: async
# Role: Workers domain read-only DB queries for worker runs, cost data, and retry operations
# Callers: L4 handlers (via policies_handler.py)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: L2 first-principles purity enforcement, PIN-520
# artifact_class: CODE

"""
Workers Read Driver (L6)

Provides async DB read operations for worker domain data.
Extracted from L2 workers.py to enforce L2 first-principles purity
(zero session.execute() calls in L2).

All methods accept an AsyncSession and return plain dicts or primitives.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession


class WorkersReadDriver:
    """Async DB read operations for workers domain."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # =========================================================================
    # Worker Runs
    # =========================================================================

    async def verify_run_exists(self, run_id: str) -> bool:
        """
        Verify that a worker_run exists by ID.
        Used for VERIFICATION_MODE persistence checks.
        """
        result = await self._session.execute(
            text("SELECT id FROM worker_runs WHERE id = :run_id"),
            {"run_id": run_id},
        )
        return result.scalar_one_or_none() is not None

    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a worker run by ID.
        Returns dict format matching WorkerRunResponse for API compatibility.
        """
        result = await self._session.execute(
            text(
                "SELECT id, task, status, success, error, output_json, "
                "replay_token_json, total_tokens, total_latency_ms, created_at "
                "FROM worker_runs WHERE id = :run_id"
            ),
            {"run_id": run_id},
        )
        row = result.mappings().first()

        if not row:
            return None

        return {
            "run_id": row["id"],
            "task": row["task"],
            "status": row["status"],
            "success": row["success"],
            "error": row["error"],
            "artifacts": json.loads(row["output_json"]) if row["output_json"] else None,
            "replay_token": json.loads(row["replay_token_json"]) if row["replay_token_json"] else None,
            "total_tokens_used": row["total_tokens"] or 0,
            "total_latency_ms": float(row["total_latency_ms"]) if row["total_latency_ms"] else 0.0,
            "policy_violations": [],  # Not stored in detail
            "recovery_log": [],  # Not stored in detail
            "drift_metrics": {},
            "execution_trace": [],
            "routing_decisions": [],
            "cost_report": None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }

    async def list_runs(
        self,
        limit: int = 20,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List recent worker runs from PostgreSQL.
        Optionally filter by tenant_id.
        """
        params: Dict[str, Any] = {"limit_val": limit}
        tenant_filter = ""
        if tenant_id:
            tenant_filter = " WHERE tenant_id = :tenant_id"
            params["tenant_id"] = tenant_id

        result = await self._session.execute(
            text(
                "SELECT id, task, status, success, created_at, total_latency_ms "
                f"FROM worker_runs{tenant_filter} "
                "ORDER BY created_at DESC LIMIT :limit_val"
            ),
            params,
        )
        rows = result.mappings().all()

        return [
            {
                "run_id": row["id"],
                "task": row["task"],
                "status": row["status"],
                "success": row["success"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else "",
                "total_latency_ms": float(row["total_latency_ms"]) if row["total_latency_ms"] else None,
            }
            for row in rows
        ]

    async def count_runs(self) -> int:
        """Count total worker runs for health check."""
        result = await self._session.execute(
            text("SELECT COUNT(*) FROM worker_runs")
        )
        return result.scalar() or 0

    # =========================================================================
    # Cost Budget & Spend
    # =========================================================================

    async def get_active_tenant_budget(
        self, tenant_id: str, budget_type: str = "tenant"
    ) -> Optional[Dict[str, Any]]:
        """
        Get tenant's active cost budget.
        Returns dict with id, daily_limit_cents, warn_threshold_pct, hard_limit_enabled.
        """
        result = await self._session.execute(
            text(
                "SELECT id, daily_limit_cents, warn_threshold_pct, hard_limit_enabled "
                "FROM cost_budgets "
                "WHERE tenant_id = :tenant_id AND is_active = true AND budget_type = :budget_type"
            ),
            {"tenant_id": tenant_id, "budget_type": budget_type},
        )
        row = result.mappings().first()

        if not row:
            return None

        return {
            "id": row["id"],
            "daily_limit_cents": row["daily_limit_cents"],
            "warn_threshold_pct": row["warn_threshold_pct"],
            "hard_limit_enabled": row["hard_limit_enabled"],
        }

    async def get_daily_spend(self, tenant_id: str, today_start: datetime) -> int:
        """
        Calculate today's total spend in cents.
        """
        result = await self._session.execute(
            text(
                "SELECT COALESCE(SUM(cost_cents), 0) "
                "FROM cost_records "
                "WHERE tenant_id = :tenant_id "
                "AND created_at >= :today_start"
            ),
            {"tenant_id": tenant_id, "today_start": today_start},
        )
        return int(result.scalar() or 0)

    # =========================================================================
    # Cost Advisories
    # =========================================================================

    async def get_existing_advisory(self, run_id: str) -> Optional[str]:
        """
        Check if a cost advisory already exists for a run.
        Returns advisory ID if exists, None otherwise.
        """
        result = await self._session.execute(
            text(
                "SELECT id FROM cost_anomalies "
                "WHERE anomaly_type = 'BUDGET_WARNING' "
                "AND metadata->>'run_id' = :run_id"
            ),
            {"run_id": run_id},
        )
        return result.scalar_one_or_none()

    async def count_advisories(self, tenant_id: str, run_id: str) -> int:
        """
        Count advisories for a run/tenant combination.
        Used for S2 advisory invariant verification.
        """
        result = await self._session.execute(
            text(
                "SELECT COUNT(*) "
                "FROM cost_anomalies "
                "WHERE tenant_id = :tenant_id "
                "AND anomaly_type = 'BUDGET_WARNING' "
                "AND metadata->>'run_id' = :run_id"
            ),
            {"tenant_id": tenant_id, "run_id": run_id},
        )
        return int(result.scalar() or 0)

    # =========================================================================
    # Run Retry Operations (reads the `runs` table, not `worker_runs`)
    # =========================================================================

    async def get_run_for_retry(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get run from the `runs` table for retry operation.
        Returns dict with run metadata needed for creating retry run.
        """
        result = await self._session.execute(
            text(
                "SELECT id, agent_id, goal, status, tenant_id, max_attempts, priority "
                "FROM runs WHERE id = :run_id"
            ),
            {"run_id": run_id},
        )
        row = result.mappings().first()

        if not row:
            return None

        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "goal": row["goal"],
            "status": row["status"],
            "tenant_id": row["tenant_id"],
            "max_attempts": row["max_attempts"],
            "priority": row["priority"],
        }

    async def insert_retry_run(
        self,
        new_run_id: str,
        agent_id: str,
        goal: str,
        parent_run_id: str,
        tenant_id: str,
        max_attempts: Optional[int],
        priority: Optional[int],
        created_at: datetime,
    ) -> None:
        """
        Insert a new retry run linked to the original.
        This is a write operation in the read driver for transaction cohesion.
        """
        await self._session.execute(
            text(
                "INSERT INTO runs (id, agent_id, goal, status, parent_run_id, "
                "tenant_id, max_attempts, priority, created_at, origin_system_id) "
                "VALUES (:id, :agent_id, :goal, :status, :parent_run_id, "
                ":tenant_id, :max_attempts, :priority, :created_at, :origin_system_id)"
            ),
            {
                "id": new_run_id,
                "agent_id": agent_id,
                "goal": goal,
                "status": "queued",
                "parent_run_id": parent_run_id,
                "tenant_id": tenant_id,
                "max_attempts": max_attempts,
                "priority": priority,
                "created_at": created_at,
                "origin_system_id": "policy-retry",
            },
        )


def get_workers_read_driver(session: AsyncSession) -> WorkersReadDriver:
    """Factory function to create a WorkersReadDriver instance."""
    return WorkersReadDriver(session)
