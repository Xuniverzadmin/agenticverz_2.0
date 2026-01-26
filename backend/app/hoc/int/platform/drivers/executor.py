# Layer: L6 — Driver
# Product: system-wide
# Wiring Type: executor
# Parent Gap: GAP-039 (JobScheduler)
# Reference: GAP-154
# Depends On: GAP-052 (JobScheduler service)
# Temporal:
#   Trigger: worker (startup)
#   Execution: async
# Role: Bind JobScheduler to APScheduler for actual execution
# Callers: Worker startup, application lifecycle
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5

"""
Module: executor
Purpose: Bind JobScheduler to APScheduler for actual execution.

Wires:
    - Source: app/services/scheduler/job_scheduler.py
    - Target: APScheduler library

Execution Modes:
    - Cron: Periodic execution via APScheduler cron trigger
    - One-time: Delayed execution via APScheduler date trigger
    - Interval: Fixed interval execution
    - Immediate: Direct execution (no scheduling)

Acceptance Criteria:
    - AC-154-01: Jobs are scheduled via APScheduler
    - AC-154-02: Cron expressions are parsed correctly
    - AC-154-03: One-time jobs execute at scheduled time
    - AC-154-04: Job handlers are invoked correctly
    - AC-154-05: Status updates propagate to JobScheduler
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("nova.services.scheduler.executor")


@dataclass
class ExecutorConfig:
    """Configuration for the APScheduler executor."""

    # Maximum concurrent jobs
    max_concurrent_jobs: int = 10

    # Default misfire grace time in seconds
    misfire_grace_time: int = 60

    # Job execution timeout in seconds
    job_timeout: int = 3600

    # Enable coalesce (run once if multiple fires missed)
    coalesce: bool = True


class APSchedulerExecutor:
    """
    Binds JobScheduler to APScheduler for real execution.

    This executor:
    1. Loads pending jobs from JobScheduler
    2. Schedules them in APScheduler
    3. Invokes registered handlers on trigger
    4. Updates JobScheduler with execution results
    """

    def __init__(
        self,
        config: Optional[ExecutorConfig] = None,
    ):
        """
        Initialize the APScheduler executor.

        Args:
            config: Executor configuration
        """
        self._config = config or ExecutorConfig()
        self._scheduler: Optional[Any] = None  # APScheduler instance
        self._job_handlers: Dict[str, Callable] = {}
        self._running = False
        self._semaphore: Optional[asyncio.Semaphore] = None

    def register_handler(self, handler_name: str, handler_fn: Callable) -> None:
        """
        Register a job handler function.

        Args:
            handler_name: Unique handler identifier
            handler_fn: Async callable that executes the job
        """
        self._job_handlers[handler_name] = handler_fn
        logger.debug(f"scheduler_executor.handler_registered: {handler_name}")

    def get_handler(self, handler_name: str) -> Optional[Callable]:
        """Get a registered handler by name."""
        return self._job_handlers.get(handler_name)

    async def start(self) -> None:
        """
        Start the APScheduler executor.

        Loads all pending jobs from JobScheduler and schedules them.
        """
        if self._running:
            logger.warning("scheduler_executor.already_running")
            return

        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.jobstores.memory import MemoryJobStore
            from apscheduler.executors.asyncio import AsyncIOExecutor

            # Initialize semaphore for concurrency control
            self._semaphore = asyncio.Semaphore(self._config.max_concurrent_jobs)

            # Configure APScheduler
            jobstores = {
                "default": MemoryJobStore(),
            }

            executors = {
                "default": AsyncIOExecutor(),
            }

            job_defaults = {
                "coalesce": self._config.coalesce,
                "max_instances": 1,
                "misfire_grace_time": self._config.misfire_grace_time,
            }

            self._scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone="UTC",
            )

            self._scheduler.start()
            self._running = True

            logger.info("scheduler_executor.started")

            # Load existing jobs from JobScheduler
            await self._load_pending_jobs()

        except ImportError as e:
            logger.error(
                "scheduler_executor.apscheduler_not_installed",
                extra={"error": str(e)},
            )
            raise RuntimeError(
                "APScheduler not installed. Install with: pip install apscheduler"
            ) from e

    async def stop(self) -> None:
        """
        Stop the APScheduler executor gracefully.

        Waits for running jobs to complete before shutdown.
        """
        if not self._running:
            return

        self._running = False

        if self._scheduler:
            self._scheduler.shutdown(wait=True)
            self._scheduler = None

        logger.info("scheduler_executor.stopped")

    async def schedule(
        self,
        job_id: str,
        handler_name: str,
        schedule_type: str,
        payload: Optional[Dict[str, Any]] = None,
        run_at: Optional[datetime] = None,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
    ) -> str:
        """
        Schedule a job for execution.

        Args:
            job_id: Unique job identifier
            handler_name: Handler to invoke
            schedule_type: Type of schedule (once, interval, cron)
            payload: Job payload data
            run_at: For one-time jobs, when to run
            interval_seconds: For interval jobs, seconds between runs
            cron_expression: For cron jobs, the cron expression

        Returns:
            APScheduler job ID
        """
        if not self._scheduler:
            raise RuntimeError("Executor not started")

        handler = self._job_handlers.get(handler_name)
        if not handler:
            raise ValueError(f"No handler registered for: {handler_name}")

        # Import triggers here to avoid import errors if APScheduler not installed
        from apscheduler.triggers.date import DateTrigger
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger

        # Determine trigger based on schedule type
        if schedule_type == "once":
            if not run_at:
                run_at = datetime.now(timezone.utc)
            trigger = DateTrigger(run_date=run_at)

        elif schedule_type == "interval":
            if not interval_seconds:
                raise ValueError("interval_seconds required for interval schedule")
            trigger = IntervalTrigger(seconds=interval_seconds)

        elif schedule_type == "cron":
            if not cron_expression:
                raise ValueError("cron_expression required for cron schedule")
            trigger = CronTrigger.from_crontab(cron_expression)

        elif schedule_type == "daily":
            # Daily at specific time (parsed from cron-like format)
            hour = 0
            minute = 0
            if cron_expression:
                parts = cron_expression.split()
                if len(parts) >= 2:
                    minute = int(parts[0]) if parts[0] != "*" else 0
                    hour = int(parts[1]) if parts[1] != "*" else 0
            trigger = CronTrigger(hour=hour, minute=minute)

        elif schedule_type == "weekly":
            # Weekly on specific day at specific time
            day_of_week = 0
            hour = 0
            minute = 0
            if cron_expression:
                parts = cron_expression.split()
                if len(parts) >= 5:
                    minute = int(parts[0]) if parts[0] != "*" else 0
                    hour = int(parts[1]) if parts[1] != "*" else 0
                    day_of_week = int(parts[4]) if parts[4] != "*" else 0
            trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)

        else:
            # Default: immediate execution
            trigger = DateTrigger(run_date=datetime.now(timezone.utc))

        # Schedule the job
        ap_job = self._scheduler.add_job(
            self._execute_job,
            trigger=trigger,
            args=[job_id, handler_name, payload or {}],
            id=job_id,
            name=f"job:{job_id}",
            replace_existing=True,
        )

        logger.info(
            "scheduler_executor.job_scheduled",
            extra={
                "job_id": job_id,
                "handler": handler_name,
                "schedule_type": schedule_type,
                "trigger": str(trigger),
            },
        )

        return ap_job.id

    async def unschedule(self, job_id: str) -> bool:
        """
        Remove a job from APScheduler.

        Args:
            job_id: Job to unschedule

        Returns:
            True if job was removed, False if not found
        """
        if not self._scheduler:
            return False

        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"scheduler_executor.job_unscheduled: {job_id}")
            return True
        except Exception:
            return False

    async def pause(self, job_id: str) -> bool:
        """Pause a scheduled job."""
        if not self._scheduler:
            return False

        try:
            self._scheduler.pause_job(job_id)
            return True
        except Exception:
            return False

    async def resume(self, job_id: str) -> bool:
        """Resume a paused job."""
        if not self._scheduler:
            return False

        try:
            self._scheduler.resume_job(job_id)
            return True
        except Exception:
            return False

    async def _execute_job(
        self,
        job_id: str,
        handler_name: str,
        payload: Dict[str, Any],
    ) -> None:
        """
        Execute a scheduled job.

        Uses semaphore for concurrency control and updates
        JobScheduler with execution results.

        Args:
            job_id: Job identifier
            handler_name: Handler to invoke
            payload: Job payload
        """
        if not self._semaphore:
            self._semaphore = asyncio.Semaphore(self._config.max_concurrent_jobs)

        async with self._semaphore:
            logger.info(
                "scheduler_executor.job_executing",
                extra={"job_id": job_id, "handler": handler_name},
            )

            handler = self._job_handlers.get(handler_name)
            if not handler:
                logger.error(
                    "scheduler_executor.handler_not_found",
                    extra={"job_id": job_id, "handler": handler_name},
                )
                await self._record_execution(job_id, False, "Handler not found")
                return

            try:
                # Update status to running
                await self._update_job_status(job_id, "running")

                # Execute handler with timeout
                await asyncio.wait_for(
                    handler(job_id, payload),
                    timeout=self._config.job_timeout,
                )

                # Record success
                await self._record_execution(job_id, True)

                logger.info(
                    "scheduler_executor.job_completed",
                    extra={"job_id": job_id},
                )

            except asyncio.TimeoutError:
                error_msg = f"Job timed out after {self._config.job_timeout}s"
                logger.error(
                    "scheduler_executor.job_timeout",
                    extra={"job_id": job_id},
                )
                await self._record_execution(job_id, False, error_msg)

            except Exception as e:
                logger.error(
                    "scheduler_executor.job_failed",
                    extra={"job_id": job_id, "error": str(e)},
                )
                await self._record_execution(job_id, False, str(e))

    async def _record_execution(
        self,
        job_id: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Record execution result in JobScheduler."""
        try:
            # L6 driver import (migrated to HOC per SWEEP-10)
            from app.hoc.int.platform.drivers.job_scheduler import get_job_scheduler

            scheduler = get_job_scheduler()
            scheduler.record_execution(job_id, success, error)

        except Exception as e:
            logger.warning(
                "scheduler_executor.record_failed",
                extra={"job_id": job_id, "error": str(e)},
            )

    async def _update_job_status(self, job_id: str, status: str) -> None:
        """Update job status in JobScheduler."""
        try:
            # L6 driver imports (migrated to HOC per SWEEP-10)
            from app.hoc.int.platform.drivers.job_scheduler import (
                JobStatus,
                get_job_scheduler,
            )

            scheduler = get_job_scheduler()
            job = scheduler.get_job(job_id)
            if job:
                job.status = JobStatus(status)

        except Exception as e:
            logger.warning(
                "scheduler_executor.status_update_failed",
                extra={"job_id": job_id, "error": str(e)},
            )

    async def _load_pending_jobs(self) -> None:
        """Load pending jobs from JobScheduler and schedule them."""
        try:
            # L6 driver imports (migrated to HOC per SWEEP-10)
            from app.hoc.int.platform.drivers.job_scheduler import (
                JobStatus,
                get_job_scheduler,
            )

            scheduler = get_job_scheduler()
            pending_jobs = scheduler.get_jobs(status=JobStatus.PENDING)
            scheduled_jobs = scheduler.get_jobs(status=JobStatus.SCHEDULED)

            jobs_to_load = pending_jobs + scheduled_jobs

            for job in jobs_to_load:
                try:
                    # Map schedule type to executor schedule type
                    schedule_type = job.schedule.schedule_type.value

                    await self.schedule(
                        job_id=job.job_id,
                        handler_name=job.handler,
                        schedule_type=schedule_type,
                        payload=job.payload,
                        run_at=job.schedule.run_at,
                        interval_seconds=job.schedule.interval_seconds,
                        cron_expression=job.schedule.cron_expression,
                    )

                except Exception as e:
                    logger.warning(
                        "scheduler_executor.job_load_failed",
                        extra={"job_id": job.job_id, "error": str(e)},
                    )

            logger.info(
                "scheduler_executor.jobs_loaded",
                extra={"count": len(jobs_to_load)},
            )

        except Exception as e:
            logger.error(
                "scheduler_executor.load_failed",
                extra={"error": str(e)},
            )

    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of currently scheduled jobs in APScheduler."""
        if not self._scheduler:
            return []

        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
            for job in self._scheduler.get_jobs()
        ]


# =========================
# Singleton Management
# =========================

_executor: Optional[APSchedulerExecutor] = None


def get_scheduler_executor() -> APSchedulerExecutor:
    """
    Get or create the singleton APSchedulerExecutor.

    Returns:
        APSchedulerExecutor instance
    """
    global _executor

    if _executor is None:
        _executor = APSchedulerExecutor()
        logger.info("scheduler_executor.created")

    return _executor


def configure_scheduler_executor(
    config: Optional[ExecutorConfig] = None,
) -> APSchedulerExecutor:
    """
    Configure the singleton APSchedulerExecutor.

    Args:
        config: Executor configuration

    Returns:
        Configured APSchedulerExecutor
    """
    global _executor

    _executor = APSchedulerExecutor(config=config)

    logger.info(
        "scheduler_executor.configured",
        extra={
            "max_concurrent_jobs": _executor._config.max_concurrent_jobs,
        },
    )

    return _executor


def reset_scheduler_executor() -> None:
    """Reset the singleton (for testing)."""
    global _executor
    _executor = None
