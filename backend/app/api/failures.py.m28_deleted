# api/failures.py
"""
M9 Failure Catalog & Recovery Tracking API Endpoints

Provides REST API for:
1. GET /api/v1/failures - List failures with filters
2. GET /api/v1/failures/{id} - Get failure details
3. PATCH /api/v1/failures/{id}/recovery - Update recovery status
4. GET /api/v1/failures/stats - Aggregate failure statistics
5. GET /api/v1/failures/unrecovered - List failures needing recovery

P1 requirement: Recovery tracking API for M10 workflow and operator acceptance.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.middleware.rate_limit import rate_limit_dependency

logger = logging.getLogger("nova.api.failures")

router = APIRouter(prefix="/api/v1/failures", tags=["failures"])


# =============================================================================
# Request/Response Models
# =============================================================================


class RecoveryUpdateRequest(BaseModel):
    """Request to update recovery status for a failure."""

    recovery_succeeded: bool = Field(..., description="Whether recovery was successful")
    notes: Optional[str] = Field(None, description="Operator notes on recovery")
    recovered_by: Optional[str] = Field(None, description="User/system that performed recovery")


class RecoveryUpdateResponse(BaseModel):
    """Response after updating recovery status."""

    id: str
    run_id: str
    recovery_attempted: bool
    recovery_succeeded: bool
    recovered_at: Optional[str]
    recovered_by: Optional[str]
    recovery_notes: Optional[str]


class FailureRecord(BaseModel):
    """Full failure record."""

    id: str
    run_id: str
    error_code: str
    error_message: Optional[str]
    category: Optional[str]
    severity: Optional[str]
    is_retryable: bool
    recovery_mode: Optional[str]
    recovery_suggestion: Optional[str]
    recovery_attempted: bool
    recovery_succeeded: bool
    recovered_at: Optional[str]
    recovered_by: Optional[str]
    recovery_notes: Optional[str]
    tenant_id: Optional[str]
    skill_id: Optional[str]
    step_index: Optional[int]
    catalog_entry_id: Optional[str]
    match_type: Optional[str]
    match_confidence: Optional[float]
    created_at: str
    updated_at: str


class FailureListResponse(BaseModel):
    """Response for failure list endpoint."""

    failures: List[FailureRecord]
    total: int
    limit: int
    offset: int


class FailureStatsResponse(BaseModel):
    """Aggregate failure statistics."""

    total_failures: int
    matched_failures: int
    unmatched_failures: int
    hit_rate: float
    recovery_attempts: int
    recovery_success_rate: float
    top_error_codes: List[Dict[str, Any]]
    top_categories: List[Dict[str, Any]]
    by_severity: Dict[str, int]
    time_range: Dict[str, str]


# =============================================================================
# Database Helpers
# =============================================================================


def _get_db_session():
    """Get database session."""
    try:
        from app.db import get_session

        return get_session()
    except ImportError:
        return None


def _failure_to_record(fm) -> FailureRecord:
    """Convert FailureMatch model to FailureRecord."""
    return FailureRecord(
        id=str(fm.id),
        run_id=fm.run_id,
        error_code=fm.error_code,
        error_message=fm.error_message,
        category=fm.category,
        severity=fm.severity,
        is_retryable=fm.is_retryable,
        recovery_mode=fm.recovery_mode,
        recovery_suggestion=fm.recovery_suggestion,
        recovery_attempted=fm.recovery_attempted,
        recovery_succeeded=fm.recovery_succeeded,
        recovered_at=fm.recovered_at.isoformat() if fm.recovered_at else None,
        recovered_by=fm.recovered_by,
        recovery_notes=fm.recovery_notes,
        tenant_id=fm.tenant_id,
        skill_id=fm.skill_id,
        step_index=fm.step_index,
        catalog_entry_id=fm.catalog_entry_id,
        match_type=fm.match_type,
        match_confidence=fm.match_confidence,
        created_at=fm.created_at.isoformat() if fm.created_at else "",
        updated_at=fm.updated_at.isoformat() if fm.updated_at else "",
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", response_model=FailureListResponse)
async def list_failures(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    error_code: Optional[str] = Query(None, description="Filter by error code"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter: unrecovered, recovered, all"),
    since_hours: Optional[int] = Query(24, description="Only failures from last N hours"),
    limit: int = Query(100, ge=1, le=1000, description="Max failures to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    List failures with optional filters.

    Supports filtering by:
    - tenant_id: Scope to specific tenant
    - run_id: Get failures for a specific run
    - error_code: Match specific error code
    - category: Filter by error category (TRANSIENT, PERMANENT, etc.)
    - status: 'unrecovered' (needs attention), 'recovered', or 'all'
    - since_hours: Time window (default 24 hours)

    Returns paginated results with total count.
    """
    try:
        from sqlmodel import Session, col, func, select

        from app.db import FailureMatch, engine

        with Session(engine) as session:
            # Build query
            query = select(FailureMatch)
            count_query = select(func.count(FailureMatch.id))

            # Apply filters
            if tenant_id:
                query = query.where(FailureMatch.tenant_id == tenant_id)
                count_query = count_query.where(FailureMatch.tenant_id == tenant_id)

            if run_id:
                query = query.where(FailureMatch.run_id == run_id)
                count_query = count_query.where(FailureMatch.run_id == run_id)

            if error_code:
                query = query.where(FailureMatch.error_code == error_code)
                count_query = count_query.where(FailureMatch.error_code == error_code)

            if category:
                query = query.where(FailureMatch.category == category)
                count_query = count_query.where(FailureMatch.category == category)

            if status == "unrecovered":
                query = query.where(FailureMatch.recovery_succeeded == False)
                count_query = count_query.where(FailureMatch.recovery_succeeded == False)
            elif status == "recovered":
                query = query.where(FailureMatch.recovery_succeeded == True)
                count_query = count_query.where(FailureMatch.recovery_succeeded == True)

            if since_hours:
                cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
                query = query.where(FailureMatch.created_at >= cutoff)
                count_query = count_query.where(FailureMatch.created_at >= cutoff)

            # Get total count
            total = session.exec(count_query).one()

            # Apply pagination and ordering
            query = query.order_by(col(FailureMatch.created_at).desc())
            query = query.offset(offset).limit(limit)

            failures = session.exec(query).all()

            return FailureListResponse(
                failures=[_failure_to_record(fm) for fm in failures],
                total=total,
                limit=limit,
                offset=offset,
            )

    except ImportError as e:
        logger.error(f"Database not available: {e}")
        raise HTTPException(status_code=503, detail="Database not available")
    except Exception as e:
        logger.error(f"List failures error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list failures: {str(e)}")


