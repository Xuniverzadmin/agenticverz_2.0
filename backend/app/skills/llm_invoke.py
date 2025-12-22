# LLM Invoke Skill
# Provides LLM inference as a skill step for agent plans
# Includes prompt caching for cost reduction (M13+)

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from ..metrics import (
    nova_llm_cost_cents_total,
    nova_llm_duration_seconds,
    nova_llm_invocations_total,
    nova_llm_tokens_total,
)
from ..schemas.skill import (
    LLMInvokeInput,
    LLMInvokeOutput,
    SkillStatus,
)
from ..utils.metrics_helpers import get_or_create_counter, get_or_create_gauge
from .registry import skill

logger = logging.getLogger("nova.skills.llm_invoke")

# =============================================================================
# PROMPT CACHE METRICS - using idempotent registration (PIN-120 PREV-1)
# =============================================================================

llm_cache_hits_total = get_or_create_counter(
    "llm_cache_hits_total",
    "Total LLM cache hits (saved API calls)",
    ["provider", "model"],
)

llm_cache_misses_total = get_or_create_counter(
    "llm_cache_misses_total",
    "Total LLM cache misses",
    ["provider", "model"],
)

llm_cache_savings_cents = get_or_create_counter(
    "llm_cache_savings_cents",
    "Estimated cost savings from cache hits in cents",
    ["provider", "model"],
)

llm_cache_size = get_or_create_gauge(
    "llm_cache_size",
    "Current number of entries in LLM cache",
)

llm_cache_evictions_total = get_or_create_counter(
    "llm_cache_evictions_total",
    "Total cache entries evicted due to TTL or size limit",
)


# =============================================================================
# PROMPT CACHE IMPLEMENTATION
# =============================================================================


@dataclass
class CacheEntry:
    """A cached LLM response with metadata."""

    response: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    estimated_cost_cents: float = 0.0


