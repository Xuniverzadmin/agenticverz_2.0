# capability_id: CAP-012
# Layer: L4 — HOC Spine (Service)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (post-dispatch)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none (pure builder — caller persists)
# Role: Dispatch audit record builder — pure, side-effect free
# Callers: OperationRegistry._audit_dispatch()
# Allowed Imports: hoc_spine/services (time)
# Forbidden Imports: L1, L2, L5, L6, sqlalchemy, app.db
# Reference: PIN-520 Phase A.6, Gap G4
# artifact_class: CODE

"""
Dispatch Audit Record — pure builder for operation dispatch records.

This module provides:
- DispatchRecord: Frozen dataclass capturing a single registry dispatch
- build_dispatch_record(): Pure builder function (no side effects)

Constitution §2.3: consequences are post-commit. This module records what
happened AFTER the operation completed. It never participates in the
operation's transaction.

Usage:
    record = build_dispatch_record(
        operation="policies.query",
        tenant_id="t_abc",
        success=True,
        duration_ms=42.3,
        authority_allowed=True,
        authority_degraded=False,
        authority_reason="governance active",
        authority_code="ALLOWED",
    )
    # Caller (AuditStore) handles persistence
"""

from dataclasses import dataclass
from typing import Optional

from app.hoc.cus.hoc_spine.services.time import utc_now


@dataclass(frozen=True)
class DispatchRecord:
    """
    Immutable record of a single operation dispatch.

    Fields mirror _audit_dispatch() log_data plus timestamp.
    Frozen: once built, never mutated.
    """

    operation: str
    tenant_id: str
    success: bool
    duration_ms: float
    timestamp: str  # ISO 8601 UTC

    # Authority decision fields
    authority_allowed: bool = True
    authority_degraded: bool = False
    authority_reason: str = ""
    authority_code: str = ""

    # Error fields (only populated on failure)
    error: Optional[str] = None
    error_code: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dict for storage/transport."""
        d = {
            "operation": self.operation,
            "tenant_id": self.tenant_id,
            "success": self.success,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp,
            "authority_allowed": self.authority_allowed,
            "authority_degraded": self.authority_degraded,
            "authority_reason": self.authority_reason,
            "authority_code": self.authority_code,
        }
        if self.error is not None:
            d["error"] = self.error
            d["error_code"] = self.error_code
        return d


def build_dispatch_record(
    operation: str,
    tenant_id: str,
    success: bool,
    duration_ms: float,
    authority_allowed: bool = True,
    authority_degraded: bool = False,
    authority_reason: str = "",
    authority_code: str = "",
    error: Optional[str] = None,
    error_code: Optional[str] = None,
) -> DispatchRecord:
    """
    Build a DispatchRecord from dispatch parameters.

    Pure function — no side effects, no I/O, no state mutation.

    Args:
        operation: Operation name (e.g. "policies.query")
        tenant_id: Tenant identifier
        success: Whether the operation succeeded
        duration_ms: Execution duration in milliseconds
        authority_allowed: Whether authority allowed the operation
        authority_degraded: Whether authority was in degraded mode
        authority_reason: Human-readable authority reason
        authority_code: Machine-readable authority code
        error: Error message (failures only)
        error_code: Error code (failures only)

    Returns:
        Frozen DispatchRecord
    """
    return DispatchRecord(
        operation=operation,
        tenant_id=tenant_id,
        success=success,
        duration_ms=duration_ms,
        timestamp=utc_now().isoformat(),
        authority_allowed=authority_allowed,
        authority_degraded=authority_degraded,
        authority_reason=authority_reason,
        authority_code=authority_code,
        error=error,
        error_code=error_code,
    )
