# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: PB-S3 Pattern Feedback API (READ-ONLY)
# Callers: Customer Console
# Allowed Imports: L3, L4, L5, L6
# Forbidden Imports: L1
# Reference: PB-S3
"""
PB-S3 Pattern Feedback API (READ-ONLY)

Exposes pattern_feedback data for observability without modification.

PB-S3 Contract:
- Feedback observes but never mutates
- Provenance references runs (read-only)
- No execution data modification allowed

READ_ONLY = True

O1: API endpoint exists ✓
O2: List visible with pagination ✓
O3: Detail accessible ✓
O4: Execution unchanged ✓ (no POST/PUT/DELETE)
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from ..auth import verify_api_key
from ..db import get_async_session
from ..models.feedback import PatternFeedback
from ..schemas.response import wrap_dict

logger = logging.getLogger("nova.api.feedback")

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback", "pb-s3", "read-only"])


# =============================================================================
# Response Models
# =============================================================================


class FeedbackSummaryResponse(BaseModel):
    """Summary of a feedback record."""

    id: str
    tenant_id: str
    pattern_type: str
    severity: str
    description: str
    signature: Optional[str]
    occurrence_count: int
    detected_at: Optional[str]
    acknowledged: bool
    provenance_count: int


class FeedbackListResponse(BaseModel):
    """Paginated list of feedback records."""

    total: int
    limit: int
    offset: int
    by_type: dict
    by_severity: dict
    items: list[FeedbackSummaryResponse]


class FeedbackDetailResponse(BaseModel):
    """Detailed feedback record."""

    id: str
    tenant_id: str
    pattern_type: str
    severity: str
    description: str
    signature: Optional[str]
    provenance: list
    occurrence_count: int
    time_window_minutes: Optional[int]
    threshold_used: Optional[str]
    extra_data: Optional[dict]
    detected_at: Optional[str]
    created_at: Optional[str]
    acknowledged: bool
    acknowledged_at: Optional[str]
    acknowledged_by: Optional[str]


# =============================================================================
# READ-ONLY Endpoints (No POST/PUT/DELETE)
# =============================================================================


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgement status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    _: str = Depends(verify_api_key),
):
    """
    List pattern feedback records (PB-S3).

    READ-ONLY: This endpoint only reads data.
    No execution data is modified by this query.
    """
    async with get_async_session() as session:
        # Build query
        query = select(PatternFeedback).order_by(PatternFeedback.detected_at.desc())

        if tenant_id:
            query = query.where(PatternFeedback.tenant_id == tenant_id)
        if pattern_type:
            query = query.where(PatternFeedback.pattern_type == pattern_type)
        if severity:
            query = query.where(PatternFeedback.severity == severity)
        if acknowledged is not None:
            query = query.where(PatternFeedback.acknowledged == acknowledged)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        records = result.scalars().all()

        # Aggregate by type and severity
        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for r in records:
            by_type[r.pattern_type] = by_type.get(r.pattern_type, 0) + 1
            by_severity[r.severity] = by_severity.get(r.severity, 0) + 1

        items = [
            FeedbackSummaryResponse(
                id=str(r.id),
                tenant_id=r.tenant_id,
                pattern_type=r.pattern_type,
                severity=r.severity,
                description=r.description[:200] if r.description else "",
                signature=r.signature,
                occurrence_count=r.occurrence_count,
                detected_at=r.detected_at.isoformat() if r.detected_at else None,
                acknowledged=r.acknowledged,
                provenance_count=len(r.provenance) if r.provenance else 0,
            )
            for r in records
        ]

        return FeedbackListResponse(
            total=total,
            limit=limit,
            offset=offset,
            by_type=by_type,
            by_severity=by_severity,
            items=items,
        )


@router.get("/{feedback_id}", response_model=FeedbackDetailResponse)
async def get_feedback(
    feedback_id: str,
    _: str = Depends(verify_api_key),
):
    """
    Get detailed feedback record by ID (PB-S3).

    READ-ONLY: This endpoint only reads data.
    No execution data is modified by this query.
    """
    try:
        feedback_uuid = UUID(feedback_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid feedback ID format")

    async with get_async_session() as session:
        result = await session.execute(select(PatternFeedback).where(PatternFeedback.id == feedback_uuid))
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")

        return FeedbackDetailResponse(
            id=str(record.id),
            tenant_id=record.tenant_id,
            pattern_type=record.pattern_type,
            severity=record.severity,
            description=record.description,
            signature=record.signature,
            provenance=record.provenance or [],
            occurrence_count=record.occurrence_count,
            time_window_minutes=record.time_window_minutes,
            threshold_used=record.threshold_used,
            extra_data=record.extra_data,
            detected_at=record.detected_at.isoformat() if record.detected_at else None,
            created_at=record.created_at.isoformat() if record.created_at else None,
            acknowledged=record.acknowledged,
            acknowledged_at=record.acknowledged_at.isoformat() if record.acknowledged_at else None,
            acknowledged_by=record.acknowledged_by,
        )


@router.get("/stats/summary")
async def get_feedback_stats(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    _: str = Depends(verify_api_key),
):
    """
    Get feedback statistics summary (PB-S3).

    READ-ONLY: This endpoint only reads aggregated data.
    No execution data is modified by this query.
    """
    async with get_async_session() as session:
        # Base query
        query = select(PatternFeedback)
        if tenant_id:
            query = query.where(PatternFeedback.tenant_id == tenant_id)

        result = await session.execute(query)
        records = result.scalars().all()

        # Aggregate stats
        total = len(records)
        acknowledged_count = sum(1 for r in records if r.acknowledged)
        unacknowledged_count = total - acknowledged_count

        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for r in records:
            by_type[r.pattern_type] = by_type.get(r.pattern_type, 0) + 1
            by_severity[r.severity] = by_severity.get(r.severity, 0) + 1

        return wrap_dict({
            "total": total,
            "acknowledged": acknowledged_count,
            "unacknowledged": unacknowledged_count,
            "by_type": by_type,
            "by_severity": by_severity,
            "read_only": True,
            "pb_s3_compliant": True,
        })
