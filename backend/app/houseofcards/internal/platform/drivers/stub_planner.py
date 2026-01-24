# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Stub planner for testing
# Callers: planner interface (test mode)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: LLM Integration

# planner/stub_planner.py
"""
Stub Planner (M2.5)

Rule-based deterministic planner for testing.
Implements PlannerInterface from interface.py.

Key features:
1. Full determinism - same inputs always produce identical plans
2. Rule-based planning using keyword matching
3. Supports all PlannerInterface methods
4. Zero-cost planning (no LLM calls)
5. Perfect for unit tests and golden file comparisons

See: app/specs/planner_determinism.md for full specification.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add parent to path for imports
_parent_path = str(Path(__file__).parent.parent)
if _parent_path not in sys.path:
    sys.path.insert(0, _parent_path)

# Direct import to avoid circular dependency through __init__.py
from planner.interface import (
    DeterminismMode,
    PlanMetadata,
    PlannerError,
    PlannerErrorCode,
    PlannerInterface,
    PlannerOutput,
    PlanStep,
    normalize_goal,
)


@dataclass
class PlanRule:
    """A rule for generating plans based on goal keywords."""

    keywords: List[str]  # Keywords to match in goal
    steps: List[PlanStep]  # Steps to include if matched
    priority: int = 0  # Higher priority rules checked first


class StubPlanner(PlannerInterface):
    """
    Rule-based stub planner for testing.

    Provides full determinism - same inputs always produce identical plans.
    Uses keyword matching to select appropriate skills.

    Usage:
        planner = StubPlanner()
        result = planner.plan(
            agent_id="test-agent",
            goal="Fetch user data from API",
            tool_manifest=[{"skill_id": "skill.http_call", ...}]
        )
    """

    VERSION = "1.0.0"

    def __init__(self, rules: Optional[List[PlanRule]] = None):
        """
        Initialize stub planner with optional custom rules.

        Args:
            rules: Custom planning rules (uses defaults if None)
        """
        self.rules = rules or self._default_rules()
        self._call_history: List[Dict[str, Any]] = []

    @property
    def planner_id(self) -> str:
        """Unique identifier for this planner."""
        return "stub"

    @property
    def version(self) -> str:
        """Planner version."""
        return self.VERSION

    def get_determinism_mode(self) -> DeterminismMode:
        """Return FULL determinism - same inputs produce identical outputs."""
        return DeterminismMode.FULL

    def _default_rules(self) -> List[PlanRule]:
        """Create default planning rules."""
        return [
            # Echo rule
            PlanRule(
                keywords=["echo", "say", "print", "output"],
                steps=[PlanStep(step_id="s1", skill="skill.echo", params={"message": "{{goal}}"})],
                priority=1,
            ),
            # HTTP fetch rule
            PlanRule(
                keywords=["fetch", "http", "api", "get", "request"],
                steps=[PlanStep(step_id="s1", skill="skill.http_call", params={"url": "{{url}}", "method": "GET"})],
                priority=2,
            ),
            # Analyze rule (multi-step)
            PlanRule(
                keywords=["analyze", "summarize", "explain"],
                steps=[
                    PlanStep(
                        step_id="s1",
                        skill="skill.http_call",
                        params={"url": "{{url}}", "method": "GET"},
                        description="Fetch data",
                    ),
                    PlanStep(
                        step_id="s2",
                        skill="skill.json_transform",
                        params={"data": "{{s1.body}}", "operation": "extract", "path": "$.data"},
                        depends_on=["s1"],
                        description="Extract data",
                    ),
                    PlanStep(
                        step_id="s3",
                        skill="skill.llm_invoke",
                        params={"prompt": "Analyze: {{s2.output}}"},
                        depends_on=["s2"],
                        description="Analyze data",
                    ),
                ],
                priority=3,
            ),
            # Transform rule
            PlanRule(
                keywords=["transform", "extract", "filter", "pick"],
                steps=[
                    PlanStep(
                        step_id="s1",
                        skill="skill.json_transform",
                        params={"data": "{{data}}", "operation": "{{operation}}", "path": "{{path}}"},
                    )
                ],
                priority=2,
            ),
            # LLM rule
            PlanRule(
                keywords=["llm", "chat", "generate", "write", "compose"],
                steps=[
                    PlanStep(
                        step_id="s1", skill="skill.llm_invoke", params={"prompt": "{{goal}}", "model": "stub-model"}
                    )
                ],
                priority=2,
            ),
        ]

    def _match_rule(self, goal: str) -> Optional[PlanRule]:
        """Find the best matching rule for a goal."""
        goal_lower = normalize_goal(goal).lower()

        matched_rules = []
        for rule in self.rules:
            if any(kw in goal_lower for kw in rule.keywords):
                matched_rules.append(rule)

        if not matched_rules:
            return None

        # Return highest priority match
        return max(matched_rules, key=lambda r: r.priority)

    def _compute_cache_key(
        self, agent_id: str, goal: str, context_summary: Optional[str], tool_manifest: Optional[List[Dict]]
    ) -> str:
        """Compute deterministic cache key for plan inputs."""
        import json

        data = {
            "agent_id": agent_id,
            "goal": normalize_goal(goal),
            "context": context_summary,
            "manifest": tool_manifest,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def _filter_steps_by_manifest(self, steps: List[PlanStep], tool_manifest: Optional[List[Dict]]) -> List[PlanStep]:
        """Filter steps to only include skills available in manifest."""
        if not tool_manifest:
            return steps  # No filtering if no manifest

        available_skills = {t.get("skill_id") for t in tool_manifest}
        return [s for s in steps if s.skill in available_skills]

    def _substitute_params(
        self, steps: List[PlanStep], goal: str, context: Optional[Dict[str, Any]] = None
    ) -> List[PlanStep]:
        """Substitute {{placeholders}} in step params."""
        context = context or {}

        def substitute(value: Any) -> Any:
            if isinstance(value, str):
                result = value
                result = result.replace("{{goal}}", goal)
                result = result.replace("{{url}}", context.get("url", "https://example.com"))
                result = result.replace("{{data}}", str(context.get("data", {})))
                result = result.replace("{{operation}}", context.get("operation", "extract"))
                result = result.replace("{{path}}", context.get("path", "$.data"))
                return result
            elif isinstance(value, dict):
                return {k: substitute(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute(v) for v in value]
            return value

        return [
            PlanStep(
                step_id=s.step_id,
                skill=s.skill,
                params=substitute(s.params),
                depends_on=s.depends_on,
                on_error=s.on_error,
                retry_count=s.retry_count,
                output_key=s.output_key,
                description=s.description,
            )
            for s in steps
        ]

    def plan(
        self,
        agent_id: str,
        goal: str,
        context_summary: Optional[str] = None,
        memory_snippets: Optional[List[Dict[str, Any]]] = None,
        tool_manifest: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Union[PlannerOutput, PlannerError]:
        """
        Generate a deterministic plan based on goal keywords.

        Args:
            agent_id: ID of the requesting agent
            goal: Natural language goal
            context_summary: Optional context (unused in stub)
            memory_snippets: Optional memories (unused in stub)
            tool_manifest: Available skills

        Returns:
            PlannerOutput with steps, or PlannerError if planning fails
        """
        # Record call for testing
        self._call_history.append(
            {"agent_id": agent_id, "goal": goal, "timestamp": datetime.now(timezone.utc).isoformat()}
        )

        # Validate input
        normalized_goal = normalize_goal(goal)
        if not normalized_goal:
            return PlannerError(code=PlannerErrorCode.INVALID_GOAL, message="Goal cannot be empty", retryable=False)

        # Find matching rule
        rule = self._match_rule(normalized_goal)
        if not rule:
            return PlannerError(
                code=PlannerErrorCode.GENERATION_FAILED,
                message=f"No matching rule for goal: {goal}",
                retryable=False,
                details={"goal": normalized_goal},
            )

        # Get steps from rule
        steps = list(rule.steps)  # Copy to avoid modifying original

        # Filter by available skills
        steps = self._filter_steps_by_manifest(steps, tool_manifest)
        if not steps:
            return PlannerError(
                code=PlannerErrorCode.NO_SKILLS_AVAILABLE,
                message="No available skills match the required plan",
                retryable=False,
                details={"required_skills": [s.skill for s in rule.steps]},
            )

        # Substitute parameters
        context = kwargs.get("context", {})
        steps = self._substitute_params(steps, normalized_goal, context)

        # Build metadata
        cache_key = self._compute_cache_key(agent_id, goal, context_summary, tool_manifest)

        metadata = PlanMetadata(
            planner=self.planner_id,
            planner_version=self.version,
            model=None,  # No model for stub
            input_tokens=0,
            output_tokens=0,
            cost_cents=0,
            deterministic=True,
            cache_key=cache_key,
        )

        return PlannerOutput(steps=steps, metadata=metadata, warnings=[])

    def add_rule(self, rule: PlanRule) -> None:
        """Add a custom planning rule."""
        self.rules.append(rule)

    def clear_rules(self) -> None:
        """Clear all rules (for testing)."""
        self.rules.clear()

    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get call history for verification."""
        return self._call_history.copy()

    def reset(self) -> None:
        """Reset planner state."""
        self._call_history.clear()


