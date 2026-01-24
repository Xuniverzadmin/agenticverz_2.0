# Layer: L5 — Execution & Workers
# AUDIENCE: INTERNAL
# PHASE: W0
# Product: system-wide
# Wiring Type: runner-hook
# Parent Gap: GAP-065 (RetrievalMediator)
# Reference: GAP-137
# Temporal:
#   Trigger: worker (step execution)
#   Execution: async
# Role: Wire RetrievalMediator as MANDATORY in LLM path
# Callers: app/worker/runner.py (step execution)
# Allowed Imports: L4 (RetrievalMediator), L6
# Forbidden Imports: L1, L2, L3

"""
Module: retrieval_hook
Purpose: Wire RetrievalMediator as MANDATORY in LLM execution path.

Wires:
    - Source: app/services/mediation/retrieval_mediator.py
    - Target: app/worker/runner.py (step execution)

Invariant: NO BYPASS ALLOWED
    - All external data retrieval MUST go through mediator
    - Direct connector access from runner is FORBIDDEN
    - Audit trail for every retrieval operation

This hook enforces:
    1. All data retrievals in step execution go through RetrievalMediator
    2. Policy checks happen before any data access
    3. Evidence is captured for audit

Acceptance Criteria:
    - AC-137-01: All retrievals go through mediator
    - AC-137-02: Direct connector access blocked
    - AC-137-03: Audit evidence emitted
    - AC-137-04: Policy blocks propagate to step
    - AC-137-05: Hook is imported in runner.py
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.mediation.retrieval_mediator import (
    MediatedResult,
    MediationDeniedError,
    RetrievalMediator,
    get_retrieval_mediator,
)
from app.core.execution_context import ExecutionContext

logger = logging.getLogger("nova.worker.hooks.retrieval_hook")


@dataclass
class RetrievalRequest:
    """
    Request for data retrieval in step execution.

    This is the standardized format for retrieval requests
    that the runner uses when a step needs external data.
    """

    plane_id: str  # Knowledge plane to access (e.g., "documents", "database")
    action: str  # Action to perform (query, retrieve, search, list)
    payload: Dict[str, Any]  # Action-specific payload
    tenant_id: str  # Tenant context
    run_id: str  # Run context
    step_index: int = 0  # Step index in the plan
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional context

    def __post_init__(self):
        """Validate request structure."""
        if not self.plane_id:
            raise ValueError("RetrievalRequest requires plane_id")
        if not self.action:
            raise ValueError("RetrievalRequest requires action")
        if not self.tenant_id:
            raise ValueError("RetrievalRequest requires tenant_id")
        if not self.run_id:
            raise ValueError("RetrievalRequest requires run_id")


@dataclass
class RetrievalResponse:
    """
    Response from a mediated retrieval.

    Contains both the data and audit information.
    """

    success: bool
    data: Any = None
    evidence_id: Optional[str] = None
    tokens_consumed: int = 0

    # Blocking information (if blocked)
    blocked: bool = False
    blocked_reason: Optional[str] = None
    blocking_policy_id: Optional[str] = None

    # Timing
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_mediated_result(cls, result: MediatedResult) -> "RetrievalResponse":
        """Create response from MediatedResult."""
        return cls(
            success=result.success,
            data=result.data,
            evidence_id=result.evidence_id,
            tokens_consumed=result.tokens_consumed,
            timestamp=result.timestamp,
        )

    @classmethod
    def blocked_response(
        cls,
        reason: str,
        policy_id: Optional[str] = None,
    ) -> "RetrievalResponse":
        """Create a blocked response."""
        return cls(
            success=False,
            blocked=True,
            blocked_reason=reason,
            blocking_policy_id=policy_id,
        )


class RetrievalHook:
    """
    Runner hook that enforces retrieval mediation.

    INVARIANT: Jobs MUST NOT access external data directly.

    This hook intercepts all data retrieval requests in the runner
    and routes them through the RetrievalMediator. Direct connector
    access from the runner is a governance violation.

    Usage in runner:
        hook = get_retrieval_hook()

        # For steps requiring retrieval
        if step.requires_retrieval:
            response = await hook.before_retrieval(
                execution_context=cursor.context,
                request=step.retrieval_request,
            )

            if not response.success:
                return StepResult.blocked(
                    reason="retrieval_blocked",
                    details=response.blocked_reason,
                )

            step.retrieval_data = response.data
    """

    def __init__(self, mediator: Optional[RetrievalMediator] = None):
        """
        Initialize RetrievalHook.

        Args:
            mediator: RetrievalMediator instance (uses singleton if None)
        """
        self._mediator = mediator

    @property
    def mediator(self) -> RetrievalMediator:
        """Get mediator (lazy initialization)."""
        if self._mediator is None:
            self._mediator = get_retrieval_mediator()
        return self._mediator

    async def before_retrieval(
        self,
        request: RetrievalRequest,
        execution_context: Optional[ExecutionContext] = None,
    ) -> RetrievalResponse:
        """
        Intercept retrieval request and route through mediator.

        INVARIANT: This method MUST be called for ALL retrievals.
        Direct connector access is a governance violation.

        Args:
            request: The retrieval request
            execution_context: Optional execution context for additional metadata

        Returns:
            RetrievalResponse with data or block information
        """
        # Enrich metadata from execution context if available
        if execution_context:
            request.metadata.update({
                "trace_id": execution_context.trace_id,
                "step_index": execution_context.step_index,
                "is_synthetic": execution_context.is_synthetic,
                "actor_id": execution_context.actor_id,
                "policy_snapshot_id": execution_context.policy_snapshot_id,
            })

        logger.debug(
            "retrieval_hook.before_retrieval",
            extra={
                "run_id": request.run_id,
                "step_index": request.step_index,
                "plane_id": request.plane_id,
                "action": request.action,
            },
        )

        try:
            # Route through mediator (policy checks, audit, etc.)
            result = await self.mediator.access(
                tenant_id=request.tenant_id,
                run_id=request.run_id,
                plane_id=request.plane_id,
                action=request.action,
                payload=request.payload,
                requesting_tenant_id=request.tenant_id,  # Same tenant
            )

            logger.info(
                "retrieval_hook.success",
                extra={
                    "run_id": request.run_id,
                    "step_index": request.step_index,
                    "plane_id": request.plane_id,
                    "evidence_id": result.evidence_id,
                    "tokens": result.tokens_consumed,
                },
            )

            return RetrievalResponse.from_mediated_result(result)

        except MediationDeniedError as e:
            # Access was denied by policy
            logger.warning(
                "retrieval_hook.denied",
                extra={
                    "run_id": request.run_id,
                    "step_index": request.step_index,
                    "plane_id": request.plane_id,
                    "reason": e.reason,
                    "policy_id": e.policy_id,
                },
            )

            return RetrievalResponse.blocked_response(
                reason=e.reason,
                policy_id=e.policy_id,
            )

        except Exception as e:
            # Unexpected error - fail-safe, block the retrieval
            logger.error(
                "retrieval_hook.error",
                extra={
                    "run_id": request.run_id,
                    "step_index": request.step_index,
                    "plane_id": request.plane_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            # Fail-closed: unexpected errors block retrieval
            return RetrievalResponse.blocked_response(
                reason=f"Unexpected error: {type(e).__name__}: {str(e)[:200]}",
            )

    async def validate_no_direct_access(
        self,
        step_params: Dict[str, Any],
        run_id: str,
    ) -> bool:
        """
        Validate that step parameters don't contain direct connector references.

        INVARIANT: Direct connector access is FORBIDDEN.

        This method checks step parameters for patterns that indicate
        direct connector access bypassing the mediator.

        Args:
            step_params: The step parameters to validate
            run_id: Run ID for logging

        Returns:
            True if valid (no direct access), False if violation detected
        """
        # Patterns that indicate direct connector access
        forbidden_patterns = [
            "connector_url",
            "direct_connector",
            "bypass_mediator",
            "raw_connection",
        ]

        for pattern in forbidden_patterns:
            if pattern in step_params:
                logger.critical(
                    "retrieval_hook.direct_access_violation",
                    extra={
                        "run_id": run_id,
                        "pattern": pattern,
                        "violation": "Direct connector access is FORBIDDEN",
                    },
                )
                return False

        return True


# =========================
# Singleton Management
# =========================

_retrieval_hook: Optional[RetrievalHook] = None


def get_retrieval_hook() -> RetrievalHook:
    """
    Get or create the singleton RetrievalHook.

    Returns:
        RetrievalHook instance
    """
    global _retrieval_hook

    if _retrieval_hook is None:
        _retrieval_hook = RetrievalHook()
        logger.info("retrieval_hook.created")

    return _retrieval_hook


def configure_retrieval_hook(
    mediator: Optional[RetrievalMediator] = None,
) -> RetrievalHook:
    """
    Configure the singleton RetrievalHook with dependencies.

    Args:
        mediator: RetrievalMediator instance to use

    Returns:
        Configured RetrievalHook
    """
    global _retrieval_hook

    _retrieval_hook = RetrievalHook(mediator=mediator)

    logger.info(
        "retrieval_hook.configured",
        extra={"has_mediator": mediator is not None},
    )

    return _retrieval_hook


def reset_retrieval_hook() -> None:
    """Reset the singleton (for testing)."""
    global _retrieval_hook
    _retrieval_hook = None
