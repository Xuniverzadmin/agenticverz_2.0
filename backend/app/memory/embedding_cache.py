# Embedding Cache Layer
"""
Redis-based cache for embedding results.
PIN-047: P3 - Embedding Cache Layer

Reduces API costs and latency by caching embedding results.
Cache key: sha256(text + model) truncated to 32 chars

Features:
- Configurable TTL (default 7 days)
- Cache hit/miss metrics
- Automatic serialization of vectors
- Provider-aware caching (different models = different keys)
"""

import hashlib
import json
import logging
import os
from typing import List, Optional

from app.utils.metrics_helpers import get_or_create_counter, get_or_create_histogram

logger = logging.getLogger("nova.memory.embedding_cache")

# Configuration
EMBEDDING_CACHE_ENABLED = os.getenv("EMBEDDING_CACHE_ENABLED", "true").lower() == "true"
EMBEDDING_CACHE_TTL = int(os.getenv("EMBEDDING_CACHE_TTL", str(7 * 24 * 3600)))  # 7 days default
EMBEDDING_CACHE_PREFIX = "emb:v1:"

# Metrics - using idempotent registration (PIN-120 PREV-1)
EMBEDDING_CACHE_HITS = get_or_create_counter(
    "aos_embedding_cache_hits_total",
    "Embedding cache hits",
    ["provider"],
)

EMBEDDING_CACHE_MISSES = get_or_create_counter(
    "aos_embedding_cache_misses_total",
    "Embedding cache misses",
    ["provider"],
)

EMBEDDING_CACHE_LATENCY = get_or_create_histogram(
    "aos_embedding_cache_latency_seconds",
    "Cache lookup latency",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
)


def compute_cache_key(text: str, model: str) -> str:
    """
    Compute cache key for embedding lookup.

    Uses sha256 of text + model to ensure unique keys
    for different models and avoid collisions.
    """
    content = f"{model}:{text}"
    return EMBEDDING_CACHE_PREFIX + hashlib.sha256(content.encode()).hexdigest()[:32]


class EmbeddingCache:
    """
    Redis-based embedding cache.

    Usage:
        cache = EmbeddingCache(redis_client)

        # Try cache first
        embedding = await cache.get(text, model="text-embedding-3-small")
        if embedding is None:
            embedding = await generate_embedding(text)
            await cache.set(text, embedding, model="text-embedding-3-small")
    """

    def __init__(self, redis_client=None):
        """
        Initialize cache with optional Redis client.

        Args:
            redis_client: Redis async client (uses global if not provided)
        """
        self._redis = redis_client
        self._enabled = EMBEDDING_CACHE_ENABLED
        logger.info(f"EmbeddingCache initialized (enabled={self._enabled}, ttl={EMBEDDING_CACHE_TTL}s)")

    async def _get_redis(self):
        """Get Redis client, initializing if needed."""
        if self._redis is not None:
            return self._redis

        # Initialize Redis connection
        redis_url = os.getenv("REDIS_URL", "")
        if not redis_url:
            logger.debug("REDIS_URL not set, embedding cache disabled")
            return None

        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("Embedding cache connected to Redis")
            return self._redis
        except Exception as e:
            logger.warning(f"Redis not available for embedding cache: {e}")
            return None

    async def get(self, text: str, model: str, provider: str = "openai") -> Optional[List[float]]:
        """
        Get cached embedding.

        Args:
            text: Original text
            model: Embedding model name
            provider: Provider name for metrics

        Returns:
            Cached embedding vector or None if not cached
        """
        if not self._enabled:
            return None

        import time

        start = time.perf_counter()

        try:
            redis = await self._get_redis()
            if redis is None:
                return None

            key = compute_cache_key(text, model)
            cached = await redis.get(key)

            latency = time.perf_counter() - start
            EMBEDDING_CACHE_LATENCY.observe(latency)

            if cached is not None:
                EMBEDDING_CACHE_HITS.labels(provider=provider).inc()
                logger.debug(f"Cache HIT for {key[:16]}...")
                return json.loads(cached)

            EMBEDDING_CACHE_MISSES.labels(provider=provider).inc()
            return None

        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            EMBEDDING_CACHE_MISSES.labels(provider=provider).inc()
            return None

    async def set(
        self,
        text: str,
        embedding: List[float],
        model: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store embedding in cache.

        Args:
            text: Original text
            embedding: Embedding vector
            model: Embedding model name
            ttl: Optional custom TTL in seconds

        Returns:
            True if stored successfully
        """
        if not self._enabled:
            return False

        try:
            redis = await self._get_redis()
            if redis is None:
                return False

            key = compute_cache_key(text, model)
            value = json.dumps(embedding)

            await redis.set(
                key,
                value,
                ex=ttl or EMBEDDING_CACHE_TTL,
            )

            logger.debug(f"Cached embedding for {key[:16]}...")
            return True

        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def invalidate(self, text: str, model: str) -> bool:
        """
        Remove embedding from cache.

        Args:
            text: Original text
            model: Embedding model name

        Returns:
            True if deleted
        """
        try:
            redis = await self._get_redis()
            if redis is None:
                return False

            key = compute_cache_key(text, model)
            result = await redis.delete(key)
            return bool(result > 0)

        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
            return False

    async def clear_all(self) -> int:
        """
        Clear all embedding cache entries.

        Returns:
            Number of entries cleared
        """
        try:
            redis = await self._get_redis()
            if redis is None:
                return 0

            # Find all embedding cache keys
            pattern = f"{EMBEDDING_CACHE_PREFIX}*"
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await redis.delete(*keys)

            logger.info(f"Cleared {len(keys)} embedding cache entries")
            return len(keys)

        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return 0

    async def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        try:
            redis = await self._get_redis()
            if redis is None:
                return {"enabled": False, "reason": "redis_unavailable"}

            # Count entries
            pattern = f"{EMBEDDING_CACHE_PREFIX}*"
            count = 0
            async for _ in redis.scan_iter(match=pattern):
                count += 1

            return {
                "enabled": self._enabled,
                "entries": count,
                "ttl_seconds": EMBEDDING_CACHE_TTL,
                "prefix": EMBEDDING_CACHE_PREFIX,
            }

        except Exception as e:
            return {"enabled": False, "reason": str(e)}


# Singleton instance
_embedding_cache: Optional[EmbeddingCache] = None


def get_embedding_cache() -> EmbeddingCache:
    """Get singleton embedding cache instance."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    return _embedding_cache
