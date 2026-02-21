# capability_id: CAP-009
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide (NOT console-owned)
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: llm_config (via driver)
#   Writes: none
# Role: LLM policy and safety limits enforcement (pure logic)
# Callers: OpenAIAdapter (L3), TenantLLMConfig (L3), llm_invoke skills
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-254 Phase B Fix
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure logic

"""
L4 LLM Policy Engine - Domain Authority for LLM Safety and Cost Controls

B01/B05 FIX: Moved from L3 adapters to L4 domain engine.
This engine is the authoritative source for:
- Safety limits (max tokens, max cost, rate limits)
- Model selection policy
- Budget enforcement
- Model restrictions

L3 adapters must delegate all policy decisions to this engine.

Environment Variables:
- LLM_MAX_TOKENS_PER_REQUEST: Max tokens per request (default: 16000)
- LLM_MAX_COST_CENTS_PER_REQUEST: Max cost in cents per request (default: 50)
- LLM_REQUESTS_PER_MINUTE: Rate limit (default: 60)
- LLM_ALLOWED_MODELS: Comma-separated list of allowed models (optional)
"""

import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.llm_policy_engine")


# =============================================================================
# L4 Domain Authority: LLM Safety Limits
# =============================================================================
# These are policy decisions that L3 adapters must respect.

# Max tokens per request (prevents runaway costs)
LLM_MAX_TOKENS_PER_REQUEST = int(os.getenv("LLM_MAX_TOKENS_PER_REQUEST", "16000"))

# Max estimated cost per single request in cents (prevents expensive requests)
LLM_MAX_COST_CENTS_PER_REQUEST = float(os.getenv("LLM_MAX_COST_CENTS_PER_REQUEST", "50"))

# Rate limit (requests per minute)
LLM_REQUESTS_PER_MINUTE = int(os.getenv("LLM_REQUESTS_PER_MINUTE", "60"))

# Model restrictions (if set, only these models are allowed)
_allowed_models_str = os.getenv("LLM_ALLOWED_MODELS", "")
LLM_ALLOWED_MODELS: Optional[List[str]] = (
    [m.strip() for m in _allowed_models_str.split(",") if m.strip()] if _allowed_models_str else None
)


# =============================================================================
# L4 Domain Authority: Model Selection Policy
# =============================================================================

# Default models by provider
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o-mini",
}

# Fallback model for cost optimization
FALLBACK_MODEL = "gpt-4o-mini"

# Allowed models list (L4 authority)
SYSTEM_ALLOWED_MODELS: List[str] = [
    "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-20241022",
    "gpt-4o",
    "gpt-4o-mini",
]

# Expensive models that require explicit permission
EXPENSIVE_MODELS: List[str] = [
    "claude-opus-4-20250514",
    "gpt-4",
    "gpt-4-turbo",
]

# Task-type to model recommendations (L4 policy)
TASK_MODEL_POLICY: Dict[str, str] = {
    "planning": "gpt-4o-mini",  # Use cheap model for planning
    "execution": "claude-sonnet-4-20250514",  # Default execution model
    "high_value": "claude-sonnet-4-20250514",  # Best model for important tasks
    "default": "claude-sonnet-4-20250514",
}


# =============================================================================
# L4 Domain Authority: Cost Model
# =============================================================================

# Cost per 1M tokens in cents
LLM_COST_MODEL: Dict[str, Dict[str, float]] = {
    # Anthropic models
    "claude-sonnet-4-20250514": {"input": 300, "output": 1500},
    "claude-3-5-sonnet-20241022": {"input": 300, "output": 1500},
    "claude-opus-4-20250514": {"input": 1500, "output": 7500},
    # OpenAI models
    "gpt-4o": {"input": 250, "output": 1000},
    "gpt-4o-2024-11-20": {"input": 250, "output": 1000},
    "gpt-4o-mini": {"input": 15, "output": 60},
    "gpt-4o-mini-2024-07-18": {"input": 15, "output": 60},
    "gpt-4-turbo": {"input": 1000, "output": 3000},
    "gpt-4": {"input": 3000, "output": 6000},
    "gpt-3.5-turbo": {"input": 50, "output": 150},
}


@dataclass
class SafetyCheckResult:
    """Result of a safety limit check."""

    allowed: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retryable: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


