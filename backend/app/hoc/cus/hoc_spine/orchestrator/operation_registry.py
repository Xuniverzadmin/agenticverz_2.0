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
    - Execute business logic (that stays in L5)
    - Make decisions (authority is checked, not created here)

Transaction ownership (PIN-520, TRANSACTION_COORDINATION_RATIONALE.md):
    - L4 handlers OWN transaction boundaries (commit/rollback)
    - L5 engines may call session.add(), session.flush()
    - L6 drivers may call session.add(), session.execute() - NEVER commit
    - Session comes from L2 via FastAPI DI, but L4 decides when to commit

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
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncGenerator, Generator, Optional, Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.hoc.cus.hoc_spine.schemas.authority_decision import AuthorityDecision

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

    The session comes from L2 via FastAPI DI. L4 handlers own transaction
    boundaries (commit/rollback).

    Session patterns:
        - Async operations: session is AsyncSession (ctx.session)
        - Sync operations: session=None, pass sync session via params["sync_session"]
        - Self-contained: session=None, L4 handler creates session internally

    Note: sync_session smuggling via params is the accepted pattern until
    we refactor to explicit dual-session fields (future work).
    """

    session: Optional[AsyncSession]  # None for sync or self-contained operations
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
      - Call other domain handlers directly (use registry for cross-domain)

    Transaction ownership (PIN-520):
      - L4 handlers/coordinators own transaction boundaries for write operations.
      - L5 engines may call session.add(), session.flush().
      - L6 drivers may call session.add(), session.execute() — NEVER commit/rollback.
      - Read-only operations should not commit/rollback.
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

    Audit & Consequences:
        Every dispatch logs: operation name, tenant, duration, outcome.
        V3: Structured logging + AuditStore persistence + Consequences pipeline.
        Dispatch records and consequences are post-commit only (Constitution §2.3).
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

        # --- Pre-dispatch: authority check (ITER3.4 — unified AuthorityDecision) ---
        authority_decision = self._check_authority(operation)

        # --- Lookup handler ---
        handler = self._handlers.get(operation)
        if handler is None:
            result = OperationResult.fail(
                error=f"No handler registered for operation: {operation}",
                error_code="UNKNOWN_OPERATION",
            )
            self._audit_dispatch(operation, ctx, result, 0.0, authority_decision)
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
        self._audit_dispatch(operation, ctx, result, duration_ms, authority_decision)

        return result

    # =========================================================================
    # Authority
    # =========================================================================

    def _check_authority(self, operation: str) -> "AuthorityDecision":
        """
        Check governance runtime state before dispatch (ITER3.4 unified).

        Returns AuthorityDecision with allow/deny/degraded state.
        Operations execute either way — authority state is recorded, not enforced
        as a gate on domain operations (kill switch affects governance workflow,
        not domain reads/writes).

        ITER3.4: Returns AuthorityDecision for uniform authority handling
        across all L4 checks. The decision is included in audit logs.
        """
        from app.hoc.cus.hoc_spine.schemas.authority_decision import AuthorityDecision

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
                return AuthorityDecision.allow_with_degraded_flag(
                    reason="Governance kill-switch active",
                    conditions=("governance_disabled",),
                )

            if degraded:
                logger.warning(
                    "operation.degraded_mode",
                    extra={"operation": operation},
                )
                return AuthorityDecision.allow_with_degraded_flag(
                    reason="System in degraded mode",
                    conditions=("degraded_mode",),
                )

            return AuthorityDecision.allow(
                reason="Governance active",
                conditions=("governance_active",),
            )

        except Exception as exc:
            # Authority check failure must not block operations
            logger.error(
                "operation.authority_check_failed",
                extra={"operation": operation, "error": str(exc)},
            )
            return AuthorityDecision.allow_with_degraded_flag(
                reason=f"Authority check failed: {exc}",
                conditions=("authority_check_error",),
            )

    # =========================================================================
    # Audit
    # =========================================================================

    def _audit_dispatch(
        self,
        operation: str,
        ctx: OperationContext,
        result: OperationResult,
        duration_ms: float,
        authority_decision: Any,  # AuthorityDecision (avoid import cycle)
    ) -> None:
        """
        Emit structured audit log, persist dispatch record, and run consequences.

        V3: Structured logging + AuditStore persistence + Consequences pipeline.
        Post-commit only — dispatch recording and consequences never participate
        in the operation's transaction (Constitution §2.3).

        ITER3.4: authority_decision is now AuthorityDecision, providing:
        - allowed: bool
        - reason: str (why allowed/denied)
        - degraded: bool (system in degraded mode)
        - code: str (machine-readable status)
        - conditions: tuple[str, ...] (checked conditions)
        """
        # Extract authority fields (ITER3.4 uniformity)
        authority_data = {
            "governance_active": authority_decision.allowed,
            "authority_degraded": authority_decision.degraded,
            "authority_reason": authority_decision.reason,
            "authority_code": authority_decision.code,
        }

        log_data = {
            "operation": operation,
            "tenant_id": ctx.tenant_id,
            "success": result.success,
            "duration_ms": round(duration_ms, 2),
            **authority_data,
        }

        if not result.success:
            log_data["error"] = result.error
            log_data["error_code"] = result.error_code

        if result.success:
            logger.info("operation.dispatched", extra=log_data)
        else:
            logger.warning("operation.failed", extra=log_data)

        # Phase A.6 (G4): Persist dispatch record to AuditStore
        # Post-commit only — never participates in the operation's transaction
        try:
            from app.hoc.cus.hoc_spine.services.dispatch_audit import (
                build_dispatch_record,
            )
            from app.hoc.cus.hoc_spine.services.audit_store import get_audit_store

            record = build_dispatch_record(
                operation=operation,
                tenant_id=ctx.tenant_id,
                success=result.success,
                duration_ms=duration_ms,
                authority_allowed=authority_decision.allowed,
                authority_degraded=authority_decision.degraded,
                authority_reason=authority_decision.reason,
                authority_code=authority_decision.code,
                error=result.error,
                error_code=result.error_code,
            )
            get_audit_store().record_dispatch(record)

            # Consequences pipeline: run post-dispatch adapters
            from app.hoc.cus.hoc_spine.consequences.pipeline import (
                get_consequence_pipeline,
            )
            get_consequence_pipeline().run(record)
        except Exception:
            # Non-blocking: audit persistence and consequences must never break dispatch
            logger.debug("audit_store.dispatch_record_failed", exc_info=True)

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


async def get_session_dep() -> AsyncGenerator[AsyncSession, None]:
    """
    L4-provided session dependency for L2 endpoints.

    L2 files must NOT import sqlalchemy or app.db directly.
    Instead, they import this dependency from L4 (operation_registry)
    and use it with FastAPI Depends():

        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_session_dep
        session = Depends(get_session_dep)

    This keeps L2 free of DB/ORM imports while still providing
    the session needed for OperationContext construction.
    """
    from app.db import get_async_session_dep

    async for session in get_async_session_dep():
        yield session


def get_sync_session_dep() -> Generator:
    """
    L4-provided SYNC session dependency for L2 endpoints that use
    synchronous Session (sqlmodel Session).

    Usage:
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_sync_session_dep
        session = Depends(get_sync_session_dep)
    """
    from app.db import get_session

    yield from get_session()


def sql_text(sql: str):
    """
    L4-provided wrapper for sqlalchemy text().

    L2 files must not import sqlalchemy directly. Use this helper
    for raw SQL text queries:

        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import sql_text
        result = await session.execute(sql_text("SELECT ..."), params)
    """
    from sqlalchemy import text as _text

    return _text(sql)


@asynccontextmanager
async def get_async_session_context():
    """
    L4-provided async session context manager for L2 endpoints that
    use `async with get_async_session() as session:` pattern.

    Usage:
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_async_session_context
        async with get_async_session_context() as session:
            ...
    """
    from app.db import get_async_session

    async with get_async_session() as session:
        yield session


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

