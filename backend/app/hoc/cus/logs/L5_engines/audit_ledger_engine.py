# Layer: L5 — Domain Engine
# NOTE: Renamed audit_ledger_service.py → audit_ledger_engine.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via incident_write_engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: audit_ledger (append-only)
# Database:
#   Scope: domain (logs)
#   Models: AuditLedger
# Role: Sync audit ledger writer for governance events (incidents)
# Callers: incident_write_engine (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4
# Reference: SWEEP-03 Batch 3, PIN-470, PIN-413 (Logs Domain)

"""
Audit Ledger Service (Sync)

PURPOSE:
    Provides sync methods to write governance events to the AuditLedger table.
    This is the APPEND-ONLY immutable governance action log.

IMPLEMENTATION NOTES:
    Created as part of SWEEP-03 Batch 3 to provide sync audit ledger
    operations for incident_write_engine.py which uses sync sessions.

INVARIANTS:
    - All writes are INSERT only (no UPDATE, no DELETE)
    - Each write is atomic within the caller's transaction
    - Events use canonical AuditEventType values
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

from app.hoc.cus.hoc_spine.schemas.domain_enums import (
    ActorType,
    AuditEntityType,
    AuditEventType,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from app.models.audit_ledger import AuditLedger

logger = logging.getLogger("nova.hoc.logs.audit_ledger_service")


class AuditLedgerService:
    """
    Sync service for writing to the audit ledger.

    L5 CONTRACT:
    - Pure database writes, no business logic
    - All methods are sync (for use with sqlmodel Session)
    - Writes happen within caller's transaction
    """

    def __init__(self, session: "Session"):
        """Initialize with sync database session."""
        self._session = session
        # PIN-520 No-Exemptions Phase 3: ORM construction delegated to L6 driver
        from app.hoc.cus.logs.L6_drivers.audit_ledger_write_driver_sync import (
            get_audit_ledger_write_driver_sync,
        )
        self._write_driver = get_audit_ledger_write_driver_sync(session)

    def _emit(
        self,
        tenant_id: str,
        event_type: AuditEventType,
        entity_type: AuditEntityType,
        entity_id: str,
        actor_type: ActorType,
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
    ) -> "AuditLedger":
        """
        Emit an audit event to the ledger.

        Args:
            tenant_id: Tenant owning this event
            event_type: Type of audit event
            entity_type: Type of entity being audited
            entity_id: ID of the entity
            actor_type: Type of actor (HUMAN, SYSTEM, AGENT)
            actor_id: Optional actor identifier
            reason: Optional reason/justification
            before_state: Optional state before change
            after_state: Optional state after change

        Returns:
            Created AuditLedger record (from L6 driver)
        """
        # PIN-520 No-Exemptions Phase 3: ORM construction in L6 driver
        entry = self._write_driver.emit_entry(
            tenant_id=tenant_id,
            event_type=event_type.value,
            entity_type=entity_type.value,
            entity_id=entity_id,
            actor_type=actor_type.value,
            actor_id=actor_id,
            action_reason=reason,
            before_state=before_state,
            after_state=after_state,
        )

        logger.info(
            "audit_event_emitted",
            extra={
                "event_type": event_type.value,
                "entity_type": entity_type.value,
                "entity_id": entity_id,
                "tenant_id": tenant_id,
            },
        )

        return entry

    # =========================================================================
    # Incident Events (Incidents Domain)
    # =========================================================================

    def incident_acknowledged(
        self,
        tenant_id: str,
        incident_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        incident_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record an incident acknowledgment event."""
        return self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.INCIDENT_ACKNOWLEDGED,
            entity_type=AuditEntityType.INCIDENT,
            entity_id=incident_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            after_state=incident_state,
        )

    def incident_resolved(
        self,
        tenant_id: str,
        incident_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        resolution_method: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record an incident resolution event."""
        if resolution_method:
            resolved_state = dict(after_state or {})
            resolved_state.setdefault("resolution_method", resolution_method)
        else:
            resolved_state = after_state
        return self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.INCIDENT_RESOLVED,
            entity_type=AuditEntityType.INCIDENT,
            entity_id=incident_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            before_state=before_state,
            after_state=resolved_state,
        )

    def incident_manually_closed(
        self,
        tenant_id: str,
        incident_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        incident_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record an incident manual closure event."""
        return self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.INCIDENT_MANUALLY_CLOSED,
            entity_type=AuditEntityType.INCIDENT,
            entity_id=incident_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            after_state=incident_state,
        )


# =============================================================================
# Factory
# =============================================================================


def get_audit_ledger_service(session: "Session") -> AuditLedgerService:
    """
    Get an AuditLedgerService instance.

    Args:
        session: Sync database session

    Returns:
        AuditLedgerService instance
    """
    return AuditLedgerService(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AuditLedgerService",
    "get_audit_ledger_service",
]
