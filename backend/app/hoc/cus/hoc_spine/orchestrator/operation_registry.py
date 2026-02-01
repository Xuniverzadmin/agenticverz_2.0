# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request)
#   Execution: async
# Lifecycle:
#   Emits: operation audit records
#   Subscribes: none
# Data Access:
#   Reads: via L5 handlers → L6 drivers
#   Writes: via L5 handlers → L6 drivers
# Role: Operation dispatch registry — maps domain operations to L5 handlers via L4 orchestrator
# Callers: L2 APIs (hoc/api/cus/{domain}/*.py)
# Allowed Imports: hoc_spine (authority, services, schemas)
# Forbidden Imports: L1, L2, L5, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), L2-L4-L5_CONSTRUCTION_PLAN.md
# Tests: backend/app/hoc/cus/hoc_spine/tests/test_operation_registry.py (16 invariants: REG-001–REG-008)
# Literature: literature/hoc_spine/orchestrator/operation_registry.md
# artifact_class: CODE

"""
Operation Registry (L4 Orchestrator)

Central dispatch layer for domain operations. L2 APIs call this instead of
importing L5 engines directly.

Flow:
    L2 HTTP → OperationRegistry.execute(op_name, ctx) → L5 handler → L6 driver

What the registry adds to every operation:
    1. Authority check (is governance active? degraded mode?)
    2. Audit record (who called what, when, outcome)
    3. Consistent error handling (L5 exceptions → OperationResult)
    4. Single dispatch point (operation name → handler lookup)

What the registry does NOT do:
    - Own transactions (the session comes from L2 via FastAPI DI)
    - Execute business logic (that stays in L5)
    - Make decisions (authority is checked, not created here)

Usage:
    # L2 API file (e.g., hoc/api/cus/overview/overview.py)
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
        get_operation_registry,
        OperationContext,
    )

    registry = get_operation_registry()
    result = await registry.execute("overview.query", OperationContext(
        session=session,
        tenant_id=tenant_id,
        params={"endpoint": "highlights"},
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return result.data

Handler registration:
    # In hoc_spine/orchestrator/handlers/{domain}_handler.py
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
        OperationHandler,
        OperationContext,
        OperationResult,
    )

    class OverviewQueryHandler(OperationHandler):
        async def execute(self, ctx: OperationContext) -> OperationResult:
            from app.hoc.cus.overview.L5_engines.overview_facade import get_overview_facade
            facade = get_overview_facade()
            data = await facade.get_highlights(session=ctx.session, tenant_id=ctx.tenant_id)
            return OperationResult.ok(data)

    # Registration (called once at startup)
    registry = get_operation_registry()
    registry.register("overview.query", OverviewQueryHandler())
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from app.hoc.cus.hoc_spine.services.time import utc_now

logger = logging.getLogger("nova.hoc_spine.orchestrator.operation_registry")

# Registry version — bump on structural changes
REGISTRY_VERSION = "1.0.0"


# =============================================================================
# DATA CONTRACTS
# =============================================================================


@dataclass(frozen=True)
class OperationContext:
    """
    Immutable context passed to every operation handler.

    The session comes from L2 via FastAPI DI. The registry does NOT
    create sessions or own transaction boundaries.
    """

    session: AsyncSession
    tenant_id: str
    params: dict[str, Any] = field(default_factory=dict)
    # Caller metadata (populated by registry, not by L2)
    operation: str = ""
    timestamp: str = ""


@dataclass
class OperationResult:
    """
    Outcome of an operation dispatch.

    L2 code inspects .success and either uses .data or raises
    based on .error / .error_code.
    """

    success: bool
    data: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    # Audit metadata (populated by registry)
    operation: str = ""
    duration_ms: float = 0.0

    @staticmethod
    def ok(data: Any = None) -> "OperationResult":
        """Create a successful result."""
        return OperationResult(success=True, data=data)

    @staticmethod
    def fail(error: str, error_code: str = "OPERATION_FAILED") -> "OperationResult":
        """Create a failed result."""
        return OperationResult(success=False, error=error, error_code=error_code)


# =============================================================================
# HANDLER PROTOCOL
# =============================================================================


@runtime_checkable
class OperationHandler(Protocol):
    """
    Protocol for domain operation handlers.

    Each handler wraps ONE L5 facade call. The handler:
      - Receives an OperationContext (session, tenant, params)
      - Calls the L5 facade
      - Returns an OperationResult

    The handler MUST NOT:
      - Import from L2
      - Create sessions
      - Call session.commit() (transaction ownership stays with caller)
      - Call other domain handlers directly (use registry for cross-domain)
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        """Execute the domain operation."""
        ...


