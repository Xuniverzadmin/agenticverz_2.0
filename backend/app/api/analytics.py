# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified ANALYTICS domain facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: Analytics Domain Declaration v1, PIN-411
#
# GOVERNANCE NOTE:
# This is the ONE facade for ANALYTICS domain.
# All analytics reads flow through this API.
# Console sidebar: LIVE (6th primary domain)
# Reporting/export: LIVE (CSV/JSON endpoints)

"""
Unified Analytics API (L2)

Customer-facing endpoints for viewing usage statistics.
All requests are tenant-scoped via auth_context.

Domain: Analytics
Subdomain: Statistics
Topic v1: Usage

Endpoints:
- GET /api/v1/analytics/statistics/usage             → Usage statistics
- GET /api/v1/analytics/statistics/usage/export.csv  → CSV export
- GET /api/v1/analytics/statistics/usage/export.json → JSON export
- GET /api/v1/analytics/_status                      → Capability probe

Architecture:
- ONE facade for all ANALYTICS needs
- Facade normalizes, aggregates, enforces contracts
- Does NOT compute - delegates to signal adapters
- Tenant isolation via auth_context (not header)
- Export endpoints use SAME aggregator (bit-equivalent)
"""

import csv
import io
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.hoc.cus.analytics.L5_engines.analytics_facade import get_analytics_facade

logger = logging.getLogger(__name__)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/analytics", tags=["analytics"])


# =============================================================================
# Enums
# =============================================================================


class ResolutionType(str, Enum):
    """Time resolution for usage data."""
    HOUR = "hour"
    DAY = "day"


class ScopeType(str, Enum):
    """Scope of usage aggregation."""
    ORG = "org"
    PROJECT = "project"
    ENV = "env"


# =============================================================================
# Response Models (Contracted)
# =============================================================================


class TimeWindow(BaseModel):
    """Generic time window specification (shared across topics)."""
    from_ts: datetime = Field(..., alias="from")
    to_ts: datetime = Field(..., alias="to")
    resolution: ResolutionType

    class Config:
        populate_by_name = True


# -----------------------------------------------------------------------------
# Usage Topic Response Models
# -----------------------------------------------------------------------------


class UsageWindow(BaseModel):
    """Time window specification."""
    from_ts: datetime = Field(..., alias="from")
    to_ts: datetime = Field(..., alias="to")
    resolution: ResolutionType

    class Config:
        populate_by_name = True


class UsageTotals(BaseModel):
    """Aggregate usage totals."""
    requests: int = Field(..., description="Total API requests")
    compute_units: int = Field(..., description="Total compute units consumed")
    tokens: int = Field(..., description="Total tokens processed")


class UsageDataPoint(BaseModel):
    """Single data point in usage time series."""
    ts: str = Field(..., description="Timestamp (ISO-8601 date or datetime)")
    requests: int
    compute_units: int
    tokens: int


class UsageSignals(BaseModel):
    """Signal source metadata for provenance."""
    sources: List[str] = Field(..., description="Signal sources used")
    freshness_sec: int = Field(..., description="Data freshness in seconds")


class UsageStatisticsResponse(BaseModel):
    """GET /api/v1/analytics/statistics/usage response (contracted)."""
    window: UsageWindow
    totals: UsageTotals
    series: List[UsageDataPoint]
    signals: UsageSignals


# -----------------------------------------------------------------------------
# Cost Topic Response Models
# -----------------------------------------------------------------------------


class CostTotals(BaseModel):
    """Aggregate cost totals."""
    spend_cents: float = Field(..., description="Total spend in cents")
    spend_usd: float = Field(..., description="Total spend in USD")
    requests: int = Field(..., description="Total requests")
    input_tokens: int = Field(..., description="Total input tokens")
    output_tokens: int = Field(..., description="Total output tokens")


class CostDataPoint(BaseModel):
    """Single data point in cost time series."""
    ts: str = Field(..., description="Timestamp (ISO-8601 date or datetime)")
    spend_cents: float = Field(..., description="Spend in cents")
    requests: int = Field(..., description="Number of requests")
    input_tokens: int = Field(..., description="Input tokens")
    output_tokens: int = Field(..., description="Output tokens")


