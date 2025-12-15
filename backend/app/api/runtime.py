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
"""

import logging
import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel, Field

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


def _get_runtime():
    """Get Runtime instance."""
    try:
        from app.worker.runtime.core import Runtime
        return Runtime()
    except ImportError as e:
        logger.warning(f"Runtime not available: {e}")
        return None


def _get_skill_registry():
    """Get skill registry."""
    try:
        from app.skills import get_skill_manifest, list_skills
        return {"manifest": get_skill_manifest, "list": list_skills}
    except ImportError as e:
        logger.warning(f"Skill registry not available: {e}")
        return None


# Default skill metadata for when registry not available
DEFAULT_SKILL_METADATA = {
    "http_call": {
        "cost_cents": 0,
        "latency_ms": 500,
        "failure_modes": [
            {"code": "TIMEOUT", "category": "TRANSIENT", "probability": 0.1},
            {"code": "DNS_FAILURE", "category": "TRANSIENT", "probability": 0.02},
            {"code": "HTTP_4XX", "category": "PERMANENT", "probability": 0.05},
            {"code": "HTTP_5XX", "category": "TRANSIENT", "probability": 0.03},
        ],
        "constraints": {"max_timeout_ms": 30000, "blocked_hosts": ["localhost", "169.254.169.254"]},
        "composition_hints": {
            "often_followed_by": ["json_transform", "llm_invoke"],
            "often_preceded_by": ["cache_lookup"],
            "anti_patterns": ["calling same URL repeatedly without cache"]
        }
    },
    "llm_invoke": {
        "cost_cents": 5,
        "latency_ms": 2000,
        "failure_modes": [
            {"code": "RATE_LIMITED", "category": "TRANSIENT", "probability": 0.05},
            {"code": "CONTEXT_OVERFLOW", "category": "PERMANENT", "probability": 0.02},
            {"code": "TIMEOUT", "category": "TRANSIENT", "probability": 0.03},
        ],
        "constraints": {"max_tokens": 100000, "models_allowed": ["claude-3-haiku", "claude-sonnet-4-20250514"]},
        "composition_hints": {
            "often_followed_by": ["json_transform", "http_call"],
            "often_preceded_by": ["http_call", "fs_read"],
            "anti_patterns": ["chaining multiple LLM calls without caching"]
        }
    },
    "json_transform": {
        "cost_cents": 0,
        "latency_ms": 10,
        "failure_modes": [
            {"code": "SCHEMA_VALIDATION_FAILED", "category": "PERMANENT", "probability": 0.01},
            {"code": "TRANSFORM_ERROR", "category": "PERMANENT", "probability": 0.01},
        ],
        "constraints": {"max_input_size_bytes": 10485760},
        "composition_hints": {
            "often_followed_by": ["http_call", "llm_invoke"],
            "often_preceded_by": ["http_call", "llm_invoke"],
            "anti_patterns": []
        }
    },
    "fs_read": {
        "cost_cents": 0,
        "latency_ms": 50,
        "failure_modes": [
            {"code": "FILE_NOT_FOUND", "category": "PERMANENT", "probability": 0.05},
            {"code": "PERMISSION_DENIED", "category": "PERMISSION", "probability": 0.02},
        ],
        "constraints": {"workspace_root": AOS_WORKSPACE_ROOT, "max_file_size_bytes": 10485760},
        "composition_hints": {
            "often_followed_by": ["llm_invoke", "json_transform"],
            "often_preceded_by": ["fs_write"],
            "anti_patterns": ["reading same file multiple times without caching"]
        }
    },
    "fs_write": {
        "cost_cents": 0,
        "latency_ms": 100,
        "failure_modes": [
            {"code": "PERMISSION_DENIED", "category": "PERMISSION", "probability": 0.05},
            {"code": "DISK_FULL", "category": "RESOURCE", "probability": 0.01},
        ],
        "constraints": {"workspace_root": AOS_WORKSPACE_ROOT, "max_file_size_bytes": 10485760},
        "composition_hints": {
            "often_followed_by": ["fs_read"],
            "often_preceded_by": ["llm_invoke", "http_call"],
            "anti_patterns": []
        }
    },
    "webhook_send": {
        "cost_cents": 0,
        "latency_ms": 300,
        "failure_modes": [
            {"code": "TIMEOUT", "category": "TRANSIENT", "probability": 0.1},
            {"code": "HTTP_5XX", "category": "TRANSIENT", "probability": 0.05},
        ],
        "constraints": {"max_payload_bytes": 1048576},
        "composition_hints": {
            "often_followed_by": [],
            "often_preceded_by": ["json_transform"],
            "anti_patterns": []
        }
    },
    "email_send": {
        "cost_cents": 1,
        "latency_ms": 500,
        "failure_modes": [
            {"code": "DELIVERY_FAILED", "category": "TRANSIENT", "probability": 0.05},
            {"code": "RATE_LIMITED", "category": "TRANSIENT", "probability": 0.02},
        ],
        "constraints": {"max_recipients": 10, "max_body_size_bytes": 1048576},
        "composition_hints": {
            "often_followed_by": [],
            "often_preceded_by": ["llm_invoke", "json_transform"],
            "anti_patterns": ["sending same email multiple times"]
        }
    },
}


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/simulate", response_model=SimulateResponse)
async def simulate_plan(
    request: SimulateRequest,
    http_request: Request = None,
    _rate_limited: bool = Depends(rate_limit_dependency),
):
    """
    Simulate a plan before execution.

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
    plan_steps = [
        {"skill": step.skill, "params": step.params, "iterations": step.iterations}
        for step in request.plan
    ]

    # Try to use CostSimulator if available
    simulator = _get_cost_simulator()
    if simulator:
        try:
            result = simulator.simulate(
                plan=plan_steps,
                budget_cents=request.budget_cents,
                agent_id=request.agent_id,
                tenant_id=request.tenant_id
            )
            return SimulateResponse(
                feasible=result.feasible,
                status=result.status.value,
                estimated_cost_cents=result.estimated_cost_cents,
                estimated_duration_ms=result.estimated_duration_ms,
                budget_remaining_cents=result.budget_remaining_cents,
                budget_sufficient=result.budget_sufficient,
                permission_gaps=result.permission_gaps,
                risks=[{
                    "step_index": r.step_index,
                    "skill_id": r.skill_id,
                    "risk_type": r.risk_type,
                    "probability": r.probability,
                    "description": r.description,
                    "mitigation": r.mitigation,
                } for r in result.risks],
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
        meta = DEFAULT_SKILL_METADATA.get(skill_id, {
            "cost_cents": 0,
            "latency_ms": 100,
            "failure_modes": [],
            "constraints": {},
        })

        base_cost = meta.get("cost_cents", 0)
        base_latency = meta.get("latency_ms", 100)

        # Multiply cost and latency by iterations
        cost = base_cost * iterations
        latency = base_latency * iterations

        total_cost += cost
        total_latency += latency

        step_estimates.append({
            "step_index": i,
            "skill_id": skill_id,
            "iterations": iterations,
            "base_cost_cents": base_cost,
            "estimated_cost_cents": cost,
            "base_latency_ms": base_latency,
            "estimated_latency_ms": latency,
        })

        # Add risks from failure modes
        for fm in meta.get("failure_modes", []):
            if fm.get("probability", 0) > 0.05:  # Only report significant risks
                risks.append({
                    "step_index": i,
                    "skill_id": skill_id,
                    "risk_type": fm.get("code", "UNKNOWN"),
                    "probability": fm.get("probability", 0),
                    "description": f"Step {i} ({skill_id}) may fail with {fm.get('code')}",
                    "mitigation": f"Retry if category is TRANSIENT" if fm.get("category") == "TRANSIENT" else None,
                })

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
async def query_runtime(request: QueryRequest):
    """
    Query runtime state.

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

    # Try to use Runtime if available
    runtime = _get_runtime()
    if runtime:
        try:
            result = await runtime.query(request.query_type, **request.params)
            return QueryResponse(
                query_type=request.query_type,
                result=result,
                supported_queries=supported_queries,
            )
        except Exception as e:
            logger.warning(f"Runtime query error: {e}")
            # Fall through to manual handling

    # Manual query handling
    if request.query_type == "remaining_budget_cents":
        # Default budget (1000 cents = $10)
        return QueryResponse(
            query_type=request.query_type,
            result={
                "remaining_cents": 1000,
                "spent_cents": 0,
                "total_cents": 1000,
            },
            supported_queries=supported_queries,
        )

    elif request.query_type == "what_did_i_try_already":
        # No history without runtime context
        return QueryResponse(
            query_type=request.query_type,
            result={"history": []},
            supported_queries=supported_queries,
        )

    elif request.query_type == "allowed_skills":
        skills = list(DEFAULT_SKILL_METADATA.keys())
        return QueryResponse(
            query_type=request.query_type,
            result={
                "skills": skills,
                "count": len(skills),
            },
            supported_queries=supported_queries,
        )

    elif request.query_type == "last_step_outcome":
        return QueryResponse(
            query_type=request.query_type,
            result={"outcome": None},
            supported_queries=supported_queries,
        )

    elif request.query_type == "skills_available_for_goal":
        goal = request.params.get("goal", "")
        # Deterministic pseudo-matching based on goal hash
        seed = sum(ord(c) for c in goal) % 997
        all_skills = list(DEFAULT_SKILL_METADATA.keys())
        # Deterministic sort using seed
        matched = sorted(all_skills, key=lambda s: (hash(s) + seed) % 1000)
        return QueryResponse(
            query_type=request.query_type,
            result={
                "goal": goal,
                "skills": matched[:5],
                "seed": seed,
            },
            supported_queries=supported_queries,
        )

    else:
        return QueryResponse(
            query_type=request.query_type,
            result={
                "error": f"Unknown query type: {request.query_type}",
                "supported": supported_queries,
            },
            supported_queries=supported_queries,
        )


@router.get("/skills", response_model=SkillListResponse)
async def list_available_skills():
    """
    List all available skills.

    Returns skill IDs and basic descriptors for each skill.
    """
    # Try to use skill registry if available
    registry = _get_skill_registry()
    if registry:
        try:
            skills_list = registry["list"]()
            manifest = registry["manifest"]()
            return SkillListResponse(
                skills=[s["name"] for s in skills_list],
                count=len(skills_list),
                descriptors={s["name"]: s for s in skills_list},
            )
        except Exception as e:
            logger.warning(f"Skill registry error: {e}")

    # Fall back to default metadata
    skills = list(DEFAULT_SKILL_METADATA.keys())
    descriptors = {}
    for skill_id in skills:
        meta = DEFAULT_SKILL_METADATA[skill_id]
        descriptors[skill_id] = {
            "skill_id": skill_id,
            "name": skill_id,
            "version": "0.1.0",
            "description": f"{skill_id} skill",
            "cost_model": {"base_cents": meta.get("cost_cents", 0)},
            "latency_ms": meta.get("latency_ms", 100),
        }

    return SkillListResponse(
        skills=skills,
        count=len(skills),
        descriptors=descriptors,
    )


@router.get("/skills/{skill_id}", response_model=SkillDescriptorResponse)
async def describe_skill(skill_id: str):
    """
    Get detailed descriptor for a skill.

    Returns full metadata including:
    - Input/output schemas
    - Cost model
    - Failure modes with recovery hints
    - Constraints
    - Composition hints (what skills often precede/follow)
    """
    # Check if skill exists
    if skill_id not in DEFAULT_SKILL_METADATA:
        # Try runtime
        runtime = _get_runtime()
        if runtime:
            try:
                descriptor = runtime.describe_skill(skill_id)
                if descriptor:
                    return SkillDescriptorResponse(
                        skill_id=descriptor.skill_id,
                        name=descriptor.name,
                        version=descriptor.version,
                        description=descriptor.description,
                        inputs_schema=descriptor.inputs_schema,
                        outputs_schema=descriptor.outputs_schema,
                        cost_model={"base_cents": descriptor.cost_model.get("base_cents", 0)},
                        failure_modes=descriptor.failure_modes or [],
                        constraints=descriptor.constraints or {},
                        composition_hints=descriptor.composition_hints or {},
                    )
            except Exception as e:
                logger.warning(f"Runtime describe_skill error: {e}")

        raise HTTPException(
            status_code=404,
            detail={
                "error": "SKILL_NOT_FOUND",
                "message": f"Skill '{skill_id}' not found",
                "available_skills": list(DEFAULT_SKILL_METADATA.keys()),
            }
        )

    meta = DEFAULT_SKILL_METADATA[skill_id]

    return SkillDescriptorResponse(
        skill_id=skill_id,
        name=skill_id,
        version="0.1.0",
        description=f"{skill_id} skill for AOS runtime",
        inputs_schema=None,  # Would come from skill contract
        outputs_schema=None,
        cost_model={"base_cents": meta.get("cost_cents", 0), "per_kb_cents": 0},
        failure_modes=meta.get("failure_modes", []),
        constraints=meta.get("constraints", {}),
        composition_hints=meta.get("composition_hints", {}),
    )


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities(
    agent_id: Optional[str] = Query(default=None, description="Agent ID"),
    tenant_id: Optional[str] = Query(default=None, description="Tenant ID"),
):
    """
    Get available capabilities for an agent/tenant.

    Returns:
    - Available skills with their current status
    - Budget information
    - Rate limit information
    - Permissions

    This allows agents to know exactly what they can do before attempting.
    """
    # Build capabilities response
    skills_caps = {}
    for skill_id, meta in DEFAULT_SKILL_METADATA.items():
        skills_caps[skill_id] = {
            "available": True,
            "cost_estimate_cents": meta.get("cost_cents", 0),
            "avg_latency_ms": meta.get("latency_ms", 100),
            "rate_limit_remaining": 95,  # Default
            "known_failure_patterns": [
                fm.get("code") for fm in meta.get("failure_modes", [])
                if fm.get("probability", 0) > 0.05
            ],
        }

    return CapabilitiesResponse(
        agent_id=agent_id,
        skills=skills_caps,
        budget={
            "total_cents": 1000,
            "remaining_cents": 1000,
            "per_step_max_cents": 100,
        },
        rate_limits={
            "http_call": {"remaining": 95, "resets_in_seconds": 60},
            "llm_invoke": {"remaining": 50, "resets_in_seconds": 60},
        },
        permissions=["read", "write", "execute"],
    )


@router.get("/resource-contract/{resource_id}")
async def get_resource_contract(resource_id: str):
    """
    Get resource contract for a specific resource.

    Returns budget, rate limits, and concurrency constraints.
    """
    # Try runtime
    runtime = _get_runtime()
    if runtime:
        try:
            contract = runtime.get_resource_contract(resource_id)
            if contract:
                return {
                    "resource_id": resource_id,
                    "budget": {
                        "total_cents": contract.budget_cents,
                        "remaining_cents": contract.budget_cents,
                    },
                    "rate_limits": {
                        "requests_per_minute": contract.rate_limit_per_minute,
                    },
                    "concurrency": {
                        "max_concurrent": contract.max_concurrent,
                    },
                }
        except Exception as e:
            logger.warning(f"Runtime get_resource_contract error: {e}")

    # Default contract
    return {
        "resource_id": resource_id,
        "budget": {
            "total_cents": 1000,
            "remaining_cents": 1000,
            "per_step_max_cents": 100,
        },
        "rate_limits": {
            "requests_per_minute": 100,
            "remaining": 95,
            "resets_at": None,
        },
        "concurrency": {
            "max_concurrent": 5,
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
):
    """
    Replay a stored plan and optionally verify determinism parity.

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
        raise HTTPException(
            status_code=501,
            detail="Replay functionality not available - module not found"
        )
    except Exception as e:
        logger.error(f"Replay error for {run_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Replay failed: {str(e)}"
        )


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
        raise HTTPException(
            status_code=501,
            detail="Trace functionality not available - module not found"
        )
    except Exception as e:
        logger.error(f"List traces error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list traces: {str(e)}"
        )


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
            raise HTTPException(
                status_code=404,
                detail=f"Trace not found: {run_id}"
            )

        return trace.to_dict()

    except HTTPException:
        raise
    except ImportError as e:
        logger.error(f"Trace store not available: {e}")
        raise HTTPException(
            status_code=501,
            detail="Trace functionality not available - module not found"
        )
    except Exception as e:
        logger.error(f"Get trace error for {run_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trace: {str(e)}"
        )
