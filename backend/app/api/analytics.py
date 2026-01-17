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
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep

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
# Signal Adapters (Internal - Behind Facade)
# =============================================================================


class SignalAdapter:
    """
    Base class for signal adapters.

    Contract: analytics.adapters.<signal>.fetch(window, resolution)

    Facade owns:
    - Time alignment
    - Cardinality control
    - Cross-signal reconciliation
    - Forward compatibility
    """

    @staticmethod
    async def fetch_cost_metrics(
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        resolution: ResolutionType,
    ) -> Dict[str, Any]:
        """Fetch cost metrics from cost_records table."""
        try:
            # Time grouping based on resolution
            if resolution == ResolutionType.HOUR:
                time_trunc = "hour"
            else:
                time_trunc = "day"

            query = text("""
                SELECT
                    DATE_TRUNC(:time_trunc, created_at) as ts,
                    COUNT(*) as requests,
                    COALESCE(SUM(input_tokens + output_tokens), 0) as tokens
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND created_at >= :from_ts
                  AND created_at < :to_ts
                GROUP BY DATE_TRUNC(:time_trunc, created_at)
                ORDER BY ts
            """)

            result = await session.execute(
                query,
                {
                    "time_trunc": time_trunc,
                    "tenant_id": tenant_id,
                    "from_ts": from_ts,
                    "to_ts": to_ts,
                },
            )
            rows = result.fetchall()

            return {
                "source": "cost_records",
                "data": [
                    {
                        "ts": row.ts.isoformat() if row.ts else None,
                        "requests": row.requests or 0,
                        "tokens": row.tokens or 0,
                    }
                    for row in rows
                ],
            }
        except Exception as e:
            logger.warning(f"Cost metrics fetch failed: {e}")
            return {"source": "cost_records", "data": [], "error": str(e)}

    @staticmethod
    async def fetch_llm_usage(
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        resolution: ResolutionType,
    ) -> Dict[str, Any]:
        """Fetch LLM usage from runs table."""
        try:
            if resolution == ResolutionType.HOUR:
                time_trunc = "hour"
            else:
                time_trunc = "day"

            query = text("""
                SELECT
                    DATE_TRUNC(:time_trunc, created_at) as ts,
                    COUNT(*) as requests,
                    COALESCE(SUM(total_tokens), 0) as tokens
                FROM runs
                WHERE tenant_id = :tenant_id
                  AND created_at >= :from_ts
                  AND created_at < :to_ts
                GROUP BY DATE_TRUNC(:time_trunc, created_at)
                ORDER BY ts
            """)

            result = await session.execute(
                query,
                {
                    "time_trunc": time_trunc,
                    "tenant_id": tenant_id,
                    "from_ts": from_ts,
                    "to_ts": to_ts,
                },
            )
            rows = result.fetchall()

            return {
                "source": "llm.usage",
                "data": [
                    {
                        "ts": row.ts.isoformat() if row.ts else None,
                        "requests": row.requests or 0,
                        "tokens": row.tokens or 0,
                    }
                    for row in rows
                ],
            }
        except Exception as e:
            logger.warning(f"LLM usage fetch failed: {e}")
            return {"source": "llm.usage", "data": [], "error": str(e)}

    @staticmethod
    async def fetch_worker_execution(
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        resolution: ResolutionType,
    ) -> Dict[str, Any]:
        """Fetch worker execution metrics from aos_traces table."""
        try:
            if resolution == ResolutionType.HOUR:
                time_trunc = "hour"
            else:
                time_trunc = "day"

            query = text("""
                SELECT
                    DATE_TRUNC(:time_trunc, created_at) as ts,
                    COUNT(*) as requests
                FROM aos_traces
                WHERE tenant_id = :tenant_id
                  AND created_at >= :from_ts
                  AND created_at < :to_ts
                GROUP BY DATE_TRUNC(:time_trunc, created_at)
                ORDER BY ts
            """)

            result = await session.execute(
                query,
                {
                    "time_trunc": time_trunc,
                    "tenant_id": tenant_id,
                    "from_ts": from_ts,
                    "to_ts": to_ts,
                },
            )
            rows = result.fetchall()

            return {
                "source": "worker.execution",
                "data": [
                    {
                        "ts": row.ts.isoformat() if row.ts else None,
                        "requests": row.requests or 0,
                    }
                    for row in rows
                ],
            }
        except Exception as e:
            logger.warning(f"Worker execution fetch failed: {e}")
            return {"source": "worker.execution", "data": [], "error": str(e)}

    @staticmethod
    async def fetch_gateway_metrics(
        _session: AsyncSession,
        _tenant_id: str,
        _from_ts: datetime,
        _to_ts: datetime,
        _resolution: ResolutionType,
    ) -> Dict[str, Any]:
        """
        Fetch gateway metrics.

        Note: Gateway metrics may come from Prometheus/external source.
        For now, we derive from runs table as proxy.
        """
        # Gateway metrics are currently derived from runs
        # In future, this would query a dedicated gateway_metrics table
        return {
            "source": "gateway.metrics",
            "data": [],
            "note": "Derived from llm.usage signal",
        }


# =============================================================================
# Signal Reconciliation
# =============================================================================


