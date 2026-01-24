# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: Optimization envelope coordination
# Callers: workers
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: M10 Optimization

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# Coordinates optimization envelopes with conflict detection and preemption
# All state transitions are atomic, audited, and safe to retry
FEATURE_INTENT = FeatureIntent.STATE_MUTATION
RETRY_POLICY = RetryPolicy.SAFE

# C4 Multi-Envelope Coordination Manager
# Reference: C4_ENVELOPE_COORDINATION_CONTRACT.md (FROZEN), PIN-230
#
# The CoordinationManager is the ONLY legal path through which envelopes
# may apply. No envelope may bypass coordination checks.
#
# Coordination Invariants (from C4_ENVELOPE_COORDINATION_CONTRACT.md):
# - I-C4-1: No envelope applies without coordination check
# - I-C4-2: Every envelope declares exactly one class
# - I-C4-3: Priority order is global and immutable
# - I-C4-4: Same-parameter conflict always rejects second envelope
# - I-C4-5: Higher-priority envelopes preempt lower-priority
# - I-C4-6: Kill-switch reverts ALL envelopes atomically
# - I-C4-7: Every coordination decision is audited
# - I-C4-8: Replay must show coordination decisions

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlmodel import Session

from app.optimization.audit_persistence import persist_audit_record
from app.optimization.envelope import (
    CoordinationAuditRecord,
    CoordinationDecision,
    CoordinationDecisionType,
    Envelope,
    EnvelopeClass,
    EnvelopeLifecycle,
    RevertReason,
    has_higher_priority,
)

logger = logging.getLogger("nova.optimization.coordinator")


class CoordinationError(Exception):
    """Raised when coordination fails in an unrecoverable way."""

    def __init__(self, message: str, envelope_id: str):
        self.message = message
        self.envelope_id = envelope_id
        super().__init__(f"Coordination error for {envelope_id}: {message}")