class LLMRateLimiter:
    """
    Sliding window rate limiter for LLM requests (L4 policy enforcement).

    L3 adapters must use this instead of implementing their own.
    """

    _instances: Dict[str, "LLMRateLimiter"] = {}
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, provider: str = "default") -> "LLMRateLimiter":
        """Get or create rate limiter for a provider."""
        with cls._lock:
            if provider not in cls._instances:
                cls._instances[provider] = cls(LLM_REQUESTS_PER_MINUTE)
            return cls._instances[provider]

    def __init__(self, requests_per_minute: int = LLM_REQUESTS_PER_MINUTE):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.timestamps: deque = deque()
        self._lock = threading.Lock()

    def check_and_record(self) -> bool:
        """
        Check if request is allowed and record it.

        Returns True if allowed, False if rate limited.
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            # Remove old timestamps outside the window
            while self.timestamps and self.timestamps[0] < window_start:
                self.timestamps.popleft()

            # Check if we're at the limit
            if len(self.timestamps) >= self.requests_per_minute:
                return False

            # Record this request
            self.timestamps.append(now)
            return True

    def requests_remaining(self) -> int:
        """Get number of requests remaining in current window."""
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            # Remove old timestamps
            while self.timestamps and self.timestamps[0] < window_start:
                self.timestamps.popleft()

            return max(0, self.requests_per_minute - len(self.timestamps))


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text (L4 domain function).

    Uses rough approximation of 4 chars per token.
    """
    return len(text) // 4


