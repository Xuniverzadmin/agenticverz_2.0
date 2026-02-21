# capability_id: CAP-012
# Layer: L2 -- Product APIs
# AUDIENCE: CUSTOMER
# Product: guard-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Guard Console cost visibility endpoints (customer transparency)
# Callers: Guard Console UI
# Allowed Imports: L3, L4, L5, L6
# Forbidden Imports: L1

"""Guard Console Cost Visibility API - Customer Cost Transparency

M29 Category 4: Cost Intelligence Completion

This router provides /guard/costs/* endpoints for the Customer Console.
Customers see their own cost data with calm vocabulary.

THE INVARIANT: All values derive from complete snapshots, never live data.
Customer sees ONLY their own tenant data - no cross-tenant leakage.

Endpoints:
- GET  /guard/costs/summary    - Cost summary with trend and projection
- GET  /guard/costs/explained  - Why costs are what they are
- GET  /guard/costs/incidents  - Cost-related incidents

CRITICAL: Uses FROZEN DTOs from app.contracts.guard.
NEVER expose founder-only fields (affected_tenants, churn_risk, etc.).

REFACTORED: All session.execute() calls moved to L6 driver via L4 handler.
L2 now uses registry dispatch for all DB operations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

# Category 2 Auth: Console authentication (aud=console, org_id required)
from app.auth.console_auth import CustomerToken, verify_console_token

# Category 3 Frozen Contracts
from app.contracts.guard import (
    CostBreakdownItemDTO,
    CustomerCostExplainedDTO,
    CustomerCostIncidentDTO,
    CustomerCostIncidentListDTO,
    CustomerCostSummaryDTO,
)

# L4 registry for dispatch (L2 must not import sqlalchemy/sqlmodel/app.db directly)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_operation_registry,
    get_sync_session_dep,
    OperationContext,
)

logger = logging.getLogger("nova.api.cost_guard")

router = APIRouter(
    prefix="/guard/costs",
    tags=["Guard Cost Visibility"],
    dependencies=[Depends(verify_console_token)],  # Category 2: Console auth (aud=console)
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _map_trend(deviation_pct: Optional[float]) -> tuple[Literal["normal", "rising", "spike"], str]:
    """Map deviation to customer-friendly trend."""
    if deviation_pct is None:
        return "normal", "Spending is within normal range"

    if deviation_pct > 200:
        return "spike", f"Spending is {deviation_pct:.0f}% above your usual level"
    elif deviation_pct > 50:
        return "rising", f"Spending has increased {deviation_pct:.0f}% from baseline"
    elif deviation_pct < -30:
        return "normal", f"Spending is {abs(deviation_pct):.0f}% below your usual level"
    else:
        return "normal", "Spending is within normal range"


def _map_severity_to_status(severity: str) -> Literal["protected", "attention_needed", "resolved"]:
    """Map internal severity to calm vocabulary."""
    if severity in ("critical", "high"):
        return "protected"  # We blocked it, you're safe
    elif severity == "medium":
        return "attention_needed"
    else:
        return "resolved"


def _generate_summary(
    by_feature: List[CostBreakdownItemDTO],
    by_model: List[CostBreakdownItemDTO],
    total_spend: int,
) -> str:
    """Generate a one-sentence summary of cost drivers."""
    if total_spend == 0:
        return "No spending recorded for this period"

    top_model = by_model[0] if by_model else None
    top_feature = by_feature[0] if by_feature else None

    if top_model and top_feature:
        return (
            f"{top_model.pct_of_total:.0f}% of your spend is from "
            f"{top_model.display_name or top_model.name} usage in "
            f"{top_feature.display_name or top_feature.name}"
        )
    elif top_model:
        return f"Most of your spend ({top_model.pct_of_total:.0f}%) is from {top_model.display_name or top_model.name}"
    elif top_feature:
        return f"Most of your spend ({top_feature.pct_of_total:.0f}%) is from {top_feature.display_name or top_feature.name}"
    else:
        return f"Your total spend for this period is ${total_spend / 100:.2f}"


async def _dispatch(session, tenant_id: str, method: str, **params):
    """Dispatch to L4 registry for cost_guard operations."""
    registry = get_operation_registry()
    ctx = OperationContext(
        session=session,
        tenant_id=tenant_id,
        params={"method": method, **params},
    )
    result = await registry.execute("incidents.cost_guard", ctx)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return result.data


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/summary", response_model=CustomerCostSummaryDTO)
async def get_cost_summary(
    tenant_id: str = Query(..., description="Your tenant ID"),
    token: CustomerToken = Depends(verify_console_token),
    session=Depends(get_sync_session_dep),
) -> CustomerCostSummaryDTO:
    """
    GET /guard/costs/summary

    Customer cost summary with trend and projection.
    Uses calm vocabulary: normal, rising, spike (not critical/high/medium).

    Shows:
    - Today spend, MTD spend, 7d spend
    - Budget usage (if configured)
    - Projected month-end
    - Trend with human-readable message
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    # Get spend totals via L4 dispatch
    spend_data = await _dispatch(
        session,
        tenant_id,
        "get_spend_totals",
        today_start=today_start,
        month_start=month_start,
        week_ago=week_ago,
    )
    spend_today = spend_data["today"]
    spend_mtd = spend_data["mtd"]
    spend_7d = spend_data["week"]

    # Get budget via L4 dispatch
    budget_data = await _dispatch(session, tenant_id, "get_budget")
    budget_daily = budget_data["daily_limit_cents"]
    budget_monthly = budget_data["monthly_limit_cents"]

    # Calculate budget percentages
    budget_used_daily = (spend_today / budget_daily * 100) if budget_daily else None
    budget_used_monthly = (spend_mtd / budget_monthly * 100) if budget_monthly else None

    # Get baseline for trend calculation via L4 dispatch
    baseline_data = await _dispatch(session, tenant_id, "get_baseline")
    baseline = baseline_data["baseline"]
    deviation = ((spend_today - baseline) / baseline * 100) if baseline and baseline > 0 else None

    # Calculate projection
    days_in_month = 30  # Approximate
    days_elapsed = (now - month_start).days + 1
    daily_avg = spend_mtd / days_elapsed if days_elapsed > 0 else 0
    projected_month_end = int(daily_avg * days_in_month)

    # Days until budget exhausted
    days_until_exhausted = None
    if budget_monthly and daily_avg > 0:
        remaining = budget_monthly - spend_mtd
        if remaining > 0:
            days_until_exhausted = int(remaining / daily_avg)
        else:
            days_until_exhausted = 0

    # Map to customer-friendly trend
    trend, trend_message = _map_trend(deviation)

    # Get last snapshot time via L4 dispatch
    snapshot_data = await _dispatch(session, tenant_id, "get_last_snapshot")
    last_updated = snapshot_data["completed_at"] if snapshot_data["completed_at"] else now

    return CustomerCostSummaryDTO(
        spend_today_cents=spend_today,
        spend_mtd_cents=spend_mtd,
        spend_7d_cents=spend_7d,
        budget_daily_cents=budget_daily,
        budget_monthly_cents=budget_monthly,
        budget_used_daily_pct=budget_used_daily,
        budget_used_monthly_pct=budget_used_monthly,
        projected_month_end_cents=projected_month_end,
        days_until_budget_exhausted=days_until_exhausted,
        trend=trend,
        trend_message=trend_message,
        last_updated=last_updated.isoformat() if isinstance(last_updated, datetime) else last_updated,
    )