async def reconcile_usage_signals(
    session: AsyncSession,
    tenant_id: str,
    from_ts: datetime,
    to_ts: datetime,
    resolution: ResolutionType,
) -> tuple[UsageTotals, List[UsageDataPoint], UsageSignals]:
    """
    Reconcile multiple signal sources into unified usage data.

    Facade owns:
    - Time alignment
    - Cardinality control
    - Cross-signal reconciliation
    - Forward compatibility
    """
    # Fetch from all signal sources
    cost_data = await SignalAdapter.fetch_cost_metrics(
        session, tenant_id, from_ts, to_ts, resolution
    )
    llm_data = await SignalAdapter.fetch_llm_usage(
        session, tenant_id, from_ts, to_ts, resolution
    )
    worker_data = await SignalAdapter.fetch_worker_execution(
        session, tenant_id, from_ts, to_ts, resolution
    )
    # Gateway metrics are derived from llm.usage, no separate fetch needed
    # Future: await SignalAdapter.fetch_gateway_metrics(...)

    # Collect sources that returned data
    sources = []
    if cost_data.get("data"):
        sources.append("cost_records")
    if llm_data.get("data"):
        sources.append("llm.usage")
    if worker_data.get("data"):
        sources.append("worker.execution")
    # Gateway is derived, always include if llm.usage present
    if llm_data.get("data"):
        sources.append("gateway.metrics")

    # Time-align and merge data points
    # Use LLM usage as primary source (most complete)
    merged_by_ts: Dict[str, Dict[str, int]] = {}

    # Process LLM data (primary for requests and tokens)
    for point in llm_data.get("data", []):
        ts = point.get("ts")
        if ts:
            if ts not in merged_by_ts:
                merged_by_ts[ts] = {"requests": 0, "compute_units": 0, "tokens": 0}
            merged_by_ts[ts]["requests"] += point.get("requests", 0)
            merged_by_ts[ts]["tokens"] += point.get("tokens", 0)

    # Enrich with cost data (tokens from cost_records may be more accurate)
    for point in cost_data.get("data", []):
        ts = point.get("ts")
        if ts:
            if ts not in merged_by_ts:
                merged_by_ts[ts] = {"requests": 0, "compute_units": 0, "tokens": 0}
            # Cost records may have more accurate token counts
            if point.get("tokens", 0) > merged_by_ts[ts]["tokens"]:
                merged_by_ts[ts]["tokens"] = point.get("tokens", 0)

    # Enrich with worker execution (compute units = trace count as proxy)
    for point in worker_data.get("data", []):
        ts = point.get("ts")
        if ts:
            if ts not in merged_by_ts:
                merged_by_ts[ts] = {"requests": 0, "compute_units": 0, "tokens": 0}
            merged_by_ts[ts]["compute_units"] += point.get("requests", 0)

    # Build sorted series
    series = []
    for ts in sorted(merged_by_ts.keys()):
        data = merged_by_ts[ts]
        # Format timestamp based on resolution
        ts_formatted = ts.split("T")[0] if resolution == ResolutionType.DAY else ts
        series.append(
            UsageDataPoint(
                ts=ts_formatted,
                requests=data["requests"],
                compute_units=data["compute_units"],
                tokens=data["tokens"],
            )
        )

    # Calculate totals
    total_requests = sum(p.requests for p in series)
    total_compute_units = sum(p.compute_units for p in series)
    total_tokens = sum(p.tokens for p in series)

    totals = UsageTotals(
        requests=total_requests,
        compute_units=total_compute_units,
        tokens=total_tokens,
    )

    # Calculate freshness (seconds since last data point)
    freshness_sec = 0
    if series:
        try:
            last_ts = series[-1].ts
            if "T" in last_ts:
                last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            else:
                last_dt = datetime.fromisoformat(last_ts + "T00:00:00+00:00")
            freshness_sec = int((datetime.now(timezone.utc) - last_dt).total_seconds())
        except Exception:
            freshness_sec = 0

    signals = UsageSignals(
        sources=sources if sources else ["none"],
        freshness_sec=max(0, freshness_sec),
    )

    return totals, series, signals


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
    Facade normalizes, aggregates, and enforces contracts.
    """
    # Scope is declared for API contract, implementation pending
    _ = scope  # Future: filter by project/env

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

    # Reconcile signals
    totals, series, signals = await reconcile_usage_signals(
        session=session,
        tenant_id=tenant_id,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=resolution,
    )

    return UsageStatisticsResponse(
        window=UsageWindow.model_validate({
            "from": from_ts,
            "to": to_ts,
            "resolution": resolution,
        }),
        totals=totals,
        series=series,
        signals=signals,
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
    """
    return AnalyticsStatusResponse(
        domain="analytics",
        subdomains=["statistics"],
        topics={
            "usage": TopicStatus(
                read=True,
                write=False,
                signals_bound=3,  # cost_records, llm.usage, worker.execution
            ),
            # Future topics (declared but not yet bound)
            # "cost": TopicStatus(read=False, write=False, signals_bound=0),
            # "anomalies": TopicStatus(read=False, write=False, signals_bound=0),
        },
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
    """
    # Scope is declared for API contract, implementation pending
    _ = scope  # Future: filter by project/env

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

    # Reconcile signals
    totals, series, signals = await reconcile_usage_signals(
        session=session,
        tenant_id=tenant_id,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=resolution,
    )

    return UsageStatisticsResponse(
        window=UsageWindow.model_validate({
            "from": from_ts,
            "to": to_ts,
            "resolution": resolution,
        }),
        totals=totals,
        series=series,
        signals=signals,
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
