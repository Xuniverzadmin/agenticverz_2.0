# Layer: L6 — Data Access Driver
# AUDIENCE: FOUNDER
# Temporal:
#   Trigger: engine
#   Execution: async
# Data Access:
#   Reads: cost_records, cost_anomalies, cost_snapshots, cost_snapshot_baselines,
#          cost_budgets, tenants
#   Writes: none
# Role: Cost intelligence read data access operations
# Callers: cost_ops_engine.py (L5 engine)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# artifact_class: CODE

"""
Cost Read Driver (L6 Data Access)

Handles database operations for founder cost intelligence:
- Global spend aggregation
- Anomaly queries
- Tenant cost rollups
- Customer drilldown queries

All methods are pure DB operations — no business logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CostReadDriver:
    """
    L6 Driver for cost intelligence read operations.

    All methods are pure DB operations — no business logic.
    Business computations (trends, projections) stay in L5.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    # =========================================================================
    # Overview queries
    # =========================================================================

    async def fetch_global_spend_summary(
        self,
        today_start: datetime,
        month_start: datetime,
        week_ago: datetime,
    ) -> dict[str, int]:
        """Fetch global spend: today, MTD, 7d."""
        sql = """
            SELECT
                COALESCE(SUM(CASE WHEN created_at >= :today THEN cost_cents ELSE 0 END), 0) as today,
                COALESCE(SUM(CASE WHEN created_at >= :month THEN cost_cents ELSE 0 END), 0) as mtd,
                COALESCE(SUM(CASE WHEN created_at >= :week THEN cost_cents ELSE 0 END), 0) as week
            FROM cost_records
        """
        result = await self._session.execute(
            text(sql), {"today": today_start, "month": month_start, "week": week_ago}
        )
        row = result.first()
        return {
            "today": int(row[0]) if row else 0,
            "mtd": int(row[1]) if row else 0,
            "week": int(row[2]) if row else 0,
        }

    async def fetch_anomaly_summary(self, cutoff: datetime) -> dict[str, int]:
        """Fetch anomaly counts: distinct tenants, total unresolved."""
        sql = """
            SELECT
                COUNT(DISTINCT tenant_id) as tenants,
                COUNT(*) as total
            FROM cost_anomalies
            WHERE resolved = false AND detected_at >= :cutoff
        """
        result = await self._session.execute(text(sql), {"cutoff": cutoff})
        row = result.first()
        return {
            "tenants": int(row[0]) if row else 0,
            "total": int(row[1]) if row else 0,
        }

    async def fetch_largest_deviation(self) -> dict[str, Any] | None:
        """Fetch the largest unresolved anomaly deviation."""
        sql = """
            SELECT tenant_id, deviation_pct, anomaly_type
            FROM cost_anomalies
            WHERE resolved = false
            ORDER BY deviation_pct DESC NULLS LAST
            LIMIT 1
        """
        result = await self._session.execute(text(sql))
        row = result.first()
        if not row:
            return None
        return {
            "tenant_id": row[0],
            "deviation_pct": float(row[1]) if row[1] else None,
            "anomaly_type": row[2],
        }

    async def fetch_last_snapshot_time(self) -> datetime | None:
        """Fetch the most recent completed snapshot time."""
        sql = """
            SELECT completed_at
            FROM cost_snapshots
            WHERE status = 'complete'
            ORDER BY completed_at DESC
            LIMIT 1
        """
        result = await self._session.execute(text(sql))
        row = result.first()
        return row[0] if row else None

    async def fetch_daily_cost_series(self, since: datetime) -> list[float]:
        """Fetch daily cost totals for trend computation."""
        sql = """
            SELECT DATE(created_at), COALESCE(SUM(cost_cents), 0)
            FROM cost_records
            WHERE created_at >= :since
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """
        result = await self._session.execute(text(sql), {"since": since})
        rows = result.all()
        return [float(row[1]) for row in rows]

    # =========================================================================
    # Anomalies queries
    # =========================================================================

    async def fetch_anomalies(
        self,
        include_resolved: bool,
        cutoff: datetime,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Fetch anomalies with optional resolved filter."""
        where_clause = "detected_at >= :cutoff"
        if not include_resolved:
            where_clause += " AND resolved = false"

        sql = f"""
            SELECT
                id, tenant_id, anomaly_type, severity, entity_type, entity_id,
                current_value_cents, expected_value_cents, deviation_pct, threshold_pct,
                message, incident_id, action_taken, resolved, detected_at, snapshot_id
            FROM cost_anomalies
            WHERE {where_clause}
            ORDER BY detected_at DESC
            LIMIT :limit
        """
        result = await self._session.execute(
            text(sql), {"cutoff": cutoff, "limit": limit}
        )
        rows = result.all()
        return [
            {
                "id": row[0],
                "tenant_id": row[1],
                "anomaly_type": row[2],
                "severity": row[3],
                "entity_type": row[4],
                "entity_id": row[5],
                "current_value_cents": row[6],
                "expected_value_cents": row[7],
                "deviation_pct": row[8],
                "threshold_pct": row[9],
                "message": row[10],
                "incident_id": row[11],
                "action_taken": row[12],
                "resolved": row[13],
                "detected_at": row[14],
                "snapshot_id": row[15],
            }
            for row in rows
        ]

    # =========================================================================
    # Tenants queries
    # =========================================================================

    async def fetch_tenant_cost_rollup(
        self,
        today_start: datetime,
        month_start: datetime,
        week_ago: datetime,
        day_ago: datetime,
        order_by: str,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        """Fetch per-tenant cost rollup with anomaly counts."""
        # Allowlist sort columns to prevent SQL injection
        allowed_sorts = {
            "spend_today DESC",
            "spend_mtd DESC",
            "deviation_pct DESC NULLS LAST",
            "anomaly_count DESC",
        }
        if order_by not in allowed_sorts:
            order_by = "spend_today DESC"

        sql = f"""
            WITH tenant_costs AS (
                SELECT
                    tenant_id,
                    COALESCE(SUM(CASE WHEN created_at >= :today THEN cost_cents ELSE 0 END), 0) as spend_today,
                    COALESCE(SUM(CASE WHEN created_at >= :month THEN cost_cents ELSE 0 END), 0) as spend_mtd,
                    COALESCE(SUM(CASE WHEN created_at >= :week THEN cost_cents ELSE 0 END), 0) as spend_7d
                FROM cost_records
                GROUP BY tenant_id
            ),
            tenant_anomalies AS (
                SELECT
                    tenant_id,
                    COUNT(*) as anomaly_count,
                    MAX(deviation_pct) as max_deviation
                FROM cost_anomalies
                WHERE resolved = false AND detected_at >= :day_ago
                GROUP BY tenant_id
            ),
            tenant_baselines AS (
                SELECT
                    tenant_id,
                    avg_daily_cost_cents
                FROM cost_snapshot_baselines
                WHERE is_current = true AND entity_type = 'tenant'
            )
            SELECT
                tc.tenant_id,
                COALESCE(t.name, tc.tenant_id) as tenant_name,
                tc.spend_today,
                tc.spend_mtd,
                tc.spend_7d,
                tb.avg_daily_cost_cents as baseline,
                CASE WHEN tb.avg_daily_cost_cents > 0
                     THEN ((tc.spend_today - tb.avg_daily_cost_cents) / tb.avg_daily_cost_cents * 100)
                     ELSE NULL END as deviation_pct,
                cb.monthly_limit_cents as budget,
                CASE WHEN cb.monthly_limit_cents > 0
                     THEN (tc.spend_mtd::float / cb.monthly_limit_cents * 100)
                     ELSE NULL END as budget_used_pct,
                COALESCE(ta.anomaly_count, 0) as anomaly_count,
                MAX(cr.created_at) as last_activity
            FROM tenant_costs tc
            LEFT JOIN tenants t ON t.id = tc.tenant_id
            LEFT JOIN tenant_baselines tb ON tb.tenant_id = tc.tenant_id
            LEFT JOIN cost_budgets cb ON cb.tenant_id = tc.tenant_id AND cb.budget_type = 'tenant'
            LEFT JOIN tenant_anomalies ta ON ta.tenant_id = tc.tenant_id
            LEFT JOIN cost_records cr ON cr.tenant_id = tc.tenant_id
            GROUP BY tc.tenant_id, t.name, tc.spend_today, tc.spend_mtd, tc.spend_7d,
                     tb.avg_daily_cost_cents, cb.monthly_limit_cents, ta.anomaly_count
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
        """
        result = await self._session.execute(
            text(sql),
            {
                "today": today_start,
                "month": month_start,
                "week": week_ago,
                "day_ago": day_ago,
                "limit": limit,
                "offset": offset,
            },
        )
        rows = result.all()
        return [
            {
                "tenant_id": row[0],
                "tenant_name": row[1],
                "spend_today": row[2],
                "spend_mtd": row[3],
                "spend_7d": row[4],
                "baseline": row[5],
                "deviation_pct": row[6],
                "budget": row[7],
                "budget_used_pct": row[8],
                "anomaly_count": row[9],
                "last_activity": row[10],
            }
            for row in rows
        ]

    async def fetch_distinct_tenant_count(self) -> int:
        """Count distinct tenants with cost records."""
        sql = "SELECT COUNT(DISTINCT tenant_id) FROM cost_records"
        result = await self._session.execute(text(sql))
        row = result.first()
        return int(row[0]) if row else 0

    # =========================================================================
    # Customer drilldown queries
    # =========================================================================

    async def check_tenant_has_data(self, tenant_id: str) -> bool:
        """Check if tenant has any cost records."""
        sql = "SELECT COUNT(*) FROM cost_records WHERE tenant_id = :tenant_id"
        result = await self._session.execute(text(sql), {"tenant_id": tenant_id})
        row = result.first()
        return bool(row and row[0] > 0)

    async def fetch_tenant_name(self, tenant_id: str) -> str | None:
        """Fetch tenant display name."""
        sql = "SELECT name FROM tenants WHERE id = :tenant_id"
        result = await self._session.execute(text(sql), {"tenant_id": tenant_id})
        row = result.first()
        return row[0] if row else None

    async def fetch_tenant_spend_summary(
        self,
        tenant_id: str,
        today_start: datetime,
        month_start: datetime,
        week_ago: datetime,
        month_ago: datetime,
    ) -> dict[str, int]:
        """Fetch tenant spend: today, MTD, 7d, 30d."""
        sql = """
            SELECT
                COALESCE(SUM(CASE WHEN created_at >= :today THEN cost_cents ELSE 0 END), 0) as today,
                COALESCE(SUM(CASE WHEN created_at >= :month_start THEN cost_cents ELSE 0 END), 0) as mtd,
                COALESCE(SUM(CASE WHEN created_at >= :week THEN cost_cents ELSE 0 END), 0) as week,
                COALESCE(SUM(CASE WHEN created_at >= :month_ago THEN cost_cents ELSE 0 END), 0) as month
            FROM cost_records
            WHERE tenant_id = :tenant_id
        """
        result = await self._session.execute(
            text(sql),
            {
                "tenant_id": tenant_id,
                "today": today_start,
                "month_start": month_start,
                "week": week_ago,
                "month_ago": month_ago,
            },
        )
        row = result.first()
        return {
            "today": int(row[0]) if row else 0,
            "mtd": int(row[1]) if row else 0,
            "week": int(row[2]) if row else 0,
            "month": int(row[3]) if row else 0,
        }

    async def fetch_tenant_baseline(self, tenant_id: str) -> float | None:
        """Fetch tenant's current baseline daily cost."""
        sql = """
            SELECT avg_daily_cost_cents
            FROM cost_snapshot_baselines
            WHERE tenant_id = :tenant_id AND entity_type = 'tenant' AND is_current = true
        """
        result = await self._session.execute(text(sql), {"tenant_id": tenant_id})
        row = result.first()
        return float(row[0]) if row else None

    async def fetch_tenant_budget(self, tenant_id: str) -> int | None:
        """Fetch tenant's active monthly budget limit."""
        sql = """
            SELECT monthly_limit_cents
            FROM cost_budgets
            WHERE tenant_id = :tenant_id AND budget_type = 'tenant' AND is_active = true
        """
        result = await self._session.execute(text(sql), {"tenant_id": tenant_id})
        row = result.first()
        return int(row[0]) if row else None

    async def fetch_tenant_daily_breakdown(
        self,
        tenant_id: str,
        since: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch daily spend breakdown for a tenant."""
        sql = """
            SELECT
                DATE(created_at) as day,
                COALESCE(SUM(cost_cents), 0) as spend,
                COUNT(*) as requests
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :since
            GROUP BY DATE(created_at)
            ORDER BY day DESC
            LIMIT 7
        """
        result = await self._session.execute(
            text(sql), {"tenant_id": tenant_id, "since": since}
        )
        rows = result.all()
        return [
            {"date": row[0], "spend": int(row[1]), "requests": int(row[2])}
            for row in rows
        ]

    async def fetch_tenant_cost_by_feature(
        self,
        tenant_id: str,
        since: datetime,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch cost breakdown by feature for a tenant."""
        sql = """
            SELECT
                COALESCE(feature_tag, 'unclassified') as feature,
                COALESCE(SUM(cost_cents), 0) as spend,
                COUNT(*) as requests
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :since
            GROUP BY feature_tag
            ORDER BY spend DESC
            LIMIT :limit
        """
        result = await self._session.execute(
            text(sql), {"tenant_id": tenant_id, "since": since, "limit": limit}
        )
        rows = result.all()
        return [
            {"feature": row[0], "spend": int(row[1]), "requests": int(row[2])}
            for row in rows
        ]

    async def fetch_tenant_cost_by_user(
        self,
        tenant_id: str,
        since: datetime,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch cost breakdown by user for a tenant."""
        sql = """
            SELECT
                COALESCE(user_id, 'unknown') as user_id,
                COALESCE(SUM(cost_cents), 0) as spend,
                COUNT(*) as requests
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :since
            GROUP BY user_id
            ORDER BY spend DESC
            LIMIT :limit
        """
        result = await self._session.execute(
            text(sql), {"tenant_id": tenant_id, "since": since, "limit": limit}
        )
        rows = result.all()
        return [
            {"user_id": row[0], "spend": int(row[1]), "requests": int(row[2])}
            for row in rows
        ]

    async def fetch_tenant_anomalous_users(self, tenant_id: str) -> set[str]:
        """Fetch user IDs with active anomalies for a tenant."""
        sql = """
            SELECT DISTINCT entity_id
            FROM cost_anomalies
            WHERE tenant_id = :tenant_id AND entity_type = 'user' AND resolved = false
        """
        result = await self._session.execute(text(sql), {"tenant_id": tenant_id})
        rows = result.all()
        return {row[0] for row in rows if row[0]}

    async def fetch_tenant_cost_by_model(
        self,
        tenant_id: str,
        since: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch cost breakdown by model for a tenant."""
        sql = """
            SELECT
                model,
                COALESCE(SUM(cost_cents), 0) as spend,
                COALESCE(SUM(input_tokens), 0) as input_tokens,
                COALESCE(SUM(output_tokens), 0) as output_tokens,
                COUNT(*) as requests
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :since
            GROUP BY model
            ORDER BY spend DESC
        """
        result = await self._session.execute(
            text(sql), {"tenant_id": tenant_id, "since": since}
        )
        rows = result.all()
        return [
            {
                "model": row[0],
                "spend": int(row[1]),
                "input_tokens": int(row[2]),
                "output_tokens": int(row[3]),
                "requests": int(row[4]),
            }
            for row in rows
        ]

    async def fetch_tenant_anomaly_history(
        self,
        tenant_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Fetch recent anomaly history for a tenant."""
        sql = """
            SELECT
                id, anomaly_type, severity, detected_at, resolved,
                deviation_pct, derived_cause, message
            FROM cost_anomalies
            WHERE tenant_id = :tenant_id
            ORDER BY detected_at DESC
            LIMIT :limit
        """
        result = await self._session.execute(
            text(sql), {"tenant_id": tenant_id, "limit": limit}
        )
        rows = result.all()
        return [
            {
                "id": row[0],
                "anomaly_type": row[1],
                "severity": row[2],
                "detected_at": row[3],
                "resolved": row[4],
                "deviation_pct": row[5],
                "derived_cause": row[6],
                "message": row[7],
            }
            for row in rows
        ]

    async def fetch_tenant_last_activity(self, tenant_id: str) -> datetime | None:
        """Fetch the most recent cost record time for a tenant."""
        sql = """
            SELECT MAX(created_at)
            FROM cost_records
            WHERE tenant_id = :tenant_id
        """
        result = await self._session.execute(text(sql), {"tenant_id": tenant_id})
        row = result.first()
        return row[0] if row and row[0] else None


def get_cost_read_driver(session: AsyncSession) -> CostReadDriver:
    """Get a CostReadDriver instance."""
    return CostReadDriver(session)
