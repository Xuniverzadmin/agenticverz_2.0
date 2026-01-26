# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: engine
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: cost_records, runs, aos_traces
#   Writes: none
# Role: Analytics read data access operations
# Callers: analytics_facade.py (L5 engine)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Phase-3B SQLAlchemy Extraction
#
# ============================================================================
# L6 DRIVER INVARIANT — ANALYTICS READ
# ============================================================================
# This driver handles PERSISTENCE only:
# - Query cost_records for cost metrics
# - Query runs for LLM usage
# - Query aos_traces for worker execution
#
# NO BUSINESS LOGIC. Time alignment, aggregation, and reconciliation
# stay in L5 engine.
# ============================================================================

"""
Analytics Read Driver (L6 Data Access)

Handles database operations for analytics queries:
- Fetching cost metrics from cost_records
- Fetching LLM usage from runs
- Fetching worker execution from aos_traces
- Fetching cost breakdowns by model and feature

Reference: PIN-470, Phase-3B SQLAlchemy Extraction
"""

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsReadDriver:
    """
    L6 Driver for analytics read operations.

    All methods are pure DB operations - no business logic.
    Business decisions (time alignment, reconciliation) stay in L5.
    """

    def __init__(self, session: AsyncSession):
        """Initialize driver with async session."""
        self._session = session

    async def fetch_cost_metrics(
        self,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        time_trunc: str,
    ) -> list[dict[str, Any]]:
        """
        Fetch cost metrics from cost_records table.

        Args:
            tenant_id: Tenant ID for isolation
            from_ts: Start of time window
            to_ts: End of time window
            time_trunc: Time truncation (hour or day)

        Returns:
            List of {ts, requests, tokens} dicts
        """
        query = text("""
            SELECT
                DATE_TRUNC(:time_trunc, created_at) as ts,
                COUNT(*) as requests,
                COALESCE(SUM(input_tokens + output_tokens), 0) as tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :from_ts
              AND created_at < :to_ts
            GROUP BY DATE_TRUNC(:time_trunc, created_at)
            ORDER BY ts
        """)

        result = await self._session.execute(
            query,
            {
                "time_trunc": time_trunc,
                "tenant_id": tenant_id,
                "from_ts": from_ts,
                "to_ts": to_ts,
            },
        )
        rows = result.fetchall()

        return [
            {
                "ts": row.ts.isoformat() if row.ts else None,
                "requests": row.requests or 0,
                "tokens": row.tokens or 0,
            }
            for row in rows
        ]

    async def fetch_llm_usage(
        self,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        time_trunc: str,
    ) -> list[dict[str, Any]]:
        """
        Fetch LLM usage from runs table.

        Args:
            tenant_id: Tenant ID for isolation
            from_ts: Start of time window
            to_ts: End of time window
            time_trunc: Time truncation (hour or day)

        Returns:
            List of {ts, requests, tokens} dicts
        """
        query = text("""
            SELECT
                DATE_TRUNC(:time_trunc, created_at) as ts,
                COUNT(*) as requests,
                COALESCE(SUM(total_tokens), 0) as tokens
            FROM runs
            WHERE tenant_id = :tenant_id
              AND created_at >= :from_ts
              AND created_at < :to_ts
            GROUP BY DATE_TRUNC(:time_trunc, created_at)
            ORDER BY ts
        """)

        result = await self._session.execute(
            query,
            {
                "time_trunc": time_trunc,
                "tenant_id": tenant_id,
                "from_ts": from_ts,
                "to_ts": to_ts,
            },
        )
        rows = result.fetchall()

        return [
            {
                "ts": row.ts.isoformat() if row.ts else None,
                "requests": row.requests or 0,
                "tokens": row.tokens or 0,
            }
            for row in rows
        ]

    async def fetch_worker_execution(
        self,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        time_trunc: str,
    ) -> list[dict[str, Any]]:
        """
        Fetch worker execution metrics from aos_traces table.

        Args:
            tenant_id: Tenant ID for isolation
            from_ts: Start of time window
            to_ts: End of time window
            time_trunc: Time truncation (hour or day)

        Returns:
            List of {ts, requests} dicts
        """
        query = text("""
            SELECT
                DATE_TRUNC(:time_trunc, created_at) as ts,
                COUNT(*) as requests
            FROM aos_traces
            WHERE tenant_id = :tenant_id
              AND created_at >= :from_ts
              AND created_at < :to_ts
            GROUP BY DATE_TRUNC(:time_trunc, created_at)
            ORDER BY ts
        """)

        result = await self._session.execute(
            query,
            {
                "time_trunc": time_trunc,
                "tenant_id": tenant_id,
                "from_ts": from_ts,
                "to_ts": to_ts,
            },
        )
        rows = result.fetchall()

        return [
            {
                "ts": row.ts.isoformat() if row.ts else None,
                "requests": row.requests or 0,
            }
            for row in rows
        ]

    async def fetch_cost_spend(
        self,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        time_trunc: str,
    ) -> list[dict[str, Any]]:
        """
        Fetch cost spend data from cost_records table.

        Args:
            tenant_id: Tenant ID for isolation
            from_ts: Start of time window
            to_ts: End of time window
            time_trunc: Time truncation (hour or day)

        Returns:
            List of {ts, spend_cents, requests, input_tokens, output_tokens} dicts
        """
        query = text("""
            SELECT
                DATE_TRUNC(:time_trunc, created_at) as ts,
                COUNT(*) as requests,
                COALESCE(SUM(cost_cents), 0) as spend_cents,
                COALESCE(SUM(input_tokens), 0) as input_tokens,
                COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :from_ts
              AND created_at < :to_ts
            GROUP BY DATE_TRUNC(:time_trunc, created_at)
            ORDER BY ts
        """)

        result = await self._session.execute(
            query,
            {
                "time_trunc": time_trunc,
                "tenant_id": tenant_id,
                "from_ts": from_ts,
                "to_ts": to_ts,
            },
        )
        rows = result.fetchall()

        return [
            {
                "ts": row.ts.isoformat() if row.ts else None,
                "spend_cents": float(row.spend_cents or 0),
                "requests": row.requests or 0,
                "input_tokens": row.input_tokens or 0,
                "output_tokens": row.output_tokens or 0,
            }
            for row in rows
        ]

    async def fetch_cost_by_model(
        self,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> list[dict[str, Any]]:
        """
        Fetch cost breakdown by model from cost_records table.

        Args:
            tenant_id: Tenant ID for isolation
            from_ts: Start of time window
            to_ts: End of time window

        Returns:
            List of {model, spend_cents, requests, input_tokens, output_tokens} dicts
        """
        query = text("""
            SELECT
                COALESCE(model, 'unknown') as model,
                COUNT(*) as requests,
                COALESCE(SUM(cost_cents), 0) as spend_cents,
                COALESCE(SUM(input_tokens), 0) as input_tokens,
                COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :from_ts
              AND created_at < :to_ts
            GROUP BY model
            ORDER BY spend_cents DESC
        """)

        result = await self._session.execute(
            query,
            {
                "tenant_id": tenant_id,
                "from_ts": from_ts,
                "to_ts": to_ts,
            },
        )
        rows = result.fetchall()

        return [
            {
                "model": row.model,
                "spend_cents": float(row.spend_cents or 0),
                "requests": row.requests or 0,
                "input_tokens": row.input_tokens or 0,
                "output_tokens": row.output_tokens or 0,
            }
            for row in rows
        ]

    async def fetch_cost_by_feature(
        self,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> list[dict[str, Any]]:
        """
        Fetch cost breakdown by feature tag from cost_records table.

        Args:
            tenant_id: Tenant ID for isolation
            from_ts: Start of time window
            to_ts: End of time window

        Returns:
            List of {feature_tag, spend_cents, requests} dicts
        """
        query = text("""
            SELECT
                COALESCE(feature_tag, 'untagged') as feature_tag,
                COUNT(*) as requests,
                COALESCE(SUM(cost_cents), 0) as spend_cents
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :from_ts
              AND created_at < :to_ts
            GROUP BY feature_tag
            ORDER BY spend_cents DESC
        """)

        result = await self._session.execute(
            query,
            {
                "tenant_id": tenant_id,
                "from_ts": from_ts,
                "to_ts": to_ts,
            },
        )
        rows = result.fetchall()

        return [
            {
                "feature_tag": row.feature_tag,
                "spend_cents": float(row.spend_cents or 0),
                "requests": row.requests or 0,
            }
            for row in rows
        ]


def get_analytics_read_driver(session: AsyncSession) -> AnalyticsReadDriver:
    """Get an AnalyticsReadDriver instance."""
    return AnalyticsReadDriver(session)
