# NOVA Planner Adapters
# Provides pluggable planner backends (stub, anthropic, openai)

import os
import logging
from typing import Protocol, Dict, Any, List, Optional

logger = logging.getLogger("nova.planners")


class PlannerProtocol(Protocol):
    """Protocol for planner adapters."""

    def plan(
        self,
        agent_id: str,
        goal: str,
        context_summary: Optional[str] = None,
        memory_snippets: Optional[List[Dict[str, Any]]] = None,
        tool_manifest: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate a plan for the given goal."""
        ...


def get_planner() -> PlannerProtocol:
    """Factory function to get the configured planner backend."""
    backend = os.getenv("PLANNER_BACKEND", "stub").lower()

    if backend == "anthropic":
        from .anthropic_adapter import AnthropicPlanner
        api_key = os.getenv("ANTHROPIC_API_KEY")
        return AnthropicPlanner(api_key=api_key)
    elif backend == "openai":
        from .openai_adapter import OpenAIPlanner
        api_key = os.getenv("OPENAI_API_KEY")
        return OpenAIPlanner(api_key=api_key)
    else:
        from .stub_adapter import StubPlanner
        return StubPlanner()


__all__ = ["get_planner", "PlannerProtocol"]
