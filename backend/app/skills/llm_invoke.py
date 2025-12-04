# LLM Invoke Skill
# Provides LLM inference as a skill step for agent plans

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..schemas.skill import (
    LLMInvokeInput,
    LLMInvokeOutput,
    LLMProvider,
    SkillStatus,
)
from ..metrics import (
    nova_llm_tokens_total,
    nova_llm_cost_cents_total,
    nova_llm_duration_seconds,
    nova_llm_invocations_total,
)
from .registry import skill

logger = logging.getLogger("nova.skills.llm_invoke")

# Cost per 1M tokens (in cents) - approximate as of Jan 2025
COST_PER_1M_TOKENS = {
    "anthropic": {
        "claude-opus-4-20250514": {"input": 1500, "output": 7500},
        "claude-sonnet-4-20250514": {"input": 300, "output": 1500},
        "claude-3-5-haiku-20241022": {"input": 80, "output": 400},
        # Default for unknown models
        "default": {"input": 300, "output": 1500},
    },
    "openai": {
        "gpt-4o": {"input": 250, "output": 1000},
        "gpt-4o-mini": {"input": 15, "output": 60},
        "default": {"input": 250, "output": 1000},
    },
}


class LLMInvokeConfig:
    """Configuration for llm_invoke skill."""

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        default_provider: str = "anthropic",
        default_model: str = "claude-sonnet-4-20250514",
        max_tokens_limit: int = 8192,
        track_costs: bool = True,
    ):
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.default_provider = default_provider
        self.default_model = default_model
        self.max_tokens_limit = max_tokens_limit
        self.track_costs = track_costs


