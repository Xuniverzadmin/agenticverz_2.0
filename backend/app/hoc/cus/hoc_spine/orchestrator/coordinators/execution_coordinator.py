# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — pre-execution scoping + job lifecycle (retry, progress, audit)
# Callers: handlers (L4), job_executor (L4)
# Allowed Imports: hoc_spine, hoc.cus.* (lazy — L4 can import L5/L6)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Wiring Plan (scoped_execution_driver, job_execution_driver)
# artifact_class: CODE

"""
Execution Coordinator (PIN-513 Wiring)

L4 coordinator that owns pre-execution scoping and job lifecycle services.

Binds two L6 drivers:
- ScopedExecutionDriver: pre-execution risk gates, scope creation/enforcement
- JobExecutionDriver: retry strategies, progress tracking, audit trail

Responsibilities:
- Create bound scopes for MEDIUM+ risk recovery actions
- Enforce scope gates before execution proceeds
- Manage retry decisions (should_retry, calculate_delay)
- Track job progress (stages, ETA)
- Emit tamper-evident audit chain

Rules:
- No business logic (L5 engines decide WHAT; this coordinates HOW)
- No session.commit() — transaction ownership stays at L4 boundary
- Cross-domain sequencing ONLY
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("nova.hoc_spine.coordinators.execution")


class ExecutionCoordinator:
    """L4 coordinator: pre-execution scoping + job lifecycle.

    Pairs ScopedExecutionDriver (risk gates) with JobExecutionDriver
    (retry, progress, audit) to provide complete execution lifecycle
    management for L4 handlers and job_executor.
    """

    # ==================== Scoped Execution (controls L6) ====================

    async def create_scope(
        self,
        incident_id: str,
        action: str,
        intent: str = "",
        max_cost_usd: float = 0.50,
        max_attempts: int = 1,
        ttl_seconds: int = 300,
        created_by: str = "system",
    ) -> Dict[str, Any]:
        """Create a bound execution scope for a recovery action.

        Args:
            incident_id: Incident this scope is tied to
            action: Action ID permitted within scope
            intent: Human-readable intent description
            max_cost_usd: Cost ceiling
            max_attempts: Maximum execution attempts
            ttl_seconds: Scope time-to-live
            created_by: Identity that created the scope

        Returns:
            Scope dict from driver (scope_id, status, etc.)
        """
        from app.hoc.cus.controls.L6_drivers.scoped_execution_driver import (
            create_recovery_scope,
        )

        result = await create_recovery_scope(
            incident_id=incident_id,
            action=action,
            intent=intent,
            max_cost_usd=max_cost_usd,
            max_attempts=max_attempts,
            ttl_seconds=ttl_seconds,
            created_by=created_by,
        )
        logger.info(
            f"Scope created: incident_id={incident_id}, action={action}"
        )
        return result

    async def execute_with_scope(
        self,
        scope_id: str,
        action: str,
        incident_id: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute an action within a bound scope.

        Enforces all P2FC-4 gates: scope exists, not exhausted/expired,
        action matches, incident matches.

        Args:
            scope_id: Bound scope ID
            action: Action to execute
            incident_id: Incident ID (must match scope)
            parameters: Action parameters

        Returns:
            Execution result dict from driver
        """
        from app.hoc.cus.controls.L6_drivers.scoped_execution_driver import (
            execute_with_scope,
        )

        return await execute_with_scope(
            scope_id=scope_id,
            action=action,
            incident_id=incident_id,
            parameters=parameters,
        )

    # ==================== Job Retry (logs L6) ====================

    def should_retry(
        self,
        job_id: str,
        error: str,
        attempt_number: int,
    ) -> Dict[str, Any]:
        """Check if a failed job should be retried.

        Args:
            job_id: Job identifier
            error: Error message from failure
            attempt_number: Current attempt number (1-based)

        Returns:
            Dict with should_retry, delay_seconds, attempt_number
        """
        from app.hoc.cus.logs.L6_drivers.job_execution_driver import (
            JobRetryManager,
        )

        manager = JobRetryManager()
        retry = manager.should_retry(
            job_id=job_id,
            error=error,
            attempt_number=attempt_number,
        )
        delay = manager.calculate_delay(attempt_number) if retry else 0

        return {
            "should_retry": retry,
            "delay_seconds": delay,
            "attempt": attempt_number,
        }

    # ==================== Job Progress (logs L6) ====================

    async def track_progress(
        self,
        job_id: str,
        percentage: Optional[float] = None,
        stage: Optional[str] = None,
        message: Optional[str] = None,
        current_step: Optional[int] = None,
    ) -> None:
        """Update job progress tracking.

        Args:
            job_id: Job identifier
            percentage: Completion percentage (0-100)
            stage: Current stage name
            message: Optional status message
            current_step: Current step index
        """
        from app.hoc.cus.logs.L6_drivers.job_execution_driver import (
            JobProgressTracker,
        )

        tracker = JobProgressTracker()
        await tracker.update(
            job_id=job_id,
            percentage=percentage,
            stage=stage,
            message=message,
            current_step=current_step,
        )

    # ==================== Job Audit (logs L6) ====================

    async def emit_audit_created(
        self,
        job_id: str,
        tenant_id: str,
        handler: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Emit a job-created audit event.

        Args:
            job_id: Job identifier
            tenant_id: Tenant identifier
            handler: Handler name
            payload: Job payload
        """
        from app.hoc.cus.logs.L6_drivers.job_execution_driver import (
            JobAuditEmitter,
        )

        emitter = JobAuditEmitter()
        event = await emitter.emit_created(
            job_id=job_id,
            tenant_id=tenant_id,
            handler=handler,
            payload=payload,
        )
        return event.__dict__ if hasattr(event, "__dict__") else {"event": event}

    async def emit_audit_completed(
        self,
        job_id: str,
        tenant_id: str,
        duration_ms: int,
        result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Emit a job-completed audit event."""
        from app.hoc.cus.logs.L6_drivers.job_execution_driver import (
            JobAuditEmitter,
        )

        emitter = JobAuditEmitter()
        event = await emitter.emit_completed(
            job_id=job_id,
            tenant_id=tenant_id,
            duration_ms=duration_ms,
            result=result,
        )
        return event.__dict__ if hasattr(event, "__dict__") else {"event": event}

    async def emit_audit_failed(
        self,
        job_id: str,
        tenant_id: str,
        error: str,
        duration_ms: Optional[int] = None,
        attempt_number: int = 1,
    ) -> Dict[str, Any]:
        """Emit a job-failed audit event."""
        from app.hoc.cus.logs.L6_drivers.job_execution_driver import (
            JobAuditEmitter,
        )

        emitter = JobAuditEmitter()
        event = await emitter.emit_failed(
            job_id=job_id,
            tenant_id=tenant_id,
            error=error,
            duration_ms=duration_ms,
            attempt_number=attempt_number,
        )
        return event.__dict__ if hasattr(event, "__dict__") else {"event": event}
