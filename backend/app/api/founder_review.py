# Layer: L2 — Product APIs
# Product: founder-console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Founder AUTO_EXECUTE Review Endpoints (Evidence-Only)
# Callers: Founder Console UI
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-333

"""
Founder AUTO_EXECUTE Review API - PIN-333

Evidence-only endpoints for reviewing SUB-019 auto-execution decisions.

CRITICAL CONSTRAINTS:
- READ-ONLY: No mutation endpoints
- EVIDENCE-ONLY: Data comes from ExecutionEnvelope + SafetyFlags
- FOUNDER-ONLY: Requires FOPS token with founder role
- NO CONTROL: Does NOT approve/reject/pause/override anything
- NO BEHAVIOR CHANGE: AUTO_EXECUTE behavior is unchanged

If any code in this file implies control → VIOLATION of PIN-333.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlmodel import Session

from app.auth.console_auth import FounderToken, verify_fops_token
from app.contracts.ops import (
    AutoExecuteReviewFilterDTO,
    AutoExecuteReviewItemDTO,
    AutoExecuteReviewListDTO,
    AutoExecuteReviewStatsDTO,
)
from app.db import get_session

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/founder/review",
    tags=["founder-review"],
)


# =============================================================================
# AUDIT EVENT EMISSION
# =============================================================================


def emit_review_audit_event(
    session: Session,
    founder_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """
    Emit audit event for founder review access.

    PIN-333: All dashboard views emit read-audit events.
    """
    try:
        # Log to standard audit table
        session.execute(
            text(
                """
                INSERT INTO audit_events (
                    event_type, actor_id, actor_type, resource_type,
                    resource_id, action, details, created_at
                )
                VALUES (
                    'FOUNDER_REVIEW_ACCESS', :founder_id, 'FOUNDER', :resource_type,
                    :resource_id, :action, :details::jsonb, NOW()
                )
                """
            ),
            {
                "founder_id": founder_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
                "details": str(details) if details else "{}",
            },
        )
        session.commit()
    except Exception as e:
        # Audit failure should not block the read operation
        logger.warning(f"Failed to emit review audit event: {e}")


# =============================================================================
# READ-ONLY ENDPOINTS
# =============================================================================


@router.get(
    "/auto-execute",
    response_model=AutoExecuteReviewListDTO,
    summary="List AUTO_EXECUTE decisions",
    description="""
    List SUB-019 AUTO_EXECUTE decisions with evidence.

    **PIN-333 Constraints:**
    - Evidence-only: Returns data from execution envelopes
    - Read-only: No mutation
    - Founder-only: Requires FOPS token

    Default: Last 7 days, all tenants.
    """,
)
async def list_auto_execute_decisions(
    # Filters
    start_time: Optional[str] = Query(None, description="ISO8601 start time"),
    end_time: Optional[str] = Query(None, description="ISO8601 end time"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    decision: Optional[str] = Query(None, description="EXECUTED or SKIPPED"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    max_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    has_safety_flags: Optional[bool] = Query(None, description="Filter for flagged items"),
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    # Auth
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
) -> AutoExecuteReviewListDTO:
    """
    List AUTO_EXECUTE decisions with filtering and pagination.

    EVIDENCE-ONLY: This endpoint returns evidence from stored envelopes.
    It does NOT influence auto-execute behavior.
    """
    # Emit audit event
    emit_review_audit_event(
        session,
        founder_id=token.sub,
        action="LIST_AUTO_EXECUTE_DECISIONS",
        resource_type="AUTO_EXECUTE_REVIEW",
        details={"filters": {"tenant_id": tenant_id, "decision": decision}},
    )

    # Default time window: last 7 days
    if not end_time:
        end_dt = datetime.now(timezone.utc)
    else:
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

    if not start_time:
        start_dt = end_dt - timedelta(days=7)
    else:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

    # Build query - read from execution_envelopes table
    # Note: This assumes execution envelopes are stored in DB
    # If not, this would need to query from evidence sink
    base_query = """
        SELECT
            e.invocation_id,
            e.envelope_id,
            e.timestamp,
            e.tenant_id,
            e.account_id,
            e.project_id,
            e.capability_id,
            e.execution_vector,
            e.confidence_score,
            e.confidence_threshold,
            e.confidence_auto_execute_triggered,
            e.recovery_action,
            e.recovery_candidate_id,
            e.input_hash,
            e.plan_hash,
            e.plan_mutation_detected,
            e.worker_identity,
            e.safety_checked,
            e.safety_passed,
            e.safety_flags,
            e.safety_warnings
        FROM execution_envelopes e
        WHERE e.capability_id = 'SUB-019'
        AND e.execution_vector = 'AUTO_EXEC'
        AND e.timestamp >= :start_time
        AND e.timestamp <= :end_time
    """

    params = {
        "start_time": start_dt,
        "end_time": end_dt,
    }

    # Add optional filters
    if tenant_id:
        base_query += " AND e.tenant_id = :tenant_id"
        params["tenant_id"] = tenant_id

    if decision:
        if decision == "EXECUTED":
            base_query += " AND e.confidence_auto_execute_triggered = true"
        elif decision == "SKIPPED":
            base_query += " AND e.confidence_auto_execute_triggered = false"

    if min_confidence is not None:
        base_query += " AND e.confidence_score >= :min_confidence"
        params["min_confidence"] = min_confidence

    if max_confidence is not None:
        base_query += " AND e.confidence_score <= :max_confidence"
        params["max_confidence"] = max_confidence

    if has_safety_flags is not None:
        if has_safety_flags:
            base_query += " AND array_length(e.safety_flags, 1) > 0"
        else:
            base_query += " AND (e.safety_flags IS NULL OR array_length(e.safety_flags, 1) = 0)"

    # Get total count
    count_query = f"SELECT COUNT(*) FROM ({base_query}) as subq"
    try:
        count_result = session.execute(text(count_query), params)
        total_count = count_result.scalar() or 0
    except Exception as e:
        logger.warning(f"Auto-execute query failed (table may not exist): {e}")
        # Return empty result if table doesn't exist yet
        return AutoExecuteReviewListDTO(
            items=[],
            total_count=0,
            page=page,
            page_size=page_size,
            executed_count=0,
            skipped_count=0,
            flagged_count=0,
        )

    # Add pagination and ordering
    offset = (page - 1) * page_size
    paginated_query = f"""
        {base_query}
        ORDER BY e.timestamp DESC
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = page_size
    params["offset"] = offset

    try:
        result = session.execute(text(paginated_query), params)
        rows = result.fetchall()
    except Exception as e:
        logger.warning(f"Auto-execute query failed: {e}")
        rows = []

    # Convert to DTOs
    items = []
    executed_count = 0
    skipped_count = 0
    flagged_count = 0

    for row in rows:
        decision_value = "EXECUTED" if row.confidence_auto_execute_triggered else "SKIPPED"
        if decision_value == "EXECUTED":
            executed_count += 1
        else:
            skipped_count += 1

        flags = row.safety_flags or []
        if flags:
            flagged_count += 1

        item = AutoExecuteReviewItemDTO(
            invocation_id=row.invocation_id,
            envelope_id=row.envelope_id,
            timestamp=row.timestamp.isoformat() if row.timestamp else "",
            tenant_id=row.tenant_id,
            account_id=row.account_id,
            project_id=row.project_id,
            capability_id="SUB-019",
            execution_vector="AUTO_EXEC",
            confidence_score=row.confidence_score or 0.0,
            threshold=row.confidence_threshold or 0.8,
            decision=decision_value,
            recovery_action=row.recovery_action,
            recovery_candidate_id=row.recovery_candidate_id,
            incident_id=None,  # Would need join to get this
            execution_result=None,  # Would need join to get this
            input_hash=row.input_hash or "",
            plan_hash=row.plan_hash or "",
            plan_mutation_detected=row.plan_mutation_detected or False,
            worker_identity=row.worker_identity or "recovery_claim_worker",
            safety_checked=row.safety_checked or False,
            safety_passed=row.safety_passed if row.safety_passed is not None else True,
            safety_flags=flags,
            safety_warnings=row.safety_warnings or [],
        )
        items.append(item)

    return AutoExecuteReviewListDTO(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        executed_count=executed_count,
        skipped_count=skipped_count,
        flagged_count=flagged_count,
    )


