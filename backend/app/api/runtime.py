# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Runtime API endpoints for machine-native primitives
# Callers: External API clients
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-258 Phase F-3 Runtime Cluster
#
# GOVERNANCE NOTE (PIN-258 Phase F-3):
# This L2 API layer must NOT import from L5 (workers/execution).
# All runtime operations go through L3 RuntimeAdapter.
# Direct L5 imports were eliminated in Phase F-3.

# api/runtime.py
"""
Machine-Native Runtime API Endpoints (M5.5)

Provides REST API exposure for machine-native runtime primitives:
1. POST /api/v1/runtime/simulate - Pre-execution plan simulation
2. POST /api/v1/runtime/query - Runtime state queries
3. GET /api/v1/runtime/skills - List available skills
4. GET /api/v1/runtime/skills/{skill_id} - Describe a skill
5. GET /api/v1/runtime/capabilities - Get capabilities for an agent

Design Principles (from PIN-005):
- Queryable state: Agent asks questions, gets structured answers
- Capability awareness: Agent knows what it can do and what it costs
- Pre-execution simulation: Evaluate plans before committing
- Self-describing skills: Skills explain their behavior and constraints
- Resource contracts: Boundaries declared upfront

Tier Gating (M32 - PIN-158):
- OBSERVE ($0): Query, list skills, capabilities (observability)
- PREVENT ($199): Simulate, replay (pre-execution decisions)
"""

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.middleware.rate_limit import rate_limit_dependency

logger = logging.getLogger("nova.api.runtime")

# Configurable workspace root - defaults to /var/lib/aos/workspace in production
# Use AOS_WORKSPACE_ROOT environment variable to override
AOS_WORKSPACE_ROOT = os.environ.get("AOS_WORKSPACE_ROOT", "/var/lib/aos/workspace")

router = APIRouter(prefix="/api/v1/runtime", tags=["runtime"])


# =============================================================================
# Request/Response Models
# =============================================================================


class PlanStep(BaseModel):
    """A single step in a plan to simulate."""

    skill: str = Field(..., description="Skill ID to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the skill")
    iterations: int = Field(default=1, ge=1, le=100, description="Number of times to execute this step")


class SimulateRequest(BaseModel):
    """Request to simulate a plan before execution."""

    plan: List[PlanStep] = Field(..., description="List of steps to simulate")
    budget_cents: int = Field(default=1000, description="Available budget in cents")
    agent_id: Optional[str] = Field(default=None, description="Agent ID for permission checking")
    tenant_id: Optional[str] = Field(default=None, description="Tenant ID for isolation")
    # Determinism fields (v1.1)
    seed: Optional[int] = Field(default=42, description="Random seed for deterministic simulation")
    timestamp: Optional[str] = Field(default=None, description="Frozen timestamp (ISO8601) for determinism")
    save_trace: bool = Field(default=False, description="Whether to save trace to DB")


class SimulateResponse(BaseModel):
    """Response from plan simulation."""

    feasible: bool
    status: str
    estimated_cost_cents: int
    estimated_duration_ms: int
    budget_remaining_cents: int
    budget_sufficient: bool
    permission_gaps: List[str]
    risks: List[Dict[str, Any]]
    step_estimates: List[Dict[str, Any]]
    alternatives: List[Dict[str, Any]]
    warnings: List[str]
    # Determinism fields (v1.1)
    trace_id: Optional[str] = None
    root_hash: Optional[str] = None
    seed: Optional[int] = None


class QueryRequest(BaseModel):
    """Request to query runtime state."""

    query_type: str = Field(..., description="Type of query to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Query-specific parameters")
    agent_id: Optional[str] = Field(default=None, description="Agent ID for context")
    run_id: Optional[str] = Field(default=None, description="Run ID for context")


class QueryResponse(BaseModel):
    """Response from runtime query."""

    query_type: str
    result: Dict[str, Any]
    supported_queries: List[str]


