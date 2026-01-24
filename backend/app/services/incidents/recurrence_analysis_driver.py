# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Recurrence analysis data access driver
# Callers: incidents_facade.py
# Allowed Imports: sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468 (Phase 2 Step 2 - L4/L6 Segregation)
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for recurrence analysis.
# Read-only statistical queries - NO business logic.
#
# RECLASSIFICATION: 2026-01-23
# Previously: recurrence_analysis_service.py (mislabeled as L4 engine)
# Reason: 0 decisions, 100% read queries = pure driver

"""
Recurrence Analysis Driver (L6)

Pure database operations for incident recurrence analysis.

Answers "how often does this type repeat?":
- Group by (category, resolution_method)
- Count occurrences over time window
- Calculate recurrence rate

Design Rules:
- Statistical analysis only
- Read-only (no writes)
- NO business logic

Reference: PIN-468, docs/architecture/incidents/INCIDENTS_DOMAIN_SQL.md#9-hist-o3
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class RecurrenceGroup:
    """A group of recurring incidents."""
    category: str
    resolution_method: Optional[str]
    total_occurrences: int
    distinct_days: int
    occurrences_per_day: float
    first_occurrence: datetime
    last_occurrence: datetime
    recent_incident_ids: list[str]


@dataclass
class RecurrenceResult:
    """Result of recurrence analysis."""
    groups: list[RecurrenceGroup]
    baseline_days: int
    total_recurring: int
    generated_at: datetime


class RecurrenceAnalysisDriver:
    """
    L6 driver for recurrence analysis queries.

    Pure database access - read-only statistical queries.
    """

    # Query parameters
    DEFAULT_BASELINE_DAYS = 30
    DEFAULT_RECURRENCE_THRESHOLD = 3

    def __init__(self, session: AsyncSession):
        self._session = session

    async def analyze_recurrence(
        self,
        tenant_id: str,
        baseline_days: int = DEFAULT_BASELINE_DAYS,
        recurrence_threshold: int = DEFAULT_RECURRENCE_THRESHOLD,
        limit: int = 20,
    ) -> RecurrenceResult:
        """
        Analyze incident recurrence patterns.

        Args:
            tenant_id: Tenant scope
            baseline_days: Days to analyze (max 90)
            recurrence_threshold: Min occurrences to flag as recurring
            limit: Max groups to return

        Returns:
            RecurrenceResult with recurring incident groups
        """
        # Parameter guards
        baseline_days = min(baseline_days, 90)
        recurrence_threshold = max(recurrence_threshold, 2)

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

        groups: list[RecurrenceGroup] = []
        total_recurring = 0

        for row in result.mappings():
            total_recurring += row["total_occurrences"]

            groups.append(RecurrenceGroup(
                category=row["category"],
                resolution_method=row["resolution_method"],
                total_occurrences=row["total_occurrences"],
                distinct_days=row["distinct_days"],
                occurrences_per_day=float(row["occurrences_per_day"]),
                first_occurrence=row["first_occurrence"],
                last_occurrence=row["last_occurrence"],
                recent_incident_ids=row["recent_incident_ids"] or [],
            ))

        return RecurrenceResult(
            groups=groups,
            baseline_days=baseline_days,
            total_recurring=total_recurring,
            generated_at=datetime.utcnow(),
        )

    async def get_recurrence_for_category(
        self,
        tenant_id: str,
        category: str,
        baseline_days: int = DEFAULT_BASELINE_DAYS,
    ) -> Optional[RecurrenceGroup]:
        """
        Get recurrence details for a specific category.

        Args:
            tenant_id: Tenant scope
            category: Category to analyze
            baseline_days: Days to analyze

        Returns:
            RecurrenceGroup if found, None otherwise
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

        return RecurrenceGroup(
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


def get_recurrence_analysis_driver(session: AsyncSession) -> RecurrenceAnalysisDriver:
    """Factory function to get RecurrenceAnalysisDriver instance."""
    return RecurrenceAnalysisDriver(session)


# Backward compatibility aliases (DEPRECATED - remove after migration)
RecurrenceAnalysisService = RecurrenceAnalysisDriver


__all__ = [
    "RecurrenceGroup",
    "RecurrenceResult",
    "RecurrenceAnalysisDriver",
    "get_recurrence_analysis_driver",
    # Deprecated alias
    "RecurrenceAnalysisService",
]
