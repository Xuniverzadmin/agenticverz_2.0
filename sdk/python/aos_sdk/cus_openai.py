"""
Customer Integration OpenAI Provider

PURPOSE:
    OpenAI provider adapter that wraps the official OpenAI SDK to
    automatically capture telemetry for visibility and governance.

SEMANTIC:
    Phase 3 scope: VISIBILITY ONLY, NO CONTROL.

    Wraps OpenAI client to:
    1. Execute LLM calls via native OpenAI SDK
    2. Capture telemetry (tokens, cost, latency)
    3. Report telemetry to AOS

    Does NOT block, throttle, or enforce limits.

USAGE:
    from aos_sdk.cus_openai import CusOpenAIProvider

    # Create governed OpenAI provider
    provider = CusOpenAIProvider(
        api_key="sk-...",
        integration_key="tenant:integration:secret",
    )

    # Use like normal OpenAI client - telemetry captured automatically
    response = provider.chat_completions_create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}],
    )

    # Or access the native client directly
    native_response = provider.client.chat.completions.create(...)

SUPPORTED OPERATIONS:
    - chat_completions_create: Chat completions (most common)
    - completions_create: Legacy completions
    - embeddings_create: Embeddings

Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .cus_base import CusBaseProvider, CusProviderConfig, CusProviderError
from .cus_cost import calculate_cost
from .cus_token_counter import extract_openai_usage

logger = logging.getLogger(__name__)

# =============================================================================
# OPENAI SDK AVAILABILITY
# =============================================================================

try:
    from openai import OpenAI

    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore


# =============================================================================
# OPENAI PROVIDER
# =============================================================================


class CusOpenAIProvider(CusBaseProvider["OpenAI"]):
    """OpenAI provider adapter with automatic telemetry.

    Phase 3: VISIBILITY ONLY - captures and reports telemetry.
    No blocking, no throttling, no policy enforcement.

    Wraps the official OpenAI Python SDK to automatically capture
    usage telemetry for all LLM calls.

    Example:
        >>> provider = CusOpenAIProvider(
        ...     api_key="sk-...",
        ...     integration_key="tenant:integration:secret",
        ... )
        >>> response = provider.chat_completions_create(
        ...     model="gpt-4o",
        ...     messages=[{"role": "user", "content": "Hello"}],
        ... )
        >>> print(response.choices[0].message.content)
    """

    def __init__(
        self,
        api_key: str,
        config: Optional[CusProviderConfig] = None,
        organization: Optional[str] = None,
        base_url: Optional[str] = None,
        **client_kwargs,
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            config: Provider configuration
            organization: Optional OpenAI organization ID
            base_url: Optional custom base URL (for proxies)
            **client_kwargs: Additional arguments for OpenAI client
        """
        if not _OPENAI_AVAILABLE:
            raise CusProviderError(
                "OpenAI SDK not installed. Install with: pip install openai"
            )

        self._organization = organization
        self._base_url = base_url

        super().__init__(api_key, config, **client_kwargs)

    def _create_client(self, api_key: str, **kwargs) -> "OpenAI":
        """Create OpenAI client."""
        client_kwargs: Dict[str, Any] = {"api_key": api_key}

        if self._organization:
            client_kwargs["organization"] = self._organization
        if self._base_url:
            client_kwargs["base_url"] = self._base_url

        client_kwargs.update(kwargs)
        return OpenAI(**client_kwargs)

    def _get_provider_name(self) -> str:
        """Return provider name."""
        return "openai"

    def _extract_usage(self, response: Any) -> tuple[int, int]:
        """Extract token usage from OpenAI response."""
        return extract_openai_usage(response)

    def _calculate_cost(self, model: str, tokens_in: int, tokens_out: int) -> int:
        """Calculate cost for OpenAI model."""
        return calculate_cost(model, tokens_in, tokens_out)

    # =========================================================================
    # CHAT COMPLETIONS
    # =========================================================================

    def chat_completions_create(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        n: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """Create a chat completion with automatic telemetry.

        Args:
            model: Model to use (e.g., "gpt-4o", "gpt-4-turbo")
            messages: List of message dicts
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            stop: Stop sequences
            n: Number of completions to generate
            stream: Whether to stream response (not yet supported for telemetry)
            tools: List of tools/functions
            tool_choice: Tool choice strategy
            response_format: Response format specification
            seed: Random seed for reproducibility
            user: End-user identifier
            **kwargs: Additional arguments

        Returns:
            ChatCompletion response object

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
        }

        if temperature is not None:
            request_kwargs["temperature"] = temperature
        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens
        if top_p is not None:
            request_kwargs["top_p"] = top_p
        if frequency_penalty is not None:
            request_kwargs["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            request_kwargs["presence_penalty"] = presence_penalty
        if stop is not None:
            request_kwargs["stop"] = stop
        if n is not None:
            request_kwargs["n"] = n
        if stream:
            request_kwargs["stream"] = stream
        if tools is not None:
            request_kwargs["tools"] = tools
        if tool_choice is not None:
            request_kwargs["tool_choice"] = tool_choice
        if response_format is not None:
            request_kwargs["response_format"] = response_format
        if seed is not None:
            request_kwargs["seed"] = seed
        if user is not None:
            request_kwargs["user"] = user

        request_kwargs.update(kwargs)

        # Execute with telemetry
        def execute():
            return self._client.chat.completions.create(**request_kwargs)

        return self._execute_with_telemetry(model, execute)

    # =========================================================================
    # LEGACY COMPLETIONS
    # =========================================================================

    def completions_create(
        self,
        model: str,
        prompt: Union[str, List[str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        **kwargs,
    ) -> Any:
        """Create a completion (legacy API) with automatic telemetry.

        Args:
            model: Model to use
            prompt: Text prompt(s)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            n: Number of completions
            stop: Stop sequences
            presence_penalty: Presence penalty
            frequency_penalty: Frequency penalty
            **kwargs: Additional arguments

        Returns:
            Completion response object
        """
        request_kwargs: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
        }

        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens
        if temperature is not None:
            request_kwargs["temperature"] = temperature
        if top_p is not None:
            request_kwargs["top_p"] = top_p
        if n is not None:
            request_kwargs["n"] = n
        if stop is not None:
            request_kwargs["stop"] = stop
        if presence_penalty is not None:
            request_kwargs["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            request_kwargs["frequency_penalty"] = frequency_penalty

        request_kwargs.update(kwargs)

        def execute():
            return self._client.completions.create(**request_kwargs)

        return self._execute_with_telemetry(model, execute)

    # =========================================================================
    # EMBEDDINGS
    # =========================================================================

    def embeddings_create(
        self,
        model: str,
        input: Union[str, List[str]],
        encoding_format: Optional[str] = None,
        dimensions: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """Create embeddings with automatic telemetry.

        Args:
            model: Embedding model (e.g., "text-embedding-3-small")
            input: Text(s) to embed
            encoding_format: Output format ("float" or "base64")
            dimensions: Output dimensions (for models that support it)
            user: End-user identifier
            **kwargs: Additional arguments

        Returns:
            Embedding response object
        """
        request_kwargs: Dict[str, Any] = {
            "model": model,
            "input": input,
        }

        if encoding_format is not None:
            request_kwargs["encoding_format"] = encoding_format
        if dimensions is not None:
            request_kwargs["dimensions"] = dimensions
        if user is not None:
            request_kwargs["user"] = user

        request_kwargs.update(kwargs)

        def execute():
            return self._client.embeddings.create(**request_kwargs)

        # Embeddings have different usage format
        return self._execute_with_telemetry(model, execute)

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-4o",
        **kwargs,
    ) -> str:
        """Simple chat interface - returns just the response text.

        Args:
            messages: List of message dicts
            model: Model to use (default: gpt-4o)
            **kwargs: Additional arguments for chat_completions_create

        Returns:
            Response text content
        """
        response = self.chat_completions_create(
            model=model,
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    def complete(
        self,
        prompt: str,
        model: str = "gpt-4o",
        **kwargs,
    ) -> str:
        """Simple completion interface - returns just the response text.

        Args:
            prompt: Text prompt
            model: Model to use
            **kwargs: Additional arguments

        Returns:
            Response text content
        """
        # Use chat completions (more modern API)
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            **kwargs,
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_openai_provider(
    api_key: Optional[str] = None,
    integration_key: Optional[str] = None,
    **kwargs,
) -> CusOpenAIProvider:
    """Factory function to create an OpenAI provider.

    Args:
        api_key: OpenAI API key (or uses OPENAI_API_KEY env var)
        integration_key: AOS integration key (or uses CUS_INTEGRATION_KEY env var)
        **kwargs: Additional arguments for CusOpenAIProvider

    Returns:
        Configured CusOpenAIProvider
    """
    import os

    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise CusProviderError("OpenAI API key required")

    config = CusProviderConfig(
        integration_key=integration_key or os.getenv("CUS_INTEGRATION_KEY"),
    )

    return CusOpenAIProvider(api_key=api_key, config=config, **kwargs)
