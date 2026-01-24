# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: per-step
#   Execution: sync
# Role: Policy prevention engine for runtime enforcement
# Callers: worker/runner.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: BACKEND_REMEDIATION_PLAN.md GAP-001, GAP-002

"""
Prevention Engine

Evaluates policies DURING run execution at each step checkpoint.
Uses the policy snapshot captured at run start (not live policies)
to ensure consistent enforcement throughout the run.

Key Responsibilities:
1. Evaluate step against policy thresholds
2. Determine action (ALLOW, WARN, BLOCK)
3. Return structured result for runner to act on

Remediation: GAP-001 (Prevention hook integration), GAP-002 (Run stop on violation)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("nova.policy.prevention_engine")


class PreventionAction(str, Enum):
    """Action to take based on policy evaluation."""
    ALLOW = "allow"  # Continue execution
    WARN = "warn"    # Continue but log warning
    BLOCK = "block"  # Stop execution immediately


class ViolationType(str, Enum):
    """Types of policy violations."""
    TOKEN_LIMIT = "token_limit"
    COST_LIMIT = "cost_limit"
    RATE_LIMIT = "rate_limit"
    CONTENT_POLICY = "content_policy"
    CUSTOM_RULE = "custom_rule"


@dataclass
class PreventionContext:
    """
    Context for policy evaluation at a step checkpoint.

    Immutable snapshot of execution state at evaluation time.
    """
    run_id: str
    tenant_id: str
    step_index: int
    policy_snapshot_id: Optional[str]

    # Accumulated metrics
    tokens_used: int = 0
    cost_cents: int = 0
    steps_completed: int = 0

    # Current step data
    step_skill: Optional[str] = None
    step_tokens: int = 0
    step_cost_cents: int = 0
    step_duration_ms: float = 0.0

    # LLM response (if applicable)
    llm_response: Optional[dict[str, Any]] = None

    # Thresholds from snapshot
    max_tokens_per_run: Optional[int] = None
    max_cost_cents_per_run: Optional[int] = None
    max_tokens_per_step: Optional[int] = None
    max_cost_cents_per_step: Optional[int] = None


@dataclass
class PreventionResult:
    """
    Result of policy evaluation.

    Contains the action to take and details about any violation.
    """
    action: PreventionAction
    policy_id: Optional[str] = None
    policy_name: Optional[str] = None
    violation_type: Optional[ViolationType] = None
    threshold_value: Optional[str] = None
    actual_value: Optional[str] = None
    reason: str = ""
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def allow(cls) -> "PreventionResult":
        """Create an ALLOW result."""
        return cls(action=PreventionAction.ALLOW)

    @classmethod
    def warn(cls, reason: str, policy_id: Optional[str] = None) -> "PreventionResult":
        """Create a WARN result."""
        return cls(
            action=PreventionAction.WARN,
            policy_id=policy_id,
            reason=reason,
        )

    @classmethod
    def block(
        cls,
        policy_id: str,
        policy_name: str,
        violation_type: ViolationType,
        threshold_value: str,
        actual_value: str,
        reason: str,
    ) -> "PreventionResult":
        """Create a BLOCK result."""
        return cls(
            action=PreventionAction.BLOCK,
            policy_id=policy_id,
            policy_name=policy_name,
            violation_type=violation_type,
            threshold_value=threshold_value,
            actual_value=actual_value,
            reason=reason,
        )


class PolicyViolationError(Exception):
    """
    Exception raised when a policy violation stops a run.

    Contains the full PreventionResult for the violation.
    """

    def __init__(self, result: PreventionResult):
        self.result = result
        super().__init__(result.reason)


class PreventionEngine:
    """
    Evaluates policies at runtime checkpoints.

    Uses policy snapshot from run start for consistent enforcement.
    """

    def __init__(self, policy_snapshot_id: Optional[str] = None):
        """
        Initialize prevention engine.

        Args:
            policy_snapshot_id: Reference to PolicySnapshot for this run
        """
        self.policy_snapshot_id = policy_snapshot_id
        self._thresholds: Optional[dict[str, Any]] = None
        self._policies: Optional[list[dict[str, Any]]] = None

    def load_snapshot(self, snapshot_id: str) -> bool:
        """
        Load policy snapshot for evaluation.

        Args:
            snapshot_id: ID of the PolicySnapshot to load

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            from sqlmodel import Session

            from app.db import engine
            from app.models.policy_snapshot import PolicySnapshot

            with Session(engine) as session:
                # Query by snapshot_id
                from sqlmodel import select
                stmt = select(PolicySnapshot).where(PolicySnapshot.snapshot_id == snapshot_id)
                result = session.exec(stmt)
                snapshot = result.first()

                if not snapshot:
                    logger.warning(
                        "policy_snapshot_not_found",
                        extra={"snapshot_id": snapshot_id},
                    )
                    return False

                # Verify integrity
                if not snapshot.verify_integrity():
                    logger.error(
                        "policy_snapshot_integrity_failed",
                        extra={"snapshot_id": snapshot_id},
                    )
                    return False

                self._thresholds = snapshot.get_thresholds()
                self._policies = snapshot.get_policies()
                self.policy_snapshot_id = snapshot_id

                logger.info(
                    "policy_snapshot_loaded",
                    extra={
                        "snapshot_id": snapshot_id,
                        "policy_count": snapshot.policy_count,
                    },
                )
                return True

        except Exception as e:
            logger.error(
                "policy_snapshot_load_failed",
                extra={"snapshot_id": snapshot_id, "error": str(e)},
            )
            return False

    def evaluate_step(self, context: PreventionContext) -> PreventionResult:
        """
        Evaluate policy at step checkpoint.

        Checks accumulated and step-level metrics against thresholds.
        Integrates conflict resolution (GAP-068), binding moments (GAP-031),
        and failure mode handling (GAP-035).

        Args:
            context: Current execution context

        Returns:
            PreventionResult with action to take
        """
        # GAP-035: Failure mode handling - wrap evaluation in try/except
        try:
            return self._evaluate_step_inner(context)
        except Exception as e:
            # GAP-035: Fail-closed on evaluation error
            from app.policy.failure_mode_handler import (
                handle_evaluation_error,
                FailureType,
            )

            failure_decision = handle_evaluation_error(
                error=e,
                context={
                    "run_id": context.run_id,
                    "tenant_id": context.tenant_id,
                    "step_index": context.step_index,
                },
            )

            if failure_decision.should_block:
                return PreventionResult.block(
                    policy_id="failure_mode",
                    policy_name="Failure Mode Handler",
                    violation_type=ViolationType.CUSTOM_RULE,
                    threshold_value="evaluation_success",
                    actual_value="evaluation_failed",
                    reason=failure_decision.reason,
                )
            else:
                # FAIL_WARN mode - log and continue
                logger.warning("prevention_evaluation_failed_warn", extra={
                    "run_id": context.run_id,
                    "error": str(e),
                })
                return PreventionResult.allow()

    def _evaluate_step_inner(self, context: PreventionContext) -> PreventionResult:
        """Inner evaluation logic (GAP-068, GAP-031 integrated)."""
        # If no snapshot loaded, allow (graceful degradation)
        if not self._thresholds:
            return PreventionResult.allow()

        # Check run-level token limit
        max_tokens = self._thresholds.get("max_tokens_per_run")
        if max_tokens and context.tokens_used > max_tokens:
            return PreventionResult.block(
                policy_id="threshold_token_limit",
                policy_name="Token Limit Policy",
                violation_type=ViolationType.TOKEN_LIMIT,
                threshold_value=str(max_tokens),
                actual_value=str(context.tokens_used),
                reason=f"Run exceeded token limit: {context.tokens_used} > {max_tokens}",
            )

        # Check run-level cost limit
        max_cost = self._thresholds.get("max_cost_cents_per_run")
        if max_cost and context.cost_cents > max_cost:
            return PreventionResult.block(
                policy_id="threshold_cost_limit",
                policy_name="Cost Limit Policy",
                violation_type=ViolationType.COST_LIMIT,
                threshold_value=str(max_cost),
                actual_value=str(context.cost_cents),
                reason=f"Run exceeded cost limit: {context.cost_cents}c > {max_cost}c",
            )

        # Check step-level token limit
        step_max_tokens = self._thresholds.get("max_tokens_per_step")
        if step_max_tokens and context.step_tokens > step_max_tokens:
            return PreventionResult.block(
                policy_id="threshold_step_token_limit",
                policy_name="Step Token Limit Policy",
                violation_type=ViolationType.TOKEN_LIMIT,
                threshold_value=str(step_max_tokens),
                actual_value=str(context.step_tokens),
                reason=f"Step exceeded token limit: {context.step_tokens} > {step_max_tokens}",
            )

        # Check step-level cost limit
        step_max_cost = self._thresholds.get("max_cost_cents_per_step")
        if step_max_cost and context.step_cost_cents > step_max_cost:
            return PreventionResult.block(
                policy_id="threshold_step_cost_limit",
                policy_name="Step Cost Limit Policy",
                violation_type=ViolationType.COST_LIMIT,
                threshold_value=str(step_max_cost),
                actual_value=str(context.step_cost_cents),
                reason=f"Step exceeded cost limit: {context.step_cost_cents}c > {step_max_cost}c",
            )

        # Check custom policies with conflict resolution (GAP-068) and binding moments (GAP-031)
        if self._policies:
            # GAP-031: Import binding moment enforcer
            from app.policy.binding_moment_enforcer import (
                should_evaluate_policy,
                EvaluationPoint,
            )

            # GAP-068: Import conflict resolver
            from app.policy.conflict_resolver import (
                resolve_policy_conflict,
                PolicyAction,
            )

            # Collect all policy evaluation results
            policy_actions = []

            for policy in self._policies:
                # GAP-031: Check binding moment before evaluating
                binding_context = {
                    "run_id": context.run_id,
                    "step_index": context.step_index,
                }
                binding_decision = should_evaluate_policy(
                    policy=type('Policy', (), {
                        'id': policy.get('id', 'unknown'),
                        'bind_at': policy.get('bind_at'),
                    })(),
                    context=binding_context,
                    evaluation_point=EvaluationPoint.STEP_POST,
                )

                if not binding_decision.should_evaluate:
                    logger.debug("policy_skipped_binding_moment", extra={
                        "policy_id": policy.get("id"),
                        "reason": binding_decision.reason,
                    })
                    continue

                result = self._evaluate_custom_policy(policy, context)

                # Convert to PolicyAction for conflict resolution
                if result.action == PreventionAction.BLOCK:
                    policy_actions.append(PolicyAction(
                        action="STOP",
                        policy_id=result.policy_id or "unknown",
                        reason=result.reason,
                        precedence=policy.get("precedence", 100),
                    ))
                elif result.action == PreventionAction.WARN:
                    policy_actions.append(PolicyAction(
                        action="WARN",
                        policy_id=result.policy_id or "unknown",
                        reason=result.reason,
                        precedence=policy.get("precedence", 100),
                    ))

            # GAP-068: Resolve conflicts if multiple policies evaluated
            if policy_actions:
                resolved = resolve_policy_conflict(
                    actions=policy_actions,
                    context={
                        "run_id": context.run_id,
                        "step_index": context.step_index,
                    },
                )

                if resolved.action.upper() in ("STOP", "BLOCK", "KILL"):
                    return PreventionResult.block(
                        policy_id=resolved.policy_id,
                        policy_name=f"Resolved from {len(policy_actions)} policies",
                        violation_type=ViolationType.CUSTOM_RULE,
                        threshold_value="policy_allow",
                        actual_value=resolved.action.upper(),
                        reason=resolved.reason,
                    )
                elif resolved.action.upper() == "WARN":
                    # Log warning but continue
                    logger.warning("policy_conflict_resolved_warn", extra={
                        "resolved_action": resolved.action,
                        "policy_id": resolved.policy_id,
                        "conflicting_count": len(policy_actions),
                    })

        return PreventionResult.allow()

    def _evaluate_custom_policy(
        self,
        policy: dict[str, Any],
        context: PreventionContext,
    ) -> PreventionResult:
        """
        Evaluate a custom policy rule.

        Args:
            policy: Policy definition
            context: Execution context

        Returns:
            PreventionResult
        """
        policy_id = policy.get("id", "unknown")
        policy_name = policy.get("name", "Custom Policy")
        policy_type = policy.get("type", "")

        # Skip inactive policies
        if not policy.get("active", True):
            return PreventionResult.allow()

        # Example: Rate limit check
        if policy_type == "rate_limit":
            max_steps = policy.get("max_steps_per_minute")
            if max_steps and context.steps_completed > max_steps:
                return PreventionResult.block(
                    policy_id=policy_id,
                    policy_name=policy_name,
                    violation_type=ViolationType.RATE_LIMIT,
                    threshold_value=str(max_steps),
                    actual_value=str(context.steps_completed),
                    reason=f"Rate limit exceeded: {context.steps_completed} steps > {max_steps}/min",
                )

        return PreventionResult.allow()


