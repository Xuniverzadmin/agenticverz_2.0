# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# PHASE: W4
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified LIFECYCLE facade - L2 API for lifecycle operations
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-131 to GAP-136 (Lifecycle APIs)
# GOVERNANCE NOTE:
# This is the ONE facade for LIFECYCLE domain.
# All lifecycle flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Lifecycle API (L2)

Provides lifecycle operations:
- POST /api/v1/lifecycle/agents (create agent)
- GET /api/v1/lifecycle/agents (list agents)
- GET /api/v1/lifecycle/agents/{id} (get agent)
- POST /api/v1/lifecycle/agents/{id}/start (start agent)
- POST /api/v1/lifecycle/agents/{id}/stop (stop agent)
- POST /api/v1/lifecycle/agents/{id}/terminate (terminate agent)
- POST /api/v1/lifecycle/runs (create run)
- GET /api/v1/lifecycle/runs (list runs)
- GET /api/v1/lifecycle/runs/{id} (get run)
- POST /api/v1/lifecycle/runs/{id}/pause (pause run)
- POST /api/v1/lifecycle/runs/{id}/resume (resume run)
- POST /api/v1/lifecycle/runs/{id}/cancel (cancel run)
- GET /api/v1/lifecycle/summary (lifecycle summary)

This is the ONLY facade for lifecycle operations.
All lifecycle APIs flow through this router.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L5 engine imports (V2.0.0 - hoc_spine)
from app.hoc.cus.hoc_spine.services.lifecycle_facade import (
    LifecycleFacade,
    get_lifecycle_facade,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/lifecycle", tags=["Lifecycle"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateAgentRequest(BaseModel):
    """Request to create an agent."""
    name: str = Field(..., description="Agent name")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CreateRunRequest(BaseModel):
    """Request to create a run."""
    agent_id: str = Field(..., description="Agent ID")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# =============================================================================
# Dependencies
# =============================================================================


def get_facade() -> LifecycleFacade:
    """Get the lifecycle facade."""
    return get_lifecycle_facade()


# =============================================================================
# Agent Endpoints (GAP-131, GAP-132)
# =============================================================================


@router.post("/agents", response_model=Dict[str, Any])
async def create_agent(
    request: CreateAgentRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.write")),
):
    """
    Create a new agent (GAP-131).
    """
    agent = await facade.create_agent(
        tenant_id=ctx.tenant_id,
        name=request.name,
        config=request.config,
        metadata=request.metadata,
    )

    return wrap_dict(agent.to_dict())


@router.get("/agents", response_model=Dict[str, Any])
async def list_agents(
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.read")),
):
    """
    List agents (GAP-131).

    Returns all agents for the tenant.
    """
    agents = await facade.list_agents(
        tenant_id=ctx.tenant_id,
        state=state,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "agents": [a.to_dict() for a in agents],
        "total": len(agents),
        "limit": limit,
        "offset": offset,
    })


@router.get("/agents/{agent_id}", response_model=Dict[str, Any])
async def get_agent(
    agent_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.read")),
):
    """
    Get a specific agent (GAP-131).
    """
    agent = await facade.get_agent(
        agent_id=agent_id,
        tenant_id=ctx.tenant_id,
    )

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return wrap_dict(agent.to_dict())


@router.post("/agents/{agent_id}/start", response_model=Dict[str, Any])
async def start_agent(
    agent_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.admin")),
):
    """
    Start an agent (GAP-132).

    **Requires admin permissions.**
    """
    agent = await facade.start_agent(
        agent_id=agent_id,
        tenant_id=ctx.tenant_id,
    )

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return wrap_dict(agent.to_dict())


@router.post("/agents/{agent_id}/stop", response_model=Dict[str, Any])
async def stop_agent(
    agent_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.admin")),
):
    """
    Stop an agent (GAP-132).

    **Requires admin permissions.**
    """
    agent = await facade.stop_agent(
        agent_id=agent_id,
        tenant_id=ctx.tenant_id,
    )

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return wrap_dict(agent.to_dict())


@router.post("/agents/{agent_id}/terminate", response_model=Dict[str, Any])
async def terminate_agent(
    agent_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.admin")),
):
    """
    Terminate an agent (GAP-132).

    **Requires admin permissions.**
    """
    agent = await facade.terminate_agent(
        agent_id=agent_id,
        tenant_id=ctx.tenant_id,
    )

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return wrap_dict(agent.to_dict())


# =============================================================================
# Run Endpoints (GAP-133, GAP-134, GAP-135, GAP-136)
# =============================================================================


@router.post("/runs", response_model=Dict[str, Any])
async def create_run(
    request: CreateRunRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.write")),
):
    """
    Create a new run (GAP-133).
    """
    run = await facade.create_run(
        tenant_id=ctx.tenant_id,
        agent_id=request.agent_id,
        input_data=request.input_data,
        metadata=request.metadata,
    )

    if not run:
        raise HTTPException(status_code=404, detail="Agent not found")

    return wrap_dict(run.to_dict())


@router.get("/runs", response_model=Dict[str, Any])
async def list_runs(
    agent_id: Optional[str] = Query(None, description="Filter by agent"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.read")),
):
    """
    List runs (GAP-133).

    Returns all runs for the tenant.
    """
    runs = await facade.list_runs(
        tenant_id=ctx.tenant_id,
        agent_id=agent_id,
        state=state,
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
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.read")),
):
    """
    Get a specific run (GAP-133).
    """
    run = await facade.get_run(
        run_id=run_id,
        tenant_id=ctx.tenant_id,
    )

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return wrap_dict(run.to_dict())


@router.post("/runs/{run_id}/pause", response_model=Dict[str, Any])
async def pause_run(
    run_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.admin")),
):
    """
    Pause a run (GAP-134).

    **Requires admin permissions.**
    """
    run = await facade.pause_run(
        run_id=run_id,
        tenant_id=ctx.tenant_id,
    )

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return wrap_dict(run.to_dict())


@router.post("/runs/{run_id}/resume", response_model=Dict[str, Any])
async def resume_run(
    run_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.admin")),
):
    """
    Resume a paused run (GAP-135).

    **Requires admin permissions.**
    """
    run = await facade.resume_run(
        run_id=run_id,
        tenant_id=ctx.tenant_id,
    )

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return wrap_dict(run.to_dict())


@router.post("/runs/{run_id}/cancel", response_model=Dict[str, Any])
async def cancel_run(
    run_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.admin")),
):
    """
    Cancel a run (GAP-136).

    **Requires admin permissions.**
    """
    run = await facade.cancel_run(
        run_id=run_id,
        tenant_id=ctx.tenant_id,
    )

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return wrap_dict(run.to_dict())


# =============================================================================
# Summary Endpoint
# =============================================================================


@router.get("/summary", response_model=Dict[str, Any])
async def get_summary(
    ctx: TenantContext = Depends(get_tenant_context),
    facade: LifecycleFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("lifecycle.read")),
):
    """
    Get lifecycle summary.

    Returns summary of agents and runs for the tenant.
    """
    summary = await facade.get_summary(tenant_id=ctx.tenant_id)

    return wrap_dict(summary.to_dict())
