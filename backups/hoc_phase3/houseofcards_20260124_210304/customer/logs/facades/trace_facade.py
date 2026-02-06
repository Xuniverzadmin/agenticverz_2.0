# Layer: L3 — Adapter
# AUDIENCE: CUSTOMER
# Role: Trace Domain Facade - Centralized access to trace operations with RAC acks
# Product: system-wide
# Temporal:
#   Trigger: worker (run execution)
#   Execution: async
# Callers: L5 runner/observability guard (via dependency injection), API routes
# Allowed Imports: L4 audit, L6 (trace store, db)
# Forbidden Imports: L1, L2, L3
# Reference: PIN-454 (Cross-Domain Orchestration Audit)


"""
Trace Domain Facade (L4 Domain Logic)

This facade provides the external interface to the Trace domain.
It wraps TraceStore operations and emits RAC acknowledgments.

Why This Facade Exists (PIN-454):
- Centralized RAC acknowledgment emission for trace operations
- Clean interface between L5 execution and L6 platform
- Domain encapsulation for trace operations

RAC Integration:
- Emits START_TRACE ack after trace creation
- Emits COMPLETE_TRACE ack after trace completion

Usage:
    from app.services.observability.trace_facade import get_trace_facade

    facade = get_trace_facade()
    trace_id = await facade.start_trace(run_id, tenant_id, agent_id)
"""

import logging
import os
from typing import Optional
from uuid import UUID

logger = logging.getLogger("nova.services.observability.trace_facade")

# RAC integration flag (PIN-454)
RAC_ENABLED = os.getenv("RAC_ENABLED", "true").lower() == "true"


class TraceFacade:
    """
    Facade for trace domain operations.

    Wraps TraceStore (L6) operations and emits RAC acknowledgments.

    Layer: L4 (Domain Logic)
    Callers: RunRunner (L5), ObservabilityGuard (L5)
    """

    def __init__(self, trace_store=None):
        """
        Initialize facade with optional trace store.

        Args:
            trace_store: Optional trace store instance. If not provided,
                        will be lazy-loaded from L6.
        """
        self._trace_store = trace_store

    @property
    def _store(self):
        """Lazy-load trace store."""
        if self._trace_store is None:
            from app.telemetry.trace_store import PostgresTraceStore
            self._trace_store = PostgresTraceStore()
        return self._trace_store

    # =========================================================================
    # Trace Lifecycle Operations
    # =========================================================================

    async def start_trace(
        self,
        run_id: str,
        tenant_id: str,
        agent_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Start a trace for a run.

        PIN-454: Emits RAC acknowledgment after trace creation.

        Args:
            run_id: ID of the run
            tenant_id: Tenant scope
            agent_id: Optional agent ID

        Returns:
            trace_id if created, None if failed
        """
        logger.debug(
            "trace_facade.start_trace",
            extra={"run_id": run_id, "tenant_id": tenant_id}
        )

        trace_id = None
        error = None

        try:
            trace_id = await self._store.start_trace(
                run_id=run_id,
                tenant_id=tenant_id,
                agent_id=agent_id,
            )
        except Exception as e:
            error = str(e)
            logger.error(
                "trace_facade.start_trace failed",
                extra={"run_id": run_id, "error": error}
            )

        # PIN-454: Emit RAC acknowledgment
        if RAC_ENABLED:
            self._emit_ack(
                run_id=run_id,
                action="start_trace",
                result_id=trace_id,
                error=error,
            )

        return trace_id

    async def complete_trace(
        self,
        trace_id: str,
        run_id: str,
        status: str,
    ) -> bool:
        """
        Complete a trace.

        PIN-454: Emits RAC acknowledgment after trace completion.

        Args:
            trace_id: ID of the trace
            run_id: ID of the run (for RAC ack)
            status: Final status of the trace

        Returns:
            True if completed successfully, False otherwise
        """
        logger.debug(
            "trace_facade.complete_trace",
            extra={"trace_id": trace_id, "status": status}
        )

        success = False
        error = None

        try:
            await self._store.complete_trace(
                trace_id=trace_id,
                status=status,
            )
            success = True
        except Exception as e:
            error = str(e)
            logger.error(
                "trace_facade.complete_trace failed",
                extra={"trace_id": trace_id, "error": error}
            )

        # PIN-454: Emit RAC acknowledgment
        if RAC_ENABLED:
            self._emit_ack(
                run_id=run_id,
                action="complete_trace",
                result_id=trace_id if success else None,
                error=error,
            )

        return success

    async def add_step(
        self,
        trace_id: str,
        step_type: str,
        data: dict,
    ) -> bool:
        """
        Add a step to a trace.

        This is best-effort and does not emit RAC acks (steps are
        not critical for audit reconciliation).

        Args:
            trace_id: ID of the trace
            step_type: Type of step
            data: Step data

        Returns:
            True if step was added, False otherwise
        """
        try:
            await self._store.add_step(
                trace_id=trace_id,
                step_type=step_type,
                **data,
            )
            return True
        except Exception as e:
            logger.warning(
                f"trace_facade.add_step failed: {e}",
                extra={"trace_id": trace_id}
            )
            return False

    # =========================================================================
    # RAC Acknowledgment
    # =========================================================================

    def _emit_ack(
        self,
        run_id: str,
        action: str,
        result_id: Optional[str],
        error: Optional[str],
    ) -> None:
        """
        Emit RAC acknowledgment for trace operations.

        PIN-454: Facades emit acks after domain operations.
        """
        try:
            from app.services.audit.models import AuditAction, AuditDomain, DomainAck
            from app.services.audit.store import get_audit_store

            # Map action string to enum
            action_enum = {
                "start_trace": AuditAction.START_TRACE,
                "complete_trace": AuditAction.COMPLETE_TRACE,
            }.get(action)

            if action_enum is None:
                logger.warning(f"Unknown trace action for RAC: {action}")
                return

            ack = DomainAck(
                run_id=UUID(run_id),
                domain=AuditDomain.LOGS,
                action=action_enum,
                result_id=result_id,
                error=error,
            )

            store = get_audit_store()
            store.add_ack(UUID(run_id), ack)

            logger.debug(
                "trace_facade.emit_ack",
                extra={
                    "run_id": run_id,
                    "domain": "logs",
                    "action": action,
                    "success": error is None,
                }
            )
        except Exception as e:
            # RAC failures should not block the facade
            logger.warning(f"Failed to emit RAC ack: {e}")


# =============================================================================
# Module-level singleton
# =============================================================================

_facade_instance: Optional[TraceFacade] = None


def get_trace_facade(trace_store=None) -> TraceFacade:
    """
    Get the trace facade singleton.

    Args:
        trace_store: Optional trace store (only used on first call)

    Returns:
        TraceFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = TraceFacade(trace_store=trace_store)
    return _facade_instance
