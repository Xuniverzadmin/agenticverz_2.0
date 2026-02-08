# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: sync (handlers), async (helper functions)
# Role: Onboarding domain handler — routes onboarding operations + async helpers for call sites
# Callers: OperationRegistry (L4), gateway_middleware, SDK endpoints, onboarding endpoints
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.account.L5_engines (lazy), L5_schemas (lazy)
# Forbidden Imports: L1, L2, L6 (except lazy in handlers), sqlalchemy (except via operation_registry)
# Reference: PIN-399 (Onboarding State Machine v1)
# artifact_class: CODE

"""
Onboarding Handler (L4 Orchestrator)

Routes onboarding domain operations to L5 engine.
Registers two operations:
  - account.onboarding.query -> OnboardingStateSnapshot
  - account.onboarding.advance -> OnboardingTransitionResult

Also provides async helper functions for call sites that need
onboarding state reads/advances outside of DI (middleware, side-effects).
L4 owns transaction boundaries for mutations.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)

logger = logging.getLogger("nova.hoc.account.onboarding_handler")


class AccountOnboardingQueryHandler:
    """
    Handler for account.onboarding.query operations.

    Returns onboarding state snapshot for a tenant.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.account.L6_drivers.onboarding_driver import (
            get_onboarding_driver,
        )
        from app.hoc.cus.account.L5_engines.onboarding_engine import (
            get_onboarding_engine,
        )

        sync_session = ctx.params.get("sync_session")
        if not sync_session:
            return OperationResult.fail(
                "Missing 'sync_session' in params", "MISSING_SESSION"
            )

        driver = get_onboarding_driver(sync_session)
        engine = get_onboarding_engine(driver)
        snapshot = engine.get_state(ctx.tenant_id)

        if snapshot is None:
            return OperationResult.fail(
                f"Tenant {ctx.tenant_id} not found", "TENANT_NOT_FOUND"
            )

        return OperationResult.ok({
            "tenant_id": snapshot.tenant_id,
            "state_value": snapshot.state_value,
            "state_name": snapshot.state_name,
            "is_complete": snapshot.is_complete,
        })


