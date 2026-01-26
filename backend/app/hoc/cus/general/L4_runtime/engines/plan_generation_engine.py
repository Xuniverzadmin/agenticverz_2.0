# Layer: L4 — Domain Engine (System Truth)
# AUDIENCE: CUSTOMER
# Product: system-wide (NOT console-owned)
# Temporal:
#   Trigger: api (run creation)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via L6 drivers
#   Writes: via L6 drivers
# Role: Plan generation (domain logic)
# Authority: Plan generation decisions (M7 pattern)
# Callers: API endpoints (L2), run creation flow
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Contract: EXECUTION_SEMANTIC_CONTRACT.md
# Reference: PIN-470, PIN-257 Phase R-2 (L5→L4 Violation Fix)
#
# GOVERNANCE NOTE: This L4 engine owns PLAN GENERATION logic.
# L5 runner.py owns only PLAN EXECUTION logic.
# This separation fixes the L5→L4 import violations identified in
# PHASE_R_L5_L4_VIOLATIONS.md (violations #2, #3).

# M7 Plan Generation Engine (L4 Domain Logic)
"""
Domain engine for plan generation.

This L4 engine contains the authoritative logic for:
1. Memory context retrieval
2. Plan generation via planner
3. Plan validation

L5 workers must receive plans from this engine (via run.plan_json),
not generate their own plans.

Reference: PIN-257 Phase R-2
Governance: PHASE_R_L5_L4_VIOLATIONS.md
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.plan_generation_engine")

# L4/L5/L6 imports (allowed per layer rules)
from app.memory import get_retriever
from app.planners import get_planner
from app.skills import get_skill_manifest
from app.utils.budget_tracker import get_budget_tracker
from app.utils.plan_inspector import validate_plan

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class PlanGenerationContext:
    """Context for plan generation."""

    agent_id: str
    goal: str
    run_id: str
    agent_budget_cents: int = 0


@dataclass
class PlanGenerationResult:
    """Result of plan generation."""

    plan: Dict[str, Any]
    plan_json: str
    steps: List[Dict[str, Any]]
    context_summary: Optional[str]
    memory_snippet_count: int
    validation_valid: bool
    validation_warnings: List[str]


# =============================================================================
# Plan Generation Engine (L4 Domain Logic)
# =============================================================================


class PlanGenerationEngine:
    """
    L4 Domain Engine for plan generation.

    This engine contains ALL plan generation logic that was previously
    scattered in L5 runner.py. It generates plans from goals using
    memory context and the configured planner.

    L5 workers must NOT:
    - Import memory.get_retriever()
    - Import planners.get_planner()
    - Generate plans inline

    L5 workers must ONLY:
    - Execute plans provided via run.plan_json
    - Fail if no plan is provided

    Reference: PIN-257 Phase R-2
    Governance: PHASE_R_L5_L4_VIOLATIONS.md Section 3.2
    """

    def __init__(self):
        """Initialize the plan generation engine."""
        self._retriever = get_retriever()
        self._planner = get_planner()

    def generate(self, context: PlanGenerationContext) -> PlanGenerationResult:
        """
        Generate a plan for a run.

        This is the core L4 domain function for plan generation. It:
        1. Retrieves memory context for the agent and goal
        2. Generates a plan using the configured planner
        3. Validates the plan for safety

        Args:
            context: PlanGenerationContext with agent_id, goal, run_id

        Returns:
            PlanGenerationResult with the generated plan

        Reference: PIN-257 Phase R-2
        """
        logger.info(
            "L4 generating plan",
            extra={
                "run_id": context.run_id,
                "agent_id": context.agent_id,
                "goal": context.goal[:100],
            },
        )

        # Step 1: Retrieve memory context for planning (L4 domain logic)
        memory_context = self._retriever.get_context_for_planning(
            agent_id=context.agent_id,
            goal=context.goal,
            current_run_id=context.run_id,
        )

        logger.debug(
            "L4 planning_with_context",
            extra={
                "run_id": context.run_id,
                "has_summary": memory_context.get("context_summary") is not None,
                "memory_count": len(memory_context.get("memory_snippets") or []),
            },
        )

        # Step 2: Generate plan using planner (L4 domain logic)
        plan = self._planner.plan(
            agent_id=context.agent_id,
            goal=context.goal,
            context_summary=memory_context.get("context_summary"),
            memory_snippets=memory_context.get("memory_snippets"),
            tool_manifest=get_skill_manifest(),
        )

        steps = plan.get("steps", [])

        # Step 3: Validate plan safety (L4 domain logic)
        validation = validate_plan(plan, agent_budget_cents=context.agent_budget_cents)
        validation_warnings = []

        if validation.warnings:
            validation_warnings = [w.message for w in validation.warnings]
            logger.warning(
                "L4 plan_validation_warnings",
                extra={
                    "run_id": context.run_id,
                    "warnings": validation_warnings[:3],
                },
            )

        if not validation.valid:
            error_messages = "; ".join(e.message for e in validation.errors[:3])
            logger.error(
                "L4 plan_validation_failed",
                extra={
                    "run_id": context.run_id,
                    "errors": error_messages,
                },
            )
            raise RuntimeError(f"Plan validation failed: {error_messages}")

        logger.info(
            "L4 plan generated",
            extra={
                "run_id": context.run_id,
                "step_count": len(steps),
                "validation_valid": validation.valid,
            },
        )

        return PlanGenerationResult(
            plan=plan,
            plan_json=json.dumps(plan),
            steps=steps,
            context_summary=memory_context.get("context_summary"),
            memory_snippet_count=len(memory_context.get("memory_snippets") or []),
            validation_valid=validation.valid,
            validation_warnings=validation_warnings,
        )


# =============================================================================
# Convenience Functions
# =============================================================================


def generate_plan_for_run(
    agent_id: str,
    goal: str,
    run_id: str,
) -> PlanGenerationResult:
    """
    Convenience function to generate a plan for a run.

    This is the L4 entry point for plan generation. It should be called
    by the run creation flow (in L2 API) to generate plans before
    the run is queued for execution.

    Args:
        agent_id: Agent ID
        goal: Run goal
        run_id: Run ID

    Returns:
        PlanGenerationResult with the generated plan

    Reference: PIN-257 Phase R-2
    """
    # Get agent budget
    budget_status = get_budget_tracker().get_status(agent_id)
    agent_budget = budget_status.remaining_cents if budget_status else 0

    context = PlanGenerationContext(
        agent_id=agent_id,
        goal=goal,
        run_id=run_id,
        agent_budget_cents=agent_budget,
    )

    engine = PlanGenerationEngine()
    return engine.generate(context)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PlanGenerationContext",
    "PlanGenerationResult",
    "PlanGenerationEngine",
    "generate_plan_for_run",
]
