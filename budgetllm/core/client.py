"""
OpenAI-compatible client wrapper with budget enforcement, caching, and safety governance.

Drop-in replacement for openai.OpenAI() with:
- Hard budget limits
- Prompt caching
- Hallucination risk scoring
- Parameter clamping
- Safety enforcement

Usage:
    # Switch from OpenAI to BudgetLLM by changing one line:
    # from openai import OpenAI
    from budgetllm import Client as OpenAI

    client = OpenAI(openai_key="sk-...", budget_cents=1000)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response["choices"][0]["message"]["content"])
    print(f"Risk score: {response['risk_score']}")  # NEW
"""

import os
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from budgetllm.core.budget import (
    BudgetExceededError,
    BudgetTracker,
    InMemoryStateAdapter,
    RedisStateAdapter,
)
from budgetllm.core.cache import PromptCache
from budgetllm.core.backends.memory import MemoryBackend
from budgetllm.core.backends.redis import RedisBackend
from budgetllm.core.safety import SafetyController, HighRiskOutputError


# Cost per 1M tokens (in cents) - approximate as of Dec 2024
COST_PER_1M_TOKENS = {
    # OpenAI
    "gpt-4o": {"input": 250, "output": 1000},
    "gpt-4o-mini": {"input": 15, "output": 60},
    "gpt-4-turbo": {"input": 1000, "output": 3000},
    "gpt-4": {"input": 3000, "output": 6000},
    "gpt-3.5-turbo": {"input": 50, "output": 150},
    # Anthropic (for future support)
    "claude-3-5-sonnet": {"input": 300, "output": 1500},
    "claude-3-5-haiku": {"input": 80, "output": 400},
    "claude-3-opus": {"input": 1500, "output": 7500},
    # Default fallback
    "default": {"input": 100, "output": 300},
}


