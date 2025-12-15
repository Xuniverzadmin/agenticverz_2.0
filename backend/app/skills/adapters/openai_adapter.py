# adapters/openai_adapter.py
"""
OpenAI Adapter for LLM Invoke Skill (M11)

Implements LLMAdapter interface for OpenAI API.
Supports:
- GPT-4o and GPT-4o-mini (cost-effective fallback to Claude)
- Native seeding support for determinism
- Error mapping to contract errors
- Cost tracking
- SAFETY LIMITS: max tokens, max cost per request, rate limiting

See: app/skills/llm_invoke_v2.py for adapter interface
See: app/skills/contracts/llm_invoke.contract.yaml for contract

Environment Variables:
- OPENAI_API_KEY: API key
- OPENAI_DEFAULT_MODEL: Default model (default: gpt-4o-mini)
- OPENAI_MAX_TOKENS_PER_REQUEST: Max tokens per request (default: 16000)
- OPENAI_MAX_COST_CENTS_PER_REQUEST: Max cost in cents per request (default: 50)
- OPENAI_REQUESTS_PER_MINUTE: Rate limit (default: 60)
"""

import hashlib
import logging
import os
import time
import threading
from collections import deque
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("nova.adapters.openai")


# =============================================================================
# Safety Limits Configuration
# =============================================================================

# Max tokens per request (prevents runaway costs)
MAX_TOKENS_PER_REQUEST = int(os.getenv("OPENAI_MAX_TOKENS_PER_REQUEST", "16000"))

# Max estimated cost per single request in cents (prevents expensive requests)
MAX_COST_CENTS_PER_REQUEST = float(os.getenv("OPENAI_MAX_COST_CENTS_PER_REQUEST", "50"))

# Rate limit (requests per minute)
REQUESTS_PER_MINUTE = int(os.getenv("OPENAI_REQUESTS_PER_MINUTE", "60"))

# Model restrictions (if set, only these models are allowed)
ALLOWED_MODELS = os.getenv("OPENAI_ALLOWED_MODELS", "").split(",") if os.getenv("OPENAI_ALLOWED_MODELS") else None


class SafetyLimitExceeded(Exception):
    """Raised when a safety limit is exceeded."""
    pass


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self, requests_per_minute: int = REQUESTS_PER_MINUTE):
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


# Import base types from llm_invoke_v2
def _get_base_types():
    from app.skills.llm_invoke_v2 import (
        LLMAdapter,
        LLMConfig,
        LLMResponse,
        Message,
        LLM_ERROR_MAP,
    )
    return LLMAdapter, LLMConfig, LLMResponse, Message, LLM_ERROR_MAP


# =============================================================================
# OpenAI Cost Model (per 1M tokens, in cents)
# =============================================================================

OPENAI_COST_MODEL = {
    "gpt-4o": {"input": 250, "output": 1000},
    "gpt-4o-2024-11-20": {"input": 250, "output": 1000},
    "gpt-4o-mini": {"input": 15, "output": 60},
    "gpt-4o-mini-2024-07-18": {"input": 15, "output": 60},
    "gpt-4-turbo": {"input": 1000, "output": 3000},
    "gpt-4": {"input": 3000, "output": 6000},
    "gpt-3.5-turbo": {"input": 50, "output": 150},
}

DEFAULT_MODEL = "gpt-4o-mini"  # Cost-effective default


# =============================================================================
# OpenAI Adapter
# =============================================================================

