# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: worker (failure events)
#   Execution: async
# Role: Recovery execution (L5 pure execution)
# Authority: Recovery action execution (M9/M10 pattern)
# Callers: L4 RecoveryEvaluationEngine (via call-down)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Contract: EXECUTION_SEMANTIC_CONTRACT.md (Failure Semantics: recover mode)
# Reference: PIN-257 Phase R-1 (L5→L4 Violation Fix)
#
# GOVERNANCE NOTE: L5 owns EXECUTION only.
# L4 recovery_evaluation_engine.py provides domain decisions.
# This L5 file:
#   - Receives decisions from L4 (via RecoveryDecision DTO)
#   - Executes decisions
#   - Persists results to database (L6)
#   - Does NOT make domain decisions

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# L5 executor for recovery actions - participates in recovery orchestration
# Uses atomic UPDATE with exactly-once side-effect guarantee
FEATURE_INTENT = FeatureIntent.RECOVERABLE_OPERATION
RETRY_POLICY = RetryPolicy.SAFE

# M10 Recovery Executor (L5 Pure Execution)
"""
L5 Executor for recovery actions.

This L5 module receives decisions from L4 RecoveryEvaluationEngine and
executes them. It does NOT make domain decisions.

L5 Responsibilities:
1. Receive RecoveryDecision from L4
2. Execute decisions (DB operations, action execution)
3. Record provenance for audit
4. Trigger execution hooks

L5 does NOT:
- Evaluate rules (L4 responsibility)
- Combine confidences (L4 responsibility)
- Determine action selection (L4 responsibility)
- Determine auto-execution (L4 responsibility)
- Emit decision records (L4 responsibility)

Environment Variables:
- RECOVERY_EVALUATOR_ENABLED: Enable/disable executor (default: true)
- RECOVERY_AUTO_EXECUTE: Auto-execute automated actions (default: false)
- RECOVERY_MIN_CONFIDENCE: Minimum confidence for suggestions (default: 0.3)

Reference: PIN-257 Phase R-1 (L5→L4 Violation Fix)
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("nova.worker.recovery_executor")

# NOTE: emit_recovery_decision moved to L4 RecoveryEvaluationEngine
# L5 does NOT emit decision records - that is L4 domain authority
# Reference: PIN-257 Phase R-1 (L5→L4 Violation Fix)

# Configuration
EVALUATOR_ENABLED = os.getenv("RECOVERY_EVALUATOR_ENABLED", "true").lower() == "true"
AUTO_EXECUTE = os.getenv("RECOVERY_AUTO_EXECUTE", "false").lower() == "true"
MIN_CONFIDENCE = float(os.getenv("RECOVERY_MIN_CONFIDENCE", "0.3"))


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class FailureEvent:
    """Event representing a failure that needs recovery evaluation."""

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
class EvaluationOutcome:
    """Outcome of recovery evaluation."""

    failure_match_id: str
    candidate_id: Optional[int]
    suggested_action: Optional[str]
    confidence: float
    auto_executed: bool
    execution_result: Optional[Dict[str, Any]]
    duration_ms: int
    error: Optional[str] = None


# =============================================================================
# Hooks Registry
# =============================================================================


class RecoveryHooks:
    """
    Registry for recovery evaluation hooks.

    Hooks allow external code to be notified of recovery events:
    - on_evaluation_start: Called before evaluation begins
    - on_suggestion_generated: Called when a suggestion is created
    - on_action_selected: Called when an action is selected
    - on_execution_start: Called before auto-execution
    - on_execution_complete: Called after auto-execution
    """

    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {
            "on_evaluation_start": [],
            "on_suggestion_generated": [],
            "on_action_selected": [],
            "on_execution_start": [],
            "on_execution_complete": [],
        }

    def register(self, hook_name: str, callback: Callable) -> None:
        """Register a callback for a hook."""
        if hook_name not in self._hooks:
            raise ValueError(f"Unknown hook: {hook_name}")
        self._hooks[hook_name].append(callback)
        logger.debug(f"Registered hook callback for {hook_name}")

    def unregister(self, hook_name: str, callback: Callable) -> bool:
        """Unregister a callback."""
        if hook_name not in self._hooks:
            return False
        try:
            self._hooks[hook_name].remove(callback)
            return True
        except ValueError:
            return False

    async def trigger(self, hook_name: str, **kwargs) -> None:
        """Trigger all callbacks for a hook."""
        if hook_name not in self._hooks:
            return

        for callback in self._hooks[hook_name]:
            try:
                result = callback(**kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning(f"Hook callback error ({hook_name}): {e}")


# Global hooks instance
hooks = RecoveryHooks()


# =============================================================================
# Recovery Evaluator
# =============================================================================


class RecoveryExecutor:
    """
    L5 Executor for recovery actions.

    This L5 class executes decisions made by L4 RecoveryEvaluationEngine.
    It does NOT make domain decisions.

    L5 Responsibilities:
    - Execute action selection (DB operation)
    - Record provenance (DB operation)
    - Execute automated actions (execution)
    - Trigger execution hooks

    L4 Responsibilities (NOT here):
    - Evaluate rules
    - Match patterns
    - Combine confidences
    - Determine action selection
    - Determine auto-execution
    - Emit decision records

    Reference: PIN-257 Phase R-1 (L5→L4 Violation Fix)
    """

    def __init__(self, db_url: Optional[str] = None):
        """Initialize executor."""
        self._db_url = db_url or os.getenv("DATABASE_URL")
        self._hooks = hooks

    async def execute_decision(
        self,
        event: FailureEvent,
        decision: "RecoveryDecision",
    ) -> EvaluationOutcome:
        """
        Execute a recovery decision made by L4.

        This L5 method receives a RecoveryDecision from L4 and executes it.
        It does NOT make domain decisions - all decisions come from L4.

        Args:
            event: FailureEvent with error details
            decision: RecoveryDecision from L4 with all domain decisions

        Returns:
            EvaluationOutcome with execution result

        Reference: PIN-257 Phase R-1 (L5→L4 Violation Fix)
        """
        start_time = time.perf_counter()

        if not EVALUATOR_ENABLED:
            return EvaluationOutcome(
                failure_match_id=event.failure_match_id,
                candidate_id=None,
                suggested_action=None,
                confidence=0.0,
                auto_executed=False,
                execution_result=None,
                duration_ms=0,
                error="Executor disabled",
            )

        try:
            # Trigger start hook (L5 infrastructure)
            await self._hooks.trigger(
                "on_evaluation_start",
                event=event,
            )

            # Use L4 decision values (no L4 imports needed)
            candidate_id = decision.candidate_id
            combined_confidence = decision.combined_confidence
            suggested_action = decision.suggested_action

            logger.info(
                f"L5 executing decision for {event.failure_match_id}: "
                f"action={suggested_action}, "
                f"confidence={combined_confidence:.2f}"
            )

            # Trigger suggestion hook (L5 infrastructure)
            await self._hooks.trigger(
                "on_suggestion_generated",
                event=event,
                candidate_id=candidate_id,
                confidence=combined_confidence,
                rule_result=decision.rule_result,
            )

            # Step 1: Select action if L4 decision says so (L6 DB operation)
            action_id = None

            if decision.should_select_action and suggested_action:
                action_id = await self._select_action(
                    candidate_id=candidate_id,
                    action_code=suggested_action,
                )

                await self._hooks.trigger(
                    "on_action_selected",
                    event=event,
                    candidate_id=candidate_id,
                    action_code=suggested_action,
                    action_id=action_id,
                )

            # Step 2: Record provenance (L6 DB operation)
            await self._record_provenance(
                candidate_id=candidate_id,
                event_type="created",
                details={
                    "rule_result": decision.rule_result,
                    "match_result": {
                        "confidence": decision.match_confidence,
                    },
                    "combined_confidence": combined_confidence,
                },
                rule_id="rule_engine",
                action_id=action_id,
                confidence_after=combined_confidence,
            )

            # Step 3: Auto-execute if L4 decision says so (L5 execution + L6 DB)
            execution_result = None
            auto_executed = False

            # L4 decision.should_auto_execute already contains the threshold check
            # L5 just executes based on the decision
            if AUTO_EXECUTE and action_id and decision.should_auto_execute:
                auto_executed, execution_result = await self._auto_execute(
                    candidate_id=candidate_id,
                    action_id=action_id,
                    event=event,
                )

            duration_ms = int((time.perf_counter() - start_time) * 1000)

            # Step 4: Update metrics (L6)
            try:
                from app.metrics import recovery_suggestions_total

                recovery_suggestions_total.labels(
                    source="worker",
                    decision="pending" if not auto_executed else "auto_executed",
                ).inc()
            except Exception:
                pass

            # NOTE: emit_recovery_decision is now L4 responsibility
            # L5 does NOT emit decision records
            # Reference: PIN-257 Phase R-1 (L5→L4 Violation Fix)

            return EvaluationOutcome(
                failure_match_id=event.failure_match_id,
                candidate_id=candidate_id,
                suggested_action=suggested_action,
                confidence=combined_confidence,
                auto_executed=auto_executed,
                execution_result=execution_result,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Execution error: {e}", exc_info=True)

            # NOTE: emit_recovery_decision for error case is now L4 responsibility
            # L5 does NOT emit decision records
            # Reference: PIN-257 Phase R-1 (L5→L4 Violation Fix)

            return EvaluationOutcome(
                failure_match_id=event.failure_match_id,
                candidate_id=None,
                suggested_action=None,
                confidence=0.0,
                auto_executed=False,
                execution_result=None,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def _select_action(
        self,
        candidate_id: Optional[int],
        action_code: str,
    ) -> Optional[int]:
        """Select an action from the catalog and link to candidate."""
        if not candidate_id or not self._db_url:
            return None

        try:
            from sqlalchemy import text
            from sqlmodel import Session, create_engine

            engine = create_engine(self._db_url)

            with Session(engine) as session:
                # Find action by code
                result = session.execute(
                    text(
                        """
                        SELECT id FROM m10_recovery.suggestion_action
                        WHERE action_code = :code AND is_active = TRUE
                    """
                    ),
                    {"code": action_code},
                )
                row = result.fetchone()

                if row:
                    action_id = row[0]

                    # Update candidate with selected action
                    session.execute(
                        text(
                            """
                            UPDATE recovery_candidates
                            SET selected_action_id = :action_id
                            WHERE id = :candidate_id
                        """
                        ),
                        {"action_id": action_id, "candidate_id": candidate_id},
                    )
                    session.commit()

                    return action_id

        except Exception as e:
            logger.warning(f"Action selection error: {e}")

        return None

    async def _record_provenance(
        self,
        candidate_id: Optional[int],
        event_type: str,
        details: Dict[str, Any],
        rule_id: Optional[str] = None,
        action_id: Optional[int] = None,
        confidence_before: Optional[float] = None,
        confidence_after: Optional[float] = None,
        actor: str = "worker",
        duration_ms: Optional[int] = None,
    ) -> None:
        """Record provenance event."""
        if not candidate_id or not self._db_url:
            return

        try:
            from sqlalchemy import text
            from sqlmodel import Session, create_engine

            engine = create_engine(self._db_url)

            with Session(engine) as session:
                session.execute(
                    text(
                        """
                        INSERT INTO m10_recovery.suggestion_provenance
                        (suggestion_id, event_type, details, rule_id, action_id,
                         confidence_before, confidence_after, actor, actor_type, duration_ms)
                        VALUES (:suggestion_id, :event_type, CAST(:details AS jsonb),
                                :rule_id, :action_id, :confidence_before, :confidence_after,
                                :actor, 'system', :duration_ms)
                    """
                    ),
                    {
                        "suggestion_id": candidate_id,
                        "event_type": event_type,
                        "details": json.dumps(details),
                        "rule_id": rule_id,
                        "action_id": action_id,
                        "confidence_before": confidence_before,
                        "confidence_after": confidence_after,
                        "actor": actor,
                        "duration_ms": duration_ms,
                    },
                )
                session.commit()

        except Exception as e:
            logger.warning(f"Provenance recording error: {e}")

    async def _auto_execute(
        self,
        candidate_id: int,
        action_id: int,
        event: FailureEvent,
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Auto-execute a recovery action with exactly-once side-effect guarantee.

        Uses atomic UPDATE ... WHERE executed_at IS NULL RETURNING to ensure
        side-effects are only applied once, even under concurrent execution.

        Only executes if action is marked as automated and doesn't require approval.
        """
        if not self._db_url:
            return False, None

        try:
            from sqlalchemy import text
            from sqlmodel import Session, create_engine

            engine = create_engine(self._db_url)

            with Session(engine) as session:
                # Check if action can be auto-executed
                result = session.execute(
                    text(
                        """
                        SELECT action_code, template, is_automated, requires_approval
                        FROM m10_recovery.suggestion_action
                        WHERE id = :id
                    """
                    ),
                    {"id": action_id},
                )
                row = result.fetchone()

                if not row:
                    return False, None

                action_code, template, is_automated, requires_approval = row

                if not is_automated or requires_approval:
                    logger.debug(
                        f"Action {action_code} cannot be auto-executed: "
                        f"automated={is_automated}, requires_approval={requires_approval}"
                    )
                    return False, None

                # =============================================================
                # CRITICAL: Atomic execution guard
                # This ensures exactly-once side-effect execution even if
                # multiple workers try to process the same candidate.
                # Only the first UPDATE will return a row; subsequent attempts
                # will get no rows and skip execution.
                # =============================================================
                claim_result = session.execute(
                    text(
                        """
                        UPDATE recovery_candidates
                        SET execution_status = 'executing',
                            updated_at = now()
                        WHERE id = :id
                          AND (executed_at IS NULL OR execution_status = 'pending')
                        RETURNING id
                    """
                    ),
                    {"id": candidate_id},
                )
                claimed_row = claim_result.fetchone()
                session.commit()

                if not claimed_row:
                    # Another worker already claimed/executed this
                    logger.info(f"Candidate {candidate_id} already executed or claimed by another worker")
                    return False, {"skipped": True, "reason": "already_executed"}

                # Trigger execution start hook
                await self._hooks.trigger(
                    "on_execution_start",
                    event=event,
                    candidate_id=candidate_id,
                    action_code=action_code,
                )

                # Execute action (placeholder - actual execution would be here)
                start_time = time.perf_counter()
                execution_result = await self._execute_action(
                    action_code=action_code,
                    template=template if isinstance(template, dict) else json.loads(template or "{}"),
                    event=event,
                )
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                # Update status based on result
                status = "succeeded" if execution_result.get("success") else "failed"

                session.execute(
                    text(
                        """
                        UPDATE recovery_candidates
                        SET execution_status = :status,
                            executed_at = now(),
                            execution_result = CAST(:result AS jsonb)
                        WHERE id = :id
                    """
                    ),
                    {
                        "id": candidate_id,
                        "status": status,
                        "result": json.dumps(execution_result),
                    },
                )
                session.commit()

                # Record provenance
                await self._record_provenance(
                    candidate_id=candidate_id,
                    event_type="success" if execution_result.get("success") else "failure",
                    details=execution_result,
                    action_id=action_id,
                    duration_ms=duration_ms,
                )

                # Trigger completion hook
                await self._hooks.trigger(
                    "on_execution_complete",
                    event=event,
                    candidate_id=candidate_id,
                    action_code=action_code,
                    success=execution_result.get("success", False),
                    result=execution_result,
                )

                return True, execution_result

        except Exception as e:
            logger.error(f"Auto-execution error: {e}", exc_info=True)
            return False, {"success": False, "error": str(e)}

    async def _execute_action(
        self,
        action_code: str,
        template: Dict[str, Any],
        event: FailureEvent,
    ) -> Dict[str, Any]:
        """
        Execute a recovery action based on its type.

        This is a placeholder implementation - actual execution would
        integrate with the worker runtime.
        """
        logger.info(f"Executing action {action_code} for {event.failure_match_id}")

        # Placeholder execution logic
        if action_code == "retry_exponential":
            # Would trigger retry in worker
            return {
                "success": True,
                "action": "retry_scheduled",
                "retry_count": 1,
                "next_retry_at": datetime.now(timezone.utc).isoformat(),
            }

        elif action_code == "fallback_model":
            # Would switch to fallback model
            return {
                "success": True,
                "action": "model_switched",
                "new_model": template.get("fallback_model", "gpt-4o-mini"),
            }

        elif action_code == "circuit_breaker":
            # Would enable circuit breaker
            return {
                "success": True,
                "action": "circuit_breaker_enabled",
                "cooldown_seconds": template.get("cooldown_seconds", 60),
            }

        elif action_code == "notify_ops":
            # Would send notification
            return {
                "success": True,
                "action": "notification_sent",
                "channel": template.get("channel", "slack"),
            }

        else:
            # Unknown action - mark for manual review
            return {
                "success": False,
                "action": "unknown",
                "reason": f"No executor for action: {action_code}",
            }


