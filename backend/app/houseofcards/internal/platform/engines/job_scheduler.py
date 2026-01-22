# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-052 (Jobs Scheduler)
"""
JobScheduler - Job scheduling and management service.

Provides scheduling capabilities for:
- Cron-like periodic jobs
- One-time delayed execution
- Interval-based recurring jobs
- Job lifecycle management
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Optional
import hashlib
import re
import uuid


class JobScheduleType(str, Enum):
    """Types of job schedules."""

    ONCE = "once"           # One-time execution
    INTERVAL = "interval"   # Fixed interval
    CRON = "cron"           # Cron expression
    DAILY = "daily"         # Daily at specific time
    WEEKLY = "weekly"       # Weekly on specific day


class JobStatus(str, Enum):
    """Status of a scheduled job."""

    PENDING = "pending"       # Waiting for first run
    SCHEDULED = "scheduled"   # Scheduled for next run
    RUNNING = "running"       # Currently executing
    COMPLETED = "completed"   # Finished (one-time)
    FAILED = "failed"         # Failed execution
    PAUSED = "paused"         # Temporarily paused
    CANCELLED = "cancelled"   # Permanently cancelled


class JobPriority(str, Enum):
    """Priority levels for jobs."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class JobSchedule:
    """Configuration for job scheduling."""

    schedule_type: JobScheduleType

    # For ONCE: specific datetime
    run_at: Optional[datetime] = None

    # For INTERVAL: interval in seconds
    interval_seconds: Optional[int] = None

    # For CRON: cron expression (simplified)
    cron_expression: Optional[str] = None

    # For DAILY: hour and minute
    daily_hour: Optional[int] = None
    daily_minute: Optional[int] = None

    # For WEEKLY: day (0=Monday, 6=Sunday)
    weekly_day: Optional[int] = None

    # Limits
    max_runs: Optional[int] = None  # None = unlimited
    expires_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schedule_type": self.schedule_type.value,
            "run_at": self.run_at.isoformat() if self.run_at else None,
            "interval_seconds": self.interval_seconds,
            "cron_expression": self.cron_expression,
            "daily_hour": self.daily_hour,
            "daily_minute": self.daily_minute,
            "weekly_day": self.weekly_day,
            "max_runs": self.max_runs,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    def calculate_next_run(
        self,
        from_time: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """Calculate next run time from given time."""
        from_time = from_time or datetime.now(timezone.utc)

        if self.schedule_type == JobScheduleType.ONCE:
            if self.run_at and self.run_at > from_time:
                return self.run_at
            return None

        elif self.schedule_type == JobScheduleType.INTERVAL:
            if self.interval_seconds:
                return from_time + timedelta(seconds=self.interval_seconds)
            return None

        elif self.schedule_type == JobScheduleType.DAILY:
            if self.daily_hour is not None:
                minute = self.daily_minute or 0
                next_run = from_time.replace(
                    hour=self.daily_hour,
                    minute=minute,
                    second=0,
                    microsecond=0,
                )
                if next_run <= from_time:
                    next_run += timedelta(days=1)
                return next_run
            return None

        elif self.schedule_type == JobScheduleType.WEEKLY:
            if self.weekly_day is not None and self.daily_hour is not None:
                minute = self.daily_minute or 0
                current_weekday = from_time.weekday()
                days_ahead = self.weekly_day - current_weekday
                if days_ahead <= 0:
                    days_ahead += 7
                next_run = from_time + timedelta(days=days_ahead)
                next_run = next_run.replace(
                    hour=self.daily_hour,
                    minute=minute,
                    second=0,
                    microsecond=0,
                )
                return next_run
            return None

        elif self.schedule_type == JobScheduleType.CRON:
            # Simplified cron parsing (minute hour day month weekday)
            if self.cron_expression:
                return self._parse_cron_next_run(from_time)
            return None

        return None

    def _parse_cron_next_run(self, from_time: datetime) -> Optional[datetime]:
        """Parse simplified cron expression for next run."""
        if not self.cron_expression:
            return None

        parts = self.cron_expression.split()
        if len(parts) < 5:
            return None

        minute_str, hour_str, day_str, month_str, weekday_str = parts[:5]

        # Very simplified: just handle * and specific values
        try:
            minute = int(minute_str) if minute_str != "*" else 0
            hour = int(hour_str) if hour_str != "*" else from_time.hour
        except ValueError:
            return None

        next_run = from_time.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )

        if next_run <= from_time:
            next_run += timedelta(hours=1 if hour_str == "*" else 24)

        return next_run


