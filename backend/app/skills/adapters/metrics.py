# LLM Adapter Metrics (M11)
"""
Token metering decorator and helpers for LLM adapter instrumentation.

Provides:
- @track_llm_usage decorator for automatic metrics collection
- track_llm_response() helper for manual tracking
- Cost estimation utilities

Usage:
    from app.skills.adapters.metrics import track_llm_usage, track_llm_response

    # Decorator usage:
    @track_llm_usage
    async def invoke(self, prompt, config):
        ...

    # Manual tracking:
    response = await adapter.invoke(prompt, config)
    track_llm_response(response, adapter_id="claude", model="claude-sonnet-4")
"""

import functools
import logging
import time
from typing import Any, Callable, Optional, Union, Tuple

logger = logging.getLogger("nova.adapters.metrics")


def _get_metrics():
    """Lazy import metrics to avoid circular imports."""
    try:
        from app.metrics import (
            nova_llm_tokens_total,
            nova_llm_cost_cents_total,
            nova_llm_duration_seconds,
            nova_llm_invocations_total,
        )
        return {
            "tokens": nova_llm_tokens_total,
            "cost": nova_llm_cost_cents_total,
            "duration": nova_llm_duration_seconds,
            "invocations": nova_llm_invocations_total,
        }
    except ImportError:
        logger.debug("Prometheus metrics not available")
        return None


def _get_cost_model():
    """Get cost model from llm_invoke_v2."""
    try:
        from app.skills.llm_invoke_v2 import COST_PER_MTOK
        return COST_PER_MTOK
    except ImportError:
        # Fallback cost model
        return {
            "claude-sonnet-4-20250514": {"input": 300, "output": 1500},
            "claude-3-5-sonnet-20241022": {"input": 300, "output": 1500},
            "claude-3-haiku-20240307": {"input": 25, "output": 125},
            "gpt-4o": {"input": 250, "output": 1000},
            "gpt-4o-mini": {"input": 15, "output": 60},
            "stub": {"input": 0, "output": 0},
        }