def estimate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Estimate cost in cents (L4 domain function).

    Args:
        model: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Estimated cost in cents
    """
    pricing = LLM_COST_MODEL.get(model, LLM_COST_MODEL.get("gpt-4o-mini", {"input": 15, "output": 60}))
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def check_safety_limits(
    model: str,
    max_tokens: int,
    estimated_input_tokens: int,
    provider: str = "default",
    max_tokens_limit: Optional[int] = None,
    max_cost_cents_limit: Optional[float] = None,
) -> SafetyCheckResult:
    """
    Check safety limits before making LLM API call (L4 domain function).

    L3 adapters must call this before invoking LLM APIs.
    They must NOT implement their own safety checks.

    Args:
        model: Model identifier
        max_tokens: Requested max tokens for completion
        estimated_input_tokens: Estimated input token count
        provider: Provider name for rate limiter
        max_tokens_limit: Override max tokens limit
        max_cost_cents_limit: Override max cost limit

    Returns:
        SafetyCheckResult indicating if request is allowed
    """
    max_tokens_limit = max_tokens_limit or LLM_MAX_TOKENS_PER_REQUEST
    max_cost_cents_limit = max_cost_cents_limit or LLM_MAX_COST_CENTS_PER_REQUEST

    # Check rate limit
    rate_limiter = LLMRateLimiter.get_instance(provider)
    if not rate_limiter.check_and_record():
        remaining = rate_limiter.requests_remaining()
        return SafetyCheckResult(
            allowed=False,
            error_type="rate_limited",
            error_message=f"Rate limit exceeded ({LLM_REQUESTS_PER_MINUTE} req/min). "
            f"Remaining: {remaining}. Please wait before retrying.",
            retryable=True,
            details={"remaining": remaining, "limit": LLM_REQUESTS_PER_MINUTE},
        )

    # Check model restrictions
    if LLM_ALLOWED_MODELS and model not in LLM_ALLOWED_MODELS:
        return SafetyCheckResult(
            allowed=False,
            error_type="invalid_model",
            error_message=f"Model '{model}' is not in allowed list: {LLM_ALLOWED_MODELS}",
            retryable=False,
            details={"model": model, "allowed_models": LLM_ALLOWED_MODELS},
        )

    # Check max tokens
    if max_tokens > max_tokens_limit:
        return SafetyCheckResult(
            allowed=False,
            error_type="invalid_prompt",
            error_message=f"Requested max_tokens ({max_tokens}) exceeds limit ({max_tokens_limit}). "
            f"Reduce max_tokens to continue.",
            retryable=False,
            details={"requested": max_tokens, "limit": max_tokens_limit},
        )

    # Estimate max possible cost (input + max output)
    estimated_max_cost = estimate_cost_cents(model, estimated_input_tokens, max_tokens)
    if estimated_max_cost > max_cost_cents_limit:
        return SafetyCheckResult(
            allowed=False,
            error_type="budget_exceeded",
            error_message=f"Estimated max cost ({estimated_max_cost:.2f}¢) exceeds limit "
            f"({max_cost_cents_limit:.2f}¢). Reduce prompt size or max_tokens.",
            retryable=False,
            details={
                "estimated_cost_cents": estimated_max_cost,
                "limit_cents": max_cost_cents_limit,
            },
        )

    return SafetyCheckResult(
        allowed=True,
        details={
            "model": model,
            "max_tokens": max_tokens,
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_cost_cents": estimated_max_cost,
        },
    )


def is_model_allowed(model: str, tenant_allowed_models: Optional[List[str]] = None) -> bool:
    """
    Check if a model is allowed (L4 domain function).

    Args:
        model: Model identifier
        tenant_allowed_models: Optional tenant-specific allowed list

    Returns:
        True if model is allowed
    """
    # Check tenant-specific list first
    if tenant_allowed_models is not None:
        return model in tenant_allowed_models

    # Check system-wide restrictions
    if LLM_ALLOWED_MODELS:
        return model in LLM_ALLOWED_MODELS

    # Default: allow all models in SYSTEM_ALLOWED_MODELS
    return model in SYSTEM_ALLOWED_MODELS


def is_expensive_model(model: str) -> bool:
    """Check if a model is classified as expensive (L4 domain function)."""
    return model in EXPENSIVE_MODELS


def get_model_for_task(
    task_type: str,
    requested_model: Optional[str] = None,
    tenant_allowed_models: Optional[List[str]] = None,
    allow_expensive: bool = False,
) -> str:
    """
    Get appropriate model for a task type (L4 policy decision).

    L3 TenantLLMConfig must delegate model selection to this function.

    Args:
        task_type: Type of task (planning, execution, high_value, default)
        requested_model: Explicitly requested model
        tenant_allowed_models: Tenant-specific allowed models
        allow_expensive: Whether expensive models are permitted

    Returns:
        Model identifier to use
    """
    # If explicit request and allowed, use it
    if requested_model and is_model_allowed(requested_model, tenant_allowed_models):
        if is_expensive_model(requested_model) and not allow_expensive:
            logger.warning(f"Expensive model {requested_model} requested but not allowed, using fallback")
        else:
            return requested_model

    # Task-based selection
    recommended = TASK_MODEL_POLICY.get(task_type, TASK_MODEL_POLICY["default"])

    # Verify it's allowed
    if is_model_allowed(recommended, tenant_allowed_models):
        return recommended

    # Fall back to cheap model
    if is_model_allowed(FALLBACK_MODEL, tenant_allowed_models):
        return FALLBACK_MODEL

    # Last resort: first allowed model
    allowed = tenant_allowed_models or SYSTEM_ALLOWED_MODELS
    return allowed[0] if allowed else "gpt-4o-mini"


def get_effective_model(
    requested_model: Optional[str],
    preferred_model: str,
    fallback_model: str,
    allowed_models: List[str],
) -> str:
    """
    Get effective model based on request and tenant config (L4 policy decision).

    L3 TenantLLMConfig.get_effective_model() must delegate to this.

    Args:
        requested_model: Model explicitly requested
        preferred_model: Tenant's preferred model
        fallback_model: Tenant's fallback model
        allowed_models: Tenant's allowed models list

    Returns:
        Model identifier to use
    """
    # Priority 1: If requested_model is in allowed_models, use it
    if requested_model and requested_model in allowed_models:
        return requested_model

    # Priority 2: Use preferred_model if available
    if preferred_model in allowed_models:
        return preferred_model

    # Priority 3: Use fallback_model
    return fallback_model


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Constants
    "LLM_MAX_TOKENS_PER_REQUEST",
    "LLM_MAX_COST_CENTS_PER_REQUEST",
    "LLM_REQUESTS_PER_MINUTE",
    "LLM_ALLOWED_MODELS",
    "LLM_COST_MODEL",
    "SYSTEM_ALLOWED_MODELS",
    "EXPENSIVE_MODELS",
    "TASK_MODEL_POLICY",
    # Classes
    "SafetyCheckResult",
    "LLMRateLimiter",
    # Functions
    "estimate_tokens",
    "estimate_cost_cents",
    "check_safety_limits",
    "is_model_allowed",
    "is_expensive_model",
    "get_model_for_task",
    "get_effective_model",
]
