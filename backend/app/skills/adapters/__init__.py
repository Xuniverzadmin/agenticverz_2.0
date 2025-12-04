# adapters/__init__.py
"""
LLM Adapters Package

Provides adapter implementations for different LLM providers.

Available Adapters:
- ClaudeAdapter: Anthropic Claude API
- ClaudeAdapterStub: Mock Claude adapter for testing
"""

from typing import TYPE_CHECKING

# Lazy imports to avoid loading anthropic SDK at import time
if TYPE_CHECKING:
    from .claude_adapter import ClaudeAdapter, ClaudeAdapterStub

_loaded = {}


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


def register_all_adapters():
    """Register all adapters with the llm_invoke adapter registry."""
    from .claude_adapter import register_claude_adapter
    register_claude_adapter()


__all__ = [
    "get_claude_adapter",
    "get_claude_stub",
    "register_all_adapters",
]
