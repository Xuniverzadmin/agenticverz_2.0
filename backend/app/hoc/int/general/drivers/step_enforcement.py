# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: worker (during step execution)
#   Execution: sync (must complete before step returns)
# Role: Guarantee enforcement happens within same step
# Callers: runner.py step execution loop
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-016, PIN-524

"""
Module: step_enforcement
Purpose: Ensures STOP/KILL actions halt execution within the same step.

Imports (Dependencies):
    - app.hoc.cus.hoc_spine.authority.runtime_switch: is_governance_active
    - app.hoc.cus.policies.L5_engines.prevention_engine: get_prevention_engine
    - app.hoc.cus.policies.L6_drivers.policy_enforcement_write_driver: record_enforcement_standalone

Exports (Provides):
    - enforce_before_step_completion(ctx, step_result) -> EnforcementResult
    - StepEnforcementError: Raised when enforcement requires halt

Wiring Points:
    - Called from: runner.py BEFORE returning step result
    - Halts: Step execution if STOP/KILL triggered
    - Records: Enforcement outcomes to policy_enforcements table (PIN-524)

Critical Invariant:
    Enforcement check MUST happen BEFORE step result is returned.
    If enforcement says STOP, the step is marked as enforcement-halted.

Centralization Warning (GPT Review):
    Step-level enforcement MUST be centralized in a SINGLE choke point.
    DO NOT scatter "before completion" checks across multiple locations.
    One misplaced await breaks enforcement. All step completion MUST flow
    through enforce_before_step_completion() — no exceptions.

Acceptance Criteria:
    - [x] AC-016-01: Enforcement runs before step completion
    - [x] AC-016-02: STOP/KILL actions halt within same step
    - [x] AC-016-03: Enforcement result logged
    - [x] AC-016-04: No orphan — wired to runner.py
    - [x] AC-016-05: Enforcement outcomes recorded to DB (PIN-524)
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger("nova.worker.enforcement.step_enforcement")


class EnforcementHaltReason(str, Enum):
    """Reasons for halting step execution."""
    POLICY_STOP = "policy_stop"
    POLICY_KILL = "policy_kill"
    BUDGET_EXCEEDED = "budget_exceeded"
    RATE_LIMITED = "rate_limited"
    GOVERNANCE_DISABLED = "governance_disabled"
    DEGRADED_MODE = "degraded_mode"


@dataclass
class EnforcementResult:
    """Result of step enforcement check."""
    should_halt: bool
    halt_reason: Optional[EnforcementHaltReason]
    policy_id: Optional[str]
    message: str
    checked_at: str


class StepEnforcementError(Exception):
    """Raised when enforcement requires immediate halt."""
    def __init__(self, result: EnforcementResult):
        self.result = result
        super().__init__(f"Enforcement halt: {result.halt_reason} - {result.message}")


def _record_enforcement_outcome(
    tenant_id: Optional[str],
    rule_id: Optional[str],
    run_id: Optional[str],
    action_taken: str,
    halt_reason: str,
    details: Dict[str, Any],
) -> None:
    """
    Record enforcement outcome to the policy_enforcements table.

    This is a fire-and-forget operation. Recording failures are logged
    but do not affect enforcement behavior.

    PIN-524: Enforcement outcomes must be recorded for audit trail.
    """
    if not tenant_id or not rule_id:
        logger.debug(
            "step_enforcement.record_skipped",
            extra={"reason": "missing tenant_id or rule_id"},
        )
        return

    try:
        from app.hoc.cus.policies.L6_drivers.policy_enforcement_write_driver import (
            record_enforcement_standalone,
        )

        # Run async recording in a new event loop (sync context)
        try:
            loop = asyncio.get_running_loop()
            # Already in async context - schedule as task
            loop.create_task(
                record_enforcement_standalone(
                    tenant_id=tenant_id,
                    rule_id=rule_id,
                    action_taken=action_taken,
                    run_id=run_id,
                    details={
                        "halt_reason": halt_reason,
                        **details,
                    },
                )
            )
        except RuntimeError:
            # No running loop - use asyncio.run
            asyncio.run(
                record_enforcement_standalone(
                    tenant_id=tenant_id,
                    rule_id=rule_id,
                    action_taken=action_taken,
                    run_id=run_id,
                    details={
                        "halt_reason": halt_reason,
                        **details,
                    },
                )
            )

        logger.debug(
            "step_enforcement.record_initiated",
            extra={
                "tenant_id": tenant_id,
                "rule_id": rule_id,
                "action_taken": action_taken,
            },
        )

    except ImportError:
        logger.warning("step_enforcement.write_driver_unavailable")
    except Exception as e:
        # Recording must never block enforcement
        logger.error(
            "step_enforcement.record_failed",
            extra={"error": str(e)},
        )


def enforce_before_step_completion(
    run_context: Any,
    step_result: Any,
    prevention_engine: Optional[Any] = None,
) -> EnforcementResult:
    """
    Enforce policies before step completion.

    This is the SINGLE CHOKE POINT for step-level enforcement.
    All step completions MUST flow through this function.

    Args:
        run_context: Current run context with tenant_id, run_id, etc.
        step_result: Result of the step execution
        prevention_engine: Optional prevention engine instance

    Returns:
        EnforcementResult with enforcement decision

    Raises:
        StepEnforcementError: If enforcement requires immediate halt
    """
    checked_at = datetime.now(timezone.utc).isoformat()

    # Check governance state first (GAP-069)
    try:
        # V2.0.0 - hoc_spine authority
        from app.hoc.cus.hoc_spine.authority.runtime_switch import is_governance_active, is_degraded_mode

        if not is_governance_active():
            logger.warning("step_enforcement.governance_disabled", extra={
                "run_id": getattr(run_context, 'run_id', 'unknown'),
            })
            return EnforcementResult(
                should_halt=False,
                halt_reason=None,
                policy_id=None,
                message="Governance disabled - enforcement bypassed",
                checked_at=checked_at,
            )

        if is_degraded_mode():
            logger.warning("step_enforcement.degraded_mode", extra={
                "run_id": getattr(run_context, 'run_id', 'unknown'),
            })
            # In degraded mode, log warning but don't halt existing runs
            # New runs are blocked at accept_new_run level
    except ImportError:
        # Runtime switch not available - continue with enforcement
        pass

    # Get or create prevention engine
    if prevention_engine is None:
        try:
            from app.hoc.cus.policies.L5_engines.prevention_engine import get_prevention_engine
            prevention_engine = get_prevention_engine()
        except ImportError:
            # Prevention engine not available - allow through
            logger.warning("step_enforcement.prevention_engine_unavailable")
            return EnforcementResult(
                should_halt=False,
                halt_reason=None,
                policy_id=None,
                message="Prevention engine unavailable",
                checked_at=checked_at,
            )

    # Evaluate policies
    try:
        # Build evaluation context from run_context and step_result
        eval_context = _build_eval_context(run_context, step_result)

        # Call prevention engine
        if hasattr(prevention_engine, 'evaluate_step'):
            decision = prevention_engine.evaluate_step(eval_context)
        elif hasattr(prevention_engine, 'evaluate'):
            decision = prevention_engine.evaluate(eval_context)
        else:
            # No evaluation method available
            return EnforcementResult(
                should_halt=False,
                halt_reason=None,
                policy_id=None,
                message="No evaluation method available",
                checked_at=checked_at,
            )

        # Check decision action
        action = getattr(decision, 'action', None) or decision.get('action', 'CONTINUE')
        policy_id = getattr(decision, 'policy_id', None) or decision.get('policy_id', None)

        action_upper = action.upper() if isinstance(action, str) else 'CONTINUE'

        if action_upper in ('STOP', 'KILL', 'ABORT', 'BLOCK'):
            halt_reason = (
                EnforcementHaltReason.POLICY_KILL if action_upper in ('KILL', 'ABORT')
                else EnforcementHaltReason.POLICY_STOP
            )

            result = EnforcementResult(
                should_halt=True,
                halt_reason=halt_reason,
                policy_id=policy_id,
                message=f"Policy {policy_id} triggered {action_upper}",
                checked_at=checked_at,
            )

            logger.info("step_enforcement.halt_triggered", extra={
                "run_id": getattr(run_context, 'run_id', 'unknown'),
                "action": action_upper,
                "policy_id": policy_id,
                "halt_reason": halt_reason.value,
            })

            # PIN-524: Record enforcement outcome to DB
            _record_enforcement_outcome(
                tenant_id=getattr(run_context, 'tenant_id', None),
                rule_id=policy_id,
                run_id=getattr(run_context, 'run_id', None),
                action_taken=action_upper,
                halt_reason=halt_reason.value,
                details={
                    "step_index": getattr(run_context, 'step_index', 0),
                    "checked_at": checked_at,
                },
            )

            # Raise error to halt step
            raise StepEnforcementError(result)

        # No halt required
        return EnforcementResult(
            should_halt=False,
            halt_reason=None,
            policy_id=policy_id,
            message=f"Policy evaluation result: {action_upper}",
            checked_at=checked_at,
        )

    except StepEnforcementError:
        # Re-raise enforcement errors
        raise
    except Exception as e:
        logger.error("step_enforcement.evaluation_error", extra={
            "run_id": getattr(run_context, 'run_id', 'unknown'),
            "error": str(e),
        })
        # Fail-closed: halt on error (GAP-035)
        result = EnforcementResult(
            should_halt=True,
            halt_reason=EnforcementHaltReason.POLICY_STOP,
            policy_id=None,
            message=f"Enforcement evaluation error (fail-closed): {e}",
            checked_at=checked_at,
        )
        raise StepEnforcementError(result)


def _build_eval_context(run_context: Any, step_result: Any) -> Dict[str, Any]:
    """Build evaluation context for prevention engine."""
    return {
        "run_id": getattr(run_context, 'run_id', None),
        "tenant_id": getattr(run_context, 'tenant_id', None),
        "step_index": getattr(run_context, 'step_index', 0),
        "step_result": step_result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
