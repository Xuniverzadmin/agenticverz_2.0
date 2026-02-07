# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified SCHEDULER facade - L2 API for scheduled job operations
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-112 (Scheduled Job API)
# GOVERNANCE NOTE:
# This is the ONE facade for SCHEDULER domain.
# All scheduler flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Scheduler API (L2)

Provides scheduled job operations:
- POST /scheduler/jobs (create job)
- GET /scheduler/jobs (list jobs)
- GET /scheduler/jobs/{id} (get job)
- PUT /scheduler/jobs/{id} (update job)
- DELETE /scheduler/jobs/{id} (delete job)
- POST /scheduler/jobs/{id}/trigger (trigger job)
- POST /scheduler/jobs/{id}/pause (pause job)
- POST /scheduler/jobs/{id}/resume (resume job)
- GET /scheduler/jobs/{id}/runs (job runs)
- GET /scheduler/runs/{id} (get run)

This is the ONLY facade for scheduler operations.
All scheduler APIs flow through this router.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L5 engine imports (V2.0.0 - hoc_spine)
from app.hoc.cus.hoc_spine.services.scheduler_facade import (
    SchedulerFacade,
    get_scheduler_facade,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateJobRequest(BaseModel):
    """Request to create scheduled job."""
    name: str = Field(..., description="Job name")
    schedule: str = Field(..., description="Cron expression (e.g., '0 9 * * *')")
    action: Dict[str, Any] = Field(..., description="Action to perform")
    description: Optional[str] = Field(None, description="Job description")
    enabled: bool = Field(True, description="Whether job is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UpdateJobRequest(BaseModel):
    """Request to update scheduled job."""
    name: Optional[str] = Field(None, description="Job name")
    schedule: Optional[str] = Field(None, description="Cron expression")
    action: Optional[Dict[str, Any]] = Field(None, description="Action to perform")
    description: Optional[str] = Field(None, description="Job description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# =============================================================================
# Dependencies
# =============================================================================


def get_facade() -> SchedulerFacade:
    """Get the scheduler facade."""
    return get_scheduler_facade()


# =============================================================================
# Job Endpoints (GAP-112)
# =============================================================================


@router.post("/jobs", response_model=Dict[str, Any])
async def create_job(
    request: CreateJobRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: SchedulerFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("scheduler.write")),
):
    """
    Create a scheduled job (GAP-112).

    **Tier: REACT ($9)** - Scheduled jobs.

    Schedule format: Standard cron expression
    - Minute (0-59)
    - Hour (0-23)
    - Day of month (1-31)
    - Month (1-12)
    - Day of week (0-7, 0 and 7 are Sunday)

    Example: "0 9 * * *" = Every day at 9:00 AM
    """
    job = await facade.create_job(
        tenant_id=ctx.tenant_id,
        name=request.name,
        schedule=request.schedule,
        action=request.action,
        description=request.description,
        enabled=request.enabled,
        metadata=request.metadata,
    )

    return wrap_dict(job.to_dict())


@router.get("/jobs", response_model=Dict[str, Any])
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: SchedulerFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("scheduler.read")),
):
    """
    List scheduled jobs.
    """
    jobs = await facade.list_jobs(
        tenant_id=ctx.tenant_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "jobs": [j.to_dict() for j in jobs],
        "total": len(jobs),
        "limit": limit,
        "offset": offset,
    })


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job(
    job_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: SchedulerFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("scheduler.read")),
):
    """
    Get a specific scheduled job.
    """
    job = await facade.get_job(
        job_id=job_id,
        tenant_id=ctx.tenant_id,
    )

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return wrap_dict(job.to_dict())


@router.put("/jobs/{job_id}", response_model=Dict[str, Any])
async def update_job(
    job_id: str,
    request: UpdateJobRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: SchedulerFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("scheduler.write")),
):
    """
    Update a scheduled job.
    """
    job = await facade.update_job(
        job_id=job_id,
        tenant_id=ctx.tenant_id,
        name=request.name,
        schedule=request.schedule,
        action=request.action,
        description=request.description,
        metadata=request.metadata,
    )

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return wrap_dict(job.to_dict())


@router.delete("/jobs/{job_id}", response_model=Dict[str, Any])
async def delete_job(
    job_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: SchedulerFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("scheduler.write")),
):
    """
    Delete a scheduled job.
    """
    success = await facade.delete_job(
        job_id=job_id,
        tenant_id=ctx.tenant_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    return wrap_dict({"success": True, "job_id": job_id})


@router.post("/jobs/{job_id}/trigger", response_model=Dict[str, Any])
async def trigger_job(
    job_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: SchedulerFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("scheduler.trigger")),
):
    """
    Trigger a job to run immediately.

    Bypasses the schedule and runs the job now.
    """
    run = await facade.trigger_job(
        job_id=job_id,
        tenant_id=ctx.tenant_id,
    )

    if not run:
        raise HTTPException(status_code=404, detail="Job not found")

    return wrap_dict(run.to_dict())


@router.post("/jobs/{job_id}/pause", response_model=Dict[str, Any])
async def pause_job(
    job_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: SchedulerFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("scheduler.write")),
):
    """
    Pause a scheduled job.

    Stops the job from running on schedule until resumed.
    """
    job = await facade.pause_job(
        job_id=job_id,
        tenant_id=ctx.tenant_id,
    )

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return wrap_dict(job.to_dict())


@router.post("/jobs/{job_id}/resume", response_model=Dict[str, Any])
async def resume_job(
    job_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: SchedulerFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("scheduler.write")),
):
    """
    Resume a paused job.

    Restarts the job's schedule.
    """
    job = await facade.resume_job(
        job_id=job_id,
        tenant_id=ctx.tenant_id,
    )

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return wrap_dict(job.to_dict())


@router.get("/jobs/{job_id}/runs", response_model=Dict[str, Any])
async def list_job_runs(
    job_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: SchedulerFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("scheduler.read")),
):
    """
    List job run history.
    """
    runs = await facade.list_runs(
        job_id=job_id,
        tenant_id=ctx.tenant_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "runs": [r.to_dict() for r in runs],
        "total": len(runs),
        "limit": limit,
        "offset": offset,
    })


@router.get("/runs/{run_id}", response_model=Dict[str, Any])
async def get_run(
    run_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: SchedulerFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("scheduler.read")),
):
    """
    Get a specific job run.
    """
    run = await facade.get_run(
        run_id=run_id,
        tenant_id=ctx.tenant_id,
    )

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return wrap_dict(run.to_dict())