class AccountOnboardingAdvanceHandler:
    """
    Handler for account.onboarding.advance operations.

    Performs onboarding state transitions.
    L4 owns transaction boundary.

    Required params:
      - sync_session: SQLModel Session (from L2 DI)
      - target_state: int (OnboardingStatus value)
      - trigger: str (what caused the transition)
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.account.L6_drivers.onboarding_driver import (
            get_onboarding_driver,
        )
        from app.hoc.cus.account.L5_engines.onboarding_engine import (
            get_onboarding_engine,
        )

        sync_session = ctx.params.get("sync_session")
        if not sync_session:
            return OperationResult.fail(
                "Missing 'sync_session' in params", "MISSING_SESSION"
            )

        target_state = ctx.params.get("target_state")
        if target_state is None:
            return OperationResult.fail(
                "Missing 'target_state' in params", "MISSING_TARGET_STATE"
            )

        trigger = ctx.params.get("trigger", "unknown")

        driver = get_onboarding_driver(sync_session)
        engine = get_onboarding_engine(driver)

        # L4 owns transaction — engine writes, we commit
        result = engine.advance(ctx.tenant_id, target_state, trigger)

        if result.success and not result.was_no_op:
            sync_session.commit()

        return OperationResult.ok({
            "success": result.success,
            "from_state": result.from_state,
            "to_state": result.to_state,
            "trigger": result.trigger,
            "message": result.message,
            "was_no_op": result.was_no_op,
        })


# =============================================================================
# ASYNC HELPER FUNCTIONS
# =============================================================================
# These are L4-owned async functions for call sites that cannot use DI
# (middleware, fire-and-forget side effects in route handlers).
# L4 owns the transaction (commit inside the async context manager).


async def async_advance_onboarding(
    tenant_id: str, target_state: int, trigger: str
) -> dict:
    """
    L4-owned async onboarding advance for middleware/async call sites.

    Uses raw SQL via get_async_session_context() — no ORM dependency.
    L4 owns the transaction (commit inside the async context manager).
    """
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
        get_async_session_context,
        sql_text,
    )
    from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingStatus

    try:
        async with get_async_session_context() as session:
            row = (await session.execute(
                sql_text("SELECT onboarding_state FROM tenants WHERE id = :tid"),
                {"tid": tenant_id},
            )).mappings().first()

            if row is None:
                return {"success": False, "message": "Tenant not found", "was_no_op": False}

            current = row["onboarding_state"]

            if current >= target_state:
                current_name = OnboardingStatus(current).name
                return {
                    "success": True,
                    "was_no_op": True,
                    "from_state": current_name,
                    "to_state": current_name,
                }

            await session.execute(
                sql_text("UPDATE tenants SET onboarding_state = :state WHERE id = :tid"),
                {"state": target_state, "tid": tenant_id},
            )
            await session.commit()

            from_name = OnboardingStatus(current).name
            to_name = OnboardingStatus(target_state).name

            logger.info(
                "onboarding_state_transition",
                extra={
                    "tenant_id": tenant_id,
                    "from_state": from_name,
                    "to_state": to_name,
                    "trigger": trigger,
                },
            )

            return {
                "success": True,
                "was_no_op": False,
                "from_state": from_name,
                "to_state": to_name,
            }

    except Exception as e:
        logger.error(
            "async_advance_onboarding_error",
            extra={"tenant_id": tenant_id, "target_state": target_state, "error": str(e)},
            exc_info=True,
        )
        return {"success": False, "message": f"Transition failed: {e}", "was_no_op": False}


async def async_get_onboarding_state(tenant_id: str) -> Optional[int]:
    """
    L4-owned async onboarding state read.

    Uses raw SQL via get_async_session_context() — no ORM dependency.
    """
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
        get_async_session_context,
        sql_text,
    )

    try:
        async with get_async_session_context() as session:
            row = (await session.execute(
                sql_text("SELECT onboarding_state FROM tenants WHERE id = :tid"),
                {"tid": tenant_id},
            )).mappings().first()

            if row is None:
                return None
            return row["onboarding_state"]

    except Exception as e:
        logger.error(
            "async_get_onboarding_state_error",
            extra={"tenant_id": tenant_id, "error": str(e)},
            exc_info=True,
        )
        return None


async def async_detect_stalled_onboarding(threshold_hours: int = 24) -> list[dict]:
    """
    L4-owned stalled onboarding detection.

    Ops/founder visibility helper: returns tenants that are not COMPLETE and were
    created more than `threshold_hours` ago.

    Returns:
      [
        {
          "tenant_id": "...",
          "state_value": 1,
          "state_name": "IDENTITY_VERIFIED",
          "created_at": "2026-02-08T00:00:00",
          "hours_stalled": 25.0,
        },
        ...
      ]

    Uses raw SQL via get_async_session_context() — no ORM dependency.
    """
    from datetime import datetime, timedelta

    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
        get_async_session_context,
        sql_text,
    )
    from app.hoc.cus.account.L5_schemas.onboarding_state import (
        OnboardingStatus,
        ONBOARDING_STATUS_NAMES,
    )

    now = datetime.utcnow()
    threshold_time = now - timedelta(hours=threshold_hours)

    async with get_async_session_context() as session:
        rows = (await session.execute(
            sql_text(
                "SELECT id, onboarding_state, created_at "
                "FROM tenants "
                "WHERE onboarding_state < :complete AND created_at < :threshold"
            ),
            {
                "complete": OnboardingStatus.COMPLETE.value,
                "threshold": threshold_time,
            },
        )).mappings().all()

        stalled: list[dict] = []
        for row in rows:
            created_at = row.get("created_at")
            if not created_at:
                continue

            state_value = row.get("onboarding_state", 0)
            state_name = ONBOARDING_STATUS_NAMES.get(state_value, f"UNKNOWN_{state_value}")
            hours_stalled = (now - created_at).total_seconds() / 3600

            stalled.append(
                {
                    "tenant_id": row.get("id"),
                    "state_value": state_value,
                    "state_name": state_name,
                    "created_at": created_at.isoformat(),
                    "hours_stalled": hours_stalled,
                }
            )

        return stalled


def register(registry: OperationRegistry) -> None:
    """Register onboarding operations with the registry."""
    registry.register("account.onboarding.query", AccountOnboardingQueryHandler())
    registry.register("account.onboarding.advance", AccountOnboardingAdvanceHandler())
