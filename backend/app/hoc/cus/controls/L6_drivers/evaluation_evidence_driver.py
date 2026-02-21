# capability_id: CAP-009
# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: engine
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: controls_evaluation_evidence
#   Writes: controls_evaluation_evidence
# Role: Controls evaluation evidence persistence (UC-MON binding fields)
# Callers: controls_handler.py (L4)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Migration 130, UC-MON Controls Evaluation
# artifact_class: CODE

"""
Controls Evaluation Evidence Driver (L6 Data Access)

Handles persistence of per-run control evaluation evidence with version binding:
- control_set_version: Version of the control set at evaluation time
- override_ids_applied: JSON array of override IDs active during evaluation
- resolver_version: Version of the resolver algorithm used
- decision: Evaluation outcome (ALLOWED, BLOCKED, THROTTLED, etc.)

L6 INVARIANT: Never commit/rollback — L4 owns transaction boundaries.
"""

import json
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ControlsEvaluationEvidenceDriver:
    """L6 Driver for controls evaluation evidence persistence."""

    async def record_evidence(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        run_id: str,
        control_set_version: str,
        override_ids_applied: list[str],
        resolver_version: str,
        decision: str,
    ) -> dict[str, Any]:
        """Record per-run controls evaluation evidence. Returns the inserted row."""
        result = await session.execute(
            text("""
                INSERT INTO controls_evaluation_evidence
                    (tenant_id, run_id, control_set_version, override_ids_applied,
                     resolver_version, decision, evaluated_at)
                VALUES
                    (:tenant_id, :run_id, :control_set_version,
                     :override_ids_applied::jsonb, :resolver_version, :decision, NOW())
                RETURNING id, tenant_id, run_id, control_set_version,
                          override_ids_applied, resolver_version, decision, evaluated_at
            """),
            {
                "tenant_id": tenant_id,
                "run_id": run_id,
                "control_set_version": control_set_version,
                "override_ids_applied": json.dumps(override_ids_applied),
                "resolver_version": resolver_version,
                "decision": decision,
            },
        )
        row = result.mappings().first()
        return dict(row) if row else {}

    async def query_evidence(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        run_id: Optional[str] = None,
        control_set_version: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query evaluation evidence with optional filters."""
        conditions = ["tenant_id = :tenant_id"]
        params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}

        if run_id:
            conditions.append("run_id = :run_id")
            params["run_id"] = run_id
        if control_set_version:
            conditions.append("control_set_version = :control_set_version")
            params["control_set_version"] = control_set_version

        where_clause = " AND ".join(conditions)
        result = await session.execute(
            text(f"""
                SELECT id, tenant_id, run_id, control_set_version,
                       override_ids_applied, resolver_version, decision, evaluated_at
                FROM controls_evaluation_evidence
                WHERE {where_clause}
                ORDER BY evaluated_at DESC
                LIMIT :limit
            """),
            params,
        )
        return [dict(row) for row in result.mappings().all()]
