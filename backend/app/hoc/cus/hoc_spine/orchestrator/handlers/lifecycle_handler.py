# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: sync
# Role: Lifecycle domain handler — routes lifecycle operations to L5 engine via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.account.L5_engines (lazy), L5_schemas (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)
# artifact_class: CODE

"""
Lifecycle Handler (L4 Orchestrator)

Routes lifecycle domain operations to L5 engine.
Registers two operations:
  - account.lifecycle.query → LifecycleStateSnapshot
  - account.lifecycle.transition → LifecycleTransitionResult

L4 owns transaction boundaries for mutations.
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class AccountLifecycleQueryHandler:
    """
    Handler for account.lifecycle.query operations.

    Returns lifecycle state snapshot for a tenant.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.account.L6_drivers.tenant_lifecycle_driver import (
            get_tenant_lifecycle_driver,
        )
        from app.hoc.cus.account.L5_engines.tenant_lifecycle_engine import (
            get_tenant_lifecycle_engine,
        )

        sync_session = ctx.params.get("sync_session")
        if not sync_session:
            return OperationResult.fail(
                "Missing 'sync_session' in params", "MISSING_SESSION"
            )

        driver = get_tenant_lifecycle_driver(sync_session)
        engine = get_tenant_lifecycle_engine(driver)
        snapshot = engine.get_state(ctx.tenant_id)

        if snapshot is None:
            return OperationResult.fail(
                f"Tenant {ctx.tenant_id} not found", "TENANT_NOT_FOUND"
            )

        return OperationResult.ok({
            "tenant_id": snapshot.tenant_id,
            "status": snapshot.status,
            "allows_sdk": snapshot.allows_sdk,
            "allows_writes": snapshot.allows_writes,
            "allows_reads": snapshot.allows_reads,
            "allows_api_keys": snapshot.allows_api_keys,
            "allows_token_refresh": snapshot.allows_token_refresh,
            "is_terminal": snapshot.is_terminal,
            "is_reversible": snapshot.is_reversible,
            "valid_transitions": snapshot.valid_transitions,
        })


class AccountLifecycleTransitionHandler:
    """
    Handler for account.lifecycle.transition operations.

    Performs lifecycle transitions (suspend, resume, terminate, archive).
    L4 owns transaction boundary.

    Required params:
      - sync_session: SQLModel Session (from L2 DI)
      - action: "suspend" | "resume" | "terminate" | "archive"
      - reason: Human-readable reason for transition
      - actor_id: ID of the actor performing the transition
      - actor_type: "FOUNDER" | "SYSTEM"
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.account.L6_drivers.tenant_lifecycle_driver import (
            get_tenant_lifecycle_driver,
        )
        from app.hoc.cus.account.L5_engines.tenant_lifecycle_engine import (
            get_tenant_lifecycle_engine,
        )
        from app.hoc.cus.account.L5_schemas.lifecycle_dtos import (
            LifecycleActorContext,
            LifecycleActorType,
        )

        sync_session = ctx.params.get("sync_session")
        if not sync_session:
            return OperationResult.fail(
                "Missing 'sync_session' in params", "MISSING_SESSION"
            )

        action = ctx.params.get("action")
        if not action:
            return OperationResult.fail(
                "Missing 'action' in params", "MISSING_ACTION"
            )

        valid_actions = {"suspend", "resume", "terminate", "archive"}
        if action not in valid_actions:
            return OperationResult.fail(
                f"Invalid action: {action}. Must be one of: {valid_actions}",
                "INVALID_ACTION",
            )

        reason = ctx.params.get("reason", "")
        actor_id = ctx.params.get("actor_id", "unknown")
        actor_type_str = ctx.params.get("actor_type", "FOUNDER")

        try:
            actor_type = LifecycleActorType(actor_type_str)
        except ValueError:
            return OperationResult.fail(
                f"Invalid actor_type: {actor_type_str}", "INVALID_ACTOR_TYPE"
            )

        actor = LifecycleActorContext(
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
        )

        driver = get_tenant_lifecycle_driver(sync_session)
        engine = get_tenant_lifecycle_engine(driver)

        # Dispatch to convenience method
        dispatch = {
            "suspend": engine.suspend,
            "resume": engine.resume,
            "terminate": engine.terminate,
            "archive": engine.archive,
        }
        method = dispatch[action]

        # L4 owns transaction — engine writes, we commit
        result = method(ctx.tenant_id, actor)

        if result.success:
            sync_session.commit()

        return OperationResult.ok({
            "success": result.success,
            "from_status": result.from_status,
            "to_status": result.to_status,
            "action": result.action,
            "error": result.error,
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
        })


def register(registry: OperationRegistry) -> None:
    """Register lifecycle operations with the registry."""
    registry.register("account.lifecycle.query", AccountLifecycleQueryHandler())
    registry.register("account.lifecycle.transition", AccountLifecycleTransitionHandler())