@router.get(
    "/auto-execute/{invocation_id}",
    response_model=AutoExecuteReviewItemDTO,
    summary="Get single AUTO_EXECUTE decision",
    description="""
    Get detailed evidence for a single AUTO_EXECUTE decision.

    **PIN-333 Constraints:**
    - Evidence-only: Returns data from execution envelope
    - Read-only: No mutation
    - Founder-only: Requires FOPS token
    """,
)
async def get_auto_execute_decision(
    invocation_id: str,
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
) -> AutoExecuteReviewItemDTO:
    """
    Get detailed evidence for a single AUTO_EXECUTE decision.

    EVIDENCE-ONLY: Returns stored envelope data, no computation or inference.
    """
    # Emit audit event
    emit_review_audit_event(
        session,
        founder_id=token.sub,
        action="GET_AUTO_EXECUTE_DECISION",
        resource_type="AUTO_EXECUTE_REVIEW",
        resource_id=invocation_id,
    )

    query = """
        SELECT
            e.invocation_id,
            e.envelope_id,
            e.timestamp,
            e.tenant_id,
            e.account_id,
            e.project_id,
            e.capability_id,
            e.execution_vector,
            e.confidence_score,
            e.confidence_threshold,
            e.confidence_auto_execute_triggered,
            e.recovery_action,
            e.recovery_candidate_id,
            e.input_hash,
            e.plan_hash,
            e.plan_mutation_detected,
            e.worker_identity,
            e.safety_checked,
            e.safety_passed,
            e.safety_flags,
            e.safety_warnings
        FROM execution_envelopes e
        WHERE e.invocation_id = :invocation_id
        AND e.capability_id = 'SUB-019'
    """

    try:
        result = session.execute(text(query), {"invocation_id": invocation_id})
        row = result.fetchone()
    except Exception as e:
        logger.warning(f"Auto-execute lookup failed: {e}")
        raise HTTPException(status_code=404, detail="Decision not found")

    if not row:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision_value = "EXECUTED" if row.confidence_auto_execute_triggered else "SKIPPED"

    return AutoExecuteReviewItemDTO(
        invocation_id=row.invocation_id,
        envelope_id=row.envelope_id,
        timestamp=row.timestamp.isoformat() if row.timestamp else "",
        tenant_id=row.tenant_id,
        account_id=row.account_id,
        project_id=row.project_id,
        capability_id="SUB-019",
        execution_vector="AUTO_EXEC",
        confidence_score=row.confidence_score or 0.0,
        threshold=row.confidence_threshold or 0.8,
        decision=decision_value,
        recovery_action=row.recovery_action,
        recovery_candidate_id=row.recovery_candidate_id,
        incident_id=None,
        execution_result=None,
        input_hash=row.input_hash or "",
        plan_hash=row.plan_hash or "",
        plan_mutation_detected=row.plan_mutation_detected or False,
        worker_identity=row.worker_identity or "recovery_claim_worker",
        safety_checked=row.safety_checked or False,
        safety_passed=row.safety_passed if row.safety_passed is not None else True,
        safety_flags=row.safety_flags or [],
        safety_warnings=row.safety_warnings or [],
    )


