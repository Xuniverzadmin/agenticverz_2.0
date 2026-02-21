# capability_id: CAP-009
# Layer: L6 — Driver
# Product: system-wide
# Wiring Type: runner-hook
# Parent Gap: GAP-016 (StepEnforcement)
# Reference: GAP-140
# Temporal:
#   Trigger: worker (after step completion)
#   Execution: async
# Role: Wire StepEnforcement to event bus for policy evaluation
# Callers: app/worker/runner.py (after step completion)
# Allowed Imports: L4 (StepEnforcement), L6 (events)
# Forbidden Imports: L1, L2, L3

"""
Module: step_enforcement_hook
Purpose: Wire StepEnforcement to event bus for policy evaluation.

Wires:
    - Source: app/worker/enforcement/step_enforcement.py
    - Target: app/events (event bus)

This hook provides:
    1. Event emission after step enforcement
    2. Policy evaluation results publication
    3. Audit trail for enforcement decisions

The hook bridges the step enforcement logic with the event system,
allowing downstream consumers to react to policy decisions.

Acceptance Criteria:
    - AC-140-01: Events emitted after enforcement
    - AC-140-02: Policy decisions included in events
    - AC-140-03: Halt decisions trigger special events
    - AC-140-04: Events include execution context
    - AC-140-05: Hook is imported in runner.py
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.execution_context import ExecutionContext

logger = logging.getLogger("nova.worker.hooks.step_enforcement_hook")


@dataclass
class StepEnforcementEvent:
    """
    Event payload for step enforcement outcomes.

    This event is published to the event bus after each step enforcement.
    """

    run_id: str
    step_index: int
    policy_checked: bool
    should_halt: bool
    halt_reason: Optional[str] = None
    policy_id: Optional[str] = None
    message: Optional[str] = None
    step_cost_cents: int = 0
    step_tokens: int = 0
    tenant_id: Optional[str] = None
    trace_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event payload."""
        return {
            "run_id": self.run_id,
            "step_index": self.step_index,
            "policy_checked": self.policy_checked,
            "should_halt": self.should_halt,
            "halt_reason": self.halt_reason,
            "policy_id": self.policy_id,
            "message": self.message,
            "step_cost_cents": self.step_cost_cents,
            "step_tokens": self.step_tokens,
            "tenant_id": self.tenant_id,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_enforcement_result(
        cls,
        run_id: str,
        step_index: int,
        enforcement_result: Any,
        step_cost_cents: int = 0,
        step_tokens: int = 0,
        execution_context: Optional[ExecutionContext] = None,
    ) -> "StepEnforcementEvent":
        """Create event from enforcement result."""
        return cls(
            run_id=run_id,
            step_index=step_index,
            policy_checked=True,
            should_halt=getattr(enforcement_result, "should_halt", False),
            halt_reason=getattr(enforcement_result, "halt_reason", None),
            policy_id=getattr(enforcement_result, "policy_id", None),
            message=getattr(enforcement_result, "message", None),
            step_cost_cents=step_cost_cents,
            step_tokens=step_tokens,
            tenant_id=execution_context.tenant_id if execution_context else None,
            trace_id=execution_context.trace_id if execution_context else None,
        )


class StepEnforcementHook:
    """
    Runner hook for step enforcement event emission.

    This hook integrates step enforcement with the event bus,
    allowing downstream consumers to react to policy decisions.

    Usage in runner:
        hook = get_step_enforcement_hook()

        # After step enforcement
        await hook.after_enforcement(
            execution_context=cursor.context,
            step_index=step_index,
            enforcement_result=enforcement_result,
            step_cost_cents=cost,
            step_tokens=tokens,
        )
    """

    def __init__(self, publisher: Optional[Any] = None):
        """
        Initialize StepEnforcementHook.

        Args:
            publisher: Event publisher (lazy loaded if None)
        """
        self._publisher = publisher

    async def after_enforcement(
        self,
        run_id: str,
        step_index: int,
        enforcement_result: Any,
        step_cost_cents: int = 0,
        step_tokens: int = 0,
        execution_context: Optional[ExecutionContext] = None,
    ) -> StepEnforcementEvent:
        """
        Emit event after step enforcement.

        Args:
            run_id: Run identifier
            step_index: Step index in the plan
            enforcement_result: Result from step enforcement
            step_cost_cents: Step cost in cents
            step_tokens: Step token usage
            execution_context: Optional execution context

        Returns:
            StepEnforcementEvent that was emitted
        """
        event = StepEnforcementEvent.from_enforcement_result(
            run_id=run_id,
            step_index=step_index,
            enforcement_result=enforcement_result,
            step_cost_cents=step_cost_cents,
            step_tokens=step_tokens,
            execution_context=execution_context,
        )

        logger.debug(
            "step_enforcement_hook.emitting",
            extra={
                "run_id": run_id,
                "step_index": step_index,
                "should_halt": event.should_halt,
            },
        )

        try:
            publisher = self._get_publisher()
            if publisher is None:
                logger.warning(
                    "step_enforcement_hook.no_publisher",
                    extra={"run_id": run_id},
                )
                return event

            # Choose event type based on outcome
            if event.should_halt:
                event_type = "step.enforcement.halted"
            else:
                event_type = "step.enforcement.passed"

            await publisher.publish(event_type, event.to_dict())

            logger.info(
                "step_enforcement_hook.emitted",
                extra={
                    "run_id": run_id,
                    "step_index": step_index,
                    "event_type": event_type,
                    "should_halt": event.should_halt,
                },
            )

        except Exception as e:
            # Don't fail on event emission errors
            logger.warning(
                "step_enforcement_hook.emission_failed",
                extra={
                    "run_id": run_id,
                    "step_index": step_index,
                    "error": str(e),
                },
            )

        return event

    async def emit_enforcement_skipped(
        self,
        run_id: str,
        step_index: int,
        reason: str,
        execution_context: Optional[ExecutionContext] = None,
    ) -> None:
        """
        Emit event when enforcement is skipped.

        This is used for audit purposes when enforcement
        cannot be performed (e.g., missing policy engine).

        Args:
            run_id: Run identifier
            step_index: Step index in the plan
            reason: Reason enforcement was skipped
            execution_context: Optional execution context
        """
        event = StepEnforcementEvent(
            run_id=run_id,
            step_index=step_index,
            policy_checked=False,
            should_halt=False,
            message=f"Enforcement skipped: {reason}",
            tenant_id=execution_context.tenant_id if execution_context else None,
            trace_id=execution_context.trace_id if execution_context else None,
        )

        try:
            publisher = self._get_publisher()
            if publisher is not None:
                await publisher.publish("step.enforcement.skipped", event.to_dict())

            logger.info(
                "step_enforcement_hook.skipped",
                extra={
                    "run_id": run_id,
                    "step_index": step_index,
                    "reason": reason,
                },
            )

        except Exception as e:
            logger.warning(
                "step_enforcement_hook.skip_emission_failed",
                extra={
                    "run_id": run_id,
                    "step_index": step_index,
                    "error": str(e),
                },
            )

    def _get_publisher(self) -> Optional[Any]:
        """Get event publisher (lazy initialization)."""
        if self._publisher is not None:
            return self._publisher

        try:
            from app.events import get_publisher
            return get_publisher()
        except ImportError:
            logger.debug("step_enforcement_hook.publisher_not_available")
            return None


# =========================
# Singleton Management
# =========================

_step_enforcement_hook: Optional[StepEnforcementHook] = None


def get_step_enforcement_hook() -> StepEnforcementHook:
    """
    Get or create the singleton StepEnforcementHook.

    Returns:
        StepEnforcementHook instance
    """
    global _step_enforcement_hook

    if _step_enforcement_hook is None:
        _step_enforcement_hook = StepEnforcementHook()
        logger.info("step_enforcement_hook.created")

    return _step_enforcement_hook


def configure_step_enforcement_hook(
    publisher: Optional[Any] = None,
) -> StepEnforcementHook:
    """
    Configure the singleton StepEnforcementHook with dependencies.

    Args:
        publisher: Event publisher to use

    Returns:
        Configured StepEnforcementHook
    """
    global _step_enforcement_hook

    _step_enforcement_hook = StepEnforcementHook(publisher=publisher)

    logger.info(
        "step_enforcement_hook.configured",
        extra={"has_publisher": publisher is not None},
    )

    return _step_enforcement_hook


def reset_step_enforcement_hook() -> None:
    """Reset the singleton (for testing)."""
    global _step_enforcement_hook
    _step_enforcement_hook = None
