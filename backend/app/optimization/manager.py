# C3 Envelope Manager
# Reference: PIN-225, C3_ENVELOPE_ABSTRACTION.md, C3_KILLSWITCH_ROLLBACK_MODEL.md
#
# Manages active envelopes and handles rollback on kill-switch.

import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from app.optimization.envelope import (
    Envelope,
    EnvelopeAuditRecord,
    EnvelopeLifecycle,
    EnvelopeValidationError,
    RevertReason,
    calculate_bounded_value,
    create_audit_record,
    validate_envelope,
)
from app.optimization.killswitch import (
    KillSwitch,
    KillSwitchEvent,
    RollbackStatus,
    get_killswitch,
)

logger = logging.getLogger("nova.optimization.manager")


@dataclass
class EnvelopeApplication:
    """Record of an active envelope application."""

    envelope: Envelope
    baseline_value: float
    applied_value: float
    applied_at: datetime
    prediction_id: str
    revert_callback: Optional[Callable[[float], None]] = None


class EnvelopeManager:
    """
    Manages the lifecycle of optimization envelopes.

    Responsibilities:
    - Validate envelopes before application
    - Track active envelopes
    - Handle kill-switch triggered rollback
    - Emit audit records
    - Ensure deterministic rollback

    Thread-safe implementation.
    """

    def __init__(self, killswitch: Optional[KillSwitch] = None):
        self._lock = threading.Lock()
        self._killswitch = killswitch or get_killswitch()
        self._active_envelopes: Dict[str, EnvelopeApplication] = {}
        self._audit_records: List[EnvelopeAuditRecord] = []

        # Register kill-switch callback
        self._killswitch.on_activate(self._on_killswitch_activated)

    @property
    def active_envelope_count(self) -> int:
        """Number of currently active envelopes."""
        with self._lock:
            return len(self._active_envelopes)

    def can_apply(self, envelope: Envelope) -> bool:
        """
        Check if an envelope can be applied.

        Returns False if:
        - Kill-switch is disabled
        - Envelope is already active
        - Envelope validation fails
        """
        # Check kill-switch first
        if self._killswitch.is_disabled:
            logger.warning(
                "envelope_apply_blocked_killswitch",
                extra={"envelope_id": envelope.envelope_id},
            )
            return False

        with self._lock:
            # Check if already active
            if envelope.envelope_id in self._active_envelopes:
                logger.warning(
                    "envelope_already_active",
                    extra={"envelope_id": envelope.envelope_id},
                )
                return False

        # Validate envelope
        try:
            validate_envelope(envelope)
            return True
        except EnvelopeValidationError as e:
            logger.error(
                "envelope_validation_failed",
                extra={
                    "envelope_id": envelope.envelope_id,
                    "rule": e.rule_id,
                    "error": e.message,
                },
            )
            return False

    def apply(
        self,
        envelope: Envelope,
        baseline_value: float,
        prediction_id: str,
        prediction_confidence: float,
        revert_callback: Optional[Callable[[float], None]] = None,
    ) -> Optional[float]:
        """
        Apply an envelope.

        Args:
            envelope: The envelope to apply
            baseline_value: Current baseline value
            prediction_id: ID of the prediction triggering this
            prediction_confidence: Confidence of the prediction (0.0-1.0)
            revert_callback: Function to call with baseline value on revert

        Returns:
            The new adjusted value, or None if application failed

        Invariants:
        - Envelope may only be Applied once
        - Returns None if kill-switch is disabled
        - Returns None if validation fails
        """
        # Check kill-switch
        if self._killswitch.is_disabled:
            logger.warning(
                "envelope_apply_rejected_killswitch_disabled",
                extra={"envelope_id": envelope.envelope_id},
            )
            return None

        # Validate
        try:
            validate_envelope(envelope)
        except EnvelopeValidationError as e:
            logger.error(
                "envelope_apply_rejected_validation",
                extra={
                    "envelope_id": envelope.envelope_id,
                    "rule": e.rule_id,
                    "error": e.message,
                },
            )
            return None

        # Check confidence threshold
        if prediction_confidence < envelope.trigger.min_confidence:
            logger.info(
                "envelope_apply_skipped_low_confidence",
                extra={
                    "envelope_id": envelope.envelope_id,
                    "confidence": prediction_confidence,
                    "min_required": envelope.trigger.min_confidence,
                },
            )
            return None

        # Calculate bounded value
        applied_value = calculate_bounded_value(baseline_value, envelope.bounds, prediction_confidence)

        now = datetime.now(timezone.utc)

        with self._lock:
            # Final kill-switch check under lock
            if self._killswitch.is_disabled:
                return None

            # Check not already active
            if envelope.envelope_id in self._active_envelopes:
                return None

            # Update envelope state
            envelope.lifecycle = EnvelopeLifecycle.ACTIVE
            envelope.applied_at = now
            envelope.prediction_id = prediction_id
            envelope.applied_value = applied_value

            # Record application
            application = EnvelopeApplication(
                envelope=envelope,
                baseline_value=baseline_value,
                applied_value=applied_value,
                applied_at=now,
                prediction_id=prediction_id,
                revert_callback=revert_callback,
            )
            self._active_envelopes[envelope.envelope_id] = application

            # Emit audit record
            audit_record = create_audit_record(envelope, baseline_value)
            self._audit_records.append(audit_record)

            logger.info(
                "envelope_applied",
                extra={
                    "envelope_id": envelope.envelope_id,
                    "target": f"{envelope.scope.target_subsystem}.{envelope.scope.target_parameter}",
                    "baseline": baseline_value,
                    "applied": applied_value,
                    "prediction_id": prediction_id,
                    "confidence": prediction_confidence,
                },
            )

        return applied_value

    def revert(
        self,
        envelope_id: str,
        reason: RevertReason,
    ) -> Optional[float]:
        """
        Revert an envelope to baseline.

        Args:
            envelope_id: ID of the envelope to revert
            reason: Why the envelope is being reverted

        Returns:
            The baseline value that was restored, or None if envelope wasn't active

        Invariants:
        - Revert restores exact baseline value
        - No gradual rollback
        - No compensating adjustments
        """
        with self._lock:
            if envelope_id not in self._active_envelopes:
                return None

            application = self._active_envelopes.pop(envelope_id)
            now = datetime.now(timezone.utc)

            # Update envelope state
            application.envelope.lifecycle = EnvelopeLifecycle.REVERTED
            application.envelope.reverted_at = now
            application.envelope.revert_reason = reason

            # Update audit record
            for record in self._audit_records:
                if record.envelope_id == envelope_id and record.reverted_at is None:
                    record.reverted_at = now
                    record.revert_reason = reason

            logger.info(
                "envelope_reverted",
                extra={
                    "envelope_id": envelope_id,
                    "reason": reason.value,
                    "baseline_restored": application.baseline_value,
                },
            )

        # Call revert callback outside lock
        if application.revert_callback:
            try:
                application.revert_callback(application.baseline_value)
            except Exception as e:
                logger.error(
                    "envelope_revert_callback_error",
                    extra={"envelope_id": envelope_id, "error": str(e)},
                )

        return application.baseline_value

    def revert_all(self, reason: RevertReason) -> int:
        """
        Revert all active envelopes.

        Args:
            reason: Why envelopes are being reverted

        Returns:
            Number of envelopes reverted

        Used by kill-switch. Order is deterministic (by envelope_id).
        """
        with self._lock:
            envelope_ids = sorted(self._active_envelopes.keys())

        reverted = 0
        for envelope_id in envelope_ids:
            if self.revert(envelope_id, reason) is not None:
                reverted += 1

        return reverted

    def _on_killswitch_activated(self, event: KillSwitchEvent) -> None:
        """
        Handle kill-switch activation.

        Rollback order (fixed per C3_KILLSWITCH_ROLLBACK_MODEL.md):
        1. Enumerate active envelopes
        2. Restore baseline values
        3. Emit audit records
        4. System returns to baseline state
        """
        logger.warning(
            "killswitch_triggered_rollback",
            extra={"event_id": event.event_id},
        )

        try:
            # Revert all envelopes
            reverted = self.revert_all(RevertReason.KILL_SWITCH)

            # Mark rollback complete
            self._killswitch.mark_rollback_complete(event.event_id, RollbackStatus.SUCCESS)

            logger.info(
                "killswitch_rollback_complete",
                extra={
                    "event_id": event.event_id,
                    "envelopes_reverted": reverted,
                },
            )
        except Exception as e:
            # Rollback failure must fail closed
            self._killswitch.mark_rollback_complete(event.event_id, RollbackStatus.FAILED)
            logger.error(
                "killswitch_rollback_failed",
                extra={"event_id": event.event_id, "error": str(e)},
            )

    def get_active_envelopes(self) -> List[Envelope]:
        """Get list of currently active envelopes."""
        with self._lock:
            return [app.envelope for app in self._active_envelopes.values()]

    def get_audit_records(self) -> List[EnvelopeAuditRecord]:
        """Get all audit records."""
        with self._lock:
            return list(self._audit_records)

    def is_envelope_active(self, envelope_id: str) -> bool:
        """Check if a specific envelope is active."""
        with self._lock:
            return envelope_id in self._active_envelopes


# Global singleton instance
_manager: Optional[EnvelopeManager] = None
_manager_lock = threading.Lock()


def get_envelope_manager() -> EnvelopeManager:
    """Get the global envelope manager instance."""
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = EnvelopeManager()
        return _manager


def reset_manager_for_testing() -> None:
    """Reset envelope manager. FOR TESTING ONLY."""
    global _manager
    with _manager_lock:
        _manager = None
