# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified INCIDENTS domain facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: INCIDENTS Domain - One Facade Architecture
# Reference: docs/architecture/incidents/INCIDENTS_DOMAIN_SQL.md
#
# GOVERNANCE NOTE:
# This is the ONE facade for INCIDENTS domain.
# All incident data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Unified Incidents API (L2)

Customer-facing endpoints for viewing incidents.
All requests are tenant-scoped via auth_context.

Endpoints:
- GET /api/v1/incidents                        → O2 list with filters
- GET /api/v1/incidents/{incident_id}          → O3 detail
- GET /api/v1/incidents/{incident_id}/evidence → O4 context (preflight)
- GET /api/v1/incidents/{incident_id}/proof    → O5 raw (preflight)
- GET /api/v1/incidents/{incident_id}/learnings → O4 post-mortem learnings
- GET /api/v1/incidents/by-run/{run_id}        → Incidents linked to run
- GET /api/v1/incidents/patterns               → ACT-O5 pattern detection
- GET /api/v1/incidents/recurring              → HIST-O3 recurrence analysis
- GET /api/v1/incidents/cost-impact            → RES-O3 cost impact analysis

Architecture:
- ONE facade for all INCIDENTS needs
- Tenant isolation via auth_context (not header)
- SDSR validates this same production API
"""

import logging
import os
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.models.killswitch import Incident
from app.schemas.response import wrap_dict
from app.services.incidents_facade import get_incidents_facade

# =============================================================================
# Module Configuration
# =============================================================================

logger = logging.getLogger(__name__)
_CURRENT_ENVIRONMENT = os.getenv("AOS_ENVIRONMENT", "preflight")


def require_preflight() -> None:
    """Guard for preflight-only endpoints (O4, O5)."""
    if _CURRENT_ENVIRONMENT != "preflight":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "preflight_only",
                "message": "This endpoint is only available in preflight console.",
            },
        )


# =============================================================================
# Enums
# =============================================================================


class LifecycleState(str, Enum):
    """Incident lifecycle state."""

    ACTIVE = "ACTIVE"
    ACKED = "ACKED"
    RESOLVED = "RESOLVED"


class Severity(str, Enum):
    """Incident severity."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CauseType(str, Enum):
    """Incident cause type."""

    LLM_RUN = "LLM_RUN"
    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"


class Topic(str, Enum):
    """UX topic for filtering."""

    ACTIVE = "ACTIVE"  # Includes ACTIVE + ACKED states
    RESOLVED = "RESOLVED"


class SortField(str, Enum):
    """Allowed sort fields."""

    CREATED_AT = "created_at"
    RESOLVED_AT = "resolved_at"
    SEVERITY = "severity"


class SortOrder(str, Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


# =============================================================================
# Response Models
# =============================================================================


class IncidentSummary(BaseModel):
    """Incident summary for list view (O2)."""

    incident_id: str
    tenant_id: str
    lifecycle_state: str
    severity: str
    category: str
    title: str
    description: Optional[str] = None
    llm_run_id: Optional[str] = None
    cause_type: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    is_synthetic: bool = False

    # Cross-domain navigation refs (PIN-447 - Policy V2 Facade)
    # These are navigational links, not operational data.
    # Incidents are narrators, not judges (INV-DOM-001).
    policy_ref: Optional[str] = None  # "/policy/active/{policy_id}"
    violation_ref: Optional[str] = None  # "/policy/violations/{violation_id}"

    class Config:
        from_attributes = True


class Pagination(BaseModel):
    """Pagination metadata."""

    limit: int
    offset: int
    next_offset: Optional[int] = None


class IncidentListResponse(BaseModel):
    """GET /incidents response."""

    items: List[IncidentSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]
    pagination: Pagination


class IncidentDetailResponse(BaseModel):
    """GET /incidents/{incident_id} response (O3)."""

    incident_id: str
    tenant_id: str
    lifecycle_state: str
    severity: str
    category: str
    title: str
    description: Optional[str] = None
    llm_run_id: Optional[str] = None
    source_run_id: Optional[str] = None
    cause_type: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    affected_agent_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    is_synthetic: bool = False
    synthetic_scenario_id: Optional[str] = None

    # Cross-domain navigation refs (PIN-447 - Policy V2 Facade)
    # These are navigational links for cross-domain traversal.
    # Incidents are narrators, not judges (INV-DOM-001).
    # Reference: docs/contracts/CROSS_DOMAIN_INVARIANTS.md
    policy_id: Optional[str] = None  # Policy that was violated
    policy_ref: Optional[str] = None  # "/policy/active/{policy_id}"
    violation_id: Optional[str] = None  # Violation record ID
    violation_ref: Optional[str] = None  # "/policy/violations/{violation_id}"
    lesson_ref: Optional[str] = None  # "/policy/lessons/{lesson_id}" (if lesson created)

    class Config:
        from_attributes = True


class IncidentsByRunResponse(BaseModel):
    """GET /incidents/by-run/{run_id} response."""

    run_id: str
    incidents: List[IncidentSummary]
    total: int


# =============================================================================
# Pattern Detection Response Models
# =============================================================================


class PatternMatchResponse(BaseModel):
    """A detected incident pattern."""

    pattern_type: str  # category_cluster, severity_spike, cascade_failure
    dimension: str  # category name, severity level, or source_run_id
    count: int
    incident_ids: List[str]
    confidence: float


class PatternDetectionResponse(BaseModel):
    """GET /incidents/patterns response (ACT-O5)."""

    patterns: List[PatternMatchResponse]
    window_hours: int
    window_start: datetime
    window_end: datetime
    incidents_analyzed: int


# =============================================================================
# Recurrence Analysis Response Models
# =============================================================================


class RecurrenceGroupResponse(BaseModel):
    """A group of recurring incidents."""

    category: str
    resolution_method: Optional[str] = None
    total_occurrences: int
    distinct_days: int
    occurrences_per_day: float
    first_occurrence: datetime
    last_occurrence: datetime
    recent_incident_ids: List[str]


class RecurrenceAnalysisResponse(BaseModel):
    """GET /incidents/recurring response (HIST-O3)."""

    groups: List[RecurrenceGroupResponse]
    baseline_days: int
    total_recurring: int
    generated_at: datetime


# =============================================================================
# Cost Impact Response Models
# =============================================================================


class CostImpactSummary(BaseModel):
    """Cost impact summary for an incident category."""

    category: str
    incident_count: int
    total_cost_impact: float
    avg_cost_impact: float
    resolution_method: Optional[str] = None


class CostImpactResponse(BaseModel):
    """GET /incidents/cost-impact response (RES-O3)."""

    summaries: List[CostImpactSummary]
    total_cost_impact: float
    baseline_days: int
    generated_at: datetime


# =============================================================================
# Topic-Scoped Response Models (Phase 1 Migration)
# =============================================================================


class IncidentMetricsResponse(BaseModel):
    """GET /incidents/metrics response - Dedicated metrics capability."""

    # Counts by state
    active_count: int
    acked_count: int
    resolved_count: int
    total_count: int

    # Containment metrics
    avg_time_to_containment_ms: Optional[int] = None
    median_time_to_containment_ms: Optional[int] = None

    # Resolution metrics
    avg_time_to_resolution_ms: Optional[int] = None
    median_time_to_resolution_ms: Optional[int] = None

    # SLA metrics
    sla_met_count: int = 0
    sla_breached_count: int = 0
    sla_compliance_rate: Optional[float] = None

    # Severity breakdown
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Time window
    window_days: int
    generated_at: datetime


class HistoricalTrendDataPoint(BaseModel):
    """A single data point in a historical trend."""

    period: str  # ISO date or date range
    incident_count: int
    resolved_count: int
    avg_resolution_time_ms: Optional[int] = None


class HistoricalTrendResponse(BaseModel):
    """GET /incidents/historical/trend response."""

    data_points: List[HistoricalTrendDataPoint]
    granularity: str  # day, week, month
    window_days: int
    total_incidents: int
    generated_at: datetime


class HistoricalDistributionEntry(BaseModel):
    """A single entry in the distribution."""

    dimension: str  # category, severity, cause_type
    value: str
    count: int
    percentage: float


class HistoricalDistributionResponse(BaseModel):
    """GET /incidents/historical/distribution response."""

    by_category: List[HistoricalDistributionEntry]
    by_severity: List[HistoricalDistributionEntry]
    by_cause_type: List[HistoricalDistributionEntry]
    window_days: int
    total_incidents: int
    generated_at: datetime


class CostTrendDataPoint(BaseModel):
    """A single data point in the cost trend."""

    period: str  # ISO date or date range
    total_cost: float
    incident_count: int
    avg_cost_per_incident: float


class CostTrendResponse(BaseModel):
    """GET /incidents/historical/cost-trend response."""

    data_points: List[CostTrendDataPoint]
    granularity: str  # day, week, month
    window_days: int
    total_cost: float
    total_incidents: int
    generated_at: datetime


# =============================================================================
# Learnings Response Models
# =============================================================================


class LearningInsightResponse(BaseModel):
    """A learning insight from incident analysis."""

    insight_type: str  # prevention, detection, response, communication
    description: str
    confidence: float
    supporting_incident_ids: List[str]


class ResolutionSummaryResponse(BaseModel):
    """Summary of incident resolution."""

    incident_id: str
    title: str
    category: Optional[str] = None
    severity: str
    resolution_method: Optional[str] = None
    time_to_resolution_ms: Optional[int] = None
    evidence_count: int
    recovery_attempted: bool


class LearningsResponse(BaseModel):
    """GET /incidents/{id}/learnings response (RES-O4)."""

    incident_id: str
    resolution_summary: ResolutionSummaryResponse
    similar_incidents: List[ResolutionSummaryResponse]
    insights: List[LearningInsightResponse]
    generated_at: datetime


# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["incidents"],
)


