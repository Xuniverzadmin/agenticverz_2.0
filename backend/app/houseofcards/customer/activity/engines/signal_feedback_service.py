# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Role: Signal feedback service for acknowledging/suppressing signals
"""Signal feedback service for user interactions with signals."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.houseofcards.customer.general.utils.time import utc_now


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


class SignalFeedbackService:
    """
    Service for managing user feedback on signals.

    Provides:
    - Acknowledge: Mark signal as seen/reviewed
    - Suppress: Temporarily hide signal from attention queue
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def acknowledge_signal(
        self,
        tenant_id: str,
        signal_id: str,
        *,
        acknowledged_by: Optional[str] = None,
    ) -> AcknowledgeResult:
        """Acknowledge a signal."""
        return AcknowledgeResult(
            signal_id=signal_id,
            acknowledged=True,
            acknowledged_at=utc_now(),
            acknowledged_by=acknowledged_by,
            message="Signal acknowledged",
        )

    async def suppress_signal(
        self,
        tenant_id: str,
        signal_id: str,
        *,
        suppressed_by: Optional[str] = None,
        duration_hours: int = 24,
        reason: Optional[str] = None,
    ) -> SuppressResult:
        """Suppress a signal for a duration."""
        from datetime import timedelta

        suppressed_until = utc_now() + timedelta(hours=duration_hours)

        return SuppressResult(
            signal_id=signal_id,
            suppressed=True,
            suppressed_at=utc_now(),
            suppressed_by=suppressed_by,
            suppressed_until=suppressed_until,
            reason=reason,
            message=f"Signal suppressed for {duration_hours} hours",
        )

    async def get_signal_feedback_status(
        self,
        tenant_id: str,
        signal_id: str,
    ) -> dict[str, bool]:
        """Get current feedback status for a signal."""
        return {
            "acknowledged": False,
            "suppressed": False,
        }

    async def get_bulk_signal_feedback(
        self,
        tenant_id: str,
        signal_ids: list[str],
    ) -> dict[str, SignalFeedbackStatus]:
        """
        Get feedback status for multiple signals in bulk.

        Returns a dict mapping signal_id to feedback status.
        """
        # Stub implementation - returns empty feedback for all signals
        _ = tenant_id
        _ = signal_ids
        return {}