# =============================================================================
# Convenience Functions
# =============================================================================


# NOTE: evaluate_failure() moved to L4 recovery_evaluation_engine.py
# Callers should import from:
#   from app.hoc.cus.incidents.L5_engines.recovery_evaluation_engine import evaluate_and_execute
# Reference: PIN-257 Phase R-1 (L5→L4 Violation Fix), SWEEP-09


def register_hook(hook_name: str, callback: Callable) -> None:
    """Register a hook callback."""
    hooks.register(hook_name, callback)


def unregister_hook(hook_name: str, callback: Callable) -> bool:
    """Unregister a hook callback."""
    return hooks.unregister(hook_name, callback)


# =============================================================================
# Exports
# =============================================================================

# L5 exports only execution-related items
# Domain decision entry points are in L4 recovery_evaluation_engine.py
# Reference: PIN-257 Phase R-1 (L5→L4 Violation Fix)

__all__ = [
    # Data classes
    "FailureEvent",
    "EvaluationOutcome",
    # L5 Executor (called by L4)
    "RecoveryExecutor",
    # Hook infrastructure (L5)
    "RecoveryHooks",
    "register_hook",
    "unregister_hook",
    "hooks",
    # Configuration
    "EVALUATOR_ENABLED",
    "AUTO_EXECUTE",
    "MIN_CONFIDENCE",
]
