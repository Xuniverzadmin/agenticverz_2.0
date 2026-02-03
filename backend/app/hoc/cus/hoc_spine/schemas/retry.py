# Layer: L4 — HOC Spine (Schema)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Retry API schemas
# Callers: API routes
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: API Schemas

# Retry Policy Schemas
# Defines retry behavior and backoff strategies

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BackoffStrategy(str, Enum):
    """Backoff strategy for retries."""

    CONSTANT = "constant"  # Same delay each time
    LINEAR = "linear"  # delay * attempt
    EXPONENTIAL = "exponential"  # delay * 2^attempt
    FIBONACCI = "fibonacci"  # fibonacci sequence delays


class RetryPolicy(BaseModel):
    """Retry policy configuration for skills and steps.

    Defines how failures should be retried, including
    max attempts, delays, and backoff strategies.
    """

    max_attempts: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts (1 = no retry)")
    backoff_strategy: BackoffStrategy = Field(
        default=BackoffStrategy.EXPONENTIAL, description="Backoff strategy between retries"
    )
    initial_delay_seconds: float = Field(default=1.0, ge=0.1, le=300, description="Initial delay before first retry")
    max_delay_seconds: float = Field(default=60.0, ge=1, le=3600, description="Maximum delay cap")
    jitter: bool = Field(default=True, description="Add random jitter to prevent thundering herd")
    retryable_errors: Optional[list[str]] = Field(
        default=None, description="List of error types to retry (None = retry all transient)"
    )

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (1-indexed)."""
        if attempt <= 1:
            return 0.0

        retry_num = attempt - 1  # Convert to 0-indexed retry count

        if self.backoff_strategy == BackoffStrategy.CONSTANT:
            delay = self.initial_delay_seconds
        elif self.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.initial_delay_seconds * retry_num
        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.initial_delay_seconds * (2 ** (retry_num - 1))
        elif self.backoff_strategy == BackoffStrategy.FIBONACCI:
            delay = self.initial_delay_seconds * self._fibonacci(retry_num)
        else:
            delay = self.initial_delay_seconds

        return min(delay, self.max_delay_seconds)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "max_attempts": 3,
                "backoff_strategy": "exponential",
                "initial_delay_seconds": 1.0,
                "max_delay_seconds": 60.0,
                "jitter": True,
            }
        }
    )

    @staticmethod
    def _fibonacci(n: int) -> int:
        """Calculate nth fibonacci number."""
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b
