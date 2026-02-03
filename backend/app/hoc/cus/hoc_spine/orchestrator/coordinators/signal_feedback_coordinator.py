# Layer: L4 — HOC Spine (Coordinator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — signal feedback queries
# Callers: ActivityFacade (L5)
# Allowed Imports: hoc_spine, bridges (lazy)
# Forbidden Imports: L1, L2, L5 engines directly
# Reference: PIN-519 System Run Introspection
# artifact_class: CODE

"""
Signal Feedback Coordinator (PIN-519)

L4 coordinator that queries signal feedback from audit ledger.

Provides feedback status for signals:
- Acknowledged: Signal was reviewed by a user
- Suppressed: Signal is temporarily hidden
- Escalated: Signal was escalated to higher priority
"""

import logging
from datetime import datetime
from typing import Any

from app.hoc.cus.hoc_spine.schemas.run_introspection_protocols import (
    SignalFeedbackResult,
)

logger = logging.getLogger("nova.hoc_spine.coordinators.signal_feedback")


class SignalFeedbackCoordinator:
    """L4 coordinator: Query signal feedback from audit ledger.

    Provides feedback status for signals by querying the audit ledger
    for SIGNAL_ACKNOWLEDGED, SIGNAL_SUPPRESSED, and SIGNAL_ESCALATED events.
    """

    async def get_signal_feedback(
        self,
        session: Any,
        tenant_id: str,
        signal_fingerprint: str,
    ) -> SignalFeedbackResult | None:
        """
        Query audit ledger for signal feedback status.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            signal_fingerprint: Unique fingerprint of the signal

        Returns:
            SignalFeedbackResult if feedback exists, None otherwise
        """
        # Get logs bridge (lazy import)
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge import (
            get_logs_bridge,
        )

        logs_bridge = get_logs_bridge()
        reader = logs_bridge.audit_ledger_read_capability(session)

        # Query audit ledger for signal feedback
        feedback_dict = await reader.get_signal_feedback(
            tenant_id=tenant_id,
            signal_fingerprint=signal_fingerprint,
        )

        if feedback_dict is None:
            logger.debug(
                "signal_feedback_not_found",
                extra={
                    "tenant_id": tenant_id,
                    "signal_fingerprint": signal_fingerprint,
                },
            )
            return None

        # Convert dict to SignalFeedbackResult
        result = SignalFeedbackResult(
            acknowledged=feedback_dict.get("acknowledged", False),
            acknowledged_by=feedback_dict.get("acknowledged_by"),
            acknowledged_at=self._parse_datetime(feedback_dict.get("acknowledged_at")),
            suppressed=feedback_dict.get("suppressed", False),
            suppressed_until=self._parse_datetime(feedback_dict.get("suppressed_until")),
            escalated=feedback_dict.get("escalated", False),
            escalated_at=self._parse_datetime(feedback_dict.get("escalated_at")),
        )

        logger.debug(
            "signal_feedback_found",
            extra={
                "tenant_id": tenant_id,
                "signal_fingerprint": signal_fingerprint,
                "acknowledged": result.acknowledged,
                "suppressed": result.suppressed,
                "escalated": result.escalated,
            },
        )

        return result

    def _parse_datetime(self, value: Any) -> datetime | None:
        """Parse datetime from various formats."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None


# =============================================================================
# Singleton
# =============================================================================

_instance = None


def get_signal_feedback_coordinator() -> SignalFeedbackCoordinator:
    """Get the singleton SignalFeedbackCoordinator instance."""
    global _instance
    if _instance is None:
        _instance = SignalFeedbackCoordinator()
    return _instance


__all__ = [
    "SignalFeedbackCoordinator",
    "get_signal_feedback_coordinator",
]
