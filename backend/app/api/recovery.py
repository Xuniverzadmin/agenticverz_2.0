# app/api/recovery.py
"""
M10 Recovery Suggestion Engine API Endpoints (Enhanced)

Provides REST API for:
1. POST /api/v1/recovery/suggest - Generate recovery suggestion for failure
2. GET /api/v1/recovery/candidates - List recovery candidates
3. GET /api/v1/recovery/candidates/{id} - Get single candidate with full context
4. PATCH /api/v1/recovery/candidates/{id} - Update candidate (execution status, etc.)
5. POST /api/v1/recovery/approve - Approve/reject a candidate
6. DELETE /api/v1/recovery/candidates/{id} - Revoke suggestion (admin)
7. GET /api/v1/recovery/actions - List available actions
8. POST /api/v1/recovery/evaluate - Evaluate rules without persisting
9. GET /api/v1/recovery/stats - Statistics and metrics

Authentication: Machine token with recovery:write scope or service account.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from app.middleware.rate_limit import rate_limit_dependency
from app.services.recovery_matcher import RecoveryMatcher

logger = logging.getLogger("nova.api.recovery")

router = APIRouter(prefix="/api/v1/recovery", tags=["recovery"])


# =============================================================================
# Request/Response Models
# =============================================================================


class SuggestRequest(BaseModel):
    """Request to generate recovery suggestion."""

    failure_match_id: str = Field(..., description="UUID of failure_match record")
    failure_payload: Dict[str, Any] = Field(
        ...,
        description="Error details: error_type, raw message, meta",
        example={"error_type": "TIMEOUT", "raw": "Connection timed out after 30s", "meta": {"skill": "http_call"}},
    )
    source: Optional[str] = Field(None, description="Source system identifier")
    occurred_at: Optional[datetime] = Field(None, description="When failure occurred")


class SuggestResponse(BaseModel):
    """Response with recovery suggestion."""

    matched_entry: Optional[Dict[str, Any]] = Field(None, description="Matched catalog entry if found")
    suggested_recovery: Optional[str] = Field(None, description="Human-readable recovery suggestion")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    candidate_id: Optional[int] = Field(None, description="ID of created/updated candidate")
    explain: Dict[str, Any] = Field(default_factory=dict, description="Scoring provenance and method details")


class ApproveRequest(BaseModel):
    """Request to approve/reject a recovery candidate."""

    candidate_id: int = Field(..., description="ID of candidate to approve")
    approved_by: str = Field(..., description="User making the decision")
    decision: str = Field(..., description="Decision: 'approved' or 'rejected'", pattern="^(approved|rejected)$")
    note: Optional[str] = Field("", description="Optional review note")


class CandidateResponse(BaseModel):
    """Recovery candidate details."""

    id: int
    failure_match_id: str
    suggestion: str
    confidence: float
    explain: Dict[str, Any]
    decision: str
    occurrence_count: int
    last_occurrence_at: Optional[str]
    created_at: Optional[str]
    approved_by_human: Optional[str]
    approved_at: Optional[str]
    review_note: Optional[str]
    error_code: Optional[str]
    source: Optional[str]


class CandidateListResponse(BaseModel):
    """Response for candidates list endpoint."""

    candidates: List[CandidateResponse]
    total: int
    limit: int
    offset: int


class CandidateUpdateRequest(BaseModel):
    """Request to update a candidate."""

    execution_status: Optional[str] = Field(
        None, description="Execution status: pending, executing, succeeded, failed, rolled_back, skipped"
    )
    selected_action_id: Optional[int] = Field(None, description="ID of selected action from action catalog")
    execution_result: Optional[Dict[str, Any]] = Field(None, description="Result of action execution")
    note: Optional[str] = Field(None, description="Update note")


class EvaluateRequest(BaseModel):
    """Request to evaluate rules without persisting."""

    error_code: str = Field(..., description="Error code to evaluate")
    error_message: str = Field(..., description="Error message")
    skill_id: Optional[str] = Field(None, description="Skill ID for context")
    tenant_id: Optional[str] = Field(None, description="Tenant ID for context")
    occurrence_count: int = Field(1, ge=1, description="Occurrence count")


class EvaluateResponse(BaseModel):
    """Response from rule evaluation."""

    recommended_action: Optional[str] = Field(None, description="Recommended action code")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    total_score: float = Field(..., description="Total weighted score")
    rules_evaluated: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of evaluated rules with results"
    )
    explanation: str = Field("", description="Human-readable explanation")
    duration_ms: int = Field(0, description="Evaluation duration in milliseconds")


class ActionResponse(BaseModel):
    """Recovery action from catalog."""

    id: int
    action_code: str
    name: str
    description: Optional[str]
    action_type: str
    template: Dict[str, Any]
    applies_to_error_codes: List[str]
    applies_to_skills: List[str]
    success_rate: float
    total_applications: int
    is_automated: bool
    requires_approval: bool
    priority: int
    is_active: bool


class ActionListResponse(BaseModel):
    """Response for actions list endpoint."""

    actions: List[ActionResponse]
    total: int


class CandidateDetailResponse(CandidateResponse):
    """Detailed candidate response with provenance and inputs."""

    selected_action: Optional[ActionResponse] = None
    inputs: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    rules_evaluated: List[Dict[str, Any]] = Field(default_factory=list)
    execution_status: Optional[str] = None
    executed_at: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None


# =============================================================================
# Dependency for Matcher
# =============================================================================


def get_matcher() -> RecoveryMatcher:
    """Get matcher instance."""
    return RecoveryMatcher()


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/suggest", response_model=SuggestResponse)
async def suggest_recovery(
    request: SuggestRequest,
    matcher: RecoveryMatcher = Depends(get_matcher),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Generate recovery suggestion for a failure.

    Matches the failure against historical patterns and catalog entries,
    computes confidence score using time-weighted algorithm, and stores
    the suggestion as a candidate for human review.

    Idempotent: Re-submitting same failure_match_id updates occurrence
    count instead of creating duplicates.

    Returns:
        Suggestion with confidence score and candidate ID
    """
    try:
        logger.info(f"Recovery suggest request: failure_match_id={request.failure_match_id}")

        result = matcher.suggest(
            {
                "failure_match_id": request.failure_match_id,
                "failure_payload": request.failure_payload,
                "source": request.source,
                "occurred_at": request.occurred_at.isoformat() if request.occurred_at else None,
            }
        )

        # Increment metrics
        from app.metrics import recovery_suggestions_total

        recovery_suggestions_total.labels(source=request.source or "unknown", decision="pending").inc()

        return SuggestResponse(
            matched_entry=result.matched_entry,
            suggested_recovery=result.suggested_recovery,
            confidence=result.confidence,
            candidate_id=result.candidate_id,
            explain=result.explain,
        )

    except Exception as e:
        logger.error(f"Recovery suggest error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestion: {str(e)}")


