# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Detect structural patterns across incidents
# Callers: Incidents API (L2)
# Allowed Imports: L6 drivers (via injection), L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel (at runtime)
# Reference: PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
# NOTE: Renamed incident_pattern_service.py → incident_pattern_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
#       Reclassified L4→L5 - Per HOC topology, engines are L5 (business logic)
#
# EXTRACTION STATUS: Phase-2.5A (2026-01-23)
# - All DB operations extracted to IncidentPatternDriver
# - Engine contains ONLY pattern detection logic
# - NO sqlalchemy/sqlmodel imports at runtime
#
# ============================================================================
# L5 ENGINE INVARIANT — INCIDENT PATTERN DOMAIN (LOCKED)
# ============================================================================
# This file MUST NOT import sqlalchemy/sqlmodel at runtime.
# All persistence is delegated to incident_pattern_driver.py.
# Business decisions (confidence calculation, thresholds) ONLY.
#
# Any violation is a Phase-2.5 regression.
# ============================================================================

"""
Incident Pattern Engine - L4 Domain Logic

Detects structural patterns across incidents:
- category_cluster: Multiple incidents in same category
- severity_spike: Multiple high/critical in short window
- cascade_failure: Multiple incidents from same source run
- resolution_pattern: Common resolution methods

Architecture:
- All DB operations delegated to IncidentPatternDriver (L6)
- Engine contains only pattern detection logic
- Read-only (no writes)

Design Rules:
- Rule-based only (v1, no ML)
- No cross-service calls
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

# L6 driver import (allowed)
from app.hoc.cus.incidents.drivers.incident_pattern_driver import (
    IncidentPatternDriver,
    get_incident_pattern_driver,
)
from app.hoc.cus.general.utils.time import utc_now

if TYPE_CHECKING:
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

    Note: All DB operations are delegated to IncidentPatternDriver (L6).
    This engine contains only pattern detection logic.
    """

    # Pattern thresholds (frozen constants)
    CATEGORY_CLUSTER_THRESHOLD = 3  # Min incidents in category to flag
    SEVERITY_SPIKE_THRESHOLD = 3  # Min high/critical in 1 hour
    CASCADE_THRESHOLD = 2  # Min incidents from same run

    def __init__(
        self,
        session: "AsyncSession",
        driver: Optional[IncidentPatternDriver] = None,
    ):
        """
        Initialize with session and optional driver.

        Args:
            session: Database session (injected, not fetched)
            driver: Optional pre-configured driver (for testing)
        """
        self._session = session
        self._driver = driver or get_incident_pattern_driver(session)

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

        PERSISTENCE: Delegated to driver.
        BUSINESS LOGIC: Pattern detection and confidence stays here (L4).
        """
        window_hours = min(window_hours, 168)  # Cap at 7 days
        window_start = utc_now() - timedelta(hours=window_hours)
        window_end = utc_now()

        all_patterns: list[PatternMatch] = []

        # Detect each pattern type (business logic stays in engine)
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

        # Get incidents analyzed count via driver
        incidents_analyzed = await self._driver.fetch_incidents_count(
            tenant_id, window_start
        )

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
        """
        Detect categories with multiple incidents.

        PERSISTENCE: Delegated to driver.
        BUSINESS LOGIC: Confidence calculation stays here (L4).
        """
        rows = await self._driver.fetch_category_clusters(
            tenant_id, window_start, self.CATEGORY_CLUSTER_THRESHOLD, limit
        )

        patterns = []
        for row in rows:
            count = row["incident_count"]
            # Confidence increases with count (business logic)
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
        """
        Detect multiple high/critical incidents in short window.

        PERSISTENCE: Delegated to driver.
        BUSINESS LOGIC: Confidence calculation stays here (L4).
        """
        rows = await self._driver.fetch_severity_spikes(
            tenant_id, self.SEVERITY_SPIKE_THRESHOLD, limit
        )

        patterns = []
        for row in rows:
            count = row["incident_count"]
            severity = row["severity"]

            # Critical spikes get higher confidence (business logic)
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
        """
        Detect multiple incidents from same source run.

        PERSISTENCE: Delegated to driver.
        BUSINESS LOGIC: Confidence calculation stays here (L4).
        """
        rows = await self._driver.fetch_cascade_failures(
            tenant_id, window_start, self.CASCADE_THRESHOLD, limit
        )

        patterns = []
        for row in rows:
            count = row["incident_count"]
            # Confidence increases with count (business logic)
            confidence = min(0.75 + (count - self.CASCADE_THRESHOLD) * 0.1, 0.95)

            patterns.append(PatternMatch(
                pattern_type="cascade_failure",
                dimension=row["source_run_id"],
                count=count,
                incident_ids=row["incident_ids"][:10],
                confidence=round(confidence, 2),
            ))

        return patterns
