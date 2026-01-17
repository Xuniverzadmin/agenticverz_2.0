# Layer: L4 — Domain Engines
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Detect structural patterns across incidents
# Callers: Incidents API (L2)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: docs/architecture/incidents/INCIDENTS_DOMAIN_SQL.md#5-act-o4

"""
Incident Pattern Service

Detects structural patterns across incidents:
- category_cluster: Multiple incidents in same category
- severity_spike: Multiple high/critical in short window
- cascade_failure: Multiple incidents from same source run
- resolution_pattern: Common resolution methods

Design Rules:
- Rule-based only (v1, no ML)
- Read-only (no writes)
- No cross-service calls
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class PatternMatch:
    """A detected incident pattern."""
    pattern_type: str
    dimension: str
    count: int
    incident_ids: list[str]
    confidence: float


@dataclass
class PatternResult:
    """Result of pattern detection."""
    patterns: list[PatternMatch]
    window_start: datetime
    window_end: datetime
    incidents_analyzed: int


class IncidentPatternService:
    """
    Detect structural patterns across incidents.

    RESPONSIBILITIES:
    - Detect category clusters
    - Detect severity spikes
    - Detect cascade failures
    - Return pattern type + confidence

    FORBIDDEN:
    - Write to any table
    - Call other services
    - Use machine learning
    """

    # Pattern thresholds (frozen constants)
    CATEGORY_CLUSTER_THRESHOLD = 3  # Min incidents in category to flag
    SEVERITY_SPIKE_THRESHOLD = 3  # Min high/critical in 1 hour
    CASCADE_THRESHOLD = 2  # Min incidents from same run

    def __init__(self, session: AsyncSession):
        self.session = session

    async def detect_patterns(
        self,
        tenant_id: str,
        window_hours: int = 24,
        limit: int = 10,
    ) -> PatternResult:
        """
        Detect all patterns within the time window.

        Args:
            tenant_id: Tenant scope
            window_hours: Hours to look back (max 168 = 7 days)
            limit: Max patterns per type

        Returns:
            PatternResult with all detected patterns
        """
        window_hours = min(window_hours, 168)  # Cap at 7 days
        window_start = datetime.utcnow() - timedelta(hours=window_hours)
        window_end = datetime.utcnow()

        all_patterns: list[PatternMatch] = []
        incidents_analyzed = 0

        # Detect each pattern type
        category_patterns = await self._detect_category_clusters(
            tenant_id, window_start, limit
        )
        all_patterns.extend(category_patterns)

        severity_patterns = await self._detect_severity_spikes(
            tenant_id, limit
        )
        all_patterns.extend(severity_patterns)

        cascade_patterns = await self._detect_cascade_failures(
            tenant_id, window_start, limit
        )
        all_patterns.extend(cascade_patterns)

        # Get incidents analyzed count
        count_sql = text("""
            SELECT COUNT(*)
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND created_at >= :window_start
        """)
        result = await self.session.execute(count_sql, {
            "tenant_id": tenant_id,
            "window_start": window_start,
        })
        incidents_analyzed = result.scalar() or 0

        return PatternResult(
            patterns=all_patterns,
            window_start=window_start,
            window_end=window_end,
            incidents_analyzed=incidents_analyzed,
        )

    async def _detect_category_clusters(
        self,
        tenant_id: str,
        window_start: datetime,
        limit: int,
    ) -> list[PatternMatch]:
        """Detect categories with multiple incidents."""
        sql = text("""
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
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "window_start": window_start,
            "threshold": self.CATEGORY_CLUSTER_THRESHOLD,
            "limit": limit,
        })

        patterns = []
        for row in result.mappings():
            count = row["incident_count"]
            # Confidence increases with count
            confidence = min(0.5 + (count - self.CATEGORY_CLUSTER_THRESHOLD) * 0.1, 0.95)

            patterns.append(PatternMatch(
                pattern_type="category_cluster",
                dimension=row["category"] or "unknown",
                count=count,
                incident_ids=row["incident_ids"][:10],  # Limit to 10
                confidence=round(confidence, 2),
            ))

        return patterns

    async def _detect_severity_spikes(
        self,
        tenant_id: str,
        limit: int,
    ) -> list[PatternMatch]:
        """Detect multiple high/critical incidents in short window."""
        sql = text("""
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
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "threshold": self.SEVERITY_SPIKE_THRESHOLD,
            "limit": limit,
        })

        patterns = []
        for row in result.mappings():
            count = row["incident_count"]
            severity = row["severity"]

            # Critical spikes get higher confidence
            base_confidence = 0.8 if severity == "critical" else 0.7
            confidence = min(base_confidence + (count - self.SEVERITY_SPIKE_THRESHOLD) * 0.05, 0.98)

            patterns.append(PatternMatch(
                pattern_type="severity_spike",
                dimension=severity,
                count=count,
                incident_ids=row["incident_ids"][:10],
                confidence=round(confidence, 2),
            ))

        return patterns

    async def _detect_cascade_failures(
        self,
        tenant_id: str,
        window_start: datetime,
        limit: int,
    ) -> list[PatternMatch]:
        """Detect multiple incidents from same source run."""
        sql = text("""
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
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "window_start": window_start,
            "threshold": self.CASCADE_THRESHOLD,
            "limit": limit,
        })

        patterns = []
        for row in result.mappings():
            count = row["incident_count"]
            confidence = min(0.75 + (count - self.CASCADE_THRESHOLD) * 0.1, 0.95)

            patterns.append(PatternMatch(
                pattern_type="cascade_failure",
                dimension=row["source_run_id"],
                count=count,
                incident_ids=row["incident_ids"][:10],
                confidence=round(confidence, 2),
            ))

        return patterns