class OpenAIAdapter:
    """
    OpenAI adapter implementing LLMAdapter interface.

    Features:
    - Native seeding: OpenAI supports seed parameter for reproducibility
    - Error mapping: Maps OpenAI API errors to contract error codes
    - Lazy loading: openai SDK is only imported when invoke() is called
    - Cost tracking: Per-model pricing in cents per million tokens
    - SAFETY LIMITS: max tokens, max cost, rate limiting, model restrictions
    """

    # Shared rate limiter across all adapter instances
    _rate_limiter = RateLimiter()

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        max_tokens_per_request: Optional[int] = None,
        max_cost_cents_per_request: Optional[float] = None,
    ):
        """
        Initialize OpenAI adapter with safety limits.

        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
            default_model: Default model to use. Defaults to gpt-4o-mini for cost.
            max_tokens_per_request: Override max tokens limit (default from env or 16000)
            max_cost_cents_per_request: Override max cost limit (default from env or 50)
        """
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._default_model = default_model or os.environ.get("OPENAI_DEFAULT_MODEL", DEFAULT_MODEL)
        self._client = None
        self._max_tokens = max_tokens_per_request or MAX_TOKENS_PER_REQUEST
        self._max_cost_cents = max_cost_cents_per_request or MAX_COST_CENTS_PER_REQUEST

    @property
    def adapter_id(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return self._default_model

    def supports_seeding(self) -> bool:
        """
        OpenAI supports native seeding via the seed parameter.

        When seed is provided, OpenAI attempts to return deterministic results.
        Combined with temperature=0, this provides good reproducibility.
        """
        return True

    def _get_client(self):
        """Lazy load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                )
        return self._client

    def _map_api_error(self, error: Exception) -> Tuple[str, str, bool]:
        """
        Map OpenAI API error to contract error type.

        Returns: (error_type, message, retryable)
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Rate limiting
        if "rate" in error_str or "429" in error_str or "RateLimitError" in error_type:
            return "rate_limited", str(error), True

        # Server overload
        if "overloaded" in error_str or "503" in error_str or "ServiceUnavailableError" in error_type:
            return "overloaded", str(error), True

        # Timeout
        if "timeout" in error_str or "Timeout" in error_type:
            return "timeout", str(error), True

        # Auth errors
        if "auth" in error_str or "key" in error_str or "401" in error_str or "AuthenticationError" in error_type:
            return "auth_failed", str(error), False

        # Content policy (moderation)
        if "content" in error_str or "policy" in error_str or "moderation" in error_str:
            return "content_blocked", str(error), False

        # Context too long
        if "context" in error_str or ("token" in error_str and "limit" in error_str) or "maximum context" in error_str:
            return "context_too_long", str(error), False

        # Invalid request
        if "invalid" in error_str or "400" in error_str or "BadRequestError" in error_type:
            return "invalid_prompt", str(error), False

        # Model not found
        if "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
            return "invalid_model", str(error), False

        # Default to transient (retryable)
        return "overloaded", str(error), True

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # OpenAI uses roughly 4 chars per token
        return len(text) // 4

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in cents."""
        pricing = OPENAI_COST_MODEL.get(model, OPENAI_COST_MODEL[DEFAULT_MODEL])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def _check_safety_limits(
        self,
        model: str,
        max_tokens: int,
        estimated_input_tokens: int
    ) -> Optional[Tuple[str, str, bool]]:
        """
        Check safety limits before making API call.

        Returns error tuple if limits exceeded, None if OK.
        """
        # Check rate limit
        if not self._rate_limiter.check_and_record():
            remaining = self._rate_limiter.requests_remaining()
            return (
                "rate_limited",
                f"Rate limit exceeded ({REQUESTS_PER_MINUTE} req/min). "
                f"Remaining: {remaining}. Please wait before retrying.",
                True  # Retryable
            )

        # Check model restrictions
        if ALLOWED_MODELS and model not in ALLOWED_MODELS:
            return (
                "invalid_model",
                f"Model '{model}' is not in allowed list: {ALLOWED_MODELS}",
                False  # Not retryable
            )

        # Check max tokens
        if max_tokens > self._max_tokens:
            return (
                "invalid_prompt",
                f"Requested max_tokens ({max_tokens}) exceeds limit ({self._max_tokens}). "
                f"Reduce max_tokens to continue.",
                False
            )

        # Estimate max possible cost (input + max output)
        estimated_max_cost = self.estimate_cost(model, estimated_input_tokens, max_tokens)
        if estimated_max_cost > self._max_cost_cents:
            return (
                "budget_exceeded",
                f"Estimated max cost ({estimated_max_cost:.2f}¢) exceeds limit "
                f"({self._max_cost_cents:.2f}¢). Reduce prompt size or max_tokens.",
                False
            )

        return None

    async def invoke(
        self,
        prompt: Union[str, List],
        config
    ) -> Union[Any, Tuple[str, str, bool]]:
        """
        Invoke OpenAI API with safety limits.

        Args:
            prompt: Text prompt or list of Message objects
            config: LLMConfig with model, temperature, etc.

        Returns:
            LLMResponse on success, or (error_type, message, retryable) tuple on error

        Safety Limits:
        - Rate limiting (requests per minute)
        - Max tokens per request
        - Max cost per request
        - Model restrictions (optional)
        """
        LLMAdapter, LLMConfig, LLMResponse, Message, LLM_ERROR_MAP = _get_base_types()

        if not self._api_key:
            return ("auth_failed", "OPENAI_API_KEY not set", False)

        start = time.perf_counter()

        try:
            client = self._get_client()

            # Build messages
            messages = []

            if isinstance(prompt, str):
                if config.system_prompt:
                    messages.append({"role": "system", "content": config.system_prompt})
                messages.append({"role": "user", "content": prompt})
            else:
                for m in prompt:
                    if hasattr(m, 'role'):
                        role, content = m.role, m.content
                    else:
                        role, content = m.get("role", "user"), m.get("content", "")
                    messages.append({"role": role, "content": content})

            # Build request kwargs
            model = config.model or self.default_model
            max_tokens = config.max_tokens

            # Estimate input tokens for safety checks
            messages_text = str(messages)
            estimated_input_tokens = self.estimate_tokens(messages_text)

            # === SAFETY LIMIT CHECKS ===
            safety_error = self._check_safety_limits(model, max_tokens, estimated_input_tokens)
            if safety_error:
                logger.warning(
                    f"Safety limit blocked request: {safety_error[0]} - {safety_error[1]}"
                )
                return safety_error

            request_kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": 0.0 if config.seed is not None else config.temperature,
            }

            # Native seeding support
            if config.seed is not None:
                request_kwargs["seed"] = config.seed

            if config.stop_sequences:
                request_kwargs["stop"] = config.stop_sequences

            # Make API call (sync client, but we're in async context)
            # OpenAI's client handles this internally
            response = client.chat.completions.create(**request_kwargs)

            latency_ms = int((time.perf_counter() - start) * 1000)

            # Extract content
            content = ""
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                if choice.message and choice.message.content:
                    content = choice.message.content

            # Map finish reason
            finish_reason_map = {
                "stop": "end_turn",
                "length": "max_tokens",
                "content_filter": "content_blocked",
            }
            raw_finish = response.choices[0].finish_reason if response.choices else "stop"
            finish_reason = finish_reason_map.get(raw_finish, "end_turn")

            # Get token usage
            input_tokens = response.usage.prompt_tokens if response.usage else self.estimate_tokens(str(messages))
            output_tokens = response.usage.completion_tokens if response.usage else self.estimate_tokens(content)

            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=response.model,
                finish_reason=finish_reason,
                latency_ms=latency_ms,
                seed=config.seed
            )

        except Exception as e:
            logger.warning(f"OpenAI API error: {e}", exc_info=True)
            return self._map_api_error(e)


# =============================================================================
# OpenAI Adapter Stub (for testing)
# =============================================================================

class OpenAIAdapterStub(OpenAIAdapter):
    """
    Stub version of OpenAIAdapter for testing without API access.

    Returns deterministic mock responses based on prompt hash.
    """

    def __init__(self):
        super().__init__(api_key="stub")
        self._mock_responses: Dict[str, Any] = {}

    def set_mock_response(self, prompt_hash: str, response):
        """Set a mock response for a specific prompt hash."""
        self._mock_responses[prompt_hash] = response

    def clear_mocks(self):
        """Clear all mock responses."""
        self._mock_responses.clear()

    async def invoke(
        self,
        prompt: Union[str, List],
        config
    ) -> Union[Any, Tuple[str, str, bool]]:
        """Return mock responses for testing."""
        LLMAdapter, LLMConfig, LLMResponse, Message, LLM_ERROR_MAP = _get_base_types()

        start = time.perf_counter()

        # Normalize prompt for hashing
        if isinstance(prompt, str):
            prompt_text = prompt
        else:
            parts = []
            for m in prompt:
                if hasattr(m, 'role'):
                    parts.append(f"{m.role}: {m.content}")
                else:
                    parts.append(f"{m.get('role', 'user')}: {m.get('content', '')}")
            prompt_text = "\n".join(parts)

        prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]

        # Check for mock response
        if prompt_hash in self._mock_responses:
            response = self._mock_responses[prompt_hash]
            if isinstance(response, tuple):
                return response  # Error tuple
            return response

        # Generate deterministic response
        if config.seed is not None:
            response_seed = f"{config.seed}:{prompt_hash}"
            response_hash = hashlib.sha256(response_seed.encode()).hexdigest()[:8]
            content = f"OpenAI stub response [{response_hash}]: {prompt_text[:40]}..."
        else:
            content = f"OpenAI stub response: {prompt_text[:40]}..."

        latency_ms = int((time.perf_counter() - start) * 1000) + 30

        return LLMResponse(
            content=content,
            input_tokens=self.estimate_tokens(prompt_text),
            output_tokens=self.estimate_tokens(content),
            model=config.model or self.default_model,
            finish_reason="end_turn",
            latency_ms=latency_ms,
            seed=config.seed
        )


# =============================================================================
# Registration
# =============================================================================

def register_openai_adapter():
    """Register OpenAI adapter with the adapter registry."""
    try:
        from app.skills.llm_invoke_v2 import register_adapter
        adapter = OpenAIAdapter()
        register_adapter(adapter)
        return adapter
    except ImportError:
        logger.warning("Could not register OpenAI adapter: register_adapter not available")
        return None
