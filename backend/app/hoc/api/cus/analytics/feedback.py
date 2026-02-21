# capability_id: CAP-012
# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: PB-S3 Pattern Feedback API (READ-ONLY)
# Callers: Customer Console
# Allowed Imports: L4 (registry)
# Forbidden Imports: L1, L5, L6, sqlalchemy
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

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import verify_api_key
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_async_session_context,
    get_operation_registry,
    OperationContext,
)
from app.schemas.response import wrap_dict

from datetime import datetime

logger = logging.getLogger("nova.api.feedback")

router = APIRouter(prefix="/feedback", tags=["feedback", "pb-s3", "read-only"])


# =============================================================================
# UC-MON Determinism: as_of Contract
# =============================================================================


def _normalize_as_of(as_of: Optional[str]) -> str:
    """
    Normalize as_of deterministic read watermark.

    UC-MON Contract:
    - If provided: validate ISO-8601 UTC format
    - If absent: generate once per request (server timestamp)
    - Same as_of + same filters = stable results
    """
    if as_of is not None:
        try:
            datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_as_of", "message": "as_of must be ISO-8601 UTC"},
            )
        return as_of
    return datetime.utcnow().isoformat() + "Z"


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
    # UC-MON Determinism
    as_of: Optional[str] = Query(None, description="Deterministic read watermark (ISO-8601 UTC)"),
    _: str = Depends(verify_api_key),
):
    """
    List pattern feedback records (PB-S3).

    READ-ONLY: This endpoint only reads data.
    No execution data is modified by this query.
    """
    effective_as_of = _normalize_as_of(as_of)

    async with get_async_session_context() as session:
        registry = get_operation_registry()
        result = await registry.execute(
            "analytics.feedback",
            OperationContext(
                session=session,
                tenant_id=tenant_id or "system",
                params={
                    "method": "list_feedback",
                    "as_of": effective_as_of,
                    "pattern_type": pattern_type,
                    "severity": severity,
                    "acknowledged": acknowledged,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        data = result.data
        items = [
            FeedbackSummaryResponse(**item)
            for item in data["items"]
        ]

        return FeedbackListResponse(
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
            by_type=data["by_type"],
            by_severity=data["by_severity"],
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
    async with get_async_session_context() as session:
        registry = get_operation_registry()
        result = await registry.execute(
            "analytics.feedback",
            OperationContext(
                session=session,
                tenant_id="system",
                params={
                    "method": "get_feedback",
                    "feedback_id": feedback_id,
                },
            ),
        )

        if not result.success:
            if result.error_code == "NOT_FOUND":
                raise HTTPException(status_code=404, detail=result.error)
            if result.error_code == "INVALID_FORMAT":
                raise HTTPException(status_code=400, detail=result.error)
            raise HTTPException(status_code=500, detail=result.error)

        return FeedbackDetailResponse(**result.data)


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
    async with get_async_session_context() as session:
        registry = get_operation_registry()
        result = await registry.execute(
            "analytics.feedback",
            OperationContext(
                session=session,
                tenant_id=tenant_id or "system",
                params={
                    "method": "get_feedback_stats",
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return wrap_dict(result.data)
