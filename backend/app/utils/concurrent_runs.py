# Concurrent Runs Limiter
# Limits concurrent runs per agent/tenant using Redis semaphore

import logging
import os
import uuid
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger("nova.utils.concurrent_runs")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_SLOT_TIMEOUT = int(os.getenv("CONCURRENT_SLOT_TIMEOUT", "3600"))  # 1 hour


class ConcurrentRunsLimiter:
    """Limits concurrent runs using Redis-based semaphore.

    Uses Redis sets to track active runs per key.
    Automatically expires slots after timeout.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        slot_timeout: int = DEFAULT_SLOT_TIMEOUT,
        fail_open: bool = True,
    ):
        """Initialize concurrent runs limiter.

        Args:
            redis_url: Redis connection URL
            slot_timeout: Seconds before a slot auto-expires
            fail_open: If True, allow runs when Redis fails
        """
        self.redis_url = redis_url or REDIS_URL
        self.slot_timeout = slot_timeout
        self.fail_open = fail_open
        self._client = None

    def _get_client(self):
        """Lazy-load Redis client."""
        if self._client is None:
            try:
                import redis
                self._client = redis.from_url(self.redis_url)
                logger.info("concurrent_limiter_connected")
            except ImportError:
                raise ImportError("redis package required: pip install redis")
            except Exception as e:
                logger.error("redis_connection_failed", extra={"error": str(e)})
                self._client = None
        return self._client

    def acquire(self, key: str, max_slots: int) -> Optional[str]:
        """Try to acquire a slot for concurrent run.

        Args:
            key: Unique key (e.g., "agent:{id}" or "tenant:{id}")
            max_slots: Maximum concurrent runs allowed

        Returns:
            Token string if acquired, None if limit reached
        """
        if max_slots <= 0:
            return str(uuid.uuid4())  # No limit

        slot_key = f"concurrent:{key}"
        token = str(uuid.uuid4())

        try:
            client = self._get_client()
            if client is None:
                return token if self.fail_open else None

            # Use sorted set with timestamp for auto-expiry
            now = int(uuid.uuid1().time)

            # Clean up expired slots first
            client.zremrangebyscore(slot_key, 0, now - (self.slot_timeout * 10_000_000))

            # Check current count
            current_count = client.zcard(slot_key)
            if current_count >= max_slots:
                logger.warning(
                    "concurrent_limit_reached",
                    extra={"key": key, "max_slots": max_slots, "current": current_count}
                )
                return None

            # Add new slot
            client.zadd(slot_key, {token: now})
            client.expire(slot_key, self.slot_timeout * 2)

            logger.debug(
                "slot_acquired",
                extra={"key": key, "token": token[:8], "count": current_count + 1}
            )

            return token

        except Exception as e:
            logger.error("concurrent_limiter_error", extra={"error": str(e), "key": key})
            return token if self.fail_open else None

    def release(self, key: str, token: str) -> bool:
        """Release a slot.

        Args:
            key: The key used when acquiring
            token: The token returned from acquire()

        Returns:
            True if released, False if not found
        """
        slot_key = f"concurrent:{key}"

        try:
            client = self._get_client()
            if client is None:
                return True

            removed = client.zrem(slot_key, token)
            if removed:
                logger.debug("slot_released", extra={"key": key, "token": token[:8]})
            return bool(removed)

        except Exception as e:
            logger.error("slot_release_error", extra={"error": str(e)})
            return False

    def get_count(self, key: str) -> int:
        """Get current count of active slots.

        Args:
            key: The key to check

        Returns:
            Number of active slots
        """
        slot_key = f"concurrent:{key}"

        try:
            client = self._get_client()
            if client is None:
                return 0

            return client.zcard(slot_key)

        except Exception:
            return 0

    @contextmanager
    def slot(self, key: str, max_slots: int):
        """Context manager for acquiring/releasing a slot.

        Args:
            key: Unique key for limiting
            max_slots: Maximum concurrent runs

        Yields:
            Token if acquired

        Raises:
            RuntimeError: If slot cannot be acquired
        """
        token = self.acquire(key, max_slots)
        if token is None:
            raise RuntimeError(f"Concurrent run limit reached for {key}")

        try:
            yield token
        finally:
            self.release(key, token)


# Singleton instance
_limiter: Optional[ConcurrentRunsLimiter] = None


def get_concurrent_limiter() -> ConcurrentRunsLimiter:
    """Get the singleton concurrent runs limiter."""
    global _limiter
    if _limiter is None:
        _limiter = ConcurrentRunsLimiter()
    return _limiter


@contextmanager
def acquire_slot(key: str, max_slots: int):
    """Convenience context manager for acquiring a slot.

    Args:
        key: Unique key (e.g., "agent:{agent_id}")
        max_slots: Maximum concurrent runs

    Yields:
        Token string

    Raises:
        RuntimeError: If limit reached
    """
    with get_concurrent_limiter().slot(key, max_slots) as token:
        yield token