@router.get(
    "/auto-execute/stats",
    response_model=AutoExecuteReviewStatsDTO,
    summary="Get AUTO_EXECUTE statistics",
    description="""
    Get aggregate statistics for AUTO_EXECUTE decisions.

    **PIN-333 Constraints:**
    - Charts reflect stored evidence only
    - No predictive analytics
    - No computed risk scores
    """,
)
async def get_auto_execute_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to aggregate"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
) -> AutoExecuteReviewStatsDTO:
    """
    Get aggregate statistics for AUTO_EXECUTE decisions.

    EVIDENCE-ONLY: Statistics are aggregations of stored envelope data.
    No predictions, no inferences, no risk scores.
    """
    # Emit audit event
    emit_review_audit_event(
        session,
        founder_id=token.sub,
        action="GET_AUTO_EXECUTE_STATS",
        resource_type="AUTO_EXECUTE_REVIEW",
        details={"days": days, "tenant_id": tenant_id},
    )

    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days)

    params = {
        "start_time": start_dt,
        "end_time": end_dt,
    }

    tenant_filter = ""
    if tenant_id:
        tenant_filter = "AND e.tenant_id = :tenant_id"
        params["tenant_id"] = tenant_id

    # Total counts
    count_query = f"""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE e.confidence_auto_execute_triggered = true) as executed,
            COUNT(*) FILTER (WHERE e.confidence_auto_execute_triggered = false) as skipped,
            COUNT(*) FILTER (WHERE array_length(e.safety_flags, 1) > 0) as flagged
        FROM execution_envelopes e
        WHERE e.capability_id = 'SUB-019'
        AND e.execution_vector = 'AUTO_EXEC'
        AND e.timestamp >= :start_time
        AND e.timestamp <= :end_time
        {tenant_filter}
    """

    try:
        result = session.execute(text(count_query), params)
        counts = result.fetchone()
        total = counts.total or 0
        executed = counts.executed or 0
        skipped = counts.skipped or 0
        flagged = counts.flagged or 0
    except Exception as e:
        logger.warning(f"Stats query failed: {e}")
        total = executed = skipped = flagged = 0

    # Confidence distribution
    confidence_query = f"""
        SELECT
            CASE
                WHEN e.confidence_score < 0.5 THEN '0.0-0.5'
                WHEN e.confidence_score < 0.6 THEN '0.5-0.6'
                WHEN e.confidence_score < 0.7 THEN '0.6-0.7'
                WHEN e.confidence_score < 0.8 THEN '0.7-0.8'
                WHEN e.confidence_score < 0.85 THEN '0.8-0.85'
                WHEN e.confidence_score < 0.9 THEN '0.85-0.9'
                WHEN e.confidence_score < 0.95 THEN '0.9-0.95'
                ELSE '0.95-1.0'
            END as bucket,
            COUNT(*) as count
        FROM execution_envelopes e
        WHERE e.capability_id = 'SUB-019'
        AND e.execution_vector = 'AUTO_EXEC'
        AND e.timestamp >= :start_time
        AND e.timestamp <= :end_time
        {tenant_filter}
        GROUP BY bucket
        ORDER BY bucket
    """

    confidence_distribution = {}
    try:
        result = session.execute(text(confidence_query), params)
        for row in result.fetchall():
            confidence_distribution[row.bucket] = row.count
    except Exception as e:
        logger.warning(f"Confidence distribution query failed: {e}")

    # Safety flag counts
    flag_query = f"""
        SELECT
            unnest(e.safety_flags) as flag,
            COUNT(*) as count
        FROM execution_envelopes e
        WHERE e.capability_id = 'SUB-019'
        AND e.execution_vector = 'AUTO_EXEC'
        AND e.timestamp >= :start_time
        AND e.timestamp <= :end_time
        AND array_length(e.safety_flags, 1) > 0
        {tenant_filter}
        GROUP BY flag
        ORDER BY count DESC
    """

    flag_counts = {}
    try:
        result = session.execute(text(flag_query), params)
        for row in result.fetchall():
            flag_counts[row.flag] = row.count
    except Exception as e:
        logger.warning(f"Flag counts query failed: {e}")

    # Daily counts for trend chart
    daily_query = f"""
        SELECT
            DATE(e.timestamp) as date,
            COUNT(*) FILTER (WHERE e.confidence_auto_execute_triggered = true) as executed,
            COUNT(*) FILTER (WHERE e.confidence_auto_execute_triggered = false) as skipped
        FROM execution_envelopes e
        WHERE e.capability_id = 'SUB-019'
        AND e.execution_vector = 'AUTO_EXEC'
        AND e.timestamp >= :start_time
        AND e.timestamp <= :end_time
        {tenant_filter}
        GROUP BY DATE(e.timestamp)
        ORDER BY date
    """

    daily_counts = []
    try:
        result = session.execute(text(daily_query), params)
        for row in result.fetchall():
            daily_counts.append({
                "date": row.date.isoformat() if row.date else "",
                "executed": row.executed or 0,
                "skipped": row.skipped or 0,
            })
    except Exception as e:
        logger.warning(f"Daily counts query failed: {e}")

    return AutoExecuteReviewStatsDTO(
        start_time=start_dt.isoformat(),
        end_time=end_dt.isoformat(),
        total_decisions=total,
        executed_count=executed,
        skipped_count=skipped,
        confidence_distribution=confidence_distribution,
        flagged_count=flagged,
        flag_counts=flag_counts,
        daily_counts=daily_counts,
    )