def create_policy_snapshot_for_run(
    tenant_id: str,
    run_id: str,
) -> Optional[str]:
    """
    Create a policy snapshot at run start.

    Captures all active policies and thresholds for consistent
    evaluation throughout the run.

    Args:
        tenant_id: Tenant ID
        run_id: Run ID for reference

    Returns:
        snapshot_id if created, None on failure
    """
    try:
        from sqlmodel import Session

        from app.db import engine
        from app.models.policy_snapshot import PolicySnapshot

        # TODO: Load actual policies from policy engine
        # For now, use default thresholds
        policies: list[dict[str, Any]] = []
        thresholds = {
            "max_tokens_per_run": 100000,  # 100K tokens per run
            "max_cost_cents_per_run": 1000,  # $10 per run
            "max_tokens_per_step": 10000,  # 10K tokens per step
            "max_cost_cents_per_step": 100,  # $1 per step
        }

        snapshot = PolicySnapshot.create_snapshot(
            tenant_id=tenant_id,
            policies=policies,
            thresholds=thresholds,
        )

        with Session(engine) as session:
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)

            logger.info(
                "policy_snapshot_created",
                extra={
                    "snapshot_id": snapshot.snapshot_id,
                    "run_id": run_id,
                    "tenant_id": tenant_id,
                },
            )
            return snapshot.snapshot_id

    except Exception as e:
        logger.error(
            "policy_snapshot_creation_failed",
            extra={"run_id": run_id, "tenant_id": tenant_id, "error": str(e)},
        )
        return None
