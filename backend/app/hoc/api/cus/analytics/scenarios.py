# Layer: L2 — Product APIs
# Product: founder-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: H2 Scenario-based cost simulation API (advisory only)
# Callers: founder console UI
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L5
# Reference: Phase H2 - Cost Simulation v1
"""
Scenario-based Cost Simulation API (H2)

READ-ONLY simulation endpoints for scenario planning.

INVARIANTS:
- Pure computation ONLY - no real budget changes
- No side effects - no database writes for simulation results
- Advisory only - results are informational, not actionable
- Scenarios can be stored for re-use (stored in-memory for v1)

Endpoints:
- GET /scenarios - List available scenarios
- POST /scenarios - Create new scenario
- GET /scenarios/{id} - Get scenario details
- DELETE /scenarios/{id} - Delete scenario
- POST /scenarios/{id}/simulate - Run simulation (pure computation)
- POST /scenarios/simulate-adhoc - Run one-off simulation without saving

Reference: Phase H2 - Cost Simulation v1
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# PIN-318: Phase 1.2 Authority Hardening - Add founder auth
from app.auth.console_auth import verify_fops_token
from app.schemas.response import wrap_dict

logger = logging.getLogger("nova.api.scenarios")

# PIN-318: Router-level auth - all endpoints require founder token (aud="fops")
router = APIRouter(prefix="/scenarios", tags=["scenarios"], dependencies=[Depends(verify_fops_token)])

# In-memory scenario storage for v1 (no database persistence for scenarios)
# This ensures READ-ONLY semantics - scenarios are session-ephemeral
_scenarios: Dict[str, "ScenarioModel"] = {}


# =============================================================================
# Models
# =============================================================================


class SimulationStepInput(BaseModel):
    """A single step in a simulation plan."""

    skill: str = Field(..., description="Skill ID to simulate")
    params: Dict[str, Any] = Field(default_factory=dict, description="Skill parameters")
    iterations: int = Field(default=1, ge=1, le=100, description="Number of iterations")


class ScenarioCreate(BaseModel):
    """Request to create a new scenario."""

    name: str = Field(..., min_length=1, max_length=100, description="Scenario name")
    description: Optional[str] = Field(None, max_length=500, description="Scenario description")
    plan: List[SimulationStepInput] = Field(..., min_items=1, max_items=50, description="Plan steps")
    budget_cents: int = Field(default=1000, ge=0, le=1000000, description="Budget in cents")


class ScenarioModel(BaseModel):
    """Stored scenario model."""

    id: str = Field(..., description="Unique scenario ID")
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    plan: List[SimulationStepInput] = Field(..., description="Plan steps")
    budget_cents: int = Field(..., description="Budget in cents")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str = Field(default="founder", description="Creator identifier")
    is_template: bool = Field(default=False, description="Is this a template scenario")


class ScenarioResponse(BaseModel):
    """Response for scenario operations."""

    id: str
    name: str
    description: Optional[str]
    plan: List[SimulationStepInput]
    budget_cents: int
    created_at: datetime
    created_by: str
    is_template: bool


class StepEstimate(BaseModel):
    """Cost estimate for a single step."""

    step_index: int
    skill_id: str
    iterations: int
    cost_cents: float
    latency_ms: float
    confidence: float


class SimulationResult(BaseModel):
    """Result of a scenario simulation (advisory only)."""

    scenario_id: Optional[str] = Field(None, description="Scenario ID if from saved scenario")
    scenario_name: Optional[str] = Field(None, description="Scenario name if from saved scenario")

    # Simulation results
    feasible: bool = Field(..., description="Is the plan feasible within budget")
    status: str = Field(..., description="Simulation status")

    # Cost breakdown
    estimated_cost_cents: int = Field(..., description="Total estimated cost")
    budget_cents: int = Field(..., description="Available budget")
    budget_remaining_cents: int = Field(..., description="Budget remaining after simulation")
    budget_utilization_pct: float = Field(..., description="Budget utilization percentage")

    # Duration
    estimated_duration_ms: int = Field(..., description="Total estimated duration")

    # Step-by-step breakdown
    step_estimates: List[StepEstimate] = Field(..., description="Per-step cost estimates")

    # Quality metrics
    confidence_score: float = Field(..., description="Overall confidence score")

    # Warnings and risks
    warnings: List[str] = Field(default_factory=list, description="Advisory warnings")
    risks: List[Dict[str, Any]] = Field(default_factory=list, description="Identified risks")

    # Metadata
    simulation_timestamp: datetime = Field(..., description="When simulation was run")
    model_version: str = Field(default="v1.0.0", description="Simulation model version")

    # Immutability notice
    is_advisory: bool = Field(default=True, description="Results are advisory only")
    note: str = Field(
        default="This simulation is advisory only. No real budget changes occur.", description="Advisory note"
    )


class AdhocSimulationRequest(BaseModel):
    """Request for ad-hoc simulation without saving scenario."""

    plan: List[SimulationStepInput] = Field(..., min_items=1, max_items=50, description="Plan steps")
    budget_cents: int = Field(default=1000, ge=0, le=1000000, description="Budget in cents")


# =============================================================================
# Default Template Scenarios
# =============================================================================


def _init_default_scenarios():
    """Initialize default template scenarios for quick access."""
    templates = [
        ScenarioModel(
            id="template-basic",
            name="Basic API Call",
            description="Single API call scenario for baseline testing",
            plan=[SimulationStepInput(skill="api_call", params={"endpoint": "/test"}, iterations=1)],
            budget_cents=100,
            created_at=datetime.now(timezone.utc),
            created_by="system",
            is_template=True,
        ),
        ScenarioModel(
            id="template-multi-step",
            name="Multi-Step Workflow",
            description="Common workflow with multiple sequential steps",
            plan=[
                SimulationStepInput(skill="data_fetch", params={}, iterations=1),
                SimulationStepInput(skill="llm_call", params={"model": "claude"}, iterations=1),
                SimulationStepInput(skill="data_store", params={}, iterations=1),
            ],
            budget_cents=500,
            created_at=datetime.now(timezone.utc),
            created_by="system",
            is_template=True,
        ),
        ScenarioModel(
            id="template-batch",
            name="Batch Processing",
            description="High-iteration batch processing scenario",
            plan=[SimulationStepInput(skill="batch_process", params={"batch_size": 100}, iterations=10)],
            budget_cents=2000,
            created_at=datetime.now(timezone.utc),
            created_by="system",
            is_template=True,
        ),
    ]

    for template in templates:
        _scenarios[template.id] = template


# Initialize defaults on module load
_init_default_scenarios()


# =============================================================================
# Pure Simulation Engine (No Side Effects)
# =============================================================================


def _simulate_plan(plan: List[SimulationStepInput], budget_cents: int) -> SimulationResult:
    """
    Run pure simulation on a plan.

    INVARIANT: This function has NO side effects.
    - No database writes
    - No external API calls
    - No budget mutations
    - Pure computation only
    """
    # Cost model (simplified for v1 - advisory only)
    # Real costs would come from historical data
    COST_MODEL = {
        "api_call": {"base_cost": 5, "per_iteration": 2, "latency_ms": 100},
        "data_fetch": {"base_cost": 3, "per_iteration": 1, "latency_ms": 50},
        "data_store": {"base_cost": 2, "per_iteration": 1, "latency_ms": 30},
        "llm_call": {"base_cost": 50, "per_iteration": 30, "latency_ms": 2000},
        "batch_process": {"base_cost": 10, "per_iteration": 5, "latency_ms": 500},
        "default": {"base_cost": 5, "per_iteration": 2, "latency_ms": 100},
    }

    step_estimates = []
    total_cost = 0
    total_latency = 0
    warnings = []
    risks = []

    for idx, step in enumerate(plan):
        model = COST_MODEL.get(step.skill, COST_MODEL["default"])

        step_cost = model["base_cost"] + (model["per_iteration"] * step.iterations)
        step_latency = model["latency_ms"] * step.iterations

        # Confidence based on whether we have real data for this skill
        confidence = 0.95 if step.skill in COST_MODEL else 0.7

        step_estimates.append(
            StepEstimate(
                step_index=idx,
                skill_id=step.skill,
                iterations=step.iterations,
                cost_cents=step_cost,
                latency_ms=step_latency,
                confidence=confidence,
            )
        )

        total_cost += step_cost
        total_latency += step_latency

        # Add warnings for unknown skills
        if step.skill not in COST_MODEL:
            warnings.append(f"Step {idx}: Unknown skill '{step.skill}' - using default estimates")

        # Add warnings for high iteration counts
        if step.iterations > 50:
            warnings.append(f"Step {idx}: High iteration count ({step.iterations}) may affect accuracy")

    # Calculate budget metrics
    budget_remaining = budget_cents - total_cost
    feasible = budget_remaining >= 0
    utilization = (total_cost / budget_cents * 100) if budget_cents > 0 else 0

    # Add risks
    if utilization > 90:
        risks.append(
            {
                "type": "budget_risk",
                "severity": "high",
                "message": f"Budget utilization is {utilization:.1f}% - high risk of overage",
            }
        )
    elif utilization > 70:
        risks.append(
            {
                "type": "budget_risk",
                "severity": "medium",
                "message": f"Budget utilization is {utilization:.1f}% - moderate risk",
            }
        )

    if total_latency > 30000:
        risks.append(
            {
                "type": "latency_risk",
                "severity": "medium",
                "message": f"Estimated duration is {total_latency / 1000:.1f}s - may exceed timeout",
            }
        )

    # Overall confidence (average of step confidences)
    avg_confidence = sum(s.confidence for s in step_estimates) / len(step_estimates) if step_estimates else 0

    return SimulationResult(
        feasible=feasible,
        status="feasible" if feasible else "budget_exceeded",
        estimated_cost_cents=total_cost,
        budget_cents=budget_cents,
        budget_remaining_cents=max(0, budget_remaining),
        budget_utilization_pct=round(utilization, 2),
        estimated_duration_ms=total_latency,
        step_estimates=step_estimates,
        confidence_score=round(avg_confidence, 3),
        warnings=warnings,
        risks=risks,
        simulation_timestamp=datetime.now(timezone.utc),
        model_version="v1.0.0",
        is_advisory=True,
        note="This simulation is advisory only. No real budget changes occur.",
    )


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("", response_model=List[ScenarioResponse])
async def list_scenarios(
    include_templates: bool = Query(True, description="Include template scenarios"),
):
    """
    List all available scenarios.

    Returns both user-created scenarios and template scenarios.
    Templates are pre-defined common scenarios for quick testing.
    """
    scenarios = []
    for scenario in _scenarios.values():
        if scenario.is_template and not include_templates:
            continue
        scenarios.append(
            ScenarioResponse(
                id=scenario.id,
                name=scenario.name,
                description=scenario.description,
                plan=scenario.plan,
                budget_cents=scenario.budget_cents,
                created_at=scenario.created_at,
                created_by=scenario.created_by,
                is_template=scenario.is_template,
            )
        )

    return sorted(scenarios, key=lambda s: (not s.is_template, s.created_at), reverse=True)


@router.post("", response_model=ScenarioResponse)
async def create_scenario(
    request: ScenarioCreate,
):
    """
    Create a new scenario.

    Scenarios are stored in-memory for v1 (session-ephemeral).
    This ensures no persistent side-effects from scenario creation.
    """
    scenario_id = f"scenario-{uuid.uuid4().hex[:8]}"

    scenario = ScenarioModel(
        id=scenario_id,
        name=request.name,
        description=request.description,
        plan=request.plan,
        budget_cents=request.budget_cents,
        created_at=datetime.now(timezone.utc),
        created_by="founder",
        is_template=False,
    )

    _scenarios[scenario_id] = scenario

    logger.info(f"Created scenario: {scenario_id} - {request.name}")

    return ScenarioResponse(
        id=scenario.id,
        name=scenario.name,
        description=scenario.description,
        plan=scenario.plan,
        budget_cents=scenario.budget_cents,
        created_at=scenario.created_at,
        created_by=scenario.created_by,
        is_template=scenario.is_template,
    )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
):
    """Get a specific scenario by ID."""
    scenario = _scenarios.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

    return ScenarioResponse(
        id=scenario.id,
        name=scenario.name,
        description=scenario.description,
        plan=scenario.plan,
        budget_cents=scenario.budget_cents,
        created_at=scenario.created_at,
        created_by=scenario.created_by,
        is_template=scenario.is_template,
    )


@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: str,
):
    """
    Delete a scenario.

    Template scenarios cannot be deleted.
    """
    scenario = _scenarios.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

    if scenario.is_template:
        raise HTTPException(status_code=400, detail="Cannot delete template scenarios")

    del _scenarios[scenario_id]

    logger.info(f"Deleted scenario: {scenario_id}")

    return wrap_dict({"message": f"Scenario {scenario_id} deleted", "success": True})


@router.post("/{scenario_id}/simulate", response_model=SimulationResult)
async def simulate_scenario(
    scenario_id: str,
    budget_override: Optional[int] = Query(None, ge=0, le=1000000, description="Override budget"),
):
    """
    Run simulation for a saved scenario.

    INVARIANT: Pure computation only.
    - No database writes
    - No budget mutations
    - No external side-effects
    - Results are advisory only
    """
    scenario = _scenarios.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

    budget = budget_override if budget_override is not None else scenario.budget_cents

    result = _simulate_plan(scenario.plan, budget)
    result.scenario_id = scenario.id
    result.scenario_name = scenario.name

    logger.info(f"Simulated scenario: {scenario_id} - feasible={result.feasible}, cost={result.estimated_cost_cents}")

    return wrap_dict(result.model_dump())


@router.post("/simulate-adhoc", response_model=SimulationResult)
async def simulate_adhoc(
    request: AdhocSimulationRequest,
):
    """
    Run ad-hoc simulation without saving scenario.

    Use this for quick one-off simulations.

    INVARIANT: Pure computation only.
    - No database writes
    - No budget mutations
    - No external side-effects
    - Results are advisory only
    """
    result = _simulate_plan(request.plan, request.budget_cents)

    logger.info(f"Ad-hoc simulation: feasible={result.feasible}, cost={result.estimated_cost_cents}")

    return wrap_dict(result.model_dump())


# =============================================================================
# Immutability Notice Endpoint
# =============================================================================


@router.get("/info/immutability")
async def get_immutability_info():
    """
    Get information about the immutability guarantees.

    This endpoint documents the READ-ONLY nature of scenario simulations.
    """
    return wrap_dict({
        "system": "H2 Cost Simulation v1",
        "guarantees": [
            "Pure computation only - no real budget changes",
            "No database writes for simulation results",
            "Results are advisory, not actionable",
            "Scenarios are session-ephemeral (in-memory storage for v1)",
        ],
        "advisory_notice": "All simulation results are for planning purposes only. "
        "No actual costs are incurred, no budgets are modified, "
        "and no real operations are triggered.",
        "reference": "Phase H2 - Cost Simulation v1",
    })
