# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Recovery ingest endpoint (idempotent failure ingestion)
# Callers: Machine clients (recovery:write scope)
# Allowed Imports: L3, L4, L5, L6
# Forbidden Imports: L1
# Reference: CAP-018

# app/api/recovery_ingest.py
# capability_id: CAP-018
"""
M10 Recovery Ingest Endpoint - Idempotent failure ingestion

Provides:
- POST /api/v1/recovery/ingest - Ingest failure for recovery evaluation

Features:
- Idempotent: Duplicate requests return existing candidate
- Transactional: All operations atomic within DB transaction
- IntegrityError handling: Catches unique constraint violations gracefully
- Worker enqueue: Optionally pushes to evaluation queue

Authentication: Machine token with recovery:write scope.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, create_engine

from app.metrics import (
    recovery_ingest_duplicates_total,
    recovery_ingest_enqueue_total,
    recovery_ingest_latency_seconds,
    recovery_ingest_total,
)
from app.middleware.rate_limit import rate_limit_dependency
# L6 driver import (migrated to HOC per SWEEP-09)
from app.hoc.cus.policies.L6_drivers.recovery_write_driver import RecoveryWriteService

logger = logging.getLogger("nova.api.recovery_ingest")

router = APIRouter(prefix="/api/v1/recovery", tags=["recovery-ingest"])


# =============================================================================
# Request/Response Models
# =============================================================================


class IngestRequest(BaseModel):
    """Request to ingest a failure for recovery evaluation."""

    failure_match_id: str = Field(..., description="UUID of failure_match record")
    failure_payload: Dict[str, Any] = Field(
        ...,
        description="Error details: error_type, raw message, meta",
        example={
            "error_type": "TIMEOUT",
            "raw": "Connection timed out after 30s",
            "meta": {"skill": "http_call", "tenant_id": "acme"},
        },
    )
    source: Optional[str] = Field("api", description="Source system identifier")
    idempotency_key: Optional[str] = Field(None, description="Optional UUID for request deduplication")
    enqueue_evaluation: bool = Field(True, description="Whether to enqueue for background evaluation")


class IngestResponse(BaseModel):
    """Response from ingest endpoint."""

    candidate_id: int = Field(..., description="ID of the recovery candidate")
    status: str = Field(..., description="accepted, duplicate, or error")
    message: str = Field(..., description="Human-readable status message")
    is_duplicate: bool = Field(False, description="Whether this was a duplicate request")
    failure_match_id: str = Field(..., description="Echo of input failure_match_id")


# =============================================================================
# Database Session Dependency
# =============================================================================


def get_db_session():
    """Create database session for request."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


