# capability_id: CAP-008
# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: Reasons for stopping retry.
# M15 Retry Policy for LLM Governance
# Handles retry logic with parameter adjustment for blocked/failed LLM calls
#
# Features:
# - Configurable max retries
# - Exponential backoff
# - Parameter clamping on retry (reduce temperature, etc.)
# - Stop conditions (budget exhausted, max retries, permanent failure)

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

logger = logging.getLogger("nova.agents.retry_policy")

T = TypeVar("T")


class RetryStopReason(str, Enum):
    """Reasons for stopping retry."""

    SUCCESS = "success"
    MAX_RETRIES = "max_retries"
    BUDGET_EXHAUSTED = "budget_exhausted"
    PERMANENT_FAILURE = "permanent_failure"
    RISK_TOO_HIGH = "risk_too_high"
    MANUAL_STOP = "manual_stop"


@dataclass
class RetryConfig:
    """Configuration for retry policy."""

    # Retry limits
    max_retries: int = 3

    # Backoff settings
    initial_backoff_ms: int = 100
    max_backoff_ms: int = 5000
    backoff_multiplier: float = 2.0

    # Parameter adjustment on retry
    temperature_reduction: float = 0.2  # Reduce by 0.2 each retry
    min_temperature: float = 0.0  # Floor

    # Risk adjustment
    risk_threshold_increase: float = 0.1  # Be more lenient each retry
    max_risk_threshold: float = 0.9  # Ceiling

    # Budget safety
    budget_safety_margin_cents: int = 20  # Stop 20 cents before exhaustion

    # Permanent failure codes (don't retry)
    permanent_failures: List[str] = field(
        default_factory=lambda: [
            "ERR_LLM_AUTH_FAILED",
            "ERR_LLM_INVALID_MODEL",
            "ERR_LLM_CONTENT_BLOCKED",
            "ERR_LLM_CONTEXT_TOO_LONG",
        ]
    )


@dataclass
class RetryState:
    """Current state of retry attempts."""

    attempt: int = 0
    last_error: Optional[str] = None
    last_error_code: Optional[str] = None
    total_cost_cents: float = 0.0
    adjustments_made: Dict[str, Any] = field(default_factory=dict)

    # Adjusted parameters (cumulative)
    current_temperature: Optional[float] = None
    current_risk_threshold: Optional[float] = None


@dataclass
class RetryResult:
    """Result of retry execution."""

    success: bool
    result: Any
    stop_reason: RetryStopReason
    total_attempts: int
    total_cost_cents: float
    final_parameters: Dict[str, Any]
    retry_history: List[Dict[str, Any]]


