# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: System runtime health handler (DB validation + registry status + authority mode)
# Callers: OperationRegistry (L4) via operation "system.health"
# Allowed Imports: hoc_spine (authority, services), app.db (via operation_registry session context)
# Forbidden Imports: L1, L2
# Reference: HOC first-principles — L2 owns /health, DB validation lives in hoc_spine
# artifact_class: CODE

"""
System Runtime Health Handler

Moves DB validation out of app.main and into hoc_spine, so L2 /health remains
the single owner of the health endpoint while still providing truth-grade
runtime checks.
"""

from __future__ import annotations

import os
from typing import Any

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
    get_async_session_context,
    get_operation_registry,
    sql_text,
)


class SystemHealthHandler:
    """Handler for system.health."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        # Self-contained operation: create a short-lived session to validate DB connectivity.
        try:
            async with get_async_session_context() as session:
                await session.execute(sql_text("SELECT 1"))
            db_status: str = "connected"
        except Exception as e:
            db_status = f"error: {str(e)[:100]}"

        try:
            from app.hoc.cus.hoc_spine.authority.runtime_switch import (
                is_degraded_mode,
                is_governance_active,
            )

            governance_state = {
                "governance_active": bool(is_governance_active()),
                "degraded_mode": bool(is_degraded_mode()),
            }
        except Exception as e:
            governance_state = {
                "governance_active": True,
                "degraded_mode": False,
                "error": str(e)[:100],
            }

        try:
            from app.events.reactor_initializer import get_reactor_status

            reactor_status: dict[str, Any] = get_reactor_status()
        except Exception as e:
            reactor_status = {"healthy": False, "error": str(e)[:100]}

        registry = get_operation_registry()
        api_key_set = bool(os.getenv("AOS_API_KEY"))

        all_healthy = (
            db_status == "connected"
            and api_key_set
            and bool(reactor_status.get("healthy", False))
            and bool(governance_state.get("governance_active", True))
        )

        return OperationResult.ok(
            {
                "status": "healthy" if all_healthy else "degraded",
                "database": db_status,
                "api_key_configured": api_key_set,
                "event_reactor": reactor_status,
                "governance": governance_state,
                "operation_registry": registry.status(),
            }
        )


def register(registry: OperationRegistry) -> None:
    """Register system operations with the registry."""

    registry.register("system.health", SystemHealthHandler())