# =============================================================================
# Helper: Get tenant from auth context
# =============================================================================


def get_tenant_id_from_auth(request: Request) -> str:
    """Extract tenant_id from auth_context. Raises 401/403 if missing."""
    auth_context = get_auth_context(request)

    if auth_context is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "not_authenticated", "message": "Authentication required."},
        )

    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_required",
                "message": "This endpoint requires tenant context.",
            },
        )

    return tenant_id


# =============================================================================
# GET /incidents - DEPRECATED (Phase 5 Migration Lockdown)
# =============================================================================
# WARNING: This endpoint is DEPRECATED and should NOT be used by UI panels.
#
# Use topic-scoped endpoints instead:
#   - /api/v1/incidents/active     (ACTIVE topic)
#   - /api/v1/incidents/resolved   (RESOLVED topic)
#   - /api/v1/incidents/historical (HISTORICAL topic)
#
# Reference: INCIDENTS_DOMAIN_MIGRATION_PLAN.md Phase 5
# =============================================================================


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="[DEPRECATED] List incidents - Use topic-scoped endpoints",
    deprecated=True,
    description="""
    ⚠️ **DEPRECATED** - Do NOT use for UI panels.

    This endpoint is maintained for backward compatibility only.
    New code MUST use topic-scoped endpoints:

    - **ACTIVE incidents**: `/api/v1/incidents/active`
    - **RESOLVED incidents**: `/api/v1/incidents/resolved`
    - **HISTORICAL incidents**: `/api/v1/incidents/historical`

    Topic-scoped endpoints enforce semantics at the boundary,
    eliminating caller-controlled topic filtering.

    Reference: INCIDENTS_DOMAIN_MIGRATION_PLAN.md
    """,
)
async def list_incidents(
    request: Request,
    # Topic filter (maps to lifecycle states)
    topic: Annotated[Topic | None, Query(description="UX Topic: ACTIVE or RESOLVED")] = None,
    # Direct filters
    lifecycle_state: Annotated[LifecycleState | None, Query(description="Direct lifecycle state filter")] = None,
    severity: Annotated[Severity | None, Query(description="Filter by severity")] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    cause_type: Annotated[CauseType | None, Query(description="Filter by cause type")] = None,
    # SDSR filter
    is_synthetic: Annotated[bool | None, Query(description="Filter by synthetic data flag")] = None,
    # Time filters
    created_after: Annotated[datetime | None, Query(description="Filter incidents created after")] = None,
    created_before: Annotated[datetime | None, Query(description="Filter incidents created before")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max incidents to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of incidents to skip")] = 0,
    # Sorting
    sort_by: Annotated[SortField, Query(description="Field to sort by")] = SortField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.DESC,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> IncidentListResponse:
    """List incidents with unified query filters. Tenant-scoped."""

    # Phase 5 Runtime Warning: Log deprecation access
    # Reference: INCIDENTS_DOMAIN_MIGRATION_PLAN.md
    user_agent = request.headers.get("user-agent", "unknown")
    referer = request.headers.get("referer", "unknown")
    logger.warning(
        "DEPRECATED ENDPOINT ACCESS: /api/v1/incidents called directly. "
        "Migrate to topic-scoped endpoints (/incidents/active, /incidents/resolved). "
        "User-Agent: %s, Referer: %s",
        user_agent[:100] if user_agent else "unknown",
        referer[:100] if referer else "unknown",
    )

    tenant_id = get_tenant_id_from_auth(request)

    # Build filters
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    # Base query with tenant isolation
    stmt = select(Incident).where(Incident.tenant_id == tenant_id)

    # Topic filter (maps to lifecycle states)
    if topic:
        if topic == Topic.ACTIVE:
            stmt = stmt.where(Incident.lifecycle_state.in_(["ACTIVE", "ACKED"]))
            filters_applied["topic"] = "ACTIVE"
        else:
            stmt = stmt.where(Incident.lifecycle_state == "RESOLVED")
            filters_applied["topic"] = "RESOLVED"
    elif lifecycle_state:
        stmt = stmt.where(Incident.lifecycle_state == lifecycle_state.value)
        filters_applied["lifecycle_state"] = lifecycle_state.value

    if severity:
        stmt = stmt.where(Incident.severity == severity.value)
        filters_applied["severity"] = severity.value

    if category:
        stmt = stmt.where(Incident.category == category)
        filters_applied["category"] = category

    if cause_type:
        stmt = stmt.where(Incident.cause_type == cause_type.value)
        filters_applied["cause_type"] = cause_type.value

    if is_synthetic is not None:
        stmt = stmt.where(Incident.is_synthetic == is_synthetic)
        filters_applied["is_synthetic"] = is_synthetic

    if created_after:
        stmt = stmt.where(Incident.created_at >= created_after)
        filters_applied["created_after"] = created_after.isoformat()

    if created_before:
        stmt = stmt.where(Incident.created_at <= created_before)
        filters_applied["created_before"] = created_before.isoformat()

    # Count query (same filters, no pagination)
    count_stmt = select(func.count(Incident.id)).where(Incident.tenant_id == tenant_id)
    if topic:
        if topic == Topic.ACTIVE:
            count_stmt = count_stmt.where(Incident.lifecycle_state.in_(["ACTIVE", "ACKED"]))
        else:
            count_stmt = count_stmt.where(Incident.lifecycle_state == "RESOLVED")
    elif lifecycle_state:
        count_stmt = count_stmt.where(Incident.lifecycle_state == lifecycle_state.value)
    if severity:
        count_stmt = count_stmt.where(Incident.severity == severity.value)
    if category:
        count_stmt = count_stmt.where(Incident.category == category)
    if cause_type:
        count_stmt = count_stmt.where(Incident.cause_type == cause_type.value)
    if is_synthetic is not None:
        count_stmt = count_stmt.where(Incident.is_synthetic == is_synthetic)
    if created_after:
        count_stmt = count_stmt.where(Incident.created_at >= created_after)
    if created_before:
        count_stmt = count_stmt.where(Incident.created_at <= created_before)

    # Sorting
    sort_column = getattr(Incident, sort_by.value)
    if sort_order == SortOrder.DESC:
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    # Pagination
    stmt = stmt.limit(limit).offset(offset)

    try:
        # Execute count
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Execute data query
        result = await session.execute(stmt)
        incidents = result.scalars().all()

        items = [
            IncidentSummary(
                incident_id=inc.id,
                tenant_id=inc.tenant_id,
                lifecycle_state=inc.lifecycle_state or "ACTIVE",
                severity=inc.severity or "medium",
                category=inc.category or "UNKNOWN",
                title=inc.title or "Untitled Incident",
                description=inc.description,
                llm_run_id=inc.llm_run_id,
                cause_type=inc.cause_type or "SYSTEM",
                error_code=inc.error_code,
                error_message=inc.error_message,
                created_at=inc.created_at,
                resolved_at=inc.resolved_at,
                is_synthetic=inc.is_synthetic or False,
            )
            for inc in incidents
        ]

        has_more = offset + len(items) < total
        next_offset = offset + limit if has_more else None

        return IncidentListResponse(
            items=items,
            total=total,
            has_more=has_more,
            filters_applied=filters_applied,
            pagination=Pagination(limit=limit, offset=offset, next_offset=next_offset),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /incidents/by-run/{run_id} - Incidents for a Run
# =============================================================================


@router.get(
    "/by-run/{run_id}",
    response_model=IncidentsByRunResponse,
    summary="Get incidents for a run",
    description="Returns all incidents linked to a specific run.",
)
async def get_incidents_for_run(
    request: Request,
    run_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> IncidentsByRunResponse:
    """Get all incidents linked to a specific run. Tenant-scoped."""

    tenant_id = get_tenant_id_from_auth(request)

    stmt = (
        select(Incident)
        .where(Incident.tenant_id == tenant_id)
        .where(Incident.source_run_id == run_id)
        .order_by(Incident.created_at.desc())
    )

    result = await session.execute(stmt)
    incidents = result.scalars().all()

    items = [
        IncidentSummary(
            incident_id=inc.id,
            tenant_id=inc.tenant_id,
            lifecycle_state=inc.lifecycle_state or "ACTIVE",
            severity=inc.severity or "medium",
            category=inc.category or "UNKNOWN",
            title=inc.title or "Untitled Incident",
            description=inc.description,
            llm_run_id=inc.llm_run_id,
            cause_type=inc.cause_type or "SYSTEM",
            error_code=inc.error_code,
            error_message=inc.error_message,
            created_at=inc.created_at,
            resolved_at=inc.resolved_at,
            is_synthetic=inc.is_synthetic or False,
        )
        for inc in incidents
    ]

    return IncidentsByRunResponse(
        run_id=run_id,
        incidents=items,
        total=len(items),
    )


# =============================================================================
# GET /incidents/patterns - ACT-O5 Pattern Detection
# NOTE: Static routes MUST be defined BEFORE /{incident_id} routes
# =============================================================================


@router.get(
    "/patterns",
    response_model=PatternDetectionResponse,
    summary="Detect incident patterns (ACT-O5)",
    description="""
    Detects structural patterns across incidents:
    - category_cluster: Multiple incidents in same category
    - severity_spike: Multiple high/critical in short window
    - cascade_failure: Multiple incidents from same source run
    """,
)
async def detect_patterns(
    request: Request,
    window_hours: Annotated[int, Query(ge=1, le=168, description="Hours to look back (max 168 = 7 days)")] = 24,
    limit: Annotated[int, Query(ge=1, le=50, description="Max patterns per type")] = 10,
    session: AsyncSession = Depends(get_async_session_dep),
) -> PatternDetectionResponse:
    """Detect incident patterns. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)

    facade = get_incidents_facade()
    result = await facade.detect_patterns(
        session=session,
        tenant_id=tenant_id,
        window_hours=window_hours,
        limit=limit,
    )

    # Map facade result to L2 response model
    return PatternDetectionResponse(
        patterns=[
            PatternMatchResponse(
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


# =============================================================================
# GET /incidents/recurring - HIST-O3 Recurrence Analysis
# =============================================================================


@router.get(
    "/recurring",
    response_model=RecurrenceAnalysisResponse,
    summary="Analyze recurring incidents (HIST-O3)",
    description="""
    Identifies recurring incident types by analyzing:
    - Category clusters
    - Resolution method patterns
    - Occurrence frequency over time
    """,
)
async def analyze_recurrence(
    request: Request,
    baseline_days: Annotated[int, Query(ge=1, le=90, description="Days to analyze (max 90)")] = 30,
    recurrence_threshold: Annotated[int, Query(ge=2, le=100, description="Min occurrences to flag as recurring")] = 3,
    limit: Annotated[int, Query(ge=1, le=50, description="Max groups to return")] = 20,
    session: AsyncSession = Depends(get_async_session_dep),
) -> RecurrenceAnalysisResponse:
    """Analyze recurring incident patterns. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)

    facade = get_incidents_facade()
    result = await facade.analyze_recurrence(
        session=session,
        tenant_id=tenant_id,
        baseline_days=baseline_days,
        recurrence_threshold=recurrence_threshold,
        limit=limit,
    )

    # Map facade result to L2 response model
    return RecurrenceAnalysisResponse(
        groups=[
            RecurrenceGroupResponse(
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


# =============================================================================
# GET /incidents/cost-impact - RES-O3 Cost Impact Analysis
# =============================================================================


@router.get(
    "/cost-impact",
    response_model=CostImpactResponse,
    summary="Analyze cost impact (RES-O3)",
    description="""
    Aggregates cost impact data across incidents:
    - Total cost by category
    - Average cost per incident
    - Resolution method effectiveness
    """,
)
async def analyze_cost_impact(
    request: Request,
    baseline_days: Annotated[int, Query(ge=1, le=90, description="Days to analyze (max 90)")] = 30,
    limit: Annotated[int, Query(ge=1, le=50, description="Max categories to return")] = 20,
    session: AsyncSession = Depends(get_async_session_dep),
) -> CostImpactResponse:
    """Analyze cost impact across incidents. Tenant-scoped."""
    from datetime import timezone

    from sqlalchemy import text

    tenant_id = get_tenant_id_from_auth(request)
    baseline_days = min(baseline_days, 90)

    # Query cost impact by category
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

    result = await session.execute(sql, {
        "tenant_id": tenant_id,
        "baseline_days": baseline_days,
        "limit": limit,
    })

    summaries: List[CostImpactSummary] = []
    total_cost = 0.0

    for row in result.mappings():
        cost = float(row["total_cost_impact"]) if row["total_cost_impact"] else 0.0
        total_cost += cost
        summaries.append(CostImpactSummary(
            category=row["category"],
            incident_count=row["incident_count"],
            total_cost_impact=cost,
            avg_cost_impact=float(row["avg_cost_impact"]) if row["avg_cost_impact"] else 0.0,
            resolution_method=row["resolution_method"],
        ))

    return CostImpactResponse(
        summaries=summaries,
        total_cost_impact=total_cost,
        baseline_days=baseline_days,
        generated_at=datetime.now(timezone.utc),
    )


# =============================================================================
# PHASE 1 MIGRATION: Topic-Scoped Endpoints
# =============================================================================
# These endpoints enforce topic semantics at the boundary level.
# No topic= or state= query params - the endpoint IS the topic.
# Reference: INCIDENTS_DOMAIN_MIGRATION_PLAN.md
# =============================================================================


# =============================================================================
# GET /incidents/active - Topic: ACTIVE (ACTIVE + ACKED states)
# =============================================================================


@router.get(
    "/active",
    response_model=IncidentListResponse,
    summary="List active incidents (Topic-Scoped)",
    description="""
    Returns paginated list of ACTIVE incidents.
    Topic is hardcoded - includes ACTIVE + ACKED lifecycle states.
    No topic= or state= query params accepted.
    """,
)
async def list_active_incidents(
    request: Request,
    # Filters (no topic/state params - topic is enforced by endpoint)
    severity: Annotated[Severity | None, Query(description="Filter by severity")] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    cause_type: Annotated[CauseType | None, Query(description="Filter by cause type")] = None,
    is_synthetic: Annotated[bool | None, Query(description="Filter by synthetic data flag")] = None,
    # Time filters
    created_after: Annotated[datetime | None, Query(description="Filter incidents created after")] = None,
    created_before: Annotated[datetime | None, Query(description="Filter incidents created before")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max incidents to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of incidents to skip")] = 0,
    # Sorting
    sort_by: Annotated[SortField, Query(description="Field to sort by")] = SortField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.DESC,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> IncidentListResponse:
    """List ACTIVE incidents. Topic enforced at endpoint boundary."""
    tenant_id = get_tenant_id_from_auth(request)
    facade = get_incidents_facade()

    try:
        result = await facade.list_active_incidents(
            session=session,
            tenant_id=tenant_id,
            severity=severity.value if severity else None,
            category=category,
            cause_type=cause_type.value if cause_type else None,
            is_synthetic=is_synthetic,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
        )

        # Convert facade result to API response
        items = [
            IncidentSummary(
                incident_id=item.incident_id,
                tenant_id=item.tenant_id,
                lifecycle_state=item.lifecycle_state,
                severity=item.severity,
                category=item.category,
                title=item.title,
                description=item.description,
                llm_run_id=item.llm_run_id,
                cause_type=item.cause_type,
                error_code=item.error_code,
                error_message=item.error_message,
                created_at=item.created_at,
                resolved_at=item.resolved_at,
                is_synthetic=item.is_synthetic,
                policy_ref=item.policy_ref,
                violation_ref=item.violation_ref,
            )
            for item in result.items
        ]

        return IncidentListResponse(
            items=items,
            total=result.total,
            has_more=result.has_more,
            filters_applied=result.filters_applied,
            pagination=Pagination(
                limit=result.pagination.limit,
                offset=result.pagination.offset,
                next_offset=result.pagination.next_offset,
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /incidents/resolved - Topic: RESOLVED
# =============================================================================


@router.get(
    "/resolved",
    response_model=IncidentListResponse,
    summary="List resolved incidents (Topic-Scoped)",
    description="""
    Returns paginated list of RESOLVED incidents.
    Topic is hardcoded - only RESOLVED lifecycle state.
    No topic= or state= query params accepted.
    """,
)
async def list_resolved_incidents(
    request: Request,
    # Filters (no topic/state params - topic is enforced by endpoint)
    severity: Annotated[Severity | None, Query(description="Filter by severity")] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    cause_type: Annotated[CauseType | None, Query(description="Filter by cause type")] = None,
    is_synthetic: Annotated[bool | None, Query(description="Filter by synthetic data flag")] = None,
    # Time filters
    resolved_after: Annotated[datetime | None, Query(description="Filter incidents resolved after")] = None,
    resolved_before: Annotated[datetime | None, Query(description="Filter incidents resolved before")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max incidents to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of incidents to skip")] = 0,
    # Sorting
    sort_by: Annotated[SortField, Query(description="Field to sort by")] = SortField.RESOLVED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.DESC,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> IncidentListResponse:
    """List RESOLVED incidents. Topic enforced at endpoint boundary."""
    tenant_id = get_tenant_id_from_auth(request)
    facade = get_incidents_facade()

    try:
        result = await facade.list_resolved_incidents(
            session=session,
            tenant_id=tenant_id,
            severity=severity.value if severity else None,
            category=category,
            cause_type=cause_type.value if cause_type else None,
            is_synthetic=is_synthetic,
            resolved_after=resolved_after,
            resolved_before=resolved_before,
            limit=limit,
            offset=offset,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
        )

        # Convert facade result to API response
        items = [
            IncidentSummary(
                incident_id=item.incident_id,
                tenant_id=item.tenant_id,
                lifecycle_state=item.lifecycle_state,
                severity=item.severity,
                category=item.category,
                title=item.title,
                description=item.description,
                llm_run_id=item.llm_run_id,
                cause_type=item.cause_type,
                error_code=item.error_code,
                error_message=item.error_message,
                created_at=item.created_at,
                resolved_at=item.resolved_at,
                is_synthetic=item.is_synthetic,
                policy_ref=item.policy_ref,
                violation_ref=item.violation_ref,
            )
            for item in result.items
        ]

        return IncidentListResponse(
            items=items,
            total=result.total,
            has_more=result.has_more,
            filters_applied=result.filters_applied,
            pagination=Pagination(
                limit=result.pagination.limit,
                offset=result.pagination.offset,
                next_offset=result.pagination.next_offset,
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /incidents/historical - Topic: HISTORICAL (resolved beyond retention)
# =============================================================================


@router.get(
    "/historical",
    response_model=IncidentListResponse,
    summary="List historical incidents (Topic-Scoped)",
    description="""
    Returns paginated list of HISTORICAL incidents.
    Historical = RESOLVED incidents beyond retention window (default 30 days).
    Topic is hardcoded - endpoint IS the topic.
    """,
)
async def list_historical_incidents(
    request: Request,
    # Historical window config
    retention_days: Annotated[int, Query(ge=7, le=365, description="Retention window in days")] = 30,
    # Filters
    severity: Annotated[Severity | None, Query(description="Filter by severity")] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    cause_type: Annotated[CauseType | None, Query(description="Filter by cause type")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max incidents to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of incidents to skip")] = 0,
    # Sorting
    sort_by: Annotated[SortField, Query(description="Field to sort by")] = SortField.RESOLVED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.DESC,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> IncidentListResponse:
    """List HISTORICAL incidents (resolved beyond retention). Topic enforced."""
    tenant_id = get_tenant_id_from_auth(request)
    facade = get_incidents_facade()

    try:
        result = await facade.list_historical_incidents(
            session=session,
            tenant_id=tenant_id,
            retention_days=retention_days,
            severity=severity.value if severity else None,
            category=category,
            cause_type=cause_type.value if cause_type else None,
            limit=limit,
            offset=offset,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
        )

        # Convert facade result to API response
        items = [
            IncidentSummary(
                incident_id=item.incident_id,
                tenant_id=item.tenant_id,
                lifecycle_state=item.lifecycle_state,
                severity=item.severity,
                category=item.category,
                title=item.title,
                description=item.description,
                llm_run_id=item.llm_run_id,
                cause_type=item.cause_type,
                error_code=item.error_code,
                error_message=item.error_message,
                created_at=item.created_at,
                resolved_at=item.resolved_at,
                is_synthetic=item.is_synthetic,
                policy_ref=item.policy_ref,
                violation_ref=item.violation_ref,
            )
            for item in result.items
        ]

        return IncidentListResponse(
            items=items,
            total=result.total,
            has_more=result.has_more,
            filters_applied=result.filters_applied,
            pagination=Pagination(
                limit=result.pagination.limit,
                offset=result.pagination.offset,
                next_offset=result.pagination.next_offset,
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /incidents/metrics - Dedicated Metrics Capability
# =============================================================================


@router.get(
    "/metrics",
    response_model=IncidentMetricsResponse,
    summary="Get incident metrics (Dedicated Capability)",
    description="""
    Returns aggregated incident metrics for ACT-O3, RES-O3 panels.
    Dedicated metrics capability - not derived from cost-impact.
    Includes: counts, containment time, resolution time, SLA compliance.
    """,
)
async def get_incident_metrics(
    request: Request,
    window_days: Annotated[int, Query(ge=1, le=90, description="Window in days")] = 30,
    session: AsyncSession = Depends(get_async_session_dep),
) -> IncidentMetricsResponse:
    """Get incident metrics. Backend-computed, deterministic."""
    from datetime import timezone
    from sqlalchemy import text

    tenant_id = get_tenant_id_from_auth(request)

    # Single comprehensive query for all metrics
    # NOTE: contained_at and sla_target_seconds columns don't exist yet.
    # Using resolved_at - created_at for resolution time. Containment and SLA
    # will be added when those columns are created (Phase 1 is additive only).
    sql = text("""
        WITH incident_stats AS (
            SELECT
                lifecycle_state,
                severity,
                -- Containment time: will be NULL until contained_at column is added
                NULL::bigint AS time_to_containment_ms,
                -- Resolution time: resolved_at - created_at
                CASE WHEN resolved_at IS NOT NULL
                     THEN EXTRACT(EPOCH FROM (resolved_at - created_at)) * 1000
                     ELSE NULL
                END AS time_to_resolution_ms,
                -- SLA: NULL until sla_target_seconds column is added
                NULL::boolean AS sla_met
            FROM incidents
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - INTERVAL '1 day' * :window_days
        )
        SELECT
            -- Counts by state
            COUNT(*) FILTER (WHERE lifecycle_state IN ('ACTIVE', 'ACKED')) AS active_count,
            COUNT(*) FILTER (WHERE lifecycle_state = 'ACKED') AS acked_count,
            COUNT(*) FILTER (WHERE lifecycle_state = 'RESOLVED') AS resolved_count,
            COUNT(*) AS total_count,

            -- Containment metrics (NULL until contained_at column exists)
            NULL::bigint AS avg_time_to_containment_ms,
            NULL::bigint AS median_time_to_containment_ms,

            -- Resolution metrics
            AVG(time_to_resolution_ms)::bigint AS avg_time_to_resolution_ms,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY time_to_resolution_ms)::bigint AS median_time_to_resolution_ms,

            -- SLA metrics (NULL until sla_target_seconds column exists)
            0 AS sla_met_count,
            0 AS sla_breached_count,

            -- Severity breakdown
            COUNT(*) FILTER (WHERE severity = 'critical') AS critical_count,
            COUNT(*) FILTER (WHERE severity = 'high') AS high_count,
            COUNT(*) FILTER (WHERE severity = 'medium') AS medium_count,
            COUNT(*) FILTER (WHERE severity = 'low') AS low_count

        FROM incident_stats
    """)

    result = await session.execute(sql, {
        "tenant_id": tenant_id,
        "window_days": window_days,
    })

    row = result.mappings().first()

    if not row:
        # No incidents - return zeros
        return IncidentMetricsResponse(
            active_count=0,
            acked_count=0,
            resolved_count=0,
            total_count=0,
            window_days=window_days,
            generated_at=datetime.now(timezone.utc),
        )

    # Calculate SLA compliance rate
    sla_total = (row["sla_met_count"] or 0) + (row["sla_breached_count"] or 0)
    sla_compliance_rate = None
    if sla_total > 0:
        sla_compliance_rate = round((row["sla_met_count"] or 0) / sla_total * 100, 2)

    return IncidentMetricsResponse(
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
        sla_compliance_rate=sla_compliance_rate,
        critical_count=row["critical_count"] or 0,
        high_count=row["high_count"] or 0,
        medium_count=row["medium_count"] or 0,
        low_count=row["low_count"] or 0,
        window_days=window_days,
        generated_at=datetime.now(timezone.utc),
    )


# =============================================================================
# GET /incidents/historical/trend - Backend-Computed Trend Analytics
# =============================================================================


@router.get(
    "/historical/trend",
    response_model=HistoricalTrendResponse,
    summary="Get historical incident trend (Backend Analytics)",
    description="""
    Returns time-series trend data for historical incidents.
    Backend-computed - frontend does NOT aggregate this.
    Granularity: day, week, or month.
    """,
)
async def get_historical_trend(
    request: Request,
    window_days: Annotated[int, Query(ge=7, le=365, description="Window in days")] = 90,
    granularity: Annotated[str, Query(description="Aggregation granularity")] = "week",
    session: AsyncSession = Depends(get_async_session_dep),
) -> HistoricalTrendResponse:
    """Get historical trend. Backend-computed, deterministic."""
    from datetime import timezone
    from sqlalchemy import text

    tenant_id = get_tenant_id_from_auth(request)

    # Validate granularity
    if granularity not in ("day", "week", "month"):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_granularity", "message": "Must be: day, week, month"},
        )

    # Use date_trunc for grouping
    trunc_unit = granularity
    if granularity == "day":
        trunc_unit = "day"
    elif granularity == "week":
        trunc_unit = "week"
    elif granularity == "month":
        trunc_unit = "month"

    sql = text(f"""
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

    result = await session.execute(sql, {
        "tenant_id": tenant_id,
        "window_days": window_days,
        "trunc_unit": trunc_unit,
    })

    data_points: List[HistoricalTrendDataPoint] = []
    total_incidents = 0

    for row in result.mappings():
        period_date = row["period"]
        period_str = period_date.strftime("%Y-%m-%d") if period_date else "unknown"
        count = row["incident_count"] or 0
        total_incidents += count

        data_points.append(HistoricalTrendDataPoint(
            period=period_str,
            incident_count=count,
            resolved_count=row["resolved_count"] or 0,
            avg_resolution_time_ms=row["avg_resolution_time_ms"],
        ))

    return HistoricalTrendResponse(
        data_points=data_points,
        granularity=granularity,
        window_days=window_days,
        total_incidents=total_incidents,
        generated_at=datetime.now(timezone.utc),
    )


# =============================================================================
# GET /incidents/historical/distribution - Backend-Computed Distribution
# =============================================================================


@router.get(
    "/historical/distribution",
    response_model=HistoricalDistributionResponse,
    summary="Get historical incident distribution (Backend Analytics)",
    description="""
    Returns distribution breakdown for historical incidents.
    Backend-computed - frontend does NOT aggregate this.
    Dimensions: category, severity, cause_type.
    """,
)
async def get_historical_distribution(
    request: Request,
    window_days: Annotated[int, Query(ge=7, le=365, description="Window in days")] = 90,
    session: AsyncSession = Depends(get_async_session_dep),
) -> HistoricalDistributionResponse:
    """Get historical distribution. Backend-computed, deterministic."""
    from datetime import timezone
    from sqlalchemy import text

    tenant_id = get_tenant_id_from_auth(request)

    # Total count for percentage calculation
    total_sql = text("""
        SELECT COUNT(*) as total
        FROM incidents
        WHERE tenant_id = :tenant_id
          AND created_at >= NOW() - INTERVAL '1 day' * :window_days
    """)

    total_result = await session.execute(total_sql, {
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

    category_result = await session.execute(category_sql, {
        "tenant_id": tenant_id,
        "window_days": window_days,
    })

    by_category: List[HistoricalDistributionEntry] = []
    for row in category_result.mappings():
        count = row["count"] or 0
        pct = round(count / total_incidents * 100, 2) if total_incidents > 0 else 0
        by_category.append(HistoricalDistributionEntry(
            dimension="category",
            value=row["value"],
            count=count,
            percentage=pct,
        ))

    # Severity distribution
    severity_sql = text("""
        SELECT COALESCE(severity, 'unknown') as value, COUNT(*) as count
        FROM incidents
        WHERE tenant_id = :tenant_id
          AND created_at >= NOW() - INTERVAL '1 day' * :window_days
        GROUP BY severity
        ORDER BY count DESC
    """)

    severity_result = await session.execute(severity_sql, {
        "tenant_id": tenant_id,
        "window_days": window_days,
    })

    by_severity: List[HistoricalDistributionEntry] = []
    for row in severity_result.mappings():
        count = row["count"] or 0
        pct = round(count / total_incidents * 100, 2) if total_incidents > 0 else 0
        by_severity.append(HistoricalDistributionEntry(
            dimension="severity",
            value=row["value"],
            count=count,
            percentage=pct,
        ))

    # Cause type distribution
    cause_sql = text("""
        SELECT COALESCE(cause_type, 'unknown') as value, COUNT(*) as count
        FROM incidents
        WHERE tenant_id = :tenant_id
          AND created_at >= NOW() - INTERVAL '1 day' * :window_days
        GROUP BY cause_type
        ORDER BY count DESC
    """)

    cause_result = await session.execute(cause_sql, {
        "tenant_id": tenant_id,
        "window_days": window_days,
    })

    by_cause_type: List[HistoricalDistributionEntry] = []
    for row in cause_result.mappings():
        count = row["count"] or 0
        pct = round(count / total_incidents * 100, 2) if total_incidents > 0 else 0
        by_cause_type.append(HistoricalDistributionEntry(
            dimension="cause_type",
            value=row["value"],
            count=count,
            percentage=pct,
        ))

    return HistoricalDistributionResponse(
        by_category=by_category,
        by_severity=by_severity,
        by_cause_type=by_cause_type,
        window_days=window_days,
        total_incidents=total_incidents,
        generated_at=datetime.now(timezone.utc),
    )


# =============================================================================
# GET /incidents/historical/cost-trend - Backend-Computed Cost Trend
# =============================================================================


@router.get(
    "/historical/cost-trend",
    response_model=CostTrendResponse,
    summary="Get historical cost trend (Backend Analytics)",
    description="""
    Returns time-series cost trend for historical incidents.
    Backend-computed - frontend does NOT aggregate this.
    """,
)
async def get_historical_cost_trend(
    request: Request,
    window_days: Annotated[int, Query(ge=7, le=365, description="Window in days")] = 90,
    granularity: Annotated[str, Query(description="Aggregation granularity")] = "week",
    session: AsyncSession = Depends(get_async_session_dep),
) -> CostTrendResponse:
    """Get historical cost trend. Backend-computed, deterministic."""
    from datetime import timezone
    from sqlalchemy import text

    tenant_id = get_tenant_id_from_auth(request)

    if granularity not in ("day", "week", "month"):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_granularity", "message": "Must be: day, week, month"},
        )

    sql = text(f"""
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

    result = await session.execute(sql, {
        "tenant_id": tenant_id,
        "window_days": window_days,
        "granularity": granularity,
    })

    data_points: List[CostTrendDataPoint] = []
    total_cost = 0.0
    total_incidents = 0

    for row in result.mappings():
        period_date = row["period"]
        period_str = period_date.strftime("%Y-%m-%d") if period_date else "unknown"
        cost = float(row["total_cost"]) if row["total_cost"] else 0.0
        count = row["incident_count"] or 0

        total_cost += cost
        total_incidents += count

        avg_cost = cost / count if count > 0 else 0.0

        data_points.append(CostTrendDataPoint(
            period=period_str,
            total_cost=round(cost, 2),
            incident_count=count,
            avg_cost_per_incident=round(avg_cost, 2),
        ))

    return CostTrendResponse(
        data_points=data_points,
        granularity=granularity,
        window_days=window_days,
        total_cost=round(total_cost, 2),
        total_incidents=total_incidents,
        generated_at=datetime.now(timezone.utc),
    )


# =============================================================================
# GET /incidents/{incident_id} - O3 Detail
# =============================================================================


@router.get(
    "/{incident_id}",
    response_model=IncidentDetailResponse,
    summary="Get incident detail (O3)",
    description="Returns detailed information about a specific incident.",
)
async def get_incident_detail(
    request: Request,
    incident_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> IncidentDetailResponse:
    """Get incident detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    stmt = select(Incident).where(Incident.id == incident_id).where(Incident.tenant_id == tenant_id)

    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return IncidentDetailResponse(
        incident_id=incident.id,
        tenant_id=incident.tenant_id,
        lifecycle_state=incident.lifecycle_state or "ACTIVE",
        severity=incident.severity or "medium",
        category=incident.category or "UNKNOWN",
        title=incident.title or "Untitled Incident",
        description=incident.description,
        llm_run_id=incident.llm_run_id,
        source_run_id=incident.source_run_id,
        cause_type=incident.cause_type or "SYSTEM",
        error_code=incident.error_code,
        error_message=incident.error_message,
        affected_agent_id=incident.affected_agent_id,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        resolved_at=incident.resolved_at,
        is_synthetic=incident.is_synthetic or False,
        synthetic_scenario_id=incident.synthetic_scenario_id,
    )


# =============================================================================
# GET /incidents/{incident_id}/evidence - O4 Context (Preflight Only)
# =============================================================================


@router.get(
    "/{incident_id}/evidence",
    summary="Get incident evidence (O4)",
    description="Returns cross-domain impact and evidence context. Preflight only.",
)
async def get_incident_evidence(
    request: Request,
    incident_id: str,
) -> dict[str, Any]:
    """Get incident evidence (O4). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth

    return wrap_dict({
        "incident_id": incident_id,
        "source_run": None,
        "policies_triggered": [],
        "related_incidents": [],
        "recovery_suggestions": [],
    })


# =============================================================================
# GET /incidents/{incident_id}/proof - O5 Raw (Preflight Only)
# =============================================================================


@router.get(
    "/{incident_id}/proof",
    summary="Get incident proof (O5)",
    description="Returns raw traces, logs, and integrity proof. Preflight only.",
)
async def get_incident_proof(
    request: Request,
    incident_id: str,
) -> dict[str, Any]:
    """Get incident proof (O5). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth

    return wrap_dict({
        "incident_id": incident_id,
        "integrity": {
            "verification_status": "UNKNOWN",
        },
        "aos_traces": [],
        "raw_logs": [],
        "timeline": [],
    })


# =============================================================================
# GET /incidents/{incident_id}/learnings - RES-O4 Post-Mortem Learnings
# =============================================================================


@router.get(
    "/{incident_id}/learnings",
    response_model=LearningsResponse,
    summary="Get incident learnings (RES-O4)",
    description="""
    Extracts post-mortem learnings from an incident:
    - Resolution summary
    - Similar past incidents
    - Actionable insights (prevention, detection, response)
    """,
)
async def get_incident_learnings(
    request: Request,
    incident_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LearningsResponse:
    """Get post-mortem learnings for an incident. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)

    facade = get_incidents_facade()
    result = await facade.get_incident_learnings(
        session=session,
        tenant_id=tenant_id,
        incident_id=incident_id,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Incident {incident_id} not found"},
        )

    # Map facade result to L2 response model
    return LearningsResponse(
        incident_id=result.incident_id,
        resolution_summary=ResolutionSummaryResponse(
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
            ResolutionSummaryResponse(
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
            LearningInsightResponse(
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
# Export Endpoints (BACKEND_REMEDIATION_PLAN GAP-004, GAP-005, GAP-008)
# =============================================================================


class ExportFormat(str, Enum):
    """Export format options."""

    JSON = "json"
    PDF = "pdf"


class ExportRequest(BaseModel):
    """Request for export with optional parameters."""

    format: ExportFormat = ExportFormat.JSON
    export_reason: Optional[str] = None
    prepared_for: Optional[str] = None  # For executive debrief


@router.post(
    "/{incident_id}/export/evidence",
    summary="Export evidence bundle",
    description="""
    Export incident evidence bundle.

    Formats:
    - json: Structured EvidenceBundle as JSON
    - pdf: Formatted PDF with trace timeline

    Reference: BACKEND_REMEDIATION_PLAN.md GAP-008
    """,
)
async def export_evidence(
    request: Request,
    incident_id: str,
    export_request: ExportRequest,
) -> Any:
    """Export incident evidence bundle."""
    from fastapi.responses import Response

    from app.services.export_bundle_service import get_export_bundle_service
    from app.services.pdf_renderer import get_pdf_renderer

    tenant_id = get_tenant_id_from_auth(request)
    auth_ctx = get_auth_context(request)
    exported_by = getattr(auth_ctx, "user_id", "system") if auth_ctx else "system"

    service = get_export_bundle_service()

    try:
        bundle = await service.create_evidence_bundle(
            incident_id=incident_id,
            exported_by=exported_by,
            export_reason=export_request.export_reason,
        )

        # Verify tenant access
        if bundle.tenant_id != tenant_id:
            raise HTTPException(
                status_code=403,
                detail={"error": "forbidden", "message": "Access denied to this incident"},
            )

        if export_request.format == ExportFormat.PDF:
            renderer = get_pdf_renderer()
            pdf_bytes = renderer.render_evidence_pdf(bundle)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="evidence_{incident_id}.pdf"'
                },
            )

        return wrap_dict(bundle.model_dump(mode="json"))

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": str(e)},
        )


@router.post(
    "/{incident_id}/export/soc2",
    summary="Export SOC2 compliance bundle",
    description="""
    Export SOC2-compliant evidence bundle with control mappings.

    Always returns PDF format with:
    - Trust Service Criteria mappings (CC7.2, CC7.3, CC7.4)
    - Attestation statement
    - Full evidence trace

    Reference: BACKEND_REMEDIATION_PLAN.md GAP-004
    """,
)
async def export_soc2(
    request: Request,
    incident_id: str,
    export_request: ExportRequest,
) -> Any:
    """Export SOC2-compliant bundle as PDF."""
    from fastapi.responses import Response

    from app.services.export_bundle_service import get_export_bundle_service
    from app.services.pdf_renderer import get_pdf_renderer

    tenant_id = get_tenant_id_from_auth(request)
    auth_ctx = get_auth_context(request)
    exported_by = getattr(auth_ctx, "user_id", "system") if auth_ctx else "system"

    service = get_export_bundle_service()

    try:
        bundle = await service.create_soc2_bundle(
            incident_id=incident_id,
            exported_by=exported_by,
        )

        # Verify tenant access
        if bundle.tenant_id != tenant_id:
            raise HTTPException(
                status_code=403,
                detail={"error": "forbidden", "message": "Access denied to this incident"},
            )

        if export_request.format == ExportFormat.PDF:
            renderer = get_pdf_renderer()
            pdf_bytes = renderer.render_soc2_pdf(bundle)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="soc2_{incident_id}.pdf"'
                },
            )

        return wrap_dict(bundle.model_dump(mode="json"))

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": str(e)},
        )


@router.post(
    "/{incident_id}/export/executive-debrief",
    summary="Export executive debrief",
    description="""
    Export non-technical executive summary.

    Always returns PDF format with:
    - Incident summary (plain English)
    - Business impact assessment
    - Recommended actions
    - Key metrics

    Reference: BACKEND_REMEDIATION_PLAN.md GAP-005
    """,
)
async def export_executive_debrief(
    request: Request,
    incident_id: str,
    export_request: ExportRequest,
) -> Any:
    """Export executive debrief as PDF."""
    from fastapi.responses import Response

    from app.services.export_bundle_service import get_export_bundle_service
    from app.services.pdf_renderer import get_pdf_renderer

    tenant_id = get_tenant_id_from_auth(request)
    auth_ctx = get_auth_context(request)
    prepared_by = getattr(auth_ctx, "user_id", "system") if auth_ctx else "system"

    service = get_export_bundle_service()

    try:
        bundle = await service.create_executive_debrief(
            incident_id=incident_id,
            prepared_for=export_request.prepared_for,
            prepared_by=prepared_by,
        )

        # Verify tenant access
        if bundle.tenant_id != tenant_id:
            raise HTTPException(
                status_code=403,
                detail={"error": "forbidden", "message": "Access denied to this incident"},
            )

        if export_request.format == ExportFormat.PDF:
            renderer = get_pdf_renderer()
            pdf_bytes = renderer.render_executive_debrief_pdf(bundle)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="debrief_{incident_id}.pdf"'
                },
            )

        return wrap_dict(bundle.model_dump(mode="json"))

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": str(e)},
        )
