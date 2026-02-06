"""Phase 4C-1: Founder Timeline View

Raw, chronological consumption of decision records.

Rules:
- Chronological order only
- No grouping
- No collapsing
- No "status pills"
- No interpretation

This is a court transcript, not a dashboard.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# PIN-318: Phase 1.2 Authority Hardening - Add founder auth
from ..auth.console_auth import verify_fops_token
from ..schemas.response import wrap_dict

logger = logging.getLogger("nova.api.founder_timeline")

# PIN-318: Router-level auth - all endpoints require founder token (aud="fops")
router = APIRouter(prefix="/founder/timeline", tags=["founder-timeline"], dependencies=[Depends(verify_fops_token)])


# =============================================================================
# Response Models (Verbatim, No Interpretation)
# =============================================================================


class DecisionRecordView(BaseModel):
    """Raw decision record - all fields exposed to founder."""

    # Identity
    decision_id: str

    # Contract-mandated metadata (DECISION_RECORD_CONTRACT v0.2)
    decision_type: str
    decision_source: str
    decision_trigger: str

    # Decision content
    decision_inputs: Dict[str, Any]
    decision_outcome: str
    decision_reason: Optional[str]

    # Context
    run_id: Optional[str]
    workflow_id: Optional[str]
    tenant_id: str

    # Causal binding (Phase 4B extension)
    request_id: Optional[str]
    causal_role: str

    # Timing
    decided_at: datetime

    # Extended details (type-specific)
    details: Dict[str, Any]


class TimelineEntry(BaseModel):
    """Single entry in the timeline - could be decision, pre-run, or outcome."""

    entry_type: str  # "decision" | "pre_run" | "outcome"
    timestamp: datetime
    record: Dict[str, Any]


class RunTimeline(BaseModel):
    """Complete timeline for a run - raw, chronological."""

    run_id: str
    entries: List[TimelineEntry]
    entry_count: int

    # No aggregation, no scoring, no interpretation
    # Just facts


# =============================================================================
# Database Access
# =============================================================================


def get_db_url() -> Optional[str]:
    """Get database URL from environment."""
    return os.environ.get("DATABASE_URL")


def fetch_run_data(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch run data for PRE-RUN and OUTCOME records.

    PRE-RUN: What was declared before execution started
    OUTCOME: What actually happened
    """
    db_url = get_db_url()
    if not db_url:
        return None

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT
                        id,
                        agent_id,
                        goal,
                        status,
                        attempts,
                        max_attempts,
                        error_message,
                        priority,
                        tenant_id,
                        idempotency_key,
                        parent_run_id,
                        created_at,
                        started_at,
                        completed_at,
                        duration_ms
                    FROM runs
                    WHERE id = :run_id
                """
                ),
                {"run_id": run_id},
            )

            row = result.fetchone()
            if not row:
                return None

            run_data = {
                "id": row.id,
                "agent_id": row.agent_id,
                "goal": row.goal,
                "status": row.status,
                "attempts": row.attempts,
                "max_attempts": row.max_attempts,
                "error_message": row.error_message,
                "priority": row.priority,
                "tenant_id": row.tenant_id,
                "idempotency_key": row.idempotency_key,
                "parent_run_id": row.parent_run_id,
                "created_at": row.created_at,
                "started_at": row.started_at,
                "completed_at": row.completed_at,
                "duration_ms": row.duration_ms,
            }

        engine.dispose()
        return run_data

    except SQLAlchemyError as e:
        logger.warning(f"Failed to fetch run data: {e}")
        return None


def fetch_decision_records(run_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all decision records for a run.

    Returns raw records, chronologically ordered.
    No filtering, no grouping, no interpretation.
    """
    db_url = get_db_url()
    if not db_url:
        return []

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT
                        decision_id,
                        decision_type,
                        decision_source,
                        decision_trigger,
                        decision_inputs,
                        decision_outcome,
                        decision_reason,
                        run_id,
                        workflow_id,
                        tenant_id,
                        request_id,
                        causal_role,
                        decided_at,
                        details
                    FROM contracts.decision_records
                    WHERE run_id = :run_id
                    ORDER BY decided_at ASC
                """
                ),
                {"run_id": run_id},
            )

            records = []
            for row in result:
                records.append(
                    {
                        "decision_id": row.decision_id,
                        "decision_type": row.decision_type,
                        "decision_source": row.decision_source,
                        "decision_trigger": row.decision_trigger,
                        "decision_inputs": row.decision_inputs or {},
                        "decision_outcome": row.decision_outcome,
                        "decision_reason": row.decision_reason,
                        "run_id": row.run_id,
                        "workflow_id": row.workflow_id,
                        "tenant_id": row.tenant_id,
                        "request_id": row.request_id,
                        "causal_role": row.causal_role,
                        "decided_at": row.decided_at,
                        "details": row.details or {},
                    }
                )

        engine.dispose()
        return records

    except SQLAlchemyError as e:
        logger.warning(f"Failed to fetch decision records: {e}")
        return []


def fetch_all_decision_records(
    limit: int = 100,
    offset: int = 0,
    decision_type: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch decision records with optional filtering.

    For founder forensics across runs.
    """
    db_url = get_db_url()
    if not db_url:
        return []

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Build query with optional filters
            where_clauses = ["1=1"]
            params: Dict[str, Any] = {"limit": limit, "offset": offset}

            if decision_type:
                where_clauses.append("decision_type = :decision_type")
                params["decision_type"] = decision_type

            if tenant_id:
                where_clauses.append("tenant_id = :tenant_id")
                params["tenant_id"] = tenant_id

            where_sql = " AND ".join(where_clauses)

            result = conn.execute(
                text(
                    f"""
                    SELECT
                        decision_id,
                        decision_type,
                        decision_source,
                        decision_trigger,
                        decision_inputs,
                        decision_outcome,
                        decision_reason,
                        run_id,
                        workflow_id,
                        tenant_id,
                        request_id,
                        causal_role,
                        decided_at,
                        details
                    FROM contracts.decision_records
                    WHERE {where_sql}
                    ORDER BY decided_at DESC
                    LIMIT :limit OFFSET :offset
                """
                ),
                params,
            )

            records = []
            for row in result:
                records.append(
                    {
                        "decision_id": row.decision_id,
                        "decision_type": row.decision_type,
                        "decision_source": row.decision_source,
                        "decision_trigger": row.decision_trigger,
                        "decision_inputs": row.decision_inputs or {},
                        "decision_outcome": row.decision_outcome,
                        "decision_reason": row.decision_reason,
                        "run_id": row.run_id,
                        "workflow_id": row.workflow_id,
                        "tenant_id": row.tenant_id,
                        "request_id": row.request_id,
                        "causal_role": row.causal_role,
                        "decided_at": row.decided_at,
                        "details": row.details or {},
                    }
                )

        engine.dispose()
        return records

    except SQLAlchemyError as e:
        logger.warning(f"Failed to fetch decision records: {e}")
        return []


