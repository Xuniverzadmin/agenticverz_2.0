# Layer: L5 — Execution & Workers
# Product: system-wide
# Wiring Type: worker
# Parent Gap: GAP-039 (JobScheduler)
# Reference: GAP-155
# Depends On: GAP-154 (APScheduler Executor), INV-W0-002 (KillSwitch), INV-W0-003 (Idempotency)
# Temporal:
#   Trigger: worker (startup)
#   Execution: async
# Role: Background worker that processes job queue
# Callers: Worker startup
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L3

"""
Module: job_queue_worker
Purpose: Background worker that processes job queue.

Wires:
    - Source: Redis job queue
    - Target: Job handlers via APSchedulerExecutor

Provides:
    - Job pickup from queue (Redis BLPOP)
    - Concurrent execution (configurable workers)
    - Dead letter queue for failed jobs
    - Graceful shutdown
    - Kill switch integration (INV-W0-002)
    - Idempotency enforcement (INV-W0-003)

Acceptance Criteria:
    - AC-155-01: Jobs are picked from Redis queue
    - AC-155-02: Concurrent workers process jobs
    - AC-155-03: Failed jobs go to dead letter queue
    - AC-155-04: Graceful shutdown waits for completion
    - AC-155-05: Kill switch is respected
    - AC-155-06: Idempotency prevents duplicate execution
"""

import asyncio
import json
import logging
import signal
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("nova.worker.job_queue_worker")


@dataclass
class WorkerConfig:
    """Configuration for the job queue worker."""

    # Redis connection
    redis_url: str = "redis://localhost:6379/0"

    # Queue names
    queue_name: str = "aos:job_queue"
    dead_letter_queue: str = "aos:job_queue:dead_letter"
    processing_queue: str = "aos:job_queue:processing"

    # Worker settings
    max_workers: int = 4
    poll_timeout: int = 1  # seconds
    max_retries: int = 3
    retry_delay_seconds: int = 60

    # Shutdown settings
    shutdown_timeout: int = 30


@dataclass
class JobMessage:
    """Message from the job queue."""

    job_id: str
    job_type: str
    tenant_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    created_at: Optional[str] = None
    capability: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobMessage":
        """Create from dictionary."""
        return cls(
            job_id=data.get("job_id", ""),
            job_type=data.get("job_type", ""),
            tenant_id=data.get("tenant_id", ""),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            retry_count=data.get("retry_count", 0),
            created_at=data.get("created_at"),
            capability=data.get("capability", "job.default"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "tenant_id": self.tenant_id,
            "payload": self.payload,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "capability": self.capability,
        }


@dataclass
class WorkerStats:
    """Statistics from the job queue worker."""

    jobs_processed: int = 0
    jobs_succeeded: int = 0
    jobs_failed: int = 0
    jobs_retried: int = 0
    jobs_dead_lettered: int = 0
    active_workers: int = 0
    started_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "jobs_processed": self.jobs_processed,
            "jobs_succeeded": self.jobs_succeeded,
            "jobs_failed": self.jobs_failed,
            "jobs_retried": self.jobs_retried,
            "jobs_dead_lettered": self.jobs_dead_lettered,
            "active_workers": self.active_workers,
            "started_at": self.started_at,
        }


