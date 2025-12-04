# adapters/claude_adapter.py
"""
Claude Adapter for LLM Invoke Skill (M3)

Implements LLMAdapter interface for Anthropic Claude API.
Supports:
- Deterministic fallback (temperature=0, seed hashing)
- Error mapping to contract errors
- Cost tracking
- Rate limit handling

See: app/skills/llm_invoke_v2.py for adapter interface
See: app/skills/contracts/llm_invoke.contract.yaml for contract
"""

import hashlib
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("nova.adapters.claude")


# Import base types from llm_invoke_v2
# Note: This is a lazy import to avoid circular dependencies
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
# Claude Cost Model (per 1M tokens, in cents)
# =============================================================================

CLAUDE_COST_MODEL = {
    "claude-3-5-sonnet-20241022": {"input": 300, "output": 1500},
    "claude-sonnet-4-20250514": {"input": 300, "output": 1500},
    "claude-3-5-haiku-20241022": {"input": 25, "output": 125},
    "claude-3-haiku-20240307": {"input": 25, "output": 125},
    "claude-3-opus-20240229": {"input": 1500, "output": 7500},
}

DEFAULT_MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# Claude Adapter
# =============================================================================

class ClaudeAdapter:
    """
    Anthropic Claude adapter implementing LLMAdapter interface.

    Features:
    - Deterministic fallback: When seed is provided, uses temperature=0
      and includes seed in system prompt for reproducibility hints
    - Error mapping: Maps Anthropic API errors to contract error codes
    - Lazy loading: anthropic SDK is only imported when invoke() is called
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude adapter.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None

    @property
    def adapter_id(self) -> str:
        return "claude"

    @property
    def default_model(self) -> str:
        return DEFAULT_MODEL

    def supports_seeding(self) -> bool:
        """
        Claude does not natively support seeding.

        We implement a deterministic fallback:
        - temperature=0 for greedy decoding
        - Seed included in system prompt as hint
        """
        return False  # Native seeding not supported

    def _get_client(self):
        """Lazy load the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
        return self._client

    def _map_api_error(self, error: Exception) -> Tuple[str, str, bool]:
        """
        Map Anthropic API error to contract error type.

        Returns: (error_type, message, retryable)
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Rate limiting
        if "rate" in error_str or "429" in error_str or "RateLimitError" in error_type:
            return "rate_limited", str(error), True

        # Overloaded
        if "overloaded" in error_str or "503" in error_str:
            return "overloaded", str(error), True

        # Timeout
        if "timeout" in error_str:
            return "timeout", str(error), True

        # Auth errors
        if "auth" in error_str or "key" in error_str or "401" in error_str:
            return "auth_failed", str(error), False

        # Content policy
        if "content" in error_str and ("block" in error_str or "policy" in error_str):
            return "content_blocked", str(error), False

        # Context too long
        if "context" in error_str or "token" in error_str and "limit" in error_str:
            return "context_too_long", str(error), False

        # Invalid request
        if "invalid" in error_str or "400" in error_str:
            return "invalid_prompt", str(error), False

        # Default to transient (retryable)
        return "overloaded", str(error), True

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Claude uses roughly 3.5 chars per token
        return len(text) // 3

    async def invoke(
        self,
        prompt: Union[str, List],
        config
    ) -> Union[Any, Tuple[str, str, bool]]:
        """
        Invoke Claude API.

        Args:
            prompt: Text prompt or list of Message objects
            config: LLMConfig with model, temperature, etc.

        Returns:
            LLMResponse on success, or (error_type, message, retryable) tuple on error
        """
        LLMAdapter, LLMConfig, LLMResponse, Message, LLM_ERROR_MAP = _get_base_types()

        if not self._api_key:
            return ("auth_failed", "ANTHROPIC_API_KEY not set", False)

        start = time.perf_counter()

        try:
            client = self._get_client()

            # Build messages
            messages = []
            system_prompt = None

            if isinstance(prompt, str):
                if config.system_prompt:
                    system_prompt = config.system_prompt
                messages.append({"role": "user", "content": prompt})
            else:
                for m in prompt:
                    if hasattr(m, 'role'):
                        role, content = m.role, m.content
                    else:
                        role, content = m.get("role", "user"), m.get("content", "")

                    if role == "system":
                        system_prompt = content
                    else:
                        messages.append({"role": role, "content": content})

            # Deterministic fallback: include seed hint in system prompt
            if config.seed is not None:
                seed_hint = f"\n\n[Determinism hint: seed={config.seed}]"
                if system_prompt:
                    system_prompt += seed_hint
                else:
                    system_prompt = f"You are a helpful assistant.{seed_hint}"

            # Build request kwargs
            request_kwargs = {
                "model": config.model or self.default_model,
                "max_tokens": config.max_tokens,
                "messages": messages,
            }

            # Temperature: force 0 for determinism when seed is set
            if config.seed is not None:
                request_kwargs["temperature"] = 0.0
            else:
                request_kwargs["temperature"] = config.temperature

            if system_prompt:
                request_kwargs["system"] = system_prompt

            if config.stop_sequences:
                request_kwargs["stop_sequences"] = config.stop_sequences

            # Make API call
            response = client.messages.create(**request_kwargs)

            latency_ms = int((time.perf_counter() - start) * 1000)

            # Extract content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, "text"):
                        content += block.text

            # Map stop reason
            stop_reason_map = {
                "end_turn": "end_turn",
                "max_tokens": "max_tokens",
                "stop_sequence": "stop_sequence",
            }
            finish_reason = stop_reason_map.get(response.stop_reason, "end_turn")

            return LLMResponse(
                content=content,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                model=response.model,
                finish_reason=finish_reason,
                latency_ms=latency_ms,
                seed=config.seed
            )

        except Exception as e:
            logger.warning(f"Claude API error: {e}", exc_info=True)
            return self._map_api_error(e)


# =============================================================================
# Registration
# =============================================================================

def register_claude_adapter():
    """Register Claude adapter with the adapter registry."""
    from app.skills.llm_invoke_v2 import register_adapter
    adapter = ClaudeAdapter()
    register_adapter(adapter)
    return adapter


# =============================================================================
# Stub for testing without API key
# =============================================================================

class ClaudeAdapterStub(ClaudeAdapter):
    """
    Stub version of ClaudeAdapter for testing without API access.

    Returns deterministic mock responses based on prompt hash.
    """

    def __init__(self):
        super().__init__(api_key="stub")
        self._mock_responses: Dict[str, Any] = {}

    def supports_seeding(self) -> bool:
        # Stub supports deterministic responses
        return True

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
            content = f"Claude stub response [{response_hash}]: {prompt_text[:40]}..."
        else:
            content = f"Claude stub response: {prompt_text[:40]}..."

        latency_ms = int((time.perf_counter() - start) * 1000) + 50

        return LLMResponse(
            content=content,
            input_tokens=self.estimate_tokens(prompt_text),
            output_tokens=self.estimate_tokens(content),
            model=config.model or self.default_model,
            finish_reason="end_turn",
            latency_ms=latency_ms,
            seed=config.seed
        )
