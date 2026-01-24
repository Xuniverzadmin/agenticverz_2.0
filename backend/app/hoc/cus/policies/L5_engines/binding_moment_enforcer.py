# Layer: L5 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api (during policy evaluation)
#   Execution: sync
# Role: Enforce binding moments - when policies are evaluated
# Callers: prevention_engine.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-031

"""
Module: binding_moment_enforcer
Purpose: Ensures policies are evaluated at the correct binding moment.

Binding moments define WHEN a policy is evaluated:
- RUN_START: Evaluate once at run start (snapshot-based)
- STEP_START: Evaluate before each step
- STEP_END: Evaluate after each step
- ON_CHANGE: Evaluate when specific fields change

If a policy has bind_at=RUN_START, it should NOT be re-evaluated mid-run.

Imports (Dependencies):
    - None (standalone)

Exports (Provides):
    - should_evaluate_policy(policy, context) -> bool
    - BindingMoment: Enum
    - get_binding_moment(policy) -> BindingMoment

Wiring Points:
    - Called from: prevention_engine.py before evaluating each policy

Acceptance Criteria:
    - [x] AC-031-01: RUN_START binding respected
    - [x] AC-031-02: STEP_START binding respected
    - [x] AC-031-03: Mid-run re-eval blocked for RUN_START
    - [x] AC-031-04: Binding moment logged
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Dict, Set
from datetime import datetime, timezone
import logging

logger = logging.getLogger("nova.policy.binding_moment_enforcer")


class BindingMoment(str, Enum):
    """When a policy should be evaluated."""
    RUN_START = "run_start"      # Once at run start
    STEP_START = "step_start"    # Before each step
    STEP_END = "step_end"        # After each step
    ON_CHANGE = "on_change"      # When monitored fields change
    ALWAYS = "always"            # Every evaluation point


class EvaluationPoint(str, Enum):
    """Current point in execution where evaluation is requested."""
    RUN_INIT = "run_init"        # Run initialization
    STEP_PRE = "step_pre"        # Before step execution
    STEP_POST = "step_post"      # After step execution
    MID_RUN = "mid_run"          # Mid-run check (e.g., policy change)


@dataclass
class BindingDecision:
    """Decision about whether to evaluate a policy."""
    should_evaluate: bool
    binding_moment: BindingMoment
    evaluation_point: EvaluationPoint
    reason: str
    policy_id: str


# Cache of already-evaluated policies per run (for RUN_START binding)
_run_evaluated_policies: Dict[str, Set[str]] = {}


def should_evaluate_policy(
    policy: Any,
    context: Dict[str, Any],
    evaluation_point: EvaluationPoint,
) -> BindingDecision:
    """
    Determine if a policy should be evaluated at this point.

    Respects the policy's bind_at setting:
    - RUN_START: Only evaluate once per run, at initialization
    - STEP_START: Evaluate before each step
    - STEP_END: Evaluate after each step
    - ON_CHANGE: Evaluate only when monitored fields change
    - ALWAYS: Evaluate at every point

    Args:
        policy: Policy object with bind_at attribute
        context: Evaluation context with run_id, step info, etc.
        evaluation_point: Current point in execution

    Returns:
        BindingDecision with should_evaluate and reason
    """
    policy_id = getattr(policy, 'id', str(policy)) if policy else 'unknown'
    run_id = context.get('run_id', 'unknown')

    # Get binding moment from policy
    binding_moment = get_binding_moment(policy)

    # Check based on binding moment
    if binding_moment == BindingMoment.RUN_START:
        # Only evaluate at run initialization
        if evaluation_point == EvaluationPoint.RUN_INIT:
            # Mark as evaluated for this run
            _mark_evaluated(run_id, policy_id)
            return BindingDecision(
                should_evaluate=True,
                binding_moment=binding_moment,
                evaluation_point=evaluation_point,
                reason="RUN_START policy at run init",
                policy_id=policy_id,
            )
        else:
            # Check if already evaluated for this run
            if _was_evaluated(run_id, policy_id):
                logger.debug("binding_moment.skipped_already_evaluated", extra={
                    "policy_id": policy_id,
                    "run_id": run_id,
                    "binding_moment": binding_moment.value,
                    "evaluation_point": evaluation_point.value,
                })
                return BindingDecision(
                    should_evaluate=False,
                    binding_moment=binding_moment,
                    evaluation_point=evaluation_point,
                    reason="RUN_START policy already evaluated for this run",
                    policy_id=policy_id,
                )
            else:
                # Not yet evaluated - this is first encounter, evaluate it
                _mark_evaluated(run_id, policy_id)
                return BindingDecision(
                    should_evaluate=True,
                    binding_moment=binding_moment,
                    evaluation_point=evaluation_point,
                    reason="RUN_START policy first evaluation",
                    policy_id=policy_id,
                )

    elif binding_moment == BindingMoment.STEP_START:
        # Evaluate only before steps
        should_eval = evaluation_point in (EvaluationPoint.STEP_PRE, EvaluationPoint.RUN_INIT)
        return BindingDecision(
            should_evaluate=should_eval,
            binding_moment=binding_moment,
            evaluation_point=evaluation_point,
            reason="STEP_START policy" if should_eval else "STEP_START not at step pre",
            policy_id=policy_id,
        )

    elif binding_moment == BindingMoment.STEP_END:
        # Evaluate only after steps
        should_eval = evaluation_point == EvaluationPoint.STEP_POST
        return BindingDecision(
            should_evaluate=should_eval,
            binding_moment=binding_moment,
            evaluation_point=evaluation_point,
            reason="STEP_END policy" if should_eval else "STEP_END not at step post",
            policy_id=policy_id,
        )

    elif binding_moment == BindingMoment.ON_CHANGE:
        # Check if monitored fields changed
        should_eval = _check_fields_changed(policy, context)
        return BindingDecision(
            should_evaluate=should_eval,
            binding_moment=binding_moment,
            evaluation_point=evaluation_point,
            reason="ON_CHANGE fields changed" if should_eval else "ON_CHANGE no changes",
            policy_id=policy_id,
        )

    else:  # ALWAYS
        return BindingDecision(
            should_evaluate=True,
            binding_moment=binding_moment,
            evaluation_point=evaluation_point,
            reason="ALWAYS binding",
            policy_id=policy_id,
        )


def get_binding_moment(policy: Any) -> BindingMoment:
    """
    Get the binding moment for a policy.

    Args:
        policy: Policy object

    Returns:
        BindingMoment enum value
    """
    if policy is None:
        return BindingMoment.ALWAYS

    # Try to get bind_at from policy
    bind_at = getattr(policy, 'bind_at', None)

    if bind_at is None:
        # Check for nested config
        config = getattr(policy, 'config', None)
        if config:
            bind_at = getattr(config, 'bind_at', None)

    if bind_at is None:
        # Default to ALWAYS if not specified
        return BindingMoment.ALWAYS

    # Convert to enum
    if isinstance(bind_at, BindingMoment):
        return bind_at

    try:
        return BindingMoment(bind_at.lower() if isinstance(bind_at, str) else bind_at)
    except ValueError:
        logger.warning("binding_moment.invalid_value", extra={
            "policy_id": getattr(policy, 'id', 'unknown'),
            "bind_at": bind_at,
            "defaulting_to": BindingMoment.ALWAYS.value,
        })
        return BindingMoment.ALWAYS


def clear_run_cache(run_id: str) -> None:
    """Clear the evaluation cache for a run (call on run completion)."""
    if run_id in _run_evaluated_policies:
        del _run_evaluated_policies[run_id]


def _mark_evaluated(run_id: str, policy_id: str) -> None:
    """Mark a policy as evaluated for a run."""
    if run_id not in _run_evaluated_policies:
        _run_evaluated_policies[run_id] = set()
    _run_evaluated_policies[run_id].add(policy_id)


def _was_evaluated(run_id: str, policy_id: str) -> bool:
    """Check if a policy was already evaluated for a run."""
    return run_id in _run_evaluated_policies and policy_id in _run_evaluated_policies[run_id]


def _check_fields_changed(policy: Any, context: Dict[str, Any]) -> bool:
    """Check if monitored fields changed (for ON_CHANGE binding)."""
    # Get monitored fields from policy
    monitored_fields = getattr(policy, 'monitored_fields', [])
    if not monitored_fields:
        return True  # No fields specified, always evaluate

    # Get previous and current values from context
    prev_values = context.get('prev_field_values', {})
    curr_values = context.get('curr_field_values', {})

    # Check if any monitored field changed
    for field in monitored_fields:
        if prev_values.get(field) != curr_values.get(field):
            return True

    return False
