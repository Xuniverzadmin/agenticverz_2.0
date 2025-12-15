# adapters/__init__.py
"""
LLM Adapters Package (M11)

Provides adapter implementations for different LLM providers with
environment-based factory selection.

Available Adapters:
- ClaudeAdapter: Anthropic Claude API (default)
- OpenAIAdapter: OpenAI API (cost-effective fallback)
- StubAdapter: Deterministic testing

STRICT MODE (ENV=prod or ENV=production):
- Raises AdapterConfigurationError instead of falling back to stub
- Ensures production deployments never silently degrade

Environment Variables:
- ENV: environment mode (prod|production enables strict mode)
- LLM_ADAPTER: claude|openai|stub (default: claude)
- ANTHROPIC_API_KEY: Required for claude adapter (from Vault)
- OPENAI_API_KEY: Required for openai adapter (from Vault)
"""

import os
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.skills.llm_invoke_v2 import LLMAdapter

logger = logging.getLogger("nova.adapters")

_loaded = {}
_adapter_instance: Optional["LLMAdapter"] = None


class AdapterConfigurationError(Exception):
    """Raised when adapter configuration is invalid in strict mode (ENV=prod)."""
    pass


def _is_strict_mode() -> bool:
    """Check if we're in strict production mode."""
    env = os.getenv("ENV", "").lower()
    return env in ("prod", "production")


def _strict_fail(message: str) -> None:
    """Raise error in strict mode, or log warning in dev mode."""
    if _is_strict_mode():
        raise AdapterConfigurationError(f"[STRICT MODE] {message}")
    logger.warning(message)


# =============================================================================
# Main Factory Function
# =============================================================================

def get_llm_adapter(force_new: bool = False) -> "LLMAdapter":
    """
    Get or create LLM adapter based on environment configuration.

    This is the primary factory function for obtaining an LLM adapter.
    It supports automatic fallback to stub if credentials are missing.

    Args:
        force_new: Force creation of new instance (for testing)

    Returns:
        LLMAdapter implementation

    Environment:
        LLM_ADAPTER: 'claude', 'openai', or 'stub' (default: claude)
        ANTHROPIC_API_KEY: Required for claude adapter
        OPENAI_API_KEY: Required for openai adapter
    """
    global _adapter_instance

    if _adapter_instance is not None and not force_new:
        return _adapter_instance

    adapter_type = os.getenv("LLM_ADAPTER", "claude").lower()

    if adapter_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            _strict_fail("LLM_ADAPTER=openai but OPENAI_API_KEY not set, falling back to stub")
            adapter_type = "stub"
        else:
            try:
                from app.skills.adapters.openai_adapter import OpenAIAdapter
                _adapter_instance = OpenAIAdapter(api_key=api_key)
                logger.info("Using OpenAIAdapter")
                return _adapter_instance
            except ImportError as e:
                _strict_fail(f"OpenAI adapter import failed: {e}, cannot use OpenAIAdapter")
                adapter_type = "stub"

    elif adapter_type == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            _strict_fail("LLM_ADAPTER=claude but ANTHROPIC_API_KEY not set, falling back to stub")
            adapter_type = "stub"
        else:
            try:
                from app.skills.adapters.claude_adapter import ClaudeAdapter
                _adapter_instance = ClaudeAdapter(api_key=api_key)
                logger.info("Using ClaudeAdapter (Anthropic)")
                return _adapter_instance
            except ImportError as e:
                _strict_fail(f"Claude adapter import failed: {e}, cannot use ClaudeAdapter")
                adapter_type = "stub"

    # Fallback to stub (blocked in strict mode unless explicitly requested)
    if _is_strict_mode() and adapter_type != "stub":
        raise AdapterConfigurationError(
            "[STRICT MODE] Cannot use StubAdapter in production. "
            "Set ANTHROPIC_API_KEY/OPENAI_API_KEY or explicitly set LLM_ADAPTER=stub to acknowledge."
        )

    from app.skills.llm_invoke_v2 import StubAdapter
    _adapter_instance = StubAdapter()
    logger.info("Using StubAdapter (testing mode)")
    return _adapter_instance


def reset_adapter():
    """Reset cached adapter instance. For testing only."""
    global _adapter_instance
    _adapter_instance = None
    _loaded.clear()
    logger.debug("LLM adapter instance reset")


# =============================================================================
# Legacy Functions (backwards compatibility)
# =============================================================================

def get_claude_adapter():
    """Get or create ClaudeAdapter instance."""
    if "claude" not in _loaded:
        from .claude_adapter import ClaudeAdapter
        _loaded["claude"] = ClaudeAdapter()
    return _loaded["claude"]


def get_claude_stub():
    """Get or create ClaudeAdapterStub instance."""
    if "claude_stub" not in _loaded:
        from .claude_adapter import ClaudeAdapterStub
        _loaded["claude_stub"] = ClaudeAdapterStub()
    return _loaded["claude_stub"]


def get_openai_adapter():
    """Get or create OpenAIAdapter instance."""
    if "openai" not in _loaded:
        from .openai_adapter import OpenAIAdapter
        _loaded["openai"] = OpenAIAdapter()
    return _loaded["openai"]


def register_all_adapters():
    """Register all adapters with the llm_invoke adapter registry."""
    from .claude_adapter import register_claude_adapter
    register_claude_adapter()
    # OpenAI adapter registration can be added here


__all__ = [
    "get_llm_adapter",
    "reset_adapter",
    "get_claude_adapter",
    "get_claude_stub",
    "get_openai_adapter",
    "register_all_adapters",
    "AdapterConfigurationError",
]
