# Layer: L2 — Product APIs
# Product: ai-console
# Temporal:
#   Trigger: HTTP request
#   Execution: async
# Role: Activity domain API - runs list and details
# Callers: Customer Console Activity page
# Reference: PIN-370 (SDSR), Customer Console v1 Constitution

"""
Activity API - Runs List for Customer Console

Queries the `runs` table (not worker_runs) for SDSR pipeline validation.
Returns data compatible with ActivityPage component.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
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