# =============================================================================
# Backwards Compatibility Layer
# =============================================================================


class LegacyStubPlanner:
    """
    Legacy stub planner interface for backwards compatibility.

    Wraps the new StubPlanner to provide the old interface used by runner.py
    """

    def __init__(self):
        self._planner = StubPlanner()

    def plan(
        self,
        agent_id: str,
        goal: str,
        context_summary: Optional[str] = None,
        memory_snippets: Optional[List[Dict[str, Any]]] = None,
        tool_manifest: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a plan (legacy interface).

        Returns dict with "steps" and "metadata" keys.
        """
        result = self._planner.plan(
            agent_id=agent_id,
            goal=goal,
            context_summary=context_summary,
            memory_snippets=memory_snippets,
            tool_manifest=tool_manifest,
        )

        if isinstance(result, PlannerError):
            # Return empty plan on error (legacy behavior)
            return {"steps": [], "metadata": {"planner": "stub", "error": result.code, "error_message": result.message}}

        return result.plan


# =============================================================================
# Example Usage
# =============================================================================


async def example_stub_planner_usage():
    """Example demonstrating stub planner usage."""
    planner = StubPlanner()

    # Test manifest
    manifest = [
        {"skill_id": "skill.http_call", "name": "HTTP Call"},
        {"skill_id": "skill.json_transform", "name": "JSON Transform"},
        {"skill_id": "skill.llm_invoke", "name": "LLM Invoke"},
    ]

    # Generate plan
    result = planner.plan(agent_id="test-agent", goal="Fetch user data and analyze it", tool_manifest=manifest)

    if isinstance(result, PlannerOutput):
        print(f"Plan generated with {len(result.steps)} steps")
        print(f"Deterministic: {result.metadata.deterministic}")
        print(f"Cache key: {result.metadata.cache_key}")
        for step in result.steps:
            print(f"  - {step.step_id}: {step.skill}")
    else:
        print(f"Planning failed: {result.code} - {result.message}")

    return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_stub_planner_usage())
