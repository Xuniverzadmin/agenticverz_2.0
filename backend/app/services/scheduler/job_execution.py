# Layer: L4 — Domain Engines
# Product: system-wide
# Wiring Type: service
# Parent Gap: GAP-039 (JobScheduler)
# Reference: GAP-156 (Retry), GAP-157 (Progress), GAP-158 (Audit)
# Temporal:
#   Trigger: worker (job execution)
#   Execution: async
# Role: Job execution support services (retry, progress, audit)
# Callers: JobQueueWorker, APSchedulerExecutor
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5

"""
Module: job_execution
Purpose: Job execution support services.

Provides:
    - GAP-156: Retry logic with exponential backoff
    - GAP-157: Progress reporting and tracking
    - GAP-158: Audit evidence emission

Acceptance Criteria:
    - AC-156-01: Exponential backoff with jitter
    - AC-156-02: Max retries respected
    - AC-156-03: Retry history recorded
    - AC-157-01: Progress percentage tracked
    - AC-157-02: Progress events emitted
    - AC-157-03: ETA calculation
    - AC-158-01: Job lifecycle audited
    - AC-158-02: Audit events are tamper-evident
    - AC-158-03: Audit includes execution context
"""

import hashlib
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("nova.services.scheduler.job_execution")


# =========================
# GAP-156: Retry Logic
# =========================


class RetryStrategy(str, Enum):
    """Retry strategy types."""

    FIXED = "fixed"  # Fixed delay
    LINEAR = "linear"  # Linear backoff
    EXPONENTIAL = "exponential"  # Exponential backoff
    FIBONACCI = "fibonacci"  # Fibonacci backoff


@dataclass
class RetryConfig:
    """Configuration for job retry."""

    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay_seconds: int = 60
    max_delay_seconds: int = 3600
    jitter_factor: float = 0.2  # Random jitter (0.0 to 1.0)
    retryable_errors: List[str] = field(default_factory=list)  # Empty = retry all


@dataclass
class RetryAttempt:
    """Record of a retry attempt."""

    attempt_number: int
    timestamp: str
    delay_seconds: int
    error: str
    will_retry: bool
    next_attempt_at: Optional[str] = None