class CostByModel(BaseModel):
    """Cost breakdown by model."""
    model: str = Field(..., description="Model name")
    spend_cents: float = Field(..., description="Total spend for this model")
    requests: int = Field(..., description="Request count")
    input_tokens: int = Field(..., description="Input tokens")
    output_tokens: int = Field(..., description="Output tokens")
    pct_of_total: float = Field(..., description="Percentage of total spend")


class CostByFeature(BaseModel):
    """Cost breakdown by feature tag."""
    feature_tag: str = Field(..., description="Feature tag")
    spend_cents: float = Field(..., description="Total spend for this feature")
    requests: int = Field(..., description="Request count")
    pct_of_total: float = Field(..., description="Percentage of total spend")


class CostSignals(BaseModel):
    """Signal source metadata for cost provenance."""
    sources: List[str] = Field(..., description="Signal sources used")
    freshness_sec: int = Field(..., description="Data freshness in seconds")


class CostStatisticsResponse(BaseModel):
    """GET /api/v1/analytics/statistics/cost response (contracted)."""
    window: TimeWindow
    totals: CostTotals
    series: List[CostDataPoint]
    by_model: List[CostByModel]
    by_feature: List[CostByFeature]
    signals: CostSignals


class TopicStatus(BaseModel):
    """Status of a topic within a subdomain."""
    read: bool
    write: bool
    signals_bound: int


class AnalyticsStatusResponse(BaseModel):
    """GET /api/v1/analytics/_status response."""
    domain: str = "analytics"
    subdomains: List[str]
    topics: Dict[str, TopicStatus]


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/statistics/usage",
    response_model=UsageStatisticsResponse,
    summary="Get usage statistics (O2)",
    description="""
Returns usage statistics for the specified time window.

**Domain:** Analytics
**Subdomain:** Statistics
**Topic:** Usage

Signal sources:
- cost_records (cost attribution)
- llm.usage (LLM runs)
- worker.execution (trace execution)
- gateway.metrics (API gateway)
""",
)
async def get_usage_statistics(
    request: Request,
    from_ts: Annotated[
        datetime,
        Query(
            alias="from",
            description="Start of time window (ISO-8601)",
        ),
    ],
    to_ts: Annotated[
        datetime,
        Query(
            alias="to",
            description="End of time window (ISO-8601)",
        ),
    ],
    resolution: Annotated[
        ResolutionType,
        Query(description="Time resolution: hour or day"),
    ] = ResolutionType.DAY,
    scope: Annotated[
        ScopeType,
        Query(description="Aggregation scope: org, project, or env"),
    ] = ScopeType.ORG,
    session: AsyncSession = Depends(get_async_session_dep),
) -> UsageStatisticsResponse:
    """
    Get usage statistics for the specified time window.

    This is the primary read endpoint for the Usage topic.
    READ-ONLY customer facade - delegates to L4 AnalyticsFacade.
    """
    # Get tenant from auth context
    auth_context = get_auth_context(request)
    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context required")

    # Validate time window
    if from_ts >= to_ts:
        raise HTTPException(
            status_code=400,
            detail="'from' must be before 'to'",
        )

    # Limit window to 90 days max
    max_window = timedelta(days=90)
    if to_ts - from_ts > max_window:
        raise HTTPException(
            status_code=400,
            detail="Time window cannot exceed 90 days",
        )

    # Delegate to L4 facade
    from app.hoc.cus.analytics.L5_engines.analytics_facade import ResolutionType as FacadeResolution, ScopeType as FacadeScope
    facade = get_analytics_facade()

    # Map L2 enums to L4 enums
    facade_resolution = FacadeResolution.HOUR if resolution == ResolutionType.HOUR else FacadeResolution.DAY
    facade_scope = FacadeScope.ORG
    if scope == ScopeType.PROJECT:
        facade_scope = FacadeScope.PROJECT
    elif scope == ScopeType.ENV:
        facade_scope = FacadeScope.ENV

    result = await facade.get_usage_statistics(
        session=session,
        tenant_id=tenant_id,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=facade_resolution,
        scope=facade_scope,
    )

    # Map L4 result to L2 response
    series = [
        UsageDataPoint(
            ts=point.ts,
            requests=point.requests,
            compute_units=point.compute_units,
            tokens=point.tokens,
        )
        for point in result.series
    ]

    return UsageStatisticsResponse(
        window=UsageWindow.model_validate({
            "from": result.window.from_ts,
            "to": result.window.to_ts,
            "resolution": resolution,
        }),
        totals=UsageTotals(
            requests=result.totals.requests,
            compute_units=result.totals.compute_units,
            tokens=result.totals.tokens,
        ),
        series=series,
        signals=UsageSignals(
            sources=result.signals.sources,
            freshness_sec=result.signals.freshness_sec,
        ),
    )


