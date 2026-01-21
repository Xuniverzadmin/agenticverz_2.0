# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-052 (Jobs Scheduler)
"""
Jobs Scheduler Services (GAP-052)

Provides job scheduling capabilities including:
- Cron-like periodic scheduling
- One-time delayed execution
- Job management and monitoring
- Tenant-isolated job queues

This module provides:
    - JobScheduler: Main scheduling service
    - ScheduledJob: Job definition model
    - JobSchedule: Schedule configuration
    - Helper functions for quick access
"""

from app.services.scheduler.job_scheduler import (
    JobPriority,
    JobSchedule,
    JobScheduleType,
    JobScheduler,
    JobSchedulerError,
    JobStatus,
    ScheduledJob,
    cancel_job,
    get_job,
    get_scheduler_stats,
    list_jobs,
    schedule_job,
)

__all__ = [
    "JobPriority",
    "JobSchedule",
    "JobScheduleType",
    "JobScheduler",
    "JobSchedulerError",
    "JobStatus",
    "ScheduledJob",
    "cancel_job",
    "get_job",
    "get_scheduler_stats",
    "list_jobs",
    "schedule_job",
]
