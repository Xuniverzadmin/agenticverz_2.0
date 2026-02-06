# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L4 handler/bridge)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via L6 cost_intelligence_sync_driver
#   Writes: via analytics L6 cost_write_driver (through analytics_bridge)
# Role: Business logic for cost intelligence operations (dashboard, breakdowns, projections)
# Callers: cost_intelligence.py (L2 API) via logs_bridge
# Allowed Imports: L5, L6 (same domain drivers)
# Forbidden Imports: L1, L2, L3, L4
# Reference: PIN-470, L2 first-principles purity migration
# artifact_class: CODE

"""
Cost Intelligence Engine (L5)

Business logic for cost intelligence operations.

Responsibilities:
- Orchestrates L6 driver calls
- Applies business logic (anomaly thresholds, trend analysis)
- Computes derived metrics (percentages, projections)
- NO direct database access (delegates to L6)

Operations:
- Get cost summary with budget calculations
- Get cost breakdowns with percentages
- Get anomalies
- Get cost projections with trend analysis
- Get current spend for budgets
"""

from datetime import datetime, timedelta
from typing import Any, List, Optional

from app.hoc.cus.logs.L6_drivers.cost_intelligence_sync_driver import (
    CostIntelligenceSyncDriver,
)
from app.hoc.cus.hoc_spine.services.time import utc_now


