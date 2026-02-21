# capability_id: CAP-005
# Layer: L5 — Domain Engine
# AUDIENCE: FOUNDER
# Role: Founder timeline decision record queries (READ-ONLY)
# Callers: L4 handler (fdr_timeline_handler)
# Forbidden Imports: L1, L2
# artifact_class: CODE

"""
Founder Timeline Engine (L5)

Raw chronological consumption of decision records.
No grouping, no collapsing, no interpretation.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("nova.hoc.fdr.timeline_engine")


def _sql_text(query: str):
    from sqlalchemy import text as _text

    return _text(query)


class TimelineEngine:
    """READ-ONLY engine for decision record timeline."""

    async def fetch_run_data(
        self, session: Any, *, run_id: str
    ) -> Optional[dict[str, Any]]:
        result = await session.execute(
            _sql_text("""
                SELECT id, agent_id, goal, status, attempts, max_attempts,
                    error_message, priority, tenant_id, idempotency_key,
                    parent_run_id, created_at, started_at, completed_at, duration_ms
                FROM runs WHERE id = :run_id
            """),
            {"run_id": run_id},
        )
        row = result.fetchone()
        if not row:
            return None
        return {
            "id": row.id, "agent_id": row.agent_id, "goal": row.goal,
            "status": row.status, "attempts": row.attempts,
            "max_attempts": row.max_attempts, "error_message": row.error_message,
            "priority": row.priority, "tenant_id": row.tenant_id,
            "idempotency_key": row.idempotency_key,
            "parent_run_id": row.parent_run_id, "created_at": row.created_at,
            "started_at": row.started_at, "completed_at": row.completed_at,
            "duration_ms": row.duration_ms,
        }

    async def fetch_decision_records(
        self, session: Any, *, run_id: str
    ) -> list[dict[str, Any]]:
        result = await session.execute(
            _sql_text("""
                SELECT decision_id, decision_type, decision_source, decision_trigger,
                    decision_inputs, decision_outcome, decision_reason, run_id,
                    workflow_id, tenant_id, request_id, causal_role, decided_at, details
                FROM contracts.decision_records
                WHERE run_id = :run_id ORDER BY decided_at ASC
            """),
            {"run_id": run_id},
        )
        records = []
        for row in result:
            records.append({
                "decision_id": row.decision_id, "decision_type": row.decision_type,
                "decision_source": row.decision_source,
                "decision_trigger": row.decision_trigger,
                "decision_inputs": row.decision_inputs or {},
                "decision_outcome": row.decision_outcome,
                "decision_reason": row.decision_reason,
                "run_id": row.run_id, "workflow_id": row.workflow_id,
                "tenant_id": row.tenant_id, "request_id": row.request_id,
                "causal_role": row.causal_role, "decided_at": row.decided_at,
                "details": row.details or {},
            })
        return records

    async def fetch_all_decision_records(
        self,
        session: Any,
        *,
        limit: int = 100,
        offset: int = 0,
        decision_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        where_clauses = ["1=1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if decision_type:
            where_clauses.append("decision_type = :decision_type")
            params["decision_type"] = decision_type
        if tenant_id:
            where_clauses.append("tenant_id = :tenant_id")
            params["tenant_id"] = tenant_id
        where_sql = " AND ".join(where_clauses)

        result = await session.execute(
            _sql_text(f"""
                SELECT decision_id, decision_type, decision_source, decision_trigger,
                    decision_inputs, decision_outcome, decision_reason, run_id,
                    workflow_id, tenant_id, request_id, causal_role, decided_at, details
                FROM contracts.decision_records
                WHERE {where_sql} ORDER BY decided_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        )
        records = []
        for row in result:
            records.append({
                "decision_id": row.decision_id, "decision_type": row.decision_type,
                "decision_source": row.decision_source,
                "decision_trigger": row.decision_trigger,
                "decision_inputs": row.decision_inputs or {},
                "decision_outcome": row.decision_outcome,
                "decision_reason": row.decision_reason,
                "run_id": row.run_id, "workflow_id": row.workflow_id,
                "tenant_id": row.tenant_id, "request_id": row.request_id,
                "causal_role": row.causal_role, "decided_at": row.decided_at,
                "details": row.details or {},
            })
        return records

    async def get_single_decision_record(
        self, session: Any, *, decision_id: str
    ) -> Optional[dict[str, Any]]:
        result = await session.execute(
            _sql_text("""
                SELECT decision_id, decision_type, decision_source, decision_trigger,
                    decision_inputs, decision_outcome, decision_reason, run_id,
                    workflow_id, tenant_id, request_id, causal_role, decided_at, details
                FROM contracts.decision_records WHERE decision_id = :decision_id
            """),
            {"decision_id": decision_id},
        )
        row = result.fetchone()
        if not row:
            return None
        return {
            "decision_id": row.decision_id, "decision_type": row.decision_type,
            "decision_source": row.decision_source,
            "decision_trigger": row.decision_trigger,
            "decision_inputs": row.decision_inputs or {},
            "decision_outcome": row.decision_outcome,
            "decision_reason": row.decision_reason,
            "run_id": row.run_id, "workflow_id": row.workflow_id,
            "tenant_id": row.tenant_id, "request_id": row.request_id,
            "causal_role": row.causal_role, "decided_at": row.decided_at,
            "details": row.details or {},
        }

    async def count_decision_records(
        self,
        session: Any,
        *,
        decision_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> int:
        where_clauses = ["1=1"]
        params: dict[str, Any] = {}
        if decision_type:
            where_clauses.append("decision_type = :decision_type")
            params["decision_type"] = decision_type
        if tenant_id:
            where_clauses.append("tenant_id = :tenant_id")
            params["tenant_id"] = tenant_id
        where_sql = " AND ".join(where_clauses)

        result = await session.execute(
            _sql_text(f"SELECT COUNT(*) FROM contracts.decision_records WHERE {where_sql}"),
            params,
        )
        return result.scalar() or 0


def get_timeline_engine() -> TimelineEngine:
    return TimelineEngine()
