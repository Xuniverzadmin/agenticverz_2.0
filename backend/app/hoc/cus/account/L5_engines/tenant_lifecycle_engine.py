# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Role: Tenant lifecycle engine — business logic for lifecycle transitions
# Callers: lifecycle_handler.py (L4)
# Allowed Imports: L5_schemas (tenant_lifecycle_enums, lifecycle_dtos)
# Forbidden Imports: sqlalchemy, sqlmodel, app.db, app.models
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)
# artifact_class: CODE

"""
Tenant Lifecycle Engine (L5)

Business logic for tenant lifecycle transitions.
Driver is injected (duck-typed), not imported at module level.
NO COMMIT — L4 handler owns transaction boundary.

Enforces:
- OFFBOARD-001: Monotonic transitions (via is_valid_transition)
- OFFBOARD-002: TERMINATED irreversible
- OFFBOARD-003: ARCHIVED unreachable from ACTIVE
"""

from __future__ import annotations

from typing import Optional

from app.hoc.cus.account.L5_schemas.tenant_lifecycle_enums import (
    TenantLifecycleStatus,
    VALID_TRANSITIONS,
    normalize_status,
    is_valid_transition,
    allows_sdk_execution,
    allows_writes,
    allows_reads,
    allows_new_api_keys,
    allows_token_refresh,
    is_terminal,
)
from app.hoc.cus.account.L5_schemas.lifecycle_dtos import (
    LifecycleActorContext,
    LifecycleTransitionResult,
    LifecycleStateSnapshot,
)


class TenantLifecycleEngine:
    """
    L5 Engine for tenant lifecycle business logic.

    Driver is injected via constructor (duck-typed).
    All methods return pure DTOs — no ORM objects.
    NO COMMIT — L4 handler owns transaction boundary.
    """

    def __init__(self, driver):
        self._driver = driver

    def get_state(self, tenant_id: str) -> Optional[LifecycleStateSnapshot]:
        """
        Get current lifecycle state snapshot for a tenant.

        Returns None if tenant not found.
        """
        raw_status = self._driver.fetch_tenant_status(tenant_id)
        if raw_status is None:
            return None

        status = normalize_status(raw_status)
        valid = VALID_TRANSITIONS.get(status, set())

        return LifecycleStateSnapshot(
            tenant_id=tenant_id,
            status=status.value,
            allows_sdk=allows_sdk_execution(status),
            allows_writes=allows_writes(status),
            allows_reads=allows_reads(status),
            allows_api_keys=allows_new_api_keys(status),
            allows_token_refresh=allows_token_refresh(status),
            is_terminal=is_terminal(status),
            is_reversible=(status == TenantLifecycleStatus.SUSPENDED),
            valid_transitions=[s.value for s in valid],
        )

    def transition(
        self,
        tenant_id: str,
        to_status: TenantLifecycleStatus,
        actor: LifecycleActorContext,
    ) -> LifecycleTransitionResult:
        """
        Attempt a lifecycle transition.

        Validates invariants, writes via driver, returns result.
        NO COMMIT — L4 handler owns transaction boundary.
        """
        # Read current status
        raw_status = self._driver.fetch_tenant_status(tenant_id)
        if raw_status is None:
            return LifecycleTransitionResult(
                success=False,
                from_status="unknown",
                to_status=to_status.value,
                action=_action_name(to_status),
                error=f"Tenant {tenant_id} not found",
            )

        from_status = normalize_status(raw_status)

        # No-op if already in target status
        if from_status == to_status:
            return LifecycleTransitionResult(
                success=False,
                from_status=from_status.value,
                to_status=to_status.value,
                action=_action_name(to_status),
                error=f"Tenant already in {to_status.value} status",
            )

        # OFFBOARD-001, 002, 003: Check transition validity
        if not is_valid_transition(from_status, to_status):
            error_msg = f"Invalid transition: {from_status.value} -> {to_status.value}"
            if from_status == TenantLifecycleStatus.TERMINATED and to_status != TenantLifecycleStatus.ARCHIVED:
                error_msg = "OFFBOARD-002: TERMINATED is irreversible"
            elif from_status == TenantLifecycleStatus.ARCHIVED:
                error_msg = "ARCHIVED is terminal-terminal"
            elif (
                from_status == TenantLifecycleStatus.ACTIVE
                and to_status == TenantLifecycleStatus.ARCHIVED
            ):
                error_msg = "OFFBOARD-003: ARCHIVED is unreachable from ACTIVE"

            return LifecycleTransitionResult(
                success=False,
                from_status=from_status.value,
                to_status=from_status.value,
                action=_action_name(to_status),
                error=error_msg,
            )

        # Write via driver (NO COMMIT)
        reason = actor.reason if to_status == TenantLifecycleStatus.SUSPENDED else None
        self._driver.update_lifecycle_status(tenant_id, to_status.value, reason)

        return LifecycleTransitionResult(
            success=True,
            from_status=from_status.value,
            to_status=to_status.value,
            action=_action_name(to_status),
        )

    # Convenience wrappers

    def suspend(self, tenant_id: str, actor: LifecycleActorContext) -> LifecycleTransitionResult:
        """Suspend a tenant (ACTIVE -> SUSPENDED)."""
        return self.transition(tenant_id, TenantLifecycleStatus.SUSPENDED, actor)

    def resume(self, tenant_id: str, actor: LifecycleActorContext) -> LifecycleTransitionResult:
        """Resume a tenant (SUSPENDED -> ACTIVE)."""
        return self.transition(tenant_id, TenantLifecycleStatus.ACTIVE, actor)

    def terminate(self, tenant_id: str, actor: LifecycleActorContext) -> LifecycleTransitionResult:
        """Terminate a tenant (ACTIVE|SUSPENDED -> TERMINATED)."""
        return self.transition(tenant_id, TenantLifecycleStatus.TERMINATED, actor)

    def archive(self, tenant_id: str, actor: LifecycleActorContext) -> LifecycleTransitionResult:
        """Archive a tenant (TERMINATED -> ARCHIVED)."""
        return self.transition(tenant_id, TenantLifecycleStatus.ARCHIVED, actor)


def _action_name(to_status: TenantLifecycleStatus) -> str:
    """Map target status to action name."""
    return {
        TenantLifecycleStatus.ACTIVE: "resume_tenant",
        TenantLifecycleStatus.SUSPENDED: "suspend_tenant",
        TenantLifecycleStatus.TERMINATED: "terminate_tenant",
        TenantLifecycleStatus.ARCHIVED: "archive_tenant",
    }.get(to_status, "unknown")


def get_tenant_lifecycle_engine(driver) -> TenantLifecycleEngine:
    """Get a TenantLifecycleEngine instance with injected driver."""
    return TenantLifecycleEngine(driver)


__all__ = [
    "TenantLifecycleEngine",
    "get_tenant_lifecycle_engine",
]