# =============================================================================
# Endpoints (Read-Only, No Interpretation)
# =============================================================================


@router.get("/run/{run_id}", response_model=RunTimeline)
async def get_run_timeline(run_id: str) -> RunTimeline:
    """
    Get complete timeline for a run.

    Structure (chronological):
    1. PRE-RUN SNAPSHOT - What was declared before execution
    2. DECISION RECORDS - Each decision made during execution
    3. OUTCOME RECORD - What actually happened

    This is a court transcript.
    Founder uses this to answer: "Did the system behave correctly given its rules?"
    """
    entries = []

    # 1. Fetch run data for PRE-RUN and OUTCOME
    run_data = fetch_run_data(run_id)

    # 2. PRE-RUN SNAPSHOT (first entry)
    if run_data:
        pre_run_snapshot = {
            "run_id": run_data["id"],
            "agent_id": run_data["agent_id"],
            "goal": run_data["goal"],
            "max_attempts": run_data["max_attempts"],
            "priority": run_data["priority"],
            "tenant_id": run_data["tenant_id"],
            "idempotency_key": run_data["idempotency_key"],
            "parent_run_id": run_data["parent_run_id"],
            "declared_at": run_data["created_at"],
        }
        entries.append(
            TimelineEntry(
                entry_type="pre_run",
                timestamp=run_data["created_at"],
                record=pre_run_snapshot,
            )
        )

    # 3. DECISION RECORDS (middle entries, chronological)
    decision_records = fetch_decision_records(run_id)
    for record in decision_records:
        entries.append(
            TimelineEntry(
                entry_type="decision",
                timestamp=record["decided_at"],
                record=record,
            )
        )

    # 4. OUTCOME RECORD (last entry)
    if run_data and run_data["completed_at"]:
        outcome_record = {
            "run_id": run_data["id"],
            "status": run_data["status"],
            "attempts": run_data["attempts"],
            "error_message": run_data["error_message"],
            "started_at": run_data["started_at"],
            "completed_at": run_data["completed_at"],
            "duration_ms": run_data["duration_ms"],
        }
        entries.append(
            TimelineEntry(
                entry_type="outcome",
                timestamp=run_data["completed_at"],
                record=outcome_record,
            )
        )
    elif run_data:
        # Run not yet complete - show placeholder
        outcome_record = {
            "run_id": run_data["id"],
            "status": run_data["status"],
            "attempts": run_data["attempts"],
            "error_message": run_data["error_message"],
            "started_at": run_data["started_at"],
            "completed_at": None,
            "duration_ms": None,
            "pending": True,
        }
        # Use started_at or created_at as timestamp for pending outcome
        outcome_ts = run_data["started_at"] or run_data["created_at"]
        entries.append(
            TimelineEntry(
                entry_type="outcome",
                timestamp=outcome_ts,
                record=outcome_record,
            )
        )

    return RunTimeline(
        run_id=run_id,
        entries=entries,
        entry_count=len(entries),
    )


