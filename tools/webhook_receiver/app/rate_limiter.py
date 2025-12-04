# tools/webhook_receiver/app/rate_limiter.py
"""
Redis-backed distributed rate limiter for webhook receiver.

Features:
- Per-IP and per-tenant rate limiting
- Fail-open behavior when Redis unavailable
- Prometheus metrics for monitoring
- Sliding window counter algorithm

Usage:
    from rate_limiter import RedisRateLimiter

    limiter = RedisRateLimiter(redis_url="redis://localhost:6379/0")
    await limiter.init()

    allowed = await limiter.allow_request(tenant_id="tenant-1", ip="1.2.3.4", rpm=100)
    if not allowed:
        raise HTTPException(status_code=429)
"""

import asyncio
import logging
import os
import time
from typing import Optional

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger("webhook.rate_limiter")

# Prometheus Metrics
RATE_LIMIT_EXCEEDED = Counter(
    "webhook_rate_limit_exceeded_total",
    "Number of requests rejected due to rate limiting",
    ["limit_type"]  # "ip" or "tenant"
)

RATE_LIMIT_REDIS_ERRORS = Counter(
    "webhook_rate_limit_redis_errors_total",
    "Redis errors when rate-limiting (fail-open triggered)"
)

RATE_LIMIT_ALLOWED = Counter(
    "webhook_rate_limit_allowed_total",
    "Number of requests allowed by rate limiter"
)

RATE_LIMIT_REDIS_CONNECTED = Gauge(
    "webhook_rate_limit_redis_connected",
    "Whether Redis connection is healthy (1=connected, 0=disconnected)"
)

