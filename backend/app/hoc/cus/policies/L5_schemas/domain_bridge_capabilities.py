# capability_id: CAP-009
# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Role: Capability Protocols for cross-domain access via DomainBridge
# Callers: lessons_engine.py, policies_limits_query_engine.py, policy_limits_engine.py
# Allowed Imports: stdlib only
# Forbidden Imports: L6, sqlalchemy
# Reference: PIN-508 Phase 2 (DomainBridge capability-narrowed Protocols)
# artifact_class: CODE

"""
Domain Bridge Capability Protocols (PIN-508 Phase 2)

These Protocols define the narrow capability interfaces that policies L5 engines
see when accessing cross-domain services via DomainBridge.

Gap 3 applied: DomainBridge returns capability Protocols, not concrete driver types.
The consumer sees only the operations it needs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# =============================================================================
# 2A: LessonsQueryCapability — used by lessons_engine.py
# =============================================================================


@runtime_checkable
class LessonsQueryCapability(Protocol):
    """Capability Protocol for lessons data access.

    PIN-508 Phase 2A: Only the methods lessons_engine actually calls.
    Implemented by LessonsDriver.
    """

    def insert_lesson(
        self,
        lesson_id: str,
        tenant_id: str,
        lesson_type: str,
        severity: Optional[str],
        source_event_id: str,
        source_event_type: str,
        source_run_id: Optional[str],
        title: str,
        description: str,
        proposed_action: Optional[str],
        detected_pattern: Optional[Dict[str, Any]],
        now: datetime,
        is_synthetic: bool,
        synthetic_scenario_id: Optional[str],
    ) -> bool: ...

    def fetch_lessons_list(
        self,
        tenant_id: str,
        lesson_type: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        include_synthetic: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]: ...

    def fetch_lesson_by_id(
        self, lesson_id: str, tenant_id: str,
    ) -> Optional[Dict[str, Any]]: ...

    def fetch_lesson_stats(self, tenant_id: str) -> List[Any]: ...

    def fetch_debounce_count(
        self,
        tenant_id: str,
        lesson_type: str,
        metric_type: str,
        hours: int,
        threshold_band: Optional[str] = None,
    ) -> int: ...

    def insert_policy_proposal_from_lesson(
        self,
        proposal_id: str,
        tenant_id: str,
        title: str,
        description: str,
        proposed_action: str,
        source_lesson_id: str,
        created_at: datetime,
        created_by: str,
    ) -> bool: ...

    def update_lesson_converted(
        self,
        lesson_id: str,
        tenant_id: str,
        converted_status: str,
        proposal_id: str,
        converted_at: datetime,
    ) -> bool: ...

    def update_lesson_deferred(
        self,
        lesson_id: str,
        tenant_id: str,
        deferred_status: str,
        defer_until: datetime,
    ) -> bool: ...

    def update_lesson_dismissed(
        self,
        lesson_id: str,
        tenant_id: str,
        dismissed_status: str,
        dismissed_at: datetime,
        dismissed_by: str,
        reason: str,
    ) -> bool: ...

    def update_lesson_reactivated(
        self,
        lesson_id: str,
        tenant_id: str,
        pending_status: str,
        from_status: str,
    ) -> bool: ...

    def fetch_expired_deferred(
        self, deferred_status: str, limit: int,
    ) -> List[Any]: ...


# =============================================================================
# 2B: LimitsQueryCapability — used by policies_limits_query_engine.py
# =============================================================================


@runtime_checkable
class LimitsQueryCapability(Protocol):
    """Capability Protocol for limits read access.

    PIN-508 Phase 2B: Only the methods LimitsQueryEngine actually calls.
    Implemented by LimitsReadDriver.
    """

    async def fetch_limits(
        self,
        tenant_id: str,
        category: str,
        status: str,
        scope: Optional[str] = None,
        enforcement: Optional[str] = None,
        limit_type: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int]: ...

    async def fetch_limit_by_id(
        self, tenant_id: str, limit_id: str,
    ) -> Optional[Dict[str, Any]]: ...

    async def fetch_budget_limits(
        self,
        tenant_id: str,
        scope: Optional[str] = None,
        status: str = "ACTIVE",
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]: ...


# =============================================================================
# 2C: PolicyLimitsCapability — used by policy_limits_engine.py
# =============================================================================


@runtime_checkable
class PolicyLimitsCapability(Protocol):
    """Capability Protocol for policy limits CRUD.

    PIN-508 Phase 2C: Only the methods PolicyLimitsService actually calls.
    Implemented by PolicyLimitsDriver.
    """

    def add_limit(self, limit: Any) -> None: ...
    def add_integrity(self, integrity: Any) -> None: ...
    async def fetch_limit_by_id(self, tenant_id: str, limit_id: str) -> Any: ...
    async def flush(self) -> None: ...


__all__ = [
    "LessonsQueryCapability",
    "LimitsQueryCapability",
    "PolicyLimitsCapability",
]
