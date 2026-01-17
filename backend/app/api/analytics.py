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

    # -------------------------------------------------------------------------
    # Cost Topic Signal Adapters
    # -------------------------------------------------------------------------

    @staticmethod
    async def fetch_cost_spend(
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        resolution: ResolutionType,
    ) -> Dict[str, Any]:
        """
        Fetch cost spend data from cost_records table.

        Returns time series with spend_cents, requests, input_tokens, output_tokens.
        """
        try:
            if resolution == ResolutionType.HOUR:
                time_trunc = "hour"
            else:
                time_trunc = "day"

            query = text("""
                SELECT
                    DATE_TRUNC(:time_trunc, created_at) as ts,
                    COUNT(*) as requests,
                    COALESCE(SUM(cost_cents), 0) as spend_cents,
                    COALESCE(SUM(input_tokens), 0) as input_tokens,
                    COALESCE(SUM(output_tokens), 0) as output_tokens
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
                        "spend_cents": float(row.spend_cents or 0),
                        "requests": row.requests or 0,
                        "input_tokens": row.input_tokens or 0,
                        "output_tokens": row.output_tokens or 0,
                    }
                    for row in rows
                ],
            }
        except Exception as e:
            logger.warning(f"Cost spend fetch failed: {e}")
            return {"source": "cost_records", "data": [], "error": str(e)}

    @staticmethod
    async def fetch_cost_by_model(
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> Dict[str, Any]:
        """
        Fetch cost breakdown by model from cost_records table.
        """
        try:
            query = text("""
                SELECT
                    COALESCE(model, 'unknown') as model,
                    COUNT(*) as requests,
                    COALESCE(SUM(cost_cents), 0) as spend_cents,
                    COALESCE(SUM(input_tokens), 0) as input_tokens,
                    COALESCE(SUM(output_tokens), 0) as output_tokens
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND created_at >= :from_ts
                  AND created_at < :to_ts
                GROUP BY model
                ORDER BY spend_cents DESC
            """)

            result = await session.execute(
                query,
                {
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
                        "model": row.model,
                        "spend_cents": float(row.spend_cents or 0),
                        "requests": row.requests or 0,
                        "input_tokens": row.input_tokens or 0,
                        "output_tokens": row.output_tokens or 0,
                    }
                    for row in rows
                ],
            }
        except Exception as e:
            logger.warning(f"Cost by model fetch failed: {e}")
            return {"source": "cost_records", "data": [], "error": str(e)}

    @staticmethod
    async def fetch_cost_by_feature(
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> Dict[str, Any]:
        """
        Fetch cost breakdown by feature tag from cost_records table.
        """
        try:
            query = text("""
                SELECT
                    COALESCE(feature_tag, 'untagged') as feature_tag,
                    COUNT(*) as requests,
                    COALESCE(SUM(cost_cents), 0) as spend_cents
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND created_at >= :from_ts
                  AND created_at < :to_ts
                GROUP BY feature_tag
                ORDER BY spend_cents DESC
            """)

            result = await session.execute(
                query,
                {
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
                        "feature_tag": row.feature_tag,
                        "spend_cents": float(row.spend_cents or 0),
                        "requests": row.requests or 0,
                    }
                    for row in rows
                ],
            }
        except Exception as e:
            logger.warning(f"Cost by feature fetch failed: {e}")
            return {"source": "cost_records", "data": [], "error": str(e)}


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


async def reconcile_cost_signals(
    session: AsyncSession,
    tenant_id: str,
    from_ts: datetime,
    to_ts: datetime,
    resolution: ResolutionType,
) -> tuple[CostTotals, List[CostDataPoint], List[CostByModel], List[CostByFeature], CostSignals]:
    """
    Reconcile cost signals into unified cost data.

    Primary source: cost_records table
    """
    # Fetch cost data from all perspectives
    spend_data = await SignalAdapter.fetch_cost_spend(
        session, tenant_id, from_ts, to_ts, resolution
    )
    model_data = await SignalAdapter.fetch_cost_by_model(
        session, tenant_id, from_ts, to_ts
    )
    feature_data = await SignalAdapter.fetch_cost_by_feature(
        session, tenant_id, from_ts, to_ts
    )

    # Collect sources
    sources = ["cost_records"] if spend_data.get("data") else []

    # Build time series
    series = []
    for point in spend_data.get("data", []):
        ts = point.get("ts")
        if ts:
            ts_formatted = ts.split("T")[0] if resolution == ResolutionType.DAY else ts
            series.append(
                CostDataPoint(
                    ts=ts_formatted,
                    spend_cents=point.get("spend_cents", 0),
                    requests=point.get("requests", 0),
                    input_tokens=point.get("input_tokens", 0),
                    output_tokens=point.get("output_tokens", 0),
                )
            )

    # Calculate totals
    total_spend_cents = sum(p.spend_cents for p in series)
    total_requests = sum(p.requests for p in series)
    total_input_tokens = sum(p.input_tokens for p in series)
    total_output_tokens = sum(p.output_tokens for p in series)

    totals = CostTotals(
        spend_cents=total_spend_cents,
        spend_usd=total_spend_cents / 100.0,
        requests=total_requests,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
    )

    # Build by-model breakdown with percentages
    by_model = []
    for item in model_data.get("data", []):
        pct = (item.get("spend_cents", 0) / total_spend_cents * 100) if total_spend_cents > 0 else 0
        by_model.append(
            CostByModel(
                model=item.get("model", "unknown"),
                spend_cents=item.get("spend_cents", 0),
                requests=item.get("requests", 0),
                input_tokens=item.get("input_tokens", 0),
                output_tokens=item.get("output_tokens", 0),
                pct_of_total=round(pct, 2),
            )
        )

    # Build by-feature breakdown with percentages
    by_feature = []
    for item in feature_data.get("data", []):
        pct = (item.get("spend_cents", 0) / total_spend_cents * 100) if total_spend_cents > 0 else 0
        by_feature.append(
            CostByFeature(
                feature_tag=item.get("feature_tag", "untagged"),
                spend_cents=item.get("spend_cents", 0),
                requests=item.get("requests", 0),
                pct_of_total=round(pct, 2),
            )
        )

    # Calculate freshness
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

    signals = CostSignals(
        sources=sources if sources else ["none"],
        freshness_sec=max(0, freshness_sec),
    )

    return totals, series, by_model, by_feature, signals


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
            "cost": TopicStatus(
                read=True,
                write=False,
                signals_bound=1,  # cost_records
            ),
            # Future topics (declared but not yet bound)
            # "anomalies": TopicStatus(read=False, write=False, signals_bound=0),
        },
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

    # Reconcile cost signals
    totals, series, by_model, by_feature, signals = await reconcile_cost_signals(
        session=session,
        tenant_id=tenant_id,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=resolution,
    )

    return CostStatisticsResponse(
        window=TimeWindow.model_validate({
            "from": from_ts,
            "to": to_ts,
            "resolution": resolution,
        }),
        totals=totals,
        series=series,
        by_model=by_model,
        by_feature=by_feature,
        signals=signals,
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

    # Reconcile cost signals
    totals, series, by_model, by_feature, signals = await reconcile_cost_signals(
        session=session,
        tenant_id=tenant_id,
        from_ts=from_ts,
        to_ts=to_ts,
        resolution=resolution,
    )

    return CostStatisticsResponse(
        window=TimeWindow.model_validate({
            "from": from_ts,
            "to": to_ts,
            "resolution": resolution,
        }),
        totals=totals,
        series=series,
        by_model=by_model,
        by_feature=by_feature,
        signals=signals,
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