def estimate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Estimate cost in cents for token usage.

    Args:
        model: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Estimated cost in cents
    """
    cost_model = _get_cost_model()
    pricing = cost_model.get(model, {"input": 100, "output": 500})
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def track_llm_response(
    response: Any,
    adapter_id: str,
    model: str,
    duration_seconds: float,
    success: bool = True,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> None:
    """
    Track LLM response metrics with tenant/agent labels for billing & throttling.

    Args:
        response: LLMResponse object or error tuple
        adapter_id: Adapter identifier (claude, openai, stub)
        model: Model identifier
        duration_seconds: Request duration
        success: Whether the request succeeded
        tenant_id: Tenant ID for multi-tenant billing & throttling
        agent_id: Agent ID for per-agent cost attribution
    """
    metrics = _get_metrics()
    if metrics is None:
        return

    # Default to "default" tenant/agent if not provided (for backwards compatibility)
    tenant_id = tenant_id or "default"
    agent_id = agent_id or "default"

    try:
        # Extract token counts
        if hasattr(response, 'input_tokens'):
            input_tokens = response.input_tokens
            output_tokens = response.output_tokens
        elif isinstance(response, dict):
            input_tokens = response.get('input_tokens', 0)
            output_tokens = response.get('output_tokens', 0)
        else:
            # Error tuple or unknown format
            input_tokens = 0
            output_tokens = 0

        # Track tokens - with tenant/agent for billing
        if input_tokens > 0:
            metrics["tokens"].labels(
                provider=adapter_id,
                model=model,
                token_type="input",
                tenant_id=tenant_id,
                agent_id=agent_id,
            ).inc(input_tokens)

        if output_tokens > 0:
            metrics["tokens"].labels(
                provider=adapter_id,
                model=model,
                token_type="output",
                tenant_id=tenant_id,
                agent_id=agent_id,
            ).inc(output_tokens)

        # Track cost - with tenant/agent for billing
        if input_tokens > 0 or output_tokens > 0:
            cost_cents = estimate_cost_cents(model, input_tokens, output_tokens)
            metrics["cost"].labels(
                provider=adapter_id,
                model=model,
                tenant_id=tenant_id,
                agent_id=agent_id,
            ).inc(cost_cents)

        # Track duration - with tenant for throttling
        metrics["duration"].labels(
            provider=adapter_id,
            model=model,
            tenant_id=tenant_id,
        ).observe(duration_seconds)

        # Track invocation - with tenant/agent for throttling
        status = "success" if success else "error"
        metrics["invocations"].labels(
            provider=adapter_id,
            model=model,
            status=status,
            tenant_id=tenant_id,
            agent_id=agent_id,
        ).inc()

        logger.debug(
            f"Tracked LLM usage: {adapter_id}/{model} tenant={tenant_id} agent={agent_id} - "
            f"{input_tokens} in, {output_tokens} out, "
            f"{duration_seconds:.2f}s, {status}"
        )

    except Exception as e:
        logger.warning(f"Failed to track LLM metrics: {e}")


def track_llm_usage(func: Callable) -> Callable:
    """
    Decorator to automatically track LLM usage metrics.

    Use on adapter invoke() methods. Expects the adapter instance to have:
    - adapter_id property
    - default_model property

    The config object can optionally have:
    - tenant_id: Tenant ID for billing/throttling
    - agent_id: Agent ID for cost attribution

    The decorated function should return either:
    - LLMResponse object on success
    - Tuple (error_type, message, retryable) on error

    Example:
        class MyAdapter(LLMAdapter):
            @track_llm_usage
            async def invoke(self, prompt, config):
                ...
    """
    @functools.wraps(func)
    async def wrapper(self, prompt, config, *args, **kwargs):
        start_time = time.perf_counter()
        success = True
        response = None

        try:
            response = await func(self, prompt, config, *args, **kwargs)

            # Check if it's an error tuple
            if isinstance(response, tuple) and len(response) == 3:
                success = False

            return response

        except Exception as e:
            success = False
            raise

        finally:
            duration = time.perf_counter() - start_time

            # Get adapter info
            adapter_id = getattr(self, 'adapter_id', 'unknown')
            model = getattr(config, 'model', None) or getattr(self, 'default_model', 'unknown')

            # Extract tenant/agent from config for billing & throttling
            tenant_id = getattr(config, 'tenant_id', None)
            agent_id = getattr(config, 'agent_id', None)

            track_llm_response(
                response=response,
                adapter_id=adapter_id,
                model=model,
                duration_seconds=duration,
                success=success,
                tenant_id=tenant_id,
                agent_id=agent_id,
            )

    return wrapper


def track_llm_usage_sync(func: Callable) -> Callable:
    """
    Synchronous version of track_llm_usage decorator.

    For non-async invoke methods.
    """
    @functools.wraps(func)
    def wrapper(self, prompt, config, *args, **kwargs):
        start_time = time.perf_counter()
        success = True
        response = None

        try:
            response = func(self, prompt, config, *args, **kwargs)

            # Check if it's an error tuple
            if isinstance(response, tuple) and len(response) == 3:
                success = False

            return response

        except Exception as e:
            success = False
            raise

        finally:
            duration = time.perf_counter() - start_time

            # Get adapter info
            adapter_id = getattr(self, 'adapter_id', 'unknown')
            model = getattr(config, 'model', None) or getattr(self, 'default_model', 'unknown')

            # Extract tenant/agent from config for billing & throttling
            tenant_id = getattr(config, 'tenant_id', None)
            agent_id = getattr(config, 'agent_id', None)

            track_llm_response(
                response=response,
                adapter_id=adapter_id,
                model=model,
                duration_seconds=duration,
                success=success,
                tenant_id=tenant_id,
                agent_id=agent_id,
            )

    return wrapper


# =============================================================================
# Monthly Cost Estimator
# =============================================================================

def estimate_monthly_cost(
    calls_per_minute: float,
    avg_input_tokens: int,
    avg_output_tokens: int,
    model: str = "claude-sonnet-4-20250514",
    pessimistic_multiplier: float = 1.0,
) -> dict:
    """
    Estimate monthly LLM costs.

    Args:
        calls_per_minute: Average calls per minute
        avg_input_tokens: Average input tokens per call
        avg_output_tokens: Average output tokens per call
        model: Model identifier
        pessimistic_multiplier: Multiply estimates (e.g., 2.0 for 2x)

    Returns:
        Dict with cost breakdown
    """
    # Apply pessimistic multiplier
    input_tokens = avg_input_tokens * pessimistic_multiplier
    output_tokens = avg_output_tokens * pessimistic_multiplier

    # Calculate monthly calls (30 days, 24 hours, 60 minutes)
    monthly_calls = calls_per_minute * 60 * 24 * 30

    # Total tokens
    total_input_tokens = monthly_calls * input_tokens
    total_output_tokens = monthly_calls * output_tokens

    # Cost in cents
    cost_model = _get_cost_model()
    pricing = cost_model.get(model, {"input": 100, "output": 500})
    input_cost_cents = (total_input_tokens / 1_000_000) * pricing["input"]
    output_cost_cents = (total_output_tokens / 1_000_000) * pricing["output"]
    total_cost_cents = input_cost_cents + output_cost_cents

    return {
        "model": model,
        "calls_per_month": int(monthly_calls),
        "total_input_tokens": int(total_input_tokens),
        "total_output_tokens": int(total_output_tokens),
        "input_cost_usd": round(input_cost_cents / 100, 2),
        "output_cost_usd": round(output_cost_cents / 100, 2),
        "total_cost_usd": round(total_cost_cents / 100, 2),
        "pessimistic_multiplier": pessimistic_multiplier,
    }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "track_llm_usage",
    "track_llm_usage_sync",
    "track_llm_response",
    "estimate_cost_cents",
    "estimate_monthly_cost",
]
