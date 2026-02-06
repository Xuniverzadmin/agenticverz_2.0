# Layer: L2a — Product API (Console-scoped)
# Product: AI Console
# Auth: verify_api_key
# Reference: PIN-240
# NOTE: Part of Phase 4C-2 contract framework.

"""Phase 4C-2: Customer Visibility Endpoints

Customer-facing endpoints for predictability and accountability.

Rules:
- Show effects, not mechanics
- No decision records exposed
- No governance internals
- Predictability before execution
- Accountability after execution
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
# L4 session + registry for L2 first-principles purity
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_operation_registry,
    get_session_dep,
    OperationContext,
)

from app.auth import verify_api_key
from app.middleware.tenancy import get_tenant_id
from app.schemas.response import wrap_dict

logger = logging.getLogger("nova.api.customer_visibility")

router = APIRouter(prefix="/customer", tags=["customer-visibility"])


# =============================================================================
# PRE-RUN DECLARATION (What will happen)
# =============================================================================


class StageDeclaration(BaseModel):
    """Single stage in the execution plan."""

    name: str  # Skill name (human-readable)
    order: int  # Execution order (1-based)
    depends_on: List[str] = Field(default_factory=list)  # Dependencies


class CostDeclaration(BaseModel):
    """Cost expectations before execution."""

    estimated_cents: int  # Best estimate
    minimum_cents: int  # Floor
    maximum_cents: int  # Ceiling (worst case)
    budget_remaining_cents: int  # Available budget


class BudgetDeclaration(BaseModel):
    """Budget enforcement mode."""

    mode: str  # "hard" | "soft"
    description: str  # Human-readable explanation
    limit_cents: Optional[int] = None  # If hard mode, the limit


class PolicyDeclaration(BaseModel):
    """Policy posture declaration."""

    posture: str  # "strict" | "advisory"
    description: str  # Human-readable explanation
    active_policies: List[str] = Field(default_factory=list)  # Policy names only


class MemoryDeclaration(BaseModel):
    """Memory mode declaration."""

    mode: str  # "isolated" | "shared"
    description: str  # Human-readable explanation


class EstimationMethodology(BaseModel):
    """
    PIN-254 Phase C Fix (C3 Partial Truth): Explicit disclosure of estimation basis.

    Ensures API consumers know whether estimates are derived from:
    - Real planner output (planner_v1)
    - Hardcoded defaults (default_stages_v1)
    - Historical data (historical_avg)
    """

    stages_source: str = "default_stages_v1"  # How stages were determined
    cost_source: str = "base_rate_v1"  # How costs were calculated
    confidence: str = "low"  # low | medium | high
    disclaimer: str = "Estimates based on default assumptions. Actual execution may vary."


class PreRunDeclaration(BaseModel):
    """
    Complete PRE-RUN declaration for customer visibility.

    This is what the customer sees BEFORE execution starts.
    Execution cannot proceed without acknowledgement.
    """

    # Identity
    agent_id: str
    goal: str

    # Stages (ordered)
    stages: List[StageDeclaration]
    stage_count: int

    # Cost expectations
    cost: CostDeclaration

    # Enforcement modes
    budget: BudgetDeclaration
    policy: PolicyDeclaration
    memory: MemoryDeclaration

    # PIN-254 Phase C Fix: Estimation transparency
    estimation_methodology: EstimationMethodology = Field(
        default_factory=EstimationMethodology, description="Disclosure of how estimates were derived (PIN-254 C3 fix)"
    )

    # Acknowledgement required
    requires_acknowledgement: bool = True
    declaration_id: str  # Used for acknowledgement
    declared_at: datetime


class AcknowledgementRequest(BaseModel):
    """Customer acknowledgement of PRE-RUN declaration."""

    declaration_id: str
    acknowledged: bool = True


class AcknowledgementResponse(BaseModel):
    """Response after acknowledgement."""

    declaration_id: str
    acknowledged: bool
    execution_allowed: bool
    message: str


# =============================================================================
# OUTCOME RECONCILIATION (What happened)
# =============================================================================


class OutcomeItem(BaseModel):
    """Single outcome item."""

    category: str  # "task" | "budget" | "policy" | "recovery"
    status: str  # "success" | "warning" | "error"
    message: str  # Human-readable explanation


class OutcomeReconciliation(BaseModel):
    """
    Complete outcome reconciliation for customer visibility.

    This is what the customer sees AFTER execution completes.
    Decomposed results, never a single success flag.
    """

    run_id: str

    # Overall (still decomposed)
    completed: bool
    outcome_count: int

    # Decomposed outcomes
    outcomes: List[OutcomeItem]

    # Summary metrics (effects only)
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_cents: Optional[int] = None

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# =============================================================================
# Helper Functions
# =============================================================================


def get_budget_mode() -> BudgetDeclaration:
    """Determine budget enforcement mode from configuration."""
    # Check if hard limits are configured
    per_run_max = int(os.environ.get("BUDGET_PER_RUN_MAX_CENTS", "500"))
    per_day_max = int(os.environ.get("BUDGET_PER_DAY_MAX_CENTS", "10000"))

    # If limits are set and non-zero, it's hard mode
    if per_run_max > 0 or per_day_max > 0:
        return BudgetDeclaration(
            mode="soft",  # Currently advisory - see PIN-167
            description="Budget limits are advisory. Execution may exceed estimates.",
            limit_cents=per_run_max,
        )
    else:
        return BudgetDeclaration(
            mode="soft",
            description="No budget limits configured. Execution will not be constrained by cost.",
            limit_cents=None,
        )


def get_policy_posture(strict_mode: bool = False) -> PolicyDeclaration:
    """Determine policy posture from configuration."""
    if strict_mode:
        return PolicyDeclaration(
            posture="strict",
            description="Policy violations will stop execution immediately.",
            active_policies=["content-accuracy", "ftc-compliance", "prompt-injection"],
        )
    else:
        return PolicyDeclaration(
            posture="advisory",
            description="Policy violations will be logged but execution continues.",
            active_policies=["content-accuracy", "ftc-compliance", "prompt-injection"],
        )


def get_memory_mode() -> MemoryDeclaration:
    """Determine memory mode from configuration."""
    memory_injection = os.environ.get("MEMORY_CONTEXT_INJECTION", "false").lower() == "true"

    if memory_injection:
        return MemoryDeclaration(
            mode="shared",
            description="Agent may use context from previous executions.",
        )
    else:
        return MemoryDeclaration(
            mode="isolated",
            description="Agent starts fresh with no memory of previous executions.",
        )


def estimate_stages(agent_id: str, goal: str) -> List[StageDeclaration]:
    """
    Estimate execution stages based on agent capabilities.

    This is a simplified version - in production, this would
    call the planner to generate a real plan.
    """
    # Default stages for business-builder type agents
    default_stages = [
        StageDeclaration(name="analyze_request", order=1, depends_on=[]),
        StageDeclaration(name="gather_context", order=2, depends_on=["analyze_request"]),
        StageDeclaration(name="generate_response", order=3, depends_on=["gather_context"]),
        StageDeclaration(name="validate_output", order=4, depends_on=["generate_response"]),
    ]

    # TODO: In production, call AnthropicPlanner.plan() to get real stages
    # For now, return default stages
    return default_stages


def estimate_cost(agent_id: str, goal: str, stages: List[StageDeclaration]) -> CostDeclaration:
    """
    Estimate cost based on stages and historical data.
    """
    # Base cost per stage (simplified)
    base_cost_per_stage = 25  # cents

    # Calculate estimates
    stage_count = len(stages)
    estimated = base_cost_per_stage * stage_count
    minimum = int(estimated * 0.5)  # Best case: 50% of estimate
    maximum = int(estimated * 2.0)  # Worst case: 200% of estimate

    # Get budget remaining (simplified)
    budget_remaining = int(os.environ.get("BUDGET_PER_DAY_MAX_CENTS", "10000"))

    return CostDeclaration(
        estimated_cents=estimated,
        minimum_cents=minimum,
        maximum_cents=maximum,
        budget_remaining_cents=budget_remaining,
    )




# =============================================================================
# In-Memory Declaration Store (Simple Implementation)
# =============================================================================

# In production, this would be Redis or DB-backed
_declaration_store: Dict[str, PreRunDeclaration] = {}
_acknowledgement_store: Dict[str, bool] = {}


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/pre-run", response_model=PreRunDeclaration)
async def get_pre_run_declaration(
    agent_id: str,
    goal: str,
    strict_mode: bool = False,
    _: str = Depends(verify_api_key),
) -> PreRunDeclaration:
    """
    Get PRE-RUN declaration before execution.

    Returns all information needed for customer to make an informed decision:
    - Stages that will execute (ordered)
    - Estimated cost range
    - Budget enforcement mode
    - Policy posture
    - Memory mode

    Customer must acknowledge before execution can proceed.
    """
    import uuid

    # Generate declaration ID
    declaration_id = str(uuid.uuid4())[:16]

    # Get stages
    stages = estimate_stages(agent_id, goal)

    # Get cost estimate
    cost = estimate_cost(agent_id, goal, stages)

    # Get enforcement modes
    budget = get_budget_mode()
    policy = get_policy_posture(strict_mode)
    memory = get_memory_mode()

    # Create declaration
    declaration = PreRunDeclaration(
        agent_id=agent_id,
        goal=goal,
        stages=stages,
        stage_count=len(stages),
        cost=cost,
        budget=budget,
        policy=policy,
        memory=memory,
        requires_acknowledgement=True,
        declaration_id=declaration_id,
        declared_at=datetime.now(timezone.utc),
    )

    # Store for acknowledgement
    _declaration_store[declaration_id] = declaration

    logger.info(
        "pre_run_declaration_created",
        extra={
            "declaration_id": declaration_id,
            "agent_id": agent_id,
            "stage_count": len(stages),
            "estimated_cost": cost.estimated_cents,
        },
    )

    return wrap_dict(declaration.model_dump())


@router.post("/acknowledge", response_model=AcknowledgementResponse)
async def acknowledge_declaration(
    request: AcknowledgementRequest,
    _: str = Depends(verify_api_key),
) -> AcknowledgementResponse:
    """
    Acknowledge PRE-RUN declaration.

    Customer must acknowledge to proceed with execution.
    This creates an audit trail of informed consent.
    """
    declaration_id = request.declaration_id

    # Check if declaration exists
    if declaration_id not in _declaration_store:
        raise HTTPException(
            status_code=404,
            detail="Declaration not found. Please request a new PRE-RUN declaration.",
        )

    # Check if already acknowledged
    if declaration_id in _acknowledgement_store:
        return AcknowledgementResponse(
            declaration_id=declaration_id,
            acknowledged=True,
            execution_allowed=True,
            message="Declaration already acknowledged. Execution is allowed.",
        )

    # Record acknowledgement
    _acknowledgement_store[declaration_id] = request.acknowledged

    if request.acknowledged:
        logger.info(
            "declaration_acknowledged",
            extra={"declaration_id": declaration_id},
        )
        return AcknowledgementResponse(
            declaration_id=declaration_id,
            acknowledged=True,
            execution_allowed=True,
            message="Declaration acknowledged. You may proceed with execution.",
        )
    else:
        logger.info(
            "declaration_rejected",
            extra={"declaration_id": declaration_id},
        )
        return AcknowledgementResponse(
            declaration_id=declaration_id,
            acknowledged=False,
            execution_allowed=False,
            message="Declaration not acknowledged. Execution is not allowed.",
        )


@router.get("/outcome/{run_id}", response_model=OutcomeReconciliation)
async def get_outcome_reconciliation(
    run_id: str,
    request: Request,
    _: str = Depends(verify_api_key),
    session=Depends(get_session_dep),
) -> OutcomeReconciliation:
    """
    Get outcome reconciliation after execution.

    Returns decomposed results (never a single success flag):
    - Task completion status
    - Budget usage status
    - Policy compliance status
    - Recovery status
    """
    # PIN-052: Get tenant_id for data isolation
    tenant_id = get_tenant_id(request)

    # L4 registry dispatch for DB operations (L2 first-principles purity)
    registry = get_operation_registry()

    # Fetch run data via L4 -> L6 driver
    run_result = await registry.execute(
        "policies.customer_visibility",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "fetch_run_outcome", "run_id": run_id, "tenant_id": tenant_id},
        ),
    )
    if not run_result.success or not run_result.data:
        raise HTTPException(status_code=404, detail="Run not found")
    run_data = run_result.data

    # Fetch decision summary via L4 -> L6 driver
    decision_result = await registry.execute(
        "policies.customer_visibility",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "fetch_decision_summary", "run_id": run_id, "tenant_id": tenant_id},
        ),
    )
    decision_summary = decision_result.data if decision_result.success else {
        "budget_warnings": 0,
        "policy_warnings": 0,
        "recovery_attempted": False,
    }

    # Build decomposed outcomes
    outcomes: List[OutcomeItem] = []

    # 1. Task outcome
    if run_data["status"] == "completed":
        outcomes.append(
            OutcomeItem(
                category="task",
                status="success",
                message="Task completed successfully.",
            )
        )
    elif run_data["status"] == "failed":
        error_msg = run_data.get("error_message", "Unknown error")
        outcomes.append(
            OutcomeItem(
                category="task",
                status="error",
                message=f"Task failed: {error_msg}",
            )
        )
    else:
        outcomes.append(
            OutcomeItem(
                category="task",
                status="warning",
                message=f"Task is {run_data['status']}.",
            )
        )

    # 2. Budget outcome
    if decision_summary["budget_warnings"] > 0:
        outcomes.append(
            OutcomeItem(
                category="budget",
                status="warning",
                message="Budget limits were exceeded.",
            )
        )
    else:
        outcomes.append(
            OutcomeItem(
                category="budget",
                status="success",
                message="Budget limits were respected.",
            )
        )

    # 3. Policy outcome
    if decision_summary["policy_warnings"] > 0:
        outcomes.append(
            OutcomeItem(
                category="policy",
                status="warning",
                message=f"{decision_summary['policy_warnings']} policy warning(s) issued.",
            )
        )
    else:
        outcomes.append(
            OutcomeItem(
                category="policy",
                status="success",
                message="No policy violations detected.",
            )
        )

    # 4. Recovery outcome
    if decision_summary["recovery_attempted"]:
        outcomes.append(
            OutcomeItem(
                category="recovery",
                status="warning",
                message="Recovery actions were attempted.",
            )
        )
    else:
        outcomes.append(
            OutcomeItem(
                category="recovery",
                status="success",
                message="No recovery was required.",
            )
        )

    # Extract cost from result if available
    cost_cents = None
    tokens_used = None
    if run_data.get("result"):
        try:
            import json

            result = json.loads(run_data["result"]) if isinstance(run_data["result"], str) else run_data["result"]
            cost_report = result.get("cost_report", {})
            cost_cents = cost_report.get("total_cost_cents")
            tokens_used = cost_report.get("total_tokens")
        except (json.JSONDecodeError, TypeError):
            pass

    return OutcomeReconciliation(
        run_id=run_id,
        completed=run_data["status"] in ["completed", "failed"],
        outcome_count=len(outcomes),
        outcomes=outcomes,
        duration_ms=run_data.get("duration_ms"),
        tokens_used=tokens_used,
        cost_cents=cost_cents,
        started_at=run_data.get("started_at"),
        completed_at=run_data.get("completed_at"),
    )


@router.get("/declaration/{declaration_id}", response_model=PreRunDeclaration)
async def get_declaration(
    declaration_id: str,
    _: str = Depends(verify_api_key),
) -> PreRunDeclaration:
    """
    Retrieve a previously created PRE-RUN declaration.
    """
    if declaration_id not in _declaration_store:
        raise HTTPException(status_code=404, detail="Declaration not found")

    return _declaration_store[declaration_id]
