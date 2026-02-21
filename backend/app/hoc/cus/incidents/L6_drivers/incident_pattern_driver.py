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
# Role: Data access for incident pattern detection operations (async)
# Callers: IncidentPatternEngine (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for incident pattern detection.
# NO business logic - only DB operations.
# Business logic (confidence calculation, threshold decisions) stays in L4 engine.
#
# EXTRACTION STATUS:
# - 2026-01-23: Initial extraction from incident_pattern_service.py (PIN-468)
#
# ============================================================================
# L6 DRIVER INVENTORY — INCIDENT PATTERN DOMAIN (CANONICAL)
# ============================================================================
# Method                              | Purpose
# ----------------------------------- | ----------------------------------------
# fetch_incidents_count               | Count incidents in time window
# fetch_category_clusters             | Get incidents grouped by category
# fetch_severity_spikes               | Get high/critical incidents in last hour
# fetch_cascade_failures              | Get incidents grouped by source run
# ============================================================================
# This is the SINGLE persistence authority for incident pattern reads.
# Do NOT create competing drivers. Extend this file.
# ============================================================================

"""
Incident Pattern Driver (L6)

Pure database operations for incident pattern detection.
All business logic stays in L4 engine.

Operations:
- Incident count queries
- Category cluster aggregation
- Severity spike detection
- Cascade failure grouping

NO business logic:
- NO confidence calculation (L4)
- NO threshold decisions (L4)
- NO pattern type determination (L4)

Reference: PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.drivers.incident_pattern")


class IncidentPatternDriver:
    """
    L6 driver for incident pattern detection operations (async).

    Pure database access - no business logic.
    All operations are READ-ONLY.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self._session = session

    async def fetch_incidents_count(
        self,
        tenant_id: str,
        window_start: datetime,
    ) -> int:
        """
        Count incidents within time window.

        Args:
            tenant_id: Tenant scope
            window_start: Start of time window

        Returns:
            Count of incidents in window
        """
        result = await self._session.execute(
            text("""
                SELECT COUNT(*)
                FROM incidents
                WHERE tenant_id = :tenant_id
                  AND created_at >= :window_start
            """),
            {
                "tenant_id": tenant_id,
                "window_start": window_start,
            },
        )
        return result.scalar() or 0

    async def fetch_category_clusters(
        self,
        tenant_id: str,
        window_start: datetime,
        threshold: int,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch incidents grouped by category for cluster detection.

        Args:
            tenant_id: Tenant scope
            window_start: Start of time window
            threshold: Minimum incidents to include
            limit: Max categories to return

        Returns:
            List of dicts with category, incident_count, incident_ids
        """
        result = await self._session.execute(
            text("""
                SELECT
                    category,
                    COUNT(*) AS incident_count,
                    array_agg(id ORDER BY created_at DESC) AS incident_ids
                FROM incidents
                WHERE tenant_id = :tenant_id
                  AND created_at >= :window_start
                  AND category IS NOT NULL
                GROUP BY category
                HAVING COUNT(*) >= :threshold
                ORDER BY incident_count DESC
                LIMIT :limit
            """),
            {
                "tenant_id": tenant_id,
                "window_start": window_start,
                "threshold": threshold,
                "limit": limit,
            },
        )
        return [dict(row) for row in result.mappings()]

    async def fetch_severity_spikes(
        self,
        tenant_id: str,
        threshold: int,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch high/critical incidents in the last hour.

        Args:
            tenant_id: Tenant scope
            threshold: Minimum incidents to include
            limit: Max severity groups to return

        Returns:
            List of dicts with severity, incident_count, incident_ids
        """
        result = await self._session.execute(
            text("""
                SELECT
                    severity,
                    COUNT(*) AS incident_count,
                    array_agg(id ORDER BY created_at DESC) AS incident_ids
                FROM incidents
                WHERE tenant_id = :tenant_id
                  AND severity IN ('critical', 'high')
                  AND created_at >= NOW() - INTERVAL '1 hour'
                  AND (lifecycle_state = 'ACTIVE' OR status = 'open')
                GROUP BY severity
                HAVING COUNT(*) >= :threshold
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                    END,
                    incident_count DESC
                LIMIT :limit
            """),
            {
                "tenant_id": tenant_id,
                "threshold": threshold,
                "limit": limit,
            },
        )
        return [dict(row) for row in result.mappings()]

    async def fetch_cascade_failures(
        self,
        tenant_id: str,
        window_start: datetime,
        threshold: int,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch incidents grouped by source run for cascade detection.

        Args:
            tenant_id: Tenant scope
            window_start: Start of time window
            threshold: Minimum incidents to include
            limit: Max source runs to return

        Returns:
            List of dicts with source_run_id, incident_count, incident_ids
        """
        result = await self._session.execute(
            text("""
                SELECT
                    source_run_id,
                    COUNT(*) AS incident_count,
                    array_agg(id ORDER BY created_at DESC) AS incident_ids
                FROM incidents
                WHERE tenant_id = :tenant_id
                  AND source_run_id IS NOT NULL
                  AND created_at >= :window_start
                GROUP BY source_run_id
                HAVING COUNT(*) >= :threshold
                ORDER BY incident_count DESC
                LIMIT :limit
            """),
            {
                "tenant_id": tenant_id,
                "window_start": window_start,
                "threshold": threshold,
                "limit": limit,
            },
        )
        return [dict(row) for row in result.mappings()]


def get_incident_pattern_driver(session: AsyncSession) -> IncidentPatternDriver:
    """Factory function to get IncidentPatternDriver instance."""
    return IncidentPatternDriver(session)


__all__ = [
    "IncidentPatternDriver",
    "get_incident_pattern_driver",
]
