# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api, worker
#   Execution: sync (DB writes)
# Role: Audit ledger write operations (L4)
# Callers: incident_write_service.py, policy services
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-413 (Logs Domain)
#
"""
Audit Ledger Service (L4)

Writes governance actions to the AuditLedger table.
Called from governance services when canonical events occur.

Events that create audit entries:
- IncidentAcknowledged, IncidentResolved, IncidentManuallyClosed
- PolicyRuleCreated, PolicyRuleModified, PolicyRuleRetired
- PolicyProposalApproved, PolicyProposalRejected
- LimitCreated, LimitUpdated, LimitBreached
- EmergencyOverrideActivated, EmergencyOverrideDeactivated
- SignalAcknowledged, SignalSuppressed (Signal Feedback)
"""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlmodel import Session

from app.models.audit_ledger import (
    ActorType,
    AuditEntityType,
    AuditEventType,
    AuditLedger,
)


class AuditLedgerService:
    """
    L4 service for audit ledger write operations.

    Provides a single entry point for emitting governance events.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    def emit(
        self,
        tenant_id: str,
        event_type: AuditEventType,
        entity_type: AuditEntityType,
        entity_id: str,
        actor_type: ActorType,
        actor_id: Optional[str] = None,
        action_reason: Optional[str] = None,
        before_state: Optional[dict[str, Any]] = None,
        after_state: Optional[dict[str, Any]] = None,
    ) -> AuditLedger:
        """
        Emit an audit event to the ledger.

        TRANSACTION CONTRACT:
        - This method MUST be called inside an active transaction
        - Caller owns the transaction boundary (commit/rollback)
        - If audit emit fails, the entire operation must fail
        - Audit record commits IFF the state change commits (atomic)

        Args:
            tenant_id: Tenant context
            event_type: Canonical event type (from AuditEventType)
            entity_type: Entity being affected
            entity_id: ID of the entity
            actor_type: Who performed the action
            actor_id: ID of the actor (if applicable)
            action_reason: Why the action was taken
            before_state: State before change (for MODIFY events)
            after_state: State after change (for MODIFY events)

        Returns:
            Created AuditLedger entry (uncommitted - caller must commit)

        Raises:
            RuntimeError: If called outside an active transaction
        """
        # GUARD: Prevent misuse - emit() must be inside a transaction
        if not self._session.in_transaction():
            raise RuntimeError(
                "AuditLedgerService.emit() called outside an active transaction. "
                "Audit events must be atomic with the state change they represent."
            )

        entry = AuditLedger(
            tenant_id=tenant_id,
            event_type=event_type.value,
            entity_type=entity_type.value,
            entity_id=entity_id,
            actor_type=actor_type.value,
            actor_id=actor_id,
            action_reason=action_reason,
            before_state=before_state,
            after_state=after_state,
            created_at=datetime.now(timezone.utc),
        )

        self._session.add(entry)
        # NO commit - caller owns transaction boundary
        # NO flush - let SQLAlchemy batch operations

        return entry

    # -------------------------------------------------------------------------
    # Convenience methods for common events
    # -------------------------------------------------------------------------

    def incident_acknowledged(
        self,
        tenant_id: str,
        incident_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
    ) -> AuditLedger:
        """Record incident acknowledgment."""
        return self.emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.INCIDENT_ACKNOWLEDGED,
            entity_type=AuditEntityType.INCIDENT,
            entity_id=incident_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action_reason=reason,
        )

    def incident_resolved(
        self,
        tenant_id: str,
        incident_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        resolution_method: Optional[str] = None,
    ) -> AuditLedger:
        """Record incident resolution."""
        return self.emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.INCIDENT_RESOLVED,
            entity_type=AuditEntityType.INCIDENT,
            entity_id=incident_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action_reason=reason,
            after_state={"resolution_method": resolution_method} if resolution_method else None,
        )

    def incident_manually_closed(
        self,
        tenant_id: str,
        incident_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        before_state: Optional[dict[str, Any]] = None,
        after_state: Optional[dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record incident manual closure."""
        return self.emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.INCIDENT_MANUALLY_CLOSED,
            entity_type=AuditEntityType.INCIDENT,
            entity_id=incident_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action_reason=reason,
            before_state=before_state,
            after_state=after_state,
        )

    def policy_rule_created(
        self,
        tenant_id: str,
        rule_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        rule_state: Optional[dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record policy rule creation."""
        return self.emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.POLICY_RULE_CREATED,
            entity_type=AuditEntityType.POLICY_RULE,
            entity_id=rule_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action_reason=reason,
            after_state=rule_state,
        )

    def policy_proposal_approved(
        self,
        tenant_id: str,
        proposal_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
    ) -> AuditLedger:
        """Record policy proposal approval."""
        return self.emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.POLICY_PROPOSAL_APPROVED,
            entity_type=AuditEntityType.POLICY_PROPOSAL,
            entity_id=proposal_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action_reason=reason,
        )

    # -------------------------------------------------------------------------
    # Signal Feedback Events (SIGNAL-ID-001, ATTN-DAMP-001)
    # -------------------------------------------------------------------------

    def signal_acknowledged(
        self,
        tenant_id: str,
        signal_fingerprint: str,
        actor_id: str,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        signal_context: Optional[dict[str, Any]] = None,
    ) -> AuditLedger:
        """
        Record signal acknowledgment.

        Invariant (SIGNAL-ID-001): signal_fingerprint MUST be derived from
        backend-computed projection, never from client input.

        Args:
            tenant_id: Tenant scope
            signal_fingerprint: Canonical signal fingerprint (sig-{hash})
            actor_id: ID of the acknowledging actor
            actor_type: Type of actor (default: HUMAN)
            reason: Optional reason for acknowledgment
            signal_context: Structured context (run_id, signal_type, risk_type)

        Returns:
            Created AuditLedger entry
        """
        return self.emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.SIGNAL_ACKNOWLEDGED,
            entity_type=AuditEntityType.SIGNAL,
            entity_id=signal_fingerprint,
            actor_type=actor_type,
            actor_id=actor_id,
            action_reason=reason,
            after_state=signal_context,
        )

    def signal_suppressed(
        self,
        tenant_id: str,
        signal_fingerprint: str,
        actor_id: str,
        suppress_until: datetime,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        signal_context: Optional[dict[str, Any]] = None,
    ) -> AuditLedger:
        """
        Record signal suppression.

        Invariant (SIGNAL-SUPPRESS-001): Suppression is time-bound (15-1440 minutes).
        No permanent silencing allowed.

        Invariant (SIGNAL-SCOPE-001): Suppression applies tenant-wide.
        actor_id is for accountability, not scoping.

        Args:
            tenant_id: Tenant scope
            signal_fingerprint: Canonical signal fingerprint (sig-{hash})
            actor_id: ID of the suppressing actor
            suppress_until: UTC datetime when suppression expires
            actor_type: Type of actor (default: HUMAN)
            reason: Optional reason for suppression
            signal_context: Structured context (run_id, signal_type, risk_type)

        Returns:
            Created AuditLedger entry
        """
        after_state = signal_context.copy() if signal_context else {}
        after_state["suppress_until"] = suppress_until.isoformat()

        return self.emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.SIGNAL_SUPPRESSED,
            entity_type=AuditEntityType.SIGNAL,
            entity_id=signal_fingerprint,
            actor_type=actor_type,
            actor_id=actor_id,
            action_reason=reason,
            after_state=after_state,
        )


def emit_audit_event(
    session: Session,
    tenant_id: str,
    event_type: AuditEventType,
    entity_type: AuditEntityType,
    entity_id: str,
    actor_type: ActorType = ActorType.SYSTEM,
    actor_id: Optional[str] = None,
    action_reason: Optional[str] = None,
    before_state: Optional[dict[str, Any]] = None,
    after_state: Optional[dict[str, Any]] = None,
) -> AuditLedger:
    """
    Convenience function to emit an audit event.

    Use this when you don't want to instantiate the service.
    """
    service = AuditLedgerService(session)
    return service.emit(
        tenant_id=tenant_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action_reason=action_reason,
        before_state=before_state,
        after_state=after_state,
    )
