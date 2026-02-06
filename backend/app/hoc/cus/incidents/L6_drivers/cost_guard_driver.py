# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: guard-console
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: cost_records, cost_budgets, cost_snapshot_baselines, cost_snapshots, cost_anomalies
#   Writes: none
# Database:
#   Scope: domain (incidents/costs)
#   Models: raw SQL (cost tables)
# Role: Data access for cost guard read operations
# Callers: incidents_handler (L4) via CostGuardQueryHandler
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, cost_guard.py refactor
# artifact_class: CODE
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for cost guard queries.
# No business logic - only DB reads and data retrieval.
# Extracted from cost_guard.py L2 (10 session.execute calls).

"""
Cost Guard Driver (L6)

Pure data access layer for cost guard read operations.
No business logic - only query construction and data retrieval.

Architecture:
    L2 (cost_guard.py) -> L4 (incidents_handler) -> L6 (this driver) -> Database

Operations:
- Spend totals (today, mtd, week)
- Budget limits
- Baselines for trend calculation
- Snapshot timestamps
- Breakdown by feature/model/user
- Cost anomalies

Reference: Extracted from cost_guard.py
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlmodel import Session


@dataclass
class SpendTotals:
    """Spend totals for different periods."""

    today: int
    mtd: int
    week: int


@dataclass
class BudgetLimits:
    """Budget configuration for a tenant."""

    daily_limit_cents: Optional[int]
    monthly_limit_cents: Optional[int]


@dataclass
class BreakdownRow:
    """A row in a cost breakdown."""

    name: str
    display_name: Optional[str]
    spend_cents: int
    request_count: int


@dataclass
class AnomalyRow:
    """A cost anomaly record."""

    id: Any
    anomaly_type: str
    severity: Optional[str]
    current_value_cents: Optional[float]
    expected_value_cents: Optional[float]
    threshold_pct: Optional[float]
    message: Optional[str]
    incident_id: Optional[Any]
    action_taken: Optional[str]
    resolved: bool
    detected_at: Optional[datetime]
    resolved_at: Optional[datetime]


class CostGuardDriver:
    """
    L6 driver for cost guard read operations.

    Pure data access - no business logic.
    All methods require tenant_id for isolation.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    def get_spend_totals(
        self,
        tenant_id: str,
        today_start: datetime,
        month_start: datetime,
        week_ago: datetime,
    ) -> SpendTotals:
        """
        Get spend totals for today, MTD, and past 7 days.

        Args:
            tenant_id: Tenant ID (required, enforces isolation)
            today_start: Start of today (UTC)
            month_start: Start of month (UTC)
            week_ago: 7 days ago (UTC)

        Returns:
            SpendTotals with today, mtd, week values in cents
        """
        result = self._session.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN created_at >= :today THEN cost_cents ELSE 0 END), 0) as today,
                    COALESCE(SUM(CASE WHEN created_at >= :month THEN cost_cents ELSE 0 END), 0) as mtd,
                    COALESCE(SUM(CASE WHEN created_at >= :week THEN cost_cents ELSE 0 END), 0) as week
                FROM cost_records
                WHERE tenant_id = :tenant_id
            """
            ),
            {"tenant_id": tenant_id, "today": today_start, "month": month_start, "week": week_ago},
        ).first()

        return SpendTotals(
            today=int(result[0]) if result else 0,
            mtd=int(result[1]) if result else 0,
            week=int(result[2]) if result else 0,
        )

    def get_budget(self, tenant_id: str) -> BudgetLimits:
        """
        Get budget limits for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            BudgetLimits with daily and monthly limits in cents
        """
        result = self._session.execute(
            text(
                """
                SELECT daily_limit_cents, monthly_limit_cents
                FROM cost_budgets
                WHERE tenant_id = :tenant_id AND budget_type = 'tenant' AND is_active = true
            """
            ),
            {"tenant_id": tenant_id},
        ).first()

        return BudgetLimits(
            daily_limit_cents=int(result[0]) if result and result[0] else None,
            monthly_limit_cents=int(result[1]) if result and result[1] else None,
        )

    def get_baseline(self, tenant_id: str) -> Optional[float]:
        """
        Get avg daily cost baseline for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Average daily cost in cents, or None if no baseline
        """
        result = self._session.execute(
            text(
                """
                SELECT avg_daily_cost_cents
                FROM cost_snapshot_baselines
                WHERE tenant_id = :tenant_id AND entity_type = 'tenant' AND is_current = true
            """
            ),
            {"tenant_id": tenant_id},
        ).first()

        return float(result[0]) if result and result[0] else None

    def get_last_snapshot(self, tenant_id: str) -> Optional[datetime]:
        """
        Get the timestamp of the last complete snapshot.

        Args:
            tenant_id: Tenant ID

        Returns:
            Datetime of last snapshot, or None
        """
        result = self._session.execute(
            text(
                """
                SELECT completed_at
                FROM cost_snapshots
                WHERE tenant_id = :tenant_id AND status = 'complete'
                ORDER BY completed_at DESC
                LIMIT 1
            """
            ),
            {"tenant_id": tenant_id},
        ).first()

        return result[0] if result else None

    def get_total_spend(self, tenant_id: str, period_start: datetime) -> int:
        """
        Get total spend since period_start.

        Args:
            tenant_id: Tenant ID
            period_start: Start of period

        Returns:
            Total spend in cents
        """
        result = self._session.execute(
            text(
                """
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE tenant_id = :tenant_id AND created_at >= :start
            """
            ),
            {"tenant_id": tenant_id, "start": period_start},
        ).first()

        return int(result[0]) if result else 0

    def get_baselines(self, tenant_id: str) -> Dict[str, float]:
        """
        Get all current baselines for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Dict mapping entity_id to avg_daily_cost_cents
        """
        result = self._session.execute(
            text(
                """
                SELECT entity_id, avg_daily_cost_cents
                FROM cost_snapshot_baselines
                WHERE tenant_id = :tenant_id AND is_current = true
            """
            ),
            {"tenant_id": tenant_id},
        ).all()

        return {row[0]: float(row[1]) for row in result if row[0]}

    def get_spend_by_feature(
        self,
        tenant_id: str,
        period_start: datetime,
        limit: int = 10,
    ) -> List[BreakdownRow]:
        """
        Get spend breakdown by feature.

        Args:
            tenant_id: Tenant ID
            period_start: Start of period
            limit: Max number of rows

        Returns:
            List of BreakdownRow sorted by spend descending
        """
        result = self._session.execute(
            text(
                """
                SELECT
                    COALESCE(cr.feature_tag, 'unclassified') as feature,
                    ft.display_name,
                    COALESCE(SUM(cr.cost_cents), 0) as spend,
                    COUNT(*) as requests
                FROM cost_records cr
                LEFT JOIN feature_tags ft ON cr.feature_tag = ft.tag AND cr.tenant_id = ft.tenant_id
                WHERE cr.tenant_id = :tenant_id AND cr.created_at >= :start
                GROUP BY cr.feature_tag, ft.display_name
                ORDER BY spend DESC
                LIMIT :limit
            """
            ),
            {"tenant_id": tenant_id, "start": period_start, "limit": limit},
        ).all()

        return [
            BreakdownRow(
                name=row[0],
                display_name=row[1],
                spend_cents=int(row[2]),
                request_count=int(row[3]),
            )
            for row in result
        ]

    def get_spend_by_model(
        self,
        tenant_id: str,
        period_start: datetime,
        limit: int = 10,
    ) -> List[BreakdownRow]:
        """
        Get spend breakdown by model.

        Args:
            tenant_id: Tenant ID
            period_start: Start of period
            limit: Max number of rows

        Returns:
            List of BreakdownRow sorted by spend descending
        """
        result = self._session.execute(
            text(
                """
                SELECT
                    model,
                    COALESCE(SUM(cost_cents), 0) as spend,
                    COUNT(*) as requests
                FROM cost_records
                WHERE tenant_id = :tenant_id AND created_at >= :start
                GROUP BY model
                ORDER BY spend DESC
                LIMIT :limit
            """
            ),
            {"tenant_id": tenant_id, "start": period_start, "limit": limit},
        ).all()

        return [
            BreakdownRow(
                name=row[0],
                display_name=None,
                spend_cents=int(row[1]),
                request_count=int(row[2]),
            )
            for row in result
        ]

    def get_spend_by_user(
        self,
        tenant_id: str,
        period_start: datetime,
        limit: int = 10,
    ) -> List[BreakdownRow]:
        """
        Get spend breakdown by user.

        Args:
            tenant_id: Tenant ID
            period_start: Start of period
            limit: Max number of rows

        Returns:
            List of BreakdownRow sorted by spend descending
        """
        result = self._session.execute(
            text(
                """
                SELECT
                    COALESCE(user_id, 'anonymous') as user_id,
                    COALESCE(SUM(cost_cents), 0) as spend,
                    COUNT(*) as requests
                FROM cost_records
                WHERE tenant_id = :tenant_id AND created_at >= :start
                GROUP BY user_id
                ORDER BY spend DESC
                LIMIT :limit
            """
            ),
            {"tenant_id": tenant_id, "start": period_start, "limit": limit},
        ).all()

        return [
            BreakdownRow(
                name=row[0],
                display_name=None,
                spend_cents=int(row[1]),
                request_count=int(row[2]),
            )
            for row in result
        ]

    def get_cost_anomalies(
        self,
        tenant_id: str,
        cutoff: datetime,
        include_resolved: bool = False,
        limit: int = 20,
    ) -> Tuple[List[AnomalyRow], bool]:
        """
        Get cost anomalies for a tenant.

        Args:
            tenant_id: Tenant ID
            cutoff: Only include anomalies detected after this time
            include_resolved: Whether to include resolved anomalies
            limit: Max number of rows

        Returns:
            Tuple of (list of AnomalyRow, has_more flag)
        """
        where_clause = "tenant_id = :tenant_id AND detected_at >= :cutoff"
        params: Dict[str, Any] = {"tenant_id": tenant_id, "cutoff": cutoff, "limit": limit + 1}

        if not include_resolved:
            where_clause += " AND resolved = false"

        result = self._session.execute(
            text(
                f"""
                SELECT
                    id, anomaly_type, severity,
                    current_value_cents, expected_value_cents, threshold_pct,
                    message, incident_id, action_taken,
                    resolved, detected_at, resolved_at
                FROM cost_anomalies
                WHERE {where_clause}
                ORDER BY detected_at DESC
                LIMIT :limit
            """
            ),
            params,
        ).all()

        has_more = len(result) > limit
        rows = result[:limit]

        anomalies = [
            AnomalyRow(
                id=row[0],
                anomaly_type=row[1],
                severity=row[2],
                current_value_cents=row[3],
                expected_value_cents=row[4],
                threshold_pct=row[5],
                message=row[6],
                incident_id=row[7],
                action_taken=row[8],
                resolved=row[9] or False,
                detected_at=row[10],
                resolved_at=row[11],
            )
            for row in rows
        ]

        return anomalies, has_more


def get_cost_guard_driver(session: Session) -> CostGuardDriver:
    """Factory function to get CostGuardDriver instance."""
    return CostGuardDriver(session)


__all__ = [
    "CostGuardDriver",
    "get_cost_guard_driver",
    "SpendTotals",
    "BudgetLimits",
    "BreakdownRow",
    "AnomalyRow",
]
