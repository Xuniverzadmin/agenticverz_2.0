# Layer: L6 — Platform Substrate
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Database operations for incidents facade - pure data access
# Callers: incidents_facade.py (L4)
# Allowed Imports: sqlalchemy, models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Violation I.1

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
]
