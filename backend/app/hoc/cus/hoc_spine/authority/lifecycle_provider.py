# Layer: L4 — hoc_spine Authority
# AUDIENCE: SHARED
# Role: Phase-9 tenant lifecycle provider (test harness + invariant reference)
# Product: system-wide
# Temporal:
#   Trigger: request/test
#   Execution: sync
# Callers: tests (phase-9), optional runtime shims
# Allowed Imports: stdlib, hoc/cus/account L5_schemas (tenant_lifecycle_state)
# Forbidden Imports: FastAPI, Starlette, DB
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)

"""
Phase-9 Tenant Lifecycle Provider (Canonical)

This module provides:
- TenantLifecycleProvider: Protocol for lifecycle operations
- MockTenantLifecycleProvider: Deterministic mock implementation
- TransitionResult: Result of lifecycle transitions

It is a *provider surface* used to mechanically validate OFFBOARD invariants.
Runtime request gating and lifecycle transitions are owned by the HOC execution
path (L2 -> L4 -> L5 -> L6) and DB-backed state, but the mock provider remains
useful for isolated invariant tests.

DESIGN INVARIANTS (LOCKED):
- OFFBOARD-001: Lifecycle transitions are monotonic
- OFFBOARD-002: TERMINATED is irreversible
- OFFBOARD-003: ARCHIVED is unreachable from ACTIVE
- OFFBOARD-004: No customer-initiated offboarding mutations
- OFFBOARD-005: All API keys must be revoked on TERMINATED
- OFFBOARD-006: SDK execution must be blocked before termination completes
- OFFBOARD-007: No new auth tokens after TERMINATED
- OFFBOARD-008: Offboarding emits unified observability events
- OFFBOARD-009: Observability never blocks offboarding
- OFFBOARD-010: All offboarding actions are auditable

APPLICABILITY:
    Lifecycle applies ONLY after OnboardingState.COMPLETE.
    Before COMPLETE, lifecycle is not applicable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional, Protocol

from app.hoc.cus.account.L5_schemas.tenant_lifecycle_state import (
    LifecycleAction,
    TenantLifecycleState,
    get_action_for_transition,
    is_valid_transition,
)

logger = logging.getLogger(__name__)


class ActorType(str, Enum):
    """Who initiated the lifecycle action."""

    FOUNDER = "FOUNDER"
    SYSTEM = "SYSTEM"
    CUSTOMER = "CUSTOMER"  # Only for reads, never for mutations


@dataclass
class ActorContext:
    """Context about who is performing the action."""

    actor_type: ActorType
    actor_id: str
    reason: str


@dataclass
class TransitionResult:
    """
    Result of a lifecycle transition attempt.

    Attributes:
        success: Whether the transition succeeded
        from_state: The state before transition attempt
        to_state: The resulting state (same as from_state if failed)
        action: The action that was attempted
        error: Error message if transition failed
        timestamp: When the transition occurred
        revoked_api_keys: Number of API keys revoked (on TERMINATED)
        blocked_workers: Number of background workers stopped
    """

    success: bool
    from_state: TenantLifecycleState
    to_state: TenantLifecycleState
    action: str
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_api_keys: int = 0
    blocked_workers: int = 0

    def to_audit_record(self) -> dict:
        return {
            "event_type": "tenant_lifecycle_transition",
            "success": self.success,
            "from_state": self.from_state.name,
            "to_state": self.to_state.name,
            "action": self.action,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "revoked_api_keys": self.revoked_api_keys,
            "blocked_workers": self.blocked_workers,
        }


@dataclass
class LifecycleTransitionRecord:
    """Historical record of a lifecycle transition."""

    tenant_id: str
    from_state: TenantLifecycleState
    to_state: TenantLifecycleState
    action: str
    actor: ActorContext
    timestamp: datetime
    success: bool
    error: Optional[str] = None


class TenantLifecycleProvider(Protocol):
    """Protocol for tenant lifecycle operations."""

    def get_state(self, tenant_id: str) -> TenantLifecycleState:
        ...

    def transition(
        self,
        tenant_id: str,
        to_state: TenantLifecycleState,
        actor: ActorContext,
    ) -> TransitionResult:
        ...

    def suspend(self, tenant_id: str, actor: ActorContext) -> TransitionResult:
        ...

    def resume(self, tenant_id: str, actor: ActorContext) -> TransitionResult:
        ...

    def terminate(self, tenant_id: str, actor: ActorContext) -> TransitionResult:
        ...

    def archive(self, tenant_id: str, actor: ActorContext) -> TransitionResult:
        ...

    def get_history(self, tenant_id: str) -> List[LifecycleTransitionRecord]:
        ...

    def allows_sdk_execution(self, tenant_id: str) -> bool:
        ...

    def allows_writes(self, tenant_id: str) -> bool:
        ...

    def allows_new_api_keys(self, tenant_id: str) -> bool:
        ...


class MockTenantLifecycleProvider:
    """
    Deterministic mock implementation of TenantLifecycleProvider.

    In-memory storage with full invariant enforcement.
    Emits observability events via callback (non-blocking per OFFBOARD-009).
    """

    def __init__(
        self,
        observability_callback: Optional[Callable[[dict], None]] = None,
        api_key_revocation_callback: Optional[Callable[[str], int]] = None,
        worker_blocking_callback: Optional[Callable[[str], int]] = None,
    ):
        self._states: Dict[str, TenantLifecycleState] = {}
        self._history: Dict[str, List[LifecycleTransitionRecord]] = {}
        self._observability_callback = observability_callback
        self._api_key_revocation_callback = api_key_revocation_callback
        self._worker_blocking_callback = worker_blocking_callback

    def get_state(self, tenant_id: str) -> TenantLifecycleState:
        return self._states.get(tenant_id, TenantLifecycleState.ACTIVE)

    def _emit_event(self, tenant_id: str, result: TransitionResult, actor: ActorContext) -> None:
        if self._observability_callback is None:
            return
        try:
            event = {
                "event_type": "tenant_lifecycle_transition",
                "tenant_id": tenant_id,
                "from_state": result.from_state.name,
                "to_state": result.to_state.name,
                "action": result.action,
                "actor_type": actor.actor_type.value,
                "actor_id": actor.actor_id,
                "reason": actor.reason,
                "success": result.success,
                "error": result.error,
                "timestamp": result.timestamp.isoformat(),
                "revoked_api_keys": result.revoked_api_keys,
                "blocked_workers": result.blocked_workers,
            }
            self._observability_callback(event)
        except Exception as e:
            logger.warning(f"Failed to emit lifecycle event: {e}")

    def transition(
        self,
        tenant_id: str,
        to_state: TenantLifecycleState,
        actor: ActorContext,
    ) -> TransitionResult:
        from_state = self.get_state(tenant_id)
        action = get_action_for_transition(from_state, to_state) or "unknown"
        timestamp = datetime.now(timezone.utc)

        if actor.actor_type == ActorType.CUSTOMER:
            result = TransitionResult(
                success=False,
                from_state=from_state,
                to_state=from_state,
                action=action,
                error="OFFBOARD-004: Customers cannot initiate lifecycle mutations",
                timestamp=timestamp,
            )
            self._emit_event(tenant_id, result, actor)
            self._record_history(tenant_id, result, actor)
            return result

        if not is_valid_transition(from_state, to_state):
            error_msg = f"Invalid transition: {from_state.name} -> {to_state.name}"
            if from_state == TenantLifecycleState.TERMINATED:
                error_msg = "OFFBOARD-002: TERMINATED is irreversible"
            elif from_state == TenantLifecycleState.ARCHIVED:
                error_msg = "ARCHIVED is terminal-terminal"
            elif from_state == TenantLifecycleState.ACTIVE and to_state == TenantLifecycleState.ARCHIVED:
                error_msg = "OFFBOARD-003: ARCHIVED is unreachable from ACTIVE"

            result = TransitionResult(
                success=False,
                from_state=from_state,
                to_state=from_state,
                action=action,
                error=error_msg,
                timestamp=timestamp,
            )
            self._emit_event(tenant_id, result, actor)
            self._record_history(tenant_id, result, actor)
            return result

        revoked_keys = 0
        blocked_workers = 0

        if to_state == TenantLifecycleState.TERMINATED:
            if self._api_key_revocation_callback:
                try:
                    revoked_keys = self._api_key_revocation_callback(tenant_id)
                except Exception as e:
                    logger.error(f"API key revocation failed: {e}")
            if self._worker_blocking_callback:
                try:
                    blocked_workers = self._worker_blocking_callback(tenant_id)
                except Exception as e:
                    logger.error(f"Worker blocking failed: {e}")

        self._states[tenant_id] = to_state

        result = TransitionResult(
            success=True,
            from_state=from_state,
            to_state=to_state,
            action=action,
            timestamp=timestamp,
            revoked_api_keys=revoked_keys,
            blocked_workers=blocked_workers,
        )
        self._emit_event(tenant_id, result, actor)
        self._record_history(tenant_id, result, actor)
        return result

    def _record_history(self, tenant_id: str, result: TransitionResult, actor: ActorContext) -> None:
        if tenant_id not in self._history:
            self._history[tenant_id] = []
        self._history[tenant_id].append(
            LifecycleTransitionRecord(
                tenant_id=tenant_id,
                from_state=result.from_state,
                to_state=result.to_state,
                action=result.action,
                actor=actor,
                timestamp=result.timestamp,
                success=result.success,
                error=result.error,
            )
        )

    def suspend(self, tenant_id: str, actor: ActorContext) -> TransitionResult:
        return self.transition(tenant_id, TenantLifecycleState.SUSPENDED, actor)

    def resume(self, tenant_id: str, actor: ActorContext) -> TransitionResult:
        return self.transition(tenant_id, TenantLifecycleState.ACTIVE, actor)

    def terminate(self, tenant_id: str, actor: ActorContext) -> TransitionResult:
        return self.transition(tenant_id, TenantLifecycleState.TERMINATED, actor)

    def archive(self, tenant_id: str, actor: ActorContext) -> TransitionResult:
        return self.transition(tenant_id, TenantLifecycleState.ARCHIVED, actor)

    def get_history(self, tenant_id: str) -> List[LifecycleTransitionRecord]:
        return self._history.get(tenant_id, []).copy()

    def allows_sdk_execution(self, tenant_id: str) -> bool:
        return self.get_state(tenant_id).allows_sdk_execution()

    def allows_writes(self, tenant_id: str) -> bool:
        return self.get_state(tenant_id).allows_writes()

    def allows_new_api_keys(self, tenant_id: str) -> bool:
        return self.get_state(tenant_id).allows_new_api_keys()

    def set_state(self, tenant_id: str, state: TenantLifecycleState) -> None:
        self._states[tenant_id] = state

    def clear(self) -> None:
        self._states.clear()
        self._history.clear()


_lifecycle_provider: Optional[TenantLifecycleProvider] = None


def get_lifecycle_provider() -> TenantLifecycleProvider:
    global _lifecycle_provider
    if _lifecycle_provider is None:
        _lifecycle_provider = MockTenantLifecycleProvider()
    return _lifecycle_provider


def set_lifecycle_provider(provider: TenantLifecycleProvider) -> None:
    global _lifecycle_provider
    _lifecycle_provider = provider


__all__ = [
    "ActorType",
    "ActorContext",
    "TransitionResult",
    "LifecycleTransitionRecord",
    "TenantLifecycleProvider",
    "MockTenantLifecycleProvider",
    "get_lifecycle_provider",
    "set_lifecycle_provider",
]

