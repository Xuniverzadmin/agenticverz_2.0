# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api or worker (scheduled execution)
#   Execution: async
# Role: Scheduler Facade - Centralized access to job scheduling operations
# Callers: L2 scheduler.py API, SDK, Worker
# Allowed Imports: L4 scheduler services, L6 (models, db)
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-112 (Scheduled Job API)

"""
Scheduler Facade (L4 Domain Logic)

This facade provides the external interface for scheduled job operations.
All scheduler APIs MUST use this facade instead of directly importing
internal scheduler modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes job scheduling logic
- Provides unified access to job management
- Single point for audit emission

L2 API Routes (GAP-112):
- POST /api/v1/scheduler/jobs (create job)
- GET /api/v1/scheduler/jobs (list jobs)
- GET /api/v1/scheduler/jobs/{id} (get job)
- PUT /api/v1/scheduler/jobs/{id} (update job)
- DELETE /api/v1/scheduler/jobs/{id} (delete job)
- POST /api/v1/scheduler/jobs/{id}/trigger (trigger job)
- POST /api/v1/scheduler/jobs/{id}/pause (pause job)
- POST /api/v1/scheduler/jobs/{id}/resume (resume job)
- GET /api/v1/scheduler/jobs/{id}/runs (job run history)

Usage:
    from app.services.scheduler.facade import get_scheduler_facade

    facade = get_scheduler_facade()

    # Create scheduled job
    job = await facade.create_job(
        tenant_id="...",
        name="Daily Report",
        schedule="0 9 * * *",
        action={"type": "run_agent", "agent_id": "..."},
    )
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("nova.services.scheduler.facade")


class JobStatus(str, Enum):
    """Job status."""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class JobRunStatus(str, Enum):
    """Job run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ScheduledJob:
    """Scheduled job definition."""
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    schedule: str  # Cron expression
    action: Dict[str, Any]  # Action to perform
    status: str
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    run_count: int
    failure_count: int
    created_at: str
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "schedule": self.schedule,
            "action": self.action,
            "status": self.status,
            "last_run_at": self.last_run_at,
            "next_run_at": self.next_run_at,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


@dataclass
class JobRun:
    """Job run history entry."""
    id: str
    job_id: str
    tenant_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    duration_ms: Optional[int]
    result: Optional[Dict[str, Any]]
    error: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "result": self.result,
            "error": self.error,
        }


