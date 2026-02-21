# capability_id: CAP-012
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: SIGNAL_ACKNOWLEDGED, SIGNAL_SUPPRESSED, SIGNAL_REOPENED
#   Subscribes: none
# Data Access:
#   Reads: signal_feedback (via L6 driver)
#   Writes: signal_feedback (via L6 driver)
# Role: Signal feedback engine for acknowledging/suppressing signals
# Callers: activity_handler.py (L4)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: UC-010 Activity Feedback Lifecycle
# artifact_class: CODE
"""Signal feedback engine for user interactions with signals."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from app.hoc.cus.hoc_spine.services.time import utc_now
from app.hoc.cus.activity.L6_drivers.signal_feedback_driver import SignalFeedbackDriver


@dataclass
class AcknowledgeResult:
    """Result of acknowledging a signal."""

    signal_id: str
    acknowledged: bool
    acknowledged_at: datetime
    acknowledged_by: Optional[str]
    message: str


@dataclass
class SuppressResult:
    """Result of suppressing a signal."""

    signal_id: str
    suppressed: bool
    suppressed_at: datetime
    suppressed_by: Optional[str]
    suppressed_until: Optional[datetime]
    reason: Optional[str]
    message: str


@dataclass
class SignalFeedbackStatus:
    """Current feedback status for a signal."""

    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    suppressed: bool = False
    suppressed_until: Optional[datetime] = None


_driver = SignalFeedbackDriver()


class SignalFeedbackService:
    """
    Service for managing user feedback on signals.

    Provides:
    - Acknowledge: Mark signal as seen/reviewed
    - Suppress: Temporarily hide signal from attention queue
    - Reopen: Revoke suppression early
    - Bulk: Apply ack/suppress to multiple signals
    """

    def __init__(self) -> None:
        pass

    async def acknowledge_signal(
        self,
        session: Any,
        tenant_id: str,
        signal_id: str,
        *,
        acknowledged_by: Optional[str] = None,
        as_of: Optional[str] = None,
    ) -> AcknowledgeResult:
        """Acknowledge a signal — persists to signal_feedback table."""
        effective_as_of = as_of or (utc_now().isoformat() + "Z")
        row = await _driver.insert_feedback(
            session,
            tenant_id=tenant_id,
            signal_fingerprint=signal_id,
            feedback_state="ACKNOWLEDGED",
            as_of=effective_as_of,
            actor_id=acknowledged_by or "system",
        )
        return AcknowledgeResult(
            signal_id=signal_id,
            acknowledged=True,
            acknowledged_at=utc_now(),
            acknowledged_by=acknowledged_by,
            message="Signal acknowledged",
        )

    async def suppress_signal(
        self,
        session: Any,
        tenant_id: str,
        signal_id: str,
        *,
        suppressed_by: Optional[str] = None,
        duration_minutes: int = 1440,
        reason: Optional[str] = None,
        as_of: Optional[str] = None,
        bulk_action_id: Optional[str] = None,
        target_set_hash: Optional[str] = None,
        target_count: Optional[int] = None,
    ) -> SuppressResult:
        """Suppress a signal for a duration — persists to signal_feedback table."""
        effective_as_of = as_of or (utc_now().isoformat() + "Z")
        suppressed_until = utc_now() + timedelta(minutes=duration_minutes)
        ttl_seconds = duration_minutes * 60

        await _driver.insert_feedback(
            session,
            tenant_id=tenant_id,
            signal_fingerprint=signal_id,
            feedback_state="SUPPRESSED",
            as_of=effective_as_of,
            actor_id=suppressed_by or "system",
            ttl_seconds=ttl_seconds,
            expires_at=suppressed_until.isoformat(),
            bulk_action_id=bulk_action_id,
            target_set_hash=target_set_hash,
            target_count=target_count,
        )
        return SuppressResult(
            signal_id=signal_id,
            suppressed=True,
            suppressed_at=utc_now(),
            suppressed_by=suppressed_by,
            suppressed_until=suppressed_until,
            reason=reason,
            message=f"Signal suppressed for {duration_minutes} minutes",
        )

    async def reopen_signal(
        self,
        session: Any,
        tenant_id: str,
        signal_id: str,
        *,
        reopened_by: Optional[str] = None,
        as_of: Optional[str] = None,
    ) -> dict[str, Any]:
        """Reopen a suppressed signal — inserts REOPENED record."""
        effective_as_of = as_of or (utc_now().isoformat() + "Z")
        row = await _driver.insert_feedback(
            session,
            tenant_id=tenant_id,
            signal_fingerprint=signal_id,
            feedback_state="REOPENED",
            as_of=effective_as_of,
            actor_id=reopened_by or "system",
        )
        return {"signal_id": signal_id, "reopened": True, "reopened_by": reopened_by}

    async def get_signal_feedback_status(
        self,
        session: Any,
        tenant_id: str,
        signal_id: str,
    ) -> dict[str, Any]:
        """Get current feedback status for a signal."""
        row = await _driver.query_feedback(
            session,
            tenant_id=tenant_id,
            signal_fingerprint=signal_id,
        )
        if not row:
            return {"acknowledged": False, "suppressed": False, "state": None}
        return {
            "state": row["feedback_state"],
            "acknowledged": row["feedback_state"] == "ACKNOWLEDGED",
            "suppressed": row["feedback_state"] == "SUPPRESSED",
            "actor_id": row.get("actor_id"),
            "expires_at": str(row["expires_at"]) if row.get("expires_at") else None,
            "created_at": str(row["created_at"]) if row.get("created_at") else None,
        }

    async def get_bulk_signal_feedback(
        self,
        session: Any,
        tenant_id: str,
        signal_ids: list[str],
    ) -> dict[str, SignalFeedbackStatus]:
        """Get feedback status for multiple signals in bulk."""
        result: dict[str, SignalFeedbackStatus] = {}
        for sig_id in signal_ids:
            row = await _driver.query_feedback(
                session,
                tenant_id=tenant_id,
                signal_fingerprint=sig_id,
            )
            if row:
                result[sig_id] = SignalFeedbackStatus(
                    acknowledged=row["feedback_state"] == "ACKNOWLEDGED",
                    suppressed=row["feedback_state"] == "SUPPRESSED",
                    suppressed_until=row.get("expires_at"),
                )
        return result

    async def evaluate_expired(
        self,
        session: Any,
        as_of: Optional[str] = None,
    ) -> int:
        """Mark expired suppressions as EVALUATED. Returns count."""
        effective_as_of = as_of or (utc_now().isoformat() + "Z")
        return await _driver.mark_expired_as_evaluated(session, as_of=effective_as_of)