class CostIntelligenceEngine:
    """
    L5 engine for cost intelligence operations.

    Contains business logic; delegates DB access to L6 driver.
    """

    def __init__(self, driver: CostIntelligenceSyncDriver):
        self._driver = driver

    # =========================================================================
    # Feature Tag Operations
    # =========================================================================

    def check_feature_tag_exists(self, tenant_id: str, tag: str) -> bool:
        """Check if a feature tag already exists for this tenant."""
        return self._driver.check_feature_tag_exists(tenant_id, tag)

    def list_feature_tags(
        self,
        tenant_id: str,
        include_inactive: bool = False,
    ) -> List[dict[str, Any]]:
        """List all feature tags for the tenant."""
        return self._driver.fetch_feature_tags(tenant_id, include_inactive)

    def get_feature_tag(self, tenant_id: str, tag: str) -> Optional[dict[str, Any]]:
        """Get a specific feature tag by tag name."""
        return self._driver.fetch_feature_tag_by_tag(tenant_id, tag)

    def get_active_feature_tag(self, tenant_id: str, tag: str) -> Optional[dict[str, Any]]:
        """Get an active feature tag for validation."""
        return self._driver.fetch_active_feature_tag(tenant_id, tag)

    def update_feature_tag(
        self,
        tenant_id: str,
        tag: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        budget_cents: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[dict[str, Any]]:
        """Update a feature tag."""
        return self._driver.update_feature_tag(
            tenant_id=tenant_id,
            tag=tag,
            display_name=display_name,
            description=description,
            budget_cents=budget_cents,
            is_active=is_active,
        )

    # =========================================================================
    # Cost Summary
    # =========================================================================

    def get_cost_summary(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime,
        days: int,
    ) -> dict[str, Any]:
        """
        Get cost summary for a period with budget calculations.

        Business logic:
        - Calculate budget usage percentage
        - Calculate days remaining at current rate
        - Build provenance metadata
        """
        # Fetch raw data from L6
        raw_summary = self._driver.fetch_cost_summary(tenant_id, period_start, period_end)
        budget = self._driver.fetch_tenant_budget(tenant_id)

        total_cost = raw_summary["total_cost"]

        # Business logic: Calculate budget metrics
        budget_daily = budget["daily_limit_cents"] if budget else None
        budget_monthly = budget["monthly_limit_cents"] if budget else None
        budget_cents = budget_daily * days if budget_daily else None
        budget_used_pct = (total_cost / budget_cents * 100) if budget_cents and budget_cents > 0 else None

        # Calculate days remaining at current rate
        daily_avg = total_cost / days if days > 0 else 0
        days_remaining = None
        if budget_monthly and daily_avg > 0:
            remaining = budget_monthly - total_cost
            days_remaining = remaining / daily_avg if remaining > 0 else 0

        # Build period description for provenance
        if days == 1:
            period_desc = "Last 24 hours"
        elif days == 7:
            period_desc = "Last 7 days"
        else:
            period_desc = f"Last {days} days"

        return {
            "tenant_id": tenant_id,
            "period_start": period_start,
            "period_end": period_end,
            "total_cost_cents": total_cost,
            "total_input_tokens": raw_summary["total_input"],
            "total_output_tokens": raw_summary["total_output"],
            "request_count": raw_summary["request_count"],
            "budget_cents": budget_cents,
            "budget_used_pct": budget_used_pct,
            "days_remaining_at_current_rate": days_remaining,
            "provenance": {
                "aggregation": "sum",
                "data_source": "cost_records",
                "computed_at": utc_now(),
                "period_description": period_desc,
            },
        }

    # =========================================================================
    # Cost Breakdowns
    # =========================================================================

    def get_total_cost(self, tenant_id: str, period_start: datetime) -> float:
        """Get total cost for a period (for percentage calculations)."""
        return self._driver.fetch_total_cost(tenant_id, period_start)

    def get_costs_by_feature(
        self,
        tenant_id: str,
        period_start: datetime,
        total_cost: float,
    ) -> List[dict[str, Any]]:
        """
        Get costs grouped by feature tag with percentage calculations.

        Business logic: Calculate pct_of_total and budget_used_pct
        """
        raw_data = self._driver.fetch_costs_by_feature(tenant_id, period_start)

        return [
            {
                "feature_tag": row["feature_tag"],
                "display_name": row["display_name"],
                "total_cost_cents": row["total_cost"],
                "request_count": row["request_count"],
                "pct_of_total": (row["total_cost"] / total_cost * 100) if total_cost > 0 else 0,
                "budget_cents": row["budget_cents"],
                "budget_used_pct": (
                    (row["total_cost"] / row["budget_cents"] * 100)
                    if row["budget_cents"] and row["budget_cents"] > 0
                    else None
                ),
            }
            for row in raw_data
        ]

    def get_costs_by_user(
        self,
        tenant_id: str,
        period_start: datetime,
        total_cost: float,
    ) -> List[dict[str, Any]]:
        """
        Get costs grouped by user with anomaly detection.

        Business logic: Detect anomalies (spending > 2x average)
        """
        raw_data = self._driver.fetch_costs_by_user(tenant_id, period_start)

        if not raw_data:
            return []

        # Business logic: Calculate average for anomaly detection
        avg_cost = sum(row["total_cost"] for row in raw_data) / len(raw_data)

        return [
            {
                "user_id": row["user_id"],
                "total_cost_cents": row["total_cost"],
                "request_count": row["request_count"],
                "pct_of_total": (row["total_cost"] / total_cost * 100) if total_cost > 0 else 0,
                "is_anomaly": row["total_cost"] > avg_cost * 2,
                "anomaly_message": (
                    f"Spending {row['total_cost'] / avg_cost:.1f}x average"
                    if row["total_cost"] > avg_cost * 2
                    else None
                ),
            }
            for row in raw_data
        ]

    def get_costs_by_model(
        self,
        tenant_id: str,
        period_start: datetime,
        total_cost: float,
    ) -> List[dict[str, Any]]:
        """
        Get costs grouped by model with percentage calculations.

        Business logic: Calculate pct_of_total
        """
        raw_data = self._driver.fetch_costs_by_model(tenant_id, period_start)

        return [
            {
                "model": row["model"],
                "total_cost_cents": row["total_cost"],
                "total_input_tokens": row["total_input"],
                "total_output_tokens": row["total_output"],
                "request_count": row["request_count"],
                "pct_of_total": (row["total_cost"] / total_cost * 100) if total_cost > 0 else 0,
            }
            for row in raw_data
        ]

    # =========================================================================
    # Anomalies
    # =========================================================================

    def get_recent_anomalies(
        self,
        tenant_id: str,
        days: int = 7,
        include_resolved: bool = False,
    ) -> List[dict[str, Any]]:
        """Get recent cost anomalies."""
        cutoff = utc_now() - timedelta(days=days)
        return self._driver.fetch_recent_anomalies(tenant_id, cutoff, include_resolved)

    # =========================================================================
    # Projections
    # =========================================================================

    def get_cost_projection(
        self,
        tenant_id: str,
        lookback_days: int = 7,
        forecast_days: int = 7,
    ) -> dict[str, Any]:
        """
        Calculate cost projection based on historical trend.

        Business logic:
        - Calculate daily average
        - Detect trend (increasing/stable/decreasing)
        - Project future costs
        - Calculate budget exhaustion
        """
        lookback_start = utc_now() - timedelta(days=lookback_days)
        daily_costs_data = self._driver.fetch_daily_costs(tenant_id, lookback_start)

        if not daily_costs_data:
            return {
                "tenant_id": tenant_id,
                "lookback_days": lookback_days,
                "forecast_days": forecast_days,
                "current_daily_avg_cents": 0,
                "projected_total_cents": 0,
                "monthly_projection_cents": 0,
                "budget_cents": None,
                "days_until_budget_exhausted": None,
                "trend": "stable",
            }

        daily_costs = [row["daily_cost"] for row in daily_costs_data]
        current_daily_avg = sum(daily_costs) / len(daily_costs)

        # Business logic: Simple trend detection (compare first half to second half)
        if len(daily_costs) >= 4:
            mid = len(daily_costs) // 2
            first_half_avg = sum(daily_costs[:mid]) / mid
            second_half_avg = sum(daily_costs[mid:]) / (len(daily_costs) - mid)

            if second_half_avg > first_half_avg * 1.2:
                trend = "increasing"
            elif second_half_avg < first_half_avg * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        projected_total = current_daily_avg * forecast_days
        monthly_projection = current_daily_avg * 30

        # Get budget for exhaustion calculation
        budget = self._driver.fetch_tenant_budget(tenant_id)

        days_until_exhausted = None
        budget_cents = None
        budget_monthly = budget["monthly_limit_cents"] if budget else None
        if budget_monthly and current_daily_avg > 0:
            budget_cents = budget_monthly
            # Get current month spend
            month_start = utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_spend = self._driver.fetch_month_spend(tenant_id, month_start)

            remaining = budget_monthly - month_spend
            days_until_exhausted = remaining / current_daily_avg if remaining > 0 else 0

        return {
            "tenant_id": tenant_id,
            "lookback_days": lookback_days,
            "forecast_days": forecast_days,
            "current_daily_avg_cents": current_daily_avg,
            "projected_total_cents": projected_total,
            "monthly_projection_cents": monthly_projection,
            "budget_cents": budget_cents,
            "days_until_budget_exhausted": days_until_exhausted,
            "trend": trend,
        }

    # =========================================================================
    # Budget Operations
    # =========================================================================

    def list_budgets(self, tenant_id: str) -> List[dict[str, Any]]:
        """List all active budgets for the tenant."""
        return self._driver.fetch_budgets(tenant_id)

    def get_budget_by_type(
        self,
        tenant_id: str,
        budget_type: str,
        entity_id: Optional[str],
    ) -> Optional[dict[str, Any]]:
        """Get a specific budget by type and entity."""
        return self._driver.fetch_budget_by_type(tenant_id, budget_type, entity_id)

    def create_budget(
        self,
        tenant_id: str,
        budget_type: str,
        entity_id: Optional[str],
        daily_limit_cents: Optional[int],
        monthly_limit_cents: Optional[int],
        warn_threshold_pct: int,
        hard_limit_enabled: bool,
    ) -> dict[str, Any]:
        """Create a new budget."""
        return self._driver.create_budget(
            tenant_id=tenant_id,
            budget_type=budget_type,
            entity_id=entity_id,
            daily_limit_cents=daily_limit_cents,
            monthly_limit_cents=monthly_limit_cents,
            warn_threshold_pct=warn_threshold_pct,
            hard_limit_enabled=hard_limit_enabled,
        )

    def update_budget(
        self,
        budget_id: str,
        daily_limit_cents: Optional[int],
        monthly_limit_cents: Optional[int],
        warn_threshold_pct: int,
        hard_limit_enabled: bool,
    ) -> dict[str, Any]:
        """Update an existing budget."""
        return self._driver.update_budget(
            budget_id=budget_id,
            daily_limit_cents=daily_limit_cents,
            monthly_limit_cents=monthly_limit_cents,
            warn_threshold_pct=warn_threshold_pct,
            hard_limit_enabled=hard_limit_enabled,
        )

    def get_current_spend(
        self,
        tenant_id: str,
        budget_type: str,
        entity_id: Optional[str],
    ) -> dict[str, float]:
        """Get current daily and monthly spend for a budget entity."""
        today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self._driver.fetch_current_spend(
            tenant_id, budget_type, entity_id, today_start, month_start
        )


def get_cost_intelligence_engine(driver: CostIntelligenceSyncDriver) -> CostIntelligenceEngine:
    """Get cost intelligence engine instance for the given (session-bound) driver."""
    return CostIntelligenceEngine(driver)


__all__ = [
    "CostIntelligenceEngine",
    "get_cost_intelligence_engine",
]