# =============================================================================
# OPERATION REGISTRY
# =============================================================================


class OperationRegistry:
    """
    Central dispatch for domain operations.

    Maps operation name strings (e.g., "policies.query") to OperationHandler
    instances. L2 APIs call execute() instead of importing L5 directly.

    Authority Gate:
        Before dispatching, checks governance runtime state.
        If governance is disabled (kill switch), operations still execute
        but are tagged as unguarded in audit.
        If degraded mode is active, a warning is logged.

    Audit:
        Every dispatch logs: operation name, tenant, duration, outcome.
        Structured logging — no external audit store dependency in v1.
        AuditStore integration deferred to Phase A.6.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, OperationHandler] = {}
        self._frozen: bool = False

    # =========================================================================
    # Registration
    # =========================================================================

    def register(self, operation: str, handler: OperationHandler) -> None:
        """
        Register a handler for an operation name.

        Args:
            operation: Dot-separated name, e.g. "policies.query"
            handler: OperationHandler implementation

        Raises:
            RuntimeError: If registry is frozen or operation already registered
        """
        if self._frozen:
            raise RuntimeError(
                f"Cannot register '{operation}': registry is frozen. "
                "Registration must happen at import time, not at request time."
            )

        if operation in self._handlers:
            raise RuntimeError(
                f"Operation '{operation}' already registered. "
                "Duplicate registration indicates a wiring bug."
            )

        # Runtime check: handler must have async execute(ctx) method
        if not callable(getattr(handler, "execute", None)):
            raise TypeError(
                f"Handler for '{operation}' does not satisfy OperationHandler protocol "
                f"(missing execute method). Got: {type(handler).__name__}"
            )

        self._handlers[operation] = handler
        logger.info(
            "operation.registered",
            extra={"operation": operation, "handler": type(handler).__name__},
        )

    def freeze(self) -> None:
        """
        Freeze the registry. No further registrations allowed.

        Call this after all handlers are registered (e.g., at startup).
        Prevents accidental runtime registration.
        """
        self._frozen = True
        logger.info(
            "registry.frozen",
            extra={"operation_count": len(self._handlers)},
        )

    # =========================================================================
    # Dispatch
    # =========================================================================

    async def execute(
        self,
        operation: str,
        ctx: OperationContext,
    ) -> OperationResult:
        """
        Dispatch an operation to its registered handler.

        Args:
            operation: Operation name, e.g. "policies.query"
            ctx: Execution context (session, tenant, params)

        Returns:
            OperationResult with success/failure and data/error
        """
        start = time.monotonic()

        # --- Pre-dispatch: authority check ---
        governance_active = self._check_authority(operation)

        # --- Lookup handler ---
        handler = self._handlers.get(operation)
        if handler is None:
            result = OperationResult.fail(
                error=f"No handler registered for operation: {operation}",
                error_code="UNKNOWN_OPERATION",
            )
            self._audit_dispatch(operation, ctx, result, 0.0, governance_active)
            return result

        # --- Build enriched context ---
        enriched_ctx = OperationContext(
            session=ctx.session,
            tenant_id=ctx.tenant_id,
            params=ctx.params,
            operation=operation,
            timestamp=utc_now().isoformat(),
        )

        # --- Execute handler ---
        try:
            result = await handler.execute(enriched_ctx)
        except Exception as exc:
            logger.error(
                "operation.handler_exception",
                extra={
                    "operation": operation,
                    "tenant_id": ctx.tenant_id,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
                exc_info=True,
            )
            result = OperationResult.fail(
                error=str(exc),
                error_code=f"HANDLER_EXCEPTION:{type(exc).__name__}",
            )

        # --- Post-dispatch: audit ---
        duration_ms = (time.monotonic() - start) * 1000
        result.operation = operation
        result.duration_ms = duration_ms
        self._audit_dispatch(operation, ctx, result, duration_ms, governance_active)

        return result

    # =========================================================================
    # Authority
    # =========================================================================

    def _check_authority(self, operation: str) -> bool:
        """
        Check governance runtime state before dispatch.

        Returns True if governance is active, False if kill-switched.
        Operations execute either way — authority state is recorded, not enforced
        as a gate on domain operations (kill switch affects governance workflow,
        not domain reads/writes).
        """
        try:
            from app.hoc.cus.hoc_spine.authority.runtime_switch import (
                is_degraded_mode,
                is_governance_active,
            )

            active = is_governance_active()
            degraded = is_degraded_mode()

            if not active:
                logger.warning(
                    "operation.governance_disabled",
                    extra={"operation": operation},
                )
            if degraded:
                logger.warning(
                    "operation.degraded_mode",
                    extra={"operation": operation},
                )

            return active
        except Exception as exc:
            # Authority check failure must not block operations
            logger.error(
                "operation.authority_check_failed",
                extra={"operation": operation, "error": str(exc)},
            )
            return False

    # =========================================================================
    # Audit
    # =========================================================================

    def _audit_dispatch(
        self,
        operation: str,
        ctx: OperationContext,
        result: OperationResult,
        duration_ms: float,
        governance_active: bool,
    ) -> None:
        """
        Emit structured audit log for every dispatch.

        V1: structured logging only. AuditStore integration planned for Phase A.6.
        """
        log_data = {
            "operation": operation,
            "tenant_id": ctx.tenant_id,
            "success": result.success,
            "duration_ms": round(duration_ms, 2),
            "governance_active": governance_active,
        }

        if not result.success:
            log_data["error"] = result.error
            log_data["error_code"] = result.error_code

        if result.success:
            logger.info("operation.dispatched", extra=log_data)
        else:
            logger.warning("operation.failed", extra=log_data)

    # =========================================================================
    # Introspection
    # =========================================================================

    @property
    def operations(self) -> list[str]:
        """Return sorted list of registered operation names."""
        return sorted(self._handlers.keys())

    @property
    def operation_count(self) -> int:
        """Return count of registered operations."""
        return len(self._handlers)

    @property
    def is_frozen(self) -> bool:
        """Return whether the registry is frozen."""
        return self._frozen

    def has_operation(self, operation: str) -> bool:
        """Check if an operation is registered."""
        return operation in self._handlers

    def get_handler(self, operation: str) -> Optional[OperationHandler]:
        """Get the handler for an operation (for testing/introspection)."""
        return self._handlers.get(operation)

    def status(self) -> dict[str, Any]:
        """Return registry status for health/diagnostics endpoints."""
        return {
            "version": REGISTRY_VERSION,
            "operation_count": len(self._handlers),
            "frozen": self._frozen,
            "operations": self.operations,
        }


# =============================================================================
# MODULE SINGLETON
# =============================================================================

_registry_instance: Optional[OperationRegistry] = None


def get_operation_registry() -> OperationRegistry:
    """
    Get the operation registry singleton.

    Returns the same instance for the lifetime of the process.
    Handlers register against this instance at import time.
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = OperationRegistry()
    return _registry_instance


def reset_operation_registry() -> None:
    """
    Reset the registry singleton. FOR TESTING ONLY.

    Production code must never call this.
    """
    global _registry_instance
    _registry_instance = None
