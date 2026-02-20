# capability_id: CAP-001
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine or L4 coordinator)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: audit_ledger
#   Writes: none (read-only)
# Database:
#   Scope: domain (logs)
#   Models: AuditLedger
# Role: Async audit ledger read operations for signal feedback queries
# Callers: L4 coordinators (signal_feedback_coordinator)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-519 (System Run Introspection)

"""
Audit Ledger Read Driver (PIN-519)

Provides async read operations for the AuditLedger table.
This complements the write-only AuditLedgerServiceAsync.

INVARIANTS:
- Read-only operations (no INSERT, UPDATE, DELETE)
- Queries are tenant-scoped
- Returns signal feedback status from audit events
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_ledger import (
    AuditEntityType,
    AuditEventType,
    AuditLedger,
)

logger = logging.getLogger("nova.hoc.logs.audit_ledger_read_driver")


class AuditLedgerReadDriver:
    """
    Async driver for reading from the audit ledger.

    L6 CONTRACT:
    - Pure database reads, no business logic
    - All methods are async (for use with AsyncSession)
    - Queries happen within caller's transaction
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self._session = session

    async def get_signal_feedback(
        self,
        tenant_id: str,
        signal_fingerprint: str,
    ) -> dict | None:
        """
        Get the latest feedback status for a signal.

        Queries audit ledger for SIGNAL_ACKNOWLEDGED, SIGNAL_SUPPRESSED,
        and SIGNAL_ESCALATED events for the given signal fingerprint.

        Args:
            tenant_id: Tenant owning this signal
            signal_fingerprint: Unique fingerprint of the signal

        Returns:
            Dict with feedback status, or None if no feedback exists
        """
        # Query for all signal feedback events for this fingerprint
        stmt = (
            select(AuditLedger)
            .where(
                and_(
                    AuditLedger.tenant_id == tenant_id,
                    AuditLedger.entity_type == AuditEntityType.SIGNAL.value,
                    AuditLedger.entity_id == signal_fingerprint,
                    AuditLedger.event_type.in_([
                        AuditEventType.SIGNAL_ACKNOWLEDGED.value,
                        AuditEventType.SIGNAL_SUPPRESSED.value,
                        AuditEventType.SIGNAL_ESCALATED.value,
                    ]),
                )
            )
            .order_by(desc(AuditLedger.created_at))
        )

        result = await self._session.execute(stmt)
        entries = result.scalars().all()

        if not entries:
            return None

        # Build feedback status from audit entries
        feedback: dict = {
            "acknowledged": False,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "suppressed": False,
            "suppressed_until": None,
            "escalated": False,
            "escalated_at": None,
        }

        for entry in entries:
            if entry.event_type == AuditEventType.SIGNAL_ACKNOWLEDGED.value:
                feedback["acknowledged"] = True
                feedback["acknowledged_by"] = entry.actor_id
                feedback["acknowledged_at"] = entry.created_at
            elif entry.event_type == AuditEventType.SIGNAL_SUPPRESSED.value:
                feedback["suppressed"] = True
                if entry.after_state and "suppressed_until" in entry.after_state:
                    feedback["suppressed_until"] = entry.after_state["suppressed_until"]
            elif entry.event_type == AuditEventType.SIGNAL_ESCALATED.value:
                feedback["escalated"] = True
                feedback["escalated_at"] = entry.created_at

        logger.debug(
            "signal_feedback_fetched",
            extra={
                "tenant_id": tenant_id,
                "signal_fingerprint": signal_fingerprint,
                "feedback": feedback,
            },
        )

        return feedback

    async def get_audit_entries_for_entity(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
    ) -> list[AuditLedger]:
        """
        Get audit entries for a specific entity.

        Args:
            tenant_id: Tenant owning this entity
            entity_type: Type of entity (AuditEntityType value)
            entity_id: ID of the entity
            limit: Maximum entries to return

        Returns:
            List of AuditLedger entries, newest first
        """
        stmt = (
            select(AuditLedger)
            .where(
                and_(
                    AuditLedger.tenant_id == tenant_id,
                    AuditLedger.entity_type == entity_type,
                    AuditLedger.entity_id == entity_id,
                )
            )
            .order_by(desc(AuditLedger.created_at))
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_signal_events_for_run(
        self,
        tenant_id: str,
        run_id: str,
        limit: int = 100,
    ) -> list[AuditLedger]:
        """
        Get all signal-related audit events for signals associated with a run.

        Note: This requires signals to have run_id encoded in their after_state
        or a separate mapping. For now, this is a placeholder for future use.

        Args:
            tenant_id: Tenant owning the run
            run_id: Run ID to query
            limit: Maximum entries to return

        Returns:
            List of AuditLedger entries for signals related to this run
        """
        # Query signal events where run_id is in after_state
        stmt = (
            select(AuditLedger)
            .where(
                and_(
                    AuditLedger.tenant_id == tenant_id,
                    AuditLedger.entity_type == AuditEntityType.SIGNAL.value,
                )
            )
            .order_by(desc(AuditLedger.created_at))
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        entries = result.scalars().all()

        # Filter to entries where run_id matches in after_state
        return [
            entry for entry in entries
            if entry.after_state and entry.after_state.get("run_id") == run_id
        ]


# =============================================================================
# Factory
# =============================================================================


def get_audit_ledger_read_driver(session: AsyncSession) -> AuditLedgerReadDriver:
    """
    Get an AuditLedgerReadDriver instance.

    Args:
        session: Async database session

    Returns:
        AuditLedgerReadDriver instance
    """
    return AuditLedgerReadDriver(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AuditLedgerReadDriver",
    "get_audit_ledger_read_driver",
]
