# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: PB-S5 Predictions API (READ-ONLY)
# Callers: Customer Console
# Allowed Imports: L3, L4, L5, L6
# Forbidden Imports: L1
# Reference: PB-S5
"""
PB-S5 Predictions API (READ-ONLY)

Exposes prediction_events data for observability without modification.

PB-S5 Contract:
- Predictions are advisory only
- Predictions have zero side-effects
- Predictions never modify execution, scheduling, or history
- Rule: Advise, don't influence

READ_ONLY = True

O1: API endpoint exists ✓
O2: List visible with pagination ✓
O3: Detail accessible ✓
O4: Execution unchanged ✓ (no POST/PUT/DELETE)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth.authority import AuthorityResult, emit_authority_audit, require_predictions_read
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_operation_registry,
    get_session_dep,
    OperationContext,
)
from app.schemas.response import wrap_dict

logger = logging.getLogger("nova.api.predictions")

router = APIRouter(prefix="/predictions", tags=["predictions", "pb-s5", "read-only"])


# =============================================================================
# Response Models
# =============================================================================


class PredictionSummaryResponse(BaseModel):
    """Summary of a prediction event."""

    id: str
    tenant_id: str
    prediction_type: str
    subject_type: str
    subject_id: str
    confidence_score: float
    is_advisory: bool
    created_at: Optional[str]
    valid_until: Optional[str]
    is_valid: bool


class PredictionListResponse(BaseModel):
    """Paginated list of predictions."""

    total: int
    limit: int
    offset: int
    by_type: dict
    by_subject_type: dict
    items: list[PredictionSummaryResponse]


class PredictionDetailResponse(BaseModel):
    """Detailed prediction event record."""

    id: str
    tenant_id: str
    prediction_type: str
    subject_type: str
    subject_id: str
    confidence_score: float
    prediction_value: dict
    contributing_factors: list
    valid_until: Optional[str]
    created_at: Optional[str]
    is_advisory: bool
    notes: Optional[str]
    is_valid: bool


# =============================================================================
# READ-ONLY Endpoints (No POST/PUT/DELETE)
# =============================================================================


@router.get("", response_model=PredictionListResponse)
async def list_predictions(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    prediction_type: Optional[str] = Query(None, description="Filter by type (failure_likelihood/cost_overrun)"),
    subject_type: Optional[str] = Query(None, description="Filter by subject type (worker/run/tenant)"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    include_expired: bool = Query(False, description="Include expired predictions"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session=Depends(get_session_dep),
    auth: AuthorityResult = Depends(require_predictions_read),
):
    """
    List prediction events (PB-S5).

    READ-ONLY: This endpoint only reads data.
    No execution data is modified by this query.
    All predictions are ADVISORY only.
    """
    # Emit authority audit for capability access
    await emit_authority_audit(auth, "predictions", subject_id="list")

    registry = get_operation_registry()
    result = await registry.execute(
        "analytics.prediction_read",
        OperationContext(
            session=session,
            tenant_id=tenant_id or "system",
            params={
                "method": "list",
                "prediction_type": prediction_type,
                "subject_type": subject_type,
                "subject_id": subject_id,
                "include_expired": include_expired,
                "limit": limit,
                "offset": offset,
            },
        ),
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    data = result.data
    items = [
        PredictionSummaryResponse(
            id=item["id"],
            tenant_id=item["tenant_id"],
            prediction_type=item["prediction_type"],
            subject_type=item["subject_type"],
            subject_id=item["subject_id"],
            confidence_score=item["confidence_score"],
            is_advisory=item["is_advisory"],
            created_at=item["created_at"],
            valid_until=item["expires_at"],
            is_valid=item["is_valid"],
        )
        for item in data["items"]
    ]

    return PredictionListResponse(
        total=data["total"],
        limit=data["limit"],
        offset=data["offset"],
        by_type=data["by_type"],
        by_subject_type=data["by_subject_type"],
        items=items,
    )


@router.get("/{prediction_id}", response_model=PredictionDetailResponse)
async def get_prediction(
    prediction_id: str,
    session=Depends(get_session_dep),
    auth: AuthorityResult = Depends(require_predictions_read),
):
    """
    Get detailed prediction by ID (PB-S5).

    READ-ONLY: This endpoint only reads data.
    No execution data is modified by this query.
    This prediction is ADVISORY only.
    """
    # Emit authority audit for capability access
    await emit_authority_audit(auth, "predictions", subject_id=prediction_id)

    registry = get_operation_registry()
    result = await registry.execute(
        "analytics.prediction_read",
        OperationContext(
            session=session,
            tenant_id="system",
            params={
                "method": "get",
                "prediction_id": prediction_id,
            },
        ),
    )

    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=f"Prediction {prediction_id} not found")
        if "Invalid" in (result.error or ""):
            raise HTTPException(status_code=400, detail="Invalid prediction ID format")
        raise HTTPException(status_code=500, detail=result.error)

    data = result.data
    return PredictionDetailResponse(
        id=data["id"],
        tenant_id=data["tenant_id"],
        prediction_type=data["prediction_type"],
        subject_type=data["subject_type"],
        subject_id=data["subject_id"],
        confidence_score=data["confidence_score"],
        prediction_value=data["prediction_value"],
        contributing_factors=data["contributing_factors"],
        valid_until=data["expires_at"],
        created_at=data["created_at"],
        is_advisory=data["is_advisory"],
        notes=data["notes"],
        is_valid=data["is_valid"],
    )


@router.get("/subject/{subject_type}/{subject_id}")
async def get_predictions_for_subject(
    subject_type: str,
    subject_id: str,
    include_expired: bool = Query(False, description="Include expired predictions"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    session=Depends(get_session_dep),
    auth: AuthorityResult = Depends(require_predictions_read),
):
    """
    Get all predictions for a specific subject (PB-S5).

    READ-ONLY: This endpoint only reads data.
    Returns all advisory predictions for a worker/run/tenant.
    """
    # Emit authority audit for capability access
    await emit_authority_audit(auth, "predictions", subject_id=f"{subject_type}:{subject_id}")

    registry = get_operation_registry()
    result = await registry.execute(
        "analytics.prediction_read",
        OperationContext(
            session=session,
            tenant_id="system",
            params={
                "method": "for_subject",
                "subject_type": subject_type,
                "subject_id": subject_id,
                "include_expired": include_expired,
                "limit": limit,
            },
        ),
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return wrap_dict(result.data)


@router.get("/stats/summary")
async def get_prediction_stats(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    include_expired: bool = Query(False, description="Include expired predictions"),
    session=Depends(get_session_dep),
    auth: AuthorityResult = Depends(require_predictions_read),
):
    """
    Get prediction statistics (PB-S5).

    READ-ONLY: This endpoint only reads aggregated data.
    No execution data is modified by this query.
    """
    # Emit authority audit for capability access
    await emit_authority_audit(auth, "predictions", subject_id="stats")

    registry = get_operation_registry()
    result = await registry.execute(
        "analytics.prediction_read",
        OperationContext(
            session=session,
            tenant_id=tenant_id or "system",
            params={
                "method": "stats",
                "include_expired": include_expired,
            },
        ),
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return wrap_dict(result.data)
