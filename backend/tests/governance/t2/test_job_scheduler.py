# Layer: L8 — Catalyst/Meta
# Product: system-wide
# Reference: GAP-052 (Jobs Scheduler)
"""
Tests for JobScheduler (GAP-052).

Verifies job scheduling capabilities including cron-like scheduling,
one-time execution, and job lifecycle management.
"""

import pytest
from datetime import datetime, timedelta, timezone


class TestJobSchedulerImports:
    """Test that all components are properly exported."""

    def test_schedule_type_import(self):
        """JobScheduleType should be importable from package."""
        from app.services.scheduler import JobScheduleType
        assert JobScheduleType.ONCE == "once"

    def test_job_status_import(self):
        """JobStatus should be importable from package."""
        from app.services.scheduler import JobStatus
        assert JobStatus.PENDING == "pending"

    def test_job_priority_import(self):
        """JobPriority should be importable from package."""
        from app.services.scheduler import JobPriority
        assert JobPriority.NORMAL == "normal"

    def test_job_schedule_import(self):
        """JobSchedule should be importable from package."""
        from app.services.scheduler import JobSchedule, JobScheduleType
        schedule = JobSchedule(schedule_type=JobScheduleType.ONCE)
        assert schedule.schedule_type == JobScheduleType.ONCE

    def test_scheduled_job_import(self):
        """ScheduledJob should be importable from package."""
        from app.services.scheduler import ScheduledJob, JobSchedule, JobScheduleType
        job = ScheduledJob(
            job_id="job-1",
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(schedule_type=JobScheduleType.ONCE),
        )
        assert job.job_id == "job-1"

    def test_scheduler_import(self):
        """JobScheduler should be importable from package."""
        from app.services.scheduler import JobScheduler
        scheduler = JobScheduler()
        assert scheduler is not None

    def test_scheduler_error_import(self):
        """JobSchedulerError should be importable from package."""
        from app.services.scheduler import JobSchedulerError
        error = JobSchedulerError("test error")
        assert str(error) == "test error"

    def test_helper_functions_import(self):
        """Helper functions should be importable from package."""
        from app.services.scheduler import (
            schedule_job,
            get_job,
            list_jobs,
            cancel_job,
            get_scheduler_stats,
        )
        assert callable(schedule_job)
        assert callable(get_job)
        assert callable(list_jobs)
        assert callable(cancel_job)
        assert callable(get_scheduler_stats)


class TestJobScheduleTypeEnum:
    """Test JobScheduleType enum."""

    def test_all_types_defined(self):
        """All schedule types should be defined."""
        from app.services.scheduler import JobScheduleType

        assert hasattr(JobScheduleType, "ONCE")
        assert hasattr(JobScheduleType, "INTERVAL")
        assert hasattr(JobScheduleType, "CRON")
        assert hasattr(JobScheduleType, "DAILY")
        assert hasattr(JobScheduleType, "WEEKLY")

    def test_type_string_values(self):
        """Type values should be lowercase strings."""
        from app.services.scheduler import JobScheduleType

        assert JobScheduleType.ONCE.value == "once"
        assert JobScheduleType.INTERVAL.value == "interval"
        assert JobScheduleType.CRON.value == "cron"


class TestJobStatusEnum:
    """Test JobStatus enum."""

    def test_all_statuses_defined(self):
        """All job statuses should be defined."""
        from app.services.scheduler import JobStatus

        assert hasattr(JobStatus, "PENDING")
        assert hasattr(JobStatus, "SCHEDULED")
        assert hasattr(JobStatus, "RUNNING")
        assert hasattr(JobStatus, "COMPLETED")
        assert hasattr(JobStatus, "FAILED")
        assert hasattr(JobStatus, "PAUSED")
        assert hasattr(JobStatus, "CANCELLED")


class TestJobPriorityEnum:
    """Test JobPriority enum."""

    def test_all_priorities_defined(self):
        """All priorities should be defined."""
        from app.services.scheduler import JobPriority

        assert hasattr(JobPriority, "LOW")
        assert hasattr(JobPriority, "NORMAL")
        assert hasattr(JobPriority, "HIGH")
        assert hasattr(JobPriority, "CRITICAL")


