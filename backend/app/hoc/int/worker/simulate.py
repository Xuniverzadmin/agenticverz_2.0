# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Pre-execution cost simulation (M5)
# Authority: Feasibility decisions (budget, permission, risk)
# Callers: API runtime, workers (pre-run checks)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-256 Phase E FIX-01
#
# Phase E FIX-01 Criteria Verification:
# - Domain Decision: YES (cost/feasibility classification)
# - Semantic Stability: YES (same plan = same result)
# - No Execution Coupling: YES (uses static metadata, no execution)
# - Idempotence: YES (deterministic by design)

"""
Pre-Execution Cost Simulator (M5) - L4 Domain Orchestrator

Cost and feasibility simulation for workflow plans before execution.

Provides:
1. Cost estimation based on skill metadata
2. Latency estimation
3. Budget feasibility check
4. Permission validation
5. Risk assessment

Design Principles:
- Offline-first: Uses static skill metadata, no execution
- Conservative: Estimates tend toward upper bounds
- Deterministic: Same plan produces same simulation result
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.worker.simulate")


class FeasibilityStatus(str, Enum):
    """Simulation feasibility results."""

    FEASIBLE = "feasible"
    BUDGET_INSUFFICIENT = "budget_insufficient"
    PERMISSION_DENIED = "permission_denied"
    SKILL_UNAVAILABLE = "skill_unavailable"
    RISK_TOO_HIGH = "risk_too_high"
    INVALID_PLAN = "invalid_plan"


@dataclass
class StepRisk:
    """Risk assessment for a single step."""

    step_index: int
    skill_id: str
    risk_type: str
    probability: float  # 0.0 to 1.0
    description: str
    mitigation: Optional[str] = None


@dataclass
class SimulationResult:
    """Result of plan simulation."""

    feasible: bool
    status: FeasibilityStatus
    estimated_cost_cents: int
    estimated_duration_ms: int
    budget_remaining_cents: int
    budget_sufficient: bool
    permission_gaps: List[str]
    risks: List[StepRisk]
    step_estimates: List[Dict[str, Any]]
    alternatives: List[Dict[str, Any]]
    warnings: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "feasible": self.feasible,
            "status": self.status.value,
            "estimated_cost_cents": self.estimated_cost_cents,
            "estimated_duration_ms": self.estimated_duration_ms,
            "budget_remaining_cents": self.budget_remaining_cents,
            "budget_sufficient": self.budget_sufficient,
            "permission_gaps": self.permission_gaps,
            "risks": [
                {
                    "step_index": r.step_index,
                    "skill_id": r.skill_id,
                    "risk_type": r.risk_type,
                    "probability": r.probability,
                    "description": r.description,
                    "mitigation": r.mitigation,
                }
                for r in self.risks
            ],
            "step_estimates": self.step_estimates,
            "alternatives": self.alternatives,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


# Default cost estimates per skill (cents)
# These are conservative estimates - real costs come from skill metadata
DEFAULT_SKILL_COSTS: Dict[str, Dict[str, Any]] = {
    "http_call": {
        "cost_cents": 0,
        "latency_ms": 500,
        "risk_probability": 0.1,
        "risk_type": "timeout",
    },
    "llm_invoke": {
        "cost_cents": 5,  # ~$0.05 average per call
        "latency_ms": 2000,
        "risk_probability": 0.05,
        "risk_type": "rate_limit",
    },
    "json_transform": {
        "cost_cents": 0,
        "latency_ms": 10,
        "risk_probability": 0.01,
        "risk_type": "transform_error",
    },
    "fs_read": {
        "cost_cents": 0,
        "latency_ms": 50,
        "risk_probability": 0.05,
        "risk_type": "not_found",
    },
    "fs_write": {
        "cost_cents": 0,
        "latency_ms": 100,
        "risk_probability": 0.05,
        "risk_type": "permission",
    },
    "shell_lite": {
        "cost_cents": 0,
        "latency_ms": 200,
        "risk_probability": 0.1,
        "risk_type": "timeout",
    },
    "kv_get": {
        "cost_cents": 0,
        "latency_ms": 5,
        "risk_probability": 0.02,
        "risk_type": "not_found",
    },
    "kv_set": {
        "cost_cents": 0,
        "latency_ms": 10,
        "risk_probability": 0.02,
        "risk_type": "quota",
    },
    "webhook_send": {
        "cost_cents": 0,
        "latency_ms": 300,
        "risk_probability": 0.1,
        "risk_type": "timeout",
    },
    "email_send": {
        "cost_cents": 1,
        "latency_ms": 500,
        "risk_probability": 0.05,
        "risk_type": "delivery",
    },
}

# Default unknown skill estimate
DEFAULT_UNKNOWN_SKILL = {
    "cost_cents": 10,
    "latency_ms": 1000,
    "risk_probability": 0.2,
    "risk_type": "unknown",
}


class CostSimulator:
    """
    Pre-execution cost and feasibility simulator.

    Usage:
        simulator = CostSimulator(budget_cents=1000)

        result = simulator.simulate([
            {"skill": "http_call", "params": {"url": "..."}},
            {"skill": "llm_invoke", "params": {"prompt": "..."}},
        ])

        if result.feasible:
            print(f"Estimated cost: {result.estimated_cost_cents} cents")
        else:
            print(f"Not feasible: {result.status}")
    """

    def __init__(
        self,
        budget_cents: int = 1000,
        allowed_skills: Optional[List[str]] = None,
        skill_costs: Optional[Dict[str, Dict[str, Any]]] = None,
        risk_threshold: float = 0.5,
    ):
        """
        Initialize simulator.

        Args:
            budget_cents: Available budget in cents
            allowed_skills: List of allowed skill IDs (None = all allowed)
            skill_costs: Override skill cost estimates
            risk_threshold: Maximum acceptable cumulative risk (0.0 to 1.0)
        """
        self.budget_cents = budget_cents
        self.allowed_skills = set(allowed_skills) if allowed_skills else None
        self.skill_costs = {**DEFAULT_SKILL_COSTS, **(skill_costs or {})}
        self.risk_threshold = risk_threshold

    def _get_skill_estimate(self, skill_id: str) -> Dict[str, Any]:
        """Get cost estimate for a skill."""
        return self.skill_costs.get(skill_id, DEFAULT_UNKNOWN_SKILL)

    def _estimate_step(self, step_index: int, step: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate cost and risk for a single step."""
        skill_id = step.get("skill", "unknown")
        params = step.get("params", {})

        estimate = self._get_skill_estimate(skill_id)

        # Adjust LLM cost based on prompt length
        cost_cents = estimate["cost_cents"]
        if skill_id == "llm_invoke" and "prompt" in params:
            # Rough estimate: 1 cent per 1000 chars
            prompt_len = len(str(params.get("prompt", "")))
            cost_cents = max(cost_cents, prompt_len // 1000)

        # Adjust HTTP latency based on timeout
        latency_ms = estimate["latency_ms"]
        if skill_id == "http_call" and "timeout" in params:
            latency_ms = min(latency_ms, params["timeout"] * 1000)

        return {
            "step_index": step_index,
            "skill_id": skill_id,
            "cost_cents": cost_cents,
            "latency_ms": latency_ms,
            "risk_probability": estimate["risk_probability"],
            "risk_type": estimate["risk_type"],
        }

    def simulate(self, plan: List[Dict[str, Any]]) -> SimulationResult:
        """
        Simulate plan execution.

        Args:
            plan: List of steps to simulate

        Returns:
            SimulationResult with estimates and feasibility
        """
        if not plan:
            return SimulationResult(
                feasible=False,
                status=FeasibilityStatus.INVALID_PLAN,
                estimated_cost_cents=0,
                estimated_duration_ms=0,
                budget_remaining_cents=self.budget_cents,
                budget_sufficient=True,
                permission_gaps=[],
                risks=[],
                step_estimates=[],
                alternatives=[],
                warnings=["Empty plan provided"],
            )

        step_estimates = []
        risks = []
        permission_gaps = []
        warnings = []
        total_cost = 0
        total_latency = 0
        cumulative_risk = 0.0

        for i, step in enumerate(plan):
            skill_id = step.get("skill", "unknown")
            iterations = step.get("iterations", 1)

            # Check permission
            if self.allowed_skills is not None and skill_id not in self.allowed_skills:
                permission_gaps.append(skill_id)

            # Get estimate for single execution
            estimate = self._estimate_step(i, step)

            # Multiply cost and latency by iterations
            step_cost = estimate["cost_cents"] * iterations
            step_latency = estimate["latency_ms"] * iterations

            # Add iterations info to estimate
            estimate["iterations"] = iterations
            estimate["base_cost_cents"] = estimate["cost_cents"]
            estimate["cost_cents"] = step_cost
            estimate["base_latency_ms"] = estimate["latency_ms"]
            estimate["latency_ms"] = step_latency

            step_estimates.append(estimate)

            total_cost += step_cost
            total_latency += step_latency

            # Track risks (risk compounds with iterations)
            if estimate["risk_probability"] > 0.05:
                # Risk increases with iterations: P(at least one failure) = 1 - (1-p)^n
                compounded_risk = 1.0 - ((1.0 - estimate["risk_probability"]) ** iterations)
                risks.append(
                    StepRisk(
                        step_index=i,
                        skill_id=skill_id,
                        risk_type=estimate["risk_type"],
                        probability=compounded_risk,
                        description=f"{skill_id} x{iterations} has {compounded_risk * 100:.0f}% chance of {estimate['risk_type']}",
                        mitigation=self._get_mitigation(estimate["risk_type"]),
                    )
                )

            # Calculate cumulative risk (simplified: 1 - product of success probabilities)
            # Use compounded risk for the step based on iterations
            step_risk = 1.0 - ((1.0 - estimate["risk_probability"]) ** iterations)
            cumulative_risk = 1.0 - ((1.0 - cumulative_risk) * (1.0 - step_risk))

        # Determine feasibility
        budget_sufficient = total_cost <= self.budget_cents
        has_permissions = len(permission_gaps) == 0
        risk_acceptable = cumulative_risk <= self.risk_threshold

        if not budget_sufficient:
            status = FeasibilityStatus.BUDGET_INSUFFICIENT
            feasible = False
        elif not has_permissions:
            status = FeasibilityStatus.PERMISSION_DENIED
            feasible = False
        elif not risk_acceptable:
            status = FeasibilityStatus.RISK_TOO_HIGH
            feasible = False
            warnings.append(
                f"Cumulative risk {cumulative_risk * 100:.0f}% exceeds threshold {self.risk_threshold * 100:.0f}%"
            )
        else:
            status = FeasibilityStatus.FEASIBLE
            feasible = True

        # Generate alternatives if not feasible
        alternatives = []
        if not budget_sufficient:
            alternatives.append(
                {
                    "suggestion": "Reduce LLM calls",
                    "potential_savings_cents": sum(
                        e["cost_cents"] for e in step_estimates if e["skill_id"] == "llm_invoke"
                    ),
                }
            )

        return SimulationResult(
            feasible=feasible,
            status=status,
            estimated_cost_cents=total_cost,
            estimated_duration_ms=total_latency,
            budget_remaining_cents=self.budget_cents - total_cost,
            budget_sufficient=budget_sufficient,
            permission_gaps=permission_gaps,
            risks=risks,
            step_estimates=step_estimates,
            alternatives=alternatives,
            warnings=warnings,
            metadata={
                "plan_steps": len(plan),
                "cumulative_risk": cumulative_risk,
                "budget_utilization": total_cost / max(self.budget_cents, 1),
            },
        )

    def _get_mitigation(self, risk_type: str) -> str:
        """Get mitigation suggestion for a risk type."""
        mitigations = {
            "timeout": "Add retry with exponential backoff",
            "rate_limit": "Implement client-side throttling",
            "transform_error": "Validate input schema before transform",
            "not_found": "Add existence check before access",
            "permission": "Verify permissions before write",
            "quota": "Check quota before operation",
            "delivery": "Use delivery confirmation",
            "unknown": "Add error handling and monitoring",
        }
        return mitigations.get(risk_type, "Add error handling")


def simulate_plan(
    plan: List[Dict[str, Any]],
    budget_cents: int = 1000,
    allowed_skills: Optional[List[str]] = None,
) -> SimulationResult:
    """
    Convenience function to simulate a plan.

    Args:
        plan: List of steps
        budget_cents: Available budget
        allowed_skills: Optional skill allowlist

    Returns:
        SimulationResult
    """
    simulator = CostSimulator(
        budget_cents=budget_cents,
        allowed_skills=allowed_skills,
    )
    return simulator.simulate(plan)


if __name__ == "__main__":
    # Quick smoke test
    print("=" * 60)
    print("Test 1: Basic plan (no iterations)")
    print("=" * 60)
    simulator = CostSimulator(budget_cents=100)

    plan = [
        {"skill": "http_call", "params": {"url": "https://api.example.com"}},
        {"skill": "llm_invoke", "params": {"prompt": "Analyze this data..."}},
        {"skill": "json_transform", "params": {"expression": "$.result"}},
    ]

    result = simulator.simulate(plan)
    print(f"Feasible: {result.feasible}")
    print(f"Status: {result.status.value}")
    print(f"Estimated cost: {result.estimated_cost_cents} cents")
    print(f"Estimated duration: {result.estimated_duration_ms} ms")
    print(f"Budget remaining: {result.budget_remaining_cents} cents")

    if result.risks:
        print("\nRisks:")
        for risk in result.risks:
            print(f"  - Step {risk.step_index}: {risk.description}")

    # Test with iterations
    print("\n" + "=" * 60)
    print("Test 2: Plan with iterations (llm_invoke x10, email_send x10)")
    print("Expected: 10*5 + 10*1 = 60 cents")
    print("=" * 60)
    simulator2 = CostSimulator(budget_cents=300)

    plan2 = [
        {"skill": "llm_invoke", "params": {"prompt": "Test"}, "iterations": 10},
        {"skill": "email_send", "params": {"to": "test@example.com"}, "iterations": 10},
    ]

    result2 = simulator2.simulate(plan2)
    print(f"Feasible: {result2.feasible}")
    print(f"Status: {result2.status.value}")
    print(f"Estimated cost: {result2.estimated_cost_cents} cents (expected: 60)")
    print(f"Estimated duration: {result2.estimated_duration_ms} ms")
    print(f"Budget remaining: {result2.budget_remaining_cents} cents")

    for step in result2.step_estimates:
        print(
            f"  Step {step['step_index']}: {step['skill_id']} x{step.get('iterations', 1)} = {step['cost_cents']} cents"
        )

    # Test budget failure with iterations
    print("\n" + "=" * 60)
    print("Test 3: Budget failure (llm_invoke x50 = 250 cents, budget = 100)")
    print("=" * 60)
    simulator3 = CostSimulator(budget_cents=100)

    plan3 = [
        {"skill": "llm_invoke", "params": {"prompt": "Test"}, "iterations": 50},
    ]

    result3 = simulator3.simulate(plan3)
    print(f"Feasible: {result3.feasible} (expected: False)")
    print(f"Status: {result3.status.value} (expected: budget_insufficient)")
    print(f"Estimated cost: {result3.estimated_cost_cents} cents (expected: 250)")
    print(f"Budget remaining: {result3.budget_remaining_cents} cents (expected: -150)")
