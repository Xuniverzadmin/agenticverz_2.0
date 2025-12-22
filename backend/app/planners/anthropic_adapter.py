# Anthropic Planner Adapter
# Uses Claude API for intelligent plan generation with proper Plan schema output

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.planners.anthropic")

# Default model - Claude Sonnet for good balance of speed/quality
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class AnthropicPlanner:
    """Anthropic Claude-based planner for intelligent plan generation.

    Generates structured plans conforming to the Plan schema using
    Claude's API with structured output guidance.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ):
        """Initialize the Anthropic planner.

        Args:
            api_key: Anthropic API key (required for real calls)
            model: Model to use for planning
            max_tokens: Maximum tokens for plan generation
            temperature: Sampling temperature (lower = more focused)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

        if self.api_key:
            logger.info("AnthropicPlanner initialized", extra={"model": model, "key_prefix": self.api_key[:8] + "..."})
        else:
            logger.warning("AnthropicPlanner: No API key - will use stub responses")

    def _get_client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None and self.api_key:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.error("anthropic package not installed - pip install anthropic")
                raise ImportError("anthropic package required: pip install anthropic")
        return self._client

    def plan(
        self,
        agent_id: str,
        goal: str,
        context_summary: Optional[str] = None,
        memory_snippets: Optional[List[Dict[str, Any]]] = None,
        tool_manifest: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate an intelligent plan using Claude.

        Args:
            agent_id: The agent requesting the plan
            goal: The goal to accomplish
            context_summary: Optional context from previous runs
            memory_snippets: Optional relevant memories
            tool_manifest: Optional available skills

        Returns:
            A plan dict conforming to Plan schema
        """
        start_time = time.time()
        plan_id = f"plan-{uuid.uuid4().hex[:12]}"

        logger.info(
            "anthropic_planner_invoked",
            extra={
                "agent_id": agent_id,
                "goal": goal[:100],
                "model": self.model,
                "has_context": context_summary is not None,
                "memory_count": len(memory_snippets) if memory_snippets else 0,
                "tool_count": len(tool_manifest) if tool_manifest else 0,
            },
        )

        # No API key - return stub
        if not self.api_key:
            logger.warning("No API key - returning stub plan")
            return self._stub_plan(plan_id, agent_id, goal, tool_manifest, start_time)

        # Build prompts
        system_prompt = self._build_system_prompt(tool_manifest)
        user_prompt = self._build_user_prompt(goal, context_summary, memory_snippets)

        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract text content
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            # Parse the plan
            plan = self._parse_response(response_text, plan_id, agent_id, goal, response, start_time)

            logger.info(
                "anthropic_plan_generated",
                extra={
                    "plan_id": plan_id,
                    "step_count": len(plan.get("steps", [])),
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                },
            )

            return plan

        except Exception as e:
            logger.exception("anthropic_planner_error", extra={"error": str(e), "agent_id": agent_id})
            # Fallback to stub on error
            return self._stub_plan(plan_id, agent_id, goal, tool_manifest, start_time)

    def _build_system_prompt(self, tool_manifest: Optional[List[Dict[str, Any]]]) -> str:
        """Build the system prompt for planning."""
        tools_section = ""
        if tool_manifest:
            tools_list = []
            for t in tool_manifest:
                name = t.get("name", "unknown")
                desc = t.get("description", "No description")
                version = t.get("version", "0.0.0")

                # Include input schema if available
                schema_hint = ""
                if "input_schema" in t:
                    props = t["input_schema"].get("properties", {})
                    required = t["input_schema"].get("required", [])
                    if props:
                        params = []
                        for k, v in list(props.items())[:5]:  # Limit to 5 params
                            req = "(required)" if k in required else "(optional)"
                            params.append(f"    - {k}: {v.get('type', 'any')} {req}")
                        schema_hint = "\n" + "\n".join(params)

                tools_list.append(f"- {name} (v{version}): {desc}{schema_hint}")

            tools_section = "\n\n## Available Skills\n" + "\n".join(tools_list)

        return f"""You are an AI planner for AOS (Agent Operating System).
Your task is to decompose goals into executable multi-step plans using available skills.

## Output Format
You MUST output a valid JSON object with this exact structure:
{{
  "reasoning": "Brief explanation of your planning approach",
  "steps": [
    {{
      "step_id": "s1",
      "skill": "skill_name",
      "params": {{}},
      "description": "What this step does",
      "depends_on": [],
      "on_error": "abort"
    }}
  ]
}}

## Rules
1. step_id must be a short string like "s1", "s2", "fetch_data", "summarize"
2. skill must match an available skill name exactly
3. params must contain valid parameters for the skill
4. depends_on is a list of step_ids that must complete first
5. on_error can be "abort", "continue", or "retry"
6. Keep plans concise: 1-5 steps for simple goals, up to 10 for complex
7. Use http_call for fetching data, llm_invoke for processing/reasoning
8. Chain steps by referencing outputs: use {{{{step_id.field}}}} syntax in params
{tools_section}

## Important
- Output ONLY valid JSON, no markdown code blocks
- Do not include any text before or after the JSON
- Validate that skill names exactly match available skills"""

    def _build_user_prompt(
        self, goal: str, context_summary: Optional[str], memory_snippets: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Build the user prompt for planning."""
        prompt_parts = [f"Goal: {goal}"]

        if context_summary:
            prompt_parts.append(f"\nContext from previous runs:\n{context_summary}")

        if memory_snippets:
            memories_text = "\n".join(
                [f"- [{m.get('memory_type', 'memory')}] {m.get('text', '')[:150]}" for m in memory_snippets[:5]]
            )
            prompt_parts.append(f"\nRelevant memories:\n{memories_text}")

        prompt_parts.append("\nGenerate the execution plan as JSON:")

        return "\n".join(prompt_parts)

    def _parse_response(
        self, response_text: str, plan_id: str, agent_id: str, goal: str, api_response: Any, start_time: float
    ) -> Dict[str, Any]:
        """Parse Claude's response into a Plan-compatible dict."""
        latency_ms = (time.time() - start_time) * 1000

        # Try to extract JSON from response
        try:
            # Handle potential markdown code blocks
            text = response_text.strip()
            if text.startswith("```"):
                # Extract from code block
                lines = text.split("\n")
                start_idx = 1 if lines[0].startswith("```") else 0
                end_idx = len(lines)
                for i, line in enumerate(lines):
                    if i > 0 and line.strip() == "```":
                        end_idx = i
                        break
                text = "\n".join(lines[start_idx:end_idx])

            parsed = json.loads(text)

        except json.JSONDecodeError as e:
            logger.warning(
                "anthropic_json_parse_failed", extra={"error": str(e), "response_preview": response_text[:200]}
            )
            # Return a fallback plan
            return self._fallback_plan(plan_id, agent_id, goal, latency_ms, api_response)

        # Build the plan structure conforming to Plan schema
        steps = []
        for i, step in enumerate(parsed.get("steps", [])):
            step_id = step.get("step_id", f"s{i+1}")
            steps.append(
                {
                    "step_id": str(step_id),
                    "skill": step.get("skill", "http_call"),
                    "params": step.get("params", {}),
                    "description": step.get("description"),
                    "depends_on": step.get("depends_on", []),
                    "on_error": step.get("on_error", "abort"),
                    "status": "pending",
                }
            )

        plan = {
            "plan_id": plan_id,
            "goal": goal,
            "steps": steps,
            "metadata": {
                "planner": "anthropic",
                "planner_version": "1.0.0",
                "model": self.model,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "reasoning": parsed.get("reasoning"),
                "input_tokens": api_response.usage.input_tokens,
                "output_tokens": api_response.usage.output_tokens,
                "latency_ms": round(latency_ms, 2),
            },
            "default_on_error": "abort",
            "context": {},
            "status": "pending",
        }

        return plan

    def _fallback_plan(
        self, plan_id: str, agent_id: str, goal: str, latency_ms: float, api_response: Any
    ) -> Dict[str, Any]:
        """Generate a fallback plan when parsing fails."""
        return {
            "plan_id": plan_id,
            "goal": goal,
            "steps": [
                {
                    "step_id": "s1",
                    "skill": "http_call",
                    "params": {"url": "https://api.github.com/zen", "method": "GET"},
                    "description": f"Fallback: {goal[:50]}",
                    "depends_on": [],
                    "on_error": "abort",
                    "status": "pending",
                }
            ],
            "metadata": {
                "planner": "anthropic",
                "planner_version": "1.0.0",
                "model": self.model,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "reasoning": "Fallback plan due to parsing error",
                "input_tokens": api_response.usage.input_tokens if api_response else 0,
                "output_tokens": api_response.usage.output_tokens if api_response else 0,
                "latency_ms": round(latency_ms, 2),
                "fallback": True,
            },
            "default_on_error": "abort",
            "context": {},
            "status": "pending",
        }

    def _stub_plan(
        self, plan_id: str, agent_id: str, goal: str, tool_manifest: Optional[List[Dict[str, Any]]], start_time: float
    ) -> Dict[str, Any]:
        """Generate a stub plan when API is unavailable."""
        latency_ms = (time.time() - start_time) * 1000

        # Pick first available skill or default to http_call
        skill = "http_call"
        if tool_manifest:
            for t in tool_manifest:
                if t.get("name"):
                    skill = t["name"]
                    break

        plan = {
            "plan_id": plan_id,
            "goal": goal,
            "steps": [
                {
                    "step_id": "s1",
                    "skill": skill,
                    "params": {"url": "https://api.github.com/zen", "method": "GET"},
                    "description": f"Stub: {goal[:50]}",
                    "depends_on": [],
                    "on_error": "abort",
                    "status": "pending",
                }
            ],
            "metadata": {
                "planner": "anthropic",
                "planner_version": "1.0.0",
                "model": self.model,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "reasoning": "Stub plan - no API key configured",
                "input_tokens": 0,
                "output_tokens": 0,
                "latency_ms": round(latency_ms, 2),
                "stub": True,
            },
            "default_on_error": "abort",
            "context": {},
            "status": "pending",
        }

        logger.info("anthropic_stub_plan_generated", extra={"plan_id": plan_id, "latency_ms": latency_ms})

        return plan
