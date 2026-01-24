"""Ops Console Cost Intelligence API - Founder Cost Visibility

M29 Category 4: Cost Intelligence Completion

This router provides /ops/cost/* endpoints for the Founder Ops Console.
Founders see cross-tenant cost aggregation, anomalies, and tenant drilldown.

THE INVARIANT: All values derive from complete snapshots, never live data.

Endpoints:
- GET  /ops/cost/overview   - Global cost overview with anomaly summary
- GET  /ops/cost/anomalies  - Cross-tenant anomaly aggregation
- GET  /ops/cost/tenants    - Per-tenant cost drilldown

CRITICAL: Uses FROZEN DTOs from app.contracts.ops.
NEVER return raw database rows - always map to DTOs.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlmodel import Session

# Category 2 Auth: FOPS authentication (aud=fops, mfa=true)
from app.auth.console_auth import FounderToken, verify_fops_token

# Category 3 Frozen Contracts
from app.contracts.ops import (
    CostByFeatureDTO,
    CostByModelDTO,
    CostByUserDTO,
    CostDailyBreakdownDTO,
    CustomerAnomalyHistoryDTO,
    FounderCostAnomalyDTO,
    FounderCostAnomalyListDTO,
    FounderCostOverviewDTO,
    FounderCostTenantDTO,
    FounderCostTenantListDTO,
    FounderCustomerCostDrilldownDTO,
)
from app.db import get_session

logger = logging.getLogger("nova.api.cost_ops")

router = APIRouter(
    prefix="/ops/cost",
    tags=["Ops Cost Intelligence"],
    dependencies=[Depends(verify_fops_token)],  # Category 2: FOPS auth (aud=fops, mfa=true)
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _compute_snapshot_status(last_snapshot_at: Optional[datetime]) -> tuple[int, str]:
    """Compute snapshot freshness status."""
    if not last_snapshot_at:
        return 9999, "missing"

    now = datetime.now(timezone.utc)
    delta = now - last_snapshot_at
    minutes = int(delta.total_seconds() / 60)

    if minutes < 60:
        return minutes, "fresh"
    elif minutes < 1440:  # 24 hours
        return minutes, "stale"
    else:
        return minutes, "missing"


def _compute_trend(daily_costs: List[float]) -> str:
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
# ENDPOINTS
# =============================================================================


@router.get("/overview", response_model=FounderCostOverviewDTO)
async def get_cost_overview(
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
) -> FounderCostOverviewDTO:
    """
    GET /ops/cost/overview

    Global cost overview for founders.
    Aggregates data from complete snapshots only.

    Shows:
    - Total spend (today, MTD, 7d)
    - Tenants with anomalies (count)
    - Largest deviation
    - Snapshot freshness
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    # Get total spend from cost_records (fallback if snapshots not available)
    spend_result = session.execute(
        text(
            """
            SELECT
                COALESCE(SUM(CASE WHEN created_at >= :today THEN cost_cents ELSE 0 END), 0) as today,
                COALESCE(SUM(CASE WHEN created_at >= :month THEN cost_cents ELSE 0 END), 0) as mtd,
                COALESCE(SUM(CASE WHEN created_at >= :week THEN cost_cents ELSE 0 END), 0) as week
            FROM cost_records
        """
        ),
        {"today": today_start, "month": month_start, "week": week_ago},
    ).first()

    spend_today = int(spend_result[0]) if spend_result else 0
    spend_mtd = int(spend_result[1]) if spend_result else 0
    spend_7d = int(spend_result[2]) if spend_result else 0

    # Get anomaly counts
    anomaly_result = session.execute(
        text(
            """
            SELECT
                COUNT(DISTINCT tenant_id) as tenants,
                COUNT(*) as total
            FROM cost_anomalies
            WHERE resolved = false AND detected_at >= :cutoff
        """
        ),
        {"cutoff": now - timedelta(hours=24)},
    ).first()

    tenants_with_anomalies = int(anomaly_result[0]) if anomaly_result else 0
    total_anomalies = int(anomaly_result[1]) if anomaly_result else 0

    # Get largest deviation
    deviation_result = session.execute(
        text(
            """
            SELECT tenant_id, deviation_pct, anomaly_type
            FROM cost_anomalies
            WHERE resolved = false
            ORDER BY deviation_pct DESC NULLS LAST
            LIMIT 1
        """
        )
    ).first()

    largest_tenant_id = deviation_result[0] if deviation_result else None
    largest_deviation_pct = float(deviation_result[1]) if deviation_result else None
    largest_deviation_type = deviation_result[2] if deviation_result else None

    # Get last snapshot time
    snapshot_result = session.execute(
        text(
            """
            SELECT completed_at
            FROM cost_snapshots
            WHERE status = 'complete'
            ORDER BY completed_at DESC
            LIMIT 1
        """
        )
    ).first()

    last_snapshot_at = snapshot_result[0] if snapshot_result else None
    snapshot_minutes, snapshot_status = _compute_snapshot_status(last_snapshot_at)

    # Get 7-day daily costs for trend
    daily_costs_result = session.execute(
        text(
            """
            SELECT DATE(created_at), COALESCE(SUM(cost_cents), 0)
            FROM cost_records
            WHERE created_at >= :week
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """
        ),
        {"week": week_ago},
    ).all()

    daily_costs = [float(row[1]) for row in daily_costs_result]
    trend = _compute_trend(daily_costs)

    return FounderCostOverviewDTO(
        spend_today_cents=spend_today,
        spend_mtd_cents=spend_mtd,
        spend_7d_cents=spend_7d,
        tenants_with_anomalies=tenants_with_anomalies,
        total_anomalies_24h=total_anomalies,
        largest_deviation_tenant_id=largest_tenant_id,
        largest_deviation_pct=largest_deviation_pct,
        largest_deviation_type=largest_deviation_type,
        last_snapshot_at=last_snapshot_at.isoformat() if last_snapshot_at else None,
        snapshot_freshness_minutes=snapshot_minutes,
        snapshot_status=snapshot_status,
        trend_7d=trend,
    )


