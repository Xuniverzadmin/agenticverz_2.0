"""
Customer Integration Anthropic Provider

PURPOSE:
    Anthropic provider adapter that wraps the official Anthropic SDK to
    automatically capture telemetry for visibility and governance.

SEMANTIC:
    Phase 3 scope: VISIBILITY ONLY, NO CONTROL.

    Wraps Anthropic client to:
    1. Execute LLM calls via native Anthropic SDK
    2. Capture telemetry (tokens, cost, latency)
    3. Report telemetry to AOS

    Does NOT block, throttle, or enforce limits.

USAGE:
    from aos_sdk.aos_sdk_cus_anthropic import CusAnthropicProvider

    # Create governed Anthropic provider
    provider = CusAnthropicProvider(
        api_key="sk-ant-...",
        integration_key="tenant:integration:secret",
    )

    # Use like normal Anthropic client - telemetry captured automatically
    response = provider.messages_create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=1024,
    )

    # Or access the native client directly
    native_response = provider.client.messages.create(...)

SUPPORTED OPERATIONS:
    - messages_create: Messages API (recommended)
    - messages_stream: Streaming messages (with estimated telemetry)

Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .aos_sdk_cus_base import CusBaseProvider, CusProviderConfig, CusProviderError
from .aos_sdk_cus_cost import calculate_cost
from .aos_sdk_cus_token_counter import extract_anthropic_usage

logger = logging.getLogger(__name__)

# =============================================================================
# ANTHROPIC SDK AVAILABILITY
# =============================================================================

try:
    from anthropic import Anthropic

    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False
    Anthropic = None  # type: ignore


# =============================================================================
# ANTHROPIC PROVIDER
# =============================================================================


class CusAnthropicProvider(CusBaseProvider["Anthropic"]):
    """Anthropic provider adapter with automatic telemetry.

    Phase 3: VISIBILITY ONLY - captures and reports telemetry.
    No blocking, no throttling, no policy enforcement.

    Wraps the official Anthropic Python SDK to automatically capture
    usage telemetry for all LLM calls.

    Example:
        >>> provider = CusAnthropicProvider(
        ...     api_key="sk-ant-...",
        ...     integration_key="tenant:integration:secret",
        ... )
        >>> response = provider.messages_create(
        ...     model="claude-sonnet-4-20250514",
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     max_tokens=1024,
        ... )
        >>> print(response.content[0].text)
    """

    def __init__(
        self,
        api_key: str,
        config: Optional[CusProviderConfig] = None,
        base_url: Optional[str] = None,
        **client_kwargs,
    ):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            config: Provider configuration
            base_url: Optional custom base URL (for proxies)
            **client_kwargs: Additional arguments for Anthropic client
        """
        if not _ANTHROPIC_AVAILABLE:
            raise CusProviderError(
                "Anthropic SDK not installed. Install with: pip install anthropic"
            )

        self._custom_base_url = base_url

        super().__init__(api_key, config, **client_kwargs)

    def _create_client(self, api_key: str, **kwargs) -> "Anthropic":
        """Create Anthropic client."""
        client_kwargs: Dict[str, Any] = {"api_key": api_key}

        if self._custom_base_url:
            client_kwargs["base_url"] = self._custom_base_url

        client_kwargs.update(kwargs)
        return Anthropic(**client_kwargs)

    def _get_provider_name(self) -> str:
        """Return provider name."""
        return "anthropic"

    def _extract_usage(self, response: Any) -> tuple[int, int]:
        """Extract token usage from Anthropic response."""
        return extract_anthropic_usage(response)

    def _calculate_cost(self, model: str, tokens_in: int, tokens_out: int) -> int:
        """Calculate cost for Anthropic model."""
        return calculate_cost(model, tokens_in, tokens_out)

    # =========================================================================
    # MESSAGES API
    # =========================================================================

    def messages_create(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """Create a message with automatic telemetry.

        Args:
            model: Model to use (e.g., "claude-sonnet-4-20250514")
            messages: List of message dicts
            max_tokens: Maximum tokens to generate (required)
            system: System prompt
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: Stop sequences
            stream: Whether to stream response (not yet supported for telemetry)
            tools: List of tools
            tool_choice: Tool choice specification
            metadata: Request metadata
            **kwargs: Additional arguments

        Returns:
            Message response object

        Note:
            Streaming is passed through but telemetry may be incomplete.
        """
        if stream:
            logger.warning(
                "Streaming enabled - telemetry will be reported with estimated tokens. "
                "For accurate telemetry, disable streaming or use track_stream()."
            )

        # Build request kwargs
        request_kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        if system is not None:
            request_kwargs["system"] = system
        if temperature is not None:
            request_kwargs["temperature"] = temperature
        if top_p is not None:
            request_kwargs["top_p"] = top_p
        if top_k is not None:
            request_kwargs["top_k"] = top_k
        if stop_sequences is not None:
            request_kwargs["stop_sequences"] = stop_sequences
        if stream:
            request_kwargs["stream"] = stream
        if tools is not None:
            request_kwargs["tools"] = tools
        if tool_choice is not None:
            request_kwargs["tool_choice"] = tool_choice
        if metadata is not None:
            request_kwargs["metadata"] = metadata

        request_kwargs.update(kwargs)

        # Execute with telemetry
        def execute():
            return self._client.messages.create(**request_kwargs)

        return self._execute_with_telemetry(model, execute)

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        system: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Simple chat interface - returns just the response text.

        Args:
            messages: List of message dicts
            model: Model to use (default: claude-sonnet-4)
            max_tokens: Maximum tokens (default: 4096)
            system: System prompt
            **kwargs: Additional arguments for messages_create

        Returns:
            Response text content
        """
        response = self.messages_create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            system=system,
            **kwargs,
        )

        # Extract text from content blocks
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
            elif isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))

        return "".join(text_parts)

    def complete(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        system: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Simple completion interface - returns just the response text.

        Args:
            prompt: User prompt
            model: Model to use
            max_tokens: Maximum tokens
            system: System prompt
            **kwargs: Additional arguments

        Returns:
            Response text content
        """
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=max_tokens,
            system=system,
            **kwargs,
        )

    def ask(
        self,
        question: str,
        context: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ) -> str:
        """Ask a question with optional context.

        Args:
            question: The question to ask
            context: Optional context/background information
            model: Model to use
            max_tokens: Maximum tokens

        Returns:
            Response text
        """
        if context:
            prompt = f"Context:\n{context}\n\nQuestion: {question}"
        else:
            prompt = question

        return self.complete(prompt, model=model, max_tokens=max_tokens)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_anthropic_provider(
    api_key: Optional[str] = None,
    integration_key: Optional[str] = None,
    **kwargs,
) -> CusAnthropicProvider:
    """Factory function to create an Anthropic provider.

    Args:
        api_key: Anthropic API key (or uses ANTHROPIC_API_KEY env var)
        integration_key: AOS integration key (or uses CUS_INTEGRATION_KEY env var)
        **kwargs: Additional arguments for CusAnthropicProvider

    Returns:
        Configured CusAnthropicProvider
    """
    import os

    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise CusProviderError("Anthropic API key required")

    config = CusProviderConfig(
        integration_key=integration_key or os.getenv("CUS_INTEGRATION_KEY"),
    )

    return CusAnthropicProvider(api_key=api_key, config=config, **kwargs)