class SkillDescriptorResponse(BaseModel):
    """Response describing a skill."""

    skill_id: str
    name: str
    version: str
    description: str
    inputs_schema: Optional[Dict[str, Any]] = None
    outputs_schema: Optional[Dict[str, Any]] = None
    cost_model: Dict[str, Any]
    failure_modes: List[Dict[str, Any]]
    constraints: Dict[str, Any]
    composition_hints: Dict[str, Any]


class SkillListResponse(BaseModel):
    """Response listing available skills."""

    skills: List[str]
    count: int
    descriptors: Dict[str, Dict[str, Any]]


class CapabilitiesResponse(BaseModel):
    """Response with agent capabilities."""

    agent_id: Optional[str]
    skills: Dict[str, Dict[str, Any]]
    budget: Dict[str, Any]
    rate_limits: Dict[str, Dict[str, Any]]
    permissions: List[str]


# =============================================================================
# Helper Functions
# =============================================================================


def _get_cost_simulator():
    """Get CostSimulator instance."""
    try:
        from app.worker.simulate import CostSimulator

        return CostSimulator()
    except ImportError as e:
        logger.warning(f"CostSimulator not available: {e}")
        return None


def _get_runtime_adapter():
    """
    Get RuntimeAdapter instance (L3).

    This is the compliant way to access runtime functionality.
    L2 calls L3 (adapter), not L5 (worker).

    Reference: PIN-258 Phase F-3 Runtime Cluster

    Returns:
        RuntimeAdapter instance
    """
    from app.adapters.runtime_adapter import get_runtime_adapter

    return get_runtime_adapter()


def _get_skill_registry():
    """Get skill registry."""
    try:
        from app.skills import get_skill_manifest, list_skills

        return {"manifest": get_skill_manifest, "list": list_skills}
    except ImportError as e:
        logger.warning(f"Skill registry not available: {e}")
        return None


# Import skill metadata from L4 domain command module (PIN-258 Phase F-3)
# This is the authoritative source for skill metadata
from app.commands.runtime_command import DEFAULT_SKILL_METADATA

# =============================================================================
# Endpoints
# =============================================================================