class TestJobSchedule:
    """Test JobSchedule dataclass."""

    def test_once_schedule(self):
        """ONCE schedule should have run_at."""
        from app.services.scheduler import JobSchedule, JobScheduleType

        run_at = datetime.now(timezone.utc) + timedelta(hours=1)
        schedule = JobSchedule(
            schedule_type=JobScheduleType.ONCE,
            run_at=run_at,
        )

        assert schedule.schedule_type == JobScheduleType.ONCE
        assert schedule.run_at == run_at

    def test_interval_schedule(self):
        """INTERVAL schedule should have interval_seconds."""
        from app.services.scheduler import JobSchedule, JobScheduleType

        schedule = JobSchedule(
            schedule_type=JobScheduleType.INTERVAL,
            interval_seconds=300,
        )

        assert schedule.schedule_type == JobScheduleType.INTERVAL
        assert schedule.interval_seconds == 300

    def test_daily_schedule(self):
        """DAILY schedule should have hour and minute."""
        from app.services.scheduler import JobSchedule, JobScheduleType

        schedule = JobSchedule(
            schedule_type=JobScheduleType.DAILY,
            daily_hour=9,
            daily_minute=30,
        )

        assert schedule.daily_hour == 9
        assert schedule.daily_minute == 30

    def test_weekly_schedule(self):
        """WEEKLY schedule should have day, hour, and minute."""
        from app.services.scheduler import JobSchedule, JobScheduleType

        schedule = JobSchedule(
            schedule_type=JobScheduleType.WEEKLY,
            weekly_day=0,  # Monday
            daily_hour=10,
        )

        assert schedule.weekly_day == 0
        assert schedule.daily_hour == 10

    def test_calculate_next_run_once(self):
        """ONCE schedule should calculate next run correctly."""
        from app.services.scheduler import JobSchedule, JobScheduleType

        now = datetime.now(timezone.utc)
        run_at = now + timedelta(hours=1)
        schedule = JobSchedule(
            schedule_type=JobScheduleType.ONCE,
            run_at=run_at,
        )

        next_run = schedule.calculate_next_run(now)
        assert next_run == run_at

    def test_calculate_next_run_once_past(self):
        """ONCE schedule in past should return None."""
        from app.services.scheduler import JobSchedule, JobScheduleType

        now = datetime.now(timezone.utc)
        run_at = now - timedelta(hours=1)
        schedule = JobSchedule(
            schedule_type=JobScheduleType.ONCE,
            run_at=run_at,
        )

        next_run = schedule.calculate_next_run(now)
        assert next_run is None

    def test_calculate_next_run_interval(self):
        """INTERVAL schedule should add interval to from_time."""
        from app.services.scheduler import JobSchedule, JobScheduleType

        now = datetime.now(timezone.utc)
        schedule = JobSchedule(
            schedule_type=JobScheduleType.INTERVAL,
            interval_seconds=300,
        )

        next_run = schedule.calculate_next_run(now)
        assert next_run == now + timedelta(seconds=300)

    def test_calculate_next_run_daily(self):
        """DAILY schedule should calculate next occurrence."""
        from app.services.scheduler import JobSchedule, JobScheduleType

        now = datetime(2026, 1, 21, 8, 0, 0, tzinfo=timezone.utc)
        schedule = JobSchedule(
            schedule_type=JobScheduleType.DAILY,
            daily_hour=10,
            daily_minute=0,
        )

        next_run = schedule.calculate_next_run(now)
        assert next_run.hour == 10
        assert next_run.minute == 0
        assert next_run.day == 21

    def test_calculate_next_run_daily_past_time(self):
        """DAILY schedule should go to next day if time passed."""
        from app.services.scheduler import JobSchedule, JobScheduleType

        now = datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc)
        schedule = JobSchedule(
            schedule_type=JobScheduleType.DAILY,
            daily_hour=10,
            daily_minute=0,
        )

        next_run = schedule.calculate_next_run(now)
        assert next_run.hour == 10
        assert next_run.day == 22

    def test_to_dict(self):
        """Schedule should serialize to dict."""
        from app.services.scheduler import JobSchedule, JobScheduleType

        schedule = JobSchedule(
            schedule_type=JobScheduleType.INTERVAL,
            interval_seconds=60,
        )
        result = schedule.to_dict()

        assert result["schedule_type"] == "interval"
        assert result["interval_seconds"] == 60


