# Layer: L5 — Domain Engine (System Truth)
# AUDIENCE: CUSTOMER
# Product: system-wide (NOT console-owned)
# Temporal:
#   Trigger: worker (via failure events)
#   Execution: async
# Lifecycle:
#   Emits: recovery_decision_emitted
#   Subscribes: run_failed
# Data Access:
#   Reads: RecoveryRule, FailureHistory (via driver)
#   Writes: RecoveryDecision (via driver)
# Role: Recovery evaluation decision-making (domain logic)
# Authority: Recovery decision generation (M9/M10 pattern)
# Callers: API endpoints, failure processing pipeline
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Contract: DECISION_RECORD_CONTRACT.md
# Reference: PIN-470, PIN-257 Phase R-1 (L5→L4 Violation Fix)
#
# GOVERNANCE NOTE: This L4 engine owns all DECISION logic.
# L5 recovery_evaluator.py owns only EXECUTION logic.
# This separation fixes the L5→L4 import violations identified in
# PHASE_R_L5_L4_VIOLATIONS.md.

# M10 Recovery Evaluation Engine (L4 Domain Logic)
"""
Domain engine for recovery evaluation decisions.

This L4 engine contains the authoritative decision logic for:
1. Rule evaluation - evaluate_rules()
2. Pattern matching - RecoveryMatcher
3. Confidence combination - combine_confidences()
4. Action selection threshold - should_select_action()
5. Auto-execution threshold - should_auto_execute()
6. Decision record emission - emit_recovery_decision()

L5 workers must call this engine and execute the returned decisions,
not implement their own decision logic.

Reference: PIN-257 Phase R-1
Governance: PHASE_R_L5_L4_VIOLATIONS.md
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("nova.services.recovery_evaluation_engine")

# L4 imports (same layer - allowed)
from app.contracts.decisions import emit_recovery_decision
# L6/L5 imports (migrated to HOC per SWEEP-09)
from app.hoc.cus.policies.L6_drivers.recovery_matcher import RecoveryMatcher
# PIN-507 Law 6: Import pure decision functions from utilities (not schemas)
from app.hoc.hoc_spine.utilities.recovery_decisions import (
    combine_confidences,
    should_auto_execute,
    should_select_action,
)
# PIN-507 Law 6: Import evaluate_rules directly from its engine (not via schemas proxy)
from app.hoc.cus.incidents.L5_engines.recovery_rule_engine import (
    evaluate_rules,
)

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class FailureContext:
    """Context for recovery evaluation (mirrors L5 FailureEvent for L4 use)."""

    failure_match_id: str
    error_code: str
    error_message: str
    skill_id: Optional[str] = None
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    occurred_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.occurred_at is None:
            self.occurred_at = datetime.now(timezone.utc)


@dataclass
class RecoveryDecision:
    """
    Domain decision DTO returned by L4 engine to L5 executor.

    This dataclass contains all decisions made by L4 domain logic.
    L5 must execute based on these decisions without reimplementing logic.

    Reference: PIN-257 Phase R-1
    """

    # Core decision outputs
    suggested_action: Optional[str]
    combined_confidence: float
    should_select_action: bool
    should_auto_execute: bool

    # Supporting data for execution
    candidate_id: Optional[int]
    rule_result: Dict[str, Any]
    match_confidence: float

    # Context (passed through from input)
    failure_match_id: str
    run_id: Optional[str]
    tenant_id: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggested_action": self.suggested_action,
            "combined_confidence": self.combined_confidence,
            "should_select_action": self.should_select_action,
            "should_auto_execute": self.should_auto_execute,
            "candidate_id": self.candidate_id,
            "rule_result": self.rule_result,
            "match_confidence": self.match_confidence,
            "failure_match_id": self.failure_match_id,
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
        }


# =============================================================================
# Recovery Evaluation Engine (L4 Domain Logic)
# =============================================================================


class RecoveryEvaluationEngine:
    """
    L4 Domain Engine for recovery evaluation decisions.

    This engine contains ALL domain decision logic that was previously
    scattered in L5 recovery_evaluator.py. It evaluates failure context
    and returns a RecoveryDecision DTO that L5 must execute.

    L5 may NOT:
    - Re-implement rule evaluation
    - Re-calculate confidence scores
    - Make action selection decisions
    - Make auto-execution decisions
    - Emit decision records

    L5 may ONLY:
    - Execute the decision returned by this engine
    - Perform DB operations (L6)
    - Trigger execution hooks

    Reference: PIN-257 Phase R-1
    Governance: PHASE_R_L5_L4_VIOLATIONS.md Section 3.4
    """

    def __init__(self):
        """Initialize the evaluation engine."""
        self._matcher = RecoveryMatcher()

    def evaluate(self, context: FailureContext) -> RecoveryDecision:
        """
        Evaluate failure context and produce recovery decision.

        This is the core L4 domain decision function. It:
        1. Evaluates rules against the failure context
        2. Generates suggestion via pattern matching
        3. Combines confidence scores (L4 domain formula)
        4. Determines if action should be selected (L4 threshold)
        5. Determines if should auto-execute (L4 threshold)

        Args:
            context: FailureContext with error details

        Returns:
            RecoveryDecision with all domain decisions

        Reference: PIN-257 Phase R-1
        """
        # Step 1: Evaluate rules (L4 domain logic)
        rule_result = evaluate_rules(
            error_code=context.error_code,
            error_message=context.error_message,
            skill_id=context.skill_id,
            tenant_id=context.tenant_id,
            occurrence_count=context.metadata.get("occurrence_count", 1),
        )

        logger.info(
            f"L4 Rule evaluation for {context.failure_match_id}: "
            f"action={rule_result.recommended_action}, "
            f"confidence={rule_result.confidence:.2f}"
        )

        # Step 2: Generate suggestion via matcher (L4 domain logic)
        match_result = self._matcher.suggest(
            {
                "failure_match_id": context.failure_match_id,
                "failure_payload": {
                    "error_type": context.error_code,
                    "raw": context.error_message,
                    "meta": context.metadata,
                },
                "source": "worker",
                "occurred_at": context.occurred_at.isoformat() if context.occurred_at else None,
            }
        )

        candidate_id = match_result.candidate_id

        # Step 3: Combine confidences (L4 domain formula)
        # Reference: PIN-257 Phase E-4 Extraction #3
        combined_confidence = combine_confidences(
            rule_confidence=rule_result.confidence,
            match_confidence=match_result.confidence,
        )

        # Step 4: Determine if action should be selected (L4 threshold)
        # Reference: PIN-257 Phase E-4 Extraction #3
        should_select = should_select_action(combined_confidence)

        # Step 5: Determine if should auto-execute (L4 threshold)
        # Reference: PIN-254 Phase A Fix (SHADOW-001)
        should_auto = should_auto_execute(combined_confidence)

        logger.info(
            f"L4 Decision for {context.failure_match_id}: "
            f"combined_confidence={combined_confidence:.2f}, "
            f"should_select={should_select}, "
            f"should_auto_execute={should_auto}"
        )

        return RecoveryDecision(
            suggested_action=rule_result.recommended_action,
            combined_confidence=combined_confidence,
            should_select_action=should_select,
            should_auto_execute=should_auto,
            candidate_id=candidate_id,
            rule_result=rule_result.to_dict(),
            match_confidence=match_result.confidence,
            failure_match_id=context.failure_match_id,
            run_id=context.run_id,
            tenant_id=context.tenant_id,
        )

    def emit_decision_record(
        self,
        decision: RecoveryDecision,
        evaluated: bool,
        triggered: bool,
    ) -> None:
        """
        Emit recovery decision record (L4 domain responsibility).

        This was previously in L5 recovery_evaluator.py but belongs in L4
        because decision record emission is part of decision-making authority.

        Args:
            decision: The RecoveryDecision produced by evaluate()
            evaluated: Whether evaluation completed successfully
            triggered: Whether auto-execution was triggered

        Reference: DECISION_RECORD_CONTRACT v0.2
        """
        # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant for telemetry.
        # Skip telemetry for decisions without tenant_id rather than using fake tenant.
        if decision.tenant_id:
            emit_recovery_decision(
                run_id=decision.run_id,
                evaluated=evaluated,
                triggered=triggered,
                action=decision.suggested_action,
                candidates_count=1 if decision.candidate_id else 0,
                reason=f"Confidence: {decision.combined_confidence:.2f}, action: {decision.suggested_action or 'none'}",
                tenant_id=decision.tenant_id,
            )


# =============================================================================
# Convenience Functions
# =============================================================================


def evaluate_recovery(
    failure_match_id: str,
    error_code: str,
    error_message: str,
    **kwargs,
) -> RecoveryDecision:
    """
    Convenience function to evaluate a failure and get a decision.

    This is the L4 entry point for recovery evaluation. It returns
    a RecoveryDecision that L5 must execute.

    Args:
        failure_match_id: ID of the failure match record
        error_code: Error code
        error_message: Error message
        **kwargs: Additional context fields

    Returns:
        RecoveryDecision with all domain decisions

    Reference: PIN-257 Phase R-1
    """
    context = FailureContext(
        failure_match_id=failure_match_id,
        error_code=error_code,
        error_message=error_message,
        skill_id=kwargs.get("skill_id"),
        tenant_id=kwargs.get("tenant_id"),
        agent_id=kwargs.get("agent_id"),
        run_id=kwargs.get("run_id"),
        metadata=kwargs.get("metadata", {}),
    )

    engine = RecoveryEvaluationEngine()
    return engine.evaluate(context)


async def evaluate_and_execute(
    failure_match_id: str,
    error_code: str,
    error_message: str,
    **kwargs,
) -> "EvaluationOutcome":
    """
    Full entry point: evaluate failure and execute decision.

    This L4 function:
    1. Creates FailureContext from input
    2. Evaluates using RecoveryEvaluationEngine (L4 domain decisions)
    3. Calls L5 RecoveryExecutor to execute the decision
    4. Emits decision record (L4 responsibility)
    5. Returns EvaluationOutcome

    This replaces the old evaluate_failure() in L5 recovery_evaluator.py.

    Args:
        failure_match_id: ID of the failure match record
        error_code: Error code
        error_message: Error message
        **kwargs: Additional context fields

    Returns:
        EvaluationOutcome with execution result

    Reference: PIN-257 Phase R-1 (L5→L4 Violation Fix)
    """
    # Import L5 executor (L4→L5 import is allowed)
    from app.worker.recovery_evaluator import (
        FailureEvent,
        RecoveryExecutor,
    )

    # Create context and event
    context = FailureContext(
        failure_match_id=failure_match_id,
        error_code=error_code,
        error_message=error_message,
        skill_id=kwargs.get("skill_id"),
        tenant_id=kwargs.get("tenant_id"),
        agent_id=kwargs.get("agent_id"),
        run_id=kwargs.get("run_id"),
        metadata=kwargs.get("metadata", {}),
    )

    event = FailureEvent(
        failure_match_id=failure_match_id,
        error_code=error_code,
        error_message=error_message,
        skill_id=kwargs.get("skill_id"),
        tenant_id=kwargs.get("tenant_id"),
        agent_id=kwargs.get("agent_id"),
        run_id=kwargs.get("run_id"),
        metadata=kwargs.get("metadata", {}),
    )

    # L4: Make domain decision
    engine = RecoveryEvaluationEngine()
    decision = engine.evaluate(context)

    # L5: Execute decision
    executor = RecoveryExecutor()
    outcome = await executor.execute_decision(event, decision)

    # L4: Emit decision record (L4 responsibility)
    engine.emit_decision_record(
        decision=decision,
        evaluated=outcome.error is None,
        triggered=outcome.auto_executed,
    )

    return outcome


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "FailureContext",
    "RecoveryDecision",
    "RecoveryEvaluationEngine",
    "evaluate_recovery",
    "evaluate_and_execute",
]