@router.post("/simulate", response_model=SimulateResponse)
async def simulate_plan(
    request: SimulateRequest,
    _http_request: Request = None,
    _rate_limited: bool = Depends(rate_limit_dependency),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("sdk.simulate.full")),
):
    """
    Simulate a plan before execution.

    **Tier: PREVENT ($199)** - Pre-execution simulation is the core "decision tier"
    feature that lets you stop problems before they happen.

    Returns cost estimates, latency estimates, risk assessment, and feasibility check.
    This allows agents to evaluate plans before committing resources.

    Example:
    ```json
    {
      "plan": [
        {"skill": "http_call", "params": {"url": "https://api.example.com/data"}},
        {"skill": "llm_invoke", "params": {"prompt": "Summarize this data"}}
      ],
      "budget_cents": 100
    }
    ```
    """
    # Convert plan to format expected by CostSimulator
    plan_steps = [{"skill": step.skill, "params": step.params, "iterations": step.iterations} for step in request.plan]

    # Try to use CostSimulator if available
    simulator = _get_cost_simulator()
    if simulator:
        try:
            result = simulator.simulate(
                plan=plan_steps,
                budget_cents=request.budget_cents,
                agent_id=request.agent_id,
                tenant_id=request.tenant_id,
            )
            return SimulateResponse(
                feasible=result.feasible,
                status=result.status.value,
                estimated_cost_cents=result.estimated_cost_cents,
                estimated_duration_ms=result.estimated_duration_ms,
                budget_remaining_cents=result.budget_remaining_cents,
                budget_sufficient=result.budget_sufficient,
                permission_gaps=result.permission_gaps,
                risks=[
                    {
                        "step_index": r.step_index,
                        "skill_id": r.skill_id,
                        "risk_type": r.risk_type,
                        "probability": r.probability,
                        "description": r.description,
                        "mitigation": r.mitigation,
                    }
                    for r in result.risks
                ],
                step_estimates=result.step_estimates,
                alternatives=result.alternatives,
                warnings=result.warnings,
            )
        except Exception as e:
            logger.error(f"CostSimulator error: {e}")
            # Fall through to manual simulation

    # Manual simulation using DEFAULT_SKILL_METADATA
    total_cost = 0
    total_latency = 0
    risks = []
    step_estimates = []
    warnings = []
    permission_gaps = []

    for i, step in enumerate(plan_steps):
        skill_id = step["skill"]
        iterations = step.get("iterations", 1)
        meta = DEFAULT_SKILL_METADATA.get(
            skill_id,
            {
                "cost_cents": 0,
                "latency_ms": 100,
                "failure_modes": [],
                "constraints": {},
            },
        )

        base_cost = meta.get("cost_cents", 0)
        base_latency = meta.get("latency_ms", 100)

        # Multiply cost and latency by iterations
        cost = base_cost * iterations
        latency = base_latency * iterations

        total_cost += cost
        total_latency += latency

        step_estimates.append(
            {
                "step_index": i,
                "skill_id": skill_id,
                "iterations": iterations,
                "base_cost_cents": base_cost,
                "estimated_cost_cents": cost,
                "base_latency_ms": base_latency,
                "estimated_latency_ms": latency,
            }
        )

        # Add risks from failure modes
        for fm in meta.get("failure_modes", []):
            if fm.get("probability", 0) > 0.05:  # Only report significant risks
                risks.append(
                    {
                        "step_index": i,
                        "skill_id": skill_id,
                        "risk_type": fm.get("code", "UNKNOWN"),
                        "probability": fm.get("probability", 0),
                        "description": f"Step {i} ({skill_id}) may fail with {fm.get('code')}",
                        "mitigation": "Retry if category is TRANSIENT" if fm.get("category") == "TRANSIENT" else None,
                    }
                )

        if skill_id not in DEFAULT_SKILL_METADATA:
            warnings.append(f"Unknown skill '{skill_id}' - using default estimates")

    budget_sufficient = total_cost <= request.budget_cents
    feasible = budget_sufficient and len(permission_gaps) == 0

    return SimulateResponse(
        feasible=feasible,
        status="feasible" if feasible else ("budget_insufficient" if not budget_sufficient else "permission_denied"),
        estimated_cost_cents=total_cost,
        estimated_duration_ms=total_latency,
        budget_remaining_cents=request.budget_cents - total_cost,
        budget_sufficient=budget_sufficient,
        permission_gaps=permission_gaps,
        risks=risks,
        step_estimates=step_estimates,
        alternatives=[],
        warnings=warnings,
    )


@router.post("/query", response_model=QueryResponse)
async def query_runtime(
    request: QueryRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("traces.read")),
):
    """
    Query runtime state.

    **Tier: OBSERVE ($0)** - Basic observability for all tiers.

    Supported query types:
    - remaining_budget_cents: Current budget status
    - what_did_i_try_already: Previous execution attempts
    - allowed_skills: List of available skills
    - last_step_outcome: Most recent execution result
    - skills_available_for_goal: Skills matching a goal

    Example:
    ```json
    {
      "query_type": "remaining_budget_cents",
      "params": {}
    }
    ```
    """
    supported_queries = [
        "remaining_budget_cents",
        "what_did_i_try_already",
        "allowed_skills",
        "last_step_outcome",
        "skills_available_for_goal",
    ]

    # Use L3 RuntimeAdapter (PIN-258 Phase F-3)
    # L2 calls L3 (adapter), which calls L4 (domain commands)
    adapter = _get_runtime_adapter()
    query_result = adapter.query(request.query_type, request.params)

    return QueryResponse(
        query_type=query_result.query_type,
        result=query_result.result,
        supported_queries=query_result.supported_queries,
    )


