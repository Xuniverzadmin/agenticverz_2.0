# capability_id: CAP-012
# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: worker (job execution)
#   Execution: async
# Role: Idempotency guarantees for job execution
# Callers: JobQueueWorker, lifecycle handlers
# Allowed Imports: L6 (Redis)
# Forbidden Imports: L1, L2, L3, L4
# Reference: INV-W0-003

"""
Module: idempotency
Purpose: Ensure job execution is idempotent by (job_id, plane_id).

INV-W0-003: Same (job_id, plane_id) MUST produce same result.

Network failures, restarts, and retries can cause duplicate job execution.
Without idempotency, side effects multiply.

Features:
    - Distributed idempotency via Redis
    - TTL-based key expiration
    - Cached result return for duplicates
    - Support for retry on transient failures

Acceptance Criteria:
    - IDEM-001: All state-mutating jobs use IdempotencyKey
    - IDEM-002: Duplicate calls return cached result
    - IDEM-003: Failed jobs can retry (unless permanent)
    - IDEM-004: TTL prevents unbounded growth
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("nova.worker.idempotency")


@dataclass(frozen=True)
class IdempotencyKey:
    """
    Idempotency key for job execution.

    INVARIANT: Same (job_id, plane_id) MUST produce same result.

    The key is a deterministic hash of job_id and plane_id to ensure
    uniqueness across distributed workers.
    """

    job_id: str
    plane_id: str

    def __post_init__(self):
        if not self.job_id:
            raise ValueError("IdempotencyKey requires job_id")
        if not self.plane_id:
            raise ValueError("IdempotencyKey requires plane_id")

    @property
    def key(self) -> str:
        """
        Compute stable idempotency key.

        Returns SHA256 hash of "{job_id}:{plane_id}" truncated to 32 chars.
        """
        payload = f"{self.job_id}:{self.plane_id}"
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    def __str__(self) -> str:
        return f"idem:{self.key}"


class JobAlreadyProcessingException(Exception):
    """
    Raised when attempting to process a job already in progress.

    This is a transient condition - the caller should wait or back off.
    """

    def __init__(self, idem_key: IdempotencyKey):
        self.idem_key = idem_key
        super().__init__(
            f"Job {idem_key.job_id} is already being processed (key: {idem_key.key})"
        )


class IdempotencyStore:
    """
    Store for tracking idempotent job executions.

    Uses Redis with TTL for distributed idempotency across workers.

    States:
        - Key not exists: Job not started
        - Key = "processing": Job in progress
        - Key = JSON result: Job completed

    TTL ensures keys expire after configured duration (default 24h).
    """

    PROCESSING_MARKER = "processing"

    def __init__(
        self,
        redis_client: Any = None,
        ttl_hours: int = 24,
        key_prefix: str = "aos:idem:",
    ):
        """
        Initialize IdempotencyStore.

        Args:
            redis_client: Redis client instance (async or sync)
            ttl_hours: TTL for idempotency keys in hours
            key_prefix: Prefix for Redis keys
        """
        self._redis = redis_client
        self._ttl = timedelta(hours=ttl_hours)
        self._key_prefix = key_prefix

    def _full_key(self, idem_key: IdempotencyKey) -> str:
        """Get full Redis key."""
        return f"{self._key_prefix}{idem_key.key}"

    async def check_and_acquire(
        self,
        idem_key: IdempotencyKey,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if job was already executed or acquire lock.

        Args:
            idem_key: Idempotency key for the job

        Returns:
            Tuple of (is_new, cached_result):
            - (True, None): First execution, lock acquired
            - (False, result): Already completed, return cached result

        Raises:
            JobAlreadyProcessingException: If job is currently in progress
        """
        if self._redis is None:
            # No Redis - allow execution (not ideal for production)
            logger.warning(
                "idempotency.no_redis",
                extra={"key": idem_key.key, "action": "allowing_execution"},
            )
            return (True, None)

        key = self._full_key(idem_key)

        try:
            # Try to acquire lock with NX (only if not exists)
            acquired = await self._redis.set(
                key,
                self.PROCESSING_MARKER,
                nx=True,  # Only set if not exists
                ex=int(self._ttl.total_seconds()),
            )

            if acquired:
                logger.debug(
                    "idempotency.lock_acquired",
                    extra={"key": idem_key.key, "job_id": idem_key.job_id},
                )
                return (True, None)

            # Key exists - check if processing or completed
            value = await self._redis.get(key)

            if value is None:
                # Race condition - key was deleted between check and get
                # Try again
                return await self.check_and_acquire(idem_key)

            if isinstance(value, bytes):
                value = value.decode("utf-8")

            if value == self.PROCESSING_MARKER:
                # Still processing - raise exception
                logger.info(
                    "idempotency.already_processing",
                    extra={"key": idem_key.key, "job_id": idem_key.job_id},
                )
                raise JobAlreadyProcessingException(idem_key)

            # Completed - return cached result
            try:
                cached_result = json.loads(value)
                logger.info(
                    "idempotency.returning_cached",
                    extra={"key": idem_key.key, "job_id": idem_key.job_id},
                )
                return (False, cached_result)
            except json.JSONDecodeError:
                # Invalid cached value - treat as new
                logger.warning(
                    "idempotency.invalid_cached_value",
                    extra={"key": idem_key.key, "value": value[:100]},
                )
                return (True, None)

        except JobAlreadyProcessingException:
            raise
        except Exception as e:
            logger.error(
                "idempotency.check_failed",
                extra={"key": idem_key.key, "error": str(e)},
            )
            # On error, allow execution (fail-open for availability)
            return (True, None)

    async def mark_complete(
        self,
        idem_key: IdempotencyKey,
        result: Dict[str, Any],
    ) -> None:
        """
        Mark job as complete with result.

        The result is cached for TTL duration, allowing duplicate calls
        to return the same result without re-execution.

        Args:
            idem_key: Idempotency key for the job
            result: Result to cache (must be JSON-serializable)
        """
        if self._redis is None:
            logger.warning(
                "idempotency.no_redis_mark_complete",
                extra={"key": idem_key.key},
            )
            return

        key = self._full_key(idem_key)

        try:
            serialized = json.dumps(result, default=str)
            await self._redis.set(
                key,
                serialized,
                ex=int(self._ttl.total_seconds()),
            )

            logger.debug(
                "idempotency.marked_complete",
                extra={"key": idem_key.key, "job_id": idem_key.job_id},
            )

        except Exception as e:
            logger.error(
                "idempotency.mark_complete_failed",
                extra={"key": idem_key.key, "error": str(e)},
            )

    async def mark_failed(
        self,
        idem_key: IdempotencyKey,
        allow_retry: bool = True,
    ) -> None:
        """
        Mark job as failed.

        Args:
            idem_key: Idempotency key for the job
            allow_retry: If True, delete key to allow retry.
                        If False, mark as permanently failed.
        """
        if self._redis is None:
            return

        key = self._full_key(idem_key)

        try:
            if allow_retry:
                # Delete key to allow retry
                await self._redis.delete(key)
                logger.debug(
                    "idempotency.key_deleted_for_retry",
                    extra={"key": idem_key.key, "job_id": idem_key.job_id},
                )
            else:
                # Mark as permanently failed
                await self._redis.set(
                    key,
                    json.dumps({"status": "permanently_failed"}),
                    ex=int(self._ttl.total_seconds()),
                )
                logger.warning(
                    "idempotency.marked_permanently_failed",
                    extra={"key": idem_key.key, "job_id": idem_key.job_id},
                )

        except Exception as e:
            logger.error(
                "idempotency.mark_failed_error",
                extra={"key": idem_key.key, "error": str(e)},
            )

    async def clear(self, idem_key: IdempotencyKey) -> None:
        """
        Clear idempotency key (for testing or manual cleanup).

        Args:
            idem_key: Idempotency key to clear
        """
        if self._redis is None:
            return

        key = self._full_key(idem_key)
        await self._redis.delete(key)