@router.get(
    "/_status",
    response_model=AnalyticsStatusResponse,
    summary="Analytics capability probe",
    description="""
Returns the status of the Analytics domain.

Purpose: De-risk console wiring later by exposing:
- Available subdomains
- Available topics per subdomain
- Read/write capabilities
- Number of signals bound
""",
)
async def get_analytics_status() -> AnalyticsStatusResponse:
    """
    Analytics capability probe.

    Used by console/clients to discover available capabilities
    before attempting to render panels.
    READ-ONLY customer facade - delegates to L4 AnalyticsFacade.
    """
    facade = get_analytics_facade()
    result = facade.get_status()

    # Map L4 result to L2 response
    topics = {
        name: TopicStatus(
            read=status.read,
            write=status.write,
            signals_bound=status.signals_bound,
        )
        for name, status in result.topics.items()
    }

    return AnalyticsStatusResponse(
        domain=result.domain,
        subdomains=result.subdomains,
        topics=topics,
    )


# =============================================================================
# Cost Topic Endpoints
# =============================================================================


@router.get(
    "/statistics/cost",
    response_model=CostStatisticsResponse,
    summary="Get cost statistics",
    description="""
Returns cost statistics for the specified time window.

**Domain:** Analytics
**Subdomain:** Statistics
**Topic:** Cost

Includes:
- Time series of spend (cents)
- Breakdown by model
- Breakdown by feature tag
- Totals with USD conversion

Signal sources:
- cost_records (primary)
""",
)
async def get_cost_statistics(
    request: Request,
    from_ts: Annotated[
        datetime,
        Query(
            alias="from",
            description="Start of time window (ISO-8601)",
        ),
    ],
    to_ts: Annotated[
        datetime,
        Query(
            alias="to",
            description="End of time window (ISO-8601)",
        ),
    ],
    resolution: Annotated[
        ResolutionType,
        Query(description="Time resolution: hour or day"),
    ] = ResolutionType.DAY,
    scope: Annotated[
        ScopeType,
        Query(description="Aggregation scope: org, project, or env"),
    ] = ScopeType.ORG,
    session: AsyncSession = Depends(get_async_session_dep),
) -> CostStatisticsResponse:
    """
    Get cost statistics for the specified time window.

    Primary endpoint for the Cost topic.
    READ-ONLY customer facade - delegates to L4 AnalyticsFacade.
    """
    # Get tenant from auth context
    auth_context = get_auth_context(request)
    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context required")

    # Validate time window
    if from_ts >= to_ts:
        raise HTTPException(
            status_code=400,
            detail="'from' must be before 'to'",
        )

    # Limit window to 90 days max
    max_window = timedelta(days=90)
    if to_ts - from_ts > max_window:
        raise HTTPException(
            status_code=400,
            detail="Time window cannot exceed 90 days",
        )

    # Delegate to L4 facade
    from app.hoc.cus.analytics.L5_engines.analytics_facade import ResolutionType as FacadeResolution, ScopeType as FacadeScope
    facade = get_analytics_facade()

    # Map L2 enums to L4 enums
    facade_resolution = FacadeResolution.HOUR if resolution == ResolutionType.HOUR else FacadeResolution.DAY
    facade_scope = FacadeScope.ORG
    if scope == ScopeType.PROJECT:
        facade_scope = FacadeScope.PROJECT
    elif scope == ScopeType.ENV:
        facade_scope = FacadeScope.ENV

    result = await facade.get_cost_statistics(
        session=session,
        tenant_id=tenant_id,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=facade_resolution,
        scope=facade_scope,
    )

    # Map L4 result to L2 response
    series = [
        CostDataPoint(
            ts=point.ts,
            spend_cents=point.spend_cents,
            requests=point.requests,
            input_tokens=point.input_tokens,
            output_tokens=point.output_tokens,
        )
        for point in result.series
    ]

    by_model = [
        CostByModel(
            model=item.model,
            spend_cents=item.spend_cents,
            requests=item.requests,
            input_tokens=item.input_tokens,
            output_tokens=item.output_tokens,
            pct_of_total=item.pct_of_total,
        )
        for item in result.by_model
    ]

    by_feature = [
        CostByFeature(
            feature_tag=item.feature_tag,
            spend_cents=item.spend_cents,
            requests=item.requests,
            pct_of_total=item.pct_of_total,
        )
        for item in result.by_feature
    ]

    return CostStatisticsResponse(
        window=TimeWindow.model_validate({
            "from": result.window.from_ts,
            "to": result.window.to_ts,
            "resolution": resolution,
        }),
        totals=CostTotals(
            spend_cents=result.totals.spend_cents,
            spend_usd=result.totals.spend_usd,
            requests=result.totals.requests,
            input_tokens=result.totals.input_tokens,
            output_tokens=result.totals.output_tokens,
        ),
        series=series,
        by_model=by_model,
        by_feature=by_feature,
        signals=CostSignals(
            sources=result.signals.sources,
            freshness_sec=result.signals.freshness_sec,
        ),
    )