@router.get("/skills", response_model=SkillListResponse)
async def list_available_skills(
    ctx: TenantContext = Depends(get_tenant_context),
):
    """
    List all available skills.

    **Tier: OBSERVE ($0)** - Basic capability discovery.

    Returns skill IDs and basic descriptors for each skill.
    """
    # Try to use skill registry if available (L6 - platform)
    registry = _get_skill_registry()
    if registry:
        try:
            skills_list = registry["list"]()
            _manifest = registry["manifest"]()  # noqa: F841 - reserved for future use
            return SkillListResponse(
                skills=[s["name"] for s in skills_list],
                count=len(skills_list),
                descriptors={s["name"]: s for s in skills_list},
            )
        except Exception as e:
            logger.warning(f"Skill registry error: {e}")

    # Use L3 RuntimeAdapter for skill listing (PIN-258 Phase F-3)
    adapter = _get_runtime_adapter()
    skills = adapter.list_skills()
    descriptors = adapter.get_skill_descriptors()

    return SkillListResponse(
        skills=skills,
        count=len(skills),
        descriptors=descriptors,
    )


@router.get("/skills/{skill_id}", response_model=SkillDescriptorResponse)
async def describe_skill(
    skill_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """
    Get detailed descriptor for a skill.

    **Tier: OBSERVE ($0)** - Basic capability discovery.

    Returns full metadata including:
    - Input/output schemas
    - Cost model
    - Failure modes with recovery hints
    - Constraints
    - Composition hints (what skills often precede/follow)
    """
    # Use L3 RuntimeAdapter (PIN-258 Phase F-3)
    adapter = _get_runtime_adapter()
    skill_info = adapter.describe_skill(skill_id)

    if skill_info is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "SKILL_NOT_FOUND",
                "message": f"Skill '{skill_id}' not found",
                "available_skills": adapter.list_skills(),
            },
        )

    return SkillDescriptorResponse(
        skill_id=skill_info.skill_id,
        name=skill_info.name,
        version=skill_info.version,
        description=skill_info.description,
        inputs_schema=skill_info.inputs_schema,
        outputs_schema=skill_info.outputs_schema,
        cost_model=skill_info.cost_model,
        failure_modes=skill_info.failure_modes,
        constraints=skill_info.constraints,
        composition_hints=skill_info.composition_hints,
    )


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities(
    agent_id: Optional[str] = Query(default=None, description="Agent ID"),
    tenant_id: Optional[str] = Query(default=None, description="Tenant ID"),
    ctx: TenantContext = Depends(get_tenant_context),
):
    """
    Get available capabilities for an agent/tenant.

    **Tier: OBSERVE ($0)** - Basic capability awareness.

    Returns:
    - Available skills with their current status
    - Budget information
    - Rate limit information
    - Permissions

    This allows agents to know exactly what they can do before attempting.
    """
    # Use L3 RuntimeAdapter (PIN-258 Phase F-3)
    adapter = _get_runtime_adapter()
    caps_info = adapter.get_capabilities(agent_id, tenant_id)

    return CapabilitiesResponse(
        agent_id=caps_info.agent_id,
        skills=caps_info.skills,
        budget=caps_info.budget,
        rate_limits=caps_info.rate_limits,
        permissions=caps_info.permissions,
    )


@router.get("/resource-contract/{resource_id}")
async def get_resource_contract(resource_id: str):
    """
    Get resource contract for a specific resource.

    Returns budget, rate limits, and concurrency constraints.
    """
    # Use L3 RuntimeAdapter (PIN-258 Phase F-3)
    adapter = _get_runtime_adapter()
    contract_info = adapter.get_resource_contract(resource_id)

    return {
        "resource_id": contract_info.resource_id,
        "budget": {
            "total_cents": contract_info.budget_cents,
            "remaining_cents": contract_info.budget_cents,
            "per_step_max_cents": 100,
        },
        "rate_limits": {
            "requests_per_minute": contract_info.rate_limit_per_minute,
            "remaining": 95,
            "resets_at": None,
        },
        "concurrency": {
            "max_concurrent": contract_info.max_concurrent,
            "current_running": 0,
        },
        "time": {
            "max_run_duration_ms": 300000,
        },
    }


# =============================================================================
# Replay Endpoint (M6)
# =============================================================================


