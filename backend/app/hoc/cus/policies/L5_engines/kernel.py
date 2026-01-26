# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api | cli | worker | sdk | auto_execute
#   Execution: sync
# Lifecycle:
#   Emits: execution_envelope
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Mandatory execution kernel - single choke point for all EXECUTE power
# Callers: HTTP handlers, CLI dispatchers, SDK wrappers, workers, AUTO_EXECUTE
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-337

"""
ExecutionKernel - PIN-337 Governance Enforcement Infrastructure

This is the MANDATORY choke point for all EXECUTE-power paths.
All execution must flow through this kernel.

INVARIANTS:
- Every EXECUTE path MUST call ExecutionKernel.invoke()
- Kernel MUST NOT block execution in v1 (PERMISSIVE mode)
- Kernel MUST emit ExecutionEnvelope for attribution
- Kernel MUST record invocation metrics
- Unknown capability_id = CI FAIL (compile-time), not runtime block

The kernel is PHYSICS, not POLICY.
If code doesn't call the kernel, it doesn't execute.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# ENFORCEMENT MODE (CAPABILITY-SCOPED)
# =============================================================================


class EnforcementMode(str, Enum):
    """
    Enforcement mode for capability execution.

    PERMISSIVE: Log and allow (v1 default)
    STRICT: Enforce authority and policy (v2+, opt-in per capability)
    """

    PERMISSIVE = "permissive"
    STRICT = "strict"


# Capability-scoped enforcement configuration
# Default: ALL capabilities are PERMISSIVE in v1
_ENFORCEMENT_CONFIG: dict[str, EnforcementMode] = {
    # All capabilities default to PERMISSIVE
    # Strictness enabled per-capability via config, not code
}


def get_enforcement_mode(capability_id: str) -> EnforcementMode:
    """
    Get enforcement mode for a capability.

    Args:
        capability_id: The capability ID (e.g., "CAP-019")

    Returns:
        EnforcementMode for this capability (default: PERMISSIVE)
    """
    return _ENFORCEMENT_CONFIG.get(capability_id, EnforcementMode.PERMISSIVE)


def set_enforcement_mode(capability_id: str, mode: EnforcementMode) -> None:
    """
    Set enforcement mode for a capability.

    This is CONFIG-DRIVEN, not code-driven.
    Used for gradual rollout of strictness.

    Args:
        capability_id: The capability ID
        mode: The enforcement mode to set
    """
    _ENFORCEMENT_CONFIG[capability_id] = mode
    logger.info(
        "enforcement_mode_changed",
        extra={
            "capability_id": capability_id,
            "mode": mode.value,
        },
    )


# =============================================================================
# INVOCATION CONTEXT
# =============================================================================


@dataclass
class InvocationContext:
    """
    Context for an execution invocation.

    Captures WHO is invoking, WHAT they're invoking, and WHERE from.
    """

    # Identity
    subject: str  # Who is executing (user_id, service_id, "system")
    tenant_id: str  # Tenant isolation

    # Optional identity fields
    account_id: Optional[str] = None
    project_id: Optional[str] = None

    # Invocation metadata
    invocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Request context (for HTTP)
    request_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None

    # Additional context
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# EXECUTION RESULT
# =============================================================================


@dataclass
class ExecutionResult:
    """
    Result of an execution through the kernel.

    Wraps the actual result with governance metadata.
    """

    # Execution outcome
    success: bool
    result: Any = None
    error: Optional[Exception] = None

    # Governance metadata
    invocation_id: str = ""
    capability_id: str = ""
    execution_vector: str = ""
    enforcement_mode: EnforcementMode = EnforcementMode.PERMISSIVE

    # Timing
    started_at: str = ""
    completed_at: str = ""
    duration_ms: float = 0.0

    # Envelope
    envelope_emitted: bool = False
    envelope_id: Optional[str] = None


# =============================================================================
# EXECUTION KERNEL (MANDATORY CHOKE POINT)
# =============================================================================


class ExecutionKernel:
    """
    Mandatory execution kernel - single choke point for all EXECUTE power.

    All EXECUTE-power paths MUST route through this kernel:
    - HTTP handlers that mutate state
    - CLI commands that execute logic
    - SDK methods that trigger execution
    - Workers that process jobs
    - AUTO_EXECUTE recovery paths

    INVARIANTS:
    - v1: PERMISSIVE (log and allow, never block)
    - Envelope emission is ALWAYS on
    - Invocation recording is ALWAYS on
    - Strictness is capability-scoped, never global

    The kernel is PHYSICS, not POLICY.
    """

    # Enforcement config reference (for direct access)
    _ENFORCEMENT_CONFIG = _ENFORCEMENT_CONFIG

    # Known capability IDs (validated at CI time, not runtime)
    # This list is populated from CAPABILITY_REGISTRY_UNIFIED.yaml
    _KNOWN_CAPABILITIES: set[str] = {
        # FIRST_CLASS (CAP-001 to CAP-021)
        "CAP-001",
        "CAP-002",
        "CAP-003",
        "CAP-004",
        "CAP-005",
        "CAP-006",
        "CAP-007",
        "CAP-008",
        "CAP-009",
        "CAP-010",
        "CAP-011",
        "CAP-012",
        "CAP-013",
        "CAP-014",
        "CAP-015",
        "CAP-016",
        "CAP-017",
        "CAP-018",
        "CAP-019",
        "CAP-020",
        "CAP-021",
        # SUBSTRATE (SUB-001 to SUB-020)
        "SUB-001",
        "SUB-002",
        "SUB-003",
        "SUB-004",
        "SUB-005",
        "SUB-006",
        "SUB-007",
        "SUB-008",
        "SUB-009",
        "SUB-010",
        "SUB-011",
        "SUB-012",
        "SUB-013",
        "SUB-014",
        "SUB-015",
        "SUB-016",
        "SUB-017",
        "SUB-018",
        "SUB-019",
        "SUB-020",
    }

    @classmethod
    def invoke(
        cls,
        capability_id: str,
        execution_vector: str,
        context: InvocationContext,
        work: Callable[[], T],
        reason: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute work through the governance kernel.

        This is the SINGLE entry point for all EXECUTE-power paths.

        Args:
            capability_id: The capability being exercised (e.g., "CAP-019")
            execution_vector: Where the execution is coming from (HTTP, CLI, SDK, WORKER, AUTO_EXEC)
            context: The invocation context (who, what, where)
            work: The actual work to execute (callable)
            reason: Optional reason for the execution

        Returns:
            ExecutionResult with governance metadata

        INVARIANTS:
        - v1: NEVER blocks execution (PERMISSIVE)
        - ALWAYS emits envelope
        - ALWAYS records invocation
        """
        started_at = datetime.now(timezone.utc)
        enforcement_mode = get_enforcement_mode(capability_id)

        # Validate capability exists (soft validation in v1)
        if capability_id not in cls._KNOWN_CAPABILITIES:
            logger.warning(
                "unknown_capability_invoked",
                extra={
                    "capability_id": capability_id,
                    "execution_vector": execution_vector,
                    "invocation_id": context.invocation_id,
                    "subject": context.subject,
                    "tenant_id": context.tenant_id,
                    "enforcement_mode": enforcement_mode.value,
                    "action": "ALLOWED (v1 permissive)",
                },
            )
            # v1: Allow execution even for unknown capability
            # CI should catch this, not runtime

        # Emit execution envelope
        envelope_id = cls._emit_envelope(
            capability_id=capability_id,
            execution_vector=execution_vector,
            context=context,
            reason=reason,
        )

        # Record invocation start
        cls._record_invocation_start(
            capability_id=capability_id,
            execution_vector=execution_vector,
            context=context,
            enforcement_mode=enforcement_mode,
        )

        # Execute the work
        result: ExecutionResult
        try:
            work_result = work()
            completed_at = datetime.now(timezone.utc)
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            result = ExecutionResult(
                success=True,
                result=work_result,
                invocation_id=context.invocation_id,
                capability_id=capability_id,
                execution_vector=execution_vector,
                enforcement_mode=enforcement_mode,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_ms=duration_ms,
                envelope_emitted=True,
                envelope_id=envelope_id,
            )

            # Record success
            cls._record_invocation_complete(
                capability_id=capability_id,
                context=context,
                success=True,
                duration_ms=duration_ms,
            )

        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            result = ExecutionResult(
                success=False,
                error=e,
                invocation_id=context.invocation_id,
                capability_id=capability_id,
                execution_vector=execution_vector,
                enforcement_mode=enforcement_mode,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_ms=duration_ms,
                envelope_emitted=True,
                envelope_id=envelope_id,
            )

            # Record failure
            cls._record_invocation_complete(
                capability_id=capability_id,
                context=context,
                success=False,
                duration_ms=duration_ms,
                error=str(e),
            )

            # Re-raise the exception (kernel doesn't swallow errors)
            raise

        return result

    @classmethod
    async def invoke_async(
        cls,
        capability_id: str,
        execution_vector: str,
        context: InvocationContext,
        work: Callable[[], T],
        reason: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Async version of invoke for async execution paths.

        Same semantics as invoke(), but for async callables.
        """
        started_at = datetime.now(timezone.utc)
        enforcement_mode = get_enforcement_mode(capability_id)

        # Validate capability exists (soft validation in v1)
        if capability_id not in cls._KNOWN_CAPABILITIES:
            logger.warning(
                "unknown_capability_invoked",
                extra={
                    "capability_id": capability_id,
                    "execution_vector": execution_vector,
                    "invocation_id": context.invocation_id,
                    "subject": context.subject,
                    "tenant_id": context.tenant_id,
                    "enforcement_mode": enforcement_mode.value,
                    "action": "ALLOWED (v1 permissive)",
                },
            )

        # Emit execution envelope
        envelope_id = cls._emit_envelope(
            capability_id=capability_id,
            execution_vector=execution_vector,
            context=context,
            reason=reason,
        )

        # Record invocation start
        cls._record_invocation_start(
            capability_id=capability_id,
            execution_vector=execution_vector,
            context=context,
            enforcement_mode=enforcement_mode,
        )

        # Execute the work
        result: ExecutionResult
        try:
            # Handle both sync and async callables
            work_result = work()
            if hasattr(work_result, "__await__"):
                work_result = await work_result

            completed_at = datetime.now(timezone.utc)
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            result = ExecutionResult(
                success=True,
                result=work_result,
                invocation_id=context.invocation_id,
                capability_id=capability_id,
                execution_vector=execution_vector,
                enforcement_mode=enforcement_mode,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_ms=duration_ms,
                envelope_emitted=True,
                envelope_id=envelope_id,
            )

            cls._record_invocation_complete(
                capability_id=capability_id,
                context=context,
                success=True,
                duration_ms=duration_ms,
            )

        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            result = ExecutionResult(
                success=False,
                error=e,
                invocation_id=context.invocation_id,
                capability_id=capability_id,
                execution_vector=execution_vector,
                enforcement_mode=enforcement_mode,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_ms=duration_ms,
                envelope_emitted=True,
                envelope_id=envelope_id,
            )

            cls._record_invocation_complete(
                capability_id=capability_id,
                context=context,
                success=False,
                duration_ms=duration_ms,
                error=str(e),
            )

            raise

        return result

    @classmethod
    def _emit_envelope(
        cls,
        capability_id: str,
        execution_vector: str,
        context: InvocationContext,
        reason: Optional[str] = None,
    ) -> str:
        """
        Emit execution envelope for attribution.

        INVARIANT: Envelope emission failure MUST NOT block execution.
        """
        try:
            from app.auth.execution_envelope import (
                CapabilityId,
                ExecutionEnvelopeFactory,
                emit_envelope,
            )
            from app.auth.execution_envelope import (
                ExecutionVector as EnvVector,
            )

            # Map capability_id to CapabilityId enum if known
            cap_enum = None
            for cap in CapabilityId:
                if cap.value == capability_id:
                    cap_enum = cap
                    break

            # Map execution_vector to ExecutionVector enum
            vec_map = {
                "HTTP": EnvVector.HTTP_ADMIN,
                "HTTP_ADMIN": EnvVector.HTTP_ADMIN,
                "CLI": EnvVector.CLI,
                "SDK": EnvVector.SDK,
                "WORKER": EnvVector.AUTO_EXEC,
                "AUTO_EXEC": EnvVector.AUTO_EXEC,
            }

            # Create and emit envelope
            if capability_id.startswith("CAP-019"):
                envelope = ExecutionEnvelopeFactory.create_admin_envelope(
                    subject=context.subject,
                    tenant_id=context.tenant_id,
                    route=f"kernel:{capability_id}",
                    raw_input={"invocation_id": context.invocation_id},
                    resolved_plan={"capability_id": capability_id, "vector": execution_vector},
                    reason_code=reason,
                    account_id=context.account_id,
                    project_id=context.project_id,
                )
                emit_envelope(envelope)
                return envelope.envelope_id

            # For other capabilities, log the invocation
            envelope_id = str(uuid.uuid4())
            logger.info(
                "execution_envelope_emitted",
                extra={
                    "envelope_id": envelope_id,
                    "capability_id": capability_id,
                    "execution_vector": execution_vector,
                    "invocation_id": context.invocation_id,
                    "subject": context.subject,
                    "tenant_id": context.tenant_id,
                    "reason": reason,
                },
            )
            return envelope_id

        except Exception as e:
            # CRITICAL: Never block execution due to envelope failure
            logger.error(
                "envelope_emission_failed",
                extra={
                    "capability_id": capability_id,
                    "invocation_id": context.invocation_id,
                    "error": str(e),
                    "action": "CONTINUED (non-blocking)",
                },
            )
            return f"failed-{uuid.uuid4()}"

    @classmethod
    def _record_invocation_start(
        cls,
        capability_id: str,
        execution_vector: str,
        context: InvocationContext,
        enforcement_mode: EnforcementMode,
    ) -> None:
        """Record invocation start for metrics and audit."""
        logger.info(
            "kernel_invocation_started",
            extra={
                "capability_id": capability_id,
                "execution_vector": execution_vector,
                "invocation_id": context.invocation_id,
                "subject": context.subject,
                "tenant_id": context.tenant_id,
                "enforcement_mode": enforcement_mode.value,
            },
        )

    @classmethod
    def _record_invocation_complete(
        cls,
        capability_id: str,
        context: InvocationContext,
        success: bool,
        duration_ms: float,
        error: Optional[str] = None,
    ) -> None:
        """Record invocation completion for metrics and audit."""
        logger.info(
            "kernel_invocation_completed",
            extra={
                "capability_id": capability_id,
                "invocation_id": context.invocation_id,
                "success": success,
                "duration_ms": duration_ms,
                "error": error,
            },
        )

    @classmethod
    def is_known_capability(cls, capability_id: str) -> bool:
        """Check if a capability ID is known to the kernel."""
        return capability_id in cls._KNOWN_CAPABILITIES

    @classmethod
    def get_known_capabilities(cls) -> set[str]:
        """Get the set of known capability IDs."""
        return cls._KNOWN_CAPABILITIES.copy()