# =============================================================================
# Health Check (Internal)
# =============================================================================


@router.get(
    "/health",
    include_in_schema=False,
)
async def analytics_health():
    """Internal health check for analytics facade."""
    return {"status": "healthy", "domain": "analytics"}


# =============================================================================
# Export Endpoints (LIVE - Not Placeholder)
# =============================================================================


async def _get_usage_data(
    request: Request,
    from_ts: datetime,
    to_ts: datetime,
    resolution: ResolutionType,
    scope: ScopeType,
    session: AsyncSession,
) -> UsageStatisticsResponse:
    """
    Internal helper to get usage data (shared by read and export endpoints).

    Ensures export is bit-equivalent to read API - no alternate code paths.
    Delegates to L4 AnalyticsFacade.
    """
    # Get tenant from auth context
    auth_context = get_auth_context(request)
    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context required")

    # Validate time window
    if from_ts >= to_ts:
        raise HTTPException(
            status_code=400,
            detail="'from' must be before 'to'",
        )

    # Limit window to 90 days max
    max_window = timedelta(days=90)
    if to_ts - from_ts > max_window:
        raise HTTPException(
            status_code=400,
            detail="Time window cannot exceed 90 days",
        )

    # Delegate to L4 facade
    from app.hoc.cus.analytics.L5_engines.analytics_facade import ResolutionType as FacadeResolution, ScopeType as FacadeScope
    facade = get_analytics_facade()

    # Map L2 enums to L4 enums
    facade_resolution = FacadeResolution.HOUR if resolution == ResolutionType.HOUR else FacadeResolution.DAY
    facade_scope = FacadeScope.ORG
    if scope == ScopeType.PROJECT:
        facade_scope = FacadeScope.PROJECT
    elif scope == ScopeType.ENV:
        facade_scope = FacadeScope.ENV

    result = await facade.get_usage_statistics(
        session=session,
        tenant_id=tenant_id,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=facade_resolution,
        scope=facade_scope,
    )

    # Map L4 result to L2 response
    series = [
        UsageDataPoint(
            ts=point.ts,
            requests=point.requests,
            compute_units=point.compute_units,
            tokens=point.tokens,
        )
        for point in result.series
    ]

    return UsageStatisticsResponse(
        window=UsageWindow.model_validate({
            "from": result.window.from_ts,
            "to": result.window.to_ts,
            "resolution": resolution,
        }),
        totals=UsageTotals(
            requests=result.totals.requests,
            compute_units=result.totals.compute_units,
            tokens=result.totals.tokens,
        ),
        series=series,
        signals=UsageSignals(
            sources=result.signals.sources,
            freshness_sec=result.signals.freshness_sec,
        ),
    )