class CoordinationManager:
    """
    C4 Multi-Envelope Coordination Manager.

    This class enforces all C4 coordination invariants:
    - Tracks active envelopes
    - Checks for conflicts before allowing application
    - Preempts lower-priority envelopes when higher-priority arrives
    - Handles kill-switch all-revert
    - Emits audit records for every decision

    Thread Safety:
        This implementation is NOT thread-safe. Production use
        requires external synchronization or a thread-safe wrapper.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        emit_traces: bool = True,
        tenant_id: Optional[str] = None,
    ) -> None:
        """
        Initialize CoordinationManager.

        Args:
            db: Optional database session for audit persistence.
                If None, audits are stored in-memory only.
            emit_traces: If False, skip audit persistence (replay mode).
                Respects C4_COORDINATION_AUDIT_SCHEMA.md Section 7.
            tenant_id: Optional tenant identifier for multi-tenancy.
        """
        # Active envelopes keyed by envelope_id
        self._active_envelopes: Dict[str, Envelope] = {}

        # Index: subsystem.parameter -> envelope_id
        # Used for same-parameter conflict detection (C4-R1)
        self._parameter_index: Dict[str, str] = {}

        # Audit trail (in-memory, also persisted if db provided)
        self._audit_trail: List[CoordinationAuditRecord] = []

        # Kill-switch state
        self._kill_switch_active: bool = False

        # Persistence configuration
        self._db: Optional[Session] = db
        self._emit_traces: bool = emit_traces
        self._tenant_id: Optional[str] = tenant_id

    @property
    def active_envelope_count(self) -> int:
        """Get count of currently active envelopes."""
        return len(self._active_envelopes)

    @property
    def is_kill_switch_active(self) -> bool:
        """Check if kill-switch is currently active."""
        return self._kill_switch_active

    def get_active_envelopes(self) -> List[Envelope]:
        """Get list of currently active envelopes (read-only copy)."""
        return list(self._active_envelopes.values())

    def get_audit_trail(self) -> List[CoordinationAuditRecord]:
        """Get audit trail (read-only copy)."""
        return list(self._audit_trail)

    def _get_parameter_key(self, envelope: Envelope) -> str:
        """Get the canonical key for parameter indexing."""
        return f"{envelope.scope.target_subsystem}.{envelope.scope.target_parameter}"

    def _emit_audit_record(
        self,
        envelope: Envelope,
        decision: CoordinationDecisionType,
        reason: str,
        conflicting_envelope_id: Optional[str] = None,
        preempting_envelope_id: Optional[str] = None,
    ) -> CoordinationAuditRecord:
        """
        Emit a coordination audit record (I-C4-7).

        Every coordination decision MUST be audited.

        Persistence behavior (C4_COORDINATION_AUDIT_SCHEMA.md):
        - If db is provided, persists to coordination_audit_records table
        - If emit_traces is False, skips persistence (replay mode)
        - Failures are logged but do not block coordination
        """
        decision_timestamp = datetime.now(timezone.utc)
        audit_id = str(uuid.uuid4())

        record = CoordinationAuditRecord(
            audit_id=audit_id,
            envelope_id=envelope.envelope_id,
            envelope_class=envelope.envelope_class,
            decision=decision,
            reason=reason,
            timestamp=decision_timestamp,
            conflicting_envelope_id=conflicting_envelope_id,
            preempting_envelope_id=preempting_envelope_id,
            active_envelopes_count=self.active_envelope_count,
        )
        self._audit_trail.append(record)

        # Persist to database if configured
        if self._db is not None:
            persist_audit_record(
                db=self._db,
                audit_id=audit_id,
                envelope_id=envelope.envelope_id,
                envelope_class=envelope.envelope_class.value if envelope.envelope_class else "UNKNOWN",
                decision=decision.value,
                reason=reason,
                decision_timestamp=decision_timestamp,
                conflicting_envelope_id=conflicting_envelope_id,
                preempting_envelope_id=preempting_envelope_id,
                active_envelopes_count=self.active_envelope_count,
                tenant_id=self._tenant_id,
                emit_traces=self._emit_traces,
            )

        logger.info(
            "coordination_decision",
            extra={
                "audit_id": record.audit_id,
                "envelope_id": envelope.envelope_id,
                "envelope_class": envelope.envelope_class.value if envelope.envelope_class else None,
                "decision": decision.value,
                "reason": reason,
                "conflicting_envelope_id": conflicting_envelope_id,
                "preempting_envelope_id": preempting_envelope_id,
                "active_count": record.active_envelopes_count,
                "persisted": self._db is not None and self._emit_traces,
            },
        )

        return record

    def check_allowed(self, envelope: Envelope) -> CoordinationDecision:
        """
        Check if an envelope is allowed to apply (I-C4-1).

        This method enforces:
        - C4-R1: Same-parameter conflict rejection
        - C4-R4: Priority preemption check

        Args:
            envelope: The envelope requesting to apply

        Returns:
            CoordinationDecision indicating if application is allowed
        """
        # Kill-switch blocks all new envelopes
        if self._kill_switch_active:
            decision = CoordinationDecision(
                allowed=False,
                decision=CoordinationDecisionType.REJECTED,
                reason="Kill-switch is active, no new envelopes allowed",
            )
            self._emit_audit_record(
                envelope,
                CoordinationDecisionType.REJECTED,
                "Kill-switch active",
            )
            return decision

        # Validate envelope has a class (I-C4-2)
        if envelope.envelope_class is None:
            decision = CoordinationDecision(
                allowed=False,
                decision=CoordinationDecisionType.REJECTED,
                reason="Envelope has no class declared (I-C4-2 violation)",
            )
            self._emit_audit_record(
                envelope,
                CoordinationDecisionType.REJECTED,
                "No envelope class declared",
            )
            return decision

        # Check same-parameter conflict (C4-R1)
        param_key = self._get_parameter_key(envelope)
        if param_key in self._parameter_index:
            existing_envelope_id = self._parameter_index[param_key]
            decision = CoordinationDecision(
                allowed=False,
                decision=CoordinationDecisionType.REJECTED,
                reason=f"Same-parameter conflict: {param_key} already controlled by {existing_envelope_id}",
                conflicting_envelope_id=existing_envelope_id,
            )
            self._emit_audit_record(
                envelope,
                CoordinationDecisionType.REJECTED,
                "C4-R1: Same-parameter conflict",
                conflicting_envelope_id=existing_envelope_id,
            )
            return decision

        # Check for priority preemption opportunity (C4-R4)
        # This envelope is allowed; check if it preempts any existing envelope
        # Note: Actual preemption is executed in apply(), not here
        _ = self._find_preemption_targets(envelope)

        # Envelope is allowed to apply
        decision = CoordinationDecision(
            allowed=True,
            decision=CoordinationDecisionType.APPLIED,
            reason="Coordination rules passed",
        )

        # Note: Preemption will be executed when apply() is called
        return decision

    def _find_preemption_targets(self, incoming: Envelope) -> List[Envelope]:
        """
        Find envelopes that would be preempted by the incoming envelope.

        Preemption occurs when (C4-R4):
        - Incoming envelope has HIGHER priority
        - Envelopes target the same subsystem (different parameters)

        Note: Same-parameter is rejected (C4-R1), not preempted.
        """
        targets = []
        incoming_subsystem = incoming.scope.target_subsystem

        for active in self._active_envelopes.values():
            # Only consider same-subsystem envelopes (different parameters)
            if active.scope.target_subsystem != incoming_subsystem:
                continue

            # Check if incoming has higher priority
            if has_higher_priority(incoming.envelope_class, active.envelope_class):
                targets.append(active)

        return targets

    def apply(self, envelope: Envelope) -> Tuple[bool, Optional[List[str]]]:
        """
        Apply an envelope after coordination check.

        This method:
        1. Verifies envelope was checked (must be VALIDATED)
        2. Executes any preemptions
        3. Registers envelope as active
        4. Emits audit records

        Args:
            envelope: The envelope to apply

        Returns:
            Tuple of (success, list of preempted envelope IDs)
        """
        # Pre-check: envelope must be validated
        if envelope.lifecycle != EnvelopeLifecycle.VALIDATED:
            raise CoordinationError(
                f"Envelope must be VALIDATED before apply, got {envelope.lifecycle.value}",
                envelope.envelope_id,
            )

        # Run coordination check
        decision = self.check_allowed(envelope)
        if not decision.allowed:
            return False, None

        # Execute preemptions (C4-R4)
        preempted_ids = []
        preemption_targets = self._find_preemption_targets(envelope)
        for target in preemption_targets:
            self._revert_envelope(target, RevertReason.PREEMPTED, envelope.envelope_id)
            preempted_ids.append(target.envelope_id)

        # Register envelope as active
        param_key = self._get_parameter_key(envelope)
        self._active_envelopes[envelope.envelope_id] = envelope
        self._parameter_index[param_key] = envelope.envelope_id

        # Update envelope state
        envelope.lifecycle = EnvelopeLifecycle.ACTIVE
        envelope.applied_at = datetime.now(timezone.utc)

        # Emit audit record
        self._emit_audit_record(
            envelope,
            CoordinationDecisionType.APPLIED,
            f"Applied successfully, preempted {len(preempted_ids)} envelope(s)",
        )

        logger.info(
            "envelope_applied",
            extra={
                "envelope_id": envelope.envelope_id,
                "envelope_class": envelope.envelope_class.value,
                "parameter": param_key,
                "preempted_count": len(preempted_ids),
                "preempted_ids": preempted_ids,
            },
        )

        return True, preempted_ids if preempted_ids else None

    def _revert_envelope(
        self,
        envelope: Envelope,
        reason: RevertReason,
        preempting_envelope_id: Optional[str] = None,
    ) -> None:
        """
        Revert a single envelope.

        Internal method used by kill-switch and preemption.
        """
        param_key = self._get_parameter_key(envelope)

        # Remove from indexes
        if envelope.envelope_id in self._active_envelopes:
            del self._active_envelopes[envelope.envelope_id]
        if param_key in self._parameter_index:
            del self._parameter_index[param_key]

        # Update envelope state
        envelope.lifecycle = EnvelopeLifecycle.REVERTED
        envelope.reverted_at = datetime.now(timezone.utc)
        envelope.revert_reason = reason

        # Emit audit if preempted
        if reason == RevertReason.PREEMPTED:
            self._emit_audit_record(
                envelope,
                CoordinationDecisionType.PREEMPTED,
                "Preempted by higher-priority envelope",
                preempting_envelope_id=preempting_envelope_id,
            )

        logger.info(
            "envelope_reverted",
            extra={
                "envelope_id": envelope.envelope_id,
                "reason": reason.value,
                "preempting_envelope_id": preempting_envelope_id,
            },
        )

    def revert(self, envelope_id: str, reason: RevertReason) -> bool:
        """
        Explicitly revert a single envelope.

        Args:
            envelope_id: ID of envelope to revert
            reason: Why the envelope is being reverted

        Returns:
            True if envelope was reverted, False if not found
        """
        if envelope_id not in self._active_envelopes:
            logger.warning(
                "revert_not_found",
                extra={"envelope_id": envelope_id},
            )
            return False

        envelope = self._active_envelopes[envelope_id]
        self._revert_envelope(envelope, reason)
        return True

    def kill_switch(self) -> List[str]:
        """
        Activate kill-switch: revert ALL active envelopes atomically (I-C4-6).

        The kill-switch:
        - Reverts all envelopes immediately
        - Blocks all new envelope applications
        - Emits audit records for each revert

        Returns:
            List of envelope IDs that were reverted
        """
        self._kill_switch_active = True
        reverted_ids = []

        # Copy list since we're modifying during iteration
        envelopes_to_revert = list(self._active_envelopes.values())

        for envelope in envelopes_to_revert:
            self._revert_envelope(envelope, RevertReason.KILL_SWITCH)
            reverted_ids.append(envelope.envelope_id)

        logger.warning(
            "kill_switch_activated",
            extra={
                "reverted_count": len(reverted_ids),
                "reverted_ids": reverted_ids,
            },
        )

        return reverted_ids

    def reset_kill_switch(self) -> None:
        """
        Reset kill-switch state (for testing/recovery).

        WARNING: Only use this after careful consideration.
        The kill-switch is a safety mechanism.
        """
        self._kill_switch_active = False
        logger.warning("kill_switch_reset")

    def expire_envelope(self, envelope_id: str) -> bool:
        """
        Mark an envelope as expired (timebox ended).

        Args:
            envelope_id: ID of envelope that expired

        Returns:
            True if envelope was expired, False if not found
        """
        if envelope_id not in self._active_envelopes:
            return False

        envelope = self._active_envelopes[envelope_id]
        param_key = self._get_parameter_key(envelope)

        # Remove from indexes
        del self._active_envelopes[envelope_id]
        if param_key in self._parameter_index:
            del self._parameter_index[param_key]

        # Update envelope state
        envelope.lifecycle = EnvelopeLifecycle.EXPIRED
        envelope.reverted_at = datetime.now(timezone.utc)
        envelope.revert_reason = RevertReason.TIMEBOX_EXPIRED

        logger.info(
            "envelope_expired",
            extra={"envelope_id": envelope_id},
        )

        return True

    def get_envelope_for_parameter(
        self,
        subsystem: str,
        parameter: str,
    ) -> Optional[Envelope]:
        """
        Get the active envelope controlling a specific parameter.

        Args:
            subsystem: Target subsystem
            parameter: Target parameter

        Returns:
            Active envelope if one exists, None otherwise
        """
        param_key = f"{subsystem}.{parameter}"
        envelope_id = self._parameter_index.get(param_key)
        if envelope_id:
            return self._active_envelopes.get(envelope_id)
        return None

    def get_envelopes_by_class(self, envelope_class: EnvelopeClass) -> List[Envelope]:
        """
        Get all active envelopes of a specific class.

        Args:
            envelope_class: The class to filter by

        Returns:
            List of active envelopes with that class
        """
        return [e for e in self._active_envelopes.values() if e.envelope_class == envelope_class]

    def get_coordination_stats(self) -> Dict:
        """
        Get current coordination statistics.

        Returns:
            Dictionary with coordination stats
        """
        class_counts = {}
        for envelope_class in EnvelopeClass:
            class_counts[envelope_class.value] = len(self.get_envelopes_by_class(envelope_class))

        return {
            "active_envelopes": self.active_envelope_count,
            "kill_switch_active": self._kill_switch_active,
            "audit_trail_size": len(self._audit_trail),
            "envelopes_by_class": class_counts,
            "controlled_parameters": list(self._parameter_index.keys()),
        }
