"""
Customer Integration Token Counter

PURPOSE:
    Model-aware token counting for LLM providers. Provides accurate
    token estimation before calls and extraction from responses.

SEMANTIC:
    Token counting is FACTUAL - it must be accurate for billing.
    This module provides:
    1. Pre-call token estimation (for budget checking in Phase 5)
    2. Post-call token extraction from responses
    3. Model-specific tokenizer selection

SUPPORTED PROVIDERS:
    - OpenAI: GPT-4, GPT-4o, GPT-3.5-turbo (tiktoken)
    - Anthropic: Claude 3/4 family (approximation)
    - Azure OpenAI: Same as OpenAI

USAGE:
    from aos_sdk.aos_sdk_cus_token_counter import (
        count_tokens,
        estimate_tokens,
        get_tokenizer,
    )

    # Estimate tokens for a prompt
    tokens = estimate_tokens("Hello, world!", model="gpt-4")

    # Count tokens in messages
    tokens = count_tokens(
        messages=[{"role": "user", "content": "Hello"}],
        model="claude-sonnet-4-20250514"
    )

Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# =============================================================================
# TOKENIZER AVAILABILITY
# =============================================================================

# Try to import tiktoken for OpenAI models
try:
    import tiktoken

    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False
    tiktoken = None  # type: ignore


# =============================================================================
# ENUMS
# =============================================================================


class CusTokenizerType(str, Enum):
    """Tokenizer types for different providers."""

    TIKTOKEN_CL100K = "tiktoken_cl100k"  # GPT-4, GPT-4o
    TIKTOKEN_P50K = "tiktoken_p50k"  # GPT-3.5, older models
    TIKTOKEN_O200K = "tiktoken_o200k"  # o1, o1-mini
    ANTHROPIC_APPROX = "anthropic_approx"  # Claude models (approximation)
    CHAR_APPROX = "char_approx"  # Fallback character-based approximation


# =============================================================================
# MODEL REGISTRY
# =============================================================================


@dataclass
class CusModelInfo:
    """Information about an LLM model for token counting.

    Attributes:
        provider: Provider name
        model_family: Model family (e.g., "gpt-4", "claude-3")
        tokenizer: Tokenizer type to use
        context_window: Maximum context window size
        chars_per_token: Average characters per token (for approximation)
    """

    provider: str
    model_family: str
    tokenizer: CusTokenizerType
    context_window: int
    chars_per_token: float = 4.0


# Model registry - maps model name patterns to model info
_MODEL_REGISTRY: Dict[str, CusModelInfo] = {
    # OpenAI GPT-4o family
    "gpt-4o": CusModelInfo("openai", "gpt-4o", CusTokenizerType.TIKTOKEN_CL100K, 128000, 4.0),
    "gpt-4o-mini": CusModelInfo("openai", "gpt-4o-mini", CusTokenizerType.TIKTOKEN_CL100K, 128000, 4.0),
    # OpenAI GPT-4 family
    "gpt-4-turbo": CusModelInfo("openai", "gpt-4-turbo", CusTokenizerType.TIKTOKEN_CL100K, 128000, 4.0),
    "gpt-4": CusModelInfo("openai", "gpt-4", CusTokenizerType.TIKTOKEN_CL100K, 8192, 4.0),
    "gpt-4-32k": CusModelInfo("openai", "gpt-4-32k", CusTokenizerType.TIKTOKEN_CL100K, 32768, 4.0),
    # OpenAI GPT-3.5 family
    "gpt-3.5-turbo": CusModelInfo("openai", "gpt-3.5-turbo", CusTokenizerType.TIKTOKEN_CL100K, 16385, 4.0),
    "gpt-3.5-turbo-16k": CusModelInfo("openai", "gpt-3.5-turbo", CusTokenizerType.TIKTOKEN_CL100K, 16385, 4.0),
    # OpenAI o1 family
    "o1": CusModelInfo("openai", "o1", CusTokenizerType.TIKTOKEN_O200K, 200000, 4.0),
    "o1-mini": CusModelInfo("openai", "o1-mini", CusTokenizerType.TIKTOKEN_O200K, 128000, 4.0),
    "o1-preview": CusModelInfo("openai", "o1-preview", CusTokenizerType.TIKTOKEN_O200K, 128000, 4.0),
    # Anthropic Claude 4 family
    "claude-opus-4": CusModelInfo("anthropic", "claude-4", CusTokenizerType.ANTHROPIC_APPROX, 200000, 3.5),
    "claude-sonnet-4": CusModelInfo("anthropic", "claude-4", CusTokenizerType.ANTHROPIC_APPROX, 200000, 3.5),
    # Anthropic Claude 3.5 family
    "claude-3-5-sonnet": CusModelInfo("anthropic", "claude-3.5", CusTokenizerType.ANTHROPIC_APPROX, 200000, 3.5),
    "claude-3-5-haiku": CusModelInfo("anthropic", "claude-3.5", CusTokenizerType.ANTHROPIC_APPROX, 200000, 3.5),
    # Anthropic Claude 3 family
    "claude-3-opus": CusModelInfo("anthropic", "claude-3", CusTokenizerType.ANTHROPIC_APPROX, 200000, 3.5),
    "claude-3-sonnet": CusModelInfo("anthropic", "claude-3", CusTokenizerType.ANTHROPIC_APPROX, 200000, 3.5),
    "claude-3-haiku": CusModelInfo("anthropic", "claude-3", CusTokenizerType.ANTHROPIC_APPROX, 200000, 3.5),
}

# Default model info for unknown models
_DEFAULT_MODEL_INFO = CusModelInfo("unknown", "unknown", CusTokenizerType.CHAR_APPROX, 8192, 4.0)


def get_model_info(model: str) -> CusModelInfo:
    """Get model information for a given model name.

    Args:
        model: Model name or identifier

    Returns:
        CusModelInfo for the model
    """
    model_lower = model.lower()

    # Exact match first
    if model_lower in _MODEL_REGISTRY:
        return _MODEL_REGISTRY[model_lower]

    # Prefix match (handles versioned models like "gpt-4o-2024-08-06")
    for pattern, info in _MODEL_REGISTRY.items():
        if model_lower.startswith(pattern):
            return info

    # Partial match for Anthropic models with dates
    for pattern, info in _MODEL_REGISTRY.items():
        if pattern in model_lower:
            return info

    logger.warning(f"Unknown model '{model}', using default token estimation")
    return _DEFAULT_MODEL_INFO


# =============================================================================
# TOKENIZER CACHE
# =============================================================================

_tokenizer_cache: Dict[str, Any] = {}


def _get_tiktoken_encoding(encoding_name: str) -> Optional[Any]:
    """Get a tiktoken encoding, with caching."""
    if not _TIKTOKEN_AVAILABLE:
        return None

    if encoding_name not in _tokenizer_cache:
        try:
            _tokenizer_cache[encoding_name] = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load tiktoken encoding '{encoding_name}': {e}")
            return None

    return _tokenizer_cache[encoding_name]


def get_tokenizer(model: str) -> Optional[Any]:
    """Get the appropriate tokenizer for a model.

    Args:
        model: Model name

    Returns:
        Tokenizer object or None if not available
    """
    info = get_model_info(model)

    if info.tokenizer == CusTokenizerType.TIKTOKEN_CL100K:
        return _get_tiktoken_encoding("cl100k_base")
    elif info.tokenizer == CusTokenizerType.TIKTOKEN_P50K:
        return _get_tiktoken_encoding("p50k_base")
    elif info.tokenizer == CusTokenizerType.TIKTOKEN_O200K:
        return _get_tiktoken_encoding("o200k_base")

    return None


# =============================================================================
# TOKEN COUNTING
# =============================================================================


def count_text_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in a text string.

    Args:
        text: Text to count tokens for
        model: Model to use for tokenization

    Returns:
        Number of tokens
    """
    info = get_model_info(model)

    # Try tiktoken first
    tokenizer = get_tokenizer(model)
    if tokenizer is not None:
        try:
            return len(tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Tiktoken encoding failed: {e}, falling back to approximation")

    # Anthropic approximation (Claude uses a different tokenizer, ~3.5 chars/token)
    if info.tokenizer == CusTokenizerType.ANTHROPIC_APPROX:
        return int(len(text) / info.chars_per_token)

    # Fallback: character approximation (~4 chars per token for English)
    return int(len(text) / info.chars_per_token)


def count_message_tokens(
    messages: List[Dict[str, Any]],
    model: str = "gpt-4",
) -> int:
    """Count tokens in a list of chat messages.

    Accounts for message formatting overhead.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use for tokenization

    Returns:
        Number of tokens
    """
    info = get_model_info(model)
    total_tokens = 0

    # Message overhead varies by model
    # GPT-4/3.5: ~4 tokens per message for role/formatting
    # Claude: ~3 tokens per message
    if info.provider == "openai":
        message_overhead = 4
    elif info.provider == "anthropic":
        message_overhead = 3
    else:
        message_overhead = 4

    for message in messages:
        # Add message overhead
        total_tokens += message_overhead

        # Count content tokens
        content = message.get("content", "")
        if isinstance(content, str):
            total_tokens += count_text_tokens(content, model)
        elif isinstance(content, list):
            # Handle multimodal content (text + images)
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        total_tokens += count_text_tokens(part.get("text", ""), model)
                    elif part.get("type") == "image_url":
                        # Images have fixed token costs (approximation)
                        # OpenAI: varies by resolution, ~85-1105 tokens
                        # Using average estimate
                        total_tokens += 300
                elif isinstance(part, str):
                    total_tokens += count_text_tokens(part, model)

        # Count name tokens if present
        if "name" in message:
            total_tokens += count_text_tokens(message["name"], model)
            total_tokens += 1  # Name separator

    # Reply priming (model needs tokens to start response)
    total_tokens += 3

    return total_tokens


def estimate_tokens(
    content: Union[str, List[Dict[str, Any]]],
    model: str = "gpt-4",
) -> int:
    """Estimate tokens for content (text or messages).

    Args:
        content: Text string or list of messages
        model: Model to use for tokenization

    Returns:
        Estimated number of tokens
    """
    if isinstance(content, str):
        return count_text_tokens(content, model)
    elif isinstance(content, list):
        return count_message_tokens(content, model)
    else:
        # Fallback: convert to string
        return count_text_tokens(str(content), model)


def count_tokens(
    messages: Optional[List[Dict[str, Any]]] = None,
    prompt: Optional[str] = None,
    model: str = "gpt-4",
) -> int:
    """Count tokens for messages or prompt.

    Args:
        messages: Chat messages (for chat completions)
        prompt: Raw prompt (for completions)
        model: Model to use for tokenization

    Returns:
        Number of tokens
    """
    if messages:
        return count_message_tokens(messages, model)
    elif prompt:
        return count_text_tokens(prompt, model)
    else:
        return 0


# =============================================================================
# RESPONSE TOKEN EXTRACTION
# =============================================================================


def extract_openai_usage(response: Any) -> tuple[int, int]:
    """Extract token usage from an OpenAI response.

    Args:
        response: OpenAI API response object

    Returns:
        Tuple of (prompt_tokens, completion_tokens)
    """
    try:
        # Chat completions response
        if hasattr(response, "usage") and response.usage:
            return (
                response.usage.prompt_tokens or 0,
                response.usage.completion_tokens or 0,
            )

        # Dict response (from raw API)
        if isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            return (
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
            )

    except Exception as e:
        logger.warning(f"Failed to extract OpenAI usage: {e}")

    return (0, 0)


def extract_anthropic_usage(response: Any) -> tuple[int, int]:
    """Extract token usage from an Anthropic response.

    Args:
        response: Anthropic API response object

    Returns:
        Tuple of (input_tokens, output_tokens)
    """
    try:
        # Message response
        if hasattr(response, "usage") and response.usage:
            return (
                response.usage.input_tokens or 0,
                response.usage.output_tokens or 0,
            )

        # Dict response
        if isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            return (
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
            )

    except Exception as e:
        logger.warning(f"Failed to extract Anthropic usage: {e}")

    return (0, 0)


def extract_usage(response: Any, provider: str) -> tuple[int, int]:
    """Extract token usage from a provider response.

    Args:
        response: API response object
        provider: Provider name ('openai', 'anthropic', etc.)

    Returns:
        Tuple of (input_tokens, output_tokens)
    """
    provider_lower = provider.lower()

    if provider_lower in ("openai", "azure_openai", "azure"):
        return extract_openai_usage(response)
    elif provider_lower == "anthropic":
        return extract_anthropic_usage(response)
    else:
        # Try OpenAI format first, then Anthropic
        tokens_in, tokens_out = extract_openai_usage(response)
        if tokens_in == 0 and tokens_out == 0:
            tokens_in, tokens_out = extract_anthropic_usage(response)
        return (tokens_in, tokens_out)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_context_window(model: str) -> int:
    """Get the context window size for a model.

    Args:
        model: Model name

    Returns:
        Context window size in tokens
    """
    return get_model_info(model).context_window


def is_within_context_window(
    tokens: int,
    model: str,
    reserve_output: int = 4096,
) -> bool:
    """Check if token count fits within context window.

    Args:
        tokens: Input token count
        model: Model name
        reserve_output: Tokens to reserve for output

    Returns:
        True if tokens fit within context window
    """
    window = get_context_window(model)
    return tokens + reserve_output <= window


def tiktoken_available() -> bool:
    """Check if tiktoken is available for accurate token counting."""
    return _TIKTOKEN_AVAILABLE