@router.get("/explained", response_model=CustomerCostExplainedDTO)
async def get_cost_explained(
    tenant_id: str = Query(..., description="Your tenant ID"),
    period: Literal["today", "7d", "30d"] = Query("7d"),
    token: CustomerToken = Depends(verify_console_token),
    session=Depends(get_sync_session_dep),
) -> CustomerCostExplainedDTO:
    """
    GET /guard/costs/explained

    Explains WHY costs are what they are.
    Breaks down by feature, model, and user.

    Does NOT expose:
    - churn_risk_score (founder only)
    - affected_tenants (founder only)
    - stickiness_delta (founder only)
    """
    now = datetime.now(timezone.utc)

    # Determine period
    if period == "today":
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "7d":
        period_start = now - timedelta(days=7)
    else:  # 30d
        period_start = now - timedelta(days=30)

    # Get total spend via L4 dispatch
    total_data = await _dispatch(
        session,
        tenant_id,
        "get_total_spend",
        period_start=period_start,
    )
    total_spend = total_data["total"]

    # Get baselines for trend via L4 dispatch
    baselines_data = await _dispatch(session, tenant_id, "get_baselines")
    baselines = baselines_data["baselines"]

    # Get by feature via L4 dispatch
    feature_data = await _dispatch(
        session,
        tenant_id,
        "get_spend_by_feature",
        period_start=period_start,
        limit=10,
    )

    by_feature = []
    for row in feature_data["rows"]:
        pct = (row["spend_cents"] / total_spend * 100) if total_spend > 0 else 0
        baseline = baselines.get(row["name"])
        trend = "normal"
        if baseline and baseline > 0:
            deviation = (row["spend_cents"] - baseline) / baseline * 100
            if deviation > 200:
                trend = "spike"
            elif deviation > 50:
                trend = "rising"

        by_feature.append(
            CostBreakdownItemDTO(
                name=row["name"],
                display_name=row["display_name"],
                spend_cents=row["spend_cents"],
                request_count=row["request_count"],
                pct_of_total=round(pct, 1),
                trend=trend,
            )
        )

    # Get by model via L4 dispatch
    model_data = await _dispatch(
        session,
        tenant_id,
        "get_spend_by_model",
        period_start=period_start,
        limit=10,
    )

    by_model = []
    for row in model_data["rows"]:
        pct = (row["spend_cents"] / total_spend * 100) if total_spend > 0 else 0
        # Simple model display name mapping
        display = row["name"].replace("claude-", "Claude ").replace("-", " ").title() if row["name"] else None

        by_model.append(
            CostBreakdownItemDTO(
                name=row["name"],
                display_name=display,
                spend_cents=row["spend_cents"],
                request_count=row["request_count"],
                pct_of_total=round(pct, 1),
                trend="normal",  # Model trend is usually stable
            )
        )

    # Get by user via L4 dispatch
    user_data = await _dispatch(
        session,
        tenant_id,
        "get_spend_by_user",
        period_start=period_start,
        limit=10,
    )

    by_user = []
    for row in user_data["rows"]:
        pct = (row["spend_cents"] / total_spend * 100) if total_spend > 0 else 0
        baseline = baselines.get(f"user:{row['name']}")
        trend = "normal"
        if baseline and baseline > 0:
            deviation = (row["spend_cents"] - baseline) / baseline * 100
            if deviation > 200:
                trend = "spike"
            elif deviation > 50:
                trend = "rising"

        by_user.append(
            CostBreakdownItemDTO(
                name=row["name"],
                display_name=None,
                spend_cents=row["spend_cents"],
                request_count=row["request_count"],
                pct_of_total=round(pct, 1),
                trend=trend,
            )
        )

    # Determine largest driver
    all_drivers = [
        ("feature", by_feature[0].name if by_feature else "", by_feature[0].pct_of_total if by_feature else 0),
        ("model", by_model[0].name if by_model else "", by_model[0].pct_of_total if by_model else 0),
        ("user", by_user[0].name if by_user else "", by_user[0].pct_of_total if by_user else 0),
    ]
    largest = max(all_drivers, key=lambda x: x[2])

    summary = _generate_summary(by_feature, by_model, total_spend)

    return CustomerCostExplainedDTO(
        period=period,
        period_start=period_start.isoformat(),
        period_end=now.isoformat(),
        total_spend_cents=total_spend,
        by_feature=by_feature,
        by_model=by_model,
        by_user=by_user,
        largest_driver_type=largest[0],
        largest_driver_name=largest[1],
        largest_driver_pct=largest[2],
        summary=summary,
    )