@router.get(
    "/statistics/usage/export.csv",
    summary="Export usage statistics (CSV)",
    description="""
Exports usage statistics as CSV.
Uses the same aggregation logic as the read API.
CSV format: timestamp,requests,compute_units,tokens

**Contract:**
- Deterministic ordering (by timestamp, UTC)
- Same query parameters as read endpoint
- Bit-equivalent to read API (no recomputation)
""",
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "CSV export file",
        }
    },
)
async def export_usage_csv(
    request: Request,
    from_ts: Annotated[
        datetime,
        Query(
            alias="from",
            description="Start of time window (ISO-8601)",
        ),
    ],
    to_ts: Annotated[
        datetime,
        Query(
            alias="to",
            description="End of time window (ISO-8601)",
        ),
    ],
    resolution: Annotated[
        ResolutionType,
        Query(description="Time resolution: hour or day"),
    ] = ResolutionType.DAY,
    scope: Annotated[
        ScopeType,
        Query(description="Aggregation scope: org, project, or env"),
    ] = ScopeType.ORG,
    session: AsyncSession = Depends(get_async_session_dep),
) -> Response:
    """
    Export usage statistics as CSV.

    Uses the same aggregation logic as the read API.
    Deterministic ordering. UTC only.
    """
    # Get usage data (same as read API)
    data = await _get_usage_data(
        request=request,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=resolution,
        scope=scope,
        session=session,
    )

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["timestamp", "requests", "compute_units", "tokens"])

    # Data rows (deterministic ordering - already sorted by timestamp)
    for point in data.series:
        writer.writerow([
            point.ts,
            point.requests,
            point.compute_units,
            point.tokens,
        ])

    # Create filename with time range
    from_str = from_ts.strftime("%Y%m%d")
    to_str = to_ts.strftime("%Y%m%d")
    filename = f"usage_{from_str}_{to_str}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/statistics/usage/export.json",
    response_model=UsageStatisticsResponse,
    summary="Export usage statistics (JSON)",
    description="""
Exports usage statistics as JSON.
Structure matches the standard usage response.

**Contract:**
- Same structure as GET /analytics/statistics/usage
- Same query parameters as read endpoint
- Bit-equivalent to read API (no recomputation)
""",
)
async def export_usage_json(
    request: Request,
    from_ts: Annotated[
        datetime,
        Query(
            alias="from",
            description="Start of time window (ISO-8601)",
        ),
    ],
    to_ts: Annotated[
        datetime,
        Query(
            alias="to",
            description="End of time window (ISO-8601)",
        ),
    ],
    resolution: Annotated[
        ResolutionType,
        Query(description="Time resolution: hour or day"),
    ] = ResolutionType.DAY,
    scope: Annotated[
        ScopeType,
        Query(description="Aggregation scope: org, project, or env"),
    ] = ScopeType.ORG,
    session: AsyncSession = Depends(get_async_session_dep),
) -> UsageStatisticsResponse:
    """
    Export usage statistics as JSON.

    Structure matches the standard usage response.
    Bit-equivalent to read API.
    """
    return await _get_usage_data(
        request=request,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=resolution,
        scope=scope,
        session=session,
    )


# =============================================================================
# Cost Export Endpoints
# =============================================================================


async def _get_cost_data(
    request: Request,
    from_ts: datetime,
    to_ts: datetime,
    resolution: ResolutionType,
    scope: ScopeType,
    session: AsyncSession,
) -> CostStatisticsResponse:
    """
    Internal helper to get cost data (shared by read and export endpoints).

    Ensures export is bit-equivalent to read API - no alternate code paths.
    Delegates to L4 AnalyticsFacade.
    """
    # Get tenant from auth context
    auth_context = get_auth_context(request)
    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context required")

    # Validate time window
    if from_ts >= to_ts:
        raise HTTPException(
            status_code=400,
            detail="'from' must be before 'to'",
        )

    # Limit window to 90 days max
    max_window = timedelta(days=90)
    if to_ts - from_ts > max_window:
        raise HTTPException(
            status_code=400,
            detail="Time window cannot exceed 90 days",
        )

    # Delegate to L4 facade
    from app.hoc.cus.analytics.L5_engines.analytics_facade import ResolutionType as FacadeResolution, ScopeType as FacadeScope
    facade = get_analytics_facade()

    # Map L2 enums to L4 enums
    facade_resolution = FacadeResolution.HOUR if resolution == ResolutionType.HOUR else FacadeResolution.DAY
    facade_scope = FacadeScope.ORG
    if scope == ScopeType.PROJECT:
        facade_scope = FacadeScope.PROJECT
    elif scope == ScopeType.ENV:
        facade_scope = FacadeScope.ENV

    result = await facade.get_cost_statistics(
        session=session,
        tenant_id=tenant_id,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=facade_resolution,
        scope=facade_scope,
    )

    # Map L4 result to L2 response
    series = [
        CostDataPoint(
            ts=point.ts,
            spend_cents=point.spend_cents,
            requests=point.requests,
            input_tokens=point.input_tokens,
            output_tokens=point.output_tokens,
        )
        for point in result.series
    ]

    by_model = [
        CostByModel(
            model=item.model,
            spend_cents=item.spend_cents,
            requests=item.requests,
            input_tokens=item.input_tokens,
            output_tokens=item.output_tokens,
            pct_of_total=item.pct_of_total,
        )
        for item in result.by_model
    ]

    by_feature = [
        CostByFeature(
            feature_tag=item.feature_tag,
            spend_cents=item.spend_cents,
            requests=item.requests,
            pct_of_total=item.pct_of_total,
        )
        for item in result.by_feature
    ]

    return CostStatisticsResponse(
        window=TimeWindow.model_validate({
            "from": result.window.from_ts,
            "to": result.window.to_ts,
            "resolution": resolution,
        }),
        totals=CostTotals(
            spend_cents=result.totals.spend_cents,
            spend_usd=result.totals.spend_usd,
            requests=result.totals.requests,
            input_tokens=result.totals.input_tokens,
            output_tokens=result.totals.output_tokens,
        ),
        series=series,
        by_model=by_model,
        by_feature=by_feature,
        signals=CostSignals(
            sources=result.signals.sources,
            freshness_sec=result.signals.freshness_sec,
        ),
    )


