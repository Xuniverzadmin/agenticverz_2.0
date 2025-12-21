# Guard API Cache Layer
"""
Redis-based cache for Guard Console endpoints.

Reduces database query latency by caching frequently-accessed data.
Critical for cross-region deployments (EU server, Singapore DB).

Cache Keys:
- guard:status:{tenant_id} - 5s TTL (real-time status)
- guard:snapshot:{tenant_id} - 10s TTL (today's metrics)
- guard:incidents:{tenant_id}:{limit}:{offset} - 5s TTL

Performance Target:
- Reduce /guard/status from 4-7s to <100ms (cache hit)
- Reduce /guard/snapshot/today from 2-6s to <100ms (cache hit)
"""

import json
import logging
import os
from typing import Dict, Optional

from prometheus_client import Counter, Histogram

logger = logging.getLogger("nova.guard.cache")

# Configuration
GUARD_CACHE_ENABLED = os.getenv("GUARD_CACHE_ENABLED", "true").lower() == "true"
GUARD_STATUS_TTL = int(os.getenv("GUARD_STATUS_TTL", "5"))  # 5 seconds
GUARD_SNAPSHOT_TTL = int(os.getenv("GUARD_SNAPSHOT_TTL", "10"))  # 10 seconds
GUARD_INCIDENTS_TTL = int(os.getenv("GUARD_INCIDENTS_TTL", "5"))  # 5 seconds
GUARD_CACHE_PREFIX = "guard:"

# Metrics
GUARD_CACHE_HITS = Counter(
    "aos_guard_cache_hits_total",
    "Guard cache hits",
    ["endpoint"],
)

GUARD_CACHE_MISSES = Counter(
    "aos_guard_cache_misses_total",
    "Guard cache misses",
    ["endpoint"],
)

GUARD_CACHE_LATENCY = Histogram(
    "aos_guard_cache_latency_seconds",
    "Guard cache lookup latency",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
)


class GuardCache:
    """
    Redis-based cache for Guard Console API.

    Usage:
        cache = GuardCache()

        # Check cache first
        data = await cache.get_status(tenant_id)
        if data is None:
            data = fetch_from_db(...)
            await cache.set_status(tenant_id, data)
    """

    _instance: Optional["GuardCache"] = None

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._enabled = GUARD_CACHE_ENABLED
        logger.info(f"GuardCache initialized (enabled={self._enabled})")

    @classmethod
    def get_instance(cls) -> "GuardCache":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _get_redis(self):
        """Get Redis client, initializing if needed."""
        if self._redis is not None:
            return self._redis

        redis_url = os.getenv("REDIS_URL", "")
        if not redis_url:
            logger.debug("REDIS_URL not set, guard cache disabled")
            return None

        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            return self._redis
        except ImportError:
            logger.warning("redis package not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return None

    def _make_key(self, endpoint: str, tenant_id: str, extra: str = "") -> str:
        """Generate cache key."""
        key = f"{GUARD_CACHE_PREFIX}{endpoint}:{tenant_id}"
        if extra:
            key += f":{extra}"
        return key

    async def get(self, endpoint: str, tenant_id: str, extra: str = "") -> Optional[Dict]:
        """Get cached data."""
        if not self._enabled:
            return None

        import time

        start = time.perf_counter()

        try:
            redis = await self._get_redis()
            if not redis:
                return None

            key = self._make_key(endpoint, tenant_id, extra)
            data = await redis.get(key)

            latency = time.perf_counter() - start
            GUARD_CACHE_LATENCY.observe(latency)

            if data:
                GUARD_CACHE_HITS.labels(endpoint=endpoint).inc()
                return json.loads(data)
            else:
                GUARD_CACHE_MISSES.labels(endpoint=endpoint).inc()
                return None

        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(self, endpoint: str, tenant_id: str, data: Dict, ttl: int, extra: str = "") -> bool:
        """Set cached data."""
        if not self._enabled:
            return False

        try:
            redis = await self._get_redis()
            if not redis:
                return False

            key = self._make_key(endpoint, tenant_id, extra)
            await redis.setex(key, ttl, json.dumps(data, default=str))
            return True

        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def invalidate(self, endpoint: str, tenant_id: str, extra: str = "") -> bool:
        """Invalidate cached data."""
        try:
            redis = await self._get_redis()
            if not redis:
                return False

            key = self._make_key(endpoint, tenant_id, extra)
            await redis.delete(key)
            return True

        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
            return False

    # Convenience methods
    async def get_status(self, tenant_id: str) -> Optional[Dict]:
        """Get cached guard status."""
        return await self.get("status", tenant_id)

    async def set_status(self, tenant_id: str, data: Dict) -> bool:
        """Cache guard status."""
        return await self.set("status", tenant_id, data, GUARD_STATUS_TTL)

    async def get_snapshot(self, tenant_id: str) -> Optional[Dict]:
        """Get cached today snapshot."""
        return await self.get("snapshot", tenant_id)

    async def set_snapshot(self, tenant_id: str, data: Dict) -> bool:
        """Cache today snapshot."""
        return await self.set("snapshot", tenant_id, data, GUARD_SNAPSHOT_TTL)

    async def get_incidents(self, tenant_id: str, limit: int = 10, offset: int = 0) -> Optional[Dict]:
        """Get cached incidents list."""
        extra = f"{limit}:{offset}"
        return await self.get("incidents", tenant_id, extra)

    async def set_incidents(self, tenant_id: str, data: Dict, limit: int = 10, offset: int = 0) -> bool:
        """Cache incidents list."""
        extra = f"{limit}:{offset}"
        return await self.set("incidents", tenant_id, data, GUARD_INCIDENTS_TTL, extra)

    async def invalidate_tenant(self, tenant_id: str) -> int:
        """Invalidate all cache for a tenant (on mutations)."""
        try:
            redis = await self._get_redis()
            if not redis:
                return 0

            pattern = f"{GUARD_CACHE_PREFIX}*:{tenant_id}*"
            keys = []
            async for key in redis.scan_iter(pattern):
                keys.append(key)

            if keys:
                await redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys for {tenant_id}")

            return len(keys)

        except Exception as e:
            logger.warning(f"Cache invalidate_tenant error: {e}")
            return 0


# Singleton accessor
def get_guard_cache() -> GuardCache:
    """Get guard cache singleton."""
    return GuardCache.get_instance()


__all__ = ["GuardCache", "get_guard_cache", "GUARD_STATUS_TTL", "GUARD_SNAPSHOT_TTL", "GUARD_INCIDENTS_TTL"]
