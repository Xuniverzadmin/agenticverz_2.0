# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-052 (Jobs Scheduler), GAP-154, GAP-155, GAP-156, GAP-157, GAP-158
"""
Jobs Scheduler Services

Provides job scheduling capabilities including:
- Cron-like periodic scheduling (GAP-052)
- One-time delayed execution
- Job management and monitoring
- Tenant-isolated job queues
- APScheduler binding (GAP-154)
- Job retry logic (GAP-156)
- Job progress reporting (GAP-157)
- Job audit evidence (GAP-158)

This module provides:
    - JobScheduler: Main scheduling service
    - ScheduledJob: Job definition model
    - JobSchedule: Schedule configuration
    - APSchedulerExecutor: Real execution binding (GAP-154)
    - JobRetryManager: Retry logic (GAP-156)
    - JobProgressTracker: Progress reporting (GAP-157)
    - JobAuditEmitter: Audit evidence (GAP-158)
"""

from app.services.scheduler.job_scheduler import (
    JobPriority,
    JobSchedule,
    JobScheduleType,
    JobScheduler,
    JobSchedulerError,
    JobStatus,
    ScheduledJob,
    SchedulerStats,
    cancel_job,
    get_job,
    get_job_scheduler,
    get_scheduler_stats,
    list_jobs,
    schedule_job,
)

from app.services.scheduler.executor import (
    APSchedulerExecutor,
    ExecutorConfig,
    get_scheduler_executor,
    configure_scheduler_executor,
)

from app.services.scheduler.job_execution import (
    # GAP-156: Retry
    JobRetryManager,
    RetryConfig,
    RetryStrategy,
    RetryAttempt,
    get_job_retry_manager,
    # GAP-157: Progress
    JobProgressTracker,
    ProgressUpdate,
    ProgressStage,
    get_job_progress_tracker,
    # GAP-158: Audit
    JobAuditEmitter,
    JobAuditEvent,
    JobAuditEventType,
    get_job_audit_emitter,
)

__all__ = [
    # GAP-052: Core Scheduler
    "JobPriority",
    "JobSchedule",
    "JobScheduleType",
    "JobScheduler",
    "JobSchedulerError",
    "JobStatus",
    "ScheduledJob",
    "SchedulerStats",
    "cancel_job",
    "get_job",
    "get_job_scheduler",
    "get_scheduler_stats",
    "list_jobs",
    "schedule_job",
    # GAP-154: APScheduler Executor
    "APSchedulerExecutor",
    "ExecutorConfig",
    "get_scheduler_executor",
    "configure_scheduler_executor",
    # GAP-156: Retry
    "JobRetryManager",
    "RetryConfig",
    "RetryStrategy",
    "RetryAttempt",
    "get_job_retry_manager",
    # GAP-157: Progress
    "JobProgressTracker",
    "ProgressUpdate",
    "ProgressStage",
    "get_job_progress_tracker",
    # GAP-158: Audit
    "JobAuditEmitter",
    "JobAuditEvent",
    "JobAuditEventType",
    "get_job_audit_emitter",
]
