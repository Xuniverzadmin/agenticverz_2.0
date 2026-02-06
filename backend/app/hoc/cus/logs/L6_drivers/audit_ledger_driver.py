# Layer: L6 — Domain Driver
# NOTE: Renamed audit_ledger_service_async.py → audit_ledger_driver.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: audit_ledger (append-only)
# Database:
#   Scope: domain (logs)
#   Models: AuditLedger
# Role: Async audit ledger writer for governance events
# Callers: policy_limits_engine, policy_rules_engine, policy_proposal_engine (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, PIN-413 (Logs Domain)

"""
Audit Ledger Service (Async)

Provides async methods to write governance events to the AuditLedger table.
This is the APPEND-ONLY immutable governance action log.

INVARIANTS:
- All writes are INSERT only (no UPDATE, no DELETE)
- Each write is atomic within the caller's transaction
- Events use canonical AuditEventType values
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_ledger import (
    ActorType,
    AuditEntityType,
    AuditEventType,
    AuditLedger,
)

logger = logging.getLogger("nova.hoc.logs.audit_ledger_service_async")


class AuditLedgerServiceAsync:
    """
    Async service for writing to the audit ledger.

    L6 CONTRACT:
    - Pure database writes, no business logic
    - All methods are async (for use with AsyncSession)
    - Writes happen within caller's transaction
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self._session = session

    async def _emit(
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
    ) -> AuditLedger:
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
            Created AuditLedger record
        """
        entry = AuditLedger(
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

        self._session.add(entry)
        # Note: Commit happens in caller's transaction
        await self._session.flush()

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
    # Limit Events (Policies Domain)
    # =========================================================================

    async def limit_created(
        self,
        tenant_id: str,
        limit_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.SYSTEM,
        reason: Optional[str] = None,
        limit_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a limit creation event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.LIMIT_CREATED,
            entity_type=AuditEntityType.LIMIT,
            entity_id=limit_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            after_state=limit_state,
        )

    async def limit_updated(
        self,
        tenant_id: str,
        limit_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.SYSTEM,
        reason: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a limit update event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.LIMIT_UPDATED,
            entity_type=AuditEntityType.LIMIT,
            entity_id=limit_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            before_state=before_state,
            after_state=after_state,
        )

    async def limit_breached(
        self,
        tenant_id: str,
        limit_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.SYSTEM,
        reason: Optional[str] = None,
        breach_details: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a limit breach event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.LIMIT_BREACHED,
            entity_type=AuditEntityType.LIMIT,
            entity_id=limit_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            after_state=breach_details,
        )

    # =========================================================================
    # Policy Rule Events (Policies Domain)
    # =========================================================================

    async def policy_rule_created(
        self,
        tenant_id: str,
        rule_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.SYSTEM,
        reason: Optional[str] = None,
        rule_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a policy rule creation event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.POLICY_RULE_CREATED,
            entity_type=AuditEntityType.POLICY_RULE,
            entity_id=rule_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            after_state=rule_state,
        )

    async def policy_rule_modified(
        self,
        tenant_id: str,
        rule_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.SYSTEM,
        reason: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a policy rule modification event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.POLICY_RULE_MODIFIED,
            entity_type=AuditEntityType.POLICY_RULE,
            entity_id=rule_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            before_state=before_state,
            after_state=after_state,
        )

    async def policy_rule_retired(
        self,
        tenant_id: str,
        rule_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.SYSTEM,
        reason: Optional[str] = None,
        rule_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a policy rule retirement event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.POLICY_RULE_RETIRED,
            entity_type=AuditEntityType.POLICY_RULE,
            entity_id=rule_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            before_state=rule_state,
        )

    # =========================================================================
    # Policy Proposal Events (Policies Domain)
    # =========================================================================

    async def policy_proposal_approved(
        self,
        tenant_id: str,
        proposal_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        proposal_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a policy proposal approval event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.POLICY_PROPOSAL_APPROVED,
            entity_type=AuditEntityType.POLICY_PROPOSAL,
            entity_id=proposal_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            after_state=proposal_state,
        )

    async def policy_proposal_rejected(
        self,
        tenant_id: str,
        proposal_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        proposal_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a policy proposal rejection event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.POLICY_PROPOSAL_REJECTED,
            entity_type=AuditEntityType.POLICY_PROPOSAL,
            entity_id=proposal_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            after_state=proposal_state,
        )

    # =========================================================================
    # Signal Feedback Events (PIN-519)
    # =========================================================================

    async def signal_acknowledged(
        self,
        tenant_id: str,
        signal_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        signal_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a signal acknowledgment event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.SIGNAL_ACKNOWLEDGED,
            entity_type=AuditEntityType.SIGNAL,
            entity_id=signal_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            after_state=signal_state,
        )

    async def signal_suppressed(
        self,
        tenant_id: str,
        signal_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.HUMAN,
        reason: Optional[str] = None,
        suppressed_until: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a signal suppression event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.SIGNAL_SUPPRESSED,
            entity_type=AuditEntityType.SIGNAL,
            entity_id=signal_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            after_state=suppressed_until,
        )

    async def signal_escalated(
        self,
        tenant_id: str,
        signal_id: str,
        actor_id: Optional[str] = None,
        actor_type: ActorType = ActorType.SYSTEM,
        reason: Optional[str] = None,
        escalation_context: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Record a signal escalation event."""
        return await self._emit(
            tenant_id=tenant_id,
            event_type=AuditEventType.SIGNAL_ESCALATED,
            entity_type=AuditEntityType.SIGNAL,
            entity_id=signal_id,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=reason,
            after_state=escalation_context,
        )


# =============================================================================
# Factory
# =============================================================================


def get_audit_ledger_service_async(session: AsyncSession) -> AuditLedgerServiceAsync:
    """
    Get an AuditLedgerServiceAsync instance.

    Args:
        session: Async database session

    Returns:
        AuditLedgerServiceAsync instance
    """
    return AuditLedgerServiceAsync(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AuditLedgerServiceAsync",
    "get_audit_ledger_service_async",
]