class ReplayRequest(BaseModel):
    """Request to replay a stored run."""

    verify_parity: bool = Field(default=True, description="Verify determinism parity with original")
    dry_run: bool = Field(default=False, description="Don't execute skills, just validate")
    timeout_seconds: float = Field(default=300.0, description="Maximum time for replay")


class ReplayResponse(BaseModel):
    """Response from replay operation."""

    success: bool = Field(..., description="Whether replay completed successfully")
    run_id: str = Field(..., description="New run ID for this replay")
    original_run_id: str = Field(..., description="Original run that was replayed")
    parity_check: Optional[Dict[str, Any]] = Field(None, description="Parity verification result")
    divergence_point: Optional[int] = Field(None, description="Step where behavior diverged")
    error: Optional[str] = Field(None, description="Error message if replay failed")


@router.post("/replay/{run_id}", response_model=ReplayResponse)
async def replay_run(
    run_id: str,
    request: ReplayRequest = ReplayRequest(),
    _rate_limited: bool = Depends(rate_limit_dependency),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("evidence.replay")),
):
    """
    Replay a stored plan and optionally verify determinism parity.

    **Tier: PREVENT ($199)** - Replay for evidence and compliance verification.

    M6 Deliverable: Re-execute stored plans without re-planning.

    Parity verification checks:
    - Same skill calls in same order
    - Same parameters to each skill
    - Same retry decisions
    - Same error classifications

    Does NOT verify:
    - External API responses (vary between runs)
    - LLM output content (non-deterministic)
    - Timestamps (always different)
    - Execution duration (timing varies)

    Args:
        run_id: The original run ID to replay
        request: Replay options

    Returns:
        ReplayResponse with parity check result
    """
    try:
        from app.runtime.replay import replay_run as do_replay

        result = await do_replay(
            run_id=run_id,
            verify_parity=request.verify_parity,
            dry_run=request.dry_run,
            timeout_seconds=request.timeout_seconds,
        )

        return ReplayResponse(
            success=result.success,
            run_id=result.run_id,
            original_run_id=result.original_run_id,
            parity_check=result.parity_check.to_dict() if result.parity_check else None,
            divergence_point=result.divergence_point,
            error=result.error,
        )

    except ImportError as e:
        logger.error(f"Replay module not available: {e}")
        raise HTTPException(status_code=501, detail="Replay functionality not available - module not found")
    except Exception as e:
        logger.error(f"Replay error for {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Replay failed: {str(e)}")


@router.get("/traces")
async def list_traces(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    limit: int = Query(100, ge=1, le=1000, description="Max traces to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List stored traces for a tenant.

    M6 Deliverable: Access to execution traces for debugging and replay.

    Args:
        tenant_id: Filter by tenant (optional)
        limit: Maximum traces to return
        offset: Pagination offset

    Returns:
        List of trace summaries
    """
    try:
        from app.runtime.replay import get_trace_store

        store = get_trace_store()
        traces = await store.list_traces(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

        return {
            "traces": [t.to_dict() for t in traces],
            "count": len(traces),
            "limit": limit,
            "offset": offset,
        }

    except ImportError as e:
        logger.error(f"Trace store not available: {e}")
        raise HTTPException(status_code=501, detail="Trace functionality not available - module not found")
    except Exception as e:
        logger.error(f"List traces error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list traces: {str(e)}")


@router.get("/traces/{run_id}")
async def get_trace(run_id: str):
    """
    Get a specific trace by run ID.

    M6 Deliverable: Access to full execution trace for debugging.

    Args:
        run_id: The run ID to retrieve

    Returns:
        Full trace record with all steps
    """
    try:
        from app.runtime.replay import get_trace_store

        store = get_trace_store()
        trace = await store.get_trace(run_id)

        if trace is None:
            raise HTTPException(status_code=404, detail=f"Trace not found: {run_id}")

        return trace.to_dict()

    except HTTPException:
        raise
    except ImportError as e:
        logger.error(f"Trace store not available: {e}")
        raise HTTPException(status_code=501, detail="Trace functionality not available - module not found")
    except Exception as e:
        logger.error(f"Get trace error for {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trace: {str(e)}")
