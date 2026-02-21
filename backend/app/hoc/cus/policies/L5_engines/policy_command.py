# capability_id: CAP-009
# Layer: L5 — Domain Engine (Command Facade)
# AUDIENCE: CUSTOMER
# NOTE: Header corrected L4→L5 (2026-01-31) — file is in L5_engines/
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async (delegates to L5)
# Role: Policy evaluation and decision authority
# Callers: policy_adapter.py (L3)
# Allowed Imports: L4, L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-258 Phase F-3 Policy Cluster
# Contract: PHASE_F_FIX_DESIGN (F-P-RULE-1 to F-P-RULE-5)
#
# GOVERNANCE NOTE (F-P-RULE-1):
# This L4 command owns ALL policy decisions. L2/L3 must NEVER evaluate
# policy truth. All cost feasibility, policy enforcement, and outcome
# classification happens here.
#
# F-P-RULE-1: Policy Decisions Live Only in L4 - all decisions here
# F-P-RULE-2: Metrics Are Effects - emitted via L5, not decisions
# F-P-RULE-3: L3 Is Translation Only - no branching, no thresholds
# F-P-RULE-4: No Dual Ownership - CostSimulator logic stays intact

"""
Policy Command (L4)

Domain command for policy evaluation and approval workflow. This L4 command:
1. Owns all policy decisions (cost feasibility, violations, outcomes)
2. Delegates to L5 for execution (metrics, simulation, enforcement)
3. Returns result objects to L3 adapter

This command may import L5 (workflow.metrics, workflow.cost_sim, workflow.policies)
because L4 → L5 is allowed per layer rules.

Reference: PIN-258 Phase F-3 Policy Cluster
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.commands.policy")


# =============================================================================
# L4 Command Result Types
# =============================================================================


@dataclass
class PolicyViolation:
    """A policy violation detected during evaluation."""

    type: str
    message: str
    policy: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyEvaluationResult:
    """Result from policy evaluation command."""

    decision: str  # "allow", "deny", "requires_approval"
    reasons: List[str]
    simulated_cost_cents: Optional[int] = None
    violations: List[PolicyViolation] = field(default_factory=list)
    approval_level_required: Optional[int] = None
    auto_approve_threshold_cents: Optional[int] = None


@dataclass
class ApprovalConfig:
    """Approval level configuration."""

    approval_level: int
    auto_approve_max_cost_cents: int
    require_human_approval: bool
    webhook_url: Optional[str]
    escalate_to: Optional[str]
    escalation_timeout_seconds: int


# =============================================================================
# L4 Domain Decisions: Cost Simulation (delegates to L5)
# =============================================================================


async def simulate_cost(
    skill_id: str,
    tenant_id: str,
    payload: Dict[str, Any],
) -> Optional[int]:
    """
    Simulate cost for a skill execution.

    This L4 command delegates to L5 CostSimulator.
    L4 → L5 is allowed per layer rules.

    Args:
        skill_id: Skill to simulate
        tenant_id: Tenant context
        payload: Execution payload

    Returns:
        Estimated cost in cents, or fallback estimate

    Reference: PIN-258 Phase F-3 (F-P-RULE-4: No Dual Ownership)
    """
    try:
        from app.workflow.cost_sim import CostSimulator

        sim = CostSimulator()
        result = await sim.simulate(skill_id=skill_id, tenant_id=tenant_id, payload=payload)
        return int(result.estimated_cost_cents)
    except ImportError:
        logger.debug("CostSimulator not available")
    except Exception as e:
        logger.warning(f"Cost simulation failed: {e}")

    # Fallback estimate
    return 10


# =============================================================================
# L4 Domain Decisions: Policy Enforcement (delegates to L5)
# =============================================================================


async def check_policy_violations(
    skill_id: str,
    tenant_id: str,
    agent_id: Optional[str],
    payload: Dict[str, Any],
    simulated_cost: Optional[int],
) -> List[PolicyViolation]:
    """
    Check for policy violations.

    This L4 command delegates to L5 PolicyEnforcer.
    L4 → L5 is allowed per layer rules.

    Args:
        skill_id: Skill being evaluated
        tenant_id: Tenant context
        agent_id: Optional agent context
        payload: Execution payload
        simulated_cost: Cost estimate from simulation

    Returns:
        List of policy violations found

    Reference: PIN-258 Phase F-3 (F-P-RULE-1: Policy Decisions in L4)
    """
    violations: List[PolicyViolation] = []

    try:
        from dataclasses import dataclass as dc

        from app.workflow.policies import BudgetExceededError, PolicyEnforcer, PolicyViolationError

        @dc
        class MinimalStep:
            id: str = "sandbox_eval"
            estimated_cost_cents: int = 0
            max_cost_cents: Optional[int] = None
            idempotency_key: Optional[str] = "sandbox"
            retry: bool = False
            max_retries: int = 0
            inputs: Dict[str, Any] = None

            def __post_init__(self):
                if self.inputs is None:
                    self.inputs = {}

        @dc
        class MinimalContext:
            run_id: str = "sandbox_eval"

        step = MinimalStep(estimated_cost_cents=simulated_cost or 0, inputs=payload)
        ctx = MinimalContext()
        enforcer = PolicyEnforcer()

        try:
            await enforcer.check_can_execute(step, ctx, agent_id=agent_id)
        except BudgetExceededError as e:
            violations.append(
                PolicyViolation(
                    type="BudgetExceededError",
                    message=str(e),
                    policy="budget",
                    details={"breach_type": e.breach_type, "limit_cents": e.limit_cents},
                )
            )
            # Record metric via L5 (F-P-RULE-2: Metrics are effects)
            _record_budget_rejection("cost", skill_id)
        except PolicyViolationError as e:
            violations.append(
                PolicyViolation(
                    type="PolicyViolationError",
                    message=str(e),
                    policy=e.policy,
                    details=e.details,
                )
            )
            # Record metric via L5 (F-P-RULE-2: Metrics are effects)
            _record_capability_violation(e.policy, skill_id, tenant_id)
        except Exception as e:
            violations.append(
                PolicyViolation(
                    type=type(e).__name__,
                    message=str(e),
                    policy="unknown",
                    details={},
                )
            )

    except ImportError:
        logger.debug("PolicyEnforcer not available")

    return violations


# =============================================================================
# L4 Domain Decisions: Policy Evaluation (combines simulation + enforcement)
# =============================================================================


async def evaluate_policy(
    skill_id: str,
    tenant_id: str,
    agent_id: Optional[str],
    payload: Dict[str, Any],
    auto_approve_max_cost_cents: int = 0,
    approval_level: int = 1,
) -> PolicyEvaluationResult:
    """
    Evaluate policy for a skill execution.

    This L4 command orchestrates:
    1. Cost simulation (via L5)
    2. Policy violation check (via L5)
    3. Decision determination
    4. Metrics emission (via L5)

    L4 → L5 is allowed per layer rules.

    Args:
        skill_id: Skill to evaluate
        tenant_id: Tenant context
        agent_id: Optional agent context
        payload: Execution payload
        auto_approve_max_cost_cents: Threshold for auto-approval
        approval_level: Required approval level

    Returns:
        PolicyEvaluationResult with decision and details

    Reference: PIN-258 Phase F-3 (F-P-RULE-1: Policy Decisions in L4)
    """
    # Step 1: Simulate cost (L4 → L5)
    simulated_cost = await simulate_cost(
        skill_id=skill_id,
        tenant_id=tenant_id,
        payload=payload,
    )

    # Step 2: Check violations (L4 → L5)
    violations = await check_policy_violations(
        skill_id=skill_id,
        tenant_id=tenant_id,
        agent_id=agent_id,
        payload=payload,
        simulated_cost=simulated_cost,
    )

    # Step 3: Determine decision (F-P-RULE-1: Decision in L4)
    if not violations:
        if simulated_cost is not None and simulated_cost <= auto_approve_max_cost_cents:
            decision = "allow"
            reasons = ["Within auto-approve threshold"]
        else:
            decision = "allow"
            reasons = ["No policy violations"]
        # Record metric (F-P-RULE-2: Metrics are effects via L5)
        _record_policy_decision("allow", "cost")
    else:
        decision = "deny"
        reasons = [v.message for v in violations]

        overridable = all(v.type in ("BudgetExceededError", "PolicyViolationError") for v in violations)
        if overridable:
            decision = "requires_approval"
            reasons.append(f"Requires level {approval_level} approval")

        # Record metric (F-P-RULE-2: Metrics are effects via L5)
        _record_policy_decision(decision, "cost")

    return PolicyEvaluationResult(
        decision=decision,
        reasons=reasons,
        simulated_cost_cents=simulated_cost,
        violations=violations,
        approval_level_required=approval_level if decision == "requires_approval" else None,
        auto_approve_threshold_cents=auto_approve_max_cost_cents,
    )


# =============================================================================
# L4 Effects: Metrics Emission (delegates to L5)
# =============================================================================
# F-P-RULE-2: Metrics Are Effects, Not Decisions
# L4 → L5 import is allowed. Metrics are emitted as side effects of decisions.


def _record_policy_decision(decision: str, policy_type: str) -> None:
    """
    Record policy decision metric.

    L4 → L5 is allowed. This is an effect, not a decision.
    """
    try:
        from app.workflow.metrics import record_policy_decision

        record_policy_decision(decision, policy_type)
    except Exception as e:
        logger.debug(f"Failed to record policy decision metric: {e}")


def _record_capability_violation(violation_type: str, skill_id: str, tenant_id: Optional[str] = None) -> None:
    """
    Record capability violation metric.

    L4 → L5 is allowed. This is an effect, not a decision.
    """
    try:
        from app.workflow.metrics import record_capability_violation

        record_capability_violation(violation_type, skill_id, tenant_id)
    except Exception as e:
        logger.debug(f"Failed to record capability violation metric: {e}")


def _record_budget_rejection(resource_type: str, skill_id: str) -> None:
    """
    Record budget rejection metric.

    L4 → L5 is allowed. This is an effect, not a decision.
    """
    try:
        from app.workflow.metrics import record_budget_rejection

        record_budget_rejection(resource_type, skill_id)
    except Exception as e:
        logger.debug(f"Failed to record budget rejection metric: {e}")


def _record_approval_request_created(policy_type: str) -> None:
    """
    Record approval request creation metric.

    L4 → L5 is allowed. This is an effect, not a decision.
    """
    try:
        from app.workflow.metrics import record_approval_request_created

        record_approval_request_created(policy_type)
    except Exception as e:
        logger.debug(f"Failed to record approval request metric: {e}")


def _record_approval_action(result: str) -> None:
    """
    Record approval action metric.

    L4 → L5 is allowed. This is an effect, not a decision.
    """
    try:
        from app.workflow.metrics import record_approval_action

        record_approval_action(result)
    except Exception as e:
        logger.debug(f"Failed to record approval action metric: {e}")


def _record_approval_escalation() -> None:
    """
    Record approval escalation metric.

    L4 → L5 is allowed. This is an effect, not a decision.
    """
    try:
        from app.workflow.metrics import record_approval_escalation

        record_approval_escalation()
    except Exception as e:
        logger.debug(f"Failed to record approval escalation metric: {e}")


def _record_webhook_fallback() -> None:
    """
    Record webhook fallback metric.

    L4 → L5 is allowed. This is an effect, not a decision.
    """
    try:
        from app.workflow.metrics import record_webhook_fallback

        record_webhook_fallback()
    except Exception as e:
        logger.debug(f"Failed to record webhook fallback metric: {e}")


# =============================================================================
# L4 Commands: Approval Workflow Actions
# =============================================================================


def record_approval_created(policy_type: str) -> None:
    """
    Record that an approval request was created.

    This is a public L4 command for L3 to call.
    Delegates metric emission to L5.
    """
    _record_approval_request_created(policy_type)


def record_approval_outcome(result: str) -> None:
    """
    Record approval outcome (approved/rejected/expired).

    This is a public L4 command for L3 to call.
    Delegates metric emission to L5.
    """
    _record_approval_action(result)


def record_escalation() -> None:
    """
    Record that an escalation occurred.

    This is a public L4 command for L3 to call.
    Delegates metric emission to L5.
    """
    _record_approval_escalation()


def record_webhook_used() -> None:
    """
    Record that webhook fallback was used.

    This is a public L4 command for L3 to call.
    Delegates metric emission to L5.
    """
    _record_webhook_fallback()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Result types
    "PolicyViolation",
    "PolicyEvaluationResult",
    "ApprovalConfig",
    # Cost simulation
    "simulate_cost",
    # Policy enforcement
    "check_policy_violations",
    # Policy evaluation
    "evaluate_policy",
    # Approval workflow commands
    "record_approval_created",
    "record_approval_outcome",
    "record_escalation",
    "record_webhook_used",
]
