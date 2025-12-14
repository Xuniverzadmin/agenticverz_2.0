"""
Prompt cache for LLM API calls.

Caches responses based on (model, messages, temperature, system_prompt).
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class CacheBackend(Protocol):
    """Protocol for cache backends."""

    def get(self, key: str) -> Optional[dict]:
        """Get cached value."""
        ...

    def set(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
        """Set cached value."""
        ...

    def delete(self, key: str) -> bool:
        """Delete cached value."""
        ...


class PromptCache:
    """
    High-level prompt cache.

    Generates cache keys from prompt parameters and manages
    cache hits/misses with metrics.

    Example:
        from budgetllm.core.backends.memory import MemoryBackend

        cache = PromptCache(backend=MemoryBackend())

        # Check cache
        cached = cache.get(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
        )

        if cached:
            return cached["response"]

        # Make API call...
        response = openai.chat.completions.create(...)

        # Store in cache
        cache.set(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            response=response_dict,
            cost_cents=0.5,
        )
    """

    def __init__(
        self,
        backend: CacheBackend,
        enabled: bool = True,
        default_ttl: int = 3600,
    ):
        """
        Initialize prompt cache.

        Args:
            backend: Cache backend (MemoryBackend or RedisBackend)
            enabled: Whether caching is enabled
            default_ttl: Default TTL in seconds
        """
        self.backend = backend
        self.enabled = enabled
        self.default_ttl = default_ttl

        # Metrics
        self.hits = 0
        self.misses = 0
        self.savings_cents = 0.0

    def _generate_key(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate cache key from prompt parameters.

        Note: max_tokens is excluded because it doesn't affect
        the semantic content of the response.
        """
        key_parts = {
            "model": model,
            "messages": messages,
            "temperature": temperature if temperature is not None else "default",
            "system_prompt": system_prompt or "",
        }
        normalized = json.dumps(key_parts, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Get cached response.

        Args:
            model: Model name
            messages: Chat messages
            temperature: Temperature setting
            system_prompt: System prompt

        Returns:
            Cached response dict or None
        """
        if not self.enabled:
            return None

        key = self._generate_key(model, messages, temperature, system_prompt)
        cached = self.backend.get(key)

        if cached is not None:
            self.hits += 1
            self.savings_cents += cached.get("cost_cents", 0)
            return cached
        else:
            self.misses += 1
            return None

    def set(
        self,
        model: str,
        messages: List[Dict[str, str]],
        response: dict,
        cost_cents: float = 0.0,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """
        Cache a response.

        Args:
            model: Model name
            messages: Chat messages
            response: Response to cache
            cost_cents: Cost of this call (for savings tracking)
            temperature: Temperature setting
            system_prompt: System prompt
            ttl: TTL in seconds

        Returns:
            Cache key
        """
        if not self.enabled:
            return ""

        key = self._generate_key(model, messages, temperature, system_prompt)

        cache_entry = {
            **response,
            "cost_cents": cost_cents,
            "cached": True,
        }

        self.backend.set(key, cache_entry, ttl or self.default_ttl)
        return key

    def invalidate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> bool:
        """
        Invalidate a cached entry.

        Returns:
            True if entry was deleted
        """
        key = self._generate_key(model, messages, temperature, system_prompt)
        return self.backend.delete(key)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0

        return {
            "enabled": self.enabled,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": round(hit_rate, 2),
            "savings_cents": round(self.savings_cents, 4),
        }

    def reset_stats(self) -> None:
        """Reset hit/miss counters."""
        self.hits = 0
        self.misses = 0
        self.savings_cents = 0.0
