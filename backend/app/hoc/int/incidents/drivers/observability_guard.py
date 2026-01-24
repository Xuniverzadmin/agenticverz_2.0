# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: worker (run execution)
#   Execution: async
# Role: Observability requirements guard - ensures trace creation with configurable failure modes
# Callers: RunRunner (L5)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: PIN-454 (Cross-Domain Orchestration Audit), FIX-004

"""
Observability Guard (L5 Execution)

This guard ensures observability requirements are met during run execution.
It handles trace creation failures according to a configurable mode.

Problem Addressed (PIN-454 G-003):
- Trace failures run in "dark mode" — no observability, compliance blind spot
- Current behavior silently continues execution when traces fail
- No indication in the run record that observability was degraded

Modes:
- STRICT: Fail run if trace creation fails (max observability, may reduce availability)
- DEGRADED: Continue but mark run as degraded (balanced — recommended)
- PERMISSIVE: Continue silently (current behavior — not recommended)

Usage:
    guard = ObservabilityGuard(mode="DEGRADED")
    trace_id = await guard.ensure_trace(trace_store, run)

    if guard.is_degraded:
        # Run is executing without full observability
        run.observability_status = "DEGRADED"
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger("nova.worker.observability_guard")


class ObservabilityMode(str, Enum):
    """Observability enforcement mode."""

    STRICT = "STRICT"  # Fail run if trace creation fails
    DEGRADED = "DEGRADED"  # Continue but mark as degraded (recommended)
    PERMISSIVE = "PERMISSIVE"  # Continue silently (legacy behavior)


class ObservabilityStatus(str, Enum):
    """Observability status for a run."""

    FULL = "FULL"  # All observability working
    DEGRADED = "DEGRADED"  # Observability partially failed
    NONE = "NONE"  # No observability (trace creation failed in PERMISSIVE mode)


class ObservabilityFailure(Exception):
    """
    Raised when observability requirements cannot be met in STRICT mode.

    This exception should halt the run to prevent unobservable execution.
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


@dataclass
class ObservabilityResult:
    """Result of observability guard operations."""

    trace_id: Optional[str] = None
    status: ObservabilityStatus = ObservabilityStatus.FULL
    error: Optional[str] = None
    degraded_at: Optional[datetime] = None


class ObservabilityGuard:
    """
    Guard for observability requirements during run execution.

    Ensures trace creation succeeds or handles failures according
    to the configured mode.

    Layer: L5 (Execution)
    Callers: RunRunner
    """

    def __init__(self, mode: Optional[str] = None):
        """
        Initialize the observability guard.

        Args:
            mode: Observability mode (STRICT, DEGRADED, PERMISSIVE).
                  Defaults to OBSERVABILITY_MODE env var or DEGRADED.
        """
        mode_str = mode or os.getenv("OBSERVABILITY_MODE", "DEGRADED")
        try:
            self.mode = ObservabilityMode(mode_str.upper())
        except ValueError:
            logger.warning(
                f"Invalid OBSERVABILITY_MODE '{mode_str}', defaulting to DEGRADED"
            )
            self.mode = ObservabilityMode.DEGRADED

        self._status = ObservabilityStatus.FULL
        self._error: Optional[str] = None
        self._degraded_at: Optional[datetime] = None

    @property
    def is_degraded(self) -> bool:
        """Check if observability is degraded."""
        return self._status != ObservabilityStatus.FULL

    @property
    def status(self) -> ObservabilityStatus:
        """Get current observability status."""
        return self._status

    @property
    def error(self) -> Optional[str]:
        """Get error message if observability failed."""
        return self._error

    async def ensure_trace(
        self,
        trace_store,  # Type: PostgresTraceStore (imported at L5 level)
        run_id: str,
        tenant_id: str,
        agent_id: Optional[str] = None,
    ) -> ObservabilityResult:
        """
        Ensure trace is created for a run, handling failures per mode.

        Args:
            trace_store: The trace store instance
            run_id: ID of the run
            tenant_id: Tenant scope
            agent_id: Optional agent ID

        Returns:
            ObservabilityResult with trace_id and status

        Raises:
            ObservabilityFailure: In STRICT mode if trace creation fails
        """
        try:
            trace_id = await trace_store.start_trace(
                run_id=run_id,
                tenant_id=tenant_id,
                agent_id=agent_id,
            )

            logger.debug(
                "observability_guard.ensure_trace succeeded",
                extra={"run_id": run_id, "trace_id": trace_id}
            )

            return ObservabilityResult(
                trace_id=trace_id,
                status=ObservabilityStatus.FULL,
            )

        except Exception as e:
            error_msg = str(e)
            logger.warning(
                f"observability_guard.ensure_trace failed: {error_msg}",
                extra={"run_id": run_id, "mode": self.mode.value}
            )

            if self.mode == ObservabilityMode.STRICT:
                # STRICT: Fail the run entirely
                raise ObservabilityFailure(
                    f"Trace creation failed (STRICT mode): {error_msg}",
                    original_error=e,
                )

            elif self.mode == ObservabilityMode.DEGRADED:
                # DEGRADED: Continue but mark as degraded
                self._status = ObservabilityStatus.DEGRADED
                self._error = error_msg
                self._degraded_at = datetime.now(timezone.utc)

                logger.warning(
                    "observability_guard: continuing in DEGRADED mode",
                    extra={"run_id": run_id, "error": error_msg}
                )

                return ObservabilityResult(
                    trace_id=None,
                    status=ObservabilityStatus.DEGRADED,
                    error=error_msg,
                    degraded_at=self._degraded_at,
                )

            else:  # PERMISSIVE
                # PERMISSIVE: Continue silently (legacy behavior)
                self._status = ObservabilityStatus.NONE

                logger.warning(
                    "observability_guard: continuing in PERMISSIVE mode (no trace)",
                    extra={"run_id": run_id, "error": error_msg}
                )

                return ObservabilityResult(
                    trace_id=None,
                    status=ObservabilityStatus.NONE,
                    error=error_msg,
                )

    async def record_step(
        self,
        trace_store,
        trace_id: Optional[str],
        step_data: dict,
    ) -> bool:
        """
        Record a trace step, handling failures gracefully.

        If we're already in DEGRADED or NONE status, this is best-effort.

        Args:
            trace_store: The trace store instance
            trace_id: The trace ID (may be None if trace creation failed)
            step_data: Step data to record

        Returns:
            True if step was recorded, False otherwise
        """
        if trace_id is None:
            # No trace — can't record step
            return False

        try:
            await trace_store.add_step(trace_id=trace_id, **step_data)
            return True
        except Exception as e:
            logger.warning(
                f"observability_guard.record_step failed: {e}",
                extra={"trace_id": trace_id}
            )
            # Don't escalate — step recording failures don't halt runs
            return False

    def get_result(self) -> ObservabilityResult:
        """Get the current observability result."""
        return ObservabilityResult(
            trace_id=None,  # Caller should track trace_id separately
            status=self._status,
            error=self._error,
            degraded_at=self._degraded_at,
        )


def get_observability_guard(mode: Optional[str] = None) -> ObservabilityGuard:
    """
    Factory function for ObservabilityGuard.

    Args:
        mode: Optional mode override (STRICT, DEGRADED, PERMISSIVE)

    Returns:
        ObservabilityGuard instance
    """
    return ObservabilityGuard(mode=mode)
