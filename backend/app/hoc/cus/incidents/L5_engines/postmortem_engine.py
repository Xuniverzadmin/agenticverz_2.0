# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Incident (via driver)
#   Writes: none
# Role: Extract learnings and post-mortem insights from resolved incidents
# Callers: Incidents API (L2)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
# NOTE: Renamed postmortem_service.py → postmortem_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
#       Reclassified L4→L5 - Per HOC topology, engines are L5 (business logic)
#
# EXTRACTION STATUS: Phase-2.5A (2026-01-23)
# - All DB operations extracted to PostMortemDriver
# - Engine contains ONLY insight generation logic
# - NO sqlalchemy/sqlmodel imports at runtime
#
# ============================================================================
# L5 ENGINE INVARIANT — POSTMORTEM DOMAIN (LOCKED)
# ============================================================================
# This file MUST NOT import sqlalchemy/sqlmodel at runtime.
# All persistence is delegated to postmortem_driver.py.
# Business decisions (insight generation) ONLY.
#
# Any violation is a Phase-2.5 regression.
# ============================================================================

"""
Post-Mortem Engine - L4 Domain Logic

Extracts learnings from resolved incidents:
- Resolution summaries
- Impact analysis
- Prevention recommendations
- Pattern correlations

Architecture:
- All DB operations delegated to PostMortemDriver (L6)
- Engine contains only insight generation logic
- Read-only (no writes)

Design Rules:
- Aggregation and analysis only
- No cross-service calls
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

# L6 driver import (allowed)
from app.hoc.cus.incidents.L6_drivers.postmortem_driver import (
    PostMortemDriver,
    get_postmortem_driver,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ResolutionSummary:
    """Summary of how an incident was resolved."""
    incident_id: str
    title: str
    category: Optional[str]
    severity: str
    resolution_method: Optional[str]
    time_to_resolution_ms: Optional[int]
    evidence_count: int
    recovery_attempted: bool


@dataclass
class LearningInsight:
    """A learning extracted from incident analysis."""
    insight_type: str  # prevention, detection, response, communication
    description: str
    confidence: float
    supporting_incident_ids: list[str]


@dataclass
class PostMortemResult:
    """Result of post-mortem analysis for an incident."""
    incident_id: str
    resolution_summary: ResolutionSummary
    similar_incidents: list[ResolutionSummary]
    insights: list[LearningInsight]
    generated_at: datetime


@dataclass
class CategoryLearnings:
    """Aggregated learnings for a category."""
    category: str
    total_incidents: int
    resolved_count: int
    avg_resolution_time_ms: Optional[float]
    common_resolution_methods: list[tuple[str, int]]  # (method, count)
    recurrence_rate: float
    insights: list[LearningInsight]


class PostMortemService:
    """
    Extract learnings and post-mortem insights from incidents.

    RESPONSIBILITIES:
    - Generate resolution summaries
    - Find similar past incidents
    - Extract actionable insights
    - Aggregate category-level learnings

    FORBIDDEN:
    - Write to any table
    - Call other services
    - Modify incident data

    Note: All DB operations are delegated to PostMortemDriver (L6).
    This engine contains only insight generation logic.
    """

    # Analysis constants
    SIMILAR_INCIDENT_LIMIT = 5
    INSIGHT_CONFIDENCE_THRESHOLD = 0.6

    def __init__(
        self,
        session: "AsyncSession",
        driver: Optional[PostMortemDriver] = None,
    ):
        """
        Initialize with session and optional driver.

        Args:
            session: Database session (injected, not fetched)
            driver: Optional pre-configured driver (for testing)
        """
        self._session = session
        self._driver = driver or get_postmortem_driver(session)

    async def get_incident_learnings(
        self,
        tenant_id: str,
        incident_id: str,
    ) -> Optional[PostMortemResult]:
        """
        Get post-mortem learnings for a specific incident.

        Args:
            tenant_id: Tenant scope
            incident_id: Incident to analyze

        Returns:
            PostMortemResult with resolution summary, similar incidents, and insights
        """
        # Get the incident's resolution summary
        resolution = await self._get_resolution_summary(tenant_id, incident_id)
        if not resolution:
            return None

        # Find similar past incidents
        similar = await self._find_similar_incidents(
            tenant_id,
            incident_id,
            resolution.category,
            self.SIMILAR_INCIDENT_LIMIT,
        )

        # Extract insights from the incident and similar ones
        insights = await self._extract_insights(
            tenant_id,
            resolution,
            similar,
        )

        return PostMortemResult(
            incident_id=incident_id,
            resolution_summary=resolution,
            similar_incidents=similar,
            insights=insights,
            generated_at=datetime.now(timezone.utc),
        )

    async def get_category_learnings(
        self,
        tenant_id: str,
        category: str,
        baseline_days: int = 30,
    ) -> Optional[CategoryLearnings]:
        """
        Get aggregated learnings for a category.

        Args:
            tenant_id: Tenant scope
            category: Category to analyze
            baseline_days: Days to analyze (max 90)

        Returns:
            CategoryLearnings with aggregated insights

        PERSISTENCE: Delegated to driver.
        BUSINESS LOGIC: Insight generation stays here (L4).
        """
        baseline_days = min(baseline_days, 90)

        # Get category statistics via driver
        stats = await self._driver.fetch_category_stats(tenant_id, category, baseline_days)
        if not stats:
            return None

        # Get common resolution methods via driver
        methods_data = await self._driver.fetch_resolution_methods(
            tenant_id, category, baseline_days
        )
        common_methods = [
            (r["resolution_method"], r["method_count"])
            for r in methods_data
        ]

        # Get recurrence data via driver
        recurrence_data = await self._driver.fetch_recurrence_data(
            tenant_id, category, baseline_days
        )
        distinct_days = recurrence_data["distinct_days"]
        total = recurrence_data["total"]
        recurrence_rate = round(total / max(distinct_days, 1), 2)

        # Generate insights based on the data (business logic - stays in L4)
        insights = self._generate_category_insights(
            category=category,
            total_incidents=stats["total_incidents"],
            resolved_count=stats["resolved_count"],
            avg_resolution_time_ms=stats["avg_resolution_time_ms"],
            common_methods=common_methods,
            recurrence_rate=recurrence_rate,
        )

        return CategoryLearnings(
            category=category,
            total_incidents=stats["total_incidents"],
            resolved_count=stats["resolved_count"],
            avg_resolution_time_ms=float(stats["avg_resolution_time_ms"]) if stats["avg_resolution_time_ms"] else None,
            common_resolution_methods=common_methods,
            recurrence_rate=recurrence_rate,
            insights=insights,
        )

    async def _get_resolution_summary(
        self,
        tenant_id: str,
        incident_id: str,
    ) -> Optional[ResolutionSummary]:
        """
        Get resolution summary for an incident.

        PERSISTENCE: Delegated to driver.
        """
        row = await self._driver.fetch_resolution_summary(tenant_id, incident_id)
        if not row:
            return None

        return ResolutionSummary(
            incident_id=row["incident_id"],
            title=row["title"] or "Untitled",
            category=row["category"],
            severity=row["severity"],
            resolution_method=row["resolution_method"],
            time_to_resolution_ms=int(row["time_to_resolution_ms"]) if row["time_to_resolution_ms"] else None,
            evidence_count=row["evidence_count"],
            recovery_attempted=row["recovery_attempted"],
        )

    async def _find_similar_incidents(
        self,
        tenant_id: str,
        exclude_incident_id: str,
        category: Optional[str],
        limit: int,
    ) -> list[ResolutionSummary]:
        """
        Find similar resolved incidents.

        PERSISTENCE: Delegated to driver.
        """
        if not category:
            return []

        rows = await self._driver.fetch_similar_incidents(
            tenant_id, exclude_incident_id, category, limit
        )

        return [
            ResolutionSummary(
                incident_id=row["incident_id"],
                title=row["title"] or "Untitled",
                category=row["category"],
                severity=row["severity"],
                resolution_method=row["resolution_method"],
                time_to_resolution_ms=int(row["time_to_resolution_ms"]) if row["time_to_resolution_ms"] else None,
                evidence_count=row["evidence_count"],
                recovery_attempted=row["recovery_attempted"],
            )
            for row in rows
        ]

    async def _extract_insights(
        self,
        tenant_id: str,
        resolution: ResolutionSummary,
        similar: list[ResolutionSummary],
    ) -> list[LearningInsight]:
        """Extract insights from incident and similar incidents."""
        insights: list[LearningInsight] = []
        all_incidents = [resolution] + similar

        # Insight: Common resolution method
        if resolution.resolution_method:
            same_method_count = sum(
                1 for s in similar
                if s.resolution_method == resolution.resolution_method
            )
            if same_method_count > 0:
                confidence = min(0.5 + same_method_count * 0.1, 0.9)
                insights.append(LearningInsight(
                    insight_type="response",
                    description=f"Resolution method '{resolution.resolution_method}' "
                               f"was used in {same_method_count + 1} similar incidents",
                    confidence=round(confidence, 2),
                    supporting_incident_ids=[
                        s.incident_id for s in [resolution] + similar
                        if s.resolution_method == resolution.resolution_method
                    ],
                ))

        # Insight: Recovery pattern
        recovery_count = sum(1 for i in all_incidents if i.recovery_attempted)
        if recovery_count >= 2:
            confidence = min(0.6 + recovery_count * 0.08, 0.85)
            insights.append(LearningInsight(
                insight_type="prevention",
                description=f"Recovery was attempted in {recovery_count} of "
                           f"{len(all_incidents)} incidents in this category",
                confidence=round(confidence, 2),
                supporting_incident_ids=[
                    i.incident_id for i in all_incidents if i.recovery_attempted
                ],
            ))

        # Insight: Resolution time pattern
        resolved_with_time = [
            i for i in all_incidents
            if i.time_to_resolution_ms is not None
        ]
        resolved_times = [
            i.time_to_resolution_ms for i in resolved_with_time
            if i.time_to_resolution_ms is not None  # Type guard for pyright
        ]
        if len(resolved_times) >= 2:
            avg_time = sum(resolved_times) / len(resolved_times)
            avg_hours = avg_time / (1000 * 60 * 60)
            confidence = min(0.5 + len(resolved_with_time) * 0.1, 0.8)

            if avg_hours < 1:
                time_desc = f"{int(avg_time / 60000)} minutes"
            elif avg_hours < 24:
                time_desc = f"{avg_hours:.1f} hours"
            else:
                time_desc = f"{avg_hours / 24:.1f} days"

            insights.append(LearningInsight(
                insight_type="detection",
                description=f"Average resolution time for this category is {time_desc}",
                confidence=round(confidence, 2),
                supporting_incident_ids=[i.incident_id for i in resolved_with_time],
            ))

        return insights

    def _generate_category_insights(
        self,
        category: str,
        total_incidents: int,
        resolved_count: int,
        avg_resolution_time_ms: Optional[float],
        common_methods: list[tuple[str, int]],
        recurrence_rate: float,
    ) -> list[LearningInsight]:
        """Generate insights based on category statistics."""
        insights: list[LearningInsight] = []

        # Resolution rate insight
        if total_incidents > 0:
            resolution_rate = resolved_count / total_incidents
            if resolution_rate >= 0.8:
                insights.append(LearningInsight(
                    insight_type="response",
                    description=f"High resolution rate ({resolution_rate:.0%}) indicates "
                               f"effective incident handling for '{category}'",
                    confidence=round(0.7 + resolution_rate * 0.2, 2),
                    supporting_incident_ids=[],
                ))
            elif resolution_rate < 0.5:
                insights.append(LearningInsight(
                    insight_type="response",
                    description=f"Low resolution rate ({resolution_rate:.0%}) suggests "
                               f"'{category}' incidents may need escalation procedures",
                    confidence=round(0.6 + (1 - resolution_rate) * 0.2, 2),
                    supporting_incident_ids=[],
                ))

        # Recurrence insight
        if recurrence_rate > 2:
            insights.append(LearningInsight(
                insight_type="prevention",
                description=f"High recurrence rate ({recurrence_rate:.1f}/day) indicates "
                           f"need for root cause analysis in '{category}'",
                confidence=min(0.6 + recurrence_rate * 0.05, 0.9),
                supporting_incident_ids=[],
            ))

        # Resolution method insight
        if common_methods:
            top_method, top_count = common_methods[0]
            if top_count >= 3:
                insights.append(LearningInsight(
                    insight_type="response",
                    description=f"'{top_method}' is the most effective resolution method "
                               f"for '{category}' (used {top_count} times)",
                    confidence=round(0.6 + min(top_count * 0.05, 0.3), 2),
                    supporting_incident_ids=[],
                ))

        return insights
