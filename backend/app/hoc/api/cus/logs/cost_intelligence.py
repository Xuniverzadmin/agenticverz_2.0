# capability_id: CAP-012
# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Cost intelligence API (attribution, anomaly actions)
# Callers: Console UI, SDK
# Allowed Imports: L3, L4, L5, L6
# Forbidden Imports: L1
# Reference: L2 first-principles purity migration — 0 session.execute calls in L2

"""
M26 Cost Intelligence API

Core Objective:
Every token spent is attributable to tenant -> user -> feature -> request.
Every anomaly must trigger an action, not a chart.

This is not reporting. This is CONTROL.

L2 PURITY:
- No session.execute() calls in this file
- All DB operations routed through L4 bridge -> L5 engine -> L6 driver
- L2 is thin: validation, response mapping, and routing only
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# L4 session dependency (L2 must not import sqlalchemy/sqlmodel/app.db directly)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_sync_session_dep
from app.hoc.cus.hoc_spine.services.time import utc_now

# L4 bridges for domain capabilities
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.analytics_bridge import (
    get_analytics_bridge,
)
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge import (
    get_logs_bridge,
)
from app.schemas.response import wrap_dict


def _get_cost_write_service(session):
    """Get cost write service via L4 analytics bridge (PIN-520 compliance)."""
    bridge = get_analytics_bridge()
    return bridge.cost_write_capability(session)


def _get_cost_intelligence_engine(session):
    """Get cost intelligence engine via L4 logs bridge (L2 purity migration)."""
    bridge = get_logs_bridge()
    return bridge.cost_intelligence_capability(session)


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


class CostProvenance(BaseModel):
    """Provenance metadata for cost interpretation panels."""

    aggregation: str = Field(..., description="Aggregation type (e.g., 'sum', 'count')")
    data_source: str = Field(..., description="Data source table/entity")
    computed_at: datetime = Field(..., description="When the data was computed")
    period_description: str = Field(..., description="Human-readable period description")


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
    provenance: CostProvenance = Field(..., description="Provenance metadata for interpretation")


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


# =============================================================================
# Provenance Envelope Response Models (ANALYTICS domain SDSR compliance)
# =============================================================================


class AnalyticsProvenance(BaseModel):
    """Provenance envelope for analytics interpretation panels.

    SDSR requires provenance metadata on all interpretation panels to ensure
    the UI can correctly display how data was derived.
    """

    sources: List[str] = Field(..., description="Data sources used (e.g., ['cost_records', 'feature_tags'])")
    window: str = Field(..., description="Time window (e.g., '24h', '7d', '30d')")
    aggregation: str = Field(..., description="Aggregation method (e.g., 'GROUP_BY:user', 'SUM')")
    generated_at: datetime = Field(..., description="When this data was computed")


class CostByUserEnvelope(BaseModel):
    """Envelope response for cost by user with provenance."""

    data: List[CostByUser]
    provenance: AnalyticsProvenance


class CostByModelEnvelope(BaseModel):
    """Envelope response for cost by model with provenance."""

    data: List[CostByModel]
    provenance: AnalyticsProvenance


class CostByFeatureEnvelope(BaseModel):
    """Envelope response for cost by feature with provenance."""

    data: List[CostByFeature]
    provenance: AnalyticsProvenance


class CostAnomaliesEnvelope(BaseModel):
    """Envelope response for cost anomalies with provenance."""

    data: List[CostAnomalyResponse]
    provenance: AnalyticsProvenance


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
    session=Depends(get_sync_session_dep),
) -> FeatureTagResponse:
    """
    Register a new feature tag.

    Feature tags are MANDATORY for cost attribution.
    No tag -> request defaulted to 'unclassified' (and flagged).
    """
    engine = _get_cost_intelligence_engine(session)

    # Check if tag already exists for this tenant
    if engine.check_feature_tag_exists(tenant_id, data.tag):
        raise HTTPException(status_code=409, detail=f"Feature tag '{data.tag}' already exists for this tenant")

    # Validate tag format (namespace.action)
    if "." not in data.tag:
        raise HTTPException(
            status_code=400, detail="Feature tag must be in namespace.action format (e.g., 'customer_support.chat')"
        )

    # Use write service for DB operations
    cost_service = _get_cost_write_service(session)
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
    session=Depends(get_sync_session_dep),
) -> List[FeatureTagResponse]:
    """List all feature tags for the tenant."""
    engine = _get_cost_intelligence_engine(session)
    tags = engine.list_feature_tags(tenant_id, include_inactive)

    return [
        FeatureTagResponse(
            id=tag["id"],
            tenant_id=tag["tenant_id"],
            tag=tag["tag"],
            display_name=tag["display_name"],
            description=tag["description"],
            budget_cents=tag["budget_cents"],
            is_active=tag["is_active"],
            created_at=tag["created_at"],
            updated_at=tag["updated_at"],
        )
        for tag in tags
    ]


@router.put("/features/{tag}", response_model=FeatureTagResponse)
async def update_feature_tag(
    tag: str,
    data: FeatureTagUpdate,
    tenant_id: str = Depends(get_tenant_id),
    session=Depends(get_sync_session_dep),
) -> FeatureTagResponse:
    """Update a feature tag."""
    engine = _get_cost_intelligence_engine(session)

    # Check existence
    existing = engine.get_feature_tag(tenant_id, tag)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Feature tag '{tag}' not found")

    # Update via engine
    updated = engine.update_feature_tag(
        tenant_id=tenant_id,
        tag=tag,
        display_name=data.display_name,
        description=data.description,
        budget_cents=data.budget_cents,
        is_active=data.is_active,
    )

    return FeatureTagResponse(
        id=updated["id"],
        tenant_id=updated["tenant_id"],
        tag=updated["tag"],
        display_name=updated["display_name"],
        description=updated["description"],
        budget_cents=updated["budget_cents"],
        is_active=updated["is_active"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )


# =============================================================================
# Cost Recording Endpoint
# =============================================================================


@router.post("/record")
async def record_cost(
    data: CostRecordCreate,
    tenant_id: str = Depends(get_tenant_id),
    session=Depends(get_sync_session_dep),
) -> dict:
    """
    Record a cost entry.

    This is called internally after each LLM invocation.
    Feature tag validation: if tag doesn't exist, default to 'unclassified'.
    """
    engine = _get_cost_intelligence_engine(session)
    feature_tag = data.feature_tag

    # Validate feature tag if provided
    if feature_tag and feature_tag != "unclassified":
        existing_tag = engine.get_active_feature_tag(tenant_id, feature_tag)
        if not existing_tag:
            logger.warning(f"Unknown feature tag '{feature_tag}' - defaulting to 'unclassified'")
            feature_tag = "unclassified"

    # Use write service for DB operations
    cost_service = _get_cost_write_service(session)
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

    return wrap_dict({"id": record.id, "status": "recorded"})


# =============================================================================
# Dashboard Endpoints
# =============================================================================


@router.get("/dashboard", response_model=CostDashboard)
async def get_cost_dashboard(
    period: str = Query("24h", regex="^(24h|7d|30d)$"),
    tenant_id: str = Depends(get_tenant_id),
    session=Depends(get_sync_session_dep),
) -> CostDashboard:
    """
    Get complete cost dashboard.

    If a CTO can't answer "what burned money yesterday?" in 10 seconds, this failed.
    """
    engine = _get_cost_intelligence_engine(session)

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

    # Get summary via engine
    summary_data = engine.get_cost_summary(tenant_id, period_start, now, days)
    summary = CostSummary(
        tenant_id=summary_data["tenant_id"],
        period_start=summary_data["period_start"],
        period_end=summary_data["period_end"],
        total_cost_cents=summary_data["total_cost_cents"],
        total_input_tokens=summary_data["total_input_tokens"],
        total_output_tokens=summary_data["total_output_tokens"],
        request_count=summary_data["request_count"],
        budget_cents=summary_data["budget_cents"],
        budget_used_pct=summary_data["budget_used_pct"],
        days_remaining_at_current_rate=summary_data["days_remaining_at_current_rate"],
        provenance=CostProvenance(**summary_data["provenance"]),
    )

    # Get by feature
    by_feature_data = engine.get_costs_by_feature(tenant_id, period_start, summary.total_cost_cents)
    by_feature = [CostByFeature(**item) for item in by_feature_data]

    # Get by user
    by_user_data = engine.get_costs_by_user(tenant_id, period_start, summary.total_cost_cents)
    by_user = [CostByUser(**item) for item in by_user_data]

    # Get by model
    by_model_data = engine.get_costs_by_model(tenant_id, period_start, summary.total_cost_cents)
    by_model = [CostByModel(**item) for item in by_model_data]

    # Get anomalies
    anomalies_data = engine.get_recent_anomalies(tenant_id, days=days)
    anomalies = [CostAnomalyResponse(**item) for item in anomalies_data]

    # Get projection
    projection_data = engine.get_cost_projection(tenant_id, lookback_days=7, forecast_days=7)
    projection = CostProjection(**projection_data)

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
    session=Depends(get_sync_session_dep),
) -> CostSummary:
    """Get cost summary for the period."""
    engine = _get_cost_intelligence_engine(session)

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

    summary_data = engine.get_cost_summary(tenant_id, period_start, now, days)
    return CostSummary(
        tenant_id=summary_data["tenant_id"],
        period_start=summary_data["period_start"],
        period_end=summary_data["period_end"],
        total_cost_cents=summary_data["total_cost_cents"],
        total_input_tokens=summary_data["total_input_tokens"],
        total_output_tokens=summary_data["total_output_tokens"],
        request_count=summary_data["request_count"],
        budget_cents=summary_data["budget_cents"],
        budget_used_pct=summary_data["budget_used_pct"],
        days_remaining_at_current_rate=summary_data["days_remaining_at_current_rate"],
        provenance=CostProvenance(**summary_data["provenance"]),
    )


@router.get("/by-feature", response_model=CostByFeatureEnvelope)
async def get_costs_by_feature(
    period: str = Query("24h", regex="^(24h|7d|30d)$"),
    tenant_id: str = Depends(get_tenant_id),
    session=Depends(get_sync_session_dep),
) -> CostByFeatureEnvelope:
    """Get cost breakdown by feature tag.

    Returns envelope with provenance for SDSR ANALYTICS domain compliance.
    """
    engine = _get_cost_intelligence_engine(session)
    now = utc_now()
    period_start = (
        now - timedelta(hours=24)
        if period == "24h"
        else now - timedelta(days=7)
        if period == "7d"
        else now - timedelta(days=30)
    )

    # Get total for percentage calculation
    total_cost = engine.get_total_cost(tenant_id, period_start)
    data = engine.get_costs_by_feature(tenant_id, period_start, total_cost)

    return CostByFeatureEnvelope(
        data=[CostByFeature(**item) for item in data],
        provenance=AnalyticsProvenance(
            sources=["cost_records", "feature_tags"],
            window=period,
            aggregation="GROUP_BY:feature_tag",
            generated_at=now,
        ),
    )


@router.get("/by-user", response_model=CostByUserEnvelope)
async def get_costs_by_user(
    period: str = Query("24h", regex="^(24h|7d|30d)$"),
    tenant_id: str = Depends(get_tenant_id),
    session=Depends(get_sync_session_dep),
) -> CostByUserEnvelope:
    """Get cost breakdown by user with anomaly detection.

    Returns envelope with provenance for SDSR ANALYTICS domain compliance.
    """
    engine = _get_cost_intelligence_engine(session)
    now = utc_now()
    period_start = (
        now - timedelta(hours=24)
        if period == "24h"
        else now - timedelta(days=7)
        if period == "7d"
        else now - timedelta(days=30)
    )

    # Get total for percentage calculation
    total_cost = engine.get_total_cost(tenant_id, period_start)
    data = engine.get_costs_by_user(tenant_id, period_start, total_cost)

    return CostByUserEnvelope(
        data=[CostByUser(**item) for item in data],
        provenance=AnalyticsProvenance(
            sources=["cost_records"],
            window=period,
            aggregation="GROUP_BY:user",
            generated_at=now,
        ),
    )


@router.get("/by-model", response_model=CostByModelEnvelope)
async def get_costs_by_model(
    period: str = Query("24h", regex="^(24h|7d|30d)$"),
    tenant_id: str = Depends(get_tenant_id),
    session=Depends(get_sync_session_dep),
) -> CostByModelEnvelope:
    """Get cost breakdown by model.

    Returns envelope with provenance for SDSR ANALYTICS domain compliance.
    """
    engine = _get_cost_intelligence_engine(session)
    now = utc_now()
    period_start = (
        now - timedelta(hours=24)
        if period == "24h"
        else now - timedelta(days=7)
        if period == "7d"
        else now - timedelta(days=30)
    )

    total_cost = engine.get_total_cost(tenant_id, period_start)
    data = engine.get_costs_by_model(tenant_id, period_start, total_cost)

    return CostByModelEnvelope(
        data=[CostByModel(**item) for item in data],
        provenance=AnalyticsProvenance(
            sources=["cost_records"],
            window=period,
            aggregation="GROUP_BY:model",
            generated_at=now,
        ),
    )


@router.get("/anomalies", response_model=CostAnomaliesEnvelope)
async def get_anomalies(
    days: int = Query(7, ge=1, le=90),
    include_resolved: bool = False,
    tenant_id: str = Depends(get_tenant_id),
    session=Depends(get_sync_session_dep),
) -> CostAnomaliesEnvelope:
    """Get detected cost anomalies.

    Returns envelope with provenance for SDSR ANALYTICS domain compliance.
    """
    engine = _get_cost_intelligence_engine(session)
    now = utc_now()
    data = engine.get_recent_anomalies(tenant_id, days, include_resolved)

    # Build window description
    window = f"{days}d" if days != 1 else "24h"

    return CostAnomaliesEnvelope(
        data=[CostAnomalyResponse(**item) for item in data],
        provenance=AnalyticsProvenance(
            sources=["cost_anomalies", "cost_records"],
            window=window,
            aggregation="DETECT:anomaly",
            generated_at=now,
        ),
    )


@router.get("/projection", response_model=CostProjection)
async def get_projection(
    lookback_days: int = Query(7, ge=1, le=30),
    forecast_days: int = Query(7, ge=1, le=30),
    tenant_id: str = Depends(get_tenant_id),
    session=Depends(get_sync_session_dep),
) -> CostProjection:
    """Get cost projection based on historical data."""
    engine = _get_cost_intelligence_engine(session)
    projection_data = engine.get_cost_projection(tenant_id, lookback_days, forecast_days)
    return CostProjection(**projection_data)


# =============================================================================
# Budget Endpoints
# =============================================================================


@router.post("/budgets", response_model=BudgetResponse)
async def create_or_update_budget(
    data: BudgetCreate,
    tenant_id: str = Depends(get_tenant_id),
    session=Depends(get_sync_session_dep),
) -> BudgetResponse:
    """Create or update a budget."""
    if data.budget_type not in ("tenant", "feature", "user"):
        raise HTTPException(status_code=400, detail="budget_type must be 'tenant', 'feature', or 'user'")

    if data.budget_type in ("feature", "user") and not data.entity_id:
        raise HTTPException(status_code=400, detail=f"entity_id required for {data.budget_type} budget")

    engine = _get_cost_intelligence_engine(session)

    # Find existing budget
    existing = engine.get_budget_by_type(tenant_id, data.budget_type, data.entity_id)

    if existing:
        # Update existing budget
        budget = engine.update_budget(
            budget_id=existing["id"],
            daily_limit_cents=data.daily_limit_cents,
            monthly_limit_cents=data.monthly_limit_cents,
            warn_threshold_pct=data.warn_threshold_pct,
            hard_limit_enabled=data.hard_limit_enabled,
        )
    else:
        # Create new budget
        budget = engine.create_budget(
            tenant_id=tenant_id,
            budget_type=data.budget_type,
            entity_id=data.entity_id,
            daily_limit_cents=data.daily_limit_cents,
            monthly_limit_cents=data.monthly_limit_cents,
            warn_threshold_pct=data.warn_threshold_pct,
            hard_limit_enabled=data.hard_limit_enabled,
        )

    # Get current spend
    current_spend = engine.get_current_spend(tenant_id, data.budget_type, data.entity_id)

    return BudgetResponse(
        id=budget["id"],
        tenant_id=budget["tenant_id"],
        budget_type=budget["budget_type"],
        entity_id=budget["entity_id"],
        daily_limit_cents=budget["daily_limit_cents"],
        monthly_limit_cents=budget["monthly_limit_cents"],
        warn_threshold_pct=budget["warn_threshold_pct"],
        hard_limit_enabled=budget["hard_limit_enabled"],
        is_active=budget["is_active"],
        current_daily_spend_cents=current_spend.get("daily"),
        current_monthly_spend_cents=current_spend.get("monthly"),
    )


@router.get("/budgets", response_model=List[BudgetResponse])
async def list_budgets(
    tenant_id: str = Depends(get_tenant_id),
    session=Depends(get_sync_session_dep),
) -> List[BudgetResponse]:
    """List all budgets for the tenant."""
    engine = _get_cost_intelligence_engine(session)
    budgets = engine.list_budgets(tenant_id)

    result = []
    for budget in budgets:
        current_spend = engine.get_current_spend(tenant_id, budget["budget_type"], budget["entity_id"])
        result.append(
            BudgetResponse(
                id=budget["id"],
                tenant_id=budget["tenant_id"],
                budget_type=budget["budget_type"],
                entity_id=budget["entity_id"],
                daily_limit_cents=budget["daily_limit_cents"],
                monthly_limit_cents=budget["monthly_limit_cents"],
                warn_threshold_pct=budget["warn_threshold_pct"],
                hard_limit_enabled=budget["hard_limit_enabled"],
                is_active=budget["is_active"],
                current_daily_spend_cents=current_spend.get("daily"),
                current_monthly_spend_cents=current_spend.get("monthly"),
            )
        )

    return wrap_dict({"items": [r.model_dump() for r in result], "total": len(result)})


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
    session=Depends(get_sync_session_dep),
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
    - Processed through the M25 loop (Pattern -> Recovery -> Policy -> Routing)
    - Resulting in automated policies to prevent future cost anomalies
    """
    # PIN-521: Route all detection through L4 coordinator (no direct L5 imports in L2)
    from app.hoc.cus.hoc_spine.orchestrator.coordinators.anomaly_incident_coordinator import (
        get_anomaly_incident_coordinator,
    )

    coordinator = get_anomaly_incident_coordinator()

    if request.escalate_to_m25:
        # MANDATORY GOVERNANCE: HIGH anomalies create incidents or crash
        # No optional dispatcher. Governance is not negotiable.
        # PIN-511: Use L4 coordinator instead of deprecated direct call
        result = await coordinator.detect_and_ingest(session, tenant_id)
        detected = result["detected"]
        escalated = result["incidents_created"]
    else:
        # PIN-521: Use coordinator's detect_only for detection without escalation
        detected = await coordinator.detect_only(session, tenant_id)
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
            message=a.message,
            incident_id=a.incident_id,
            action_taken=a.action_taken,
            resolved=a.resolved,
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