class JobRetryManager:
    """
    Manages job retry logic with configurable strategies.

    GAP-156: Job Retry Logic

    Supports:
    - Exponential backoff with jitter
    - Configurable max retries
    - Retry history tracking
    - Error classification
    """

    # Fibonacci sequence for FIBONACCI strategy
    FIB_SEQUENCE = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize the retry manager.

        Args:
            config: Retry configuration
        """
        self._config = config or RetryConfig()
        self._retry_history: Dict[str, List[RetryAttempt]] = {}

    def should_retry(
        self,
        job_id: str,
        error: str,
        attempt_number: int,
    ) -> bool:
        """
        Determine if a job should be retried.

        Args:
            job_id: Job identifier
            error: Error message
            attempt_number: Current attempt number (1-based)

        Returns:
            True if should retry, False otherwise
        """
        # Check max retries
        if attempt_number >= self._config.max_retries:
            logger.info(
                "job_retry.max_retries_exceeded",
                extra={"job_id": job_id, "attempts": attempt_number},
            )
            return False

        # Check if error is retryable
        if self._config.retryable_errors:
            is_retryable = any(
                pattern in error for pattern in self._config.retryable_errors
            )
            if not is_retryable:
                logger.info(
                    "job_retry.non_retryable_error",
                    extra={"job_id": job_id, "error": error},
                )
                return False

        return True

    def calculate_delay(self, attempt_number: int) -> int:
        """
        Calculate retry delay based on strategy.

        Args:
            attempt_number: Current attempt number (1-based)

        Returns:
            Delay in seconds
        """
        base = self._config.base_delay_seconds

        if self._config.strategy == RetryStrategy.FIXED:
            delay = base

        elif self._config.strategy == RetryStrategy.LINEAR:
            delay = base * attempt_number

        elif self._config.strategy == RetryStrategy.EXPONENTIAL:
            delay = base * (2 ** (attempt_number - 1))

        elif self._config.strategy == RetryStrategy.FIBONACCI:
            fib_index = min(attempt_number - 1, len(self.FIB_SEQUENCE) - 1)
            delay = base * self.FIB_SEQUENCE[fib_index]

        else:
            delay = base

        # Apply jitter
        if self._config.jitter_factor > 0:
            jitter = delay * self._config.jitter_factor * random.random()
            delay = int(delay + jitter)

        # Clamp to max
        delay = min(delay, self._config.max_delay_seconds)

        return delay

    def record_retry(
        self,
        job_id: str,
        attempt_number: int,
        error: str,
        will_retry: bool,
    ) -> RetryAttempt:
        """
        Record a retry attempt.

        Args:
            job_id: Job identifier
            attempt_number: Current attempt number
            error: Error message
            will_retry: Whether job will be retried

        Returns:
            RetryAttempt record
        """
        delay = self.calculate_delay(attempt_number)
        now = datetime.now(timezone.utc)

        attempt = RetryAttempt(
            attempt_number=attempt_number,
            timestamp=now.isoformat(),
            delay_seconds=delay,
            error=error,
            will_retry=will_retry,
            next_attempt_at=(
                (now + timedelta(seconds=delay)).isoformat()
                if will_retry
                else None
            ),
        )

        # Track history
        if job_id not in self._retry_history:
            self._retry_history[job_id] = []
        self._retry_history[job_id].append(attempt)

        logger.info(
            "job_retry.recorded",
            extra={
                "job_id": job_id,
                "attempt": attempt_number,
                "will_retry": will_retry,
                "delay": delay,
            },
        )

        return attempt

    def get_retry_history(self, job_id: str) -> List[RetryAttempt]:
        """Get retry history for a job."""
        return self._retry_history.get(job_id, [])

    def clear_history(self, job_id: str) -> None:
        """Clear retry history for a job."""
        self._retry_history.pop(job_id, None)


# =========================
# GAP-157: Progress Reporting
# =========================


class ProgressStage(str, Enum):
    """Standard progress stages."""

    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressUpdate:
    """A progress update for a job."""

    job_id: str
    percentage: float  # 0.0 to 100.0
    stage: ProgressStage
    message: Optional[str] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    started_at: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    eta_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "percentage": self.percentage,
            "stage": self.stage.value,
            "message": self.message,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "eta_seconds": self.eta_seconds,
            "metadata": self.metadata,
        }


class JobProgressTracker:
    """
    Tracks and reports job progress.

    GAP-157: Job Progress Reporting

    Provides:
    - Percentage tracking
    - Step-based progress
    - ETA calculation
    - Progress event emission
    """

    def __init__(self, publisher: Optional[Any] = None):
        """
        Initialize the progress tracker.

        Args:
            publisher: Event publisher for progress events
        """
        self._publisher = publisher
        self._progress: Dict[str, ProgressUpdate] = {}
        self._callbacks: Dict[str, List[Callable]] = {}

    async def start(
        self,
        job_id: str,
        total_steps: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProgressUpdate:
        """
        Start tracking progress for a job.

        Args:
            job_id: Job identifier
            total_steps: Optional total number of steps
            metadata: Additional metadata

        Returns:
            Initial progress update
        """
        now = datetime.now(timezone.utc).isoformat()

        update = ProgressUpdate(
            job_id=job_id,
            percentage=0.0,
            stage=ProgressStage.STARTING,
            current_step=0,
            total_steps=total_steps,
            started_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        self._progress[job_id] = update
        await self._emit_progress(update)

        logger.debug(f"job_progress.started: {job_id}")
        return update

    async def update(
        self,
        job_id: str,
        percentage: Optional[float] = None,
        stage: Optional[ProgressStage] = None,
        message: Optional[str] = None,
        current_step: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ProgressUpdate]:
        """
        Update progress for a job.

        Args:
            job_id: Job identifier
            percentage: Optional new percentage
            stage: Optional new stage
            message: Optional status message
            current_step: Optional current step number
            metadata: Optional additional metadata

        Returns:
            Updated progress or None if not found
        """
        existing = self._progress.get(job_id)
        if not existing:
            return None

        now = datetime.now(timezone.utc).isoformat()

        # Update fields
        if percentage is not None:
            existing.percentage = min(max(percentage, 0.0), 100.0)

        if stage is not None:
            existing.stage = stage

        if message is not None:
            existing.message = message

        if current_step is not None:
            existing.current_step = current_step
            # Auto-calculate percentage from steps
            if existing.total_steps and existing.total_steps > 0:
                existing.percentage = (current_step / existing.total_steps) * 100.0

        if metadata:
            existing.metadata.update(metadata)

        existing.updated_at = now

        # Calculate ETA
        existing.eta_seconds = self._calculate_eta(existing)

        # Set stage to running if not explicitly set
        if stage is None and existing.stage == ProgressStage.STARTING:
            existing.stage = ProgressStage.RUNNING

        await self._emit_progress(existing)

        return existing

    async def complete(
        self,
        job_id: str,
        message: Optional[str] = None,
    ) -> Optional[ProgressUpdate]:
        """
        Mark a job as complete.

        Args:
            job_id: Job identifier
            message: Optional completion message

        Returns:
            Final progress update
        """
        existing = self._progress.get(job_id)
        if not existing:
            return None

        existing.percentage = 100.0
        existing.stage = ProgressStage.COMPLETED
        existing.message = message or "Completed"
        existing.updated_at = datetime.now(timezone.utc).isoformat()
        existing.eta_seconds = 0

        await self._emit_progress(existing)

        logger.debug(f"job_progress.completed: {job_id}")
        return existing

    async def fail(
        self,
        job_id: str,
        message: Optional[str] = None,
    ) -> Optional[ProgressUpdate]:
        """
        Mark a job as failed.

        Args:
            job_id: Job identifier
            message: Optional failure message

        Returns:
            Final progress update
        """
        existing = self._progress.get(job_id)
        if not existing:
            return None

        existing.stage = ProgressStage.FAILED
        existing.message = message or "Failed"
        existing.updated_at = datetime.now(timezone.utc).isoformat()
        existing.eta_seconds = None

        await self._emit_progress(existing)

        logger.debug(f"job_progress.failed: {job_id}")
        return existing

    def get_progress(self, job_id: str) -> Optional[ProgressUpdate]:
        """Get current progress for a job."""
        return self._progress.get(job_id)

    def register_callback(
        self,
        job_id: str,
        callback: Callable[[ProgressUpdate], None],
    ) -> None:
        """Register a callback for progress updates."""
        if job_id not in self._callbacks:
            self._callbacks[job_id] = []
        self._callbacks[job_id].append(callback)

    def _calculate_eta(self, update: ProgressUpdate) -> Optional[int]:
        """Calculate estimated time to completion."""
        if not update.started_at or update.percentage <= 0:
            return None

        try:
            started = datetime.fromisoformat(update.started_at)
            now = datetime.now(timezone.utc)
            elapsed = (now - started).total_seconds()

            # Calculate rate
            progress_per_second = update.percentage / elapsed
            if progress_per_second <= 0:
                return None

            remaining_progress = 100.0 - update.percentage
            eta_seconds = int(remaining_progress / progress_per_second)

            return eta_seconds

        except Exception:
            return None

    async def _emit_progress(self, update: ProgressUpdate) -> None:
        """Emit progress event."""
        # Invoke callbacks
        callbacks = self._callbacks.get(update.job_id, [])
        for callback in callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.warning(
                    "job_progress.callback_failed",
                    extra={"job_id": update.job_id, "error": str(e)},
                )

        # Publish to event bus
        publisher = self._get_publisher()
        if publisher:
            try:
                await publisher.publish(
                    "job.progress.updated",
                    update.to_dict(),
                )
            except Exception as e:
                logger.warning(
                    "job_progress.publish_failed",
                    extra={"job_id": update.job_id, "error": str(e)},
                )

    def _get_publisher(self) -> Optional[Any]:
        """Get event publisher."""
        if self._publisher is not None:
            return self._publisher

        try:
            from app.events import get_publisher
            return get_publisher()
        except ImportError:
            return None


# =========================
# GAP-158: Job Audit Evidence
# =========================


class JobAuditEventType(str, Enum):
    """Types of job audit events."""

    JOB_CREATED = "job_created"
    JOB_SCHEDULED = "job_scheduled"
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_RETRIED = "job_retried"
    JOB_CANCELLED = "job_cancelled"
    JOB_DEAD_LETTERED = "job_dead_lettered"


@dataclass
class JobAuditEvent:
    """
    Audit event for job execution.

    Provides tamper-evident audit trail for compliance.
    """

    event_id: str
    event_type: JobAuditEventType
    job_id: str
    tenant_id: str
    timestamp: str
    # Execution context
    handler: Optional[str] = None
    attempt_number: int = 1
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    # Payload hash (not raw for privacy)
    payload_hash: Optional[str] = None
    result_hash: Optional[str] = None
    # Integrity
    integrity_hash: Optional[str] = None
    previous_event_hash: Optional[str] = None
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Compute integrity hash."""
        if self.integrity_hash is None:
            self.integrity_hash = self._compute_integrity_hash()

    def _compute_integrity_hash(self) -> str:
        """Compute tamper-evident integrity hash."""
        hash_input = (
            f"{self.event_id}|{self.event_type.value}|{self.job_id}|"
            f"{self.tenant_id}|{self.timestamp}|{self.previous_event_hash or ''}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()[:32]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "job_id": self.job_id,
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp,
            "handler": self.handler,
            "attempt_number": self.attempt_number,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "payload_hash": self.payload_hash,
            "result_hash": self.result_hash,
            "integrity_hash": self.integrity_hash,
            "previous_event_hash": self.previous_event_hash,
            "metadata": self.metadata,
        }

    def verify_integrity(self) -> bool:
        """Verify integrity hash is valid."""
        expected = self._compute_integrity_hash()
        return self.integrity_hash == expected


