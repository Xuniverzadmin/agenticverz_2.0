# Layer: L6 — Platform Substrate
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Database operations for recurrence analysis - pure data access
# Callers: recurrence_analysis_service.py (L4)
# Allowed Imports: sqlalchemy, models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Violation I.2

"""
Recurrence Analysis Driver (L6)

Pure database access layer for recurrence analysis.
Returns snapshots (dicts/dataclasses), not ORM models.

Responsibilities:
- Execute queries against incidents table for recurrence patterns
- Return data snapshots
- NO business logic
- NO threshold decisions (that's L4's job)

This driver was extracted from recurrence_analysis_service.py per HOC Layer Topology V1.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Snapshot Types (L6 returns these, not computed results)
# =============================================================================


@dataclass
class RecurrenceGroupSnapshot:
    """Raw recurrence group data from database."""

    category: str
    resolution_method: Optional[str]
    total_occurrences: int
    distinct_days: int
    occurrences_per_day: float
    first_occurrence: datetime
    last_occurrence: datetime
    recent_incident_ids: list[str]


# =============================================================================
# Recurrence Analysis Driver
# =============================================================================


class RecurrenceAnalysisDriver:
    """
    L6 Database driver for recurrence analysis.

    Pure data access - no business logic.
    Returns snapshots, not computed analysis.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_recurrence_groups(
        self,
        tenant_id: str,
        baseline_days: int,
        recurrence_threshold: int,
        limit: int,
    ) -> list[RecurrenceGroupSnapshot]:
        """
        Fetch recurrence groups from database.

        Args:
            tenant_id: Tenant scope
            baseline_days: Days to analyze (caller should cap this)
            recurrence_threshold: Min occurrences to include (caller should validate)
            limit: Max groups to return

        Returns:
            List of recurrence group snapshots
        """
        sql = text("""
            WITH recurrence_groups AS (
                SELECT
                    COALESCE(category, 'uncategorized') AS category,
                    resolution_method,
                    COUNT(*) AS total_occurrences,
                    COUNT(DISTINCT DATE(created_at)) AS distinct_days,
                    MIN(created_at) AS first_occurrence,
                    MAX(created_at) AS last_occurrence,
                    array_agg(id ORDER BY created_at DESC) AS incident_ids
                FROM incidents
                WHERE tenant_id = :tenant_id
                  AND created_at >= NOW() - INTERVAL '1 day' * :baseline_days
                GROUP BY category, resolution_method
                HAVING COUNT(*) >= :recurrence_threshold
            )
            SELECT
                category,
                resolution_method,
                total_occurrences,
                distinct_days,
                ROUND(total_occurrences::numeric / GREATEST(distinct_days, 1), 2) AS occurrences_per_day,
                first_occurrence,
                last_occurrence,
                incident_ids[1:5] AS recent_incident_ids
            FROM recurrence_groups
            ORDER BY total_occurrences DESC
            LIMIT :limit
        """)

        result = await self._session.execute(sql, {
            "tenant_id": tenant_id,
            "baseline_days": baseline_days,
            "recurrence_threshold": recurrence_threshold,
            "limit": limit,
        })

        groups: list[RecurrenceGroupSnapshot] = []
        for row in result.mappings():
            groups.append(RecurrenceGroupSnapshot(
                category=row["category"],
                resolution_method=row["resolution_method"],
                total_occurrences=row["total_occurrences"],
                distinct_days=row["distinct_days"],
                occurrences_per_day=float(row["occurrences_per_day"]),
                first_occurrence=row["first_occurrence"],
                last_occurrence=row["last_occurrence"],
                recent_incident_ids=row["recent_incident_ids"] or [],
            ))

        return groups

    async def fetch_recurrence_for_category(
        self,
        tenant_id: str,
        category: str,
        baseline_days: int,
    ) -> Optional[RecurrenceGroupSnapshot]:
        """
        Fetch recurrence details for a specific category.

        Args:
            tenant_id: Tenant scope
            category: Category to analyze
            baseline_days: Days to analyze

        Returns:
            RecurrenceGroupSnapshot if found, None otherwise
        """
        sql = text("""
            SELECT
                COALESCE(category, 'uncategorized') AS category,
                resolution_method,
                COUNT(*) AS total_occurrences,
                COUNT(DISTINCT DATE(created_at)) AS distinct_days,
                MIN(created_at) AS first_occurrence,
                MAX(created_at) AS last_occurrence,
                array_agg(id ORDER BY created_at DESC) AS incident_ids
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND category = :category
              AND created_at >= NOW() - INTERVAL '1 day' * :baseline_days
            GROUP BY category, resolution_method
            ORDER BY total_occurrences DESC
            LIMIT 1
        """)

        result = await self._session.execute(sql, {
            "tenant_id": tenant_id,
            "category": category,
            "baseline_days": baseline_days,
        })

        row = result.mappings().first()
        if not row:
            return None

        return RecurrenceGroupSnapshot(
            category=row["category"],
            resolution_method=row["resolution_method"],
            total_occurrences=row["total_occurrences"],
            distinct_days=row["distinct_days"],
            occurrences_per_day=round(
                row["total_occurrences"] / max(row["distinct_days"], 1), 2
            ),
            first_occurrence=row["first_occurrence"],
            last_occurrence=row["last_occurrence"],
            recent_incident_ids=(row["incident_ids"] or [])[:5],
        )


__all__ = [
    "RecurrenceAnalysisDriver",
    "RecurrenceGroupSnapshot",
]