@skill(
    name="llm_invoke",
    input_schema=LLMInvokeInput,
    output_schema=LLMInvokeOutput,
    tags=["ai", "llm", "inference", "claude", "openai"],
    default_config={
        "default_provider": "anthropic",
        "default_model": "claude-sonnet-4-20250514",
        "max_tokens_limit": 8192,
        "track_costs": True,
    },
)
class LLMInvokeSkill:
    """LLM inference skill for AI-powered processing steps.

    Supports Anthropic Claude and OpenAI models. Can be used for:
    - Text summarization
    - Data extraction
    - Content generation
    - Reasoning and analysis
    """

    VERSION = "1.0.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = LLMInvokeConfig(**(config or {}))
        self._anthropic_client = None
        self._openai_client = None

    def _get_anthropic_client(self):
        """Lazy-load Anthropic client."""
        if self._anthropic_client is None:
            if not self.config.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(
                    api_key=self.config.anthropic_api_key
                )
            except ImportError:
                raise ImportError("anthropic package required: pip install anthropic")
        return self._anthropic_client

    def _get_openai_client(self):
        """Lazy-load OpenAI client."""
        if self._openai_client is None:
            if not self.config.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            try:
                import openai
                self._openai_client = openai.OpenAI(
                    api_key=self.config.openai_api_key
                )
            except ImportError:
                raise ImportError("openai package required: pip install openai")
        return self._openai_client

    def _calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Calculate cost in cents."""
        provider_costs = COST_PER_1M_TOKENS.get(provider, {})
        model_costs = provider_costs.get(model, provider_costs.get("default", {}))

        input_cost = (input_tokens / 1_000_000) * model_costs.get("input", 0)
        output_cost = (output_tokens / 1_000_000) * model_costs.get("output", 0)

        return round(input_cost + output_cost, 4)

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM inference.

        Args:
            params: Input parameters matching LLMInvokeInput schema

        Returns:
            Result dict with response and usage metrics
        """
        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        # Parse input
        try:
            input_data = LLMInvokeInput(**params)
        except Exception as e:
            logger.error("llm_invoke_input_validation_failed", extra={"error": str(e)})
            raise ValueError(f"Invalid input: {e}")

        provider = input_data.provider.value
        model = input_data.model
        messages = [{"role": m.role, "content": m.content} for m in input_data.messages]

        logger.info(
            "llm_invoke_start",
            extra={
                "provider": provider,
                "model": model,
                "message_count": len(messages),
                "max_tokens": input_data.max_tokens,
            }
        )

        try:
            if provider == "anthropic":
                result = await self._invoke_anthropic(input_data, messages)
            elif provider == "openai":
                result = await self._invoke_openai(input_data, messages)
            elif provider == "local":
                result = await self._invoke_local(input_data, messages)
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            duration = time.time() - start_time
            logger.exception(
                "llm_invoke_error",
                extra={
                    "provider": provider,
                    "model": model,
                    "error": str(e)[:200],
                    "duration": round(duration, 3),
                }
            )
            # Record error metrics
            nova_llm_invocations_total.labels(
                provider=provider, model=model, status="error"
            ).inc()
            nova_llm_duration_seconds.labels(
                provider=provider, model=model
            ).observe(duration)

            return {
                "skill": "llm_invoke",
                "skill_version": self.VERSION,
                "status": SkillStatus.ERROR.value,
                "duration_seconds": round(duration, 3),
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e)[:500],
                "result": {
                    "response_text": "",
                    "llm_model": model,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "finish_reason": "error",
                    "error": str(e)[:200],
                },
                "side_effects": {},
            }

        duration = time.time() - start_time
        completed_at = datetime.now(timezone.utc)

        # Calculate cost if tracking enabled
        cost_cents = None
        if self.config.track_costs:
            cost_cents = self._calculate_cost(
                provider,
                model,
                result["input_tokens"],
                result["output_tokens"],
            )

        logger.info(
            "llm_invoke_complete",
            extra={
                "provider": provider,
                "model": model,
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "cost_cents": cost_cents,
                "duration": round(duration, 3),
            }
        )

        # Record success metrics
        nova_llm_invocations_total.labels(
            provider=provider, model=model, status="success"
        ).inc()
        nova_llm_duration_seconds.labels(
            provider=provider, model=model
        ).observe(duration)
        nova_llm_tokens_total.labels(
            provider=provider, model=model, token_type="input"
        ).inc(result["input_tokens"])
        nova_llm_tokens_total.labels(
            provider=provider, model=model, token_type="output"
        ).inc(result["output_tokens"])
        if cost_cents:
            nova_llm_cost_cents_total.labels(
                provider=provider, model=model
            ).inc(cost_cents)

        return {
            "skill": "llm_invoke",
            "skill_version": self.VERSION,
            "status": SkillStatus.OK.value,
            "duration_seconds": round(duration, 3),
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "error": None,
            "result": {
                "response_text": result["response_text"],
                "llm_model": result["model_used"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "finish_reason": result["finish_reason"],
                "cost_cents": cost_cents,
            },
            "side_effects": {
                "tokens_used": result["input_tokens"] + result["output_tokens"],
                "cost_cents": cost_cents,
            },
        }

    async def _invoke_anthropic(
        self,
        input_data: LLMInvokeInput,
        messages: list,
    ) -> Dict[str, Any]:
        """Invoke Anthropic Claude API."""
        client = self._get_anthropic_client()

        # Build request
        request_kwargs = {
            "model": input_data.model,
            "max_tokens": min(input_data.max_tokens, self.config.max_tokens_limit),
            "messages": messages,
        }

        if input_data.system_prompt:
            request_kwargs["system"] = input_data.system_prompt

        if input_data.temperature is not None:
            request_kwargs["temperature"] = input_data.temperature

        if input_data.stop_sequences:
            request_kwargs["stop_sequences"] = input_data.stop_sequences

        # Make synchronous call (Anthropic SDK is sync)
        # In production, use asyncio.to_thread for true async
        import asyncio
        response = await asyncio.to_thread(
            client.messages.create,
            **request_kwargs
        )

        # Extract response
        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text += block.text

        return {
            "response_text": response_text,
            "model_used": response.model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "finish_reason": response.stop_reason or "end_turn",
        }

    async def _invoke_openai(
        self,
        input_data: LLMInvokeInput,
        messages: list,
    ) -> Dict[str, Any]:
        """Invoke OpenAI API."""
        client = self._get_openai_client()

        # Add system prompt as first message if provided
        openai_messages = []
        if input_data.system_prompt:
            openai_messages.append({
                "role": "system",
                "content": input_data.system_prompt,
            })
        openai_messages.extend(messages)

        # Build request
        request_kwargs = {
            "model": input_data.model,
            "max_tokens": min(input_data.max_tokens, self.config.max_tokens_limit),
            "messages": openai_messages,
        }

        if input_data.temperature is not None:
            request_kwargs["temperature"] = input_data.temperature

        if input_data.stop_sequences:
            request_kwargs["stop"] = input_data.stop_sequences

        # Make synchronous call
        import asyncio
        response = await asyncio.to_thread(
            client.chat.completions.create,
            **request_kwargs
        )

        choice = response.choices[0]
        return {
            "response_text": choice.message.content or "",
            "model_used": response.model,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "finish_reason": choice.finish_reason or "stop",
        }

    async def _invoke_local(
        self,
        input_data: LLMInvokeInput,
        messages: list,
    ) -> Dict[str, Any]:
        """Invoke local LLM endpoint (stub for now).

        Can be extended to support Ollama, vLLM, or other local inference.
        """
        logger.warning("llm_invoke_local_stub", extra={"model": input_data.model})

        # Return stub response
        combined_content = " ".join(m["content"] for m in messages)
        return {
            "response_text": f"[LOCAL STUB] Processed {len(combined_content)} chars from {len(messages)} messages",
            "model_used": input_data.model,
            "input_tokens": len(combined_content) // 4,  # Rough estimate
            "output_tokens": 20,
            "finish_reason": "stub",
        }