class ChatCompletions:
    """
    OpenAI-compatible chat.completions namespace.

    Mirrors openai.chat.completions with budget enforcement.
    """

    def __init__(self, client: "Client"):
        self._client = client

    def create(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = "gpt-4o-mini",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a chat completion (OpenAI-compatible).

        Args:
            messages: List of message dicts with role and content
            model: Model to use (default: gpt-4o-mini)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            stop: Stop sequences
            stream: Enable streaming (not yet supported)
            **kwargs: Additional OpenAI parameters

        Returns:
            OpenAI-compatible response dict with cost_cents added

        Raises:
            BudgetExceededError: If budget limit exceeded
            ValueError: If messages is None
        """
        if messages is None:
            raise ValueError("messages parameter is required")

        if stream:
            raise NotImplementedError(
                "Streaming not yet supported. Use stream=False."
            )

        return self._client._handle_chat_request(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop,
            **kwargs,
        )


class ChatNamespace:
    """
    OpenAI-compatible chat namespace.

    Provides client.chat.completions.create() interface.
    """

    def __init__(self, client: "Client"):
        self.completions = ChatCompletions(client)
        self._client = client

    def __call__(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Shortcut: client.chat("hi") → client.chat.completions.create(...)

        Args:
            prompt: User message string
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            OpenAI-compatible response dict
        """
        return self._client._handle_chat_request(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            **kwargs,
        )


class Client:
    """
    OpenAI-compatible client with budget enforcement, caching, and safety governance.

    Drop-in replacement for openai.OpenAI() with:
    - Hard budget limits (daily, monthly, cumulative)
    - Automatic kill-switch when limit exceeded
    - Prompt caching for cost savings
    - Hallucination risk scoring
    - Parameter clamping (temperature, top_p, max_tokens)
    - Safety enforcement (optional blocking)

    Features:
    - client.chat.completions.create() - exact OpenAI API match
    - client.chat("hi") - convenient shortcut
    - risk_score in every response (0.0-1.0)
    - risk_factors breakdown for transparency

    Example - OpenAI drop-in replacement:
        # Change this:
        # from openai import OpenAI
        # client = OpenAI()

        # To this:
        from budgetllm import Client as OpenAI
        client = OpenAI(openai_key="sk-...", budget_cents=1000)

        # Same API works:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response["choices"][0]["message"]["content"])
        print(f"Cost: {response['cost_cents']} cents")
        print(f"Risk: {response['risk_score']}")

    Example - With safety governance:
        client = Client(
            budget_cents=1000,
            max_temperature=0.7,      # Clamp high temps
            enforce_safety=True,       # Enable blocking
            risk_threshold=0.6,        # Block if risk > 0.6
        )
    """

    def __init__(
        self,
        openai_key: Optional[str] = None,
        budget_cents: Optional[int] = None,
        daily_limit_cents: Optional[int] = None,
        monthly_limit_cents: Optional[int] = None,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        redis_url: Optional[str] = None,
        auto_pause: bool = True,
        # Safety governance parameters
        max_temperature: float = 1.0,
        max_top_p: float = 1.0,
        max_completion_tokens: int = 4096,
        enforce_safety: bool = False,
        block_on_high_risk: bool = True,
        risk_threshold: float = 0.6,
    ):
        """
        Initialize BudgetLLM client.

        Args:
            openai_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            budget_cents: Hard budget limit in cents (never resets)
            daily_limit_cents: Daily spend limit in cents
            monthly_limit_cents: Monthly spend limit in cents
            cache_enabled: Enable prompt caching (default: True)
            cache_ttl: Cache TTL in seconds (default: 3600)
            redis_url: Redis URL for shared cache/state (optional)
            auto_pause: Raise exception when budget exceeded (default: True)

            # Safety governance (opt-in)
            max_temperature: Maximum temperature (default: 1.0, no clamping)
            max_top_p: Maximum top_p (default: 1.0, no clamping)
            max_completion_tokens: Maximum completion tokens (default: 4096)
            enforce_safety: Enable safety enforcement (default: False)
            block_on_high_risk: Block outputs exceeding risk_threshold (default: True)
            risk_threshold: Risk score threshold for blocking (default: 0.6)
        """
        # Get API key
        self.api_key = openai_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Pass openai_key or set OPENAI_API_KEY env var."
            )

        # Initialize OpenAI client
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI package required. Install with: pip install openai"
            )

        self._openai = openai.OpenAI(api_key=self.api_key)

        # Initialize state adapter (Redis or in-memory)
        if redis_url:
            state_adapter = RedisStateAdapter(redis_url)
            cache_backend = RedisBackend(url=redis_url, default_ttl=cache_ttl)
        else:
            state_adapter = InMemoryStateAdapter()
            cache_backend = MemoryBackend(default_ttl=cache_ttl)

        # Initialize budget tracker
        self.budget = BudgetTracker(
            daily_limit_cents=daily_limit_cents,
            monthly_limit_cents=monthly_limit_cents,
            hard_limit_cents=budget_cents,
            auto_pause=auto_pause,
            state_adapter=state_adapter,
        )

        # Initialize cache
        self._cache = PromptCache(
            backend=cache_backend,
            enabled=cache_enabled,
            default_ttl=cache_ttl,
        )

        # Initialize safety controller
        self.safety = SafetyController(
            max_temperature=max_temperature,
            max_top_p=max_top_p,
            max_tokens=max_completion_tokens,
            enforce_safety=enforce_safety,
            block_on_high_risk=block_on_high_risk,
            risk_threshold=risk_threshold,
        )

        # Settings
        self._cache_enabled = cache_enabled

        # OpenAI-compatible namespaces
        self.chat = ChatNamespace(self)

    def _estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost in cents."""
        costs = COST_PER_1M_TOKENS.get(model, COST_PER_1M_TOKENS["default"])
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return round(input_cost + output_cost, 6)

    def _estimate_input_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Rough estimate of input tokens.

        Uses ~4 chars per token heuristic.
        """
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return max(1, total_chars // 4)

    def _build_openai_response(
        self,
        response_id: str,
        model: str,
        content: str,
        finish_reason: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_cents: float,
        cache_hit: bool = False,
        risk_score: float = 0.0,
        risk_factors: Optional[Dict[str, Any]] = None,
        params_clamped: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build OpenAI-compatible response format.

        Matches the exact structure returned by openai.chat.completions.create()
        with BudgetLLM additions for cost, caching, and safety governance.
        """
        return {
            "id": response_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "finish_reason": finish_reason,
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            # BudgetLLM additions
            "cost_cents": cost_cents,
            "cache_hit": cache_hit,
            # Safety governance additions
            "risk_score": risk_score,
            "risk_factors": risk_factors or {},
            "params_clamped": params_clamped or {},
        }

    def _handle_chat_request(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        enable_cache: Optional[bool] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Internal handler for chat completion requests.

        Flow:
        1. Classify prompt type
        2. Clamp parameters (safety governance)
        3. Check cache
        4. Enforce budget limits
        5. Make OpenAI API call
        6. Analyze output for risk signals
        7. Calculate risk score
        8. Enforce safety (if enabled)
        9. Record cost
        10. Cache response
        11. Return response with risk_score
        """
        # Determine cache usage
        use_cache = enable_cache if enable_cache is not None else self._cache_enabled

        # 1. Classify prompt type (for risk weighting)
        prompt_type, prompt_confidence = self.safety.classify_prompt(messages)

        # 2. Clamp parameters (safety governance)
        original_temp = temperature
        original_top_p = top_p
        original_max_tokens = max_tokens

        clamped_temp, clamped_top_p, clamped_max_tokens = self.safety.clamp_params(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

        # Track what was clamped
        params_clamped = self.safety.was_clamped(
            original_temp, original_top_p, original_max_tokens,
            clamped_temp, clamped_top_p, clamped_max_tokens,
        )

        # Use clamped values
        temperature = clamped_temp
        top_p = clamped_top_p
        max_tokens = clamped_max_tokens

        # 3. Check cache first (with clamped parameters)
        if use_cache:
            cached = self._cache.get(
                model=model,
                messages=messages,
                temperature=temperature,
            )

            if cached:
                # Return cached response with cache_hit=True, cost=0
                # Use cached risk data if available
                return self._build_openai_response(
                    response_id=cached.get("id", f"chatcmpl-cached-{uuid.uuid4().hex[:8]}"),
                    model=model,
                    content=cached.get("content", ""),
                    finish_reason=cached.get("finish_reason", "stop"),
                    prompt_tokens=cached.get("prompt_tokens", 0),
                    completion_tokens=cached.get("completion_tokens", 0),
                    cost_cents=0.0,  # Free from cache!
                    cache_hit=True,
                    risk_score=cached.get("risk_score", 0.0),
                    risk_factors=cached.get("risk_factors", {}),
                    params_clamped=params_clamped,
                )

        # 4. Check budget before making API call
        self.budget.check_limits()

        # 5. Build request parameters
        request_params = {
            "model": model,
            "messages": messages,
        }

        if temperature is not None:
            request_params["temperature"] = temperature
        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens
        if top_p is not None:
            request_params["top_p"] = top_p

        # Pass through any additional kwargs (stop, etc.)
        # Remove our custom params that OpenAI doesn't understand
        openai_kwargs = {k: v for k, v in kwargs.items() if k not in ("enable_cache",)}
        request_params.update(openai_kwargs)

        # 6. Make actual OpenAI API call
        response = self._openai.chat.completions.create(**request_params)

        # 7. Extract response data
        choice = response.choices[0]
        content = choice.message.content or ""
        finish_reason = choice.finish_reason
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        # 8. Analyze output for risk signals
        output_signals = self.safety.analyze_output(content)

        # 9. Calculate risk score
        input_params = {
            "temperature": temperature or 0.7,  # Default if not specified
            "top_p": top_p or 1.0,
            "max_tokens": max_tokens or completion_tokens,
        }

        risk_score, risk_factors = self.safety.score_risk(
            prompt_type=prompt_type,
            input_params=input_params,
            output_signals=output_signals,
            model=model,
        )

        # Add prompt classification to risk factors
        risk_factors["prompt_confidence"] = prompt_confidence

        # 10. Enforce safety (may raise HighRiskOutputError)
        self.safety.enforce(risk_score, risk_factors)

        # 11. Calculate and record cost
        cost_cents = self._estimate_cost(model, prompt_tokens, completion_tokens)

        # Record cost in budget tracker (convert to integer microcents for precision)
        cost_microcents = int(cost_cents * 100)  # Store as hundredths of a cent
        if cost_microcents > 0:
            self.budget.record_cost(cost_microcents)

        # 12. Build OpenAI-compatible result
        result = self._build_openai_response(
            response_id=response.id,
            model=response.model,
            content=content,
            finish_reason=finish_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_cents=cost_cents,
            cache_hit=False,
            risk_score=risk_score,
            risk_factors=risk_factors,
            params_clamped=params_clamped,
        )

        # 13. Store in cache (include risk data)
        if use_cache:
            cache_data = {
                "id": response.id,
                "content": content,
                "finish_reason": finish_reason,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "risk_score": risk_score,
                "risk_factors": risk_factors,
            }
            self._cache.set(
                model=model,
                messages=messages,
                response=cache_data,
                cost_cents=cost_cents,
                temperature=temperature,
            )

        return result

    # =========================================================================
    # Status & Control Methods
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """
        Get current budget and cache status.

        Returns:
            Dict with budget limits, spend, and cache stats
        """
        return {
            "budget": self.budget.get_status(),
            "cache": self._cache.get_stats(),
        }

    def pause(self) -> None:
        """Manually pause (kill switch). Blocks all API calls."""
        self.budget.pause()

    def resume(self) -> None:
        """Resume after pause."""
        self.budget.resume()

    def is_paused(self) -> bool:
        """Check if client is paused."""
        return self.budget.is_paused()

    def reset(self) -> None:
        """Reset all counters and cache stats (for testing)."""
        self.budget.reset_all()
        self._cache.reset_stats()


# =============================================================================
# Convenience Functions
# =============================================================================

def create_client(
    openai_key: Optional[str] = None,
    budget_cents: Optional[int] = None,
    **kwargs,
) -> Client:
    """
    Create a BudgetLLM client.

    Convenience wrapper around Client().

    Example:
        from budgetllm import create_client

        client = create_client(budget_cents=1000)
        response = client.chat("Hello!")
    """
    return Client(
        openai_key=openai_key,
        budget_cents=budget_cents,
        **kwargs,
    )
