# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: Optimization audit trail persistence
# Callers: optimization/coordinator
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: M10 Optimization

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# Append-only INSERT operations to coordination_audit_records
# Non-blocking failures, replay-safe, atomic operations
FEATURE_INTENT = FeatureIntent.STATE_MUTATION
RETRY_POLICY = RetryPolicy.SAFE

# C4 Coordination Audit Persistence
# Reference: C4_COORDINATION_AUDIT_SCHEMA.md
#
# This module persists coordination audit records to the database.
# It is the ONLY module that writes to coordination_audit_records.
#
# Design Principles:
# - Append-only: INSERT only, never UPDATE
# - Non-blocking: Failures log but don't block coordination
# - Replay-safe: Respects emit_traces flag
# - Isolated: No learning imports (CI-C4-8)

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import Field, Session, SQLModel

logger = logging.getLogger("nova.optimization.audit_persistence")


def _now_utc() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


class CoordinationAuditRecordDB(SQLModel, table=True):
    """
    SQLModel for coordination_audit_records table.

    This is a read-only reflection of the table created by migration
    063_c4_coordination_audit.py. The model is for persistence only.
    """

    __tablename__ = "coordination_audit_records"

    audit_id: UUID = Field(primary_key=True)
    envelope_id: str = Field(max_length=100)
    envelope_class: str = Field(max_length=20)
    decision: str = Field(max_length=20)
    reason: str
    decision_timestamp: datetime
    created_at: datetime = Field(default_factory=_now_utc)
    conflicting_envelope_id: Optional[str] = Field(default=None, max_length=100)
    preempting_envelope_id: Optional[str] = Field(default=None, max_length=100)
    active_envelopes_count: int = Field(default=0)
    tenant_id: Optional[str] = Field(default=None, max_length=100)


def persist_audit_record(
    db: Session,
    audit_id: str,
    envelope_id: str,
    envelope_class: str,
    decision: str,
    reason: str,
    decision_timestamp: datetime,
    conflicting_envelope_id: Optional[str] = None,
    preempting_envelope_id: Optional[str] = None,
    active_envelopes_count: int = 0,
    tenant_id: Optional[str] = None,
    emit_traces: bool = True,
) -> bool:
    """
    Persist a coordination audit record to the database.

    This function is the ONLY legal path to write audit records.

    Args:
        db: Database session
        audit_id: UUID of the audit record
        envelope_id: ID of the envelope being coordinated
        envelope_class: SAFETY, RELIABILITY, COST, or PERFORMANCE
        decision: APPLIED, REJECTED, or PREEMPTED
        reason: Human-readable reason for decision
        decision_timestamp: When the decision was made
        conflicting_envelope_id: For REJECTED, the conflicting envelope
        preempting_envelope_id: For PREEMPTED, the preempting envelope
        active_envelopes_count: Count of active envelopes at decision time
        tenant_id: Optional tenant identifier
        emit_traces: If False, skip persistence (replay mode)

    Returns:
        True if persisted successfully, False otherwise
    """
    # Replay safety: skip persistence during replay
    if not emit_traces:
        logger.debug(
            "audit_skipped_replay",
            extra={"envelope_id": envelope_id, "reason": "emit_traces=False"},
        )
        return True  # Not an error, just skipped

    try:
        # Convert string UUID to UUID object
        audit_uuid = UUID(audit_id) if isinstance(audit_id, str) else audit_id

        record = CoordinationAuditRecordDB(
            audit_id=audit_uuid,
            envelope_id=envelope_id,
            envelope_class=envelope_class,
            decision=decision,
            reason=reason,
            decision_timestamp=decision_timestamp,
            conflicting_envelope_id=conflicting_envelope_id,
            preempting_envelope_id=preempting_envelope_id,
            active_envelopes_count=active_envelopes_count,
            tenant_id=tenant_id,
        )
        db.add(record)
        db.commit()

        logger.debug(
            "audit_persisted",
            extra={
                "audit_id": audit_id,
                "envelope_id": envelope_id,
                "decision": decision,
            },
        )
        return True

    except Exception as e:
        # Non-blocking: log error but don't raise
        # Coordination correctness > audit completeness
        logger.error(
            "audit_persistence_failed",
            extra={
                "envelope_id": envelope_id,
                "decision": decision,
                "error": str(e),
            },
        )
        # Rollback the failed transaction
        try:
            db.rollback()
        except Exception:
            pass
        return False