@router.get("/stats", response_model=FailureStatsResponse)
async def get_failure_stats(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    since_hours: int = Query(24, description="Stats for last N hours"),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Get aggregate failure statistics.

    Returns:
    - Total failure count
    - Hit/miss rates
    - Recovery success rate
    - Top error codes
    - Distribution by category and severity
    """
    try:
        from sqlmodel import Session, col, func, select

        from app.db import FailureMatch, engine

        with Session(engine) as session:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

            # Base filter
            base_filter = FailureMatch.created_at >= cutoff
            if tenant_id:
                base_filter = base_filter & (FailureMatch.tenant_id == tenant_id)

            # Total failures
            total = session.exec(select(func.count(FailureMatch.id)).where(base_filter)).one()

            # Matched (catalog_entry_id not null)
            matched = session.exec(
                select(func.count(FailureMatch.id)).where(base_filter & (FailureMatch.catalog_entry_id.isnot(None)))
            ).one()

            unmatched = total - matched
            hit_rate = matched / total if total > 0 else 0.0

            # Recovery stats
            recovery_attempts = session.exec(
                select(func.count(FailureMatch.id)).where(base_filter & (FailureMatch.recovery_attempted == True))
            ).one()

            recovery_successes = session.exec(
                select(func.count(FailureMatch.id)).where(base_filter & (FailureMatch.recovery_succeeded == True))
            ).one()

            recovery_success_rate = recovery_successes / recovery_attempts if recovery_attempts > 0 else 0.0

            # Top error codes
            count_col = func.count(FailureMatch.id)
            top_codes_result = session.exec(
                select(FailureMatch.error_code, count_col)
                .where(base_filter)
                .group_by(FailureMatch.error_code)
                .order_by(count_col.desc())
                .limit(10)
            ).all()
            top_codes = [{"error_code": row[0], "count": row[1]} for row in top_codes_result]

            # Top categories
            top_cats_result = session.exec(
                select(FailureMatch.category, count_col)
                .where(base_filter)
                .group_by(FailureMatch.category)
                .order_by(count_col.desc())
            ).all()
            top_cats = [{"category": row[0] or "UNKNOWN", "count": row[1]} for row in top_cats_result]

            # By severity
            severity_result = session.exec(
                select(FailureMatch.severity, count_col).where(base_filter).group_by(FailureMatch.severity)
            ).all()
            by_severity = {row[0] or "UNKNOWN": row[1] for row in severity_result}

            return FailureStatsResponse(
                total_failures=total,
                matched_failures=matched,
                unmatched_failures=unmatched,
                hit_rate=round(hit_rate, 4),
                recovery_attempts=recovery_attempts,
                recovery_success_rate=round(recovery_success_rate, 4),
                top_error_codes=top_codes,
                top_categories=top_cats,
                by_severity=by_severity,
                time_range={
                    "since": cutoff.isoformat(),
                    "until": datetime.now(timezone.utc).isoformat(),
                },
            )

    except ImportError as e:
        logger.error(f"Database not available: {e}")
        raise HTTPException(status_code=503, detail="Database not available")
    except Exception as e:
        logger.error(f"Get failure stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/unrecovered", response_model=FailureListResponse)
async def list_unrecovered_failures(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    category: Optional[str] = Query(None, description="Filter by category"),
    since_hours: int = Query(24, description="Only failures from last N hours"),
    limit: int = Query(50, ge=1, le=500, description="Max failures to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    List failures that need recovery attention.

    This is a convenience endpoint for operators to see failures that:
    - Have not been marked as recovered
    - Have recovery suggestions available

    Ordered by severity (critical first) and recency.
    """
    try:
        from sqlmodel import Session, case, col, func, select

        from app.db import FailureMatch, engine

        with Session(engine) as session:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

            query = select(FailureMatch).where(
                (FailureMatch.recovery_succeeded == False) & (FailureMatch.created_at >= cutoff)
            )
            count_query = select(func.count(FailureMatch.id)).where(
                (FailureMatch.recovery_succeeded == False) & (FailureMatch.created_at >= cutoff)
            )

            if tenant_id:
                query = query.where(FailureMatch.tenant_id == tenant_id)
                count_query = count_query.where(FailureMatch.tenant_id == tenant_id)

            if category:
                query = query.where(FailureMatch.category == category)
                count_query = count_query.where(FailureMatch.category == category)

            # Get total count
            total = session.exec(count_query).one()

            # Order by severity (CRITICAL > ERROR > WARNING > INFO) then by time
            severity_order = case(
                (FailureMatch.severity == "CRITICAL", 0),
                (FailureMatch.severity == "ERROR", 1),
                (FailureMatch.severity == "WARNING", 2),
                else_=3,
            )

            query = query.order_by(severity_order, col(FailureMatch.created_at).desc())
            query = query.offset(offset).limit(limit)

            failures = session.exec(query).all()

            return FailureListResponse(
                failures=[_failure_to_record(fm) for fm in failures],
                total=total,
                limit=limit,
                offset=offset,
            )

    except ImportError as e:
        logger.error(f"Database not available: {e}")
        raise HTTPException(status_code=503, detail="Database not available")
    except Exception as e:
        logger.error(f"List unrecovered failures error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list unrecovered failures: {str(e)}")


@router.get("/{failure_id}", response_model=FailureRecord)
async def get_failure(
    failure_id: str,
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Get detailed failure record by ID.

    Returns full failure information including:
    - Error details
    - Recovery suggestions
    - Current recovery status
    - Execution context
    """
    try:
        from sqlmodel import Session, select

        from app.db import FailureMatch, engine

        with Session(engine) as session:
            # Try UUID parse
            try:
                failure_uuid = UUID(failure_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid failure ID format: {failure_id}")

            # Use session.get() for direct ID lookup
            failure = session.get(FailureMatch, failure_uuid)

            if not failure:
                raise HTTPException(status_code=404, detail=f"Failure not found: {failure_id}")

            return _failure_to_record(failure)

    except HTTPException:
        raise
    except ImportError as e:
        logger.error(f"Database not available: {e}")
        raise HTTPException(status_code=503, detail="Database not available")
    except Exception as e:
        logger.error(f"Get failure error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get failure: {str(e)}")


@router.patch("/{failure_id}/recovery", response_model=RecoveryUpdateResponse)
async def update_recovery_status(
    failure_id: str,
    request: RecoveryUpdateRequest,
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Update recovery status for a failure.

    P1 requirement: Critical for M10 workflow and operator acceptance.

    Args:
        failure_id: UUID of the failure record
        request: Recovery status update

    Returns:
        Updated failure record with recovery info

    Side effects:
        - Updates recovery metrics (recovery_success_total / recovery_failure_total)
        - Sets recovered_at timestamp
    """
    try:
        from sqlmodel import Session, select

        from app.db import FailureMatch, engine
        from app.runtime.failure_catalog import update_recovery_status as update_metrics

        with Session(engine) as session:
            # Parse UUID
            try:
                failure_uuid = UUID(failure_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid failure ID format: {failure_id}")

            # Use session.get() for direct ID lookup
            failure = session.get(FailureMatch, failure_uuid)

            if not failure:
                raise HTTPException(status_code=404, detail=f"Failure not found: {failure_id}")

            # Update recovery status
            if request.recovery_succeeded:
                failure.mark_recovery_succeeded(by=request.recovered_by, notes=request.notes)
            else:
                failure.mark_recovery_failed(by=request.recovered_by, notes=request.notes)

            session.add(failure)
            session.commit()
            session.refresh(failure)

            # Extract values while session is open to avoid DetachedInstanceError
            response_data = {
                "id": str(failure.id),
                "run_id": failure.run_id,
                "recovery_attempted": failure.recovery_attempted,
                "recovery_succeeded": failure.recovery_succeeded,
                "recovered_at": failure.recovered_at.isoformat() if failure.recovered_at else None,
                "recovered_by": failure.recovered_by,
                "recovery_notes": failure.recovery_notes,
            }
            recovery_mode = failure.recovery_mode or "unknown"
            error_code = failure.error_code[:50] if failure.error_code else "unknown"

        # Update metrics (outside session)
        try:
            update_metrics(
                succeeded=request.recovery_succeeded,
                recovery_mode=recovery_mode,
                error_code=error_code,
            )
        except Exception as e:
            logger.warning(f"Failed to update recovery metrics: {e}")

        logger.info(
            f"M9: Recovery status updated for {failure_id}: "
            f"succeeded={request.recovery_succeeded}, by={request.recovered_by}"
        )

        return RecoveryUpdateResponse(**response_data)

    except HTTPException:
        raise
    except ImportError as e:
        logger.error(f"Database not available: {e}")
        raise HTTPException(status_code=503, detail="Database not available")
    except Exception as e:
        logger.error(f"Update recovery status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update recovery status: {str(e)}")