@dataclass
class ScheduledJob:
    """Representation of a scheduled job."""

    job_id: str
    tenant_id: str
    name: str
    handler: str  # Handler identifier or function name
    schedule: JobSchedule

    # Status
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL

    # Execution info
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0
    last_error: Optional[str] = None

    # Payload
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def calculate_next_run(
        self,
        from_time: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """Calculate and update next run time."""
        # Check max runs
        if (
            self.schedule.max_runs is not None
            and self.run_count >= self.schedule.max_runs
        ):
            return None

        # Check expiry
        from_time = from_time or datetime.now(timezone.utc)
        if self.schedule.expires_at and from_time >= self.schedule.expires_at:
            return None

        next_run = self.schedule.calculate_next_run(from_time)
        self.next_run = next_run
        self.updated_at = datetime.now(timezone.utc)
        return next_run

    def record_run(
        self,
        success: bool,
        error: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> None:
        """Record a job execution."""
        now = now or datetime.now(timezone.utc)
        self.run_count += 1
        self.last_run = now
        self.updated_at = now

        if success:
            self.last_error = None
            if self.schedule.schedule_type == JobScheduleType.ONCE:
                self.status = JobStatus.COMPLETED
                self.next_run = None  # Clear next_run for completed one-time jobs
            else:
                self.status = JobStatus.SCHEDULED
                self.calculate_next_run(now)
        else:
            self.failure_count += 1
            self.last_error = error
            self.status = JobStatus.FAILED

    def pause(self) -> None:
        """Pause the job."""
        if self.status not in (JobStatus.COMPLETED, JobStatus.CANCELLED):
            self.status = JobStatus.PAUSED
            self.updated_at = datetime.now(timezone.utc)

    def resume(self, now: Optional[datetime] = None) -> None:
        """Resume a paused job."""
        if self.status == JobStatus.PAUSED:
            self.status = JobStatus.SCHEDULED
            self.calculate_next_run(now)
            self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        """Cancel the job."""
        self.status = JobStatus.CANCELLED
        self.next_run = None
        self.updated_at = datetime.now(timezone.utc)

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """Check if job is due for execution."""
        if self.status not in (JobStatus.PENDING, JobStatus.SCHEDULED):
            return False

        if self.next_run is None:
            return False

        now = now or datetime.now(timezone.utc)
        return self.next_run <= now

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "handler": self.handler,
            "schedule": self.schedule.to_dict(),
            "status": self.status.value,
            "priority": self.priority.value,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
            "last_error": self.last_error,
            "payload": self.payload,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SchedulerStats:
    """Statistics from the job scheduler."""

    total_jobs: int = 0
    pending_jobs: int = 0
    scheduled_jobs: int = 0
    running_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    paused_jobs: int = 0
    cancelled_jobs: int = 0

    # Counters
    total_runs: int = 0
    total_failures: int = 0

    # By type
    jobs_by_type: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_jobs": self.total_jobs,
            "pending_jobs": self.pending_jobs,
            "scheduled_jobs": self.scheduled_jobs,
            "running_jobs": self.running_jobs,
            "completed_jobs": self.completed_jobs,
            "failed_jobs": self.failed_jobs,
            "paused_jobs": self.paused_jobs,
            "cancelled_jobs": self.cancelled_jobs,
            "total_runs": self.total_runs,
            "total_failures": self.total_failures,
            "jobs_by_type": self.jobs_by_type,
        }


class JobSchedulerError(Exception):
    """Exception for scheduler errors."""

    def __init__(
        self,
        message: str,
        job_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.job_id = job_id

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error": self.message,
            "job_id": self.job_id,
        }


class JobScheduler:
    """
    Service for scheduling and managing jobs.

    Features:
    - Multiple schedule types (once, interval, cron, daily, weekly)
    - Priority-based ordering
    - Tenant isolation
    - Job lifecycle management
    - Statistics and monitoring
    """

    def __init__(self):
        """Initialize the scheduler."""
        self._jobs: dict[str, ScheduledJob] = {}
        self._handlers: dict[str, Callable] = {}
        self._tenant_jobs: dict[str, set[str]] = {}

    def register_handler(
        self,
        handler_name: str,
        handler_fn: Callable,
    ) -> None:
        """Register a job handler function."""
        self._handlers[handler_name] = handler_fn

    def get_handler(self, handler_name: str) -> Optional[Callable]:
        """Get a registered handler."""
        return self._handlers.get(handler_name)

    def schedule(
        self,
        tenant_id: str,
        name: str,
        handler: str,
        schedule: JobSchedule,
        payload: Optional[dict[str, Any]] = None,
        priority: JobPriority = JobPriority.NORMAL,
        metadata: Optional[dict[str, Any]] = None,
        job_id: Optional[str] = None,
    ) -> ScheduledJob:
        """
        Schedule a new job.

        Args:
            tenant_id: Tenant identifier
            name: Human-readable job name
            handler: Handler identifier
            schedule: Schedule configuration
            payload: Job payload data
            priority: Job priority
            metadata: Additional metadata
            job_id: Optional specific job ID

        Returns:
            The scheduled job
        """
        job_id = job_id or str(uuid.uuid4())

        job = ScheduledJob(
            job_id=job_id,
            tenant_id=tenant_id,
            name=name,
            handler=handler,
            schedule=schedule,
            priority=priority,
            payload=payload or {},
            metadata=metadata or {},
        )

        # Calculate initial next run
        job.calculate_next_run()
        if job.next_run:
            job.status = JobStatus.SCHEDULED

        # Store job
        self._jobs[job_id] = job

        # Track by tenant
        if tenant_id not in self._tenant_jobs:
            self._tenant_jobs[tenant_id] = set()
        self._tenant_jobs[tenant_id].add(job_id)

        return job

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def get_jobs(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        schedule_type: Optional[JobScheduleType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ScheduledJob]:
        """
        Get jobs with optional filters.

        Args:
            tenant_id: Filter by tenant
            status: Filter by status
            schedule_type: Filter by schedule type
            limit: Max results
            offset: Skip first N results

        Returns:
            List of matching jobs
        """
        jobs = list(self._jobs.values())

        if tenant_id:
            jobs = [j for j in jobs if j.tenant_id == tenant_id]

        if status:
            jobs = [j for j in jobs if j.status == status]

        if schedule_type:
            jobs = [j for j in jobs if j.schedule.schedule_type == schedule_type]

        # Sort by priority and next_run
        priority_order = {
            JobPriority.CRITICAL: 0,
            JobPriority.HIGH: 1,
            JobPriority.NORMAL: 2,
            JobPriority.LOW: 3,
        }
        jobs.sort(
            key=lambda j: (
                priority_order.get(j.priority, 2),
                j.next_run or datetime.max.replace(tzinfo=timezone.utc),
            )
        )

        return jobs[offset:offset + limit]

    def get_due_jobs(
        self,
        tenant_id: Optional[str] = None,
        now: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[ScheduledJob]:
        """Get jobs that are due for execution."""
        now = now or datetime.now(timezone.utc)
        jobs = []

        for job in self._jobs.values():
            if tenant_id and job.tenant_id != tenant_id:
                continue

            if job.is_due(now):
                jobs.append(job)

        # Sort by priority
        priority_order = {
            JobPriority.CRITICAL: 0,
            JobPriority.HIGH: 1,
            JobPriority.NORMAL: 2,
            JobPriority.LOW: 3,
        }
        jobs.sort(key=lambda j: priority_order.get(j.priority, 2))

        return jobs[:limit]

    def pause_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Pause a job."""
        job = self._jobs.get(job_id)
        if job:
            job.pause()
        return job

    def resume_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Resume a paused job."""
        job = self._jobs.get(job_id)
        if job:
            job.resume()
        return job

    def cancel_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Cancel a job."""
        job = self._jobs.get(job_id)
        if job:
            job.cancel()
        return job

    def delete_job(self, job_id: str) -> bool:
        """Permanently delete a job."""
        job = self._jobs.get(job_id)
        if not job:
            return False

        del self._jobs[job_id]

        # Remove from tenant tracking
        if job.tenant_id in self._tenant_jobs:
            self._tenant_jobs[job.tenant_id].discard(job_id)

        return True

    def record_execution(
        self,
        job_id: str,
        success: bool,
        error: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> Optional[ScheduledJob]:
        """Record job execution result."""
        job = self._jobs.get(job_id)
        if job:
            job.record_run(success, error, now)
        return job

    def update_payload(
        self,
        job_id: str,
        payload: dict[str, Any],
    ) -> Optional[ScheduledJob]:
        """Update job payload."""
        job = self._jobs.get(job_id)
        if job:
            job.payload = payload
            job.updated_at = datetime.now(timezone.utc)
        return job

    def get_statistics(
        self,
        tenant_id: Optional[str] = None,
    ) -> SchedulerStats:
        """Get scheduler statistics."""
        stats = SchedulerStats()

        for job in self._jobs.values():
            if tenant_id and job.tenant_id != tenant_id:
                continue

            stats.total_jobs += 1
            stats.total_runs += job.run_count
            stats.total_failures += job.failure_count

            # Count by status
            if job.status == JobStatus.PENDING:
                stats.pending_jobs += 1
            elif job.status == JobStatus.SCHEDULED:
                stats.scheduled_jobs += 1
            elif job.status == JobStatus.RUNNING:
                stats.running_jobs += 1
            elif job.status == JobStatus.COMPLETED:
                stats.completed_jobs += 1
            elif job.status == JobStatus.FAILED:
                stats.failed_jobs += 1
            elif job.status == JobStatus.PAUSED:
                stats.paused_jobs += 1
            elif job.status == JobStatus.CANCELLED:
                stats.cancelled_jobs += 1

            # Count by type
            schedule_type = job.schedule.schedule_type.value
            stats.jobs_by_type[schedule_type] = (
                stats.jobs_by_type.get(schedule_type, 0) + 1
            )

        return stats

    def clear_tenant(self, tenant_id: str) -> int:
        """Clear all jobs for a tenant."""
        job_ids = list(self._tenant_jobs.get(tenant_id, set()))
        for job_id in job_ids:
            self.delete_job(job_id)
        return len(job_ids)

    def reset(self) -> None:
        """Reset all state (for testing)."""
        self._jobs.clear()
        self._handlers.clear()
        self._tenant_jobs.clear()


# Module-level singleton
_scheduler: Optional[JobScheduler] = None


def get_job_scheduler() -> JobScheduler:
    """Get the singleton scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler


def _reset_scheduler() -> None:
    """Reset the singleton (for testing)."""
    global _scheduler
    if _scheduler:
        _scheduler.reset()
    _scheduler = None


# Helper functions
def schedule_job(
    tenant_id: str,
    name: str,
    handler: str,
    schedule: JobSchedule,
    payload: Optional[dict[str, Any]] = None,
    priority: JobPriority = JobPriority.NORMAL,
) -> ScheduledJob:
    """Schedule a new job using the singleton scheduler."""
    scheduler = get_job_scheduler()
    return scheduler.schedule(
        tenant_id=tenant_id,
        name=name,
        handler=handler,
        schedule=schedule,
        payload=payload,
        priority=priority,
    )


def get_job(job_id: str) -> Optional[ScheduledJob]:
    """Get a job by ID using the singleton scheduler."""
    scheduler = get_job_scheduler()
    return scheduler.get_job(job_id)


def list_jobs(
    tenant_id: Optional[str] = None,
    status: Optional[JobStatus] = None,
    limit: int = 100,
) -> list[ScheduledJob]:
    """List jobs using the singleton scheduler."""
    scheduler = get_job_scheduler()
    return scheduler.get_jobs(tenant_id=tenant_id, status=status, limit=limit)


def cancel_job(job_id: str) -> Optional[ScheduledJob]:
    """Cancel a job using the singleton scheduler."""
    scheduler = get_job_scheduler()
    return scheduler.cancel_job(job_id)


def get_scheduler_stats(tenant_id: Optional[str] = None) -> SchedulerStats:
    """Get scheduler statistics."""
    scheduler = get_job_scheduler()
    return scheduler.get_statistics(tenant_id=tenant_id)