# =============================================================================
# Ingest Endpoint
# =============================================================================


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Accepted for processing"},
        409: {"description": "Duplicate request (returns existing candidate)"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"},
    },
)
async def ingest_failure(
    request: IngestRequest,
    session: Session = Depends(get_db_session),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Ingest a failure for recovery suggestion evaluation.

    This endpoint is idempotent:
    - If idempotency_key is provided and matches an existing request, returns existing candidate
    - If failure_match_id already has a candidate, updates occurrence count and returns it
    - Otherwise, creates a new candidate and optionally enqueues for evaluation

    Returns 202 Accepted with candidate_id for new ingestions.
    Returns 200 OK with is_duplicate=True for duplicate requests.
    """
    start_time = time.perf_counter()
    status_label = "error"
    source_label = request.source or "api"

    try:
        failure_match_id = request.failure_match_id
        payload = request.failure_payload
        idempotency_key = request.idempotency_key

        logger.info(f"Ingest request: failure_match_id={failure_match_id}, idempotency_key={idempotency_key}")

        # =================================================================
        # Normalize error for candidate
        # =================================================================
        import hashlib

        error_type = payload.get("error_type", payload.get("error_code", "UNKNOWN"))
        raw_message = payload.get("raw", payload.get("error_message", ""))
        normalized = str(raw_message).lower().strip()[:500]
        signature_input = f"{error_type}:{normalized}"
        error_signature = hashlib.sha256(signature_input.encode()).hexdigest()[:16]

        # Generate default suggestion
        suggestion = _generate_default_suggestion(error_type, raw_message)

        # =================================================================
        # Atomic upsert: INSERT ... ON CONFLICT DO UPDATE RETURNING
        # This eliminates all race conditions between SELECT+INSERT
        # =================================================================
        # Phase 2B: Use write service for DB operations
        write_service = RecoveryWriteService(session)

        try:
            explain_json = json.dumps(
                {
                    "method": "pending_evaluation",
                    "source": request.source,
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            candidate_id, is_insert, occurrence_count = write_service.upsert_recovery_candidate(
                failure_match_id=failure_match_id,
                suggestion=suggestion,
                confidence=0.2,  # Default pending evaluation
                explain_json=explain_json,
                error_code=error_type,
                error_signature=error_signature,
                source=request.source,
                idempotency_key=idempotency_key,
            )
            write_service.commit()

            if not is_insert:
                # This was an update (duplicate)
                logger.info(f"Updated existing candidate: id={candidate_id}, occurrence_count={occurrence_count}")
                status_label = "duplicate"
                recovery_ingest_duplicates_total.labels(detection_method="upsert_conflict").inc()
                return IngestResponse(
                    candidate_id=candidate_id,
                    status="duplicate",
                    message=f"Updated occurrence count to {occurrence_count}",
                    is_duplicate=True,
                    failure_match_id=failure_match_id,
                )

        except IntegrityError as ie:
            write_service.rollback()

            # Handle edge case: idempotency_key conflict (different failure_match_id)
            msg = str(ie.orig).lower() if ie.orig else ""
            logger.warning(f"IntegrityError on upsert: {msg}")

            if idempotency_key and "idempotency_key" in msg:
                # Idempotency key matched different failure_match_id
                existing = write_service.get_candidate_by_idempotency_key(idempotency_key)

                if existing:
                    status_label = "duplicate"
                    recovery_ingest_duplicates_total.labels(detection_method="idempotency_key").inc()
                    return IngestResponse(
                        candidate_id=existing[0],
                        status="duplicate",
                        message="Idempotency key matched existing candidate",
                        is_duplicate=True,
                        failure_match_id=existing[1],
                    )

            # Unknown integrity error
            raise HTTPException(status_code=500, detail=f"Database integrity error: {str(ie.orig)}")

        # =================================================================
        # Optionally enqueue for background evaluation
        # =================================================================
        if request.enqueue_evaluation:
            try:
                _enqueue_evaluation(candidate_id, failure_match_id)
                recovery_ingest_enqueue_total.labels(status="success").inc()
            except Exception as e:
                # Non-fatal: evaluation will be picked up by polling worker
                logger.warning(f"Failed to enqueue evaluation for candidate {candidate_id}: {e}")
                recovery_ingest_enqueue_total.labels(status="failed").inc()
        else:
            recovery_ingest_enqueue_total.labels(status="skipped").inc()

        logger.info(f"Created new candidate: id={candidate_id}")
        status_label = "accepted"

        return IngestResponse(
            candidate_id=candidate_id,
            status="accepted",
            message="Failure accepted for recovery evaluation",
            is_duplicate=False,
            failure_match_id=failure_match_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to ingest failure: {str(e)}")
    finally:
        # Record metrics
        duration = time.perf_counter() - start_time
        recovery_ingest_total.labels(status=status_label, source=source_label).inc()
        recovery_ingest_latency_seconds.labels(status=status_label).observe(duration)


# =============================================================================
# Helper Functions
# =============================================================================


def _generate_default_suggestion(error_code: str, error_message: str) -> str:
    """Generate default recovery suggestion based on error type."""
    defaults = {
        "TIMEOUT": "Increase timeout threshold or implement retry with exponential backoff",
        "HTTP_5XX": "Check service health, implement circuit breaker, retry with backoff",
        "RATE_LIMITED": "Implement rate limiting with jitter, queue requests",
        "BUDGET_EXCEEDED": "Check budget allocation, consider cost optimization",
        "PERMISSION_DENIED": "Verify credentials and permissions configuration",
        "PARSE_ERROR": "Validate input format, check schema compatibility",
        "CONNECTION_ERROR": "Check network connectivity, implement retry logic",
        "AUTH": "Verify authentication credentials and token expiration",
    }

    error_upper = error_code.upper()
    for prefix, suggestion in defaults.items():
        if error_upper.startswith(prefix) or prefix in error_upper:
            return suggestion

    return f"Review error '{error_code}' and implement appropriate error handling"


async def _enqueue_evaluation_async(
    candidate_id: int,
    failure_match_id: str,
    idempotency_key: Optional[str] = None,
    session: Optional[Session] = None,
) -> bool:
    """
    Enqueue candidate for background evaluation using Redis Streams.

    Strategy:
    1. Try Redis Streams (durable, with consumer groups)
    2. If Redis fails, fallback to DB work_queue table
    3. Worker prioritizes Redis stream, falls back to DB scan

    Args:
        candidate_id: ID of the recovery candidate
        failure_match_id: UUID of the failure match
        idempotency_key: Optional idempotency key for deduplication
        session: Optional DB session for fallback queue

    Returns:
        True if enqueued successfully (either Redis or DB), False otherwise
    """
    enqueue_method = "unknown"

    try:
        # Try Redis Streams first (durable queue)
        from app.tasks.recovery_queue_stream import enqueue_stream

        msg_id = await enqueue_stream(
            candidate_id=candidate_id,
            priority=0.0,
            metadata={"failure_match_id": failure_match_id},
            idempotency_key=idempotency_key,
        )

        if msg_id:
            enqueue_method = "redis_stream"
            logger.info(f"Evaluation enqueued to Redis Stream: candidate_id={candidate_id}, msg_id={msg_id}")
            return True
        else:
            logger.warning(f"Redis Stream enqueue returned None for candidate {candidate_id}")
            # Fall through to DB fallback

    except ImportError:
        logger.warning("Redis Streams not available, trying DB fallback")
    except Exception as e:
        logger.warning(f"Redis Stream enqueue error: {e}, trying DB fallback")

    # DB Fallback: Insert into work_queue table
    try:
        if session is None:
            # Need to create a session for DB fallback
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                engine = create_engine(db_url, pool_pre_ping=True)
                session = Session(engine)
                owns_session = True
            else:
                logger.error("No DATABASE_URL for fallback queue")
                return False
        else:
            owns_session = False

        try:
            # Phase 2B: Use write service for DB operations
            write_service = RecoveryWriteService(session)
            write_service.enqueue_evaluation_db_fallback(candidate_id, idempotency_key)
            write_service.commit()
            enqueue_method = "db_fallback"
            logger.info(f"Evaluation enqueued to DB fallback: candidate_id={candidate_id}")
            return True
        finally:
            if owns_session:
                session.close()

    except Exception as e:
        logger.error(f"DB fallback enqueue failed: {e}")
        return False


def _enqueue_evaluation(
    candidate_id: int,
    failure_match_id: str,
    idempotency_key: Optional[str] = None,
    session: Optional[Session] = None,
) -> None:
    """
    Sync wrapper for enqueue_evaluation.

    Tries Redis Streams first, falls back to DB work_queue.
    """
    import asyncio

    try:
        # Try to get running event loop
        loop = asyncio.get_running_loop()
        # Schedule the async enqueue (non-blocking)
        loop.create_task(_enqueue_evaluation_async(candidate_id, failure_match_id, idempotency_key, session))
    except RuntimeError:
        # No event loop running, create one
        try:
            asyncio.run(_enqueue_evaluation_async(candidate_id, failure_match_id, idempotency_key, session))
        except Exception as e:
            logger.warning(f"Async enqueue failed: {e}")
            # Last resort: log for polling worker
            logger.info(
                f"Evaluation queued (polling): candidate_id={candidate_id}, failure_match_id={failure_match_id}"
            )