class SchedulerFacade:
    """
    Facade for scheduled job operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    scheduler services.

    Layer: L4 (Domain Logic)
    Callers: scheduler.py (L2), aos_sdk, Worker
    """

    def __init__(self):
        """Initialize facade."""
        # In-memory stores for demo (would be database in production)
        self._jobs: Dict[str, ScheduledJob] = {}
        self._runs: Dict[str, JobRun] = {}

    # =========================================================================
    # Job CRUD Operations (GAP-112)
    # =========================================================================

    async def create_job(
        self,
        tenant_id: str,
        name: str,
        schedule: str,
        action: Dict[str, Any],
        description: Optional[str] = None,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScheduledJob:
        """
        Create a scheduled job.

        Args:
            tenant_id: Tenant ID
            name: Job name
            schedule: Cron expression
            action: Action to perform
            description: Optional description
            enabled: Whether job is active
            metadata: Additional metadata

        Returns:
            Created ScheduledJob
        """
        logger.info(
            "facade.create_job",
            extra={"tenant_id": tenant_id, "name": name, "schedule": schedule}
        )

        now = datetime.now(timezone.utc)
        job_id = str(uuid.uuid4())

        # Calculate next run time (simplified - in production use croniter)
        next_run = self._calculate_next_run(schedule, now)

        job = ScheduledJob(
            id=job_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            schedule=schedule,
            action=action,
            status=JobStatus.ACTIVE.value if enabled else JobStatus.DISABLED.value,
            last_run_at=None,
            next_run_at=next_run.isoformat() if next_run else None,
            run_count=0,
            failure_count=0,
            created_at=now.isoformat(),
            metadata=metadata or {},
        )

        self._jobs[job_id] = job
        return job

    async def list_jobs(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ScheduledJob]:
        """
        List scheduled jobs.

        Args:
            tenant_id: Tenant ID
            status: Optional filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of ScheduledJob
        """
        results = []
        for job in self._jobs.values():
            if job.tenant_id != tenant_id:
                continue
            if status and job.status != status:
                continue
            results.append(job)

        # Sort by created_at descending
        results.sort(key=lambda j: j.created_at, reverse=True)

        return results[offset:offset + limit]

    async def get_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> Optional[ScheduledJob]:
        """
        Get a specific job.

        Args:
            job_id: Job ID
            tenant_id: Tenant ID for authorization

        Returns:
            ScheduledJob or None if not found
        """
        job = self._jobs.get(job_id)
        if job and job.tenant_id == tenant_id:
            return job
        return None

    async def update_job(
        self,
        job_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        schedule: Optional[str] = None,
        action: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ScheduledJob]:
        """
        Update a scheduled job.

        Args:
            job_id: Job ID
            tenant_id: Tenant ID for authorization
            name: New name
            schedule: New schedule
            action: New action
            description: New description
            metadata: New metadata

        Returns:
            Updated ScheduledJob or None if not found
        """
        job = self._jobs.get(job_id)
        if not job or job.tenant_id != tenant_id:
            return None

        now = datetime.now(timezone.utc)

        if name:
            job.name = name
        if schedule:
            job.schedule = schedule
            job.next_run_at = self._calculate_next_run(schedule, now).isoformat()
        if action:
            job.action = action
        if description is not None:
            job.description = description
        if metadata:
            job.metadata.update(metadata)

        job.updated_at = now.isoformat()
        return job

    async def delete_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Delete a scheduled job.

        Args:
            job_id: Job ID
            tenant_id: Tenant ID for authorization

        Returns:
            True if deleted, False if not found
        """
        job = self._jobs.get(job_id)
        if not job or job.tenant_id != tenant_id:
            return False

        del self._jobs[job_id]
        logger.info("facade.delete_job", extra={"job_id": job_id})
        return True

    # =========================================================================
    # Job Control Operations (GAP-112)
    # =========================================================================

    async def trigger_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> Optional[JobRun]:
        """
        Trigger a job to run immediately.

        Args:
            job_id: Job ID
            tenant_id: Tenant ID for authorization

        Returns:
            JobRun or None if not found
        """
        job = self._jobs.get(job_id)
        if not job or job.tenant_id != tenant_id:
            return None

        logger.info("facade.trigger_job", extra={"job_id": job_id})

        # Create a run
        now = datetime.now(timezone.utc)
        run_id = str(uuid.uuid4())

        run = JobRun(
            id=run_id,
            job_id=job_id,
            tenant_id=tenant_id,
            status=JobRunStatus.RUNNING.value,
            started_at=now.isoformat(),
            completed_at=None,
            duration_ms=None,
            result=None,
            error=None,
        )

        self._runs[run_id] = run

        # Simulate completion (in production, would be async)
        run.status = JobRunStatus.COMPLETED.value
        run.completed_at = now.isoformat()
        run.duration_ms = 100
        run.result = {"status": "success"}

        # Update job stats
        job.last_run_at = now.isoformat()
        job.run_count += 1
        job.next_run_at = self._calculate_next_run(job.schedule, now).isoformat()

        return run

    async def pause_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> Optional[ScheduledJob]:
        """
        Pause a scheduled job.

        Args:
            job_id: Job ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated ScheduledJob or None if not found
        """
        job = self._jobs.get(job_id)
        if not job or job.tenant_id != tenant_id:
            return None

        job.status = JobStatus.PAUSED.value
        job.updated_at = datetime.now(timezone.utc).isoformat()
        logger.info("facade.pause_job", extra={"job_id": job_id})
        return job

    async def resume_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> Optional[ScheduledJob]:
        """
        Resume a paused job.

        Args:
            job_id: Job ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated ScheduledJob or None if not found
        """
        job = self._jobs.get(job_id)
        if not job or job.tenant_id != tenant_id:
            return None

        now = datetime.now(timezone.utc)
        job.status = JobStatus.ACTIVE.value
        job.next_run_at = self._calculate_next_run(job.schedule, now).isoformat()
        job.updated_at = now.isoformat()
        logger.info("facade.resume_job", extra={"job_id": job_id})
        return job

    # =========================================================================
    # Job Run History (GAP-112)
    # =========================================================================

    async def list_runs(
        self,
        job_id: str,
        tenant_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[JobRun]:
        """
        List job runs.

        Args:
            job_id: Job ID
            tenant_id: Tenant ID for authorization
            status: Optional filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of JobRun
        """
        # Verify job access
        job = self._jobs.get(job_id)
        if not job or job.tenant_id != tenant_id:
            return []

        results = []
        for run in self._runs.values():
            if run.job_id != job_id:
                continue
            if status and run.status != status:
                continue
            results.append(run)

        # Sort by started_at descending
        results.sort(key=lambda r: r.started_at, reverse=True)

        return results[offset:offset + limit]

    async def get_run(
        self,
        run_id: str,
        tenant_id: str,
    ) -> Optional[JobRun]:
        """
        Get a specific job run.

        Args:
            run_id: Run ID
            tenant_id: Tenant ID for authorization

        Returns:
            JobRun or None if not found
        """
        run = self._runs.get(run_id)
        if run and run.tenant_id == tenant_id:
            return run
        return None

    def _calculate_next_run(
        self,
        schedule: str,
        from_time: datetime,
    ) -> datetime:
        """
        Calculate next run time from cron expression.

        In production, would use croniter library.
        For demo, returns 1 hour from now.
        """
        from datetime import timedelta
        return from_time + timedelta(hours=1)


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[SchedulerFacade] = None


def get_scheduler_facade() -> SchedulerFacade:
    """
    Get the scheduler facade instance.

    This is the recommended way to access scheduler operations
    from L2 APIs and the SDK.

    Returns:
        SchedulerFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = SchedulerFacade()
    return _facade_instance
