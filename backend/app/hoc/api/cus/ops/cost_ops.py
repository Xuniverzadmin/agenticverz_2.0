# Layer: L2 — Product APIs
# AUDIENCE: FOUNDER
# Product: ops-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Ops Console cost intelligence endpoints (founder cost visibility)
# Callers: Ops Console UI
# Allowed Imports: L4
# Forbidden Imports: L1, L5, L6
# artifact_class: CODE

"""Ops Console Cost Intelligence API - Founder Cost Visibility

M29 Category 4: Cost Intelligence Completion

This router provides /ops/cost/* endpoints for the Founder Ops Console.
Founders see cross-tenant cost aggregation, anomalies, and tenant drilldown.

THE INVARIANT: All values derive from complete snapshots, never live data.

Endpoints:
- GET  /ops/cost/overview   - Global cost overview with anomaly summary
- GET  /ops/cost/anomalies  - Cross-tenant anomaly aggregation
- GET  /ops/cost/tenants    - Per-tenant cost drilldown
- GET  /ops/cost/customers/{tenant_id} - Deep-dive cost analysis

CRITICAL: Uses FROZEN DTOs from app.contracts.ops.
NEVER return raw database rows - always map to DTOs.

Architecture:
- L2 is thin HTTP boundary — no SQL, no business logic
- All operations route through L4 registry → L5 engine → L6 driver
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

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
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)

logger = logging.getLogger("nova.api.cost_ops")

router = APIRouter(
    prefix="/ops/cost",
    tags=["Ops Cost Intelligence"],
    dependencies=[Depends(verify_fops_token)],  # Category 2: FOPS auth (aud=fops, mfa=true)
)


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/overview", response_model=FounderCostOverviewDTO)
async def get_cost_overview(
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_session_dep),
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
    registry = get_operation_registry()
    op = await registry.execute(
        "ops.cost",
        OperationContext(
            session=session,
            tenant_id="FOUNDER",
            params={"method": "get_overview"},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    return FounderCostOverviewDTO(
        spend_today_cents=result.spend_today_cents,
        spend_mtd_cents=result.spend_mtd_cents,
        spend_7d_cents=result.spend_7d_cents,
        tenants_with_anomalies=result.tenants_with_anomalies,
        total_anomalies_24h=result.total_anomalies_24h,
        largest_deviation_tenant_id=result.largest_deviation_tenant_id,
        largest_deviation_pct=result.largest_deviation_pct,
        largest_deviation_type=result.largest_deviation_type,
        last_snapshot_at=result.last_snapshot_at,
        snapshot_freshness_minutes=result.snapshot_freshness_minutes,
        snapshot_status=result.snapshot_status,
        trend_7d=result.trend_7d,
    )


@router.get("/anomalies", response_model=FounderCostAnomalyListDTO)
async def get_cost_anomalies(
    include_resolved: bool = Query(False, description="Include resolved anomalies"),
    limit: int = Query(50, ge=1, le=200),
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_session_dep),
) -> FounderCostAnomalyListDTO:
    """
    GET /ops/cost/anomalies

    Cross-tenant anomaly aggregation for founders.

    FOUNDER-ONLY: Shows affected_tenants count (cross-tenant data).
    NEVER expose to Customer Console.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "ops.cost",
        OperationContext(
            session=session,
            tenant_id="FOUNDER",
            params={
                "method": "get_anomalies",
                "include_resolved": include_resolved,
                "limit": limit,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    anomalies = [
        FounderCostAnomalyDTO(
            id=a.id,
            anomaly_type=a.anomaly_type,
            severity=a.severity,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            current_value_cents=a.current_value_cents,
            expected_value_cents=a.expected_value_cents,
            deviation_pct=a.deviation_pct,
            threshold_pct=a.threshold_pct,
            affected_tenants=a.affected_tenants,
            is_systemic=a.is_systemic,
            message=a.message,
            incident_id=a.incident_id,
            derived_cause=None,
            action_taken=a.action_taken,
            resolved=a.resolved,
            detected_at=a.detected_at,
            snapshot_id=a.snapshot_id,
        )
        for a in result.anomalies
    ]

    return FounderCostAnomalyListDTO(
        anomalies=anomalies,
        total=result.total,
        tenants_affected=result.tenants_affected,
        systemic_count=result.systemic_count,
    )


@router.get("/tenants", response_model=FounderCostTenantListDTO)
async def get_cost_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("spend_today", regex="^(spend_today|spend_mtd|deviation|anomaly_count)$"),
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_session_dep),
) -> FounderCostTenantListDTO:
    """
    GET /ops/cost/tenants

    Per-tenant cost drilldown for founders.
    Shows each tenant's cost metrics with anomaly indicators.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "ops.cost",
        OperationContext(
            session=session,
            tenant_id="FOUNDER",
            params={
                "method": "get_tenants",
                "page": page,
                "page_size": page_size,
                "sort_by": sort_by,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    result = op.data
    tenants = [
        FounderCostTenantDTO(
            tenant_id=t.tenant_id,
            tenant_name=t.tenant_name,
            spend_today_cents=t.spend_today_cents,
            spend_mtd_cents=t.spend_mtd_cents,
            spend_7d_cents=t.spend_7d_cents,
            deviation_from_baseline_pct=t.deviation_from_baseline_pct,
            baseline_7d_avg_cents=t.baseline_7d_avg_cents,
            budget_monthly_cents=t.budget_monthly_cents,
            budget_used_pct=t.budget_used_pct,
            has_anomaly=t.has_anomaly,
            anomaly_count_24h=t.anomaly_count_24h,
            trend=t.trend,
            last_activity=t.last_activity,
        )
        for t in result.tenants
    ]

    return FounderCostTenantListDTO(
        tenants=tenants,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get("/customers/{tenant_id}", response_model=FounderCustomerCostDrilldownDTO)
async def get_customer_cost_drilldown(
    tenant_id: str,
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_session_dep),
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
    registry = get_operation_registry()
    op = await registry.execute(
        "ops.cost",
        OperationContext(
            session=session,
            tenant_id="FOUNDER",
            params={
                "method": "get_customer_drilldown",
                "tenant_id": tenant_id,
            },
        ),
    )
    if not op.success:
        if op.error_code == "TENANT_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail=f"Tenant {tenant_id} not found or has no cost data",
            )
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    r = op.data

    daily_breakdown = [
        CostDailyBreakdownDTO(
            date=d.date,
            spend_cents=d.spend_cents,
            request_count=d.request_count,
            avg_cost_per_request_cents=d.avg_cost_per_request_cents,
        )
        for d in r.daily_breakdown
    ]

    by_feature = [
        CostByFeatureDTO(
            feature_tag=f.feature_tag,
            display_name=None,
            spend_cents=f.spend_cents,
            request_count=f.request_count,
            pct_of_total=f.pct_of_total,
            trend="stable",
        )
        for f in r.by_feature
    ]

    by_user = [
        CostByUserDTO(
            user_id=u.user_id,
            spend_cents=u.spend_cents,
            request_count=u.request_count,
            pct_of_total=u.pct_of_total,
            is_anomalous=u.is_anomalous,
        )
        for u in r.by_user
    ]

    by_model = [
        CostByModelDTO(
            model=m.model,
            spend_cents=m.spend_cents,
            input_tokens=m.input_tokens,
            output_tokens=m.output_tokens,
            request_count=m.request_count,
            pct_of_total=m.pct_of_total,
        )
        for m in r.by_model
    ]

    recent_anomalies = [
        CustomerAnomalyHistoryDTO(
            id=a.id,
            anomaly_type=a.anomaly_type,
            severity=a.severity,
            detected_at=a.detected_at,
            resolved=a.resolved,
            deviation_pct=a.deviation_pct,
            derived_cause=a.derived_cause,
            message=a.message,
        )
        for a in r.recent_anomalies
    ]

    return FounderCustomerCostDrilldownDTO(
        tenant_id=r.tenant_id,
        tenant_name=r.tenant_name,
        spend_today_cents=r.spend_today_cents,
        spend_mtd_cents=r.spend_mtd_cents,
        spend_7d_cents=r.spend_7d_cents,
        spend_30d_cents=r.spend_30d_cents,
        baseline_7d_avg_cents=r.baseline_7d_avg_cents,
        deviation_from_baseline_pct=r.deviation_from_baseline_pct,
        budget_monthly_cents=r.budget_monthly_cents,
        budget_used_pct=r.budget_used_pct,
        projected_month_end_cents=r.projected_month_end_cents,
        days_until_budget_exhausted=r.days_until_budget_exhausted,
        daily_breakdown=daily_breakdown,
        by_feature=by_feature,
        by_user=by_user,
        by_model=by_model,
        largest_driver_type=r.largest_driver_type,
        largest_driver_name=r.largest_driver_name,
        largest_driver_pct=r.largest_driver_pct,
        active_anomalies=r.active_anomalies,
        recent_anomalies=recent_anomalies,
        trend_7d=r.trend_7d,
        trend_message=r.trend_message,
        last_activity=r.last_activity,
        last_updated=r.last_updated,
    )
