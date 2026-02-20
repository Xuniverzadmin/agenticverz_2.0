# capability_id: CAP-001
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L5 audit_ledger_engine.py)
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
# Role: Sync audit ledger writer — ORM construction for L5 engine
# Callers: audit_ledger_engine.py (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-520 No-Exemptions Phase 3
# artifact_class: CODE

"""
Audit Ledger Sync Write Driver (L6)

ORM construction for audit ledger entries. Mirrors the async driver
(audit_ledger_driver.py) but uses sync sqlmodel Session.

PIN-520 No-Exemptions Phase 3: Moves AuditLedger ORM construction out of
the L5 engine so L5 has zero runtime app.models imports.

L6 Contract:
    - Session REQUIRED (passed from L4 handler via L5 engine)
    - L6 does NOT commit (L4 owns transaction boundary)
    - All writes are INSERT only (append-only governance log)
"""

import logging
from typing import Any, Dict, Optional

from sqlmodel import Session

from app.models.audit_ledger import AuditLedger

logger = logging.getLogger("nova.hoc.logs.audit_ledger_write_driver_sync")


class AuditLedgerWriteDriverSync:
    """L6 sync driver for constructing and persisting AuditLedger ORM rows."""

    def __init__(self, session: Session):
        self._session = session

    def emit_entry(
        self,
        tenant_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_type: str,
        actor_id: Optional[str] = None,
        action_reason: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
    ) -> AuditLedger:
        """Construct and persist an AuditLedger ORM row.

        Args:
            All fields as primitive strings (enum .value already applied by L5).

        Returns:
            Flushed AuditLedger ORM row with generated ID.
        """
        entry = AuditLedger(
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

        self._session.add(entry)
        self._session.flush()

        return entry


def get_audit_ledger_write_driver_sync(session: Session) -> AuditLedgerWriteDriverSync:
    """Factory for AuditLedgerWriteDriverSync."""
    return AuditLedgerWriteDriverSync(session)
