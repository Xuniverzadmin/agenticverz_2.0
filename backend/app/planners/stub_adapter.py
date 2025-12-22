# Stub Planner Adapter
# Default fallback planner that returns a basic single-step plan

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.planners.stub")


class StubPlanner:
    """Stub planner for testing and fallback scenarios.

    Returns a simple single-step plan that directly executes the goal.
    """

    def __init__(self):
        logger.info("StubPlanner initialized (fallback mode)")

    def plan(
        self,
        agent_id: str,
        goal: str,
        context_summary: Optional[str] = None,
        memory_snippets: Optional[List[Dict[str, Any]]] = None,
        tool_manifest: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate a stub plan with a single step.

        Args:
            agent_id: The agent requesting the plan
            goal: The goal to accomplish
            context_summary: Optional context from previous runs
            memory_snippets: Optional relevant memories
            tool_manifest: Optional available tools

        Returns:
            A plan dict with steps array
        """
        logger.info(
            "Generating stub plan",
            extra={
                "agent_id": agent_id,
                "goal": goal[:100],
                "has_context": context_summary is not None,
                "memory_count": len(memory_snippets) if memory_snippets else 0,
                "tool_count": len(tool_manifest) if tool_manifest else 0,
            },
        )

        # Determine skill based on goal keywords
        skill = "http_call"  # Default skill
        skill_params = {"url": "https://api.github.com/zen", "method": "GET"}

        if tool_manifest:
            # Use first available tool if manifest provided
            available_skills = [t.get("name") for t in tool_manifest if t.get("name")]
            if available_skills:
                skill = available_skills[0]
                logger.debug(f"Using skill from manifest: {skill}")

        plan = {
            "plan_id": f"stub-{agent_id[:8]}",
            "agent_id": agent_id,
            "goal": goal,
            "planner": "stub",
            "steps": [
                {
                    "step_id": 1,
                    "description": f"Execute goal: {goal[:50]}",
                    "skill": skill,
                    "params": skill_params,
                    "depends_on": [],
                }
            ],
            "metadata": {"model": None, "tokens_used": 0, "latency_ms": 0},
        }

        logger.info("Stub plan generated", extra={"plan_id": plan["plan_id"], "step_count": len(plan["steps"])})

        return plan
