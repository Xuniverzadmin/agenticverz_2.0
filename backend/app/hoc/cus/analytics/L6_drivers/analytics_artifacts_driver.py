# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: engine
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: analytics_artifacts
#   Writes: analytics_artifacts
# Role: Analytics artifact reproducibility persistence (UC-MON-06)
# Callers: analytics_handler.py (L4)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Migration 131, UC-MON Analytics Reproducibility
# artifact_class: CODE

"""
Analytics Artifacts Driver (L6 Data Access)

Handles persistence of analytics artifact metadata for reproducible computation:
- dataset_version: Version of the dataset used
- input_window_hash: Deterministic hash of the input window
- compute_code_version: Version of the compute code
- as_of: Point-in-time snapshot timestamp

L6 INVARIANT: Never commit/rollback — L4 owns transaction boundaries.
"""

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsArtifactsDriver:
    """L6 Driver for analytics artifact reproducibility persistence."""

    async def save_artifact(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        dataset_id: str,
        dataset_version: str,
        input_window_hash: str,
        as_of: str,
        compute_code_version: str,
    ) -> dict[str, Any]:
        """Save an analytics artifact record. Returns the inserted row."""
        result = await session.execute(
            text("""
                INSERT INTO analytics_artifacts
                    (tenant_id, dataset_id, dataset_version, input_window_hash,
                     as_of, compute_code_version)
                VALUES
                    (:tenant_id, :dataset_id, :dataset_version, :input_window_hash,
                     :as_of::timestamptz, :compute_code_version)
                ON CONFLICT ON CONSTRAINT uq_analytics_artifacts_tenant_dataset_version
                DO UPDATE SET
                    input_window_hash = EXCLUDED.input_window_hash,
                    as_of = EXCLUDED.as_of,
                    compute_code_version = EXCLUDED.compute_code_version
                RETURNING id, tenant_id, dataset_id, dataset_version,
                          input_window_hash, as_of, compute_code_version, created_at
            """),
            {
                "tenant_id": tenant_id,
                "dataset_id": dataset_id,
                "dataset_version": dataset_version,
                "input_window_hash": input_window_hash,
                "as_of": as_of,
                "compute_code_version": compute_code_version,
            },
        )
        row = result.mappings().first()
        return dict(row) if row else {}

    async def get_artifact(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        dataset_id: str,
        dataset_version: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Query analytics artifacts with optional version filter."""
        conditions = ["tenant_id = :tenant_id", "dataset_id = :dataset_id"]
        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "dataset_id": dataset_id,
        }

        if dataset_version:
            conditions.append("dataset_version = :dataset_version")
            params["dataset_version"] = dataset_version

        where_clause = " AND ".join(conditions)
        result = await session.execute(
            text(f"""
                SELECT id, tenant_id, dataset_id, dataset_version,
                       input_window_hash, as_of, compute_code_version, created_at
                FROM analytics_artifacts
                WHERE {where_clause}
                ORDER BY created_at DESC
            """),
            params,
        )
        return [dict(row) for row in result.mappings().all()]

    async def list_artifacts(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List all analytics artifacts for a tenant."""
        result = await session.execute(
            text("""
                SELECT id, tenant_id, dataset_id, dataset_version,
                       input_window_hash, as_of, compute_code_version, created_at
                FROM analytics_artifacts
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"tenant_id": tenant_id, "limit": limit},
        )
        return [dict(row) for row in result.mappings().all()]
