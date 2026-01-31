# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: worker (job execution)
#   Execution: async
# Role: Guard that enforces RuntimeSwitch checks during job execution
# Callers: JobQueueWorker, lifecycle handlers, APScheduler executor
# Allowed Imports: L4 (RuntimeSwitch), L6
# Forbidden Imports: L1, L2, L3
# Reference: INV-W0-002

"""
Module: kill_switch_guard
Purpose: Enforce RuntimeSwitch checks during job execution.

INV-W0-002: Jobs MUST be killable at any point.

Every job execution MUST check RuntimeSwitch:
1. At start — before any work begins
2. On heartbeat — every N seconds during execution
3. On completion — before committing results

If RuntimeSwitch disables the capability, the job must be aborted.

Acceptance Criteria:
    - KS-001: All job handlers use KillSwitchGuard
    - KS-002: Heartbeat check every 30s
    - KS-003: Killed jobs do not commit
    - KS-004: Kill events audited
"""

import logging
import time
from typing import Optional, Callable, Awaitable

# V2.0.0 - hoc_spine authority
from app.hoc.hoc_spine.authority.runtime_switch import (
    is_governance_active,
    is_degraded_mode,
    get_governance_state,
)

logger = logging.getLogger("nova.worker.kill_switch_guard")


class JobKilledException(Exception):
    """
    Raised when a job is killed by RuntimeSwitch.

    This exception should NOT be caught and retried - the job must stop.
    """

    def __init__(self, job_id: str, capability: str, reason: str):
        self.job_id = job_id
        self.capability = capability
        self.reason = reason
        super().__init__(f"Job {job_id} killed: {reason}")


class KillSwitchGuard:
    """
    Guard that enforces RuntimeSwitch checks during job execution.

    INVARIANT: Jobs MUST be killable at any point.

    Usage:
        guard = KillSwitchGuard("lifecycle.ingest")

        # At start
        await guard.check_or_abort(job_id)

        # During processing (in loop)
        while processing:
            await guard.heartbeat_check(job_id)
            # ... do work ...

        # Before commit
        await guard.check_or_abort(job_id)
        await commit_results()
    """

    def __init__(
        self,
        capability: str,
        heartbeat_interval_seconds: int = 30,
        on_abort: Optional[Callable[[str, str], Awaitable[None]]] = None,
    ):
        """
        Initialize KillSwitchGuard.

        Args:
            capability: Capability being guarded (e.g., "lifecycle.ingest")
            heartbeat_interval_seconds: Interval for heartbeat checks (default 30s)
            on_abort: Optional callback when job is aborted
        """
        self._capability = capability
        self._heartbeat_interval = heartbeat_interval_seconds
        self._last_check: Optional[float] = None
        self._on_abort = on_abort

    async def check_or_abort(self, job_id: str) -> bool:
        """
        Check if capability is enabled. Raises JobKilledException if disabled.

        This is a HARD CHECK - must be called:
        1. Before any work begins
        2. Before committing results

        Args:
            job_id: Job identifier for logging

        Returns:
            True if check passed

        Raises:
            JobKilledException: If capability is disabled
        """
        # Check global governance
        if not is_governance_active():
            await self._abort_job(job_id, "Governance disabled globally")
            raise JobKilledException(
                job_id=job_id,
                capability=self._capability,
                reason="Governance disabled globally",
            )

        # Check degraded mode
        if is_degraded_mode():
            # In degraded mode, existing jobs can complete but should warn
            logger.warning(
                "kill_switch_guard.degraded_mode",
                extra={
                    "job_id": job_id,
                    "capability": self._capability,
                    "action": "allowing_completion",
                },
            )
            # Don't abort - allow to complete with warning

        # Check capability-specific toggle
        if not await self._is_capability_enabled():
            await self._abort_job(job_id, f"Capability {self._capability} disabled")
            raise JobKilledException(
                job_id=job_id,
                capability=self._capability,
                reason=f"RuntimeSwitch disabled: {self._capability}",
            )

        self._last_check = time.time()

        logger.debug(
            "kill_switch_guard.check_passed",
            extra={
                "job_id": job_id,
                "capability": self._capability,
            },
        )

        return True

    async def heartbeat_check(self, job_id: str) -> bool:
        """
        Check on heartbeat interval. No-op if interval not elapsed.

        Use this in processing loops to periodically verify the job
        should continue running.

        Args:
            job_id: Job identifier for logging

        Returns:
            True if check passed (or interval not elapsed)

        Raises:
            JobKilledException: If capability is disabled
        """
        now = time.time()

        # Skip if interval not elapsed
        if self._last_check is not None:
            elapsed = now - self._last_check
            if elapsed < self._heartbeat_interval:
                return True

        # Perform full check
        return await self.check_or_abort(job_id)

    async def _is_capability_enabled(self) -> bool:
        """
        Check if specific capability is enabled.

        Currently delegates to global governance state.
        In future, can be extended for per-capability toggles.
        """
        # For now, use global governance state
        # TODO: Add per-capability toggles in RuntimeSwitch
        return is_governance_active()

    async def _abort_job(self, job_id: str, reason: str) -> None:
        """
        Abort the job and emit audit event.

        Args:
            job_id: Job identifier
            reason: Reason for abort
        """
        logger.warning(
            "kill_switch_guard.job_aborted",
            extra={
                "job_id": job_id,
                "capability": self._capability,
                "reason": reason,
                "governance_state": get_governance_state(),
            },
        )

        # Emit abort event for audit (KS-004)
        await self._emit_abort_event(job_id, reason)

        # Call custom abort handler if provided
        if self._on_abort:
            try:
                await self._on_abort(job_id, reason)
            except Exception as e:
                logger.error(
                    "kill_switch_guard.abort_handler_failed",
                    extra={"job_id": job_id, "error": str(e)},
                )

    async def _emit_abort_event(self, job_id: str, reason: str) -> None:
        """
        Emit audit event for job abort.

        Args:
            job_id: Job identifier
            reason: Reason for abort
        """
        try:
            from app.events import get_publisher

            publisher = get_publisher()
            await publisher.publish(
                "job.killed_by_switch",
                {
                    "job_id": job_id,
                    "capability": self._capability,
                    "reason": reason,
                    "governance_state": get_governance_state(),
                    "timestamp": time.time(),
                },
            )
        except Exception as e:
            # Don't fail on event emission - just log
            logger.error(
                "kill_switch_guard.event_emit_failed",
                extra={"job_id": job_id, "error": str(e)},
            )


def get_kill_switch_guard(
    capability: str,
    heartbeat_interval_seconds: int = 30,
) -> KillSwitchGuard:
    """
    Factory to create KillSwitchGuard for a capability.

    Args:
        capability: Capability being guarded (e.g., "lifecycle.ingest")
        heartbeat_interval_seconds: Interval for heartbeat checks

    Returns:
        KillSwitchGuard instance
    """
    return KillSwitchGuard(
        capability=capability,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
    )
