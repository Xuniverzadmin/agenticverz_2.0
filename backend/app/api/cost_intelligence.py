"""
M26 Cost Intelligence API

Core Objective:
Every token spent is attributable to tenant → user → feature → request.
Every anomaly must trigger an action, not a chart.

This is not reporting. This is CONTROL.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlmodel import Session, select

from app.db import (
    CostAnomaly,
    CostBudget,
    CostRecord,
    FeatureTag,
    get_session,
    utc_now,
)

# Phase 2B: Write service for DB operations
from app.services.cost_write_service import CostWriteService


def get_tenant_id(tenant_id: str = Query(..., description="Tenant ID")) -> str:
    """Extract tenant_id from query parameter."""
    return tenant_id


logger = logging.getLogger("nova.cost_intelligence")

router = APIRouter(prefix="/cost", tags=["Cost Intelligence"])


# =============================================================================
# Request/Response Models
# =============================================================================


class FeatureTagCreate(BaseModel):
    """Create a new feature tag."""

    tag: str = Field(..., description="Feature namespace (e.g., 'customer_support.chat')")
    display_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = None
    budget_cents: Optional[int] = Field(None, ge=0, description="Per-feature budget in cents")


class FeatureTagResponse(BaseModel):
    """Feature tag response."""

    id: str
    tenant_id: str
    tag: str
    display_name: str
    description: Optional[str]
    budget_cents: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FeatureTagUpdate(BaseModel):
    """Update a feature tag."""

    display_name: Optional[str] = None
    description: Optional[str] = None
    budget_cents: Optional[int] = None
    is_active: Optional[bool] = None


class CostRecordCreate(BaseModel):
    """Record a cost entry."""

    user_id: Optional[str] = None
    feature_tag: Optional[str] = None
    request_id: Optional[str] = None
    workflow_id: Optional[str] = None
    skill_id: Optional[str] = None
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_cents: float


class CostSummary(BaseModel):
    """Cost summary for a period."""

    tenant_id: str
    period_start: datetime
    period_end: datetime
    total_cost_cents: float
    total_input_tokens: int
    total_output_tokens: int
    request_count: int
    budget_cents: Optional[int]
    budget_used_pct: Optional[float]
    days_remaining_at_current_rate: Optional[float]


class CostByFeature(BaseModel):
    """Cost breakdown by feature."""

    feature_tag: str
    display_name: Optional[str]
    total_cost_cents: float
    request_count: int
    pct_of_total: float
    budget_cents: Optional[int]
    budget_used_pct: Optional[float]


class CostByUser(BaseModel):
    """Cost breakdown by user."""

    user_id: str
    total_cost_cents: float
    request_count: int
    pct_of_total: float
    is_anomaly: bool
    anomaly_message: Optional[str]


class CostByModel(BaseModel):
    """Cost breakdown by model."""

    model: str
    total_cost_cents: float
    total_input_tokens: int
    total_output_tokens: int
    request_count: int
    pct_of_total: float


class CostProjection(BaseModel):
    """Cost projection for upcoming period."""

    tenant_id: str
    lookback_days: int
    forecast_days: int
    current_daily_avg_cents: float
    projected_total_cents: float
    monthly_projection_cents: float
    budget_cents: Optional[int]
    days_until_budget_exhausted: Optional[float]
    trend: str  # "increasing", "stable", "decreasing"


class CostAnomalyResponse(BaseModel):
    """Cost anomaly response."""

    id: str
    tenant_id: str
    anomaly_type: str
    severity: str
    entity_type: str
    entity_id: Optional[str]
    current_value_cents: float
    expected_value_cents: float
    deviation_pct: float
    message: str
    incident_id: Optional[str]
    action_taken: Optional[str]
    resolved: bool
    detected_at: datetime


class CostDashboard(BaseModel):
    """Complete cost dashboard data."""

    summary: CostSummary
    by_feature: List[CostByFeature]
    by_user: List[CostByUser]
    by_model: List[CostByModel]
    anomalies: List[CostAnomalyResponse]
    projection: CostProjection


class BudgetCreate(BaseModel):
    """Create or update a budget."""

    budget_type: str = Field(..., description="'tenant', 'feature', or 'user'")
    entity_id: Optional[str] = Field(None, description="Feature tag or user ID")
    daily_limit_cents: Optional[int] = Field(None, ge=0)
    monthly_limit_cents: Optional[int] = Field(None, ge=0)
    warn_threshold_pct: int = Field(80, ge=0, le=100)
    hard_limit_enabled: bool = False


class BudgetResponse(BaseModel):
    """Budget response."""

    id: str
    tenant_id: str
    budget_type: str
    entity_id: Optional[str]
    daily_limit_cents: Optional[int]
    monthly_limit_cents: Optional[int]
    warn_threshold_pct: int
    hard_limit_enabled: bool
    is_active: bool
    current_daily_spend_cents: Optional[float]
    current_monthly_spend_cents: Optional[float]


# =============================================================================
# Feature Tag Endpoints
# =============================================================================


@router.post("/features", response_model=FeatureTagResponse)
async def create_feature_tag(
    data: FeatureTagCreate,
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> FeatureTagResponse:
    """
    Register a new feature tag.

    Feature tags are MANDATORY for cost attribution.
    No tag → request defaulted to 'unclassified' (and flagged).
    """
    # Check if tag already exists for this tenant
    existing = session.exec(
        select(FeatureTag).where(
            FeatureTag.tenant_id == tenant_id,
            FeatureTag.tag == data.tag,
        )
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail=f"Feature tag '{data.tag}' already exists for this tenant")

    # Validate tag format (namespace.action)
    if "." not in data.tag:
        raise HTTPException(
            status_code=400, detail="Feature tag must be in namespace.action format (e.g., 'customer_support.chat')"
        )

    # Phase 2B: Use write service for DB operations
    cost_service = CostWriteService(session)
    feature_tag = cost_service.create_feature_tag(
        tenant_id=tenant_id,
        tag=data.tag,
        display_name=data.display_name,
        description=data.description,
        budget_cents=data.budget_cents,
    )

    logger.info(f"Created feature tag: {data.tag} for tenant {tenant_id}")

    return FeatureTagResponse(
        id=feature_tag.id,
        tenant_id=feature_tag.tenant_id,
        tag=feature_tag.tag,
        display_name=feature_tag.display_name,
        description=feature_tag.description,
        budget_cents=feature_tag.budget_cents,
        is_active=feature_tag.is_active,
        created_at=feature_tag.created_at,
        updated_at=feature_tag.updated_at,
    )


@router.get("/features", response_model=List[FeatureTagResponse])
async def list_feature_tags(
    include_inactive: bool = False,
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> List[FeatureTagResponse]:
    """List all feature tags for the tenant."""
    query = select(FeatureTag).where(FeatureTag.tenant_id == tenant_id)

    if not include_inactive:
        query = query.where(FeatureTag.is_active == True)

    tags = session.exec(query.order_by(FeatureTag.tag)).all()

    return [
        FeatureTagResponse(
            id=tag.id,
            tenant_id=tag.tenant_id,
            tag=tag.tag,
            display_name=tag.display_name,
            description=tag.description,
            budget_cents=tag.budget_cents,
            is_active=tag.is_active,
            created_at=tag.created_at,
            updated_at=tag.updated_at,
        )
        for tag in tags
    ]


@router.put("/features/{tag}", response_model=FeatureTagResponse)
async def update_feature_tag(
    tag: str,
    data: FeatureTagUpdate,
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> FeatureTagResponse:
    """Update a feature tag."""
    feature_tag = session.exec(
        select(FeatureTag).where(
            FeatureTag.tenant_id == tenant_id,
            FeatureTag.tag == tag,
        )
    ).first()

    if not feature_tag:
        raise HTTPException(status_code=404, detail=f"Feature tag '{tag}' not found")

    # Phase 2B: Use write service for DB operations
    cost_service = CostWriteService(session)
    feature_tag = cost_service.update_feature_tag(
        feature_tag=feature_tag,
        display_name=data.display_name,
        description=data.description,
        budget_cents=data.budget_cents,
        is_active=data.is_active,
    )

    return FeatureTagResponse(
        id=feature_tag.id,
        tenant_id=feature_tag.tenant_id,
        tag=feature_tag.tag,
        display_name=feature_tag.display_name,
        description=feature_tag.description,
        budget_cents=feature_tag.budget_cents,
        is_active=feature_tag.is_active,
        created_at=feature_tag.created_at,
        updated_at=feature_tag.updated_at,
    )


# =============================================================================
# Cost Recording Endpoint
# =============================================================================


@router.post("/record")
async def record_cost(
    data: CostRecordCreate,
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> dict:
    """
    Record a cost entry.

    This is called internally after each LLM invocation.
    Feature tag validation: if tag doesn't exist, default to 'unclassified'.
    """
    feature_tag = data.feature_tag

    # Validate feature tag if provided
    if feature_tag and feature_tag != "unclassified":
        existing_tag = session.exec(
            select(FeatureTag).where(
                FeatureTag.tenant_id == tenant_id,
                FeatureTag.tag == feature_tag,
                FeatureTag.is_active == True,
            )
        ).first()

        if not existing_tag:
            logger.warning(f"Unknown feature tag '{feature_tag}' - defaulting to 'unclassified'")
            feature_tag = "unclassified"

    # Phase 2B: Use write service for DB operations
    cost_service = CostWriteService(session)
    record = cost_service.create_cost_record(
        tenant_id=tenant_id,
        user_id=data.user_id,
        feature_tag=feature_tag,
        request_id=data.request_id,
        workflow_id=data.workflow_id,
        skill_id=data.skill_id,
        model=data.model,
        input_tokens=data.input_tokens,
        output_tokens=data.output_tokens,
        cost_cents=int(data.cost_cents),
    )

    return {"id": record.id, "status": "recorded"}


# =============================================================================
# Dashboard Endpoints
# =============================================================================


@router.get("/dashboard", response_model=CostDashboard)
async def get_cost_dashboard(
    period: str = Query("24h", regex="^(24h|7d|30d)$"),
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> CostDashboard:
    """
    Get complete cost dashboard.

    If a CTO can't answer "what burned money yesterday?" in 10 seconds, this failed.
    """
    # Calculate time range
    now = utc_now()
    if period == "24h":
        period_start = now - timedelta(hours=24)
        days = 1
    elif period == "7d":
        period_start = now - timedelta(days=7)
        days = 7
    else:  # 30d
        period_start = now - timedelta(days=30)
        days = 30

    # Get summary
    summary = await _get_cost_summary(session, tenant_id, period_start, now, days)

    # Get by feature
    by_feature = await _get_costs_by_feature(session, tenant_id, period_start, summary.total_cost_cents)

    # Get by user
    by_user = await _get_costs_by_user(session, tenant_id, period_start, summary.total_cost_cents)

    # Get by model
    by_model = await _get_costs_by_model(session, tenant_id, period_start, summary.total_cost_cents)

    # Get anomalies
    anomalies = await _get_recent_anomalies(session, tenant_id, days=days)

    # Get projection
    projection = await _get_cost_projection(session, tenant_id, lookback_days=7, forecast_days=7)

    return CostDashboard(
        summary=summary,
        by_feature=by_feature,
        by_user=by_user,
        by_model=by_model,
        anomalies=anomalies,
        projection=projection,
    )


@router.get("/summary", response_model=CostSummary)
async def get_cost_summary(
    period: str = Query("24h", regex="^(24h|7d|30d)$"),
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> CostSummary:
    """Get cost summary for the period."""
    now = utc_now()
    if period == "24h":
        period_start = now - timedelta(hours=24)
        days = 1
    elif period == "7d":
        period_start = now - timedelta(days=7)
        days = 7
    else:
        period_start = now - timedelta(days=30)
        days = 30

    return await _get_cost_summary(session, tenant_id, period_start, now, days)


@router.get("/by-feature", response_model=List[CostByFeature])
async def get_costs_by_feature(
    period: str = Query("24h", regex="^(24h|7d|30d)$"),
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> List[CostByFeature]:
    """Get cost breakdown by feature tag."""
    now = utc_now()
    period_start = (
        now - timedelta(hours=24)
        if period == "24h"
        else now - timedelta(days=7)
        if period == "7d"
        else now - timedelta(days=30)
    )

    # Get total for percentage calculation
    total_result = session.execute(
        text(
            """
            SELECT COALESCE(SUM(cost_cents), 0) as total
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :period_start
        """
        ).bindparams(tenant_id=tenant_id, period_start=period_start)
    ).first()
    total_cost = total_result[0] if total_result else 0

    return await _get_costs_by_feature(session, tenant_id, period_start, total_cost)


@router.get("/by-user", response_model=List[CostByUser])
async def get_costs_by_user(
    period: str = Query("24h", regex="^(24h|7d|30d)$"),
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> List[CostByUser]:
    """Get cost breakdown by user with anomaly detection."""
    now = utc_now()
    period_start = (
        now - timedelta(hours=24)
        if period == "24h"
        else now - timedelta(days=7)
        if period == "7d"
        else now - timedelta(days=30)
    )

    # Get total for percentage calculation
    total_result = session.execute(
        text(
            """
            SELECT COALESCE(SUM(cost_cents), 0) as total
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :period_start
        """
        ).bindparams(tenant_id=tenant_id, period_start=period_start)
    ).first()
    total_cost = total_result[0] if total_result else 0

    return await _get_costs_by_user(session, tenant_id, period_start, total_cost)


@router.get("/by-model", response_model=List[CostByModel])
async def get_costs_by_model(
    period: str = Query("24h", regex="^(24h|7d|30d)$"),
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> List[CostByModel]:
    """Get cost breakdown by model."""
    now = utc_now()
    period_start = (
        now - timedelta(hours=24)
        if period == "24h"
        else now - timedelta(days=7)
        if period == "7d"
        else now - timedelta(days=30)
    )

    total_result = session.execute(
        text(
            """
            SELECT COALESCE(SUM(cost_cents), 0) as total
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :period_start
        """
        ).bindparams(tenant_id=tenant_id, period_start=period_start)
    ).first()
    total_cost = total_result[0] if total_result else 0

    return await _get_costs_by_model(session, tenant_id, period_start, total_cost)


@router.get("/anomalies", response_model=List[CostAnomalyResponse])
async def get_anomalies(
    days: int = Query(7, ge=1, le=90),
    include_resolved: bool = False,
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> List[CostAnomalyResponse]:
    """Get detected cost anomalies."""
    return await _get_recent_anomalies(session, tenant_id, days, include_resolved)


@router.get("/projection", response_model=CostProjection)
async def get_projection(
    lookback_days: int = Query(7, ge=1, le=30),
    forecast_days: int = Query(7, ge=1, le=30),
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> CostProjection:
    """Get cost projection based on historical data."""
    return await _get_cost_projection(session, tenant_id, lookback_days, forecast_days)


# =============================================================================
# Budget Endpoints
# =============================================================================


@router.post("/budgets", response_model=BudgetResponse)
async def create_or_update_budget(
    data: BudgetCreate,
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> BudgetResponse:
    """Create or update a budget."""
    if data.budget_type not in ("tenant", "feature", "user"):
        raise HTTPException(status_code=400, detail="budget_type must be 'tenant', 'feature', or 'user'")

    if data.budget_type in ("feature", "user") and not data.entity_id:
        raise HTTPException(status_code=400, detail=f"entity_id required for {data.budget_type} budget")

    # Find existing budget (read operation)
    existing = session.exec(
        select(CostBudget).where(
            CostBudget.tenant_id == tenant_id,
            CostBudget.budget_type == data.budget_type,
            CostBudget.entity_id == data.entity_id,
        )
    ).first()

    # Phase 2B: Use write service for DB operations
    cost_service = CostWriteService(session)
    budget = cost_service.create_or_update_budget(
        existing_budget=existing,
        tenant_id=tenant_id,
        budget_type=data.budget_type,
        entity_id=data.entity_id,
        daily_limit_cents=data.daily_limit_cents,
        monthly_limit_cents=data.monthly_limit_cents,
        warn_threshold_pct=data.warn_threshold_pct,
        hard_limit_enabled=data.hard_limit_enabled,
    )

    # Get current spend
    current_spend = await _get_current_spend(session, tenant_id, data.budget_type, data.entity_id)

    return BudgetResponse(
        id=budget.id,
        tenant_id=budget.tenant_id,
        budget_type=budget.budget_type,
        entity_id=budget.entity_id,
        daily_limit_cents=budget.daily_limit_cents,
        monthly_limit_cents=budget.monthly_limit_cents,
        warn_threshold_pct=budget.warn_threshold_pct,
        hard_limit_enabled=budget.hard_limit_enabled,
        is_active=budget.is_active,
        current_daily_spend_cents=current_spend.get("daily"),
        current_monthly_spend_cents=current_spend.get("monthly"),
    )


@router.get("/budgets", response_model=List[BudgetResponse])
async def list_budgets(
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> List[BudgetResponse]:
    """List all budgets for the tenant."""
    budgets = session.exec(
        select(CostBudget).where(
            CostBudget.tenant_id == tenant_id,
            CostBudget.is_active == True,
        )
    ).all()

    result = []
    for budget in budgets:
        current_spend = await _get_current_spend(session, tenant_id, budget.budget_type, budget.entity_id)
        result.append(
            BudgetResponse(
                id=budget.id,
                tenant_id=budget.tenant_id,
                budget_type=budget.budget_type,
                entity_id=budget.entity_id,
                daily_limit_cents=budget.daily_limit_cents,
                monthly_limit_cents=budget.monthly_limit_cents,
                warn_threshold_pct=budget.warn_threshold_pct,
                hard_limit_enabled=budget.hard_limit_enabled,
                is_active=budget.is_active,
                current_daily_spend_cents=current_spend.get("daily"),
                current_monthly_spend_cents=current_spend.get("monthly"),
            )
        )

    return result


# =============================================================================
# Helper Functions
# =============================================================================


async def _get_cost_summary(
    session: Session,
    tenant_id: str,
    period_start: datetime,
    period_end: datetime,
    days: int,
) -> CostSummary:
    """Get cost summary for a period."""
    result = session.execute(
        text(
            """
            SELECT
                COALESCE(SUM(cost_cents), 0) as total_cost,
                COALESCE(SUM(input_tokens), 0) as total_input,
                COALESCE(SUM(output_tokens), 0) as total_output,
                COUNT(*) as request_count
            FROM cost_records
            WHERE tenant_id = :tenant_id
              AND created_at >= :period_start
              AND created_at <= :period_end
        """
        ),
        {"tenant_id": tenant_id, "period_start": period_start, "period_end": period_end},
    ).first()

    total_cost = result[0] if result else 0
    total_input = result[1] if result else 0
    total_output = result[2] if result else 0
    request_count = result[3] if result else 0

    # Get budget
    budget = session.exec(
        select(CostBudget).where(
            CostBudget.tenant_id == tenant_id,
            CostBudget.budget_type == "tenant",
            CostBudget.entity_id == None,
            CostBudget.is_active == True,
        )
    ).first()

    budget_cents = budget.daily_limit_cents * days if budget and budget.daily_limit_cents else None
    budget_used_pct = (total_cost / budget_cents * 100) if budget_cents and budget_cents > 0 else None

    # Calculate days remaining at current rate
    daily_avg = total_cost / days if days > 0 else 0
    days_remaining = None
    if budget and budget.monthly_limit_cents and daily_avg > 0:
        remaining = budget.monthly_limit_cents - total_cost
        days_remaining = remaining / daily_avg if remaining > 0 else 0

    return CostSummary(
        tenant_id=tenant_id,
        period_start=period_start,
        period_end=period_end,
        total_cost_cents=total_cost,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        request_count=request_count,
        budget_cents=budget_cents,
        budget_used_pct=budget_used_pct,
        days_remaining_at_current_rate=days_remaining,
    )


async def _get_costs_by_feature(
    session: Session,
    tenant_id: str,
    period_start: datetime,
    total_cost: float,
) -> List[CostByFeature]:
    """Get costs grouped by feature tag."""
    results = session.execute(
        text(
            """
            SELECT
                COALESCE(cr.feature_tag, 'unclassified') as feature_tag,
                ft.display_name,
                ft.budget_cents,
                COALESCE(SUM(cr.cost_cents), 0) as total_cost,
                COUNT(*) as request_count
            FROM cost_records cr
            LEFT JOIN feature_tags ft ON cr.feature_tag = ft.tag AND cr.tenant_id = ft.tenant_id
            WHERE cr.tenant_id = :tenant_id AND cr.created_at >= :period_start
            GROUP BY cr.feature_tag, ft.display_name, ft.budget_cents
            ORDER BY total_cost DESC
        """
        ),
        {"tenant_id": tenant_id, "period_start": period_start},
    ).all()

    return [
        CostByFeature(
            feature_tag=row[0],
            display_name=row[1],
            total_cost_cents=row[3],
            request_count=row[4],
            pct_of_total=(row[3] / total_cost * 100) if total_cost > 0 else 0,
            budget_cents=row[2],
            budget_used_pct=(row[3] / row[2] * 100) if row[2] and row[2] > 0 else None,
        )
        for row in results
    ]


async def _get_costs_by_user(
    session: Session,
    tenant_id: str,
    period_start: datetime,
    total_cost: float,
) -> List[CostByUser]:
    """Get costs grouped by user with anomaly detection."""
    # Get current period costs by user
    results = session.execute(
        text(
            """
            SELECT
                COALESCE(user_id, 'anonymous') as user_id,
                COALESCE(SUM(cost_cents), 0) as total_cost,
                COUNT(*) as request_count
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :period_start
            GROUP BY user_id
            ORDER BY total_cost DESC
        """
        ),
        {"tenant_id": tenant_id, "period_start": period_start},
    ).all()

    # Calculate average to detect anomalies (user spending > 2x average)
    if not results:
        return []

    avg_cost = sum(row[1] for row in results) / len(results)

    return [
        CostByUser(
            user_id=row[0],
            total_cost_cents=row[1],
            request_count=row[2],
            pct_of_total=(row[1] / total_cost * 100) if total_cost > 0 else 0,
            is_anomaly=row[1] > avg_cost * 2,
            anomaly_message=f"Spending {row[1] / avg_cost:.1f}x average" if row[1] > avg_cost * 2 else None,
        )
        for row in results
    ]


async def _get_costs_by_model(
    session: Session,
    tenant_id: str,
    period_start: datetime,
    total_cost: float,
) -> List[CostByModel]:
    """Get costs grouped by model."""
    results = session.execute(
        text(
            """
            SELECT
                model,
                COALESCE(SUM(cost_cents), 0) as total_cost,
                COALESCE(SUM(input_tokens), 0) as total_input,
                COALESCE(SUM(output_tokens), 0) as total_output,
                COUNT(*) as request_count
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :period_start
            GROUP BY model
            ORDER BY total_cost DESC
        """
        ),
        {"tenant_id": tenant_id, "period_start": period_start},
    ).all()

    return [
        CostByModel(
            model=row[0],
            total_cost_cents=row[1],
            total_input_tokens=row[2],
            total_output_tokens=row[3],
            request_count=row[4],
            pct_of_total=(row[1] / total_cost * 100) if total_cost > 0 else 0,
        )
        for row in results
    ]


async def _get_recent_anomalies(
    session: Session,
    tenant_id: str,
    days: int = 7,
    include_resolved: bool = False,
) -> List[CostAnomalyResponse]:
    """Get recent anomalies."""
    cutoff = utc_now() - timedelta(days=days)

    query = select(CostAnomaly).where(
        CostAnomaly.tenant_id == tenant_id,
        CostAnomaly.detected_at >= cutoff,
    )

    if not include_resolved:
        query = query.where(CostAnomaly.resolved == False)

    anomalies = session.exec(query.order_by(cast(Any, CostAnomaly.detected_at).desc())).all()

    return [
        CostAnomalyResponse(
            id=a.id,
            tenant_id=a.tenant_id,
            anomaly_type=a.anomaly_type,
            severity=a.severity,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            current_value_cents=a.current_value_cents,
            expected_value_cents=a.expected_value_cents,
            deviation_pct=a.deviation_pct,
            message=a.message,
            incident_id=a.incident_id,
            action_taken=a.action_taken,
            resolved=a.resolved,
            detected_at=a.detected_at,
        )
        for a in anomalies
    ]


async def _get_cost_projection(
    session: Session,
    tenant_id: str,
    lookback_days: int = 7,
    forecast_days: int = 7,
) -> CostProjection:
    """Calculate cost projection based on historical trend."""
    lookback_start = utc_now() - timedelta(days=lookback_days)

    # Get daily costs for the lookback period
    results = session.execute(
        text(
            """
            SELECT
                DATE(created_at) as day,
                COALESCE(SUM(cost_cents), 0) as daily_cost
            FROM cost_records
            WHERE tenant_id = :tenant_id AND created_at >= :lookback_start
            GROUP BY DATE(created_at)
            ORDER BY day
        """
        ),
        {"tenant_id": tenant_id, "lookback_start": lookback_start},
    ).all()

    if not results:
        return CostProjection(
            tenant_id=tenant_id,
            lookback_days=lookback_days,
            forecast_days=forecast_days,
            current_daily_avg_cents=0,
            projected_total_cents=0,
            monthly_projection_cents=0,
            budget_cents=None,
            days_until_budget_exhausted=None,
            trend="stable",
        )

    daily_costs = [row[1] for row in results]
    current_daily_avg = sum(daily_costs) / len(daily_costs)

    # Simple trend detection: compare first half to second half
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
    budget = session.exec(
        select(CostBudget).where(
            CostBudget.tenant_id == tenant_id,
            CostBudget.budget_type == "tenant",
            CostBudget.entity_id == None,
            CostBudget.is_active == True,
        )
    ).first()

    days_until_exhausted = None
    budget_cents = None
    if budget and budget.monthly_limit_cents and current_daily_avg > 0:
        budget_cents = budget.monthly_limit_cents
        # Get current month spend
        month_start = utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_spend = session.execute(
            text(
                """
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE tenant_id = :tenant_id AND created_at >= :month_start
            """
            ),
            {"tenant_id": tenant_id, "month_start": month_start},
        ).first()

        remaining = budget.monthly_limit_cents - (month_spend[0] if month_spend else 0)
        days_until_exhausted = remaining / current_daily_avg if remaining > 0 else 0

    return CostProjection(
        tenant_id=tenant_id,
        lookback_days=lookback_days,
        forecast_days=forecast_days,
        current_daily_avg_cents=current_daily_avg,
        projected_total_cents=projected_total,
        monthly_projection_cents=monthly_projection,
        budget_cents=budget_cents,
        days_until_budget_exhausted=days_until_exhausted,
        trend=trend,
    )


async def _get_current_spend(
    session: Session,
    tenant_id: str,
    budget_type: str,
    entity_id: Optional[str],
) -> dict:
    """Get current daily and monthly spend for a budget entity."""
    today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    where_clause = "tenant_id = :tenant_id"
    params = {"tenant_id": tenant_id, "today_start": today_start, "month_start": month_start}

    if budget_type == "feature":
        where_clause += " AND feature_tag = :entity_id"
        params["entity_id"] = entity_id
    elif budget_type == "user":
        where_clause += " AND user_id = :entity_id"
        params["entity_id"] = entity_id

    # Daily spend
    daily_result = session.execute(
        text(
            f"""
            SELECT COALESCE(SUM(cost_cents), 0)
            FROM cost_records
            WHERE {where_clause} AND created_at >= :today_start
        """
        ),
        params,
    ).first()

    # Monthly spend
    monthly_result = session.execute(
        text(
            f"""
            SELECT COALESCE(SUM(cost_cents), 0)
            FROM cost_records
            WHERE {where_clause} AND created_at >= :month_start
        """
        ),
        params,
    ).first()

    return {
        "daily": daily_result[0] if daily_result else 0,
        "monthly": monthly_result[0] if monthly_result else 0,
    }


# =============================================================================
# Anomaly Detection with M25 Integration
# =============================================================================


class AnomalyDetectionRequest(BaseModel):
    """Request to trigger anomaly detection."""

    escalate_to_m25: bool = Field(True, description="Whether to escalate HIGH/CRITICAL anomalies to M25 incident loop")


class AnomalyDetectionResponse(BaseModel):
    """Response from anomaly detection."""

    detected_count: int
    escalated_count: int
    anomalies: List[CostAnomalyResponse]
    escalated: List[dict] = []


@router.post("/anomalies/detect", response_model=AnomalyDetectionResponse)
async def trigger_anomaly_detection(
    request: AnomalyDetectionRequest = AnomalyDetectionRequest(),
    tenant_id: str = Depends(get_tenant_id),
    session: Session = Depends(get_session),
) -> AnomalyDetectionResponse:
    """
    Trigger anomaly detection for this tenant.

    This endpoint:
    1. Scans for USER_SPIKE, FEATURE_SPIKE, BUDGET_WARNING, BUDGET_EXCEEDED
    2. Persists detected anomalies to database
    3. Optionally escalates HIGH/CRITICAL anomalies to M25 incident loop

    M25 Integration:
    When escalate_to_m25=True (default), HIGH and CRITICAL anomalies are:
    - Converted to M25 incidents
    - Processed through the M25 loop (Pattern → Recovery → Policy → Routing)
    - Resulting in automated policies to prevent future cost anomalies
    """
    from app.services.cost_anomaly_detector import (
        run_anomaly_detection,
        run_anomaly_detection_with_m25,
    )

    if request.escalate_to_m25:
        # Try to get M25 dispatcher if available
        dispatcher = None
        try:
            from app.integrations.dispatcher import get_dispatcher

            dispatcher = get_dispatcher()
        except Exception:
            logger.warning("M25 dispatcher not available - anomalies will not be escalated")

        result = await run_anomaly_detection_with_m25(session, tenant_id, dispatcher)
        detected = result["detected"]
        escalated = result["escalated_to_m25"]
    else:
        detected = await run_anomaly_detection(session, tenant_id)
        escalated = []

    # Convert to response models
    anomaly_responses = [
        CostAnomalyResponse(
            id=a.id,
            tenant_id=a.tenant_id,
            anomaly_type=a.anomaly_type,
            severity=a.severity,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            current_value_cents=a.current_value_cents,
            expected_value_cents=a.expected_value_cents,
            deviation_pct=a.deviation_pct,
            threshold_pct=a.threshold_pct,
            message=a.message,
            incident_id=a.incident_id,
            action_taken=a.action_taken,
            resolved=a.resolved,
            resolved_at=a.resolved_at,
            detected_at=a.detected_at,
        )
        for a in detected
    ]

    logger.info(
        f"Anomaly detection for tenant {tenant_id}: detected={len(detected)}, escalated_to_m25={len(escalated)}"
    )

    return AnomalyDetectionResponse(
        detected_count=len(detected),
        escalated_count=len(escalated),
        anomalies=anomaly_responses,
        escalated=escalated,
    )
