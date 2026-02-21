# capability_id: CAP-012
# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Tenant lifecycle IntEnum + transition helpers (stdlib only; derives truth from tenant_lifecycle_enums)
# Callers: lifecycle gates, deprecated lifecycle_provider tests, legacy shims
# Allowed Imports: stdlib + same-domain L5_schemas
# Forbidden Imports: sqlalchemy, sqlmodel, app.db, app.models
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)
# artifact_class: CODE

"""
Tenant Lifecycle State (IntEnum)

Canonical location for the Phase-9 tenant lifecycle *state machine API surface*.

Single source of truth:
- Transition validity is derived from `tenant_lifecycle_enums.VALID_TRANSITIONS`
  (the canonical status/DB-value representation). This module provides an
  IntEnum view without duplicating transition rules.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Set, Tuple

from app.hoc.cus.account.L5_schemas.tenant_lifecycle_enums import (
    TenantLifecycleStatus,
    VALID_TRANSITIONS as _STATUS_VALID_TRANSITIONS,
    is_valid_transition as _is_valid_status_transition,
)


class TenantLifecycleState(IntEnum):
    ACTIVE = 100
    SUSPENDED = 200
    TERMINATED = 300
    ARCHIVED = 400

    def allows_sdk_execution(self) -> bool:
        return self == TenantLifecycleState.ACTIVE

    def allows_writes(self) -> bool:
        return self == TenantLifecycleState.ACTIVE

    def allows_reads(self) -> bool:
        return self in (TenantLifecycleState.ACTIVE, TenantLifecycleState.SUSPENDED)

    def allows_new_api_keys(self) -> bool:
        return self == TenantLifecycleState.ACTIVE

    def allows_token_refresh(self) -> bool:
        return self in (TenantLifecycleState.ACTIVE, TenantLifecycleState.SUSPENDED)

    def is_terminal(self) -> bool:
        return self >= TenantLifecycleState.TERMINATED

    def is_reversible(self) -> bool:
        return self == TenantLifecycleState.SUSPENDED


_STATUS_TO_STATE = {
    TenantLifecycleStatus.ACTIVE: TenantLifecycleState.ACTIVE,
    TenantLifecycleStatus.SUSPENDED: TenantLifecycleState.SUSPENDED,
    TenantLifecycleStatus.TERMINATED: TenantLifecycleState.TERMINATED,
    TenantLifecycleStatus.ARCHIVED: TenantLifecycleState.ARCHIVED,
}
_STATE_TO_STATUS = {v: k for k, v in _STATUS_TO_STATE.items()}


def _to_status(state: TenantLifecycleState) -> TenantLifecycleStatus:
    return _STATE_TO_STATUS[state]


def _to_state(status: TenantLifecycleStatus) -> TenantLifecycleState:
    return _STATUS_TO_STATE[status]


VALID_TRANSITIONS: dict[TenantLifecycleState, Set[TenantLifecycleState]] = {
    _to_state(from_status): {_to_state(to_status) for to_status in to_statuses}
    for from_status, to_statuses in _STATUS_VALID_TRANSITIONS.items()
}


def is_valid_transition(from_state: TenantLifecycleState, to_state: TenantLifecycleState) -> bool:
    return _is_valid_status_transition(_to_status(from_state), _to_status(to_state))


def get_valid_transitions(from_state: TenantLifecycleState) -> Set[TenantLifecycleState]:
    return VALID_TRANSITIONS.get(from_state, set()).copy()


class LifecycleAction:
    SUSPEND = "suspend_tenant"
    RESUME = "resume_tenant"
    TERMINATE = "terminate_tenant"
    ARCHIVE = "archive_tenant"


ACTION_TRANSITIONS: dict[str, Tuple[Set[TenantLifecycleState], TenantLifecycleState]] = {
    LifecycleAction.SUSPEND: ({TenantLifecycleState.ACTIVE}, TenantLifecycleState.SUSPENDED),
    LifecycleAction.RESUME: ({TenantLifecycleState.SUSPENDED}, TenantLifecycleState.ACTIVE),
    LifecycleAction.TERMINATE: (
        {TenantLifecycleState.ACTIVE, TenantLifecycleState.SUSPENDED},
        TenantLifecycleState.TERMINATED,
    ),
    LifecycleAction.ARCHIVE: ({TenantLifecycleState.TERMINATED}, TenantLifecycleState.ARCHIVED),
}


def get_action_for_transition(from_state: TenantLifecycleState, to_state: TenantLifecycleState) -> str | None:
    for action, (valid_from, target) in ACTION_TRANSITIONS.items():
        if from_state in valid_from and to_state == target:
            return action
    return None


__all__ = [
    "TenantLifecycleState",
    "LifecycleAction",
    "VALID_TRANSITIONS",
    "ACTION_TRANSITIONS",
    "is_valid_transition",
    "get_valid_transitions",
    "get_action_for_transition",
]