class PromptCache:
    """
    Thread-safe LLM prompt cache with TTL and size limits.

    Features:
    - Exact match caching on (provider, model, messages, system_prompt, temperature)
    - Configurable TTL (default 1 hour)
    - Configurable max size (default 1000 entries)
    - LRU-style eviction when size limit reached
    - Thread-safe for multi-worker environments

    Usage:
        cache = PromptCache(ttl_seconds=3600, max_size=1000)

        # Check cache
        cached = cache.get(provider, model, messages, system_prompt, temperature)
        if cached:
            return cached  # Free!

        # Make LLM call...
        result = await call_llm(...)

        # Store in cache
        cache.set(provider, model, messages, system_prompt, temperature, result, cost)
    """

    def __init__(
        self,
        ttl_seconds: int = 3600,  # 1 hour default
        max_size: int = 1000,
        enabled: bool = True,
    ):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.enabled = enabled
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._access_order: Dict[str, datetime] = {}  # For LRU eviction

    def _generate_cache_key(
        self,
        provider: str,
        model: str,
        messages: list,
        system_prompt: Optional[str],
        temperature: Optional[float],
    ) -> str:
        """
        Generate a deterministic cache key from request parameters.

        Note: We include temperature because different temperatures produce
        different outputs. We exclude max_tokens because it doesn't affect
        the semantic content of the response.
        """
        # Normalize messages to ensure consistent hashing
        normalized_messages = json.dumps(messages, sort_keys=True, ensure_ascii=True)

        # Build key components
        key_parts = [
            f"provider:{provider}",
            f"model:{model}",
            f"system:{system_prompt or ''}",
            f"temp:{temperature if temperature is not None else 'default'}",
            f"messages:{normalized_messages}",
        ]

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(
        self,
        provider: str,
        model: str,
        messages: list,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired.

        Returns:
            Cached response dict or None if not found/expired
        """
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(provider, model, messages, system_prompt, temperature)

        with self._lock:
            entry = self._cache.get(cache_key)

            if entry is None:
                return None

            # Check expiration
            now = datetime.now(timezone.utc)
            if now >= entry.expires_at:
                # Expired - remove and return None
                del self._cache[cache_key]
                if cache_key in self._access_order:
                    del self._access_order[cache_key]
                llm_cache_evictions_total.inc()
                llm_cache_size.set(len(self._cache))
                logger.debug("llm_cache_expired", extra={"key": cache_key[:16]})
                return None

            # Cache hit!
            entry.hit_count += 1
            self._access_order[cache_key] = now

            logger.info(
                "llm_cache_hit",
                extra={
                    "key": cache_key[:16],
                    "hit_count": entry.hit_count,
                    "age_seconds": (now - entry.created_at).total_seconds(),
                    "saved_cents": entry.estimated_cost_cents,
                },
            )

            return entry.response

    def set(
        self,
        provider: str,
        model: str,
        messages: list,
        system_prompt: Optional[str],
        temperature: Optional[float],
        response: Dict[str, Any],
        estimated_cost_cents: float = 0.0,
    ) -> str:
        """
        Store a response in the cache.

        Args:
            provider: LLM provider
            model: Model name
            messages: Chat messages
            system_prompt: System prompt if any
            temperature: Temperature setting
            response: LLM response to cache
            estimated_cost_cents: Estimated cost of this call

        Returns:
            Cache key for reference
        """
        if not self.enabled:
            return ""

        cache_key = self._generate_cache_key(provider, model, messages, system_prompt, temperature)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.ttl_seconds)

        entry = CacheEntry(
            response=response,
            created_at=now,
            expires_at=expires_at,
            hit_count=0,
            estimated_cost_cents=estimated_cost_cents,
        )

        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_oldest()

            self._cache[cache_key] = entry
            self._access_order[cache_key] = now
            llm_cache_size.set(len(self._cache))

        logger.debug(
            "llm_cache_set",
            extra={
                "key": cache_key[:16],
                "ttl_seconds": self.ttl_seconds,
                "cost_cents": estimated_cost_cents,
            },
        )

        return cache_key

    def _evict_oldest(self) -> None:
        """Evict the least recently accessed entry."""
        if not self._access_order:
            return

        # Find oldest
        oldest_key = min(self._access_order, key=self._access_order.get)

        if oldest_key in self._cache:
            del self._cache[oldest_key]
        if oldest_key in self._access_order:
            del self._access_order[oldest_key]

        llm_cache_evictions_total.inc()
        logger.debug("llm_cache_evicted", extra={"key": oldest_key[:16]})

    def clear(self) -> int:
        """Clear all cache entries. Returns count of cleared entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._access_order.clear()
            llm_cache_size.set(0)
        return count

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            entries = list(self._cache.values())

        now = datetime.now(timezone.utc)
        total_hits = sum(e.hit_count for e in entries)
        total_savings = sum(e.hit_count * e.estimated_cost_cents for e in entries)
        avg_age = 0.0
        if entries:
            avg_age = sum((now - e.created_at).total_seconds() for e in entries) / len(entries)

        return {
            "enabled": self.enabled,
            "size": len(entries),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "total_hits": total_hits,
            "total_savings_cents": round(total_savings, 2),
            "average_age_seconds": round(avg_age, 1),
        }


# Global cache instance
_prompt_cache: Optional[PromptCache] = None


def get_prompt_cache() -> PromptCache:
    """Get or create the global prompt cache."""
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = PromptCache(
            ttl_seconds=int(os.getenv("LLM_CACHE_TTL_SECONDS", "3600")),
            max_size=int(os.getenv("LLM_CACHE_MAX_SIZE", "1000")),
            enabled=os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true",
        )
    return _prompt_cache


def configure_prompt_cache(
    ttl_seconds: int = 3600,
    max_size: int = 1000,
    enabled: bool = True,
) -> PromptCache:
    """Configure the global prompt cache."""
    global _prompt_cache
    _prompt_cache = PromptCache(
        ttl_seconds=ttl_seconds,
        max_size=max_size,
        enabled=enabled,
    )
    return _prompt_cache


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

                self._anthropic_client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
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

                self._openai_client = openai.OpenAI(api_key=self.config.openai_api_key)
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
                "cache_enabled": input_data.enable_cache,
            },
        )

        # =========================================================
        # PROMPT CACHE CHECK - Check cache before making LLM call
        # =========================================================
        cache = get_prompt_cache()
        cached_response = None

        if input_data.enable_cache and cache.enabled:
            cached_response = cache.get(
                provider=provider,
                model=model,
                messages=messages,
                system_prompt=input_data.system_prompt,
                temperature=input_data.temperature,
            )

            if cached_response is not None:
                duration = time.time() - start_time
                completed_at = datetime.now(timezone.utc)

                # Update cache metrics
                llm_cache_hits_total.labels(provider=provider, model=model).inc()

                # Calculate estimated savings (what this call would have cost)
                estimated_cost = self._calculate_cost(
                    provider,
                    model,
                    cached_response.get("input_tokens", 0),
                    cached_response.get("output_tokens", 0),
                )
                llm_cache_savings_cents.labels(provider=provider, model=model).inc(estimated_cost)

                logger.info(
                    "llm_invoke_cache_hit",
                    extra={
                        "provider": provider,
                        "model": model,
                        "saved_cents": estimated_cost,
                        "duration_ms": round(duration * 1000, 1),
                    },
                )

                # Return cached response
                return {
                    "skill": "llm_invoke",
                    "skill_version": self.VERSION,
                    "status": SkillStatus.OK.value,
                    "duration_seconds": round(duration, 3),
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "error": None,
                    "result": {
                        "response_text": cached_response["response_text"],
                        "llm_model": cached_response["model_used"],
                        "input_tokens": cached_response["input_tokens"],
                        "output_tokens": cached_response["output_tokens"],
                        "finish_reason": cached_response["finish_reason"],
                        "cost_cents": 0.0,  # No cost for cache hit!
                        "cache_hit": True,
                    },
                    "side_effects": {
                        "tokens_used": 0,  # No tokens consumed
                        "cost_cents": 0.0,
                        "cache_hit": True,
                        "saved_cents": estimated_cost,
                    },
                }

        # Cache miss - record metric
        if input_data.enable_cache and cache.enabled:
            llm_cache_misses_total.labels(provider=provider, model=model).inc()

        # =========================================================
        # LLM CALL - Make the actual API call
        # =========================================================
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
                },
            )
            # Record error metrics
            nova_llm_invocations_total.labels(
                provider=provider, model=model, status="error", tenant_id="default", agent_id="skill"
            ).inc()
            nova_llm_duration_seconds.labels(provider=provider, model=model, tenant_id="default").observe(duration)

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
            },
        )

        # Record success metrics
        nova_llm_invocations_total.labels(
            provider=provider, model=model, status="success", tenant_id="default", agent_id="skill"
        ).inc()
        nova_llm_duration_seconds.labels(provider=provider, model=model, tenant_id="default").observe(duration)
        nova_llm_tokens_total.labels(
            provider=provider, model=model, token_type="input", tenant_id="default", agent_id="skill"
        ).inc(result["input_tokens"])
        nova_llm_tokens_total.labels(
            provider=provider, model=model, token_type="output", tenant_id="default", agent_id="skill"
        ).inc(result["output_tokens"])
        if cost_cents:
            nova_llm_cost_cents_total.labels(provider=provider, model=model, tenant_id="default", agent_id="skill").inc(
                cost_cents
            )

        # =========================================================
        # CACHE STORAGE - Store successful response in cache
        # =========================================================
        if input_data.enable_cache and cache.enabled:
            cache.set(
                provider=provider,
                model=model,
                messages=messages,
                system_prompt=input_data.system_prompt,
                temperature=input_data.temperature,
                response=result,
                estimated_cost_cents=cost_cents or 0.0,
            )
            logger.debug(
                "llm_invoke_cached",
                extra={
                    "provider": provider,
                    "model": model,
                    "cost_cents": cost_cents,
                },
            )

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
                "cache_hit": False,
            },
            "side_effects": {
                "tokens_used": result["input_tokens"] + result["output_tokens"],
                "cost_cents": cost_cents,
                "cache_hit": False,
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

        response = await asyncio.to_thread(client.messages.create, **request_kwargs)

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
            openai_messages.append(
                {
                    "role": "system",
                    "content": input_data.system_prompt,
                }
            )
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

        response = await asyncio.to_thread(client.chat.completions.create, **request_kwargs)

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
