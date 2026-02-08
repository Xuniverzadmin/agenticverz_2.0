# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Lifecycle DTOs — actor context, transition result, state snapshot
# Callers: tenant_lifecycle_engine.py (L5), lifecycle_handler.py (L4)
# Allowed Imports: stdlib only
# Forbidden Imports: sqlalchemy, sqlmodel, app.db, app.models
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)
# artifact_class: CODE

"""
Lifecycle DTOs

Pure-stdlib dataclasses for lifecycle operations.
No DB dependencies — used by L5 engine and L4 handler.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class LifecycleActorType(str, Enum):
    """Who initiated the lifecycle action."""

    FOUNDER = "FOUNDER"
    SYSTEM = "SYSTEM"


@dataclass
class LifecycleActorContext:
    """Context about who is performing the lifecycle action."""

    actor_type: LifecycleActorType
    actor_id: str
    reason: str


@dataclass
class LifecycleTransitionResult:
    """
    Result of a lifecycle transition attempt.

    Returned by L5 engine, consumed by L4 handler → L2 API.
    """

    success: bool
    from_status: str
    to_status: str
    action: str
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LifecycleStateSnapshot:
    """
    Read-only snapshot of a tenant's lifecycle state.

    Returned by L5 engine for query operations.
    """

    tenant_id: str
    status: str
    allows_sdk: bool
    allows_writes: bool
    allows_reads: bool
    allows_api_keys: bool
    allows_token_refresh: bool
    is_terminal: bool
    is_reversible: bool
    valid_transitions: List[str]


__all__ = [
    "LifecycleActorType",
    "LifecycleActorContext",
    "LifecycleTransitionResult",
    "LifecycleStateSnapshot",
]
