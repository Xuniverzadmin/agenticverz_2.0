# capability_id: CAP-009
# Layer: L6 — Driver
# AUDIENCE: INTERNAL
# Role: Enforce usage limits and monitor health in runner
# PHASE: W0
# Product: system-wide
# Wiring Type: runner-hook
# Parent Gap: GAP-053 (UsageMonitor), GAP-054 (HealthMonitor), GAP-055 (LimitEnforcer)
# Reference: GAP-139
# Temporal:
#   Trigger: worker (step loop)
#   Execution: async
# Callers: app/worker/runner.py (step loop)
# Allowed Imports: L4 (monitors, limits), L6
# Forbidden Imports: L1, L2, L3


"""
Module: limit_hook
Purpose: Enforce usage limits and monitor health in runner.

Wires:
    - Source: app/services/monitors/usage_monitor.py
    - Source: app/services/monitors/health_monitor.py
    - Source: app/services/limits/limit_enforcer.py
    - Target: app/worker/runner.py (step loop)

Enforcement Points:
    - Before step: Check limits, may block
    - After step: Record usage, update monitors

This hook ensures:
    1. Tenant limits are enforced before step execution
    2. Usage is recorded after each step
    3. Health metrics are updated for monitoring

Acceptance Criteria:
    - AC-139-01: Limits checked before each step
    - AC-139-02: Block decision halts execution
    - AC-139-03: Usage recorded after step
    - AC-139-04: Health metrics updated
    - AC-139-05: Hook is imported in runner.py
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from app.core.execution_context import ExecutionContext

logger = logging.getLogger("nova.worker.hooks.limit_hook")


class LimitDecision(str, Enum):
    """Decision outcomes for limit checks."""

    ALLOW = "allow"  # Proceed with execution
    WARN = "warn"  # Proceed but emit warning
    BLOCK = "block"  # Halt execution


class LimitType(str, Enum):
    """Types of limits that can be enforced."""

    COST = "cost"  # Cost/budget limit
    TOKEN = "token"  # Token usage limit
    RATE = "rate"  # Rate limit
    STEP = "step"  # Max steps per run
    TIME = "time"  # Execution time limit


@dataclass
class LimitCheckResult:
    """
    Result of a limit check.

    Contains the decision and context for enforcement.
    """

    decision: LimitDecision
    limit_type: Optional[str] = None
    current_usage: Optional[float] = None
    max_allowed: Optional[float] = None
    utilization_percent: Optional[float] = None
    message: Optional[str] = None
    policy_id: Optional[str] = None
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "decision": self.decision.value,
            "limit_type": self.limit_type,
            "current_usage": self.current_usage,
            "max_allowed": self.max_allowed,
            "utilization_percent": self.utilization_percent,
            "message": self.message,
            "policy_id": self.policy_id,
            "checked_at": self.checked_at,
        }

    @classmethod
    def allow(cls) -> "LimitCheckResult":
        """Create an allow result."""
        return cls(decision=LimitDecision.ALLOW)

    @classmethod
    def warn(
        cls,
        limit_type: str,
        current_usage: float,
        max_allowed: float,
        message: Optional[str] = None,
    ) -> "LimitCheckResult":
        """Create a warning result."""
        utilization = (current_usage / max_allowed * 100) if max_allowed > 0 else 0
        return cls(
            decision=LimitDecision.WARN,
            limit_type=limit_type,
            current_usage=current_usage,
            max_allowed=max_allowed,
            utilization_percent=utilization,
            message=message or f"Approaching {limit_type} limit: {utilization:.1f}% utilized",
        )

    @classmethod
    def block(
        cls,
        limit_type: str,
        current_usage: float,
        max_allowed: float,
        policy_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> "LimitCheckResult":
        """Create a block result."""
        return cls(
            decision=LimitDecision.BLOCK,
            limit_type=limit_type,
            current_usage=current_usage,
            max_allowed=max_allowed,
            utilization_percent=100.0,
            policy_id=policy_id,
            message=message or f"{limit_type.title()} limit exceeded: {current_usage} >= {max_allowed}",
        )


@dataclass
class UsageRecord:
    """Record of resource usage for a step."""

    tenant_id: str
    run_id: str
    step_index: int
    cost_cents: int = 0
    tokens_used: int = 0
    latency_ms: float = 0.0
    skill_name: Optional[str] = None
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "step_index": self.step_index,
            "cost_cents": self.cost_cents,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "skill_name": self.skill_name,
            "recorded_at": self.recorded_at,
        }


class LimitHook:
    """
    Runner hook for limit enforcement and usage monitoring.

    This hook integrates with:
    - LimitEnforcer: Pre-step limit checks
    - UsageMonitor: Post-step usage recording
    - HealthMonitor: System health tracking

    Usage in runner:
        hook = get_limit_hook()

        # Before step execution
        check_result = await hook.before_step(
            execution_context=cursor.context,
            estimated_cost=step_cost_estimate,
        )

        if check_result.decision == LimitDecision.BLOCK:
            return StepResult.blocked(
                reason="limit_exceeded",
                details=check_result.message,
            )

        # Execute step...

        # After step execution
        await hook.after_step(
            execution_context=cursor.context,
            actual_cost=step_cost,
            tokens_used=step_tokens,
            latency_ms=step_latency,
        )
    """

    # Warning threshold (percentage of limit)
    WARNING_THRESHOLD_PERCENT = 80.0

    def __init__(
        self,
        limit_enforcer: Optional[Any] = None,
        usage_monitor: Optional[Any] = None,
    ):
        """
        Initialize LimitHook.

        Args:
            limit_enforcer: LimitEnforcer instance (lazy loaded if None)
            usage_monitor: UsageMonitor instance (lazy loaded if None)
        """
        self._limit_enforcer = limit_enforcer
        self._usage_monitor = usage_monitor

    async def before_step(
        self,
        tenant_id: str,
        run_id: str,
        step_index: int,
        estimated_cost: float = 0.0,
        estimated_tokens: int = 0,
        execution_context: Optional[ExecutionContext] = None,
    ) -> LimitCheckResult:
        """
        Check limits before step execution.

        This method checks all applicable limits and returns the most
        restrictive decision (BLOCK > WARN > ALLOW).

        Args:
            tenant_id: Tenant identifier
            run_id: Run identifier
            step_index: Step index in the plan
            estimated_cost: Estimated cost in cents
            estimated_tokens: Estimated token usage
            execution_context: Optional execution context

        Returns:
            LimitCheckResult with ALLOW, WARN, or BLOCK decision.
        """
        logger.debug(
            "limit_hook.before_step",
            extra={
                "tenant_id": tenant_id,
                "run_id": run_id,
                "step_index": step_index,
                "estimated_cost": estimated_cost,
            },
        )

        try:
            # Try to get limit enforcer
            enforcer = self._get_limit_enforcer()
            if enforcer is None:
                # No enforcer configured - allow by default
                logger.debug(
                    "limit_hook.no_enforcer",
                    extra={"run_id": run_id, "action": "allow"},
                )
                return LimitCheckResult.allow()

            # Check cost limits
            cost_result = await self._check_cost_limit(
                enforcer, tenant_id, estimated_cost
            )
            if cost_result.decision == LimitDecision.BLOCK:
                return cost_result

            # Check token limits
            token_result = await self._check_token_limit(
                enforcer, tenant_id, estimated_tokens
            )
            if token_result.decision == LimitDecision.BLOCK:
                return token_result

            # Check rate limits
            rate_result = await self._check_rate_limit(enforcer, tenant_id, run_id)
            if rate_result.decision == LimitDecision.BLOCK:
                return rate_result

            # Return most restrictive non-block result
            for result in [cost_result, token_result, rate_result]:
                if result.decision == LimitDecision.WARN:
                    logger.info(
                        "limit_hook.warning",
                        extra={
                            "run_id": run_id,
                            "step_index": step_index,
                            **result.to_dict(),
                        },
                    )
                    return result

            return LimitCheckResult.allow()

        except Exception as e:
            # Fail-open: on error, allow execution but log warning
            logger.warning(
                "limit_hook.check_failed",
                extra={
                    "run_id": run_id,
                    "step_index": step_index,
                    "error": str(e),
                    "action": "allow_on_error",
                },
            )
            return LimitCheckResult.allow()

    async def after_step(
        self,
        tenant_id: str,
        run_id: str,
        step_index: int,
        actual_cost: int = 0,
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        skill_name: Optional[str] = None,
        execution_context: Optional[ExecutionContext] = None,
    ) -> UsageRecord:
        """
        Record usage after step execution.

        This method records the actual resource consumption and updates
        monitoring systems.

        Args:
            tenant_id: Tenant identifier
            run_id: Run identifier
            step_index: Step index in the plan
            actual_cost: Actual cost in cents
            tokens_used: Actual token usage
            latency_ms: Step execution latency
            skill_name: Name of the skill executed
            execution_context: Optional execution context

        Returns:
            UsageRecord with recorded metrics
        """
        record = UsageRecord(
            tenant_id=tenant_id,
            run_id=run_id,
            step_index=step_index,
            cost_cents=actual_cost,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            skill_name=skill_name,
        )

        logger.debug(
            "limit_hook.after_step",
            extra={
                "run_id": run_id,
                "step_index": step_index,
                "cost_cents": actual_cost,
                "tokens_used": tokens_used,
            },
        )

        try:
            monitor = self._get_usage_monitor()
            if monitor is not None:
                await monitor.record_usage(
                    tenant_id=tenant_id,
                    run_id=run_id,
                    step_index=step_index,
                    cost=actual_cost,
                    tokens=tokens_used,
                    latency_ms=latency_ms,
                )

                logger.debug(
                    "limit_hook.usage_recorded",
                    extra={"run_id": run_id, "step_index": step_index},
                )
            else:
                logger.debug(
                    "limit_hook.no_monitor",
                    extra={"run_id": run_id},
                )

        except Exception as e:
            # Don't fail on recording errors
            logger.warning(
                "limit_hook.record_failed",
                extra={
                    "run_id": run_id,
                    "step_index": step_index,
                    "error": str(e),
                },
            )

        return record

    async def _check_cost_limit(
        self,
        enforcer: Any,
        tenant_id: str,
        estimated_cost: float,
    ) -> LimitCheckResult:
        """Check cost/budget limits."""
        try:
            if not hasattr(enforcer, "check_cost_limit"):
                return LimitCheckResult.allow()

            result = await enforcer.check_cost_limit(
                tenant_id=tenant_id,
                estimated_cost=estimated_cost,
            )

            if result.exceeded:
                return LimitCheckResult.block(
                    limit_type=LimitType.COST.value,
                    current_usage=result.current_usage,
                    max_allowed=result.max_allowed,
                    policy_id=getattr(result, "policy_id", None),
                )

            if result.warning or (
                result.max_allowed > 0
                and result.current_usage / result.max_allowed * 100 >= self.WARNING_THRESHOLD_PERCENT
            ):
                return LimitCheckResult.warn(
                    limit_type=LimitType.COST.value,
                    current_usage=result.current_usage,
                    max_allowed=result.max_allowed,
                )

            return LimitCheckResult.allow()

        except AttributeError:
            return LimitCheckResult.allow()

    async def _check_token_limit(
        self,
        enforcer: Any,
        tenant_id: str,
        estimated_tokens: int,
    ) -> LimitCheckResult:
        """Check token usage limits."""
        try:
            if not hasattr(enforcer, "check_token_limit"):
                return LimitCheckResult.allow()

            result = await enforcer.check_token_limit(
                tenant_id=tenant_id,
                estimated_tokens=estimated_tokens,
            )

            if result.exceeded:
                return LimitCheckResult.block(
                    limit_type=LimitType.TOKEN.value,
                    current_usage=result.current_usage,
                    max_allowed=result.max_allowed,
                )

            return LimitCheckResult.allow()

        except AttributeError:
            return LimitCheckResult.allow()

    async def _check_rate_limit(
        self,
        enforcer: Any,
        tenant_id: str,
        run_id: str,
    ) -> LimitCheckResult:
        """Check rate limits."""
        try:
            if not hasattr(enforcer, "check_rate_limit"):
                return LimitCheckResult.allow()

            result = await enforcer.check_rate_limit(
                tenant_id=tenant_id,
                operation="step_execution",
            )

            if result.exceeded:
                return LimitCheckResult.block(
                    limit_type=LimitType.RATE.value,
                    current_usage=result.current_usage,
                    max_allowed=result.max_allowed,
                    message="Rate limit exceeded. Please retry later.",
                )

            return LimitCheckResult.allow()

        except AttributeError:
            return LimitCheckResult.allow()

    def _get_limit_enforcer(self) -> Optional[Any]:
        """Get limit enforcer (lazy initialization)."""
        if self._limit_enforcer is not None:
            return self._limit_enforcer

        try:
            # L5 engine import (migrated to HOC per SWEEP-03, GAP-055)
            from app.hoc.int.policies.L5_engines.limit_enforcer_contract import (
                get_limit_enforcer,
            )
            return get_limit_enforcer()
        except ImportError:
            logger.debug("limit_hook.limit_enforcer_not_available")
            return None

    def _get_usage_monitor(self) -> Optional[Any]:
        """Get usage monitor (lazy initialization)."""
        if self._usage_monitor is not None:
            return self._usage_monitor

        try:
            # L5 engine import (migrated to HOC per SWEEP-03, GAP-053)
            from app.hoc.int.policies.L5_engines.usage_monitor_contract import (
                get_usage_monitor,
            )
            return get_usage_monitor()
        except ImportError:
            logger.debug("limit_hook.usage_monitor_not_available")
            return None


# =========================
# Singleton Management
# =========================

_limit_hook: Optional[LimitHook] = None


def get_limit_hook() -> LimitHook:
    """
    Get or create the singleton LimitHook.

    Returns:
        LimitHook instance
    """
    global _limit_hook

    if _limit_hook is None:
        _limit_hook = LimitHook()
        logger.info("limit_hook.created")

    return _limit_hook


def configure_limit_hook(
    limit_enforcer: Optional[Any] = None,
    usage_monitor: Optional[Any] = None,
) -> LimitHook:
    """
    Configure the singleton LimitHook with dependencies.

    Args:
        limit_enforcer: LimitEnforcer instance to use
        usage_monitor: UsageMonitor instance to use

    Returns:
        Configured LimitHook
    """
    global _limit_hook

    _limit_hook = LimitHook(
        limit_enforcer=limit_enforcer,
        usage_monitor=usage_monitor,
    )

    logger.info(
        "limit_hook.configured",
        extra={
            "has_limit_enforcer": limit_enforcer is not None,
            "has_usage_monitor": usage_monitor is not None,
        },
    )

    return _limit_hook


def reset_limit_hook() -> None:
    """Reset the singleton (for testing)."""
    global _limit_hook
    _limit_hook = None
