# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: engine
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: v_runs_o2, runs
#   Writes: none
# Role: Activity read data access operations
# Callers: activity_facade.py (L5 engine)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Phase-3B SQLAlchemy Extraction
#
# ============================================================================
# L6 DRIVER INVARIANT — ACTIVITY READ
# ============================================================================
# This driver handles PERSISTENCE only:
# - Query runs (v_runs_o2 view)
# - Query metrics aggregates
# - Query threshold signals
#
# NO BUSINESS LOGIC. Signal computation, risk evaluation, and
# summary generation stay in L5 engine.
# ============================================================================

"""
Activity Read Driver (L6 Data Access)

Handles database operations for activity queries:
- Fetching runs with filters
- Fetching run details
- Fetching metrics aggregates
- Fetching threshold signals

Reference: PIN-470, Phase-3B SQLAlchemy Extraction
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ActivityReadDriver:
    """
    L6 Driver for activity read operations.

    All methods are pure DB operations - no business logic.
    Business decisions (risk computation, signal synthesis) stay in L5.
    """

    def __init__(self, session: AsyncSession):
        """Initialize driver with async session."""
        self._session = session

    async def count_runs(
        self,
        where_sql: str,
        params: dict[str, Any],
    ) -> int:
        """
        Count runs matching filters.

        Args:
            where_sql: WHERE clause SQL
            params: Query parameters

        Returns:
            Total count
        """
        count_sql = f"SELECT COUNT(*) as total FROM v_runs_o2 WHERE {where_sql}"
        result = await self._session.execute(text(count_sql), params)
        return result.scalar() or 0

    async def fetch_runs(
        self,
        where_sql: str,
        params: dict[str, Any],
        sort_by: str,
        sort_dir: str,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        """
        Fetch runs matching filters.

        Args:
            where_sql: WHERE clause SQL
            params: Query parameters
            sort_by: Field to sort by
            sort_dir: Sort direction (ASC/DESC)
            limit: Max rows
            offset: Rows to skip

        Returns:
            List of run dicts
        """
        data_sql = f"""
            SELECT
                run_id, tenant_id, project_id, is_synthetic, source, provider_type,
                state, status, started_at, last_seen_at, completed_at, duration_ms,
                risk_level, latency_bucket, evidence_health, integrity_status,
                incident_count, policy_draft_count, policy_violation,
                input_tokens, output_tokens, estimated_cost_usd
            FROM v_runs_o2
            WHERE {where_sql}
            ORDER BY {sort_by} {sort_dir}
            LIMIT :limit OFFSET :offset
        """
        query_params = {**params, "limit": limit, "offset": offset}
        result = await self._session.execute(text(data_sql), query_params)
        return [dict(row) for row in result.mappings().all()]

    async def fetch_run_detail(
        self,
        tenant_id: str,
        run_id: str,
    ) -> dict[str, Any] | None:
        """
        Fetch single run detail.

        Args:
            tenant_id: Tenant ID for isolation
            run_id: Run ID to fetch

        Returns:
            Run dict or None if not found
        """
        sql = """
            SELECT *
            FROM v_runs_o2
            WHERE run_id = :run_id AND tenant_id = :tenant_id
        """
        result = await self._session.execute(
            text(sql), {"run_id": run_id, "tenant_id": tenant_id}
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def fetch_status_summary(
        self,
        where_sql: str,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Fetch runs grouped by status.

        Args:
            where_sql: WHERE clause SQL
            params: Query parameters

        Returns:
            List of {status, count} dicts
        """
        sql = f"""
            SELECT status, COUNT(*) as count
            FROM v_runs_o2
            WHERE {where_sql}
            GROUP BY status
            ORDER BY count DESC
        """
        result = await self._session.execute(text(sql), params)
        return [dict(row) for row in result.mappings().all()]

    async def fetch_runs_with_policy_context(
        self,
        where_sql: str,
        params: dict[str, Any],
        sort_by: str,
        sort_dir: str,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        """
        Fetch runs with policy context columns.

        Args:
            where_sql: WHERE clause SQL
            params: Query parameters
            sort_by: Field to sort by
            sort_dir: Sort direction (ASC/DESC)
            limit: Max rows
            offset: Rows to skip

        Returns:
            List of run dicts with policy context
        """
        data_sql = f"""
            SELECT
                run_id, tenant_id, project_id, is_synthetic, source, provider_type,
                state, status, started_at, last_seen_at, completed_at, duration_ms,
                risk_level, latency_bucket, evidence_health, integrity_status,
                incident_count, policy_draft_count, policy_violation,
                input_tokens, output_tokens, estimated_cost_usd,
                COALESCE(policy_id, 'default') as policy_id,
                COALESCE(policy_name, 'Default Policy') as policy_name,
                COALESCE(policy_scope, 'TENANT') as policy_scope,
                limit_type,
                threshold_value,
                threshold_unit,
                COALESCE(threshold_source, 'DEFAULT') as threshold_source,
                COALESCE(evaluation_outcome, 'OK') as evaluation_outcome,
                actual_value,
                risk_type,
                proximity_pct
            FROM v_runs_o2
            WHERE {where_sql}
            ORDER BY {sort_by} {sort_dir}
            LIMIT :limit OFFSET :offset
        """
        query_params = {**params, "limit": limit, "offset": offset}
        result = await self._session.execute(text(data_sql), query_params)
        return [dict(row) for row in result.mappings().all()]

    async def fetch_at_risk_runs(
        self,
        where_sql: str,
        params: dict[str, Any],
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        """
        Fetch at-risk runs for signal synthesis.

        Args:
            where_sql: WHERE clause SQL
            params: Query parameters
            limit: Max rows
            offset: Rows to skip

        Returns:
            List of at-risk run dicts
        """
        sql = f"""
            SELECT
                run_id, tenant_id, project_id, is_synthetic, source, provider_type,
                state, status, started_at, risk_level, evidence_health,
                COALESCE(policy_id, 'default') as policy_id,
                COALESCE(policy_name, 'Default Policy') as policy_name,
                COALESCE(policy_scope, 'TENANT') as policy_scope,
                limit_type,
                threshold_value,
                threshold_unit,
                COALESCE(threshold_source, 'DEFAULT') as threshold_source,
                COALESCE(evaluation_outcome, 'OK') as evaluation_outcome,
                actual_value,
                risk_type,
                proximity_pct
            FROM v_runs_o2
            WHERE {where_sql}
            ORDER BY started_at DESC
            LIMIT :limit OFFSET :offset
        """
        query_params = {**params, "limit": limit, "offset": offset}
        result = await self._session.execute(text(sql), query_params)
        return [dict(row) for row in result.mappings().all()]

    async def fetch_metrics(
        self,
        where_sql: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Fetch aggregated metrics.

        Args:
            where_sql: WHERE clause SQL
            params: Query parameters

        Returns:
            Dict with metric counts
        """
        sql = f"""
            SELECT
                COUNT(*) FILTER (WHERE risk_level = 'AT_RISK') as at_risk_count,
                COUNT(*) FILTER (WHERE risk_level = 'VIOLATED') as violated_count,
                COUNT(*) FILTER (WHERE risk_level = 'NEAR_THRESHOLD') as near_threshold_count,
                COUNT(*) FILTER (WHERE risk_level != 'NORMAL') as total_at_risk,
                COUNT(*) FILTER (WHERE state = 'LIVE') as live_count,
                COUNT(*) FILTER (WHERE state = 'COMPLETED') as completed_count,
                COUNT(*) FILTER (WHERE evidence_health = 'FLOWING') as evidence_flowing_count,
                COUNT(*) FILTER (WHERE evidence_health = 'DEGRADED') as evidence_degraded_count,
                COUNT(*) FILTER (WHERE evidence_health = 'MISSING') as evidence_missing_count,
                COUNT(*) FILTER (WHERE risk_type = 'COST') as cost_risk_count,
                COUNT(*) FILTER (WHERE risk_type = 'TIME') as time_risk_count,
                COUNT(*) FILTER (WHERE risk_type = 'TOKENS') as token_risk_count,
                COUNT(*) FILTER (WHERE risk_type = 'RATE') as rate_risk_count
            FROM v_runs_o2
            WHERE {where_sql}
        """
        result = await self._session.execute(text(sql), params)
        row = result.mappings().first()
        return dict(row) if row else {}

    async def fetch_threshold_signals(
        self,
        where_sql: str,
        params: dict[str, Any],
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        """
        Fetch threshold proximity signals.

        Args:
            where_sql: WHERE clause SQL
            params: Query parameters
            limit: Max rows
            offset: Rows to skip

        Returns:
            List of threshold signal dicts
        """
        sql = f"""
            SELECT
                run_id,
                COALESCE(limit_type, 'UNKNOWN') as limit_type,
                COALESCE(proximity_pct, 0) as proximity_pct,
                COALESCE(evaluation_outcome, 'OK') as evaluation_outcome,
                COALESCE(policy_id, 'default') as policy_id,
                COALESCE(policy_name, 'Default Policy') as policy_name,
                COALESCE(policy_scope, 'TENANT') as policy_scope,
                threshold_value,
                threshold_unit,
                COALESCE(threshold_source, 'DEFAULT') as threshold_source,
                actual_value,
                risk_type
            FROM v_runs_o2
            WHERE {where_sql}
            ORDER BY proximity_pct DESC
            LIMIT :limit OFFSET :offset
        """
        query_params = {**params, "limit": limit, "offset": offset}
        result = await self._session.execute(text(sql), query_params)
        return [dict(row) for row in result.mappings().all()]

    async def fetch_dimension_breakdown(
        self,
        dimension: str,
        where_sql: str,
        params: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        """
        Fetch dimension breakdown (GROUP BY dimension).

        Args:
            dimension: Column to group by (must be a valid v_runs_o2 column)
            where_sql: WHERE clause SQL
            params: Query parameters
            limit: Max groups

        Returns:
            List of dicts with 'value' and 'count' keys
        """
        # Allowlist columns to prevent SQL injection via dimension param
        allowed = {
            "risk_level", "latency_bucket", "evidence_health",
            "integrity_status", "source", "provider_type", "status", "state",
        }
        if dimension not in allowed:
            return []

        sql = f"""
            SELECT
                COALESCE({dimension}::text, 'unknown') as value,
                COUNT(*) as count
            FROM v_runs_o2
            WHERE {where_sql}
            GROUP BY {dimension}
            ORDER BY count DESC
            LIMIT :limit
        """
        query_params = {**params, "limit": limit}
        result = await self._session.execute(text(sql), query_params)
        return [dict(row) for row in result.mappings().all()]


def get_activity_read_driver(session: AsyncSession) -> ActivityReadDriver:
    """Get an ActivityReadDriver instance."""
    return ActivityReadDriver(session)