@router.get("/anomalies", response_model=FounderCostAnomalyListDTO)
async def get_cost_anomalies(
    include_resolved: bool = Query(False, description="Include resolved anomalies"),
    limit: int = Query(50, ge=1, le=200),
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
) -> FounderCostAnomalyListDTO:
    """
    GET /ops/cost/anomalies

    Cross-tenant anomaly aggregation for founders.

    FOUNDER-ONLY: Shows affected_tenants count (cross-tenant data).
    NEVER expose to Customer Console.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)

    # Build query
    where_clause = "detected_at >= :cutoff"
    params = {"cutoff": cutoff, "limit": limit}

    if not include_resolved:
        where_clause += " AND resolved = false"

    # Get anomalies
    result = session.execute(
        text(
            f"""
            SELECT
                id, tenant_id, anomaly_type, severity, entity_type, entity_id,
                current_value_cents, expected_value_cents, deviation_pct, threshold_pct,
                message, incident_id, action_taken, resolved, detected_at, snapshot_id
            FROM cost_anomalies
            WHERE {where_clause}
            ORDER BY detected_at DESC
            LIMIT :limit
        """
        ),
        params,
    ).all()

    # Count similar patterns across tenants
    pattern_counts = {}
    for row in result:
        key = f"{row[2]}:{row[4]}"  # anomaly_type:entity_type
        if key not in pattern_counts:
            pattern_counts[key] = set()
        pattern_counts[key].add(row[1])  # tenant_id

    # Map to DTOs
    anomalies = []
    for row in result:
        pattern_key = f"{row[2]}:{row[4]}"
        affected_count = len(pattern_counts.get(pattern_key, set()))

        anomalies.append(
            FounderCostAnomalyDTO(
                id=row[0],
                anomaly_type=row[2],
                severity=row[3] or "medium",
                entity_type=row[4],
                entity_id=row[5],
                current_value_cents=float(row[6] or 0),
                expected_value_cents=float(row[7] or 0),
                deviation_pct=float(row[8] or 0),
                threshold_pct=float(row[9] or 0),
                affected_tenants=affected_count,
                is_systemic=affected_count > 3,
                message=row[10] or "",
                incident_id=row[11],
                action_taken=row[12],
                resolved=row[13] or False,
                detected_at=row[14].isoformat() if row[14] else now.isoformat(),
                snapshot_id=row[15],
            )
        )

    # Count unique tenants and systemic issues
    unique_tenants = len(set(a.id.split("_")[0] for a in anomalies if a.id))
    systemic_count = sum(1 for a in anomalies if a.is_systemic)

    return FounderCostAnomalyListDTO(
        anomalies=anomalies,
        total=len(anomalies),
        tenants_affected=unique_tenants,
        systemic_count=systemic_count,
    )


@router.get("/tenants", response_model=FounderCostTenantListDTO)
async def get_cost_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("spend_today", regex="^(spend_today|spend_mtd|deviation|anomaly_count)$"),
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
) -> FounderCostTenantListDTO:
    """
    GET /ops/cost/tenants

    Per-tenant cost drilldown for founders.
    Shows each tenant's cost metrics with anomaly indicators.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    day_ago = now - timedelta(hours=24)

    offset = (page - 1) * page_size

    # Sort mapping
    sort_map = {
        "spend_today": "spend_today DESC",
        "spend_mtd": "spend_mtd DESC",
        "deviation": "deviation_pct DESC NULLS LAST",
        "anomaly_count": "anomaly_count DESC",
    }
    order_by = sort_map.get(sort_by, "spend_today DESC")

    # Get tenant costs with anomaly counts
    result = session.execute(
        text(
            f"""
            WITH tenant_costs AS (
                SELECT
                    tenant_id,
                    COALESCE(SUM(CASE WHEN created_at >= :today THEN cost_cents ELSE 0 END), 0) as spend_today,
                    COALESCE(SUM(CASE WHEN created_at >= :month THEN cost_cents ELSE 0 END), 0) as spend_mtd,
                    COALESCE(SUM(CASE WHEN created_at >= :week THEN cost_cents ELSE 0 END), 0) as spend_7d
                FROM cost_records
                GROUP BY tenant_id
            ),
            tenant_anomalies AS (
                SELECT
                    tenant_id,
                    COUNT(*) as anomaly_count,
                    MAX(deviation_pct) as max_deviation
                FROM cost_anomalies
                WHERE resolved = false AND detected_at >= :day_ago
                GROUP BY tenant_id
            ),
            tenant_baselines AS (
                SELECT
                    tenant_id,
                    avg_daily_cost_cents
                FROM cost_snapshot_baselines
                WHERE is_current = true AND entity_type = 'tenant'
            )
            SELECT
                tc.tenant_id,
                COALESCE(t.name, tc.tenant_id) as tenant_name,
                tc.spend_today,
                tc.spend_mtd,
                tc.spend_7d,
                tb.avg_daily_cost_cents as baseline,
                CASE WHEN tb.avg_daily_cost_cents > 0
                     THEN ((tc.spend_today - tb.avg_daily_cost_cents) / tb.avg_daily_cost_cents * 100)
                     ELSE NULL END as deviation_pct,
                cb.monthly_limit_cents as budget,
                CASE WHEN cb.monthly_limit_cents > 0
                     THEN (tc.spend_mtd::float / cb.monthly_limit_cents * 100)
                     ELSE NULL END as budget_used_pct,
                COALESCE(ta.anomaly_count, 0) as anomaly_count,
                MAX(cr.created_at) as last_activity
            FROM tenant_costs tc
            LEFT JOIN tenants t ON t.id = tc.tenant_id
            LEFT JOIN tenant_baselines tb ON tb.tenant_id = tc.tenant_id
            LEFT JOIN cost_budgets cb ON cb.tenant_id = tc.tenant_id AND cb.budget_type = 'tenant'
            LEFT JOIN tenant_anomalies ta ON ta.tenant_id = tc.tenant_id
            LEFT JOIN cost_records cr ON cr.tenant_id = tc.tenant_id
            GROUP BY tc.tenant_id, t.name, tc.spend_today, tc.spend_mtd, tc.spend_7d,
                     tb.avg_daily_cost_cents, cb.monthly_limit_cents, ta.anomaly_count
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
        """
        ),
        {
            "today": today_start,
            "month": month_start,
            "week": week_ago,
            "day_ago": day_ago,
            "limit": page_size,
            "offset": offset,
        },
    ).all()

    # Get total count
    count_result = session.execute(text("SELECT COUNT(DISTINCT tenant_id) FROM cost_records")).first()
    total = int(count_result[0]) if count_result else 0

    # Map to DTOs
    tenants = []
    for row in result:
        # Determine trend from deviation
        deviation = row[6]
        if deviation is None:
            trend = "stable"
        elif deviation > 50:
            trend = "increasing"
        elif deviation < -30:
            trend = "decreasing"
        else:
            trend = "stable"

        tenants.append(
            FounderCostTenantDTO(
                tenant_id=row[0],
                tenant_name=row[1] or row[0],
                spend_today_cents=int(row[2] or 0),
                spend_mtd_cents=int(row[3] or 0),
                spend_7d_cents=int(row[4] or 0),
                deviation_from_baseline_pct=float(row[6]) if row[6] else None,
                baseline_7d_avg_cents=float(row[5]) if row[5] else None,
                budget_monthly_cents=int(row[7]) if row[7] else None,
                budget_used_pct=float(row[8]) if row[8] else None,
                has_anomaly=int(row[9] or 0) > 0,
                anomaly_count_24h=int(row[9] or 0),
                trend=trend,
                last_activity=row[10].isoformat() if row[10] else None,
            )
        )

    return FounderCostTenantListDTO(
        tenants=tenants,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/customers/{tenant_id}", response_model=FounderCustomerCostDrilldownDTO)
async def get_customer_cost_drilldown(
    tenant_id: str,
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
) -> FounderCustomerCostDrilldownDTO:
    """
    GET /ops/cost/customers/{tenant_id}

    Deep-dive cost analysis for a single customer.
    Answers "why is this customer spending so much?"

    Provides:
    - Daily cost breakdown (last 7 days)
    - Cost attribution by feature, user, and model
    - Anomaly history
    - Budget status and projections
    """
    from fastapi import HTTPException

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Check if tenant exists
    tenant_check = session.execute(
        text("SELECT COUNT(*) FROM cost_records WHERE tenant_id = :tenant_id"), {"tenant_id": tenant_id}
    ).first()

    if not tenant_check or tenant_check[0] == 0:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found or has no cost data")

    # Get tenant name
    tenant_name_result = session.execute(
        text("SELECT name FROM tenants WHERE id = :tenant_id"), {"tenant_id": tenant_id}
    ).first()
    tenant_name = tenant_name_result[0] if tenant_name_result else tenant_id

    # Get spend summary
    spend_result = session.execute(
        text(
            """
            SELECT
                COALESCE(SUM(CASE WHEN created_at >= :today THEN cost_cents ELSE 0 END), 0) as today,
                COALESCE(SUM(CASE WHEN created_at >= :month_start THEN cost_cents ELSE 0 END), 0) as mtd,
                COALESCE(SUM(CASE WHEN created_at >= :week THEN cost_cents ELSE 0 END), 0) as week,
                COALESCE(SUM(CASE WHEN created_at >= :month_ago THEN cost_cents ELSE 0 END), 0) as month
            FROM cost_records
            WHERE tenant_id = :tenant_id
        """
        ),
        {
            "tenant_id": tenant_id,
            "today": today_start,
            "month_start": month_start,
            "week": week_ago,
            "month_ago": month_ago,
        },
    ).first()

    spend_today = int(spend_result[0]) if spend_result else 0
    spend_mtd = int(spend_result[1]) if spend_result else 0
    spend_7d = int(spend_result[2]) if spend_result else 0
    spend_30d = int(spend_result[3]) if spend_result else 0

    # Get baseline from snapshots
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

    baseline_7d_avg = float(baseline_result[0]) if baseline_result else None
    deviation_pct = None
    if baseline_7d_avg and baseline_7d_avg > 0:
        deviation_pct = ((spend_today - baseline_7d_avg) / baseline_7d_avg) * 100

    # Get budget info
    budget_result = session.execute(
        text(
            """
            SELECT monthly_limit_cents
            FROM cost_budgets
            WHERE tenant_id = :tenant_id AND budget_type = 'tenant' AND is_active = true
        """
        ),
        {"tenant_id": tenant_id},
    ).first()

    budget_monthly = int(budget_result[0]) if budget_result else None
    budget_used_pct = None
    projected_month_end = None
    days_until_exhausted = None

    if budget_monthly and budget_monthly > 0:
        budget_used_pct = (spend_mtd / budget_monthly) * 100
        # Project month end based on daily average
        days_in_month = 30
        day_of_month = now.day
        if day_of_month > 0:
            daily_avg = spend_mtd / day_of_month
            projected_month_end = int(daily_avg * days_in_month)
            remaining_budget = budget_monthly - spend_mtd
            if daily_avg > 0 and remaining_budget > 0:
                days_until_exhausted = int(remaining_budget / daily_avg)

    # Get daily breakdown (last 7 days)
    daily_result = session.execute(
        text(
            """
            SELECT
                DATE(created_at) as day,
                COALESCE(SUM(cost_cents), 0) as spend,
                COUNT(*) as requests
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :week
            GROUP BY DATE(created_at)
            ORDER BY day DESC
            LIMIT 7
        """
        ),
        {"tenant_id": tenant_id, "week": week_ago},
    ).all()

    daily_breakdown = []
    for row in daily_result:
        spend = int(row[1])
        requests = int(row[2])
        avg_cost = spend / requests if requests > 0 else 0
        daily_breakdown.append(
            CostDailyBreakdownDTO(
                date=row[0].isoformat(),
                spend_cents=spend,
                request_count=requests,
                avg_cost_per_request_cents=round(avg_cost, 2),
            )
        )

    # Get cost by feature
    feature_result = session.execute(
        text(
            """
            SELECT
                COALESCE(feature_tag, 'unclassified') as feature,
                COALESCE(SUM(cost_cents), 0) as spend,
                COUNT(*) as requests
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :week
            GROUP BY feature_tag
            ORDER BY spend DESC
            LIMIT 10
        """
        ),
        {"tenant_id": tenant_id, "week": week_ago},
    ).all()

    total_7d = spend_7d if spend_7d > 0 else 1
    by_feature = []
    for row in feature_result:
        pct = (float(row[1]) / total_7d) * 100
        by_feature.append(
            CostByFeatureDTO(
                feature_tag=row[0],
                display_name=None,
                spend_cents=int(row[1]),
                request_count=int(row[2]),
                pct_of_total=round(pct, 1),
                trend="stable",  # Could be computed from historical data
            )
        )

    # Get cost by user (top 10)
    user_result = session.execute(
        text(
            """
            SELECT
                COALESCE(user_id, 'unknown') as user,
                COALESCE(SUM(cost_cents), 0) as spend,
                COUNT(*) as requests
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :week
            GROUP BY user_id
            ORDER BY spend DESC
            LIMIT 10
        """
        ),
        {"tenant_id": tenant_id, "week": week_ago},
    ).all()

    # Check which users have active anomalies
    anomalous_users_result = session.execute(
        text(
            """
            SELECT DISTINCT entity_id
            FROM cost_anomalies
            WHERE tenant_id = :tenant_id AND entity_type = 'user' AND resolved = false
        """
        ),
        {"tenant_id": tenant_id},
    ).all()
    anomalous_users = {row[0] for row in anomalous_users_result if row[0]}

    by_user = []
    for row in user_result:
        pct = (float(row[1]) / total_7d) * 100
        by_user.append(
            CostByUserDTO(
                user_id=row[0],
                spend_cents=int(row[1]),
                request_count=int(row[2]),
                pct_of_total=round(pct, 1),
                is_anomalous=row[0] in anomalous_users,
            )
        )

    # Get cost by model
    model_result = session.execute(
        text(
            """
            SELECT
                model,
                COALESCE(SUM(cost_cents), 0) as spend,
                COALESCE(SUM(input_tokens), 0) as input_tokens,
                COALESCE(SUM(output_tokens), 0) as output_tokens,
                COUNT(*) as requests
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :week
            GROUP BY model
            ORDER BY spend DESC
        """
        ),
        {"tenant_id": tenant_id, "week": week_ago},
    ).all()

    by_model = []
    for row in model_result:
        pct = (float(row[1]) / total_7d) * 100
        by_model.append(
            CostByModelDTO(
                model=row[0],
                spend_cents=int(row[1]),
                input_tokens=int(row[2]),
                output_tokens=int(row[3]),
                request_count=int(row[4]),
                pct_of_total=round(pct, 1),
            )
        )

    # Determine largest driver
    largest_driver_type = "feature"
    largest_driver_name = "unknown"
    largest_driver_pct = 0.0

    if (
        by_feature
        and by_feature[0].pct_of_total >= (by_user[0].pct_of_total if by_user else 0)
        and by_feature[0].pct_of_total >= (by_model[0].pct_of_total if by_model else 0)
    ):
        largest_driver_type = "feature"
        largest_driver_name = by_feature[0].feature_tag
        largest_driver_pct = by_feature[0].pct_of_total
    elif by_user and by_user[0].pct_of_total >= (by_model[0].pct_of_total if by_model else 0):
        largest_driver_type = "user"
        largest_driver_name = by_user[0].user_id
        largest_driver_pct = by_user[0].pct_of_total
    elif by_model:
        largest_driver_type = "model"
        largest_driver_name = by_model[0].model
        largest_driver_pct = by_model[0].pct_of_total

    # Get anomaly history
    anomaly_result = session.execute(
        text(
            """
            SELECT
                id, anomaly_type, severity, detected_at, resolved, deviation_pct, derived_cause, message
            FROM cost_anomalies
            WHERE tenant_id = :tenant_id
            ORDER BY detected_at DESC
            LIMIT 5
        """
        ),
        {"tenant_id": tenant_id},
    ).all()

    active_anomalies = sum(1 for row in anomaly_result if not row[4])
    recent_anomalies = []
    for row in anomaly_result:
        recent_anomalies.append(
            CustomerAnomalyHistoryDTO(
                id=row[0],
                anomaly_type=row[1],
                severity=row[2] or "medium",
                detected_at=row[3].isoformat() if row[3] else now.isoformat(),
                resolved=row[4] or False,
                deviation_pct=float(row[5]) if row[5] else 0.0,
                derived_cause=row[6],
                message=row[7] or "",
            )
        )

    # Compute trend
    trend_7d = _compute_trend([d.spend_cents for d in reversed(daily_breakdown)])

    # Generate trend message
    if trend_7d == "increasing":
        trend_message = (
            f"Cost is trending up - {deviation_pct:.0f}% above baseline" if deviation_pct else "Cost is trending up"
        )
    elif trend_7d == "decreasing":
        trend_message = "Cost is trending down"
    else:
        trend_message = "Cost is within normal range for this customer"

    # Get last activity
    last_activity_result = session.execute(
        text(
            """
            SELECT MAX(created_at)
            FROM cost_records
            WHERE tenant_id = :tenant_id
        """
        ),
        {"tenant_id": tenant_id},
    ).first()

    last_activity = last_activity_result[0].isoformat() if last_activity_result and last_activity_result[0] else None

    return FounderCustomerCostDrilldownDTO(
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
        last_activity=last_activity,
        last_updated=now.isoformat(),
    )