RATE_LIMIT_REDIS_LATENCY = Histogram(
    "webhook_rate_limit_redis_latency_seconds",
    "Redis operation latency for rate limiting",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_RPM = int(os.getenv("RATE_LIMIT_RPM", "100"))
DEFAULT_WINDOW_SECONDS = 60


class RedisRateLimiter:
    """
    Distributed rate limiter using Redis.

    Implements a sliding window counter with:
    - Per-IP limiting (prevents single IP from overwhelming)
    - Per-tenant limiting (prevents single tenant from monopolizing)
    - Fail-open behavior (allows requests if Redis unavailable)
    """

    def __init__(
        self,
        redis_url: str = REDIS_URL,
        default_rpm: int = DEFAULT_RPM,
        window_seconds: int = DEFAULT_WINDOW_SECONDS
    ):
        self.redis_url = redis_url
        self.default_rpm = default_rpm
        self.window_seconds = window_seconds
        self._client = None
        self._connected = False

    async def init(self) -> bool:
        """
        Initialize Redis connection.

        Returns:
            True if connected successfully, False otherwise
        """
        if self._client is not None:
            return self._connected

        try:
            # Use redis-py async client (redis>=4.2.0)
            import redis.asyncio as aioredis

            self._client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Test connection
            await self._client.ping()
            self._connected = True
            RATE_LIMIT_REDIS_CONNECTED.set(1)
            logger.info(f"Redis rate limiter connected to {self.redis_url}")
            return True

        except ImportError:
            logger.error("redis package not installed. Install with: pip install redis>=4.2.0")
            self._connected = False
            RATE_LIMIT_REDIS_CONNECTED.set(0)
            return False

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Rate limiting will fail-open.")
            self._connected = False
            RATE_LIMIT_REDIS_CONNECTED.set(0)
            return False

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._connected = False
            RATE_LIMIT_REDIS_CONNECTED.set(0)

    async def _incr_with_expiry(self, key: str, window_seconds: int) -> int:
        """
        Increment counter and set expiry if new.

        Uses INCR + EXPIRE in a pipeline for atomicity.
        """
        try:
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            results = await pipe.execute()
            return int(results[0])

        except Exception as e:
            RATE_LIMIT_REDIS_ERRORS.inc()
            logger.warning(f"Redis INCR error for {key}: {e}")
            raise

    async def allow_request(
        self,
        tenant_id: str,
        ip: str,
        rpm: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> bool:
        """
        Check if request should be allowed.

        Args:
            tenant_id: Tenant identifier (from header or token)
            ip: Client IP address
            rpm: Requests per minute limit (uses default if not specified)
            request_id: Optional request ID for log correlation

        Returns:
            True if request allowed, False if rate limited

        Note:
            Fails open (returns True) if Redis unavailable
        """
        if rpm is None:
            rpm = self.default_rpm

        # If not connected, try to reconnect
        if not self._connected:
            await self.init()

        # If still not connected, fail-open
        if not self._connected or self._client is None:
            logger.debug(
                f"Redis unavailable, failing open | "
                f"tenant_id={tenant_id} ip={ip} request_id={request_id}"
            )
            RATE_LIMIT_ALLOWED.inc()
            return True

        # Key format: rate:{tenant}:{ip}:{minute}
        # Using consistent prefix to avoid key collisions with other Redis usage
        minute = int(time.time()) // self.window_seconds
        per_ip_key = f"rate:{tenant_id}:{ip}:{minute}"
        per_tenant_key = f"rate:{tenant_id}:_tenant:{minute}"

        try:
            # Track Redis latency
            start_time = time.perf_counter()

            # Increment both counters concurrently
            ip_count, tenant_count = await asyncio.gather(
                self._incr_with_expiry(per_ip_key, self.window_seconds + 1),
                self._incr_with_expiry(per_tenant_key, self.window_seconds + 1)
            )

            # Record latency
            latency_seconds = time.perf_counter() - start_time
            latency_ms = latency_seconds * 1000
            RATE_LIMIT_REDIS_LATENCY.observe(latency_seconds)

            # Check if either limit exceeded
            if ip_count > rpm:
                RATE_LIMIT_EXCEEDED.labels(limit_type="ip").inc()
                logger.info(
                    f"Rate limit exceeded for IP | "
                    f"tenant_id={tenant_id} ip={ip} request_id={request_id} "
                    f"count={ip_count}/{rpm} redis_latency_ms={latency_ms:.2f}"
                )
                return False

            if tenant_count > rpm:
                RATE_LIMIT_EXCEEDED.labels(limit_type="tenant").inc()
                logger.info(
                    f"Rate limit exceeded for tenant | "
                    f"tenant_id={tenant_id} ip={ip} request_id={request_id} "
                    f"count={tenant_count}/{rpm} redis_latency_ms={latency_ms:.2f}"
                )
                return False

            RATE_LIMIT_ALLOWED.inc()
            return True

        except Exception as e:
            # Redis error -> fail-open
            logger.warning(
                f"Rate limit check failed, allowing request | "
                f"tenant_id={tenant_id} ip={ip} request_id={request_id} "
                f"error={str(e)[:100]}"
            )
            RATE_LIMIT_ALLOWED.inc()
            return True

    async def get_current_counts(self, tenant_id: str, ip: str) -> dict:
        """
        Get current request counts for debugging.

        Returns:
            Dict with ip_count and tenant_count
        """
        if not self._connected or self._client is None:
            return {"ip_count": -1, "tenant_count": -1, "error": "not_connected"}

        try:
            window = int(time.time()) // self.window_seconds
            # Key format: rate:{tenant}:{ip}:{minute}
            per_ip_key = f"rate:{tenant_id}:{ip}:{window}"
            per_tenant_key = f"rate:{tenant_id}:_tenant:{window}"

            ip_count = await self._client.get(per_ip_key)
            tenant_count = await self._client.get(per_tenant_key)

            return {
                "ip_count": int(ip_count) if ip_count else 0,
                "tenant_count": int(tenant_count) if tenant_count else 0,
                "window": window,
                "rpm_limit": self.default_rpm
            }
        except Exception as e:
            return {"error": str(e)}

    async def reset_limits(self, tenant_id: Optional[str] = None, ip: Optional[str] = None):
        """
        Reset rate limit counters (for testing/admin).

        Args:
            tenant_id: Reset tenant counter
            ip: Reset IP counter
        """
        if not self._connected or self._client is None:
            return

        try:
            window = int(time.time()) // self.window_seconds

            if ip and tenant_id:
                # Key format: rate:{tenant}:{ip}:{minute}
                key = f"rate:{tenant_id}:{ip}:{window}"
                await self._client.delete(key)

            if tenant_id:
                # Tenant aggregate key
                key = f"rate:{tenant_id}:_tenant:{window}"
                await self._client.delete(key)

        except Exception as e:
            logger.warning(f"Failed to reset limits: {e}")


# Singleton instance
_rate_limiter: Optional[RedisRateLimiter] = None


def get_rate_limiter() -> RedisRateLimiter:
    """Get or create singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RedisRateLimiter()
    return _rate_limiter


async def init_rate_limiter() -> RedisRateLimiter:
    """Initialize and return rate limiter."""
    limiter = get_rate_limiter()
    await limiter.init()
    return limiter
