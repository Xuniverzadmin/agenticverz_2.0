# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Tenant lifecycle status enum + transition logic (pure stdlib, no DB)
# Callers: tenant_lifecycle_engine.py (L5), lifecycle_handler.py (L4), lifecycle_gate.py (L2)
# Allowed Imports: stdlib only
# Forbidden Imports: sqlalchemy, sqlmodel, app.db, app.models
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)
# artifact_class: CODE

"""
Tenant Lifecycle Status Enums

Pure-stdlib enum mirroring TenantLifecycleState (IntEnum) but using the
VARCHAR values stored in `Tenant.status`. Maps legacy "churned" → "terminated".

DESIGN INVARIANTS (LOCKED):
- OFFBOARD-001: Lifecycle transitions are monotonic
- OFFBOARD-002: TERMINATED is irreversible
- OFFBOARD-003: ARCHIVED is unreachable from ACTIVE
"""

from enum import Enum
from typing import Dict, Optional, Set


class TenantLifecycleStatus(str, Enum):
    """
    Tenant lifecycle status values (matches DB VARCHAR).

    These are the canonical string values stored in Tenant.status.
    """

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ARCHIVED = "archived"


# Legacy status mapping — normalize on read
LEGACY_STATUS_MAP: Dict[str, str] = {
    "churned": "terminated",
}


# Valid transitions matrix (from_status -> set of valid to_statuses)
# Enforces OFFBOARD-001 (monotonic), OFFBOARD-002 (TERMINATED irreversible),
# OFFBOARD-003 (ARCHIVED unreachable from ACTIVE)
VALID_TRANSITIONS: Dict[TenantLifecycleStatus, Set[TenantLifecycleStatus]] = {
    TenantLifecycleStatus.ACTIVE: {
        TenantLifecycleStatus.SUSPENDED,
        TenantLifecycleStatus.TERMINATED,
    },
    TenantLifecycleStatus.SUSPENDED: {
        TenantLifecycleStatus.ACTIVE,  # resume (only reversible path)
        TenantLifecycleStatus.TERMINATED,
    },
    TenantLifecycleStatus.TERMINATED: {
        TenantLifecycleStatus.ARCHIVED,
    },
    TenantLifecycleStatus.ARCHIVED: set(),  # terminal-terminal, no exits
}


def normalize_status(raw: Optional[str]) -> TenantLifecycleStatus:
    """
    Normalize a raw DB status string to TenantLifecycleStatus.

    Handles legacy values (e.g. "churned" → TERMINATED) and defaults
    to ACTIVE for None/unknown values.
    """
    if raw is None:
        return TenantLifecycleStatus.ACTIVE

    normalized = LEGACY_STATUS_MAP.get(raw, raw).lower()
    try:
        return TenantLifecycleStatus(normalized)
    except ValueError:
        return TenantLifecycleStatus.ACTIVE


def is_valid_transition(
    from_status: TenantLifecycleStatus,
    to_status: TenantLifecycleStatus,
) -> bool:
    """
    Check if a lifecycle transition is valid.

    Enforces:
    - OFFBOARD-001: Monotonic transitions (except SUSPENDED -> ACTIVE)
    - OFFBOARD-002: TERMINATED is irreversible
    - OFFBOARD-003: ARCHIVED is unreachable from ACTIVE
    """
    return to_status in VALID_TRANSITIONS.get(from_status, set())


def allows_sdk_execution(status: TenantLifecycleStatus) -> bool:
    """Check if SDK execution is allowed in this status."""
    return status == TenantLifecycleStatus.ACTIVE


def allows_writes(status: TenantLifecycleStatus) -> bool:
    """Check if data writes are allowed in this status."""
    return status == TenantLifecycleStatus.ACTIVE


def allows_reads(status: TenantLifecycleStatus) -> bool:
    """Check if data reads are allowed in this status."""
    return status in (
        TenantLifecycleStatus.ACTIVE,
        TenantLifecycleStatus.SUSPENDED,
    )


def allows_new_api_keys(status: TenantLifecycleStatus) -> bool:
    """Check if new API keys can be created in this status."""
    return status == TenantLifecycleStatus.ACTIVE


def allows_token_refresh(status: TenantLifecycleStatus) -> bool:
    """Check if auth token refresh is allowed in this status."""
    return status in (
        TenantLifecycleStatus.ACTIVE,
        TenantLifecycleStatus.SUSPENDED,
    )


def is_terminal(status: TenantLifecycleStatus) -> bool:
    """Check if this is a terminal status (no return to ACTIVE)."""
    return status in (
        TenantLifecycleStatus.TERMINATED,
        TenantLifecycleStatus.ARCHIVED,
    )


__all__ = [
    "TenantLifecycleStatus",
    "LEGACY_STATUS_MAP",
    "VALID_TRANSITIONS",
    "normalize_status",
    "is_valid_transition",
    "allows_sdk_execution",
    "allows_writes",
    "allows_reads",
    "allows_new_api_keys",
    "allows_token_refresh",
    "is_terminal",
]
