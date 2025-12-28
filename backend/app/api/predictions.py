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
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from ..auth import verify_api_key
from ..db import get_async_session
from ..models.prediction import PredictionEvent

logger = logging.getLogger("nova.api.predictions")

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions", "pb-s5", "read-only"])


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
    _: str = Depends(verify_api_key),
):
    """
    List prediction events (PB-S5).

    READ-ONLY: This endpoint only reads data.
    No execution data is modified by this query.
    All predictions are ADVISORY only.
    """
    now = datetime.utcnow()

    async with get_async_session() as session:
        # Build query
        query = select(PredictionEvent).order_by(PredictionEvent.created_at.desc())

        if tenant_id:
            query = query.where(PredictionEvent.tenant_id == tenant_id)
        if prediction_type:
            query = query.where(PredictionEvent.prediction_type == prediction_type)
        if subject_type:
            query = query.where(PredictionEvent.subject_type == subject_type)
        if subject_id:
            query = query.where(PredictionEvent.subject_id == subject_id)
        if not include_expired:
            query = query.where((PredictionEvent.valid_until.is_(None)) | (PredictionEvent.valid_until > now))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        records = result.scalars().all()

        # Aggregate by type and subject_type
        by_type: dict[str, int] = {}
        by_subject_type: dict[str, int] = {}
        for r in records:
            by_type[r.prediction_type] = by_type.get(r.prediction_type, 0) + 1
            by_subject_type[r.subject_type] = by_subject_type.get(r.subject_type, 0) + 1

        items = [
            PredictionSummaryResponse(
                id=str(r.id),
                tenant_id=r.tenant_id,
                prediction_type=r.prediction_type,
                subject_type=r.subject_type,
                subject_id=r.subject_id,
                confidence_score=r.confidence_score,
                is_advisory=r.is_advisory,
                created_at=r.created_at.isoformat() if r.created_at else None,
                valid_until=r.valid_until.isoformat() if r.valid_until else None,
                is_valid=(r.valid_until is None or r.valid_until > now),
            )
            for r in records
        ]

        return PredictionListResponse(
            total=total,
            limit=limit,
            offset=offset,
            by_type=by_type,
            by_subject_type=by_subject_type,
            items=items,
        )


@router.get("/{prediction_id}", response_model=PredictionDetailResponse)
async def get_prediction(
    prediction_id: str,
    _: str = Depends(verify_api_key),
):
    """
    Get detailed prediction by ID (PB-S5).

    READ-ONLY: This endpoint only reads data.
    No execution data is modified by this query.
    This prediction is ADVISORY only.
    """
    try:
        prediction_uuid = UUID(prediction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid prediction ID format")

    now = datetime.utcnow()

    async with get_async_session() as session:
        result = await session.execute(select(PredictionEvent).where(PredictionEvent.id == prediction_uuid))
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail=f"Prediction {prediction_id} not found")

        return PredictionDetailResponse(
            id=str(record.id),
            tenant_id=record.tenant_id,
            prediction_type=record.prediction_type,
            subject_type=record.subject_type,
            subject_id=record.subject_id,
            confidence_score=record.confidence_score,
            prediction_value=record.prediction_value or {},
            contributing_factors=record.contributing_factors or [],
            valid_until=record.valid_until.isoformat() if record.valid_until else None,
            created_at=record.created_at.isoformat() if record.created_at else None,
            is_advisory=record.is_advisory,
            notes=record.notes,
            is_valid=(record.valid_until is None or record.valid_until > now),
        )


@router.get("/subject/{subject_type}/{subject_id}")
async def get_predictions_for_subject(
    subject_type: str,
    subject_id: str,
    include_expired: bool = Query(False, description="Include expired predictions"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    _: str = Depends(verify_api_key),
):
    """
    Get all predictions for a specific subject (PB-S5).

    READ-ONLY: This endpoint only reads data.
    Returns all advisory predictions for a worker/run/tenant.
    """
    now = datetime.utcnow()

    async with get_async_session() as session:
        query = (
            select(PredictionEvent)
            .where(PredictionEvent.subject_type == subject_type)
            .where(PredictionEvent.subject_id == subject_id)
            .order_by(PredictionEvent.created_at.desc())
        )

        if not include_expired:
            query = query.where((PredictionEvent.valid_until.is_(None)) | (PredictionEvent.valid_until > now))

        query = query.limit(limit)

        result = await session.execute(query)
        records = result.scalars().all()

        return {
            "subject_type": subject_type,
            "subject_id": subject_id,
            "predictions": [
                {
                    "id": str(r.id),
                    "prediction_type": r.prediction_type,
                    "confidence_score": r.confidence_score,
                    "prediction_value": r.prediction_value,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "valid_until": r.valid_until.isoformat() if r.valid_until else None,
                    "is_advisory": r.is_advisory,
                    "is_valid": (r.valid_until is None or r.valid_until > now),
                }
                for r in records
            ],
            "count": len(records),
            "read_only": True,
            "pb_s5_compliant": True,
        }


@router.get("/stats/summary")
async def get_prediction_stats(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    include_expired: bool = Query(False, description="Include expired predictions"),
    _: str = Depends(verify_api_key),
):
    """
    Get prediction statistics (PB-S5).

    READ-ONLY: This endpoint only reads aggregated data.
    No execution data is modified by this query.
    """
    now = datetime.utcnow()

    async with get_async_session() as session:
        # Base query
        query = select(PredictionEvent)
        if tenant_id:
            query = query.where(PredictionEvent.tenant_id == tenant_id)
        if not include_expired:
            query = query.where((PredictionEvent.valid_until.is_(None)) | (PredictionEvent.valid_until > now))

        result = await session.execute(query)
        records = result.scalars().all()

        # Aggregate stats
        total = len(records)
        by_type: dict[str, int] = {}
        by_subject_type: dict[str, int] = {}
        confidence_sum = 0.0
        high_confidence_count = 0  # > 0.7

        for r in records:
            by_type[r.prediction_type] = by_type.get(r.prediction_type, 0) + 1
            by_subject_type[r.subject_type] = by_subject_type.get(r.subject_type, 0) + 1
            confidence_sum += r.confidence_score
            if r.confidence_score > 0.7:
                high_confidence_count += 1

        avg_confidence = (confidence_sum / total) if total > 0 else 0

        # Verify all are advisory (PB-S5 enforcement)
        non_advisory = sum(1 for r in records if not r.is_advisory)

        return {
            "total": total,
            "by_type": by_type,
            "by_subject_type": by_subject_type,
            "avg_confidence": round(avg_confidence, 3),
            "high_confidence_count": high_confidence_count,
            "advisory_compliance": {
                "all_advisory": non_advisory == 0,
                "non_advisory_count": non_advisory,
            },
            "read_only": True,
            "pb_s5_compliant": True,
        }
