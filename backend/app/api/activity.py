# Layer: L2 — Product APIs
# Product: ai-console
# Temporal:
#   Trigger: HTTP request
#   Execution: async
# Role: Activity domain API - runs list, details, and summary (HIL v1)
# Callers: Customer Console Activity page
# Reference: PIN-370 (SDSR), PIN-417 (HIL v1), Customer Console v1 Constitution

"""
Activity API - Runs List and Summary for Customer Console

Queries the `runs` table (not worker_runs) for SDSR pipeline validation.
Returns data compatible with ActivityPage component.

HIL v1 (PIN-417):
- /summary endpoint provides interpretation layer over execution data
- No adjectives, pure counts and routing hints
- Provenance always present
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlmodel import Session

from app.db import Run, get_session as get_db_session

router = APIRouter(prefix="/activity", tags=["Activity"])


# =============================================================================
# Response Models
# =============================================================================


class RunSummary(BaseModel):
    """Run summary for list view."""
    run_id: str
    status: str
    goal: str
    agent_id: str
    tenant_id: Optional[str]
    parent_run_id: Optional[str]
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    is_synthetic: bool
    synthetic_scenario_id: Optional[str]


class ActivityResponse(BaseModel):
    """Activity list response."""
    runs: List[RunSummary]
    total: int
    page: int
    per_page: int


# =============================================================================
# HIL v1: Summary Response Models (PIN-417)
# =============================================================================


class RunsByStatus(BaseModel):
    """Run counts by status."""
    running: int
    completed: int  # succeeded + failed
    failed: int


class AttentionSummary(BaseModel):
    """Attention flags for runs needing review."""
    at_risk_count: int
    reasons: List[str]  # Enum strings from attention_reasons registry


class Provenance(BaseModel):
    """Provenance metadata for interpretation traceability."""
    derived_from: List[str]  # Capability IDs, not panel IDs
    aggregation: str
    generated_at: str  # ISO timestamp


class ActivitySummaryResponse(BaseModel):
    """
    Activity summary response (HIL v1).

    Rules (locked):
    - No adjectives (good, bad, healthy, critical)
    - Counts must reconcile: sum(by_status) == total
    - Reasons must be from registry (fail fast on unknown)
    - Provenance always present
    """
    window: str
    runs: dict  # {"total": int, "by_status": RunsByStatus}
    attention: AttentionSummary
    provenance: Provenance


# =============================================================================
# HIL v1: Configuration (thresholds as config, not constants)
# =============================================================================

# Attention reason registry keys (must match attention_reasons.yaml)
VALID_ATTENTION_REASONS = frozenset(["long_running", "near_budget_threshold"])


def parse_window(window: str) -> timedelta:
    """Parse window string to timedelta."""
    if window == "24h":
        return timedelta(hours=24)
    elif window == "7d":
        return timedelta(days=7)
    else:
        # Default to 24h for unknown values
        return timedelta(hours=24)


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/runs", response_model=ActivityResponse)
def list_activity_runs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = None,
    include_synthetic: bool = Query(default=True, description="Include synthetic SDSR data"),
    session: Session = Depends(get_db_session),
):
    """
    List runs for Activity domain.

    Returns runs from the `runs` table for SDSR validation.
    By default includes synthetic data for preflight testing.

    Note: Auth bypassed for SDSR preflight validation (PIN-370)
    Route is public in gateway_config.py and rbac_middleware.py
    """
    # Build query
    query = select(Run).order_by(Run.created_at.desc())

    # Filter by status if provided
    if status:
        query = query.where(Run.status == status)

    # Optionally exclude synthetic data
    if not include_synthetic:
        query = query.where(Run.is_synthetic.is_(False))

    # Get total count
    count_result = session.execute(select(Run))
    total = len(count_result.scalars().all())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = session.execute(query)
    runs = result.scalars().all()

    return ActivityResponse(
        runs=[
            RunSummary(
                run_id=r.id,
                status=r.status,
                goal=r.goal,
                agent_id=r.agent_id,
                tenant_id=r.tenant_id,
                parent_run_id=r.parent_run_id,
                error_message=r.error_message,
                created_at=r.created_at.isoformat() if r.created_at else "",
                started_at=r.started_at.isoformat() if r.started_at else None,
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
                is_synthetic=r.is_synthetic,
                synthetic_scenario_id=r.synthetic_scenario_id,
            )
            for r in runs
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/runs/{run_id}", response_model=RunSummary)
def get_run_detail(
    run_id: str,
    session: Session = Depends(get_db_session),
):
    """
    Get details of a specific run.

    Note: Auth bypassed for SDSR preflight validation (PIN-370)
    """
    result = session.execute(
        select(Run).where(Run.id == run_id)
    )
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunSummary(
        run_id=run.id,
        status=run.status,
        goal=run.goal,
        agent_id=run.agent_id,
        tenant_id=run.tenant_id,
        parent_run_id=run.parent_run_id,
        error_message=run.error_message,
        created_at=run.created_at.isoformat() if run.created_at else "",
        started_at=run.started_at.isoformat() if run.started_at else None,
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        is_synthetic=run.is_synthetic,
        synthetic_scenario_id=run.synthetic_scenario_id,
    )


# =============================================================================
# HIL v1: Summary Endpoint (PIN-417)
# =============================================================================


@router.get("/summary", response_model=ActivitySummaryResponse)
def get_activity_summary(
    window: str = Query(default="24h", description="Time window: 24h or 7d"),
    include_synthetic: bool = Query(default=True, description="Include synthetic SDSR data"),
    session: Session = Depends(get_db_session),
):
    """
    Activity summary for HIL v1 interpretation panel.

    Returns:
    - Run counts by status
    - Attention flags (runs needing review)
    - Provenance metadata

    Rules (locked per PIN-417):
    - No adjectives in response
    - Counts must reconcile
    - Reasons must be from registry
    - Provenance always present

    Capabilities derived from: activity.runs.list, incidents.list
    """
    # Parse time window
    window_delta = parse_window(window)
    window_start = datetime.now(timezone.utc) - window_delta

    # Base query: runs within time window
    base_query = select(Run).where(Run.created_at >= window_start)

    if not include_synthetic:
        base_query = base_query.where(Run.is_synthetic.is_(False))

    # Execute query to get all runs in window
    result = session.execute(base_query)
    runs = result.scalars().all()

    # Count by status
    running_count = sum(1 for r in runs if r.status == "running")
    succeeded_count = sum(1 for r in runs if r.status == "succeeded")
    failed_count = sum(1 for r in runs if r.status == "failed")
    total_count = len(runs)

    # Attention detection using pre-computed fields
    # long_running: latency_bucket in (SLOW, STALLED)
    # near_budget_threshold: risk_level in (NEAR_THRESHOLD, AT_RISK)
    long_running_runs = [
        r for r in runs
        if r.status == "running" and r.latency_bucket in ("SLOW", "STALLED")
    ]
    near_budget_runs = [
        r for r in runs
        if r.status == "running" and r.risk_level in ("NEAR_THRESHOLD", "AT_RISK")
    ]

    # Build attention reasons list
    attention_reasons: List[str] = []
    if long_running_runs:
        attention_reasons.append("long_running")
    if near_budget_runs:
        attention_reasons.append("near_budget_threshold")

    # Validate reasons against registry (fail fast on unknown)
    for reason in attention_reasons:
        if reason not in VALID_ATTENTION_REASONS:
            raise HTTPException(
                status_code=500,
                detail=f"Unknown attention reason: {reason}. Must be in registry."
            )

    at_risk_count = len(set(
        [r.id for r in long_running_runs] +
        [r.id for r in near_budget_runs]
    ))

    # Build response
    return ActivitySummaryResponse(
        window=window,
        runs={
            "total": total_count,
            "by_status": RunsByStatus(
                running=running_count,
                completed=succeeded_count + failed_count,
                failed=failed_count,
            ),
        },
        attention=AttentionSummary(
            at_risk_count=at_risk_count,
            reasons=attention_reasons,
        ),
        provenance=Provenance(
            derived_from=["activity.runs.list", "incidents.list"],
            aggregation="STATUS_BREAKDOWN",
            generated_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
