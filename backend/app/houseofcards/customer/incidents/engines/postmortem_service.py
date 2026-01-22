# Layer: L4 — Domain Engines
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Extract learnings and post-mortem insights from resolved incidents
# Callers: Incidents API (L2)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: docs/architecture/incidents/INCIDENTS_DOMAIN_SQL.md#8-res-o4

"""
Post-Mortem Service

Extracts learnings from resolved incidents:
- Resolution summaries
- Impact analysis
- Prevention recommendations
- Pattern correlations

Design Rules:
- Aggregation and analysis only
- Read-only (no writes)
- No cross-service calls
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
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
    """

    # Analysis constants
    SIMILAR_INCIDENT_LIMIT = 5
    INSIGHT_CONFIDENCE_THRESHOLD = 0.6

    def __init__(self, session: AsyncSession):
        self.session = session

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
        """
        baseline_days = min(baseline_days, 90)

        # Get category statistics
        stats_sql = text("""
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
        """)

        result = await self.session.execute(stats_sql, {
            "tenant_id": tenant_id,
            "category": category,
            "baseline_days": baseline_days,
        })
        row = result.mappings().first()
        if not row or row["total_incidents"] == 0:
            return None

        # Get common resolution methods
        methods_sql = text("""
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
            LIMIT 5
        """)

        methods_result = await self.session.execute(methods_sql, {
            "tenant_id": tenant_id,
            "category": category,
            "baseline_days": baseline_days,
        })

        common_methods = [
            (r["resolution_method"], r["method_count"])
            for r in methods_result.mappings()
        ]

        # Calculate recurrence rate
        recurrence_sql = text("""
            SELECT
                COUNT(DISTINCT DATE(created_at)) AS distinct_days,
                COUNT(*) AS total
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND category = :category
              AND created_at >= NOW() - INTERVAL '1 day' * :baseline_days
        """)

        recurrence_result = await self.session.execute(recurrence_sql, {
            "tenant_id": tenant_id,
            "category": category,
            "baseline_days": baseline_days,
        })
        recurrence_row = recurrence_result.mappings().first()

        distinct_days = recurrence_row["distinct_days"] if recurrence_row else 1
        total = recurrence_row["total"] if recurrence_row else 0
        recurrence_rate = round(total / max(distinct_days, 1), 2)

        # Generate insights based on the data
        insights = self._generate_category_insights(
            category=category,
            total_incidents=row["total_incidents"],
            resolved_count=row["resolved_count"],
            avg_resolution_time_ms=row["avg_resolution_time_ms"],
            common_methods=common_methods,
            recurrence_rate=recurrence_rate,
        )

        return CategoryLearnings(
            category=category,
            total_incidents=row["total_incidents"],
            resolved_count=row["resolved_count"],
            avg_resolution_time_ms=float(row["avg_resolution_time_ms"]) if row["avg_resolution_time_ms"] else None,
            common_resolution_methods=common_methods,
            recurrence_rate=recurrence_rate,
            insights=insights,
        )

    async def _get_resolution_summary(
        self,
        tenant_id: str,
        incident_id: str,
    ) -> Optional[ResolutionSummary]:
        """Get resolution summary for an incident."""
        sql = text("""
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
        """)

        result = await self.session.execute(sql, {
            "incident_id": incident_id,
            "tenant_id": tenant_id,
        })
        row = result.mappings().first()
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
        """Find similar resolved incidents."""
        if not category:
            return []

        sql = text("""
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
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "category": category,
            "exclude_id": exclude_incident_id,
            "limit": limit,
        })

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
            for row in result.mappings()
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
