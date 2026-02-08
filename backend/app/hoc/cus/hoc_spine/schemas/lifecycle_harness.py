# Layer: L4 — HOC Spine (Schemas)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Lifecycle harness kit — protocol interfaces for lifecycle operations
# Callers: L4 handlers, L5 engines (duck-typed injection)
# Allowed Imports: stdlib only
# Forbidden Imports: sqlalchemy, sqlmodel, app.db, app.models
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)
# artifact_class: CODE

"""
Lifecycle Harness Kit

Protocol interfaces for lifecycle operations. These define the behavioral
contracts that L4 uses to interact with domain-specific lifecycle engines
without direct cross-domain imports.

Follows hoc_spine/schemas/protocols.py pattern (@runtime_checkable).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class LifecycleReaderPort(Protocol):
    """
    Behavioral contract for lifecycle state reads.

    Implemented by: TenantLifecycleEngine (account/L5_engines)
    Consumed by: L4 handlers, lifecycle gate
    Wired by: L4 handler (constructor injection)
    """

    def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get current lifecycle state for an entity."""
        ...


@runtime_checkable
class LifecycleWriterPort(Protocol):
    """
    Behavioral contract for lifecycle state mutations.

    Implemented by: TenantLifecycleEngine (account/L5_engines)
    Consumed by: L4 handlers
    Wired by: L4 handler (constructor injection)
    """

    def transition(
        self,
        entity_id: str,
        to_state: str,
        actor_type: str,
        actor_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Attempt a lifecycle transition. Returns result dict."""
        ...


@dataclass
class LifecycleGateDecision:
    """
    Decision from lifecycle gate evaluation.

    Used by middleware to decide whether to allow/deny a request
    based on the entity's current lifecycle state.
    """

    allowed: bool
    state: str
    reason: str
    entity_id: str


__all__ = [
    "LifecycleReaderPort",
    "LifecycleWriterPort",
    "LifecycleGateDecision",
]