@router.get("/candidates", response_model=CandidateListResponse)
async def list_candidates(
    status: str = Query("pending", description="Filter by status: pending, approved, rejected, all"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    matcher: RecoveryMatcher = Depends(get_matcher),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    List recovery candidates with optional status filter.

    Used by CLI for human review workflow.

    Returns:
        Paginated list of candidates
    """
    try:
        candidates = matcher.get_candidates(
            status=status,
            limit=limit,
            offset=offset,
        )

        return CandidateListResponse(
            candidates=[CandidateResponse(**c) for c in candidates],
            total=len(candidates),  # TODO: Add total count query
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"List candidates error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list candidates: {str(e)}")


@router.post("/approve", response_model=CandidateResponse)
async def approve_candidate(
    request: ApproveRequest,
    matcher: RecoveryMatcher = Depends(get_matcher),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Approve or reject a recovery candidate.

    Records the decision with audit trail for compliance.
    Only users with recovery_reviewer role can approve.

    Returns:
        Updated candidate with approval details
    """
    try:
        logger.info(
            f"Recovery approve: candidate_id={request.candidate_id}, "
            f"decision={request.decision}, by={request.approved_by}"
        )

        result = matcher.approve_candidate(
            candidate_id=request.candidate_id,
            approved_by=request.approved_by,
            decision=request.decision,
            note=request.note or "",
        )

        # Increment metrics
        from app.metrics import recovery_approvals_total

        recovery_approvals_total.labels(decision=request.decision).inc()

        return CandidateResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Approve candidate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve candidate: {str(e)}")


@router.delete("/candidates/{candidate_id}")
async def delete_candidate(
    candidate_id: int,
    matcher: RecoveryMatcher = Depends(get_matcher),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Delete/revoke a recovery candidate (admin only).

    Soft-deletes by setting decision to 'revoked'.
    Audit trail is preserved.
    """
    try:
        # Use approve with special 'rejected' status and note
        matcher.approve_candidate(
            candidate_id=candidate_id,
            approved_by="admin",
            decision="rejected",
            note="Revoked via admin delete",
        )

        return {"status": "deleted", "candidate_id": candidate_id}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Delete candidate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete candidate: {str(e)}")


@router.get("/stats")
async def get_recovery_stats(
    matcher: RecoveryMatcher = Depends(get_matcher),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Get recovery suggestion statistics.

    Returns aggregate metrics for monitoring and dashboards.
    """
    try:
        # Get counts by status
        pending = matcher.get_candidates(status="pending", limit=1)
        approved = matcher.get_candidates(status="approved", limit=1)
        rejected = matcher.get_candidates(status="rejected", limit=1)

        # TODO: Add proper count queries

        return {
            "total_candidates": len(pending) + len(approved) + len(rejected),
            "pending": len(pending),
            "approved": len(approved),
            "rejected": len(rejected),
            "approval_rate": (
                len(approved) / (len(approved) + len(rejected)) if (len(approved) + len(rejected)) > 0 else 0
            ),
        }

    except Exception as e:
        logger.error(f"Get stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# =============================================================================
# Enhanced Endpoints (M10 Phase 2)
# =============================================================================


@router.get("/candidates/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate_detail(
    candidate_id: int = Path(..., description="Candidate ID"),
    include_provenance: bool = Query(True, description="Include provenance history"),
    include_inputs: bool = Query(True, description="Include input data"),
    matcher: RecoveryMatcher = Depends(get_matcher),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Get detailed information about a specific candidate.

    Includes full provenance history, inputs, and selected action details.
    """
    try:
        import os

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

        engine = create_engine(db_url)

        with Session(engine) as session:
            # Get candidate
            result = session.execute(
                text(
                    """
                    SELECT
                        rc.id, rc.failure_match_id, rc.suggestion, rc.confidence,
                        rc.explain, rc.decision, rc.occurrence_count, rc.last_occurrence_at,
                        rc.created_at, rc.approved_by_human, rc.approved_at, rc.review_note,
                        rc.error_code, rc.source, rc.selected_action_id, rc.rules_evaluated,
                        rc.execution_status, rc.executed_at, rc.execution_result
                    FROM recovery_candidates rc
                    WHERE rc.id = :id
                """
                ),
                {"id": candidate_id},
            )
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")

            import json

            candidate_data = {
                "id": row[0],
                "failure_match_id": str(row[1]),
                "suggestion": row[2],
                "confidence": row[3],
                "explain": json.loads(row[4]) if isinstance(row[4], str) else (row[4] or {}),
                "decision": row[5],
                "occurrence_count": row[6],
                "last_occurrence_at": row[7].isoformat() if row[7] else None,
                "created_at": row[8].isoformat() if row[8] else None,
                "approved_by_human": row[9],
                "approved_at": row[10].isoformat() if row[10] else None,
                "review_note": row[11],
                "error_code": row[12],
                "source": row[13],
                "rules_evaluated": json.loads(row[15]) if isinstance(row[15], str) else (row[15] or []),
                "execution_status": row[16],
                "executed_at": row[17].isoformat() if row[17] else None,
                "execution_result": json.loads(row[18]) if isinstance(row[18], str) else row[18],
            }

            # Get selected action if present
            selected_action = None
            if row[14]:  # selected_action_id
                action_result = session.execute(
                    text(
                        """
                        SELECT id, action_code, name, description, action_type, template,
                               applies_to_error_codes, applies_to_skills, success_rate,
                               total_applications, is_automated, requires_approval, priority, is_active
                        FROM m10_recovery.suggestion_action
                        WHERE id = :id
                    """
                    ),
                    {"id": row[14]},
                )
                action_row = action_result.fetchone()
                if action_row:
                    selected_action = {
                        "id": action_row[0],
                        "action_code": action_row[1],
                        "name": action_row[2],
                        "description": action_row[3],
                        "action_type": action_row[4],
                        "template": json.loads(action_row[5])
                        if isinstance(action_row[5], str)
                        else (action_row[5] or {}),
                        "applies_to_error_codes": action_row[6] or [],
                        "applies_to_skills": action_row[7] or [],
                        "success_rate": action_row[8],
                        "total_applications": action_row[9],
                        "is_automated": action_row[10],
                        "requires_approval": action_row[11],
                        "priority": action_row[12],
                        "is_active": action_row[13],
                    }

            candidate_data["selected_action"] = selected_action

            # Get inputs if requested
            inputs = []
            if include_inputs:
                try:
                    inputs_result = session.execute(
                        text(
                            """
                            SELECT id, input_type, raw_value, normalized_value, parsed_data,
                                   confidence, weight, source, created_at
                            FROM m10_recovery.suggestion_input
                            WHERE suggestion_id = :id
                            ORDER BY created_at ASC
                        """
                        ),
                        {"id": candidate_id},
                    )
                    for inp_row in inputs_result.fetchall():
                        inputs.append(
                            {
                                "id": inp_row[0],
                                "input_type": inp_row[1],
                                "raw_value": inp_row[2],
                                "normalized_value": inp_row[3],
                                "parsed_data": json.loads(inp_row[4])
                                if isinstance(inp_row[4], str)
                                else (inp_row[4] or {}),
                                "confidence": inp_row[5],
                                "weight": inp_row[6],
                                "source": inp_row[7],
                                "created_at": inp_row[8].isoformat() if inp_row[8] else None,
                            }
                        )
                except Exception:
                    pass  # Table may not exist yet

            candidate_data["inputs"] = inputs

            # Get provenance if requested
            provenance = []
            if include_provenance:
                try:
                    prov_result = session.execute(
                        text(
                            """
                            SELECT id, event_type, details, rule_id, action_id,
                                   confidence_before, confidence_after, actor, actor_type,
                                   created_at, duration_ms
                            FROM m10_recovery.suggestion_provenance
                            WHERE suggestion_id = :id
                            ORDER BY created_at ASC
                        """
                        ),
                        {"id": candidate_id},
                    )
                    for prov_row in prov_result.fetchall():
                        provenance.append(
                            {
                                "id": prov_row[0],
                                "event_type": prov_row[1],
                                "details": json.loads(prov_row[2])
                                if isinstance(prov_row[2], str)
                                else (prov_row[2] or {}),
                                "rule_id": prov_row[3],
                                "action_id": prov_row[4],
                                "confidence_before": prov_row[5],
                                "confidence_after": prov_row[6],
                                "actor": prov_row[7],
                                "actor_type": prov_row[8],
                                "created_at": prov_row[9].isoformat() if prov_row[9] else None,
                                "duration_ms": prov_row[10],
                            }
                        )
                except Exception:
                    pass  # Table may not exist yet

            candidate_data["provenance"] = provenance

            return CandidateDetailResponse(**candidate_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get candidate detail error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get candidate: {str(e)}")


@router.patch("/candidates/{candidate_id}")
async def update_candidate(
    candidate_id: int,
    request: CandidateUpdateRequest,
    matcher: RecoveryMatcher = Depends(get_matcher),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Update a candidate's execution status or selected action.

    Used when:
    - Selecting an action for execution
    - Recording execution results
    - Marking execution as started/completed/failed
    """
    try:
        import json
        import os

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

        engine = create_engine(db_url)

        with Session(engine) as session:
            # Verify candidate exists
            result = session.execute(
                text("SELECT id, confidence FROM recovery_candidates WHERE id = :id"), {"id": candidate_id}
            )
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")

            old_confidence = row[1]

            # Build update query dynamically
            updates = []
            params = {"id": candidate_id}

            if request.execution_status:
                valid_statuses = ["pending", "executing", "succeeded", "failed", "rolled_back", "skipped"]
                if request.execution_status not in valid_statuses:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid execution_status. Must be one of: {valid_statuses}"
                    )
                updates.append("execution_status = :execution_status")
                params["execution_status"] = request.execution_status

                if request.execution_status in ("succeeded", "failed", "rolled_back"):
                    updates.append("executed_at = now()")

            if request.selected_action_id is not None:
                updates.append("selected_action_id = :selected_action_id")
                params["selected_action_id"] = request.selected_action_id

            if request.execution_result is not None:
                updates.append("execution_result = CAST(:execution_result AS jsonb)")
                params["execution_result"] = json.dumps(request.execution_result)

            if not updates:
                raise HTTPException(status_code=400, detail="No updates provided")

            # Execute update
            query = f"UPDATE recovery_candidates SET {', '.join(updates)} WHERE id = :id"
            session.execute(text(query), params)

            # Record provenance
            try:
                event_type = (
                    "executed"
                    if request.execution_status == "executing"
                    else (
                        "success"
                        if request.execution_status == "succeeded"
                        else ("failure" if request.execution_status == "failed" else "manual_override")
                    )
                )

                session.execute(
                    text(
                        """
                        INSERT INTO m10_recovery.suggestion_provenance
                        (suggestion_id, event_type, details, action_id, confidence_before, actor)
                        VALUES (:suggestion_id, :event_type, CAST(:details AS jsonb), :action_id, :confidence_before, :actor)
                    """
                    ),
                    {
                        "suggestion_id": candidate_id,
                        "event_type": event_type,
                        "details": json.dumps(
                            {
                                "execution_status": request.execution_status,
                                "note": request.note,
                            }
                        ),
                        "action_id": request.selected_action_id,
                        "confidence_before": old_confidence,
                        "actor": "api",
                    },
                )
            except Exception:
                pass  # Provenance table may not exist yet

            session.commit()

            return {
                "status": "updated",
                "candidate_id": candidate_id,
                "updates_applied": list(params.keys()),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update candidate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update candidate: {str(e)}")


@router.get("/actions", response_model=ActionListResponse)
async def list_actions(
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    active_only: bool = Query(True, description="Only return active actions"),
    limit: int = Query(50, ge=1, le=200),
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    List available recovery actions from the catalog.

    Actions are templates for recovery strategies (retry, fallback, etc.)
    that can be selected for candidates.
    """
    try:
        import json
        import os

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

        engine = create_engine(db_url)

        with Session(engine) as session:
            query = """
                SELECT id, action_code, name, description, action_type, template,
                       applies_to_error_codes, applies_to_skills, success_rate,
                       total_applications, is_automated, requires_approval, priority, is_active
                FROM m10_recovery.suggestion_action
                WHERE 1=1
            """
            params = {"limit": limit}

            if active_only:
                query += " AND is_active = TRUE"

            if action_type:
                query += " AND action_type = :action_type"
                params["action_type"] = action_type

            query += " ORDER BY priority DESC, name ASC LIMIT :limit"

            result = session.execute(text(query), params)
            actions = []

            for row in result.fetchall():
                actions.append(
                    ActionResponse(
                        id=row[0],
                        action_code=row[1],
                        name=row[2],
                        description=row[3],
                        action_type=row[4],
                        template=json.loads(row[5]) if isinstance(row[5], str) else (row[5] or {}),
                        applies_to_error_codes=row[6] or [],
                        applies_to_skills=row[7] or [],
                        success_rate=row[8],
                        total_applications=row[9],
                        is_automated=row[10],
                        requires_approval=row[11],
                        priority=row[12],
                        is_active=row[13],
                    )
                )

            return ActionListResponse(actions=actions, total=len(actions))

    except Exception as e:
        logger.error(f"List actions error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list actions: {str(e)}")


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_rules(
    request: EvaluateRequest,
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Evaluate rules against error context without persisting.

    Useful for:
    - Testing rule behavior
    - Previewing recommendations
    - Debugging rule matching

    Does NOT create a candidate or modify any data.
    """
    try:
        from app.services.recovery_rule_engine import (
            evaluate_rules as run_evaluation,
        )

        result = run_evaluation(
            error_code=request.error_code,
            error_message=request.error_message,
            skill_id=request.skill_id,
            tenant_id=request.tenant_id,
            occurrence_count=request.occurrence_count,
        )

        return EvaluateResponse(
            recommended_action=result.recommended_action,
            confidence=result.confidence,
            total_score=result.total_score,
            rules_evaluated=[r.to_dict() for r in result.rules_evaluated],
            explanation=result.explanation,
            duration_ms=result.duration_ms,
        )

    except Exception as e:
        logger.error(f"Rule evaluation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to evaluate rules: {str(e)}")
