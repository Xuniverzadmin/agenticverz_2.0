# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: ai-console
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
# Role: Database operations for incidents facade - pure data access
# Callers: incidents_facade.py (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Violation I.1

"""
Incidents Facade Driver (L6)

Pure database access layer for the incidents facade.
Returns snapshots (dicts/dataclasses), not ORM models.

Responsibilities:
- Execute queries against incidents table
- Return data snapshots
- NO business logic
- NO result type composition (that's L4's job)

This driver was extracted from incidents_facade.py per HOC Layer Topology V1.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.killswitch import Incident


# =============================================================================
# Snapshot Types (L6 returns these, not ORM models)
# =============================================================================


@dataclass
class IncidentSnapshot:
    """Raw incident data snapshot from database."""

    id: str
    tenant_id: str
    lifecycle_state: Optional[str]
    severity: Optional[str]
    category: Optional[str]
    title: Optional[str]
    description: Optional[str]
    llm_run_id: Optional[str]
    source_run_id: Optional[str]
    cause_type: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    affected_agent_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    is_synthetic: Optional[bool]
    synthetic_scenario_id: Optional[str]


@dataclass
class IncidentListSnapshot:
    """Paginated list of incident snapshots."""

    items: list[IncidentSnapshot]
    total: int


@dataclass
class MetricsSnapshot:
    """Raw metrics aggregates from database."""

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
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


@dataclass
class CostImpactRowSnapshot:
    """Single row from cost impact query."""

    category: str
    resolution_method: Optional[str]
    incident_count: int
    total_cost_impact: float
    avg_cost_impact: float


@dataclass
class HistoricalTrendRowSnapshot:
    """Single row from historical trend query."""

    period: str
    incident_count: int
    resolved_count: int
    avg_resolution_time_ms: Optional[int]


@dataclass
class HistoricalDistributionRowSnapshot:
    """Single row from distribution query."""

    dimension: str
    value: str
    count: int


@dataclass
class CostTrendRowSnapshot:
    """Single row from cost trend query."""

    period: str
    total_cost: float
    incident_count: int


# =============================================================================
# Incidents Facade Driver
# =============================================================================


class IncidentsFacadeDriver:
    """
    L6 Database driver for incidents facade.

    Pure data access - no business logic.
    Returns snapshots, not ORM models.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    # -------------------------------------------------------------------------
    # List Operations
    # -------------------------------------------------------------------------

    async def fetch_active_incidents(
        self,
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
    ) -> IncidentListSnapshot:
        """Fetch active incidents (ACTIVE + ACKED states)."""
        # Base query with tenant isolation + ACTIVE topic
        stmt = (
            select(Incident)
            .where(Incident.tenant_id == tenant_id)
            .where(Incident.lifecycle_state.in_(["ACTIVE", "ACKED"]))
        )

        count_stmt = (
            select(func.count(Incident.id))
            .where(Incident.tenant_id == tenant_id)
            .where(Incident.lifecycle_state.in_(["ACTIVE", "ACKED"]))
        )

        # Apply filters
        if severity:
            stmt = stmt.where(Incident.severity == severity)
            count_stmt = count_stmt.where(Incident.severity == severity)

        if category:
            stmt = stmt.where(Incident.category == category)
            count_stmt = count_stmt.where(Incident.category == category)

        if cause_type:
            stmt = stmt.where(Incident.cause_type == cause_type)
            count_stmt = count_stmt.where(Incident.cause_type == cause_type)

        if is_synthetic is not None:
            stmt = stmt.where(Incident.is_synthetic == is_synthetic)
            count_stmt = count_stmt.where(Incident.is_synthetic == is_synthetic)

        if created_after:
            stmt = stmt.where(Incident.created_at >= created_after)
            count_stmt = count_stmt.where(Incident.created_at >= created_after)

        if created_before:
            stmt = stmt.where(Incident.created_at <= created_before)
            count_stmt = count_stmt.where(Incident.created_at <= created_before)

        # Sorting
        sort_column = getattr(Incident, sort_by)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Pagination
        stmt = stmt.limit(limit).offset(offset)

        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        result = await self._session.execute(stmt)
        incidents = result.scalars().all()

        items = [self._to_snapshot(inc) for inc in incidents]

        return IncidentListSnapshot(items=items, total=total)

    async def fetch_resolved_incidents(
        self,
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
    ) -> IncidentListSnapshot:
        """Fetch resolved incidents."""
        stmt = (
            select(Incident)
            .where(Incident.tenant_id == tenant_id)
            .where(Incident.lifecycle_state == "RESOLVED")
        )

        count_stmt = (
            select(func.count(Incident.id))
            .where(Incident.tenant_id == tenant_id)
            .where(Incident.lifecycle_state == "RESOLVED")
        )

        # Apply filters
        if severity:
            stmt = stmt.where(Incident.severity == severity)
            count_stmt = count_stmt.where(Incident.severity == severity)

        if category:
            stmt = stmt.where(Incident.category == category)
            count_stmt = count_stmt.where(Incident.category == category)

        if cause_type:
            stmt = stmt.where(Incident.cause_type == cause_type)
            count_stmt = count_stmt.where(Incident.cause_type == cause_type)

        if is_synthetic is not None:
            stmt = stmt.where(Incident.is_synthetic == is_synthetic)
            count_stmt = count_stmt.where(Incident.is_synthetic == is_synthetic)

        if resolved_after:
            stmt = stmt.where(Incident.resolved_at >= resolved_after)
            count_stmt = count_stmt.where(Incident.resolved_at >= resolved_after)

        if resolved_before:
            stmt = stmt.where(Incident.resolved_at <= resolved_before)
            count_stmt = count_stmt.where(Incident.resolved_at <= resolved_before)

        # Sorting
        sort_column = getattr(Incident, sort_by)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        stmt = stmt.limit(limit).offset(offset)

        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        result = await self._session.execute(stmt)
        incidents = result.scalars().all()

        items = [self._to_snapshot(inc) for inc in incidents]

        return IncidentListSnapshot(items=items, total=total)

    async def fetch_historical_incidents(
        self,
        tenant_id: str,
        cutoff_date: datetime,
        *,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        cause_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "resolved_at",
        sort_order: str = "desc",
    ) -> IncidentListSnapshot:
        """Fetch historical incidents (resolved before cutoff date)."""
        stmt = (
            select(Incident)
            .where(Incident.tenant_id == tenant_id)
            .where(Incident.lifecycle_state == "RESOLVED")
            .where(Incident.resolved_at < cutoff_date)
        )

        count_stmt = (
            select(func.count(Incident.id))
            .where(Incident.tenant_id == tenant_id)
            .where(Incident.lifecycle_state == "RESOLVED")
            .where(Incident.resolved_at < cutoff_date)
        )

        if severity:
            stmt = stmt.where(Incident.severity == severity)
            count_stmt = count_stmt.where(Incident.severity == severity)

        if category:
            stmt = stmt.where(Incident.category == category)
            count_stmt = count_stmt.where(Incident.category == category)

        if cause_type:
            stmt = stmt.where(Incident.cause_type == cause_type)
            count_stmt = count_stmt.where(Incident.cause_type == cause_type)

        # Sorting
        sort_column = getattr(Incident, sort_by)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        stmt = stmt.limit(limit).offset(offset)

        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        result = await self._session.execute(stmt)
        incidents = result.scalars().all()

        items = [self._to_snapshot(inc) for inc in incidents]

        return IncidentListSnapshot(items=items, total=total)

    # -------------------------------------------------------------------------
    # Detail Operations
    # -------------------------------------------------------------------------

    async def fetch_incident_by_id(
        self,
        tenant_id: str,
        incident_id: str,
    ) -> Optional[IncidentSnapshot]:
        """Fetch single incident by ID with tenant isolation."""
        stmt = (
            select(Incident)
            .where(Incident.id == incident_id)
            .where(Incident.tenant_id == tenant_id)
        )

        result = await self._session.execute(stmt)
        incident = result.scalar_one_or_none()

        if not incident:
            return None

        return self._to_snapshot(incident)

    async def fetch_incidents_by_run(
        self,
        tenant_id: str,
        run_id: str,
    ) -> list[IncidentSnapshot]:
        """Fetch all incidents linked to a specific run."""
        stmt = (
            select(Incident)
            .where(Incident.tenant_id == tenant_id)
            .where(Incident.source_run_id == run_id)
            .order_by(Incident.created_at.desc())
        )

        result = await self._session.execute(stmt)
        incidents = result.scalars().all()

        return [self._to_snapshot(inc) for inc in incidents]

    # -------------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------------

    async def fetch_metrics_aggregates(
        self,
        tenant_id: str,
        window_days: int,
    ) -> Optional[MetricsSnapshot]:
        """Fetch aggregated metrics using raw SQL."""
        sql = text("""
            WITH incident_stats AS (
                SELECT
                    lifecycle_state,
                    severity,
                    NULL::bigint AS time_to_containment_ms,
                    CASE WHEN resolved_at IS NOT NULL
                         THEN EXTRACT(EPOCH FROM (resolved_at - created_at)) * 1000
                         ELSE NULL
                    END AS time_to_resolution_ms,
                    NULL::boolean AS sla_met
                FROM incidents
                WHERE tenant_id = :tenant_id
                  AND created_at >= NOW() - INTERVAL '1 day' * :window_days
            )
            SELECT
                COUNT(*) FILTER (WHERE lifecycle_state IN ('ACTIVE', 'ACKED')) AS active_count,
                COUNT(*) FILTER (WHERE lifecycle_state = 'ACKED') AS acked_count,
                COUNT(*) FILTER (WHERE lifecycle_state = 'RESOLVED') AS resolved_count,
                COUNT(*) AS total_count,
                NULL::bigint AS avg_time_to_containment_ms,
                NULL::bigint AS median_time_to_containment_ms,
                AVG(time_to_resolution_ms)::bigint AS avg_time_to_resolution_ms,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY time_to_resolution_ms)::bigint AS median_time_to_resolution_ms,
                0 AS sla_met_count,
                0 AS sla_breached_count,
                COUNT(*) FILTER (WHERE severity = 'critical') AS critical_count,
                COUNT(*) FILTER (WHERE severity = 'high') AS high_count,
                COUNT(*) FILTER (WHERE severity = 'medium') AS medium_count,
                COUNT(*) FILTER (WHERE severity = 'low') AS low_count
            FROM incident_stats
        """)

        result = await self._session.execute(sql, {
            "tenant_id": tenant_id,
            "window_days": window_days,
        })

        row = result.mappings().first()

        if not row:
            return None

        return MetricsSnapshot(
            active_count=row["active_count"] or 0,
            acked_count=row["acked_count"] or 0,
            resolved_count=row["resolved_count"] or 0,
            total_count=row["total_count"] or 0,
            avg_time_to_containment_ms=row["avg_time_to_containment_ms"],
            median_time_to_containment_ms=row["median_time_to_containment_ms"],
            avg_time_to_resolution_ms=row["avg_time_to_resolution_ms"],
            median_time_to_resolution_ms=row["median_time_to_resolution_ms"],
            sla_met_count=row["sla_met_count"] or 0,
            sla_breached_count=row["sla_breached_count"] or 0,
            critical_count=row["critical_count"] or 0,
            high_count=row["high_count"] or 0,
            medium_count=row["medium_count"] or 0,
            low_count=row["low_count"] or 0,
        )

    # -------------------------------------------------------------------------
    # Cost Impact
    # -------------------------------------------------------------------------

    async def fetch_cost_impact_data(
        self,
        tenant_id: str,
        baseline_days: int,
        limit: int,
    ) -> list[CostImpactRowSnapshot]:
        """Fetch cost impact aggregates using raw SQL."""
        sql = text("""
            SELECT
                COALESCE(category, 'uncategorized') AS category,
                resolution_method,
                COUNT(*) AS incident_count,
                SUM(cost_impact) AS total_cost_impact,
                AVG(cost_impact) AS avg_cost_impact
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND cost_impact IS NOT NULL
              AND created_at >= NOW() - INTERVAL '1 day' * :baseline_days
            GROUP BY category, resolution_method
            ORDER BY total_cost_impact DESC NULLS LAST
            LIMIT :limit
        """)

        result = await self._session.execute(sql, {
            "tenant_id": tenant_id,
            "baseline_days": baseline_days,
            "limit": limit,
        })

        rows: list[CostImpactRowSnapshot] = []
        for row in result.mappings():
            rows.append(CostImpactRowSnapshot(
                category=row["category"],
                resolution_method=row["resolution_method"],
                incident_count=row["incident_count"],
                total_cost_impact=float(row["total_cost_impact"]) if row["total_cost_impact"] else 0.0,
                avg_cost_impact=float(row["avg_cost_impact"]) if row["avg_cost_impact"] else 0.0,
            ))

        return rows

    # -------------------------------------------------------------------------
    # Deprecated List (all incidents with filters)
    # -------------------------------------------------------------------------

    async def fetch_all_incidents(
        self,
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
    ) -> IncidentListSnapshot:
        """Fetch incidents with full filter set (deprecated endpoint)."""
        stmt = select(Incident).where(Incident.tenant_id == tenant_id)
        count_stmt = select(func.count(Incident.id)).where(Incident.tenant_id == tenant_id)

        # Topic filter (maps to lifecycle states)
        if topic:
            if topic == "ACTIVE":
                stmt = stmt.where(Incident.lifecycle_state.in_(["ACTIVE", "ACKED"]))
                count_stmt = count_stmt.where(Incident.lifecycle_state.in_(["ACTIVE", "ACKED"]))
            else:
                stmt = stmt.where(Incident.lifecycle_state == "RESOLVED")
                count_stmt = count_stmt.where(Incident.lifecycle_state == "RESOLVED")
        elif lifecycle_state:
            stmt = stmt.where(Incident.lifecycle_state == lifecycle_state)
            count_stmt = count_stmt.where(Incident.lifecycle_state == lifecycle_state)

        if severity:
            stmt = stmt.where(Incident.severity == severity)
            count_stmt = count_stmt.where(Incident.severity == severity)

        if category:
            stmt = stmt.where(Incident.category == category)
            count_stmt = count_stmt.where(Incident.category == category)

        if cause_type:
            stmt = stmt.where(Incident.cause_type == cause_type)
            count_stmt = count_stmt.where(Incident.cause_type == cause_type)

        if is_synthetic is not None:
            stmt = stmt.where(Incident.is_synthetic == is_synthetic)
            count_stmt = count_stmt.where(Incident.is_synthetic == is_synthetic)

        if created_after:
            stmt = stmt.where(Incident.created_at >= created_after)
            count_stmt = count_stmt.where(Incident.created_at >= created_after)

        if created_before:
            stmt = stmt.where(Incident.created_at <= created_before)
            count_stmt = count_stmt.where(Incident.created_at <= created_before)

        # Sorting
        sort_column = getattr(Incident, sort_by)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Pagination
        stmt = stmt.limit(limit).offset(offset)

        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        result = await self._session.execute(stmt)
        incidents = result.scalars().all()

        items = [self._to_snapshot(inc) for inc in incidents]
        return IncidentListSnapshot(items=items, total=total)

    # -------------------------------------------------------------------------
    # Historical Analytics
    # -------------------------------------------------------------------------

    async def fetch_historical_trend(
        self,
        tenant_id: str,
        window_days: int,
        trunc_unit: str,
    ) -> list[HistoricalTrendRowSnapshot]:
        """Fetch historical trend data grouped by time period."""
        sql = text("""
            SELECT
                DATE_TRUNC(:trunc_unit, created_at) AS period,
                COUNT(*) AS incident_count,
                COUNT(*) FILTER (WHERE lifecycle_state = 'RESOLVED') AS resolved_count,
                AVG(
                    CASE WHEN resolved_at IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (resolved_at - created_at)) * 1000
                    ELSE NULL END
                )::bigint AS avg_resolution_time_ms
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - INTERVAL '1 day' * :window_days
            GROUP BY DATE_TRUNC(:trunc_unit, created_at)
            ORDER BY period ASC
        """)

        result = await self._session.execute(sql, {
            "tenant_id": tenant_id,
            "window_days": window_days,
            "trunc_unit": trunc_unit,
        })

        rows: list[HistoricalTrendRowSnapshot] = []
        for row in result.mappings():
            period_date = row["period"]
            period_str = period_date.strftime("%Y-%m-%d") if period_date else "unknown"
            rows.append(HistoricalTrendRowSnapshot(
                period=period_str,
                incident_count=row["incident_count"] or 0,
                resolved_count=row["resolved_count"] or 0,
                avg_resolution_time_ms=row["avg_resolution_time_ms"],
            ))

        return rows

    async def fetch_historical_distribution(
        self,
        tenant_id: str,
        window_days: int,
    ) -> dict[str, Any]:
        """Fetch distribution data across category, severity, cause_type."""
        # Total count
        total_sql = text("""
            SELECT COUNT(*) as total
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - INTERVAL '1 day' * :window_days
        """)

        total_result = await self._session.execute(total_sql, {
            "tenant_id": tenant_id,
            "window_days": window_days,
        })
        total_incidents = total_result.scalar() or 0

        # Category distribution
        category_sql = text("""
            SELECT COALESCE(category, 'uncategorized') as value, COUNT(*) as count
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - INTERVAL '1 day' * :window_days
            GROUP BY category
            ORDER BY count DESC
        """)
        category_result = await self._session.execute(category_sql, {
            "tenant_id": tenant_id,
            "window_days": window_days,
        })
        by_category = [
            HistoricalDistributionRowSnapshot(dimension="category", value=r["value"], count=r["count"] or 0)
            for r in category_result.mappings()
        ]

        # Severity distribution
        severity_sql = text("""
            SELECT COALESCE(severity, 'unknown') as value, COUNT(*) as count
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - INTERVAL '1 day' * :window_days
            GROUP BY severity
            ORDER BY count DESC
        """)
        severity_result = await self._session.execute(severity_sql, {
            "tenant_id": tenant_id,
            "window_days": window_days,
        })
        by_severity = [
            HistoricalDistributionRowSnapshot(dimension="severity", value=r["value"], count=r["count"] or 0)
            for r in severity_result.mappings()
        ]

        # Cause type distribution
        cause_sql = text("""
            SELECT COALESCE(cause_type, 'unknown') as value, COUNT(*) as count
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - INTERVAL '1 day' * :window_days
            GROUP BY cause_type
            ORDER BY count DESC
        """)
        cause_result = await self._session.execute(cause_sql, {
            "tenant_id": tenant_id,
            "window_days": window_days,
        })
        by_cause_type = [
            HistoricalDistributionRowSnapshot(dimension="cause_type", value=r["value"], count=r["count"] or 0)
            for r in cause_result.mappings()
        ]

        return {
            "total_incidents": total_incidents,
            "by_category": by_category,
            "by_severity": by_severity,
            "by_cause_type": by_cause_type,
        }

    async def fetch_historical_cost_trend(
        self,
        tenant_id: str,
        window_days: int,
        granularity: str,
    ) -> list[CostTrendRowSnapshot]:
        """Fetch cost trend data grouped by time period."""
        sql = text("""
            SELECT
                DATE_TRUNC(:granularity, created_at) AS period,
                COALESCE(SUM(cost_impact), 0) AS total_cost,
                COUNT(*) AS incident_count
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - INTERVAL '1 day' * :window_days
            GROUP BY DATE_TRUNC(:granularity, created_at)
            ORDER BY period ASC
        """)

        result = await self._session.execute(sql, {
            "tenant_id": tenant_id,
            "window_days": window_days,
            "granularity": granularity,
        })

        rows: list[CostTrendRowSnapshot] = []
        for row in result.mappings():
            period_date = row["period"]
            period_str = period_date.strftime("%Y-%m-%d") if period_date else "unknown"
            rows.append(CostTrendRowSnapshot(
                period=period_str,
                total_cost=float(row["total_cost"]) if row["total_cost"] else 0.0,
                incident_count=row["incident_count"] or 0,
            ))

        return rows

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _to_snapshot(self, inc: Incident) -> IncidentSnapshot:
        """Convert ORM model to snapshot. No business logic."""
        return IncidentSnapshot(
            id=inc.id,
            tenant_id=inc.tenant_id,
            lifecycle_state=inc.lifecycle_state,
            severity=inc.severity,
            category=inc.category,
            title=inc.title,
            description=inc.description,
            llm_run_id=inc.llm_run_id,
            source_run_id=inc.source_run_id,
            cause_type=inc.cause_type,
            error_code=inc.error_code,
            error_message=inc.error_message,
            affected_agent_id=inc.affected_agent_id,
            created_at=inc.created_at,
            updated_at=inc.updated_at,
            resolved_at=inc.resolved_at,
            is_synthetic=inc.is_synthetic,
            synthetic_scenario_id=inc.synthetic_scenario_id,
        )


__all__ = [
    "IncidentsFacadeDriver",
    "IncidentSnapshot",
    "IncidentListSnapshot",
    "MetricsSnapshot",
    "CostImpactRowSnapshot",
    "HistoricalTrendRowSnapshot",
    "HistoricalDistributionRowSnapshot",
    "CostTrendRowSnapshot",
]