def _hash_value(value: Any) -> str:
    """Hash a value for audit purposes."""
    if value is None:
        return ""
    serialized = str(value)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


class JobAuditEmitter:
    """
    Emits audit events for job execution.

    GAP-158: Job Audit Evidence

    Provides:
    - Compliance-grade audit trail
    - Tamper-evident event chain
    - Execution context capture
    """

    def __init__(self, publisher: Optional[Any] = None):
        """
        Initialize the audit emitter.

        Args:
            publisher: Event publisher
        """
        self._publisher = publisher
        self._last_event_hash: Optional[str] = None
        self._event_counter: int = 0

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import uuid
        self._event_counter += 1
        return f"job-audit-{uuid.uuid4().hex[:12]}-{self._event_counter}"

    async def emit_created(
        self,
        job_id: str,
        tenant_id: str,
        handler: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> JobAuditEvent:
        """Emit job created event."""
        event = JobAuditEvent(
            event_id=self._generate_event_id(),
            event_type=JobAuditEventType.JOB_CREATED,
            job_id=job_id,
            tenant_id=tenant_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            handler=handler,
            payload_hash=_hash_value(payload) if payload else None,
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def emit_started(
        self,
        job_id: str,
        tenant_id: str,
        handler: str,
        attempt_number: int = 1,
    ) -> JobAuditEvent:
        """Emit job started event."""
        event = JobAuditEvent(
            event_id=self._generate_event_id(),
            event_type=JobAuditEventType.JOB_STARTED,
            job_id=job_id,
            tenant_id=tenant_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            handler=handler,
            attempt_number=attempt_number,
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def emit_completed(
        self,
        job_id: str,
        tenant_id: str,
        duration_ms: int,
        result: Optional[Dict[str, Any]] = None,
    ) -> JobAuditEvent:
        """Emit job completed event."""
        event = JobAuditEvent(
            event_id=self._generate_event_id(),
            event_type=JobAuditEventType.JOB_COMPLETED,
            job_id=job_id,
            tenant_id=tenant_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_ms=duration_ms,
            result_hash=_hash_value(result) if result else None,
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def emit_failed(
        self,
        job_id: str,
        tenant_id: str,
        error: str,
        duration_ms: Optional[int] = None,
        attempt_number: int = 1,
    ) -> JobAuditEvent:
        """Emit job failed event."""
        event = JobAuditEvent(
            event_id=self._generate_event_id(),
            event_type=JobAuditEventType.JOB_FAILED,
            job_id=job_id,
            tenant_id=tenant_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            error=error,
            duration_ms=duration_ms,
            attempt_number=attempt_number,
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def emit_retried(
        self,
        job_id: str,
        tenant_id: str,
        attempt_number: int,
        delay_seconds: int,
        error: str,
    ) -> JobAuditEvent:
        """Emit job retried event."""
        event = JobAuditEvent(
            event_id=self._generate_event_id(),
            event_type=JobAuditEventType.JOB_RETRIED,
            job_id=job_id,
            tenant_id=tenant_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            error=error,
            attempt_number=attempt_number,
            metadata={"delay_seconds": delay_seconds},
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def _emit(self, event: JobAuditEvent) -> None:
        """Emit event and update chain."""
        logger.debug(
            "job_audit.emitting",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "job_id": event.job_id,
            },
        )

        try:
            publisher = self._get_publisher()
            if publisher:
                await publisher.publish(
                    f"job.audit.{event.event_type.value}",
                    event.to_dict(),
                )

            self._last_event_hash = event.integrity_hash

        except Exception as e:
            logger.error(
                "job_audit.emission_failed",
                extra={"event_id": event.event_id, "error": str(e)},
            )

    def _get_publisher(self) -> Optional[Any]:
        """Get event publisher."""
        if self._publisher is not None:
            return self._publisher

        try:
            from app.events import get_publisher
            return get_publisher()
        except ImportError:
            return None


# =========================
# Singleton Management
# =========================

_retry_manager: Optional[JobRetryManager] = None
_progress_tracker: Optional[JobProgressTracker] = None
_audit_emitter: Optional[JobAuditEmitter] = None


def get_job_retry_manager() -> JobRetryManager:
    """Get the singleton JobRetryManager."""
    global _retry_manager
    if _retry_manager is None:
        _retry_manager = JobRetryManager()
    return _retry_manager


def get_job_progress_tracker() -> JobProgressTracker:
    """Get the singleton JobProgressTracker."""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = JobProgressTracker()
    return _progress_tracker


def get_job_audit_emitter() -> JobAuditEmitter:
    """Get the singleton JobAuditEmitter."""
    global _audit_emitter
    if _audit_emitter is None:
        _audit_emitter = JobAuditEmitter()
    return _audit_emitter


def reset_job_execution_services() -> None:
    """Reset all singletons (for testing)."""
    global _retry_manager, _progress_tracker, _audit_emitter
    _retry_manager = None
    _progress_tracker = None
    _audit_emitter = None
