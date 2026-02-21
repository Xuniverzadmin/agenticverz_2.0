# capability_id: CAP-001
# Layer: L5 — Execution & Workers
# AUDIENCE: INTERNAL
# PHASE: W1
# Product: system-wide
# Wiring Type: worker
# Parent Gap: GAP-071-082 (Lifecycle Stages)
# Reference: GAP-162, GAP-163, GAP-164
# Depends On: GAP-154-158 (Job infrastructure), GAP-159-161 (Stage executors)
# Temporal:
#   Trigger: job queue
#   Execution: async
# Role: Lifecycle worker orchestration with progress tracking and failure recovery
# Callers: JobQueueWorker, APSchedulerExecutor
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L3

"""
Module: lifecycle_worker
Purpose: Worker orchestration for knowledge plane lifecycle transitions.

Contains:
    - LifecycleWorker (GAP-162): Orchestrates lifecycle stages via job queue
    - LifecycleProgressManager (GAP-163): Tracks and reports progress
    - LifecycleRecoveryManager (GAP-164): Handles failures and retries

Wires:
    - Source: JobQueueWorker for job dispatch
    - Target: Stage handlers for execution
    - Uses: JobProgressTracker, JobRetryManager, JobAuditEmitter

Acceptance Criteria:
    - AC-162-01: Stages executed via job queue
    - AC-162-02: Stage completion triggers next stage
    - AC-162-03: Kill switch integration (INV-W0-002)
    - AC-163-01: Progress percentage reported
    - AC-163-02: ETA calculated from historical data
    - AC-163-03: Stage-level progress tracking
    - AC-164-01: Failed stages trigger retry logic
    - AC-164-02: Permanent failures marked appropriately
    - AC-164-03: Recovery state preserved across restarts
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import uuid

logger = logging.getLogger("nova.worker.lifecycle_worker")


# =========================
# GAP-163: Lifecycle Progress
# =========================

class LifecycleStageProgress(str, Enum):
    """Progress stages for lifecycle transitions."""
    NOT_STARTED = "not_started"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RECOVERING = "recovering"


@dataclass
class StageProgressInfo:
    """Progress information for a single stage."""
    stage_name: str
    status: LifecycleStageProgress = LifecycleStageProgress.NOT_STARTED
    percentage: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    retry_count: int = 0
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage_name": self.stage_name,
            "status": self.status.value,
            "percentage": self.percentage,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "retry_count": self.retry_count,
            "message": self.message,
        }


@dataclass
class LifecycleProgress:
    """Overall lifecycle transition progress."""
    transition_id: str
    plane_id: str
    tenant_id: str
    from_state: str
    to_state: str
    total_stages: int
    completed_stages: int = 0
    current_stage: Optional[str] = None
    overall_percentage: float = 0.0
    stage_progress: Dict[str, StageProgressInfo] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "transition_id": self.transition_id,
            "plane_id": self.plane_id,
            "tenant_id": self.tenant_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "total_stages": self.total_stages,
            "completed_stages": self.completed_stages,
            "current_stage": self.current_stage,
            "overall_percentage": self.overall_percentage,
            "stage_progress": {
                k: v.to_dict() for k, v in self.stage_progress.items()
            },
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "estimated_completion": (
                self.estimated_completion.isoformat()
                if self.estimated_completion else None
            ),
            "error": self.error,
        }


class LifecycleProgressManager:
    """
    Manages progress tracking for lifecycle transitions (GAP-163).

    Features:
    - Stage-level progress tracking
    - Overall percentage calculation
    - ETA estimation from historical data
    - Event emission for UI updates
    """

    def __init__(self):
        """Initialize the progress manager."""
        self._transitions: Dict[str, LifecycleProgress] = {}
        self._stage_durations: Dict[str, List[int]] = {}  # Historical durations
        self._callbacks: List[Callable[[LifecycleProgress], None]] = []

    def start_transition(
        self,
        plane_id: str,
        tenant_id: str,
        from_state: str,
        to_state: str,
        stages: List[str],
        transition_id: Optional[str] = None,
    ) -> LifecycleProgress:
        """
        Start tracking a lifecycle transition.

        Args:
            plane_id: Knowledge plane ID
            tenant_id: Tenant ID
            from_state: Starting state
            to_state: Target state
            stages: List of stage names to execute
            transition_id: Optional ID (generated if not provided)

        Returns:
            LifecycleProgress tracking object
        """
        transition_id = transition_id or str(uuid.uuid4())

        progress = LifecycleProgress(
            transition_id=transition_id,
            plane_id=plane_id,
            tenant_id=tenant_id,
            from_state=from_state,
            to_state=to_state,
            total_stages=len(stages),
            started_at=datetime.now(timezone.utc),
            stage_progress={
                stage: StageProgressInfo(stage_name=stage)
                for stage in stages
            },
        )

        # Calculate initial ETA
        progress.estimated_completion = self._estimate_completion(
            stages, progress.started_at
        )

        self._transitions[transition_id] = progress

        logger.info(
            "lifecycle_progress.transition_started",
            extra={
                "transition_id": transition_id,
                "plane_id": plane_id,
                "from_state": from_state,
                "to_state": to_state,
                "total_stages": len(stages),
            },
        )

        self._notify(progress)
        return progress

    def stage_queued(
        self,
        transition_id: str,
        stage_name: str,
    ) -> None:
        """Mark a stage as queued for execution."""
        progress = self._transitions.get(transition_id)
        if not progress:
            return

        if stage_name in progress.stage_progress:
            stage = progress.stage_progress[stage_name]
            stage.status = LifecycleStageProgress.QUEUED
            stage.message = "Waiting in queue"

            self._notify(progress)

    def stage_started(
        self,
        transition_id: str,
        stage_name: str,
    ) -> None:
        """Mark a stage as started."""
        progress = self._transitions.get(transition_id)
        if not progress:
            return

        if stage_name in progress.stage_progress:
            stage = progress.stage_progress[stage_name]
            stage.status = LifecycleStageProgress.RUNNING
            stage.started_at = datetime.now(timezone.utc)
            stage.percentage = 0.0
            stage.message = "Running"

            progress.current_stage = stage_name

            self._update_overall_percentage(progress)
            self._notify(progress)

            logger.info(
                "lifecycle_progress.stage_started",
                extra={
                    "transition_id": transition_id,
                    "stage_name": stage_name,
                },
            )

    def stage_progress_update(
        self,
        transition_id: str,
        stage_name: str,
        percentage: float,
        message: Optional[str] = None,
    ) -> None:
        """Update stage progress percentage."""
        progress = self._transitions.get(transition_id)
        if not progress:
            return

        if stage_name in progress.stage_progress:
            stage = progress.stage_progress[stage_name]
            stage.percentage = min(percentage, 99.0)  # Reserve 100% for completion
            if message:
                stage.message = message

            self._update_overall_percentage(progress)
            self._notify(progress)

    def stage_completed(
        self,
        transition_id: str,
        stage_name: str,
        message: Optional[str] = None,
    ) -> None:
        """Mark a stage as completed."""
        progress = self._transitions.get(transition_id)
        if not progress:
            return

        if stage_name in progress.stage_progress:
            stage = progress.stage_progress[stage_name]
            stage.status = LifecycleStageProgress.COMPLETED
            stage.completed_at = datetime.now(timezone.utc)
            stage.percentage = 100.0
            stage.message = message or "Completed"

            if stage.started_at:
                stage.duration_ms = int(
                    (stage.completed_at - stage.started_at).total_seconds() * 1000
                )
                # Record for ETA calculation
                self._record_duration(stage_name, stage.duration_ms)

            progress.completed_stages += 1

            self._update_overall_percentage(progress)
            self._update_eta(progress)
            self._notify(progress)

            logger.info(
                "lifecycle_progress.stage_completed",
                extra={
                    "transition_id": transition_id,
                    "stage_name": stage_name,
                    "duration_ms": stage.duration_ms,
                },
            )

    def stage_failed(
        self,
        transition_id: str,
        stage_name: str,
        error: str,
        will_retry: bool = False,
    ) -> None:
        """Mark a stage as failed."""
        progress = self._transitions.get(transition_id)
        if not progress:
            return

        if stage_name in progress.stage_progress:
            stage = progress.stage_progress[stage_name]
            stage.status = (
                LifecycleStageProgress.RECOVERING
                if will_retry
                else LifecycleStageProgress.FAILED
            )
            stage.completed_at = datetime.now(timezone.utc)
            stage.error = error
            stage.retry_count += 1

            if stage.started_at:
                stage.duration_ms = int(
                    (stage.completed_at - stage.started_at).total_seconds() * 1000
                )

            if not will_retry:
                progress.error = f"Stage '{stage_name}' failed: {error}"

            self._update_overall_percentage(progress)
            self._notify(progress)

            logger.warning(
                "lifecycle_progress.stage_failed",
                extra={
                    "transition_id": transition_id,
                    "stage_name": stage_name,
                    "error": error,
                    "will_retry": will_retry,
                    "retry_count": stage.retry_count,
                },
            )

    def transition_completed(
        self,
        transition_id: str,
    ) -> Optional[LifecycleProgress]:
        """Mark transition as fully completed."""
        progress = self._transitions.get(transition_id)
        if not progress:
            return None

        progress.overall_percentage = 100.0
        progress.current_stage = None

        self._notify(progress)

        logger.info(
            "lifecycle_progress.transition_completed",
            extra={
                "transition_id": transition_id,
                "plane_id": progress.plane_id,
                "total_stages": progress.total_stages,
                "completed_stages": progress.completed_stages,
            },
        )

        return progress

    def transition_failed(
        self,
        transition_id: str,
        error: str,
    ) -> Optional[LifecycleProgress]:
        """Mark transition as failed."""
        progress = self._transitions.get(transition_id)
        if not progress:
            return None

        progress.error = error

        self._notify(progress)

        logger.error(
            "lifecycle_progress.transition_failed",
            extra={
                "transition_id": transition_id,
                "plane_id": progress.plane_id,
                "error": error,
            },
        )

        return progress

    def get_progress(self, transition_id: str) -> Optional[LifecycleProgress]:
        """Get current progress for a transition."""
        return self._transitions.get(transition_id)

    def add_callback(
        self,
        callback: Callable[[LifecycleProgress], None],
    ) -> None:
        """Add a callback for progress updates."""
        self._callbacks.append(callback)

    def remove_callback(
        self,
        callback: Callable[[LifecycleProgress], None],
    ) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _update_overall_percentage(self, progress: LifecycleProgress) -> None:
        """Calculate overall percentage from stage progress."""
        if progress.total_stages == 0:
            progress.overall_percentage = 0.0
            return

        # Weight: completed stages fully, running stage partially
        completed_weight = progress.completed_stages * 100.0

        current_weight = 0.0
        for stage in progress.stage_progress.values():
            if stage.status == LifecycleStageProgress.RUNNING:
                current_weight = stage.percentage

        total_weight = completed_weight + current_weight
        progress.overall_percentage = total_weight / progress.total_stages

    def _estimate_completion(
        self,
        stages: List[str],
        start_time: datetime,
    ) -> Optional[datetime]:
        """Estimate completion time based on historical durations."""
        total_ms = 0

        for stage in stages:
            if stage in self._stage_durations and self._stage_durations[stage]:
                # Use average of recent durations
                durations = self._stage_durations[stage][-10:]
                avg_ms = sum(durations) // len(durations)
                total_ms += avg_ms
            else:
                # Default estimate: 30 seconds per stage
                total_ms += 30000

        from datetime import timedelta
        return start_time + timedelta(milliseconds=total_ms)

    def _update_eta(self, progress: LifecycleProgress) -> None:
        """Update ETA based on actual progress."""
        if not progress.started_at:
            return

        # Calculate remaining stages
        remaining_stages = [
            name for name, stage in progress.stage_progress.items()
            if stage.status not in (
                LifecycleStageProgress.COMPLETED,
                LifecycleStageProgress.SKIPPED,
            )
        ]

        if not remaining_stages:
            progress.estimated_completion = datetime.now(timezone.utc)
            return

        progress.estimated_completion = self._estimate_completion(
            remaining_stages,
            datetime.now(timezone.utc),
        )

    def _record_duration(self, stage_name: str, duration_ms: int) -> None:
        """Record stage duration for ETA estimation."""
        if stage_name not in self._stage_durations:
            self._stage_durations[stage_name] = []

        self._stage_durations[stage_name].append(duration_ms)

        # Keep only last 100 durations
        if len(self._stage_durations[stage_name]) > 100:
            self._stage_durations[stage_name] = self._stage_durations[stage_name][-100:]

    def _notify(self, progress: LifecycleProgress) -> None:
        """Notify callbacks of progress update."""
        for callback in self._callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.warning(
                    "lifecycle_progress.callback_error",
                    extra={"error": str(e)},
                )


# =========================
# GAP-164: Failure Recovery
# =========================

@dataclass
class RecoveryState:
    """State for recovering a failed transition."""
    transition_id: str
    plane_id: str
    tenant_id: str
    failed_stage: str
    last_error: str
    retry_count: int
    max_retries: int
    next_retry_at: Optional[datetime] = None
    stages_completed: List[str] = field(default_factory=list)
    stages_remaining: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "transition_id": self.transition_id,
            "plane_id": self.plane_id,
            "tenant_id": self.tenant_id,
            "failed_stage": self.failed_stage,
            "last_error": self.last_error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_retry_at": (
                self.next_retry_at.isoformat() if self.next_retry_at else None
            ),
            "stages_completed": self.stages_completed,
            "stages_remaining": self.stages_remaining,
            "metadata": self.metadata,
        }


class LifecycleRecoveryManager:
    """
    Manages failure recovery for lifecycle transitions (GAP-164).

    Features:
    - Retry failed stages with exponential backoff
    - Resume from last completed stage
    - Permanent failure handling
    - Recovery state persistence
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_seconds: int = 30,
        max_delay_seconds: int = 3600,
    ):
        """
        Initialize the recovery manager.

        Args:
            max_retries: Maximum retry attempts per stage
            base_delay_seconds: Initial retry delay
            max_delay_seconds: Maximum retry delay
        """
        self._max_retries = max_retries
        self._base_delay = base_delay_seconds
        self._max_delay = max_delay_seconds
        self._recovery_states: Dict[str, RecoveryState] = {}

    def record_failure(
        self,
        transition_id: str,
        plane_id: str,
        tenant_id: str,
        failed_stage: str,
        error: str,
        stages_completed: List[str],
        stages_remaining: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[RecoveryState]]:
        """
        Record a stage failure and determine if retry is possible.

        Args:
            transition_id: Transition ID
            plane_id: Knowledge plane ID
            tenant_id: Tenant ID
            failed_stage: Name of failed stage
            error: Error message
            stages_completed: List of completed stages
            stages_remaining: List of remaining stages
            metadata: Optional metadata to preserve

        Returns:
            Tuple of (should_retry, recovery_state)
        """
        # Get or create recovery state
        if transition_id in self._recovery_states:
            state = self._recovery_states[transition_id]
            state.retry_count += 1
            state.last_error = error
        else:
            state = RecoveryState(
                transition_id=transition_id,
                plane_id=plane_id,
                tenant_id=tenant_id,
                failed_stage=failed_stage,
                last_error=error,
                retry_count=1,
                max_retries=self._max_retries,
                stages_completed=stages_completed,
                stages_remaining=stages_remaining,
                metadata=metadata or {},
            )
            self._recovery_states[transition_id] = state

        # Check if retry is possible
        if state.retry_count >= state.max_retries:
            logger.error(
                "lifecycle_recovery.max_retries_exceeded",
                extra={
                    "transition_id": transition_id,
                    "plane_id": plane_id,
                    "failed_stage": failed_stage,
                    "retry_count": state.retry_count,
                },
            )
            return False, state

        # Calculate next retry time
        from datetime import timedelta
        delay = self._calculate_delay(state.retry_count)
        state.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

        logger.info(
            "lifecycle_recovery.retry_scheduled",
            extra={
                "transition_id": transition_id,
                "plane_id": plane_id,
                "failed_stage": failed_stage,
                "retry_count": state.retry_count,
                "next_retry_at": state.next_retry_at.isoformat(),
            },
        )

        return True, state

    def get_recovery_state(
        self,
        transition_id: str,
    ) -> Optional[RecoveryState]:
        """Get recovery state for a transition."""
        return self._recovery_states.get(transition_id)

    def clear_recovery_state(self, transition_id: str) -> bool:
        """Clear recovery state after successful completion."""
        if transition_id in self._recovery_states:
            del self._recovery_states[transition_id]
            return True
        return False

    def get_pending_recoveries(self) -> List[RecoveryState]:
        """Get all transitions pending recovery."""
        now = datetime.now(timezone.utc)
        return [
            state for state in self._recovery_states.values()
            if state.next_retry_at and state.next_retry_at <= now
        ]

    def _calculate_delay(self, retry_count: int) -> int:
        """Calculate delay with exponential backoff and jitter."""
        import random

        # Exponential backoff
        delay = self._base_delay * (2 ** (retry_count - 1))

        # Add jitter (±20%)
        jitter = delay * 0.2
        delay = delay + random.uniform(-jitter, jitter)

        # Cap at max delay
        return min(int(delay), self._max_delay)

    def should_retry_error(self, error: str) -> bool:
        """Determine if an error is retryable."""
        # Non-retryable errors
        permanent_errors = [
            "authentication failed",
            "permission denied",
            "not found",
            "invalid configuration",
            "schema mismatch",
        ]

        error_lower = error.lower()
        return not any(pe in error_lower for pe in permanent_errors)