class RetryPolicy:
    """
    Retry policy for LLM calls with parameter adjustment.

    On each retry:
    1. Reduce temperature (more deterministic)
    2. Increase risk threshold (more lenient)
    3. Apply exponential backoff
    4. Check budget with safety margin

    Stop conditions:
    - Success
    - Max retries reached
    - Budget exhausted (with safety margin)
    - Permanent failure code
    - Risk still too high after max adjustments
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def should_retry(
        self,
        state: RetryState,
        error_code: Optional[str],
        budget_remaining: Optional[int],
    ) -> Tuple[bool, RetryStopReason]:
        """
        Determine if we should retry.

        Args:
            state: Current retry state
            error_code: Error code from last attempt
            budget_remaining: Remaining budget in cents

        Returns:
            Tuple of (should_retry, stop_reason)
        """
        # Check max retries
        if state.attempt >= self.config.max_retries:
            return False, RetryStopReason.MAX_RETRIES

        # Check permanent failure
        if error_code in self.config.permanent_failures:
            return False, RetryStopReason.PERMANENT_FAILURE

        # Check budget with safety margin
        if budget_remaining is not None:
            if budget_remaining <= self.config.budget_safety_margin_cents:
                return False, RetryStopReason.BUDGET_EXHAUSTED

        return True, RetryStopReason.SUCCESS

    def get_adjusted_parameters(
        self,
        state: RetryState,
        original_temperature: float = 0.7,
        original_risk_threshold: float = 0.6,
    ) -> Dict[str, Any]:
        """
        Get adjusted parameters for next retry attempt.

        Args:
            state: Current retry state
            original_temperature: Original temperature setting
            original_risk_threshold: Original risk threshold

        Returns:
            Dict with adjusted parameters
        """
        # Calculate temperature reduction
        temp_reduction = self.config.temperature_reduction * state.attempt
        new_temp = max(self.config.min_temperature, original_temperature - temp_reduction)

        # Calculate risk threshold increase
        threshold_increase = self.config.risk_threshold_increase * state.attempt
        new_threshold = min(self.config.max_risk_threshold, original_risk_threshold + threshold_increase)

        return {
            "temperature": new_temp,
            "risk_threshold": new_threshold,
            "attempt": state.attempt + 1,
            "adjustments": {
                "temperature_reduced_by": temp_reduction,
                "risk_threshold_increased_by": threshold_increase,
            },
        }

    def get_backoff_ms(self, attempt: int) -> int:
        """Calculate backoff time for attempt."""
        backoff = self.config.initial_backoff_ms * (self.config.backoff_multiplier**attempt)
        return min(int(backoff), self.config.max_backoff_ms)

    async def execute_with_retry(
        self,
        func: Callable[..., T],
        original_params: Dict[str, Any],
        budget_remaining: Optional[int] = None,
        on_retry: Optional[Callable[[RetryState], None]] = None,
    ) -> RetryResult:
        """
        Execute function with retry policy.

        Args:
            func: Async function to execute
            original_params: Original parameters
            budget_remaining: Remaining budget (updated per attempt)
            on_retry: Optional callback on each retry

        Returns:
            RetryResult with outcome and history
        """
        state = RetryState(
            current_temperature=original_params.get("temperature", 0.7),
            current_risk_threshold=original_params.get("risk_threshold", 0.6),
        )

        retry_history: List[Dict[str, Any]] = []
        final_result = None
        stop_reason = RetryStopReason.MAX_RETRIES

        while True:
            # Get adjusted parameters
            adjusted = self.get_adjusted_parameters(
                state,
                original_temperature=original_params.get("temperature", 0.7),
                original_risk_threshold=original_params.get("risk_threshold", 0.6),
            )

            # Merge with original params
            current_params = {
                **original_params,
                "temperature": adjusted["temperature"],
                "risk_threshold": adjusted["risk_threshold"],
            }

            # Execute
            try:
                result = await func(**current_params)

                # Check if result indicates success
                if hasattr(result, "success") and result.success:
                    final_result = result
                    stop_reason = RetryStopReason.SUCCESS

                    # Track cost
                    if hasattr(result, "cost_cents"):
                        state.total_cost_cents += result.cost_cents or 0

                    retry_history.append(
                        {
                            "attempt": state.attempt + 1,
                            "success": True,
                            "parameters": current_params,
                            "cost_cents": getattr(result, "cost_cents", 0),
                        }
                    )
                    break

                # Result indicates failure (blocked, budget exceeded, etc.)
                if hasattr(result, "blocked") and result.blocked:
                    state.last_error = getattr(result, "blocked_reason", "blocked")
                    state.last_error_code = getattr(result, "error_code", "ERR_BLOCKED")
                else:
                    state.last_error = getattr(result, "error", "unknown")
                    state.last_error_code = getattr(result, "error_code", "ERR_UNKNOWN")

                # Track cost even on failure
                if hasattr(result, "cost_cents"):
                    state.total_cost_cents += result.cost_cents or 0
                    if budget_remaining is not None:
                        budget_remaining -= int(result.cost_cents or 0)

                retry_history.append(
                    {
                        "attempt": state.attempt + 1,
                        "success": False,
                        "error": state.last_error,
                        "error_code": state.last_error_code,
                        "parameters": current_params,
                        "cost_cents": getattr(result, "cost_cents", 0),
                    }
                )

                final_result = result

            except Exception as e:
                state.last_error = str(e)
                state.last_error_code = "ERR_EXCEPTION"

                retry_history.append(
                    {
                        "attempt": state.attempt + 1,
                        "success": False,
                        "error": str(e),
                        "error_code": "ERR_EXCEPTION",
                        "parameters": current_params,
                    }
                )

            state.attempt += 1

            # Check if we should retry
            should_continue, reason = self.should_retry(state, state.last_error_code, budget_remaining)

            if not should_continue:
                stop_reason = reason
                break

            # Backoff before retry
            backoff_ms = self.get_backoff_ms(state.attempt)
            logger.info(
                "retry_backoff",
                extra={
                    "attempt": state.attempt,
                    "backoff_ms": backoff_ms,
                    "error": state.last_error,
                },
            )

            # Callback
            if on_retry:
                on_retry(state)

            # Wait
            await _async_sleep(backoff_ms / 1000.0)

        return RetryResult(
            success=stop_reason == RetryStopReason.SUCCESS,
            result=final_result,
            stop_reason=stop_reason,
            total_attempts=state.attempt + 1,
            total_cost_cents=state.total_cost_cents,
            final_parameters={
                "temperature": adjusted["temperature"],
                "risk_threshold": adjusted["risk_threshold"],
            },
            retry_history=retry_history,
        )


async def _async_sleep(seconds: float):
    """Async sleep helper."""
    import asyncio

    await asyncio.sleep(seconds)


# =============================================================================
# Convenience functions
# =============================================================================


def get_default_retry_config() -> RetryConfig:
    """Get default retry configuration."""
    return RetryConfig()


def create_retry_policy(
    max_retries: int = 3,
    temperature_reduction: float = 0.2,
    budget_safety_margin_cents: int = 20,
) -> RetryPolicy:
    """Create a retry policy with custom settings."""
    return RetryPolicy(
        RetryConfig(
            max_retries=max_retries,
            temperature_reduction=temperature_reduction,
            budget_safety_margin_cents=budget_safety_margin_cents,
        )
    )