@router.get("/decisions", response_model=List[DecisionRecordView])
async def list_decision_records(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    decision_type: Optional[str] = Query(None, description="Filter by type: routing, recovery, memory, policy, budget"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
) -> List[DecisionRecordView]:
    """
    List all decision records.

    For founder forensics across runs.
    No aggregation, no scoring.
    Just filtered visibility.
    """
    records = fetch_all_decision_records(
        limit=limit,
        offset=offset,
        decision_type=decision_type,
        tenant_id=tenant_id,
    )

    return [DecisionRecordView(**r) for r in records]


@router.get("/decisions/{decision_id}", response_model=DecisionRecordView)
async def get_decision_record(decision_id: str) -> DecisionRecordView:
    """
    Get a single decision record by ID.

    All fields exposed. No interpretation.
    """
    db_url = get_db_url()
    if not db_url:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT
                        decision_id,
                        decision_type,
                        decision_source,
                        decision_trigger,
                        decision_inputs,
                        decision_outcome,
                        decision_reason,
                        run_id,
                        workflow_id,
                        tenant_id,
                        request_id,
                        causal_role,
                        decided_at,
                        details
                    FROM contracts.decision_records
                    WHERE decision_id = :decision_id
                """
                ),
                {"decision_id": decision_id},
            )

            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Decision record not found")

            record = {
                "decision_id": row.decision_id,
                "decision_type": row.decision_type,
                "decision_source": row.decision_source,
                "decision_trigger": row.decision_trigger,
                "decision_inputs": row.decision_inputs or {},
                "decision_outcome": row.decision_outcome,
                "decision_reason": row.decision_reason,
                "run_id": row.run_id,
                "workflow_id": row.workflow_id,
                "tenant_id": row.tenant_id,
                "request_id": row.request_id,
                "causal_role": row.causal_role,
                "decided_at": row.decided_at,
                "details": row.details or {},
            }

        engine.dispose()
        return DecisionRecordView(**record)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.warning(f"Failed to fetch decision record: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.get("/count")
async def count_decision_records(
    decision_type: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    Count decision records.

    No aggregation beyond counting.
    """
    db_url = get_db_url()
    if not db_url:
        return wrap_dict({"count": 0, "error": "Database not configured"})

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            where_clauses = ["1=1"]
            params: Dict[str, Any] = {}

            if decision_type:
                where_clauses.append("decision_type = :decision_type")
                params["decision_type"] = decision_type

            if tenant_id:
                where_clauses.append("tenant_id = :tenant_id")
                params["tenant_id"] = tenant_id

            where_sql = " AND ".join(where_clauses)

            result = conn.execute(
                text(f"SELECT COUNT(*) FROM contracts.decision_records WHERE {where_sql}"),
                params,
            )

            count = result.scalar() or 0

        engine.dispose()
        return wrap_dict({"count": count})

    except SQLAlchemyError as e:
        logger.warning(f"Failed to count decision records: {e}")
        return wrap_dict({"count": 0, "error": str(e)})
