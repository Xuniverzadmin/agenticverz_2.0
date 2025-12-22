# Rate Limiter
# Token bucket rate limiting using Redis

import logging
import os
import time
from typing import Optional

logger = logging.getLogger("nova.utils.rate_limiter")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Lua script for atomic token bucket operation
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local rate = tonumber(ARGV[1])
local now_ts = tonumber(ARGV[2])

local bucket = redis.call("HMGET", key, "tokens", "last")
local tokens = tonumber(bucket[1]) or rate
local last = tonumber(bucket[2]) or now_ts

local elapsed = math.max(0, now_ts - last)
local refill = (elapsed / 60) * rate
tokens = math.min(rate, tokens + refill)

if tokens < 1 then
    redis.call("HMSET", key, "tokens", tokens, "last", now_ts)
    redis.call("EXPIRE", key, 120)
    return 0
else
    tokens = tokens - 1
    redis.call("HMSET", key, "tokens", tokens, "last", now_ts)
    redis.call("EXPIRE", key, 120)
    return 1
end
"""


class RateLimiter:
    """Token bucket rate limiter using Redis.

    Provides per-key rate limiting with configurable RPM.
    Falls back to allowing requests if Redis is unavailable.
    """

    def __init__(self, redis_url: Optional[str] = None, fail_open: bool = True):
        """Initialize rate limiter.

        Args:
            redis_url: Redis connection URL
            fail_open: If True, allow requests when Redis fails
        """
        self.redis_url = redis_url or REDIS_URL
        self.fail_open = fail_open
        self._client = None
        self._script_sha = None

    def _get_client(self):
        """Lazy-load Redis client."""
        if self._client is None:
            try:
                import redis

                self._client = redis.from_url(self.redis_url)
                # Pre-load the Lua script
                self._script_sha = self._client.script_load(TOKEN_BUCKET_LUA)
                logger.info("rate_limiter_connected", extra={"url": self.redis_url[:20] + "..."})
            except ImportError:
                logger.error("redis package not installed - pip install redis")
                raise ImportError("redis package required: pip install redis")
            except Exception as e:
                logger.error("redis_connection_failed", extra={"error": str(e)})
                self._client = None
        return self._client

    def allow(self, key: str, rate_per_min: int) -> bool:
        """Check if request should be allowed.

        Args:
            key: Unique key for rate limiting (e.g., "agent:{id}" or "tenant:{id}")
            rate_per_min: Maximum requests per minute

        Returns:
            True if allowed, False if rate limited
        """
        if rate_per_min <= 0:
            return True  # No limit configured

        bucket_key = f"rate:{key}"
        now = int(time.time())

        try:
            client = self._get_client()
            if client is None:
                return self.fail_open

            # Execute Lua script atomically
            if self._script_sha:
                result = client.evalsha(self._script_sha, 1, bucket_key, rate_per_min, now)
            else:
                result = client.eval(TOKEN_BUCKET_LUA, 1, bucket_key, rate_per_min, now)

            allowed = bool(result)

            if not allowed:
                logger.warning("rate_limited", extra={"key": key, "rate_per_min": rate_per_min})

            return allowed

        except Exception as e:
            logger.error("rate_limiter_error", extra={"error": str(e), "key": key})
            return self.fail_open

    def get_remaining(self, key: str, rate_per_min: int) -> int:
        """Get remaining tokens for a key.

        Args:
            key: Rate limit key
            rate_per_min: Configured rate

        Returns:
            Estimated remaining tokens
        """
        bucket_key = f"rate:{key}"
        try:
            client = self._get_client()
            if client is None:
                return rate_per_min

            data = client.hgetall(bucket_key)
            if not data:
                return rate_per_min

            tokens = float(data.get(b"tokens", rate_per_min))
            return max(0, int(tokens))

        except Exception:
            return rate_per_min


# Singleton instance
_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the singleton rate limiter instance."""
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter


def allow_request(key: str, rate_per_min: int) -> bool:
    """Convenience function to check rate limit.

    Args:
        key: Rate limit key
        rate_per_min: Max requests per minute

    Returns:
        True if allowed
    """
    return get_rate_limiter().allow(key, rate_per_min)