# Singleton instance
_idempotency_store: Optional[IdempotencyStore] = None


def get_idempotency_store() -> IdempotencyStore:
    """
    Get or create singleton IdempotencyStore.

    Uses Redis URL from environment variable REDIS_URL.
    """
    global _idempotency_store

    if _idempotency_store is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis.asyncio as redis

                client = redis.from_url(redis_url)
                _idempotency_store = IdempotencyStore(redis_client=client)
                logger.info("idempotency_store.created_with_redis")
            except Exception as e:
                logger.error(
                    "idempotency_store.redis_init_failed",
                    extra={"error": str(e)},
                )
                _idempotency_store = IdempotencyStore()  # No Redis
        else:
            logger.warning("idempotency_store.no_redis_url")
            _idempotency_store = IdempotencyStore()

    return _idempotency_store


def configure_idempotency_store(
    redis_client: Any = None,
    ttl_hours: int = 24,
) -> IdempotencyStore:
    """
    Configure singleton IdempotencyStore with custom settings.

    Args:
        redis_client: Redis client instance
        ttl_hours: TTL for keys in hours

    Returns:
        Configured IdempotencyStore
    """
    global _idempotency_store

    _idempotency_store = IdempotencyStore(
        redis_client=redis_client,
        ttl_hours=ttl_hours,
    )

    logger.info(
        "idempotency_store.configured",
        extra={
            "ttl_hours": ttl_hours,
            "has_redis": redis_client is not None,
        },
    )

    return _idempotency_store