@router.get("/incidents", response_model=CustomerCostIncidentListDTO)
async def get_cost_incidents(
    tenant_id: str = Query(..., description="Your tenant ID"),
    include_resolved: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    token: CustomerToken = Depends(verify_console_token),
    session=Depends(get_sync_session_dep),
) -> CustomerCostIncidentListDTO:
    """
    GET /guard/costs/incidents

    Cost-related incidents visible to customer.
    Uses calm vocabulary (protected, attention_needed).
    Does NOT expose severity levels directly.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    # Get cost anomalies via L4 dispatch
    anomaly_data = await _dispatch(
        session,
        tenant_id,
        "get_cost_anomalies",
        cutoff=cutoff,
        include_resolved=include_resolved,
        limit=limit,
    )

    result = anomaly_data["anomalies"]
    has_more = anomaly_data["has_more"]

    # Map to customer-friendly DTOs
    incidents = []
    for row in result:
        # Map anomaly_type to trigger_type
        anomaly_type = row["anomaly_type"]
        if "budget" in anomaly_type.lower():
            if "exceeded" in anomaly_type.lower():
                trigger_type = "budget_exceeded"
            else:
                trigger_type = "budget_warning"
        else:
            trigger_type = "cost_spike"

        # Calculate cost avoided (difference between current and threshold)
        current = float(row["current_value_cents"] or 0)
        threshold = float(row["threshold_pct"] or 0)
        cost_avoided = max(0, int(current - threshold))

        # Map severity to calm status
        severity = row["severity"] or "medium"
        is_resolved = row["resolved"] or False

        if is_resolved:
            status = "resolved"
        else:
            status = _map_severity_to_status(severity)

        # Generate customer-friendly title
        if trigger_type == "cost_spike":
            title = "Unusual spending detected"
        elif trigger_type == "budget_warning":
            title = "Approaching budget limit"
        else:
            title = "Budget limit reached"

        # Generate recommendation
        if trigger_type == "cost_spike":
            recommendation = "Review your usage in Cost Explained to see what's driving spend"
        elif trigger_type == "budget_warning":
            recommendation = "Consider increasing your budget or reducing usage"
        else:
            recommendation = "Increase your budget or pause operations to resume spending"

        detected_at = row["detected_at"]
        resolved_at = row["resolved_at"]

        incidents.append(
            CustomerCostIncidentDTO(
                id=f"inc_{row['id']}",
                title=title,
                status=status,
                trigger_type=trigger_type,
                cost_at_trigger_cents=int(current),
                cost_avoided_cents=cost_avoided,
                threshold_cents=int(threshold) if threshold else None,
                action_taken=row["action_taken"] or "Alerted you about this cost event",
                recommendation=recommendation,
                detected_at=detected_at.isoformat() if isinstance(detected_at, datetime) else (detected_at or now.isoformat()),
                resolved_at=resolved_at.isoformat() if isinstance(resolved_at, datetime) else resolved_at,
            )
        )

    return CustomerCostIncidentListDTO(
        incidents=incidents,
        total=len(incidents),
        has_more=has_more,
    )
