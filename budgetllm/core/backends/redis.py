"""
Redis cache backend for BudgetLLM.

Shared cache across multiple processes/workers.
"""

import hashlib
import json
from typing import Optional


class RedisBackend:
    """
    Redis-backed cache backend.

    Features:
    - Shared across processes
    - Automatic TTL expiration
    - Atomic operations

    Example:
        cache = RedisBackend(url="redis://localhost:6379/0")
        cache.set("key", {"response": "hello"}, ttl=3600)
        value = cache.get("key")
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        key_prefix: str = "budgetllm:cache",
        default_ttl: int = 3600,
    ):
        """
        Initialize Redis cache.

        Args:
            url: Redis connection URL
            key_prefix: Prefix for all cache keys
            default_ttl: Default TTL in seconds
        """
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Redis support requires 'redis' package. "
                "Install with: pip install budgetllm[redis]"
            )

        self._client = redis.Redis.from_url(url, decode_responses=True)
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}:{key}"

    def _generate_key(self, prompt_data: dict) -> str:
        """Generate cache key from prompt data."""
        normalized = json.dumps(prompt_data, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get(self, key: str) -> Optional[dict]:
        """
        Get cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        full_key = self._make_key(key)
        raw = self._client.get(full_key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set(
        self,
        key: str,
        value: dict,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if not specified)
        """
        ttl = ttl or self.default_ttl
        full_key = self._make_key(key)
        self._client.setex(full_key, ttl, json.dumps(value))

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        full_key = self._make_key(key)
        return bool(self._client.delete(full_key))

    def clear(self) -> int:
        """
        Clear all entries with our prefix.

        Returns:
            Number of entries cleared
        """
        pattern = f"{self.key_prefix}:*"
        keys = self._client.keys(pattern)
        if keys:
            return self._client.delete(*keys)
        return 0

    def size(self) -> int:
        """Get approximate number of entries."""
        pattern = f"{self.key_prefix}:*"
        return len(self._client.keys(pattern))

    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": self.size(),
            "default_ttl": self.default_ttl,
            "backend": "redis",
        }

    def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return self._client.ping()
        except Exception:
            return False
