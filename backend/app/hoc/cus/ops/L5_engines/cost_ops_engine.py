# capability_id: CAP-012
# Layer: L5 — Domain Engine
# AUDIENCE: FOUNDER
# Product: ops-console
# Temporal:
#   Trigger: api
#   Execution: async
# Data Access:
#   Reads: via L6 cost_read_driver
#   Writes: none (read-only)
# Role: Cost intelligence engine — business logic for founder cost visibility
# Callers: ops_handler.py (L4 handler)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# artifact_class: CODE

"""
Cost Ops Engine (L5)

Business logic for founder cost intelligence.
Delegates DB queries to L6 cost_read_driver, performs:
- Trend computation
- Budget projections
- Cost driver analysis
- Anomaly pattern detection

Operations:
- get_overview: Global cost overview with anomaly summary
- get_anomalies: Cross-tenant anomaly aggregation
- get_tenants: Per-tenant cost drilldown
- get_customer_drilldown: Deep-dive cost analysis for a single customer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol


class CostReadDriverPort(Protocol):
    async def fetch_global_spend_summary(self, today_start: datetime, month_start: datetime, week_ago: datetime) -> dict[str, int]: ...
    async def fetch_anomaly_summary(self, cutoff: datetime) -> dict[str, int]: ...
    async def fetch_largest_deviation(self) -> dict[str, Any] | None: ...
    async def fetch_last_snapshot_time(self) -> datetime | None: ...
    async def fetch_daily_cost_series(self, since: datetime) -> list[int]: ...
    async def fetch_anomalies(self, include_resolved: bool, cutoff: datetime, limit: int) -> list[dict[str, Any]]: ...
    async def fetch_tenant_cost_rollup(self, today_start: datetime, month_start: datetime, week_ago: datetime, day_ago: datetime, order_by: str, limit: int, offset: int) -> list[dict[str, Any]]: ...
    async def fetch_distinct_tenant_count(self) -> int: ...
    async def check_tenant_has_data(self, tenant_id: str) -> bool: ...
    async def fetch_tenant_name(self, tenant_id: str) -> str | None: ...
    async def fetch_tenant_spend_summary(self, tenant_id: str, today_start: datetime, month_start: datetime, week_ago: datetime, month_ago: datetime) -> dict[str, int]: ...
    async def fetch_tenant_baseline(self, tenant_id: str) -> float | None: ...
    async def fetch_tenant_budget(self, tenant_id: str) -> int | None: ...
    async def fetch_tenant_daily_breakdown(self, tenant_id: str, since: datetime) -> list[dict[str, Any]]: ...
    async def fetch_tenant_cost_by_feature(self, tenant_id: str, since: datetime) -> list[dict[str, Any]]: ...
    async def fetch_tenant_cost_by_user(self, tenant_id: str, since: datetime) -> list[dict[str, Any]]: ...
    async def fetch_tenant_anomalous_users(self, tenant_id: str) -> list[dict[str, Any]]: ...
    async def fetch_tenant_cost_by_model(self, tenant_id: str, since: datetime) -> list[dict[str, Any]]: ...
    async def fetch_tenant_anomaly_history(self, tenant_id: str) -> list[dict[str, Any]]: ...
    async def fetch_tenant_last_activity(self, tenant_id: str) -> datetime | None: ...


# =============================================================================
# Result Dataclasses
# =============================================================================


@dataclass
class CostOverviewResult:
    """Global cost overview."""

    spend_today_cents: int
    spend_mtd_cents: int
    spend_7d_cents: int
    tenants_with_anomalies: int
    total_anomalies_24h: int
    largest_deviation_tenant_id: str | None
    largest_deviation_pct: float | None
    largest_deviation_type: str | None
    last_snapshot_at: str | None
    snapshot_freshness_minutes: int
    snapshot_status: str
    trend_7d: str


@dataclass
class AnomalyItem:
    """Single anomaly item."""

    id: Any
    anomaly_type: str
    severity: str
    entity_type: str | None
    entity_id: str | None
    current_value_cents: float
    expected_value_cents: float
    deviation_pct: float
    threshold_pct: float
    affected_tenants: int
    is_systemic: bool
    message: str
    incident_id: Any
    action_taken: str | None
    resolved: bool
    detected_at: str
    snapshot_id: Any


@dataclass
class CostAnomalyListResult:
    """Anomaly list result."""

    anomalies: list[AnomalyItem]
    total: int
    tenants_affected: int
    systemic_count: int


@dataclass
class TenantCostItem:
    """Single tenant cost item."""

    tenant_id: str
    tenant_name: str
    spend_today_cents: int
    spend_mtd_cents: int
    spend_7d_cents: int
    deviation_from_baseline_pct: float | None
    baseline_7d_avg_cents: float | None
    budget_monthly_cents: int | None
    budget_used_pct: float | None
    has_anomaly: bool
    anomaly_count_24h: int
    trend: str
    last_activity: str | None


@dataclass
class CostTenantListResult:
    """Tenant list result."""

    tenants: list[TenantCostItem]
    total: int
    page: int
    page_size: int


@dataclass
class DailyBreakdownItem:
    """Daily cost breakdown item."""

    date: str
    spend_cents: int
    request_count: int
    avg_cost_per_request_cents: float


@dataclass
class FeatureCostItem:
    """Cost by feature item."""

    feature_tag: str
    spend_cents: int
    request_count: int
    pct_of_total: float


@dataclass
class UserCostItem:
    """Cost by user item."""

    user_id: str
    spend_cents: int
    request_count: int
    pct_of_total: float
    is_anomalous: bool


@dataclass
class ModelCostItem:
    """Cost by model item."""

    model: str
    spend_cents: int
    input_tokens: int
    output_tokens: int
    request_count: int
    pct_of_total: float


@dataclass
class AnomalyHistoryItem:
    """Anomaly history item."""

    id: Any
    anomaly_type: str
    severity: str
    detected_at: str
    resolved: bool
    deviation_pct: float
    derived_cause: str | None
    message: str


@dataclass
class CustomerDrilldownResult:
    """Customer cost drilldown result."""

    tenant_id: str
    tenant_name: str
    spend_today_cents: int
    spend_mtd_cents: int
    spend_7d_cents: int
    spend_30d_cents: int
    baseline_7d_avg_cents: float | None
    deviation_from_baseline_pct: float | None
    budget_monthly_cents: int | None
    budget_used_pct: float | None
    projected_month_end_cents: int | None
    days_until_budget_exhausted: int | None
    daily_breakdown: list[DailyBreakdownItem]
    by_feature: list[FeatureCostItem]
    by_user: list[UserCostItem]
    by_model: list[ModelCostItem]
    largest_driver_type: str
    largest_driver_name: str
    largest_driver_pct: float
    active_anomalies: int
    recent_anomalies: list[AnomalyHistoryItem]
    trend_7d: str
    trend_message: str
    last_activity: str | None
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =============================================================================
# Pure computation helpers
# =============================================================================


def _compute_snapshot_status(last_snapshot_at: datetime | None) -> tuple[int, str]:
    """Compute snapshot freshness status."""
    if not last_snapshot_at:
        return 9999, "missing"

    now = datetime.now(timezone.utc)
    delta = now - last_snapshot_at
    minutes = int(delta.total_seconds() / 60)

    if minutes < 60:
        return minutes, "fresh"
    elif minutes < 1440:
        return minutes, "stale"
    else:
        return minutes, "missing"


def _compute_trend(daily_costs: list[float]) -> str:
    """Compute trend from daily cost values."""
    if len(daily_costs) < 4:
        return "stable"

    mid = len(daily_costs) // 2
    first_half_avg = sum(daily_costs[:mid]) / mid if mid > 0 else 0
    second_half_avg = sum(daily_costs[mid:]) / (len(daily_costs) - mid)

    if first_half_avg == 0:
        return "stable"

    ratio = second_half_avg / first_half_avg
    if ratio > 1.2:
        return "increasing"
    elif ratio < 0.8:
        return "decreasing"
    return "stable"


# =============================================================================
# Engine
# =============================================================================


class CostOpsEngine:
    """
    L5 Engine for founder cost intelligence.

    All database access is via L6 CostReadDriver.
    This engine owns business logic only.
    """

    async def get_overview(self, driver: CostReadDriverPort) -> CostOverviewResult:
        """Get global cost overview with anomaly summary."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)

        spend = await driver.fetch_global_spend_summary(today_start, month_start, week_ago)
        anomaly = await driver.fetch_anomaly_summary(now - timedelta(hours=24))
        deviation = await driver.fetch_largest_deviation()
        last_snapshot_at = await driver.fetch_last_snapshot_time()
        daily_costs = await driver.fetch_daily_cost_series(week_ago)

        snapshot_minutes, snapshot_status = _compute_snapshot_status(last_snapshot_at)
        trend = _compute_trend(daily_costs)

        return CostOverviewResult(
            spend_today_cents=spend["today"],
            spend_mtd_cents=spend["mtd"],
            spend_7d_cents=spend["week"],
            tenants_with_anomalies=anomaly["tenants"],
            total_anomalies_24h=anomaly["total"],
            largest_deviation_tenant_id=deviation["tenant_id"] if deviation else None,
            largest_deviation_pct=deviation["deviation_pct"] if deviation else None,
            largest_deviation_type=deviation["anomaly_type"] if deviation else None,
            last_snapshot_at=last_snapshot_at.isoformat() if last_snapshot_at else None,
            snapshot_freshness_minutes=snapshot_minutes,
            snapshot_status=snapshot_status,
            trend_7d=trend,
        )

    async def get_anomalies(
        self,
        driver: CostReadDriverPort,
        *,
        include_resolved: bool = False,
        limit: int = 50,
    ) -> CostAnomalyListResult:
        """Get cross-tenant anomaly aggregation."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=7)

        rows = await driver.fetch_anomalies(include_resolved, cutoff, limit)

        # Count similar patterns across tenants
        pattern_counts: dict[str, set[str]] = {}
        for row in rows:
            key = f"{row['anomaly_type']}:{row['entity_type']}"
            if key not in pattern_counts:
                pattern_counts[key] = set()
            pattern_counts[key].add(row["tenant_id"])

        anomalies = []
        for row in rows:
            pattern_key = f"{row['anomaly_type']}:{row['entity_type']}"
            affected_count = len(pattern_counts.get(pattern_key, set()))

            anomalies.append(
                AnomalyItem(
                    id=row["id"],
                    anomaly_type=row["anomaly_type"],
                    severity=row["severity"] or "medium",
                    entity_type=row["entity_type"],
                    entity_id=row["entity_id"],
                    current_value_cents=float(row["current_value_cents"] or 0),
                    expected_value_cents=float(row["expected_value_cents"] or 0),
                    deviation_pct=float(row["deviation_pct"] or 0),
                    threshold_pct=float(row["threshold_pct"] or 0),
                    affected_tenants=affected_count,
                    is_systemic=affected_count > 3,
                    message=row["message"] or "",
                    incident_id=row["incident_id"],
                    action_taken=row["action_taken"],
                    resolved=row["resolved"] or False,
                    detected_at=row["detected_at"].isoformat() if row["detected_at"] else now.isoformat(),
                    snapshot_id=row["snapshot_id"],
                )
            )

        unique_tenants = len({row["tenant_id"] for row in rows})
        systemic_count = sum(1 for a in anomalies if a.is_systemic)

        return CostAnomalyListResult(
            anomalies=anomalies,
            total=len(anomalies),
            tenants_affected=unique_tenants,
            systemic_count=systemic_count,
        )

    async def get_tenants(
        self,
        driver: CostReadDriverPort,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "spend_today",
    ) -> CostTenantListResult:
        """Get per-tenant cost drilldown."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        day_ago = now - timedelta(hours=24)
        offset = (page - 1) * page_size

        sort_map = {
            "spend_today": "spend_today DESC",
            "spend_mtd": "spend_mtd DESC",
            "deviation": "deviation_pct DESC NULLS LAST",
            "anomaly_count": "anomaly_count DESC",
        }
        order_by = sort_map.get(sort_by, "spend_today DESC")

        rows = await driver.fetch_tenant_cost_rollup(
            today_start, month_start, week_ago, day_ago, order_by, page_size, offset
        )
        total = await driver.fetch_distinct_tenant_count()

        tenants = []
        for row in rows:
            deviation = row["deviation_pct"]
            if deviation is None:
                trend = "stable"
            elif deviation > 50:
                trend = "increasing"
            elif deviation < -30:
                trend = "decreasing"
            else:
                trend = "stable"

            tenants.append(
                TenantCostItem(
                    tenant_id=row["tenant_id"],
                    tenant_name=row["tenant_name"] or row["tenant_id"],
                    spend_today_cents=int(row["spend_today"] or 0),
                    spend_mtd_cents=int(row["spend_mtd"] or 0),
                    spend_7d_cents=int(row["spend_7d"] or 0),
                    deviation_from_baseline_pct=float(row["deviation_pct"]) if row["deviation_pct"] else None,
                    baseline_7d_avg_cents=float(row["baseline"]) if row["baseline"] else None,
                    budget_monthly_cents=int(row["budget"]) if row["budget"] else None,
                    budget_used_pct=float(row["budget_used_pct"]) if row["budget_used_pct"] else None,
                    has_anomaly=int(row["anomaly_count"] or 0) > 0,
                    anomaly_count_24h=int(row["anomaly_count"] or 0),
                    trend=trend,
                    last_activity=row["last_activity"].isoformat() if row["last_activity"] else None,
                )
            )

        return CostTenantListResult(
            tenants=tenants,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_customer_drilldown(
        self,
        driver: CostReadDriverPort,
        *,
        tenant_id: str,
    ) -> CustomerDrilldownResult | None:
        """Deep-dive cost analysis for a single customer."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Check tenant exists
        if not await driver.check_tenant_has_data(tenant_id):
            return None

        # Fetch all data
        tenant_name = await driver.fetch_tenant_name(tenant_id) or tenant_id
        spend = await driver.fetch_tenant_spend_summary(
            tenant_id, today_start, month_start, week_ago, month_ago
        )
        baseline_7d_avg = await driver.fetch_tenant_baseline(tenant_id)
        budget_monthly = await driver.fetch_tenant_budget(tenant_id)
        daily_rows = await driver.fetch_tenant_daily_breakdown(tenant_id, week_ago)
        feature_rows = await driver.fetch_tenant_cost_by_feature(tenant_id, week_ago)
        user_rows = await driver.fetch_tenant_cost_by_user(tenant_id, week_ago)
        anomalous_users = await driver.fetch_tenant_anomalous_users(tenant_id)
        model_rows = await driver.fetch_tenant_cost_by_model(tenant_id, week_ago)
        anomaly_rows = await driver.fetch_tenant_anomaly_history(tenant_id)
        last_activity = await driver.fetch_tenant_last_activity(tenant_id)

        spend_today = spend["today"]
        spend_mtd = spend["mtd"]
        spend_7d = spend["week"]
        spend_30d = spend["month"]

        # Compute deviation from baseline
        deviation_pct = None
        if baseline_7d_avg and baseline_7d_avg > 0:
            deviation_pct = ((spend_today - baseline_7d_avg) / baseline_7d_avg) * 100

        # Compute budget projections
        budget_used_pct = None
        projected_month_end = None
        days_until_exhausted = None
        if budget_monthly and budget_monthly > 0:
            budget_used_pct = (spend_mtd / budget_monthly) * 100
            days_in_month = 30
            day_of_month = now.day
            if day_of_month > 0:
                daily_avg = spend_mtd / day_of_month
                projected_month_end = int(daily_avg * days_in_month)
                remaining_budget = budget_monthly - spend_mtd
                if daily_avg > 0 and remaining_budget > 0:
                    days_until_exhausted = int(remaining_budget / daily_avg)

        # Build daily breakdown
        daily_breakdown = []
        for row in daily_rows:
            avg_cost = row["spend"] / row["requests"] if row["requests"] > 0 else 0
            daily_breakdown.append(
                DailyBreakdownItem(
                    date=row["date"].isoformat(),
                    spend_cents=row["spend"],
                    request_count=row["requests"],
                    avg_cost_per_request_cents=round(avg_cost, 2),
                )
            )

        # Build feature breakdown
        total_7d = spend_7d if spend_7d > 0 else 1
        by_feature = [
            FeatureCostItem(
                feature_tag=row["feature"],
                spend_cents=row["spend"],
                request_count=row["requests"],
                pct_of_total=round((row["spend"] / total_7d) * 100, 1),
            )
            for row in feature_rows
        ]

        # Build user breakdown
        by_user = [
            UserCostItem(
                user_id=row["user_id"],
                spend_cents=row["spend"],
                request_count=row["requests"],
                pct_of_total=round((row["spend"] / total_7d) * 100, 1),
                is_anomalous=row["user_id"] in anomalous_users,
            )
            for row in user_rows
        ]

        # Build model breakdown
        by_model = [
            ModelCostItem(
                model=row["model"],
                spend_cents=row["spend"],
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                request_count=row["requests"],
                pct_of_total=round((row["spend"] / total_7d) * 100, 1),
            )
            for row in model_rows
        ]

        # Determine largest driver
        largest_driver_type = "feature"
        largest_driver_name = "unknown"
        largest_driver_pct = 0.0
        feature_pct = by_feature[0].pct_of_total if by_feature else 0
        user_pct = by_user[0].pct_of_total if by_user else 0
        model_pct = by_model[0].pct_of_total if by_model else 0

        if by_feature and feature_pct >= user_pct and feature_pct >= model_pct:
            largest_driver_type = "feature"
            largest_driver_name = by_feature[0].feature_tag
            largest_driver_pct = feature_pct
        elif by_user and user_pct >= model_pct:
            largest_driver_type = "user"
            largest_driver_name = by_user[0].user_id
            largest_driver_pct = user_pct
        elif by_model:
            largest_driver_type = "model"
            largest_driver_name = by_model[0].model
            largest_driver_pct = model_pct

        # Build anomaly history
        active_anomalies = sum(1 for row in anomaly_rows if not row["resolved"])
        recent_anomalies = [
            AnomalyHistoryItem(
                id=row["id"],
                anomaly_type=row["anomaly_type"],
                severity=row["severity"] or "medium",
                detected_at=row["detected_at"].isoformat() if row["detected_at"] else now.isoformat(),
                resolved=row["resolved"] or False,
                deviation_pct=float(row["deviation_pct"]) if row["deviation_pct"] else 0.0,
                derived_cause=row["derived_cause"],
                message=row["message"] or "",
            )
            for row in anomaly_rows
        ]

        # Compute trend
        trend_7d = _compute_trend([d.spend_cents for d in reversed(daily_breakdown)])
        if trend_7d == "increasing":
            trend_message = (
                f"Cost is trending up - {deviation_pct:.0f}% above baseline"
                if deviation_pct
                else "Cost is trending up"
            )
        elif trend_7d == "decreasing":
            trend_message = "Cost is trending down"
        else:
            trend_message = "Cost is within normal range for this customer"

        return CustomerDrilldownResult(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            spend_today_cents=spend_today,
            spend_mtd_cents=spend_mtd,
            spend_7d_cents=spend_7d,
            spend_30d_cents=spend_30d,
            baseline_7d_avg_cents=baseline_7d_avg,
            deviation_from_baseline_pct=round(deviation_pct, 1) if deviation_pct else None,
            budget_monthly_cents=budget_monthly,
            budget_used_pct=round(budget_used_pct, 1) if budget_used_pct else None,
            projected_month_end_cents=projected_month_end,
            days_until_budget_exhausted=days_until_exhausted,
            daily_breakdown=daily_breakdown,
            by_feature=by_feature,
            by_user=by_user,
            by_model=by_model,
            largest_driver_type=largest_driver_type,
            largest_driver_name=largest_driver_name,
            largest_driver_pct=largest_driver_pct,
            active_anomalies=active_anomalies,
            recent_anomalies=recent_anomalies,
            trend_7d=trend_7d,
            trend_message=trend_message,
            last_activity=last_activity.isoformat() if last_activity else None,
        )


# Singleton
_engine: CostOpsEngine | None = None


def get_cost_ops_engine() -> CostOpsEngine:
    """Get the CostOpsEngine singleton."""
    global _engine
    if _engine is None:
        _engine = CostOpsEngine()
    return _engine


# Backward compatibility alias (legacy name from app.services.ops)
get_ops_facade = get_cost_ops_engine