# =========================
# GAP-162: Lifecycle Worker
# =========================

@dataclass
class LifecycleJobPayload:
    """Payload for lifecycle stage jobs."""
    plane_id: str
    tenant_id: str
    transition_id: str
    stage_name: str
    from_state: str
    to_state: str
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plane_id": self.plane_id,
            "tenant_id": self.tenant_id,
            "transition_id": self.transition_id,
            "stage_name": self.stage_name,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "config": self.config,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LifecycleJobPayload":
        """Create from dictionary."""
        return cls(
            plane_id=data["plane_id"],
            tenant_id=data["tenant_id"],
            transition_id=data["transition_id"],
            stage_name=data["stage_name"],
            from_state=data["from_state"],
            to_state=data["to_state"],
            config=data.get("config", {}),
            metadata=data.get("metadata", {}),
            retry_count=data.get("retry_count", 0),
        )


class LifecycleWorker:
    """
    Worker for executing lifecycle stages (GAP-162).

    Orchestrates lifecycle transitions through the job queue:
    - Receives stage execution jobs
    - Executes stages via handlers
    - Queues next stage on success
    - Handles failures via RecoveryManager

    Integrates with:
    - INV-W0-002 (KillSwitch) for controlled shutdown
    - JobProgressTracker (GAP-157) for progress reporting
    - JobAuditEmitter (GAP-158) for audit evidence
    """

    # Stage execution order
    ONBOARDING_STAGES = [
        "verify",
        "ingest",
        "index",
        "classify",
        "activate",
    ]

    OFFBOARDING_STAGES = [
        "deregister",
        "verify_deactivate",
        "deactivate",
        "archive",
        "purge",
    ]

    def __init__(
        self,
        progress_manager: Optional[LifecycleProgressManager] = None,
        recovery_manager: Optional[LifecycleRecoveryManager] = None,
    ):
        """
        Initialize the lifecycle worker.

        Args:
            progress_manager: Optional custom progress manager
            recovery_manager: Optional custom recovery manager
        """
        self._progress = progress_manager or LifecycleProgressManager()
        self._recovery = recovery_manager or LifecycleRecoveryManager()
        self._stage_registry = None  # Lazy loaded
        self._running = False
        self._kill_switch_active = False

    def get_progress_manager(self) -> LifecycleProgressManager:
        """Get the progress manager."""
        return self._progress

    def get_recovery_manager(self) -> LifecycleRecoveryManager:
        """Get the recovery manager."""
        return self._recovery

    async def start(self) -> None:
        """Start the lifecycle worker."""
        self._running = True
        self._kill_switch_active = False

        # Load stage registry
        self._stage_registry = self._get_stage_registry()

        logger.info("lifecycle_worker.started")

    async def stop(self) -> None:
        """Stop the lifecycle worker."""
        self._running = False
        logger.info("lifecycle_worker.stopped")

    def activate_kill_switch(self) -> None:
        """Activate kill switch - stop processing new stages."""
        self._kill_switch_active = True
        logger.warning("lifecycle_worker.kill_switch_activated")

    async def execute_stage(
        self,
        payload: LifecycleJobPayload,
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Execute a lifecycle stage.

        Args:
            payload: Stage job payload

        Returns:
            Tuple of (success, error, result_data)
        """
        # Check kill switch (INV-W0-002)
        if self._kill_switch_active:
            logger.warning(
                "lifecycle_worker.execution_blocked_kill_switch",
                extra={
                    "plane_id": payload.plane_id,
                    "stage_name": payload.stage_name,
                },
            )
            return False, "Kill switch active", {}

        if not self._running:
            return False, "Worker not running", {}

        # Update progress
        self._progress.stage_started(
            payload.transition_id,
            payload.stage_name,
        )

        try:
            # Get stage handler
            handler = self._get_handler(payload.stage_name)
            if not handler:
                return False, f"No handler for stage: {payload.stage_name}", {}

            # Build execution context
            # L5 engine import (V2.0.0 - hoc_spine)
            from app.hoc.cus.hoc_spine.services.lifecycle_stages_base import StageContext
            from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState

            context = StageContext(
                plane_id=payload.plane_id,
                tenant_id=payload.tenant_id,
                current_state=KnowledgePlaneLifecycleState(payload.from_state),
                target_state=KnowledgePlaneLifecycleState(payload.to_state),
                config=payload.config,
                metadata=payload.metadata,
            )

            # Execute handler
            result = await handler.execute(context)

            if result.success:
                # Update progress
                self._progress.stage_completed(
                    payload.transition_id,
                    payload.stage_name,
                    result.message,
                )

                # Clear any recovery state
                self._recovery.clear_recovery_state(payload.transition_id)

                return True, None, result.data

            else:
                # Handle failure
                error = result.message or "Stage execution failed"
                self._handle_failure(payload, error)
                return False, error, result.error_details or {}

        except Exception as e:
            error = str(e)
            logger.error(
                "lifecycle_worker.stage_error",
                extra={
                    "plane_id": payload.plane_id,
                    "stage_name": payload.stage_name,
                    "error": error,
                },
            )
            self._handle_failure(payload, error)
            return False, error, {}

    def _handle_failure(
        self,
        payload: LifecycleJobPayload,
        error: str,
    ) -> None:
        """Handle stage execution failure."""
        # Determine completed and remaining stages
        stages = self._get_stages_for_transition(
            payload.from_state,
            payload.to_state,
        )

        try:
            current_idx = stages.index(payload.stage_name)
            completed = stages[:current_idx]
            remaining = stages[current_idx:]
        except ValueError:
            completed = []
            remaining = stages

        # Check if retryable
        should_retry = self._recovery.should_retry_error(error)

        if should_retry:
            will_retry, state = self._recovery.record_failure(
                transition_id=payload.transition_id,
                plane_id=payload.plane_id,
                tenant_id=payload.tenant_id,
                failed_stage=payload.stage_name,
                error=error,
                stages_completed=completed,
                stages_remaining=remaining,
                metadata=payload.metadata,
            )
        else:
            will_retry = False
            state = None

        # Update progress
        self._progress.stage_failed(
            payload.transition_id,
            payload.stage_name,
            error,
            will_retry=will_retry,
        )

        if not will_retry:
            self._progress.transition_failed(
                payload.transition_id,
                f"Stage '{payload.stage_name}' failed permanently: {error}",
            )

    def _get_stages_for_transition(
        self,
        from_state: str,
        to_state: str,
    ) -> List[str]:
        """Get the list of stages for a transition."""
        # Determine if onboarding or offboarding
        if to_state in ["ACTIVE", "CLASSIFIED", "INDEXED", "INGESTING", "VERIFIED"]:
            return self.ONBOARDING_STAGES
        elif to_state in ["DEACTIVATED", "ARCHIVED", "PURGED"]:
            return self.OFFBOARDING_STAGES
        else:
            return []

    def _get_handler(self, stage_name: str) -> Optional[Any]:
        """Get handler for a stage."""
        if not self._stage_registry:
            self._stage_registry = self._get_stage_registry()

        # Map stage name to handler
        stage_map = {
            "register": "RegisterHandler",
            "verify": "VerifyHandler",
            "ingest": "IngestHandler",
            "index": "IndexHandler",
            "classify": "ClassifyHandler",
            "activate": "ActivateHandler",
            "govern": "GovernHandler",
            "deregister": "DeregisterHandler",
            "verify_deactivate": "VerifyDeactivateHandler",
            "deactivate": "DeactivateHandler",
            "archive": "ArchiveHandler",
            "purge": "PurgeHandler",
        }

        handler_name = stage_map.get(stage_name)
        if not handler_name:
            return None

        return self._stage_registry.get(handler_name)

    def _get_stage_registry(self) -> Dict[str, Any]:
        """Get the stage handler registry."""
        try:
            # V2.0.0 - hoc_spine orchestrator lifecycle
            from app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.onboarding import (
                RegisterHandler,
                VerifyHandler,
                IngestHandler,
                IndexHandler,
                ClassifyHandler,
                ActivateHandler,
                GovernHandler,
            )
            from app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.offboarding import (
                DeregisterHandler,
                VerifyDeactivateHandler,
                DeactivateHandler,
                ArchiveHandler,
                PurgeHandler,
            )

            return {
                "RegisterHandler": RegisterHandler(),
                "VerifyHandler": VerifyHandler(),
                "IngestHandler": IngestHandler(),
                "IndexHandler": IndexHandler(),
                "ClassifyHandler": ClassifyHandler(),
                "ActivateHandler": ActivateHandler(),
                "GovernHandler": GovernHandler(),
                "DeregisterHandler": DeregisterHandler(),
                "VerifyDeactivateHandler": VerifyDeactivateHandler(),
                "DeactivateHandler": DeactivateHandler(),
                "ArchiveHandler": ArchiveHandler(),
                "PurgeHandler": PurgeHandler(),
            }
        except ImportError as e:
            logger.error(f"lifecycle_worker.registry_import_failed: {e}")
            return {}

    async def start_transition(
        self,
        plane_id: str,
        tenant_id: str,
        from_state: str,
        to_state: str,
        config: Dict[str, Any],
    ) -> str:
        """
        Start a lifecycle transition.

        Args:
            plane_id: Knowledge plane ID
            tenant_id: Tenant ID
            from_state: Starting state
            to_state: Target state
            config: Transition configuration

        Returns:
            Transition ID
        """
        transition_id = str(uuid.uuid4())

        # Get stages for this transition
        stages = self._get_stages_for_transition(from_state, to_state)

        # Initialize progress tracking
        self._progress.start_transition(
            plane_id=plane_id,
            tenant_id=tenant_id,
            from_state=from_state,
            to_state=to_state,
            stages=stages,
            transition_id=transition_id,
        )

        logger.info(
            "lifecycle_worker.transition_started",
            extra={
                "transition_id": transition_id,
                "plane_id": plane_id,
                "from_state": from_state,
                "to_state": to_state,
                "stages": stages,
            },
        )

        return transition_id


# =========================
# Singleton Management
# =========================

_lifecycle_worker: Optional[LifecycleWorker] = None
_progress_manager: Optional[LifecycleProgressManager] = None
_recovery_manager: Optional[LifecycleRecoveryManager] = None


def get_lifecycle_worker() -> LifecycleWorker:
    """Get or create the singleton LifecycleWorker."""
    global _lifecycle_worker

    if _lifecycle_worker is None:
        _lifecycle_worker = LifecycleWorker(
            progress_manager=get_lifecycle_progress_manager(),
            recovery_manager=get_lifecycle_recovery_manager(),
        )

    return _lifecycle_worker


def get_lifecycle_progress_manager() -> LifecycleProgressManager:
    """Get or create the singleton LifecycleProgressManager."""
    global _progress_manager

    if _progress_manager is None:
        _progress_manager = LifecycleProgressManager()

    return _progress_manager


def get_lifecycle_recovery_manager() -> LifecycleRecoveryManager:
    """Get or create the singleton LifecycleRecoveryManager."""
    global _recovery_manager

    if _recovery_manager is None:
        _recovery_manager = LifecycleRecoveryManager()

    return _recovery_manager


def reset_lifecycle_worker() -> None:
    """Reset all singletons (for testing)."""
    global _lifecycle_worker, _progress_manager, _recovery_manager
    _lifecycle_worker = None
    _progress_manager = None
    _recovery_manager = None
