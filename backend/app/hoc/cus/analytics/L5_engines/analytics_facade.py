# capability_id: CAP-002
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via L6 drivers
#   Writes: none
# Role: Analytics Facade - Centralized access to analytics domain operations
# Callers: app.hoc.api.cus.analytics.* (L2)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, Analytics Domain Declaration v1, PIN-411, W4 Pattern
# Location: hoc/cus/analytics/L5_engines/analytics_facade.py
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.

"""
Analytics Facade (L5)

Provides unified access to analytics domain operations.
This is the single entry point for all analytics business logic.

Operations:
- get_usage_statistics: Get usage statistics for a time window
- get_cost_statistics: Get cost statistics for a time window
- get_status: Get analytics domain capability status

Signal Sources:
- cost_records (cost attribution)
- llm.usage (LLM runs)
- worker.execution (trace execution)
- gateway.metrics (API gateway)

Reference: Analytics Domain Declaration v1
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from app.hoc.cus.analytics.L6_drivers.analytics_read_driver import (
    get_analytics_read_driver,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.services.analytics.facade")


# =============================================================================
# Enums
# =============================================================================


# Re-export from L5_schemas for backward compatibility (PIN-504)
from app.hoc.cus.analytics.L5_schemas.query_types import ResolutionType, ScopeType


# =============================================================================
# Result Dataclasses
# =============================================================================


@dataclass
class TimeWindowResult:
    """Time window specification."""

    from_ts: datetime
    to_ts: datetime
    resolution: str


@dataclass
class UsageTotalsResult:
    """Aggregate usage totals."""

    requests: int
    compute_units: int
    tokens: int


@dataclass
class UsageDataPointResult:
    """Single data point in usage time series."""

    ts: str
    requests: int
    compute_units: int
    tokens: int


@dataclass
class SignalSourceResult:
    """Signal source metadata."""

    sources: list[str]
    freshness_sec: int


@dataclass
class UsageStatisticsResult:
    """Usage statistics result."""

    window: TimeWindowResult
    totals: UsageTotalsResult
    series: list[UsageDataPointResult]
    signals: SignalSourceResult


@dataclass
class CostTotalsResult:
    """Aggregate cost totals."""

    spend_cents: float
    spend_usd: float
    requests: int
    input_tokens: int
    output_tokens: int


@dataclass
class CostDataPointResult:
    """Single data point in cost time series."""

    ts: str
    spend_cents: float
    requests: int
    input_tokens: int
    output_tokens: int


@dataclass
class CostByModelResult:
    """Cost breakdown by model."""

    model: str
    spend_cents: float
    requests: int
    input_tokens: int
    output_tokens: int
    pct_of_total: float


@dataclass
class CostByFeatureResult:
    """Cost breakdown by feature tag."""

    feature_tag: str
    spend_cents: float
    requests: int
    pct_of_total: float


@dataclass
class CostStatisticsResult:
    """Cost statistics result."""

    window: TimeWindowResult
    totals: CostTotalsResult
    series: list[CostDataPointResult]
    by_model: list[CostByModelResult]
    by_feature: list[CostByFeatureResult]
    signals: SignalSourceResult


@dataclass
class TopicStatusResult:
    """Status of a topic within a subdomain."""

    read: bool
    write: bool
    signals_bound: int


@dataclass
class AnalyticsStatusResult:
    """Analytics domain status."""

    domain: str = "analytics"
    subdomains: list[str] = field(default_factory=lambda: ["statistics"])
    topics: dict[str, TopicStatusResult] = field(default_factory=dict)


# =============================================================================
# Signal Adapters
# =============================================================================


class SignalAdapter:
    """
    Signal adapters for fetching data from various sources.

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
    ) -> dict[str, Any]:
        """Fetch cost metrics from cost_records table."""
        try:
            time_trunc = "hour" if resolution == ResolutionType.HOUR else "day"
            driver = get_analytics_read_driver(session)
            data = await driver.fetch_cost_metrics(tenant_id, from_ts, to_ts, time_trunc)
            return {"source": "cost_records", "data": data}
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
    ) -> dict[str, Any]:
        """Fetch LLM usage from runs table."""
        try:
            time_trunc = "hour" if resolution == ResolutionType.HOUR else "day"
            driver = get_analytics_read_driver(session)
            data = await driver.fetch_llm_usage(tenant_id, from_ts, to_ts, time_trunc)
            return {"source": "llm.usage", "data": data}
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
    ) -> dict[str, Any]:
        """Fetch worker execution metrics from aos_traces table."""
        try:
            time_trunc = "hour" if resolution == ResolutionType.HOUR else "day"
            driver = get_analytics_read_driver(session)
            data = await driver.fetch_worker_execution(tenant_id, from_ts, to_ts, time_trunc)
            return {"source": "worker.execution", "data": data}
        except Exception as e:
            logger.warning(f"Worker execution fetch failed: {e}")
            return {"source": "worker.execution", "data": [], "error": str(e)}

    @staticmethod
    async def fetch_cost_spend(
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        resolution: ResolutionType,
    ) -> dict[str, Any]:
        """Fetch cost spend data from cost_records table."""
        try:
            time_trunc = "hour" if resolution == ResolutionType.HOUR else "day"
            driver = get_analytics_read_driver(session)
            data = await driver.fetch_cost_spend(tenant_id, from_ts, to_ts, time_trunc)
            return {"source": "cost_records", "data": data}
        except Exception as e:
            logger.warning(f"Cost spend fetch failed: {e}")
            return {"source": "cost_records", "data": [], "error": str(e)}

    @staticmethod
    async def fetch_cost_by_model(
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> dict[str, Any]:
        """Fetch cost breakdown by model from cost_records table."""
        try:
            driver = get_analytics_read_driver(session)
            data = await driver.fetch_cost_by_model(tenant_id, from_ts, to_ts)
            return {"source": "cost_records", "data": data}
        except Exception as e:
            logger.warning(f"Cost by model fetch failed: {e}")
            return {"source": "cost_records", "data": [], "error": str(e)}

    @staticmethod
    async def fetch_cost_by_feature(
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> dict[str, Any]:
        """Fetch cost breakdown by feature tag from cost_records table."""
        try:
            driver = get_analytics_read_driver(session)
            data = await driver.fetch_cost_by_feature(tenant_id, from_ts, to_ts)
            return {"source": "cost_records", "data": data}
        except Exception as e:
            logger.warning(f"Cost by feature fetch failed: {e}")
            return {"source": "cost_records", "data": [], "error": str(e)}


# =============================================================================
# Facade Class
# =============================================================================


class AnalyticsFacade:
    """
    Unified facade for Analytics domain operations.

    This class provides a single entry point for all analytics business logic.
    """

    def __init__(self) -> None:
        """Initialize facade."""
        pass

    async def get_usage_statistics(
        self,
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        *,
        resolution: ResolutionType = ResolutionType.DAY,
        scope: ScopeType = ScopeType.ORG,
    ) -> UsageStatisticsResult:
        """
        Get usage statistics for the specified time window.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            from_ts: Start of time window
            to_ts: End of time window
            resolution: Time resolution (hour or day)
            scope: Aggregation scope (org, project, env)

        Returns:
            UsageStatisticsResult with aggregated usage data
        """
        # Scope is declared for API contract, implementation pending
        _ = scope

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

        # Collect sources that returned data
        sources = []
        if cost_data.get("data"):
            sources.append("cost_records")
        if llm_data.get("data"):
            sources.append("llm.usage")
        if worker_data.get("data"):
            sources.append("worker.execution")
        if llm_data.get("data"):
            sources.append("gateway.metrics")

        # Time-align and merge data points
        merged_by_ts: dict[str, dict[str, int]] = {}

        # Process LLM data (primary for requests and tokens)
        for point in llm_data.get("data", []):
            ts = point.get("ts")
            if ts:
                if ts not in merged_by_ts:
                    merged_by_ts[ts] = {"requests": 0, "compute_units": 0, "tokens": 0}
                merged_by_ts[ts]["requests"] += point.get("requests", 0)
                merged_by_ts[ts]["tokens"] += point.get("tokens", 0)

        # Enrich with cost data
        for point in cost_data.get("data", []):
            ts = point.get("ts")
            if ts:
                if ts not in merged_by_ts:
                    merged_by_ts[ts] = {"requests": 0, "compute_units": 0, "tokens": 0}
                if point.get("tokens", 0) > merged_by_ts[ts]["tokens"]:
                    merged_by_ts[ts]["tokens"] = point.get("tokens", 0)

        # Enrich with worker execution
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
            ts_formatted = ts.split("T")[0] if resolution == ResolutionType.DAY else ts
            series.append(
                UsageDataPointResult(
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

        # Calculate freshness
        freshness_sec = self._calculate_freshness(series)

        return UsageStatisticsResult(
            window=TimeWindowResult(
                from_ts=from_ts,
                to_ts=to_ts,
                resolution=resolution.value,
            ),
            totals=UsageTotalsResult(
                requests=total_requests,
                compute_units=total_compute_units,
                tokens=total_tokens,
            ),
            series=series,
            signals=SignalSourceResult(
                sources=sources if sources else ["none"],
                freshness_sec=max(0, freshness_sec),
            ),
        )

    async def get_cost_statistics(
        self,
        session: AsyncSession,
        tenant_id: str,
        from_ts: datetime,
        to_ts: datetime,
        *,
        resolution: ResolutionType = ResolutionType.DAY,
        scope: ScopeType = ScopeType.ORG,
    ) -> CostStatisticsResult:
        """
        Get cost statistics for the specified time window.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            from_ts: Start of time window
            to_ts: End of time window
            resolution: Time resolution (hour or day)
            scope: Aggregation scope (org, project, env)

        Returns:
            CostStatisticsResult with aggregated cost data
        """
        # Scope is declared for API contract, implementation pending
        _ = scope

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
                    CostDataPointResult(
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

        # Build by-model breakdown
        by_model = []
        for item in model_data.get("data", []):
            pct = (item.get("spend_cents", 0) / total_spend_cents * 100) if total_spend_cents > 0 else 0
            by_model.append(
                CostByModelResult(
                    model=item.get("model", "unknown"),
                    spend_cents=item.get("spend_cents", 0),
                    requests=item.get("requests", 0),
                    input_tokens=item.get("input_tokens", 0),
                    output_tokens=item.get("output_tokens", 0),
                    pct_of_total=round(pct, 2),
                )
            )

        # Build by-feature breakdown
        by_feature = []
        for item in feature_data.get("data", []):
            pct = (item.get("spend_cents", 0) / total_spend_cents * 100) if total_spend_cents > 0 else 0
            by_feature.append(
                CostByFeatureResult(
                    feature_tag=item.get("feature_tag", "untagged"),
                    spend_cents=item.get("spend_cents", 0),
                    requests=item.get("requests", 0),
                    pct_of_total=round(pct, 2),
                )
            )

        # Calculate freshness
        freshness_sec = self._calculate_freshness_from_cost(series)

        return CostStatisticsResult(
            window=TimeWindowResult(
                from_ts=from_ts,
                to_ts=to_ts,
                resolution=resolution.value,
            ),
            totals=CostTotalsResult(
                spend_cents=total_spend_cents,
                spend_usd=total_spend_cents / 100.0,
                requests=total_requests,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
            ),
            series=series,
            by_model=by_model,
            by_feature=by_feature,
            signals=SignalSourceResult(
                sources=sources if sources else ["none"],
                freshness_sec=max(0, freshness_sec),
            ),
        )

    def get_status(self) -> AnalyticsStatusResult:
        """
        Get analytics domain capability status.

        Returns:
            AnalyticsStatusResult with available capabilities
        """
        return AnalyticsStatusResult(
            domain="analytics",
            subdomains=["statistics"],
            topics={
                "usage": TopicStatusResult(
                    read=True,
                    write=False,
                    signals_bound=3,
                ),
                "cost": TopicStatusResult(
                    read=True,
                    write=False,
                    signals_bound=1,
                ),
            },
        )

    def _calculate_freshness(self, series: list[UsageDataPointResult]) -> int:
        """Calculate data freshness in seconds."""
        if not series:
            return 0
        try:
            last_ts = series[-1].ts
            if "T" in last_ts:
                last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            else:
                last_dt = datetime.fromisoformat(last_ts + "T00:00:00+00:00")
            return int((datetime.now(timezone.utc) - last_dt).total_seconds())
        except Exception:
            return 0

    def _calculate_freshness_from_cost(self, series: list[CostDataPointResult]) -> int:
        """Calculate data freshness in seconds from cost series."""
        if not series:
            return 0
        try:
            last_ts = series[-1].ts
            if "T" in last_ts:
                last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            else:
                last_dt = datetime.fromisoformat(last_ts + "T00:00:00+00:00")
            return int((datetime.now(timezone.utc) - last_dt).total_seconds())
        except Exception:
            return 0


# =============================================================================
# Singleton Instance
# =============================================================================

_facade_instance: AnalyticsFacade | None = None


def get_analytics_facade() -> AnalyticsFacade:
    """Get the singleton AnalyticsFacade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = AnalyticsFacade()
    return _facade_instance