class TestScheduledJob:
    """Test ScheduledJob dataclass."""

    def test_job_creation(self):
        """Job should be created with required fields."""
        from app.services.scheduler import (
            ScheduledJob,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        job = ScheduledJob(
            job_id="job-1",
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(schedule_type=JobScheduleType.ONCE),
        )

        assert job.job_id == "job-1"
        assert job.tenant_id == "tenant-1"
        assert job.name == "Test Job"
        assert job.status == JobStatus.PENDING
        assert job.run_count == 0

    def test_calculate_next_run(self):
        """Job should calculate and update next run."""
        from app.services.scheduler import (
            ScheduledJob,
            JobSchedule,
            JobScheduleType,
        )

        now = datetime.now(timezone.utc)
        run_at = now + timedelta(hours=1)
        job = ScheduledJob(
            job_id="job-1",
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.ONCE,
                run_at=run_at,
            ),
        )

        next_run = job.calculate_next_run(now)
        assert next_run == run_at
        assert job.next_run == run_at

    def test_record_run_success(self):
        """Recording success should update counters."""
        from app.services.scheduler import (
            ScheduledJob,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        job = ScheduledJob(
            job_id="job-1",
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(schedule_type=JobScheduleType.ONCE),
        )

        job.record_run(success=True)

        assert job.run_count == 1
        assert job.failure_count == 0
        assert job.status == JobStatus.COMPLETED
        assert job.last_run is not None

    def test_record_run_failure(self):
        """Recording failure should update counters."""
        from app.services.scheduler import (
            ScheduledJob,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        job = ScheduledJob(
            job_id="job-1",
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(schedule_type=JobScheduleType.ONCE),
        )

        job.record_run(success=False, error="Test error")

        assert job.run_count == 1
        assert job.failure_count == 1
        assert job.status == JobStatus.FAILED
        assert job.last_error == "Test error"

    def test_pause_resume(self):
        """Job should pause and resume correctly."""
        from app.services.scheduler import (
            ScheduledJob,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        job = ScheduledJob(
            job_id="job-1",
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )
        job.status = JobStatus.SCHEDULED

        job.pause()
        assert job.status == JobStatus.PAUSED

        job.resume()
        assert job.status == JobStatus.SCHEDULED

    def test_cancel(self):
        """Job should cancel correctly."""
        from app.services.scheduler import (
            ScheduledJob,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        job = ScheduledJob(
            job_id="job-1",
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(schedule_type=JobScheduleType.ONCE),
        )

        job.cancel()
        assert job.status == JobStatus.CANCELLED
        assert job.next_run is None

    def test_is_due(self):
        """is_due should check if job is ready for execution."""
        from app.services.scheduler import (
            ScheduledJob,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        now = datetime.now(timezone.utc)
        past = now - timedelta(minutes=1)

        job = ScheduledJob(
            job_id="job-1",
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(schedule_type=JobScheduleType.ONCE),
        )
        job.status = JobStatus.SCHEDULED
        job.next_run = past

        assert job.is_due(now) is True

    def test_is_due_not_yet(self):
        """is_due should return False for future jobs."""
        from app.services.scheduler import (
            ScheduledJob,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=1)

        job = ScheduledJob(
            job_id="job-1",
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(schedule_type=JobScheduleType.ONCE),
        )
        job.status = JobStatus.SCHEDULED
        job.next_run = future

        assert job.is_due(now) is False

    def test_to_dict(self):
        """Job should serialize to dict."""
        from app.services.scheduler import (
            ScheduledJob,
            JobSchedule,
            JobScheduleType,
        )

        job = ScheduledJob(
            job_id="job-1",
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(schedule_type=JobScheduleType.ONCE),
        )
        result = job.to_dict()

        assert result["job_id"] == "job-1"
        assert result["tenant_id"] == "tenant-1"
        assert result["name"] == "Test Job"
        assert result["status"] == "pending"


class TestJobSchedulerError:
    """Test JobSchedulerError exception."""

    def test_error_creation(self):
        """Error should be created with message."""
        from app.services.scheduler import JobSchedulerError

        error = JobSchedulerError(
            message="Job not found",
            job_id="job-1",
        )

        assert str(error) == "Job not found"
        assert error.job_id == "job-1"

    def test_error_to_dict(self):
        """Error should serialize to dict."""
        from app.services.scheduler import JobSchedulerError

        error = JobSchedulerError(
            message="Failed to schedule",
            job_id="job-1",
        )
        result = error.to_dict()

        assert result["error"] == "Failed to schedule"
        assert result["job_id"] == "job-1"


class TestJobScheduler:
    """Test JobScheduler core functionality."""

    @pytest.fixture(autouse=True)
    def reset_scheduler(self):
        """Reset scheduler before each test."""
        from app.services.scheduler.job_scheduler import _reset_scheduler
        _reset_scheduler()
        yield
        _reset_scheduler()

    def test_scheduler_creation(self):
        """Scheduler should be created."""
        from app.services.scheduler import JobScheduler

        scheduler = JobScheduler()
        assert scheduler is not None

    def test_schedule_job(self):
        """Scheduling a job should create and store it."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        scheduler = JobScheduler()
        now = datetime.now(timezone.utc)
        run_at = now + timedelta(hours=1)

        job = scheduler.schedule(
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.ONCE,
                run_at=run_at,
            ),
        )

        assert job.job_id is not None
        assert job.tenant_id == "tenant-1"
        assert job.name == "Test Job"
        assert job.status == JobStatus.SCHEDULED
        assert job.next_run == run_at

    def test_get_job(self):
        """Getting a job by ID should work."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
        )

        scheduler = JobScheduler()
        job = scheduler.schedule(
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        retrieved = scheduler.get_job(job.job_id)
        assert retrieved is not None
        assert retrieved.job_id == job.job_id

    def test_get_job_not_found(self):
        """Getting non-existent job should return None."""
        from app.services.scheduler import JobScheduler

        scheduler = JobScheduler()
        retrieved = scheduler.get_job("nonexistent")
        assert retrieved is None


class TestJobSchedulerFiltering:
    """Test job filtering and listing."""

    @pytest.fixture(autouse=True)
    def reset_scheduler(self):
        """Reset scheduler before each test."""
        from app.services.scheduler.job_scheduler import _reset_scheduler
        _reset_scheduler()
        yield
        _reset_scheduler()

    def test_get_jobs_by_tenant(self):
        """Jobs should be filterable by tenant."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
        )

        scheduler = JobScheduler()

        for i in range(3):
            scheduler.schedule(
                tenant_id="tenant-1",
                name=f"Job {i}",
                handler="test_handler",
                schedule=JobSchedule(
                    schedule_type=JobScheduleType.INTERVAL,
                    interval_seconds=60,
                ),
            )

        scheduler.schedule(
            tenant_id="tenant-2",
            name="Other Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        jobs = scheduler.get_jobs(tenant_id="tenant-1")
        assert len(jobs) == 3

    def test_get_jobs_by_status(self):
        """Jobs should be filterable by status."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        scheduler = JobScheduler()

        job1 = scheduler.schedule(
            tenant_id="tenant-1",
            name="Job 1",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        job2 = scheduler.schedule(
            tenant_id="tenant-1",
            name="Job 2",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )
        scheduler.pause_job(job2.job_id)

        scheduled_jobs = scheduler.get_jobs(status=JobStatus.SCHEDULED)
        paused_jobs = scheduler.get_jobs(status=JobStatus.PAUSED)

        assert len(scheduled_jobs) == 1
        assert len(paused_jobs) == 1

    def test_get_due_jobs(self):
        """Due jobs should be retrievable."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
        )

        scheduler = JobScheduler()
        now = datetime.now(timezone.utc)

        # Due job - use interval which will be scheduled immediately
        job1 = scheduler.schedule(
            tenant_id="tenant-1",
            name="Due Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=1,  # 1 second interval
            ),
        )
        # Manually set next_run to past to make it due
        job1.next_run = now - timedelta(seconds=1)

        # Future job
        job2 = scheduler.schedule(
            tenant_id="tenant-1",
            name="Future Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.ONCE,
                run_at=now + timedelta(hours=1),
            ),
        )

        due_jobs = scheduler.get_due_jobs(now=now)
        assert len(due_jobs) == 1
        assert due_jobs[0].job_id == job1.job_id


class TestJobSchedulerOperations:
    """Test job operations."""

    @pytest.fixture(autouse=True)
    def reset_scheduler(self):
        """Reset scheduler before each test."""
        from app.services.scheduler.job_scheduler import _reset_scheduler
        _reset_scheduler()
        yield
        _reset_scheduler()

    def test_pause_job(self):
        """Pausing a job should update status."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        scheduler = JobScheduler()
        job = scheduler.schedule(
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        scheduler.pause_job(job.job_id)
        assert job.status == JobStatus.PAUSED

    def test_resume_job(self):
        """Resuming a job should update status."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        scheduler = JobScheduler()
        job = scheduler.schedule(
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        scheduler.pause_job(job.job_id)
        scheduler.resume_job(job.job_id)
        assert job.status == JobStatus.SCHEDULED

    def test_cancel_job(self):
        """Cancelling a job should update status."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        scheduler = JobScheduler()
        job = scheduler.schedule(
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        scheduler.cancel_job(job.job_id)
        assert job.status == JobStatus.CANCELLED

    def test_delete_job(self):
        """Deleting a job should remove it."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
        )

        scheduler = JobScheduler()
        job = scheduler.schedule(
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        result = scheduler.delete_job(job.job_id)
        assert result is True
        assert scheduler.get_job(job.job_id) is None

    def test_record_execution(self):
        """Recording execution should update job."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
        )

        scheduler = JobScheduler()
        job = scheduler.schedule(
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        scheduler.record_execution(job.job_id, success=True)
        assert job.run_count == 1
        assert job.last_run is not None


class TestJobSchedulerStatistics:
    """Test statistics gathering."""

    @pytest.fixture(autouse=True)
    def reset_scheduler(self):
        """Reset scheduler before each test."""
        from app.services.scheduler.job_scheduler import _reset_scheduler
        _reset_scheduler()
        yield
        _reset_scheduler()

    def test_get_statistics(self):
        """Statistics should be collected correctly."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
        )

        scheduler = JobScheduler()

        for i in range(5):
            scheduler.schedule(
                tenant_id="tenant-1",
                name=f"Job {i}",
                handler="test_handler",
                schedule=JobSchedule(
                    schedule_type=JobScheduleType.INTERVAL,
                    interval_seconds=60,
                ),
            )

        stats = scheduler.get_statistics()
        assert stats.total_jobs == 5
        assert stats.scheduled_jobs == 5

    def test_get_statistics_by_tenant(self):
        """Statistics should filter by tenant."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
        )

        scheduler = JobScheduler()

        for i in range(3):
            scheduler.schedule(
                tenant_id="tenant-1",
                name=f"Job {i}",
                handler="test_handler",
                schedule=JobSchedule(
                    schedule_type=JobScheduleType.INTERVAL,
                    interval_seconds=60,
                ),
            )

        scheduler.schedule(
            tenant_id="tenant-2",
            name="Other Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        stats = scheduler.get_statistics(tenant_id="tenant-1")
        assert stats.total_jobs == 3

    def test_clear_tenant(self):
        """Clearing tenant should remove all jobs."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
        )

        scheduler = JobScheduler()

        for i in range(5):
            scheduler.schedule(
                tenant_id="tenant-1",
                name=f"Job {i}",
                handler="test_handler",
                schedule=JobSchedule(
                    schedule_type=JobScheduleType.INTERVAL,
                    interval_seconds=60,
                ),
            )

        cleared = scheduler.clear_tenant("tenant-1")
        assert cleared == 5

        jobs = scheduler.get_jobs(tenant_id="tenant-1")
        assert len(jobs) == 0


class TestJobSchedulerHandlers:
    """Test handler registration."""

    @pytest.fixture(autouse=True)
    def reset_scheduler(self):
        """Reset scheduler before each test."""
        from app.services.scheduler.job_scheduler import _reset_scheduler
        _reset_scheduler()
        yield
        _reset_scheduler()

    def test_register_handler(self):
        """Handler should be registerable."""
        from app.services.scheduler import JobScheduler

        scheduler = JobScheduler()

        def my_handler():
            pass

        scheduler.register_handler("my_handler", my_handler)

        retrieved = scheduler.get_handler("my_handler")
        assert retrieved is my_handler

    def test_get_unregistered_handler(self):
        """Getting unregistered handler should return None."""
        from app.services.scheduler import JobScheduler

        scheduler = JobScheduler()
        handler = scheduler.get_handler("nonexistent")
        assert handler is None


class TestHelperFunctions:
    """Test module-level helper functions."""

    @pytest.fixture(autouse=True)
    def reset_scheduler(self):
        """Reset scheduler before each test."""
        from app.services.scheduler.job_scheduler import _reset_scheduler
        _reset_scheduler()
        yield
        _reset_scheduler()

    def test_schedule_job_helper(self):
        """schedule_job should use singleton."""
        from app.services.scheduler import (
            schedule_job,
            JobSchedule,
            JobScheduleType,
        )

        job = schedule_job(
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        assert job.job_id is not None

    def test_get_job_helper(self):
        """get_job should use singleton."""
        from app.services.scheduler import (
            schedule_job,
            get_job,
            JobSchedule,
            JobScheduleType,
        )

        job = schedule_job(
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        retrieved = get_job(job.job_id)
        assert retrieved is not None
        assert retrieved.job_id == job.job_id

    def test_list_jobs_helper(self):
        """list_jobs should use singleton."""
        from app.services.scheduler import (
            schedule_job,
            list_jobs,
            JobSchedule,
            JobScheduleType,
        )

        for i in range(3):
            schedule_job(
                tenant_id="tenant-1",
                name=f"Job {i}",
                handler="test_handler",
                schedule=JobSchedule(
                    schedule_type=JobScheduleType.INTERVAL,
                    interval_seconds=60,
                ),
            )

        jobs = list_jobs(tenant_id="tenant-1")
        assert len(jobs) == 3

    def test_cancel_job_helper(self):
        """cancel_job should use singleton."""
        from app.services.scheduler import (
            schedule_job,
            cancel_job,
            get_job,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        job = schedule_job(
            tenant_id="tenant-1",
            name="Test Job",
            handler="test_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
        )

        cancel_job(job.job_id)
        retrieved = get_job(job.job_id)
        assert retrieved.status == JobStatus.CANCELLED

    def test_get_scheduler_stats_helper(self):
        """get_scheduler_stats should use singleton."""
        from app.services.scheduler import (
            schedule_job,
            get_scheduler_stats,
            JobSchedule,
            JobScheduleType,
        )

        for i in range(3):
            schedule_job(
                tenant_id="tenant-1",
                name=f"Job {i}",
                handler="test_handler",
                schedule=JobSchedule(
                    schedule_type=JobScheduleType.INTERVAL,
                    interval_seconds=60,
                ),
            )

        stats = get_scheduler_stats()
        assert stats.total_jobs == 3


class TestJobSchedulerUseCases:
    """Test real-world use cases."""

    @pytest.fixture(autouse=True)
    def reset_scheduler(self):
        """Reset scheduler before each test."""
        from app.services.scheduler.job_scheduler import _reset_scheduler
        _reset_scheduler()
        yield
        _reset_scheduler()

    def test_recurring_cleanup_job(self):
        """Simulate a recurring cleanup job scenario."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        scheduler = JobScheduler()
        now = datetime.now(timezone.utc)

        # Schedule daily cleanup
        job = scheduler.schedule(
            tenant_id="tenant-1",
            name="Daily Cleanup",
            handler="cleanup_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.DAILY,
                daily_hour=3,
                daily_minute=0,
            ),
        )

        assert job.status == JobStatus.SCHEDULED
        assert job.next_run is not None

        # Simulate execution
        scheduler.record_execution(job.job_id, success=True)

        assert job.run_count == 1
        assert job.status == JobStatus.SCHEDULED
        # Should have next run scheduled
        assert job.next_run is not None

    def test_one_time_migration_job(self):
        """Simulate a one-time migration job scenario."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
            JobStatus,
        )

        scheduler = JobScheduler()
        now = datetime.now(timezone.utc)

        # Schedule one-time migration
        job = scheduler.schedule(
            tenant_id="tenant-1",
            name="Data Migration",
            handler="migration_handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.ONCE,
                run_at=now + timedelta(hours=1),
            ),
            payload={"migration_version": "v2"},
        )

        assert job.status == JobStatus.SCHEDULED
        assert job.payload["migration_version"] == "v2"

        # Simulate execution
        scheduler.record_execution(job.job_id, success=True)

        assert job.status == JobStatus.COMPLETED
        assert job.next_run is None

    def test_priority_ordering(self):
        """Jobs should be ordered by priority."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
            JobPriority,
        )

        scheduler = JobScheduler()
        now = datetime.now(timezone.utc)
        past = now - timedelta(minutes=1)

        # Schedule jobs with different priorities using INTERVAL
        job_low = scheduler.schedule(
            tenant_id="tenant-1",
            name="Low Priority",
            handler="handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
            priority=JobPriority.LOW,
        )
        job_low.next_run = past  # Make it due

        job_critical = scheduler.schedule(
            tenant_id="tenant-1",
            name="Critical Priority",
            handler="handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
            priority=JobPriority.CRITICAL,
        )
        job_critical.next_run = past  # Make it due

        job_normal = scheduler.schedule(
            tenant_id="tenant-1",
            name="Normal Priority",
            handler="handler",
            schedule=JobSchedule(
                schedule_type=JobScheduleType.INTERVAL,
                interval_seconds=60,
            ),
            priority=JobPriority.NORMAL,
        )
        job_normal.next_run = past  # Make it due

        due_jobs = scheduler.get_due_jobs(now=now)

        # Should be ordered: Critical, Normal, Low
        assert len(due_jobs) == 3
        assert due_jobs[0].name == "Critical Priority"
        assert due_jobs[1].name == "Normal Priority"
        assert due_jobs[2].name == "Low Priority"

    def test_tenant_isolation(self):
        """Jobs should be isolated by tenant."""
        from app.services.scheduler import (
            JobScheduler,
            JobSchedule,
            JobScheduleType,
        )

        scheduler = JobScheduler()

        for i in range(5):
            scheduler.schedule(
                tenant_id="tenant-1",
                name=f"Tenant 1 Job {i}",
                handler="handler",
                schedule=JobSchedule(
                    schedule_type=JobScheduleType.INTERVAL,
                    interval_seconds=60,
                ),
            )

        for i in range(3):
            scheduler.schedule(
                tenant_id="tenant-2",
                name=f"Tenant 2 Job {i}",
                handler="handler",
                schedule=JobSchedule(
                    schedule_type=JobScheduleType.INTERVAL,
                    interval_seconds=60,
                ),
            )

        tenant1_jobs = scheduler.get_jobs(tenant_id="tenant-1")
        tenant2_jobs = scheduler.get_jobs(tenant_id="tenant-2")

        assert len(tenant1_jobs) == 5
        assert len(tenant2_jobs) == 3

        # Clear tenant 1
        scheduler.clear_tenant("tenant-1")

        tenant1_jobs = scheduler.get_jobs(tenant_id="tenant-1")
        tenant2_jobs = scheduler.get_jobs(tenant_id="tenant-2")

        assert len(tenant1_jobs) == 0
        assert len(tenant2_jobs) == 3  # Unaffected
