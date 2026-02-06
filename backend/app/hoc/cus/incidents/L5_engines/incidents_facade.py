# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Location: hoc/cus/incidents/L5_engines/incidents_facade.py
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Incident (via driver)
#   Writes: none
# Role: Incidents domain facade - unified entry point for incident management operations
# Callers: L2 incidents API (incidents.py)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
#
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.
#
# All DB operations extracted to incidents_facade_driver.py (L6).
# This facade now delegates to driver, no direct sqlalchemy imports.

"""
Incidents Domain Facade (L5)

Unified facade for incident management operations.

Provides:
- List incidents: active, resolved, historical
- Get incident detail
- Get incidents by run
- Pattern detection (ACT-O5)
- Recurrence analysis (HIST-O3)
- Cost impact analysis (RES-O3)
- Metrics
- Historical trend/distribution/cost-trend
- Post-mortem learnings (RES-O4)

All operations are tenant-scoped for isolation.

Architecture:
- Facade → Driver (L6) for DB operations
- Facade → Engine (L4) for business logic delegation
- No direct sqlalchemy imports
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.hoc.cus.incidents.L6_drivers.incidents_facade_driver import (
    IncidentsFacadeDriver,
    IncidentSnapshot,
)


# =============================================================================
# Result Types - Incident Summary
# =============================================================================


@dataclass
class IncidentSummaryResult:
    """Incident summary for list view (O2)."""

    incident_id: str
    tenant_id: str
    lifecycle_state: str
    severity: str
    category: str
    title: str
    description: Optional[str]
    llm_run_id: Optional[str]
    cause_type: str
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    is_synthetic: bool = False
    policy_ref: Optional[str] = None
    violation_ref: Optional[str] = None


@dataclass
class PaginationResult:
    """Pagination metadata."""

    limit: int
    offset: int
    next_offset: Optional[int]


@dataclass
class IncidentListResult:
    """Incidents list response."""

    items: list[IncidentSummaryResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]
    pagination: PaginationResult


# =============================================================================
# Result Types - Incident Detail
# =============================================================================


@dataclass
class IncidentDetailResult:
    """Incident detail response (O3)."""

    incident_id: str
    tenant_id: str
    lifecycle_state: str
    severity: str
    category: str
    title: str
    description: Optional[str]
    llm_run_id: Optional[str]
    source_run_id: Optional[str]
    cause_type: str
    error_code: Optional[str]
    error_message: Optional[str]
    affected_agent_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    is_synthetic: bool = False
    synthetic_scenario_id: Optional[str] = None
    policy_id: Optional[str] = None
    policy_ref: Optional[str] = None
    violation_id: Optional[str] = None
    violation_ref: Optional[str] = None
    lesson_ref: Optional[str] = None


@dataclass
class IncidentsByRunResult:
    """Incidents by run response."""

    run_id: str
    incidents: list[IncidentSummaryResult]
    total: int


# =============================================================================
# Result Types - Pattern Detection (ACT-O5)
# =============================================================================


@dataclass
class PatternMatchResult:
    """A detected incident pattern."""

    pattern_type: str  # category_cluster, severity_spike, cascade_failure
    dimension: str  # category name, severity level, or source_run_id
    count: int
    incident_ids: list[str]
    confidence: float


@dataclass
class PatternDetectionResult:
    """Pattern detection response."""

    patterns: list[PatternMatchResult]
    window_hours: int
    window_start: datetime
    window_end: datetime
    incidents_analyzed: int


# =============================================================================
# Result Types - Recurrence Analysis (HIST-O3)
# =============================================================================


@dataclass
class RecurrenceGroupResult:
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
class RecurrenceAnalysisResult:
    """Recurrence analysis response."""

    groups: list[RecurrenceGroupResult]
    baseline_days: int
    total_recurring: int
    generated_at: datetime


# =============================================================================
# Result Types - Cost Impact (RES-O3)
# =============================================================================


@dataclass
class CostImpactSummaryResult:
    """Cost impact summary for an incident category."""

    category: str
    incident_count: int
    total_cost_impact: float
    avg_cost_impact: float
    resolution_method: Optional[str]


@dataclass
class CostImpactResult:
    """Cost impact analysis response."""

    summaries: list[CostImpactSummaryResult]
    total_cost_impact: float
    baseline_days: int
    generated_at: datetime


# =============================================================================
# Result Types - Metrics
# =============================================================================


@dataclass
class IncidentMetricsResult:
    """Incident metrics response."""

    active_count: int
    acked_count: int
    resolved_count: int
    total_count: int
    avg_time_to_containment_ms: Optional[int]
    median_time_to_containment_ms: Optional[int]
    avg_time_to_resolution_ms: Optional[int]
    median_time_to_resolution_ms: Optional[int]
    sla_met_count: int
    sla_breached_count: int
    sla_compliance_rate: Optional[float]
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    window_days: int
    generated_at: datetime


# =============================================================================
# Result Types - Historical Analytics
# =============================================================================


@dataclass
class HistoricalTrendDataPointResult:
    """A single data point in a historical trend."""

    period: str
    incident_count: int
    resolved_count: int
    avg_resolution_time_ms: Optional[int]


@dataclass
class HistoricalTrendResult:
    """Historical trend response."""

    data_points: list[HistoricalTrendDataPointResult]
    granularity: str
    window_days: int
    total_incidents: int
    generated_at: datetime


@dataclass
class HistoricalDistributionEntryResult:
    """A single entry in the distribution."""

    dimension: str  # category, severity, cause_type
    value: str
    count: int
    percentage: float


@dataclass
class HistoricalDistributionResult:
    """Historical distribution response."""

    by_category: list[HistoricalDistributionEntryResult]
    by_severity: list[HistoricalDistributionEntryResult]
    by_cause_type: list[HistoricalDistributionEntryResult]
    window_days: int
    total_incidents: int
    generated_at: datetime


@dataclass
class CostTrendDataPointResult:
    """A single data point in the cost trend."""

    period: str
    total_cost: float
    incident_count: int
    avg_cost_per_incident: float


@dataclass
class CostTrendResult:
    """Cost trend response."""

    data_points: list[CostTrendDataPointResult]
    granularity: str
    window_days: int
    total_cost: float
    total_incidents: int
    generated_at: datetime


# =============================================================================
# Result Types - Learnings (RES-O4)
# =============================================================================


@dataclass
class LearningInsightResult:
    """A learning insight from incident analysis."""

    insight_type: str  # prevention, detection, response, communication
    description: str
    confidence: float
    supporting_incident_ids: list[str]


@dataclass
class ResolutionSummaryResult:
    """Summary of incident resolution."""

    incident_id: str
    title: str
    category: Optional[str]
    severity: str
    resolution_method: Optional[str]
    time_to_resolution_ms: Optional[int]
    evidence_count: int
    recovery_attempted: bool


@dataclass
class LearningsResult:
    """Incident learnings response."""

    incident_id: str
    resolution_summary: ResolutionSummaryResult
    similar_incidents: list[ResolutionSummaryResult]
    insights: list[LearningInsightResult]
    generated_at: datetime


# =============================================================================
# Incidents Facade
# =============================================================================


class IncidentsFacade:
    """
    Unified facade for incident management.

    Provides:
    - List incidents: active, resolved, historical
    - Get incident detail
    - Get incidents by run
    - Metrics
    - Cost impact analysis

    All operations are tenant-scoped for isolation.

    Architecture:
    - Delegates DB operations to IncidentsFacadeDriver (L6)
    - No direct sqlalchemy access
    """

    # -------------------------------------------------------------------------
    # List Operations
    # -------------------------------------------------------------------------

    async def list_active_incidents(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        cause_type: Optional[str] = None,
        is_synthetic: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> IncidentListResult:
        """List active incidents (ACTIVE + ACKED states)."""
        driver = IncidentsFacadeDriver(session)

        snapshot = await driver.fetch_active_incidents(
            tenant_id=tenant_id,
            severity=severity,
            category=category,
            cause_type=cause_type,
            is_synthetic=is_synthetic,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        filters_applied: dict[str, Any] = {
            "tenant_id": tenant_id,
            "topic": "ACTIVE",
        }
        if severity:
            filters_applied["severity"] = severity
        if category:
            filters_applied["category"] = category
        if cause_type:
            filters_applied["cause_type"] = cause_type
        if is_synthetic is not None:
            filters_applied["is_synthetic"] = is_synthetic
        if created_after:
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            filters_applied["created_before"] = created_before.isoformat()

        items = [self._snapshot_to_summary(s) for s in snapshot.items]
        has_more = offset + len(items) < snapshot.total
        next_offset = offset + limit if has_more else None

        return IncidentListResult(
            items=items,
            total=snapshot.total,
            has_more=has_more,
            filters_applied=filters_applied,
            pagination=PaginationResult(limit=limit, offset=offset, next_offset=next_offset),
        )

    async def list_resolved_incidents(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        cause_type: Optional[str] = None,
        is_synthetic: Optional[bool] = None,
        resolved_after: Optional[datetime] = None,
        resolved_before: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "resolved_at",
        sort_order: str = "desc",
    ) -> IncidentListResult:
        """List resolved incidents."""
        driver = IncidentsFacadeDriver(session)

        snapshot = await driver.fetch_resolved_incidents(
            tenant_id=tenant_id,
            severity=severity,
            category=category,
            cause_type=cause_type,
            is_synthetic=is_synthetic,
            resolved_after=resolved_after,
            resolved_before=resolved_before,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        filters_applied: dict[str, Any] = {
            "tenant_id": tenant_id,
            "topic": "RESOLVED",
        }
        if severity:
            filters_applied["severity"] = severity
        if category:
            filters_applied["category"] = category
        if cause_type:
            filters_applied["cause_type"] = cause_type
        if is_synthetic is not None:
            filters_applied["is_synthetic"] = is_synthetic
        if resolved_after:
            filters_applied["resolved_after"] = resolved_after.isoformat()
        if resolved_before:
            filters_applied["resolved_before"] = resolved_before.isoformat()

        items = [self._snapshot_to_summary(s) for s in snapshot.items]
        has_more = offset + len(items) < snapshot.total
        next_offset = offset + limit if has_more else None

        return IncidentListResult(
            items=items,
            total=snapshot.total,
            has_more=has_more,
            filters_applied=filters_applied,
            pagination=PaginationResult(limit=limit, offset=offset, next_offset=next_offset),
        )

    async def list_historical_incidents(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        retention_days: int = 30,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        cause_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "resolved_at",
        sort_order: str = "desc",
    ) -> IncidentListResult:
        """List historical incidents (resolved beyond retention window)."""
        driver = IncidentsFacadeDriver(session)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        snapshot = await driver.fetch_historical_incidents(
            tenant_id=tenant_id,
            cutoff_date=cutoff_date,
            severity=severity,
            category=category,
            cause_type=cause_type,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        filters_applied: dict[str, Any] = {
            "tenant_id": tenant_id,
            "topic": "HISTORICAL",
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
        }
        if severity:
            filters_applied["severity"] = severity
        if category:
            filters_applied["category"] = category
        if cause_type:
            filters_applied["cause_type"] = cause_type

        items = [self._snapshot_to_summary(s) for s in snapshot.items]
        has_more = offset + len(items) < snapshot.total
        next_offset = offset + limit if has_more else None

        return IncidentListResult(
            items=items,
            total=snapshot.total,
            has_more=has_more,
            filters_applied=filters_applied,
            pagination=PaginationResult(limit=limit, offset=offset, next_offset=next_offset),
        )

    # -------------------------------------------------------------------------
    # Deprecated List (full filter set)
    # -------------------------------------------------------------------------

    async def list_incidents(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        topic: Optional[str] = None,
        lifecycle_state: Optional[str] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        cause_type: Optional[str] = None,
        is_synthetic: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> IncidentListResult:
        """List incidents with full filter set (deprecated endpoint)."""
        driver = IncidentsFacadeDriver(session)

        snapshot = await driver.fetch_all_incidents(
            tenant_id=tenant_id,
            topic=topic,
            lifecycle_state=lifecycle_state,
            severity=severity,
            category=category,
            cause_type=cause_type,
            is_synthetic=is_synthetic,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        filters_applied: dict[str, Any] = {"tenant_id": tenant_id}
        if topic:
            filters_applied["topic"] = topic
        elif lifecycle_state:
            filters_applied["lifecycle_state"] = lifecycle_state
        if severity:
            filters_applied["severity"] = severity
        if category:
            filters_applied["category"] = category
        if cause_type:
            filters_applied["cause_type"] = cause_type
        if is_synthetic is not None:
            filters_applied["is_synthetic"] = is_synthetic
        if created_after:
            filters_applied["created_after"] = created_after.isoformat()
        if created_before:
            filters_applied["created_before"] = created_before.isoformat()

        items = [self._snapshot_to_summary(s) for s in snapshot.items]
        has_more = offset + len(items) < snapshot.total
        next_offset = offset + limit if has_more else None

        return IncidentListResult(
            items=items,
            total=snapshot.total,
            has_more=has_more,
            filters_applied=filters_applied,
            pagination=PaginationResult(limit=limit, offset=offset, next_offset=next_offset),
        )

    # -------------------------------------------------------------------------
    # Detail Operations
    # -------------------------------------------------------------------------

    async def get_incident_detail(
        self,
        session: "AsyncSession",
        tenant_id: str,
        incident_id: str,
    ) -> Optional[IncidentDetailResult]:
        """Get incident detail. Tenant isolation enforced."""
        driver = IncidentsFacadeDriver(session)

        snapshot = await driver.fetch_incident_by_id(
            tenant_id=tenant_id,
            incident_id=incident_id,
        )

        if not snapshot:
            return None

        return IncidentDetailResult(
            incident_id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            lifecycle_state=snapshot.lifecycle_state or "ACTIVE",
            severity=snapshot.severity or "medium",
            category=snapshot.category or "UNKNOWN",
            title=snapshot.title or "Untitled Incident",
            description=snapshot.description,
            llm_run_id=snapshot.llm_run_id,
            source_run_id=snapshot.source_run_id,
            cause_type=snapshot.cause_type or "SYSTEM",
            error_code=snapshot.error_code,
            error_message=snapshot.error_message,
            affected_agent_id=snapshot.affected_agent_id,
            created_at=snapshot.created_at,
            updated_at=snapshot.updated_at,
            resolved_at=snapshot.resolved_at,
            is_synthetic=snapshot.is_synthetic or False,
            synthetic_scenario_id=snapshot.synthetic_scenario_id,
        )

    async def get_incidents_for_run(
        self,
        session: "AsyncSession",
        tenant_id: str,
        run_id: str,
    ) -> IncidentsByRunResult:
        """Get all incidents linked to a specific run."""
        driver = IncidentsFacadeDriver(session)

        snapshots = await driver.fetch_incidents_by_run(
            tenant_id=tenant_id,
            run_id=run_id,
        )

        items = [self._snapshot_to_summary(s) for s in snapshots]

        return IncidentsByRunResult(
            run_id=run_id,
            incidents=items,
            total=len(items),
        )

    # -------------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------------

    async def get_metrics(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        window_days: int = 30,
    ) -> IncidentMetricsResult:
        """Get incident metrics. Backend-computed, deterministic."""
        driver = IncidentsFacadeDriver(session)

        snapshot = await driver.fetch_metrics_aggregates(
            tenant_id=tenant_id,
            window_days=window_days,
        )

        if not snapshot:
            return IncidentMetricsResult(
                active_count=0,
                acked_count=0,
                resolved_count=0,
                total_count=0,
                avg_time_to_containment_ms=None,
                median_time_to_containment_ms=None,
                avg_time_to_resolution_ms=None,
                median_time_to_resolution_ms=None,
                sla_met_count=0,
                sla_breached_count=0,
                sla_compliance_rate=None,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                window_days=window_days,
                generated_at=datetime.now(timezone.utc),
            )

        sla_total = snapshot.sla_met_count + snapshot.sla_breached_count
        sla_compliance_rate = None
        if sla_total > 0:
            sla_compliance_rate = round(snapshot.sla_met_count / sla_total * 100, 2)

        return IncidentMetricsResult(
            active_count=snapshot.active_count,
            acked_count=snapshot.acked_count,
            resolved_count=snapshot.resolved_count,
            total_count=snapshot.total_count,
            avg_time_to_containment_ms=snapshot.avg_time_to_containment_ms,
            median_time_to_containment_ms=snapshot.median_time_to_containment_ms,
            avg_time_to_resolution_ms=snapshot.avg_time_to_resolution_ms,
            median_time_to_resolution_ms=snapshot.median_time_to_resolution_ms,
            sla_met_count=snapshot.sla_met_count,
            sla_breached_count=snapshot.sla_breached_count,
            sla_compliance_rate=sla_compliance_rate,
            critical_count=snapshot.critical_count,
            high_count=snapshot.high_count,
            medium_count=snapshot.medium_count,
            low_count=snapshot.low_count,
            window_days=window_days,
            generated_at=datetime.now(timezone.utc),
        )

    # -------------------------------------------------------------------------
    # Cost Impact Analysis
    # -------------------------------------------------------------------------

    async def analyze_cost_impact(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        baseline_days: int = 30,
        limit: int = 20,
    ) -> CostImpactResult:
        """Analyze cost impact across incidents."""
        driver = IncidentsFacadeDriver(session)
        baseline_days = min(baseline_days, 90)

        rows = await driver.fetch_cost_impact_data(
            tenant_id=tenant_id,
            baseline_days=baseline_days,
            limit=limit,
        )

        summaries: list[CostImpactSummaryResult] = []
        total_cost = 0.0

        for row in rows:
            total_cost += row.total_cost_impact
            summaries.append(CostImpactSummaryResult(
                category=row.category,
                incident_count=row.incident_count,
                total_cost_impact=row.total_cost_impact,
                avg_cost_impact=row.avg_cost_impact,
                resolution_method=row.resolution_method,
            ))

        return CostImpactResult(
            summaries=summaries,
            total_cost_impact=total_cost,
            baseline_days=baseline_days,
            generated_at=datetime.now(timezone.utc),
        )

    # -------------------------------------------------------------------------
    # Historical Analytics
    # -------------------------------------------------------------------------

    async def get_historical_trend(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        window_days: int = 90,
        granularity: str = "week",
    ) -> HistoricalTrendResult:
        """Get historical trend. Backend-computed, deterministic."""
        driver = IncidentsFacadeDriver(session)

        rows = await driver.fetch_historical_trend(
            tenant_id=tenant_id,
            window_days=window_days,
            trunc_unit=granularity,
        )

        data_points: list[HistoricalTrendDataPointResult] = []
        total_incidents = 0

        for row in rows:
            total_incidents += row.incident_count
            data_points.append(HistoricalTrendDataPointResult(
                period=row.period,
                incident_count=row.incident_count,
                resolved_count=row.resolved_count,
                avg_resolution_time_ms=row.avg_resolution_time_ms,
            ))

        return HistoricalTrendResult(
            data_points=data_points,
            granularity=granularity,
            window_days=window_days,
            total_incidents=total_incidents,
            generated_at=datetime.now(timezone.utc),
        )

    async def get_historical_distribution(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        window_days: int = 90,
    ) -> HistoricalDistributionResult:
        """Get historical distribution. Backend-computed, deterministic."""
        driver = IncidentsFacadeDriver(session)

        data = await driver.fetch_historical_distribution(
            tenant_id=tenant_id,
            window_days=window_days,
        )

        total_incidents = data["total_incidents"]

        by_category = [
            HistoricalDistributionEntryResult(
                dimension=r.dimension,
                value=r.value,
                count=r.count,
                percentage=round(r.count / total_incidents * 100, 2) if total_incidents > 0 else 0,
            )
            for r in data["by_category"]
        ]

        by_severity = [
            HistoricalDistributionEntryResult(
                dimension=r.dimension,
                value=r.value,
                count=r.count,
                percentage=round(r.count / total_incidents * 100, 2) if total_incidents > 0 else 0,
            )
            for r in data["by_severity"]
        ]

        by_cause_type = [
            HistoricalDistributionEntryResult(
                dimension=r.dimension,
                value=r.value,
                count=r.count,
                percentage=round(r.count / total_incidents * 100, 2) if total_incidents > 0 else 0,
            )
            for r in data["by_cause_type"]
        ]

        return HistoricalDistributionResult(
            by_category=by_category,
            by_severity=by_severity,
            by_cause_type=by_cause_type,
            window_days=window_days,
            total_incidents=total_incidents,
            generated_at=datetime.now(timezone.utc),
        )

    async def get_historical_cost_trend(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        window_days: int = 90,
        granularity: str = "week",
    ) -> CostTrendResult:
        """Get historical cost trend. Backend-computed, deterministic."""
        driver = IncidentsFacadeDriver(session)

        rows = await driver.fetch_historical_cost_trend(
            tenant_id=tenant_id,
            window_days=window_days,
            granularity=granularity,
        )

        data_points: list[CostTrendDataPointResult] = []
        total_cost = 0.0
        total_incidents = 0

        for row in rows:
            cost = row.total_cost
            count = row.incident_count
            total_cost += cost
            total_incidents += count
            avg_cost = cost / count if count > 0 else 0.0

            data_points.append(CostTrendDataPointResult(
                period=row.period,
                total_cost=round(cost, 2),
                incident_count=count,
                avg_cost_per_incident=round(avg_cost, 2),
            ))

        return CostTrendResult(
            data_points=data_points,
            granularity=granularity,
            window_days=window_days,
            total_cost=round(total_cost, 2),
            total_incidents=total_incidents,
            generated_at=datetime.now(timezone.utc),
        )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _snapshot_to_summary(self, snapshot: IncidentSnapshot) -> IncidentSummaryResult:
        """Convert snapshot to summary result. Applies business defaults."""
        return IncidentSummaryResult(
            incident_id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            lifecycle_state=snapshot.lifecycle_state or "ACTIVE",
            severity=snapshot.severity or "medium",
            category=snapshot.category or "UNKNOWN",
            title=snapshot.title or "Untitled Incident",
            description=snapshot.description,
            llm_run_id=snapshot.llm_run_id,
            cause_type=snapshot.cause_type or "SYSTEM",
            error_code=snapshot.error_code,
            error_message=snapshot.error_message,
            created_at=snapshot.created_at,
            resolved_at=snapshot.resolved_at,
            is_synthetic=snapshot.is_synthetic or False,
        )

    # -------------------------------------------------------------------------
    # Pattern Detection (ACT-O5)
    # -------------------------------------------------------------------------

    async def detect_patterns(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        window_hours: int = 24,
        limit: int = 10,
    ) -> PatternDetectionResult:
        """
        Detect incident patterns.

        Identifies:
        - category_cluster: Multiple incidents in same category
        - severity_spike: Multiple high/critical incidents in short window
        - cascade_failure: Multiple incidents from same source run
        """
        # L5 engine import (migrated to HOC per SWEEP-05)
        from app.hoc.cus.incidents.L5_engines.incident_pattern_engine import IncidentPatternService

        service = IncidentPatternService(session)
        result = await service.detect_patterns(
            tenant_id=tenant_id,
            window_hours=window_hours,
            limit=limit,
        )

        # Map service result to facade result type
        return PatternDetectionResult(
            patterns=[
                PatternMatchResult(
                    pattern_type=p.pattern_type,
                    dimension=p.dimension,
                    count=p.count,
                    incident_ids=p.incident_ids,
                    confidence=p.confidence,
                )
                for p in result.patterns
            ],
            window_hours=window_hours,
            window_start=result.window_start,
            window_end=result.window_end,
            incidents_analyzed=result.incidents_analyzed,
        )

    # -------------------------------------------------------------------------
    # Recurrence Analysis (HIST-O3)
    # -------------------------------------------------------------------------

    async def analyze_recurrence(
        self,
        session: "AsyncSession",
        tenant_id: str,
        *,
        baseline_days: int = 30,
        recurrence_threshold: int = 3,
        limit: int = 20,
    ) -> RecurrenceAnalysisResult:
        """
        Analyze recurring incident types.

        Identifies incident categories that recur frequently.
        """
        # L5 engine import (migrated to HOC per SWEEP-05, PIN-468)
        from app.hoc.cus.incidents.L5_engines.recurrence_analysis_engine import RecurrenceAnalysisService

        service = RecurrenceAnalysisService(session)
        result = await service.analyze_recurrence(
            tenant_id=tenant_id,
            baseline_days=baseline_days,
            recurrence_threshold=recurrence_threshold,
            limit=limit,
        )

        # Map service result to facade result type
        return RecurrenceAnalysisResult(
            groups=[
                RecurrenceGroupResult(
                    category=g.category,
                    resolution_method=g.resolution_method,
                    total_occurrences=g.total_occurrences,
                    distinct_days=g.distinct_days,
                    occurrences_per_day=g.occurrences_per_day,
                    first_occurrence=g.first_occurrence,
                    last_occurrence=g.last_occurrence,
                    recent_incident_ids=g.recent_incident_ids,
                )
                for g in result.groups
            ],
            baseline_days=result.baseline_days,
            total_recurring=result.total_recurring,
            generated_at=result.generated_at,
        )

    # -------------------------------------------------------------------------
    # Post-Mortem Learnings (RES-O4)
    # -------------------------------------------------------------------------

    async def get_incident_learnings(
        self,
        session: "AsyncSession",
        tenant_id: str,
        incident_id: str,
    ) -> Optional[LearningsResult]:
        """
        Extract post-mortem learnings from an incident.

        Provides resolution summary, similar incidents, and actionable insights.
        """
        # L5 engine import (migrated to HOC per SWEEP-05)
        from app.hoc.cus.incidents.L5_engines.postmortem_engine import PostMortemService

        service = PostMortemService(session)
        result = await service.get_incident_learnings(
            tenant_id=tenant_id,
            incident_id=incident_id,
        )

        if not result:
            return None

        # Map service result to facade result type
        return LearningsResult(
            incident_id=result.incident_id,
            resolution_summary=ResolutionSummaryResult(
                incident_id=result.resolution_summary.incident_id,
                title=result.resolution_summary.title,
                category=result.resolution_summary.category,
                severity=result.resolution_summary.severity,
                resolution_method=result.resolution_summary.resolution_method,
                time_to_resolution_ms=result.resolution_summary.time_to_resolution_ms,
                evidence_count=result.resolution_summary.evidence_count,
                recovery_attempted=result.resolution_summary.recovery_attempted,
            ),
            similar_incidents=[
                ResolutionSummaryResult(
                    incident_id=s.incident_id,
                    title=s.title,
                    category=s.category,
                    severity=s.severity,
                    resolution_method=s.resolution_method,
                    time_to_resolution_ms=s.time_to_resolution_ms,
                    evidence_count=s.evidence_count,
                    recovery_attempted=s.recovery_attempted,
                )
                for s in result.similar_incidents
            ],
            insights=[
                LearningInsightResult(
                    insight_type=i.insight_type,
                    description=i.description,
                    confidence=i.confidence,
                    supporting_incident_ids=i.supporting_incident_ids,
                )
                for i in result.insights
            ],
            generated_at=result.generated_at,
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_facade_instance: IncidentsFacade | None = None


def get_incidents_facade() -> IncidentsFacade:
    """Get the singleton IncidentsFacade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = IncidentsFacade()
    return _facade_instance


__all__ = [
    # Facade
    "IncidentsFacade",
    "get_incidents_facade",
    # Result types - Summary
    "IncidentSummaryResult",
    "PaginationResult",
    "IncidentListResult",
    # Result types - Detail
    "IncidentDetailResult",
    "IncidentsByRunResult",
    # Result types - Pattern Detection
    "PatternMatchResult",
    "PatternDetectionResult",
    # Result types - Recurrence
    "RecurrenceGroupResult",
    "RecurrenceAnalysisResult",
    # Result types - Cost Impact
    "CostImpactSummaryResult",
    "CostImpactResult",
    # Result types - Metrics
    "IncidentMetricsResult",
    # Result types - Historical
    "HistoricalTrendDataPointResult",
    "HistoricalTrendResult",
    "HistoricalDistributionEntryResult",
    "HistoricalDistributionResult",
    "CostTrendDataPointResult",
    "CostTrendResult",
    # Result types - Learnings
    "LearningInsightResult",
    "ResolutionSummaryResult",
    "LearningsResult",
]
