# Layer: L2 — Product APIs
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
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlmodel import Session

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
from app.db import get_session

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


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/summary", response_model=CustomerCostSummaryDTO)
async def get_cost_summary(
    tenant_id: str = Query(..., description="Your tenant ID"),
    token: CustomerToken = Depends(verify_console_token),
    session: Session = Depends(get_session),
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

    # Get spend totals
    spend_result = session.execute(
        text(
            """
            SELECT
                COALESCE(SUM(CASE WHEN created_at >= :today THEN cost_cents ELSE 0 END), 0) as today,
                COALESCE(SUM(CASE WHEN created_at >= :month THEN cost_cents ELSE 0 END), 0) as mtd,
                COALESCE(SUM(CASE WHEN created_at >= :week THEN cost_cents ELSE 0 END), 0) as week
            FROM cost_records
            WHERE tenant_id = :tenant_id
        """
        ),
        {"tenant_id": tenant_id, "today": today_start, "month": month_start, "week": week_ago},
    ).first()

    spend_today = int(spend_result[0]) if spend_result else 0
    spend_mtd = int(spend_result[1]) if spend_result else 0
    spend_7d = int(spend_result[2]) if spend_result else 0

    # Get budget
    budget_result = session.execute(
        text(
            """
            SELECT daily_limit_cents, monthly_limit_cents
            FROM cost_budgets
            WHERE tenant_id = :tenant_id AND budget_type = 'tenant' AND is_active = true
        """
        ),
        {"tenant_id": tenant_id},
    ).first()

    budget_daily = int(budget_result[0]) if budget_result and budget_result[0] else None
    budget_monthly = int(budget_result[1]) if budget_result and budget_result[1] else None

    # Calculate budget percentages
    budget_used_daily = (spend_today / budget_daily * 100) if budget_daily else None
    budget_used_monthly = (spend_mtd / budget_monthly * 100) if budget_monthly else None

    # Get baseline for trend calculation
    baseline_result = session.execute(
        text(
            """
            SELECT avg_daily_cost_cents
            FROM cost_snapshot_baselines
            WHERE tenant_id = :tenant_id AND entity_type = 'tenant' AND is_current = true
        """
        ),
        {"tenant_id": tenant_id},
    ).first()

    baseline = float(baseline_result[0]) if baseline_result and baseline_result[0] else None
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

    # Get last snapshot time
    snapshot_result = session.execute(
        text(
            """
            SELECT completed_at
            FROM cost_snapshots
            WHERE tenant_id = :tenant_id AND status = 'complete'
            ORDER BY completed_at DESC
            LIMIT 1
        """
        ),
        {"tenant_id": tenant_id},
    ).first()

    last_updated = snapshot_result[0] if snapshot_result else now

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
    session: Session = Depends(get_session),
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

    # Get total spend
    total_result = session.execute(
        text(
            """
            SELECT COALESCE(SUM(cost_cents), 0)
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :start
        """
        ),
        {"tenant_id": tenant_id, "start": period_start},
    ).first()

    total_spend = int(total_result[0]) if total_result else 0

    # Get baseline for trend
    baseline_result = session.execute(
        text(
            """
            SELECT entity_id, avg_daily_cost_cents
            FROM cost_snapshot_baselines
            WHERE tenant_id = :tenant_id AND is_current = true
        """
        ),
        {"tenant_id": tenant_id},
    ).all()

    baselines = {row[0]: float(row[1]) for row in baseline_result if row[0]}

    # Get by feature
    feature_result = session.execute(
        text(
            """
            SELECT
                COALESCE(cr.feature_tag, 'unclassified') as feature,
                ft.display_name,
                COALESCE(SUM(cr.cost_cents), 0) as spend,
                COUNT(*) as requests
            FROM cost_records cr
            LEFT JOIN feature_tags ft ON cr.feature_tag = ft.tag AND cr.tenant_id = ft.tenant_id
            WHERE cr.tenant_id = :tenant_id AND cr.created_at >= :start
            GROUP BY cr.feature_tag, ft.display_name
            ORDER BY spend DESC
            LIMIT 10
        """
        ),
        {"tenant_id": tenant_id, "start": period_start},
    ).all()

    by_feature = []
    for row in feature_result:
        pct = (row[2] / total_spend * 100) if total_spend > 0 else 0
        baseline = baselines.get(row[0])
        trend = "normal"
        if baseline and baseline > 0:
            deviation = (row[2] - baseline) / baseline * 100
            if deviation > 200:
                trend = "spike"
            elif deviation > 50:
                trend = "rising"

        by_feature.append(
            CostBreakdownItemDTO(
                name=row[0],
                display_name=row[1],
                spend_cents=int(row[2]),
                request_count=int(row[3]),
                pct_of_total=round(pct, 1),
                trend=trend,
            )
        )

    # Get by model
    model_result = session.execute(
        text(
            """
            SELECT
                model,
                COALESCE(SUM(cost_cents), 0) as spend,
                COUNT(*) as requests
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :start
            GROUP BY model
            ORDER BY spend DESC
            LIMIT 10
        """
        ),
        {"tenant_id": tenant_id, "start": period_start},
    ).all()

    by_model = []
    for row in model_result:
        pct = (row[1] / total_spend * 100) if total_spend > 0 else 0
        # Simple model display name mapping
        display = row[0].replace("claude-", "Claude ").replace("-", " ").title() if row[0] else None

        by_model.append(
            CostBreakdownItemDTO(
                name=row[0],
                display_name=display,
                spend_cents=int(row[1]),
                request_count=int(row[2]),
                pct_of_total=round(pct, 1),
                trend="normal",  # Model trend is usually stable
            )
        )

    # Get by user (top 10)
    user_result = session.execute(
        text(
            """
            SELECT
                COALESCE(user_id, 'anonymous') as user_id,
                COALESCE(SUM(cost_cents), 0) as spend,
                COUNT(*) as requests
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :start
            GROUP BY user_id
            ORDER BY spend DESC
            LIMIT 10
        """
        ),
        {"tenant_id": tenant_id, "start": period_start},
    ).all()

    by_user = []
    for row in user_result:
        pct = (row[1] / total_spend * 100) if total_spend > 0 else 0
        baseline = baselines.get(f"user:{row[0]}")
        trend = "normal"
        if baseline and baseline > 0:
            deviation = (row[1] - baseline) / baseline * 100
            if deviation > 200:
                trend = "spike"
            elif deviation > 50:
                trend = "rising"

        by_user.append(
            CostBreakdownItemDTO(
                name=row[0],
                display_name=None,
                spend_cents=int(row[1]),
                request_count=int(row[2]),
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
    session: Session = Depends(get_session),
) -> CustomerCostIncidentListDTO:
    """
    GET /guard/costs/incidents

    Cost-related incidents visible to customer.
    Uses calm vocabulary (protected, attention_needed).
    Does NOT expose severity levels directly.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    # Get cost anomalies that have been linked to incidents
    where_clause = "tenant_id = :tenant_id AND detected_at >= :cutoff"
    params = {"tenant_id": tenant_id, "cutoff": cutoff, "limit": limit + 1}

    if not include_resolved:
        where_clause += " AND resolved = false"

    result = session.execute(
        text(
            f"""
            SELECT
                id, anomaly_type, severity,
                current_value_cents, expected_value_cents, threshold_pct,
                message, incident_id, action_taken,
                resolved, detected_at, resolved_at
            FROM cost_anomalies
            WHERE {where_clause}
            ORDER BY detected_at DESC
            LIMIT :limit
        """
        ),
        params,
    ).all()

    has_more = len(result) > limit
    result = result[:limit]

    # Map to customer-friendly DTOs
    incidents = []
    for row in result:
        # Map anomaly_type to trigger_type
        anomaly_type = row[1]
        if "budget" in anomaly_type.lower():
            if "exceeded" in anomaly_type.lower():
                trigger_type = "budget_exceeded"
            else:
                trigger_type = "budget_warning"
        else:
            trigger_type = "cost_spike"

        # Calculate cost avoided (difference between current and threshold)
        current = float(row[3] or 0)
        threshold = float(row[5] or 0)
        cost_avoided = max(0, int(current - threshold))

        # Map severity to calm status
        severity = row[2] or "medium"
        is_resolved = row[9] or False

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

        incidents.append(
            CustomerCostIncidentDTO(
                id=f"inc_{row[0]}",
                title=title,
                status=status,
                trigger_type=trigger_type,
                cost_at_trigger_cents=int(current),
                cost_avoided_cents=cost_avoided,
                threshold_cents=int(threshold) if threshold else None,
                action_taken=row[8] or "Alerted you about this cost event",
                recommendation=recommendation,
                detected_at=row[10].isoformat() if row[10] else now.isoformat(),
                resolved_at=row[11].isoformat() if row[11] else None,
            )
        )

    return CustomerCostIncidentListDTO(
        incidents=incidents,
        total=len(incidents),
        has_more=has_more,
    )