@router.get(
    "/statistics/cost/export.csv",
    summary="Export cost statistics (CSV)",
    description="""
Exports cost statistics as CSV.
Uses the same aggregation logic as the read API.
CSV format: timestamp,spend_cents,requests,input_tokens,output_tokens

**Contract:**
- Deterministic ordering (by timestamp, UTC)
- Same query parameters as read endpoint
- Bit-equivalent to read API (no recomputation)
""",
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "CSV export file",
        }
    },
)
async def export_cost_csv(
    request: Request,
    from_ts: Annotated[
        datetime,
        Query(
            alias="from",
            description="Start of time window (ISO-8601)",
        ),
    ],
    to_ts: Annotated[
        datetime,
        Query(
            alias="to",
            description="End of time window (ISO-8601)",
        ),
    ],
    resolution: Annotated[
        ResolutionType,
        Query(description="Time resolution: hour or day"),
    ] = ResolutionType.DAY,
    scope: Annotated[
        ScopeType,
        Query(description="Aggregation scope: org, project, or env"),
    ] = ScopeType.ORG,
    session: AsyncSession = Depends(get_async_session_dep),
) -> Response:
    """
    Export cost statistics as CSV.

    Uses the same aggregation logic as the read API.
    Deterministic ordering. UTC only.
    """
    # Get cost data (same as read API)
    data = await _get_cost_data(
        request=request,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=resolution,
        scope=scope,
        session=session,
    )

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["timestamp", "spend_cents", "requests", "input_tokens", "output_tokens"])

    # Data rows (deterministic ordering - already sorted by timestamp)
    for point in data.series:
        writer.writerow([
            point.ts,
            point.spend_cents,
            point.requests,
            point.input_tokens,
            point.output_tokens,
        ])

    # Create filename with time range
    from_str = from_ts.strftime("%Y%m%d")
    to_str = to_ts.strftime("%Y%m%d")
    filename = f"cost_{from_str}_{to_str}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/statistics/cost/export.json",
    response_model=CostStatisticsResponse,
    summary="Export cost statistics (JSON)",
    description="""
Exports cost statistics as JSON.
Structure matches the standard cost response.

**Contract:**
- Same structure as GET /analytics/statistics/cost
- Same query parameters as read endpoint
- Bit-equivalent to read API (no recomputation)
""",
)
async def export_cost_json(
    request: Request,
    from_ts: Annotated[
        datetime,
        Query(
            alias="from",
            description="Start of time window (ISO-8601)",
        ),
    ],
    to_ts: Annotated[
        datetime,
        Query(
            alias="to",
            description="End of time window (ISO-8601)",
        ),
    ],
    resolution: Annotated[
        ResolutionType,
        Query(description="Time resolution: hour or day"),
    ] = ResolutionType.DAY,
    scope: Annotated[
        ScopeType,
        Query(description="Aggregation scope: org, project, or env"),
    ] = ScopeType.ORG,
    session: AsyncSession = Depends(get_async_session_dep),
) -> CostStatisticsResponse:
    """
    Export cost statistics as JSON.

    Structure matches the standard cost response.
    Bit-equivalent to read API.
    """
    return await _get_cost_data(
        request=request,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=resolution,
        scope=scope,
        session=session,
    )
