# capability_id: CAP-001
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Incident
#   Writes: none
# Database:
#   Scope: domain (incidents)
#   Models: Incident
# Role: Data access for post-mortem analytics operations (async)
# Callers: PostMortemEngine (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for post-mortem analytics.
# NO business logic - only DB operations.
# Business logic (insight generation, confidence calculation) stays in L4 engine.
#
# EXTRACTION STATUS:
# - 2026-01-23: Initial extraction from postmortem_service.py (PIN-468)
#
# ============================================================================
# L6 DRIVER INVENTORY — POSTMORTEM DOMAIN (CANONICAL)
# ============================================================================
# Method                              | Purpose
# ----------------------------------- | ----------------------------------------
# fetch_category_stats                | Get incident counts and resolution times
# fetch_resolution_methods            | Get common resolution methods for category
# fetch_recurrence_data               | Get recurrence rate data
# fetch_resolution_summary            | Get resolution summary for single incident
# fetch_similar_incidents             | Find similar resolved incidents
# ============================================================================
# This is the SINGLE persistence authority for post-mortem reads.
# Do NOT create competing drivers. Extend this file.
# ============================================================================

"""
Post-Mortem Driver (L6)

Pure database operations for post-mortem analytics.
All business logic stays in L4 engine.

Operations:
- Category statistics queries
- Resolution method aggregation
- Recurrence rate calculation
- Similar incident lookup

NO business logic:
- NO insight generation (L4)
- NO confidence calculation (L4)
- NO pattern analysis (L4)

Reference: PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.drivers.postmortem")


class PostMortemDriver:
    """
    L6 driver for post-mortem analytics operations (async).

    Pure database access - no business logic.
    All operations are READ-ONLY.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self._session = session

    async def fetch_category_stats(
        self,
        tenant_id: str,
        category: str,
        baseline_days: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch category statistics.

        Args:
            tenant_id: Tenant scope
            category: Category to analyze
            baseline_days: Days to look back

        Returns:
            Dict with total_incidents, resolved_count, avg_resolution_time_ms
            or None if no data
        """
        result = await self._session.execute(
            text("""
                SELECT
                    COUNT(*) AS total_incidents,
                    COUNT(*) FILTER (WHERE lifecycle_state = 'RESOLVED' OR status = 'resolved') AS resolved_count,
                    AVG(
                        CASE WHEN resolved_at IS NOT NULL THEN
                            EXTRACT(EPOCH FROM (resolved_at - created_at)) * 1000
                        END
                    ) AS avg_resolution_time_ms
                FROM incidents
                WHERE tenant_id = :tenant_id
                  AND category = :category
                  AND created_at >= NOW() - INTERVAL '1 day' * :baseline_days
            """),
            {
                "tenant_id": tenant_id,
                "category": category,
                "baseline_days": baseline_days,
            },
        )
        row = result.mappings().first()
        if not row or row["total_incidents"] == 0:
            return None
        return dict(row)

    async def fetch_resolution_methods(
        self,
        tenant_id: str,
        category: str,
        baseline_days: int,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Fetch common resolution methods for a category.

        Args:
            tenant_id: Tenant scope
            category: Category to analyze
            baseline_days: Days to look back
            limit: Max methods to return

        Returns:
            List of dicts with resolution_method and method_count
        """
        result = await self._session.execute(
            text("""
                SELECT
                    resolution_method,
                    COUNT(*) AS method_count
                FROM incidents
                WHERE tenant_id = :tenant_id
                  AND category = :category
                  AND resolution_method IS NOT NULL
                  AND created_at >= NOW() - INTERVAL '1 day' * :baseline_days
                GROUP BY resolution_method
                ORDER BY method_count DESC
                LIMIT :limit
            """),
            {
                "tenant_id": tenant_id,
                "category": category,
                "baseline_days": baseline_days,
                "limit": limit,
            },
        )
        return [dict(row) for row in result.mappings()]

    async def fetch_recurrence_data(
        self,
        tenant_id: str,
        category: str,
        baseline_days: int,
    ) -> Dict[str, int]:
        """
        Fetch recurrence rate data.

        Args:
            tenant_id: Tenant scope
            category: Category to analyze
            baseline_days: Days to look back

        Returns:
            Dict with distinct_days and total counts
        """
        result = await self._session.execute(
            text("""
                SELECT
                    COUNT(DISTINCT DATE(created_at)) AS distinct_days,
                    COUNT(*) AS total
                FROM incidents
                WHERE tenant_id = :tenant_id
                  AND category = :category
                  AND created_at >= NOW() - INTERVAL '1 day' * :baseline_days
            """),
            {
                "tenant_id": tenant_id,
                "category": category,
                "baseline_days": baseline_days,
            },
        )
        row = result.mappings().first()
        return {
            "distinct_days": row["distinct_days"] if row else 1,
            "total": row["total"] if row else 0,
        }

    async def fetch_resolution_summary(
        self,
        tenant_id: str,
        incident_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch resolution summary for an incident.

        Args:
            tenant_id: Tenant scope
            incident_id: Incident to analyze

        Returns:
            Dict with incident details or None if not found
        """
        result = await self._session.execute(
            text("""
                SELECT
                    i.id AS incident_id,
                    i.title,
                    i.category,
                    i.severity,
                    i.resolution_method,
                    CASE WHEN i.resolved_at IS NOT NULL THEN
                        EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) * 1000
                    END AS time_to_resolution_ms,
                    (SELECT COUNT(*) FROM incident_evidence WHERE incident_id = i.id) AS evidence_count,
                    EXISTS(
                        SELECT 1 FROM incident_evidence
                        WHERE incident_id = i.id AND recovery_executed = TRUE
                    ) AS recovery_attempted
                FROM incidents i
                WHERE i.id = :incident_id
                  AND i.tenant_id = :tenant_id
            """),
            {
                "incident_id": incident_id,
                "tenant_id": tenant_id,
            },
        )
        row = result.mappings().first()
        if not row:
            return None
        return dict(row)

    async def fetch_similar_incidents(
        self,
        tenant_id: str,
        exclude_incident_id: str,
        category: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch similar resolved incidents.

        Args:
            tenant_id: Tenant scope
            exclude_incident_id: Incident to exclude
            category: Category to match
            limit: Max incidents to return

        Returns:
            List of dicts with incident details
        """
        result = await self._session.execute(
            text("""
                SELECT
                    i.id AS incident_id,
                    i.title,
                    i.category,
                    i.severity,
                    i.resolution_method,
                    CASE WHEN i.resolved_at IS NOT NULL THEN
                        EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) * 1000
                    END AS time_to_resolution_ms,
                    (SELECT COUNT(*) FROM incident_evidence WHERE incident_id = i.id) AS evidence_count,
                    EXISTS(
                        SELECT 1 FROM incident_evidence
                        WHERE incident_id = i.id AND recovery_executed = TRUE
                    ) AS recovery_attempted
                FROM incidents i
                WHERE i.tenant_id = :tenant_id
                  AND i.category = :category
                  AND i.id != :exclude_id
                  AND (i.lifecycle_state = 'RESOLVED' OR i.status = 'resolved')
                ORDER BY i.resolved_at DESC
                LIMIT :limit
            """),
            {
                "tenant_id": tenant_id,
                "category": category,
                "exclude_id": exclude_incident_id,
                "limit": limit,
            },
        )
        return [dict(row) for row in result.mappings()]


def get_postmortem_driver(session: AsyncSession) -> PostMortemDriver:
    """Factory function to get PostMortemDriver instance."""
    return PostMortemDriver(session)


__all__ = [
    "PostMortemDriver",
    "get_postmortem_driver",
]