class JobQueueWorker:
    """
    Background worker for processing job queue.

    Integrates with:
    - INV-W0-002 (KillSwitchGuard): Checks kill switch before/during execution
    - INV-W0-003 (IdempotencyStore): Ensures jobs are processed exactly once
    """

    def __init__(
        self,
        config: Optional[WorkerConfig] = None,
    ):
        """
        Initialize the job queue worker.

        Args:
            config: Worker configuration
        """
        self._config = config or WorkerConfig()
        self._redis: Optional[Any] = None
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._handlers: Dict[str, Callable] = {}
        self._stats = WorkerStats()
        self._shutdown_event = asyncio.Event()

    def register_handler(self, job_type: str, handler: Callable) -> None:
        """
        Register a handler for a job type.

        Args:
            job_type: Type of job to handle
            handler: Async callable (job_id, payload) -> None
        """
        self._handlers[job_type] = handler
        logger.debug(f"job_queue_worker.handler_registered: {job_type}")

    async def start(self) -> None:
        """
        Start the job queue worker.

        Connects to Redis and starts worker tasks.
        """
        if self._running:
            logger.warning("job_queue_worker.already_running")
            return

        try:
            import redis.asyncio as redis

            self._redis = await redis.from_url(self._config.redis_url)

            # Test connection
            await self._redis.ping()

            self._running = True
            self._stats.started_at = datetime.now(timezone.utc).isoformat()

            # Start worker tasks
            for i in range(self._config.max_workers):
                task = asyncio.create_task(self._worker_loop(i))
                self._tasks.append(task)
                self._stats.active_workers += 1

            logger.info(
                "job_queue_worker.started",
                extra={"workers": self._config.max_workers},
            )

        except ImportError:
            logger.error("job_queue_worker.redis_not_installed")
            raise RuntimeError("redis package not installed")

        except Exception as e:
            logger.error(
                "job_queue_worker.start_failed",
                extra={"error": str(e)},
            )
            raise

    async def stop(self) -> None:
        """
        Stop the job queue worker gracefully.

        Waits for running jobs to complete.
        """
        if not self._running:
            return

        logger.info("job_queue_worker.stopping")

        self._running = False
        self._shutdown_event.set()

        # Wait for tasks with timeout
        if self._tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=self._config.shutdown_timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("job_queue_worker.shutdown_timeout")
                for task in self._tasks:
                    task.cancel()

        self._tasks.clear()
        self._stats.active_workers = 0

        if self._redis:
            await self._redis.close()
            self._redis = None

        logger.info("job_queue_worker.stopped")

    async def enqueue(
        self,
        job_id: str,
        job_type: str,
        tenant_id: str,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        capability: Optional[str] = None,
    ) -> None:
        """
        Add a job to the queue.

        Args:
            job_id: Unique job identifier
            job_type: Type of job (maps to handler)
            tenant_id: Tenant identifier
            payload: Job payload data
            metadata: Additional metadata
            capability: Kill switch capability to check
        """
        if not self._redis:
            raise RuntimeError("Worker not started")

        message = JobMessage(
            job_id=job_id,
            job_type=job_type,
            tenant_id=tenant_id,
            payload=payload or {},
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc).isoformat(),
            capability=capability or "job.default",
        )

        await self._redis.rpush(
            self._config.queue_name,
            json.dumps(message.to_dict()),
        )

        logger.info(
            "job_queue_worker.job_enqueued",
            extra={"job_id": job_id, "job_type": job_type},
        )

    async def get_stats(self) -> WorkerStats:
        """Get worker statistics."""
        return self._stats

    async def _worker_loop(self, worker_id: int) -> None:
        """
        Worker loop — continuously pick and process jobs.

        Args:
            worker_id: Worker identifier for logging
        """
        logger.info(f"job_queue_worker.worker_started: {worker_id}")

        while self._running:
            try:
                # Check shutdown
                if self._shutdown_event.is_set():
                    break

                # Block waiting for job
                result = await asyncio.wait_for(
                    self._redis.blpop(
                        self._config.queue_name,
                        timeout=self._config.poll_timeout,
                    ),
                    timeout=self._config.poll_timeout + 1,
                )

                if result:
                    _, job_data = result
                    await self._process_job(worker_id, job_data)

            except asyncio.TimeoutError:
                continue

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(
                    "job_queue_worker.worker_error",
                    extra={"worker_id": worker_id, "error": str(e)},
                )
                await asyncio.sleep(1)

        logger.info(f"job_queue_worker.worker_stopped: {worker_id}")

    async def _process_job(self, worker_id: int, job_data: bytes) -> None:
        """
        Process a single job from the queue.

        Integrates:
        - INV-W0-002: Kill switch checks
        - INV-W0-003: Idempotency enforcement

        Args:
            worker_id: Worker identifier
            job_data: Raw job data from Redis
        """
        try:
            message = JobMessage.from_dict(json.loads(job_data))
        except Exception as e:
            logger.error(
                "job_queue_worker.parse_failed",
                extra={"error": str(e)},
            )
            return

        job_id = message.job_id
        self._stats.jobs_processed += 1

        logger.info(
            "job_queue_worker.processing",
            extra={
                "worker_id": worker_id,
                "job_id": job_id,
                "job_type": message.job_type,
            },
        )

        try:
            # INV-W0-002: Check kill switch
            if not await self._check_kill_switch(message):
                logger.warning(
                    "job_queue_worker.killed",
                    extra={"job_id": job_id},
                )
                await self._move_to_dead_letter(message, "Kill switch triggered")
                return

            # INV-W0-003: Check idempotency
            is_new, cached_result = await self._check_idempotency(message)
            if not is_new:
                logger.info(
                    "job_queue_worker.duplicate",
                    extra={"job_id": job_id},
                )
                return

            # Get handler
            handler = self._handlers.get(message.job_type)
            if not handler:
                logger.warning(
                    "job_queue_worker.no_handler",
                    extra={"job_id": job_id, "job_type": message.job_type},
                )
                await self._move_to_dead_letter(
                    message,
                    f"No handler for job type: {message.job_type}",
                )
                return

            # Execute handler
            await handler(job_id, message.payload)

            # Mark idempotency complete
            await self._mark_idempotency_complete(message, {"status": "completed"})

            self._stats.jobs_succeeded += 1
            logger.info(
                "job_queue_worker.completed",
                extra={"job_id": job_id},
            )

        except Exception as e:
            logger.error(
                "job_queue_worker.failed",
                extra={"job_id": job_id, "error": str(e)},
            )
            self._stats.jobs_failed += 1

            # Handle retry or dead letter
            await self._handle_failure(message, str(e))

    async def _check_kill_switch(self, message: JobMessage) -> bool:
        """
        Check kill switch for job capability.

        INV-W0-002: Kill switch integration.

        Args:
            message: Job message

        Returns:
            True if execution is allowed, False if killed
        """
        try:
            from app.core.kill_switch_guard import KillSwitchGuard

            guard = KillSwitchGuard(capability=message.capability or "job.default")
            await guard.check_or_abort(message.job_id)
            return True

        except ImportError:
            # Kill switch module not available — allow execution
            logger.debug("job_queue_worker.kill_switch_not_available")
            return True

        except Exception as e:
            # Kill switch triggered or error
            logger.warning(
                "job_queue_worker.kill_switch_blocked",
                extra={"job_id": message.job_id, "error": str(e)},
            )
            return False

    async def _check_idempotency(
        self,
        message: JobMessage,
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check idempotency for job.

        INV-W0-003: Idempotency enforcement.

        Args:
            message: Job message

        Returns:
            (is_new, cached_result)
        """
        try:
            from app.core.idempotency import IdempotencyKey, get_idempotency_store

            idem_key = IdempotencyKey(
                job_id=message.job_id,
                plane_id=message.tenant_id,
            )

            store = get_idempotency_store()
            return await store.check_and_acquire(idem_key)

        except ImportError:
            # Idempotency module not available — treat as new
            logger.debug("job_queue_worker.idempotency_not_available")
            return (True, None)

        except Exception as e:
            logger.warning(
                "job_queue_worker.idempotency_check_failed",
                extra={"job_id": message.job_id, "error": str(e)},
            )
            # On error, treat as new to avoid blocking
            return (True, None)

    async def _mark_idempotency_complete(
        self,
        message: JobMessage,
        result: Dict[str, Any],
    ) -> None:
        """Mark job as complete in idempotency store."""
        try:
            from app.core.idempotency import IdempotencyKey, get_idempotency_store

            idem_key = IdempotencyKey(
                job_id=message.job_id,
                plane_id=message.tenant_id,
            )

            store = get_idempotency_store()
            await store.mark_complete(idem_key, result)

        except Exception as e:
            logger.warning(
                "job_queue_worker.idempotency_complete_failed",
                extra={"job_id": message.job_id, "error": str(e)},
            )

    async def _handle_failure(self, message: JobMessage, error: str) -> None:
        """
        Handle job failure — retry or dead letter.

        Args:
            message: Job message
            error: Error message
        """
        if message.retry_count < self._config.max_retries:
            # Retry
            message.retry_count += 1
            message.metadata["last_error"] = error
            message.metadata["last_retry_at"] = datetime.now(timezone.utc).isoformat()

            # Re-enqueue with delay
            await asyncio.sleep(self._config.retry_delay_seconds)
            await self._redis.rpush(
                self._config.queue_name,
                json.dumps(message.to_dict()),
            )

            self._stats.jobs_retried += 1
            logger.info(
                "job_queue_worker.retrying",
                extra={
                    "job_id": message.job_id,
                    "retry": message.retry_count,
                },
            )

        else:
            # Dead letter
            await self._move_to_dead_letter(message, error)

    async def _move_to_dead_letter(self, message: JobMessage, reason: str) -> None:
        """
        Move job to dead letter queue.

        Args:
            message: Job message
            reason: Reason for dead lettering
        """
        message.metadata["dead_letter_reason"] = reason
        message.metadata["dead_lettered_at"] = datetime.now(timezone.utc).isoformat()

        await self._redis.rpush(
            self._config.dead_letter_queue,
            json.dumps(message.to_dict()),
        )

        self._stats.jobs_dead_lettered += 1

        logger.warning(
            "job_queue_worker.dead_lettered",
            extra={"job_id": message.job_id, "reason": reason},
        )

        # Mark idempotency as failed (non-retryable)
        try:
            from app.core.idempotency import IdempotencyKey, get_idempotency_store

            idem_key = IdempotencyKey(
                job_id=message.job_id,
                plane_id=message.tenant_id,
            )

            store = get_idempotency_store()
            await store.mark_failed(idem_key, allow_retry=False)

        except Exception:
            pass


# =========================
# Singleton Management
# =========================

_worker: Optional[JobQueueWorker] = None


def get_job_queue_worker() -> JobQueueWorker:
    """
    Get or create the singleton JobQueueWorker.

    Returns:
        JobQueueWorker instance
    """
    global _worker

    if _worker is None:
        _worker = JobQueueWorker()
        logger.info("job_queue_worker.created")

    return _worker


def configure_job_queue_worker(
    config: Optional[WorkerConfig] = None,
) -> JobQueueWorker:
    """
    Configure the singleton JobQueueWorker.

    Args:
        config: Worker configuration

    Returns:
        Configured JobQueueWorker
    """
    global _worker

    _worker = JobQueueWorker(config=config)

    logger.info(
        "job_queue_worker.configured",
        extra={"max_workers": _worker._config.max_workers},
    )

    return _worker


def reset_job_queue_worker() -> None:
    """Reset the singleton (for testing)."""
    global _worker
    _worker = None
