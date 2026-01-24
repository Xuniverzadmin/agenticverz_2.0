# M12 Blackboard Service
# Shared Redis blackboard for agent coordination
#
# Features:
# - KV read/write
# - Atomic increment
# - Pattern read (SCAN)
# - Distributed locks (SET NX)

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis

logger = logging.getLogger("nova.agents.blackboard_service")

# Default key prefix
KEY_PREFIX = "agents:blackboard:"
LOCK_PREFIX = "agents:lock:"
RESULT_PREFIX = "agents:job:"


@dataclass
class BlackboardEntry:
    """Entry in the blackboard."""

    key: str
    value: Any
    ttl: Optional[int] = None


@dataclass
class LockResult:
    """Result of a lock operation."""

    acquired: bool
    lock_key: str
    ttl: Optional[int] = None
    holder: Optional[str] = None


class BlackboardService:
    """
    Shared blackboard for M12 multi-agent coordination.

    Uses Redis for:
    - Fast KV operations
    - Atomic counters
    - Pattern matching
    - Distributed locks
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        key_prefix: str = KEY_PREFIX,
    ):
        self.redis_url = redis_url if redis_url is not None else os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.key_prefix = key_prefix
        self.lock_prefix = LOCK_PREFIX
        self.result_prefix = RESULT_PREFIX

        self.redis = redis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )

    def _key(self, key: str) -> str:
        """Build full Redis key."""
        return f"{self.key_prefix}{key}"

    def _lock_key(self, key: str) -> str:
        """Build lock key."""
        return f"{self.lock_prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from blackboard.

        Args:
            key: Blackboard key

        Returns:
            Value or None if not found
        """
        try:
            value = self.redis.get(self._key(key))
            if value is None:
                return None

            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except Exception as e:
            logger.warning(f"Blackboard get failed: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in blackboard.

        Args:
            key: Blackboard key
            value: Value to store (will be JSON serialized)
            ttl: Optional TTL in seconds

        Returns:
            True if set successfully
        """
        try:
            # JSON serialize non-string values
            if not isinstance(value, str):
                value = json.dumps(value)

            if ttl:
                self.redis.setex(self._key(key), ttl, value)
            else:
                self.redis.set(self._key(key), value)

            return True

        except Exception as e:
            logger.warning(f"Blackboard set failed: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from blackboard."""
        try:
            self.redis.delete(self._key(key))
            return True
        except Exception as e:
            logger.warning(f"Blackboard delete failed: {e}")
            return False

    def increment(
        self,
        key: str,
        amount: int = 1,
    ) -> Optional[int]:
        """
        Atomically increment a counter.

        Args:
            key: Counter key
            amount: Increment amount (can be negative)

        Returns:
            New value or None on error
        """
        try:
            return int(self.redis.incrby(self._key(key), amount))
        except Exception as e:
            logger.warning(f"Blackboard increment failed: {e}")
            return None

    def increment_float(
        self,
        key: str,
        amount: float = 1.0,
    ) -> Optional[float]:
        """
        Atomically increment a float counter.

        Args:
            key: Counter key
            amount: Increment amount

        Returns:
            New value or None on error
        """
        try:
            return self.redis.incrbyfloat(self._key(key), amount)
        except Exception as e:
            logger.warning(f"Blackboard increment_float failed: {e}")
            return None

    def scan_pattern(
        self,
        pattern: str,
        count: int = 100,
    ) -> List[BlackboardEntry]:
        """
        Scan for keys matching pattern.

        Args:
            pattern: Glob pattern (e.g., "job:*:result")
            count: Max results to return

        Returns:
            List of matching entries
        """
        entries = []
        full_pattern = f"{self.key_prefix}{pattern}"

        try:
            cursor = 0
            while len(entries) < count:
                cursor, keys = self.redis.scan(cursor, match=full_pattern, count=100)

                for key in keys:
                    if len(entries) >= count:
                        break

                    # Get value and TTL
                    value = self.redis.get(key)
                    ttl = self.redis.ttl(key)

                    # Strip prefix from key
                    short_key = key[len(self.key_prefix) :] if key.startswith(self.key_prefix) else key

                    # Try to parse JSON
                    try:
                        parsed = json.loads(value) if value else None
                    except (json.JSONDecodeError, TypeError):
                        parsed = value

                    entries.append(
                        BlackboardEntry(
                            key=short_key,
                            value=parsed,
                            ttl=ttl if ttl > 0 else None,
                        )
                    )

                if cursor == 0:
                    break

        except Exception as e:
            logger.warning(f"Blackboard scan failed: {e}")

        return entries

    def acquire_lock(
        self,
        key: str,
        holder: str,
        ttl: int = 30,
    ) -> LockResult:
        """
        Acquire a distributed lock.

        Uses SET NX (set if not exists) for atomic lock acquisition.

        Args:
            key: Lock name
            holder: Identity of lock holder
            ttl: Lock TTL in seconds (prevents deadlocks)

        Returns:
            LockResult with acquisition status
        """
        lock_key = self._lock_key(key)

        try:
            # SET NX with TTL
            acquired = self.redis.set(
                lock_key,
                holder,
                nx=True,
                ex=ttl,
            )

            if acquired:
                logger.debug(f"Lock acquired: {key} by {holder}")
                return LockResult(
                    acquired=True,
                    lock_key=key,
                    ttl=ttl,
                    holder=holder,
                )
            else:
                # Check who holds the lock
                current_holder = self.redis.get(lock_key)
                return LockResult(
                    acquired=False,
                    lock_key=key,
                    holder=current_holder,
                )

        except Exception as e:
            logger.warning(f"Lock acquire failed: {e}")
            return LockResult(
                acquired=False,
                lock_key=key,
            )

    def release_lock(
        self,
        key: str,
        holder: str,
    ) -> bool:
        """
        Release a lock (only if held by holder).

        Args:
            key: Lock name
            holder: Expected lock holder

        Returns:
            True if released, False if not held by holder
        """
        lock_key = self._lock_key(key)

        try:
            # Use Lua script for atomic check-and-delete
            script = """
                if redis.call('get', KEYS[1]) == ARGV[1] then
                    return redis.call('del', KEYS[1])
                else
                    return 0
                end
            """
            result = self.redis.eval(script, 1, lock_key, holder)
            released = result == 1

            if released:
                logger.debug(f"Lock released: {key} by {holder}")

            return bool(released)

        except Exception as e:
            logger.warning(f"Lock release failed: {e}")
            return False

    def extend_lock(
        self,
        key: str,
        holder: str,
        ttl: int = 30,
    ) -> bool:
        """
        Extend lock TTL (only if held by holder).

        Args:
            key: Lock name
            holder: Expected lock holder
            ttl: New TTL in seconds

        Returns:
            True if extended
        """
        lock_key = self._lock_key(key)

        try:
            # Use Lua script for atomic check-and-extend
            script = """
                if redis.call('get', KEYS[1]) == ARGV[1] then
                    return redis.call('expire', KEYS[1], ARGV[2])
                else
                    return 0
                end
            """
            result = self.redis.eval(script, 1, lock_key, holder, ttl)
            return bool(result == 1)

        except Exception as e:
            logger.warning(f"Lock extend failed: {e}")
            return False

    # === Job Result Storage ===

    def store_result(
        self,
        job_id: UUID,
        item_index: int,
        result: Any,
        ttl: int = 3600,
    ) -> bool:
        """
        Store job item result in blackboard.

        Args:
            job_id: Job ID
            item_index: Item index
            result: Result data
            ttl: TTL in seconds

        Returns:
            True if stored
        """
        key = f"job:{job_id}:results:{item_index}"
        return self.set(key, result, ttl=ttl)

    def get_results(
        self,
        job_id: UUID,
    ) -> Dict[int, Any]:
        """
        Get all results for a job.

        Args:
            job_id: Job ID

        Returns:
            Dict of item_index -> result
        """
        pattern = f"job:{job_id}:results:*"
        entries = self.scan_pattern(pattern, count=10000)

        results = {}
        for entry in entries:
            # Extract item index from key
            try:
                parts = entry.key.split(":")
                if len(parts) >= 4:
                    idx = int(parts[3])
                    results[idx] = entry.value
            except (ValueError, IndexError):
                continue

        return results

    def store_aggregate(
        self,
        job_id: UUID,
        aggregate: Any,
        ttl: int = 86400,
    ) -> bool:
        """
        Store aggregated job result.

        Args:
            job_id: Job ID
            aggregate: Aggregated result
            ttl: TTL in seconds (default 24h)

        Returns:
            True if stored
        """
        key = f"job:{job_id}:aggregate"
        return self.set(key, aggregate, ttl=ttl)

    def get_aggregate(self, job_id: UUID) -> Optional[Any]:
        """Get aggregated job result."""
        key = f"job:{job_id}:aggregate"
        return self.get(key)

    def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            return bool(self.redis.ping())
        except Exception:
            return False


# Singleton instance
_service: Optional[BlackboardService] = None


def get_blackboard_service() -> BlackboardService:
    """Get singleton blackboard service instance."""
    global _service
    if _service is None:
        _service = BlackboardService()
    return _service
