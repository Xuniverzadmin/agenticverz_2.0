# Layer: L6 — Driver
# AUDIENCE: FOUNDER
# Role: Data access for founder action write operations
# Callers: founder action engines (L4)
# Allowed Imports: ORM models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for founder action writes.
# NO business logic - only DB operations.
#
# EXTRACTION STATUS: RECLASSIFIED (2026-01-23)

"""
Founder Action Write Driver (L6)

Pure database write operations for Founder Actions.

L4 (FounderActionWriteService) → L6 (this driver)

Responsibilities:
- Persist FounderAction records
- Update reversal status
- NO business logic (L4 responsibility)

Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlmodel import Session

from app.models.tenant import FounderAction


class FounderActionWriteDriver:
    """
    L6 driver for founder action write operations.

    Pure database access - no business logic.
    """

    def __init__(self, session: Session):
        self._session = session

    def create_founder_action(
        self,
        action_type: str,
        target_type: str,
        target_id: str,
        target_name: Optional[str],
        reason_code: str,
        reason_note: Optional[str],
        source_incident_id: Optional[str],
        founder_id: str,
        founder_email: str,
        mfa_verified: bool,
        is_reversible: bool,
    ) -> FounderAction:
        """
        Create a new founder action record and persist.

        Args:
            action_type: Type of action (FREEZE_TENANT, etc.)
            target_type: Target type (TENANT, API_KEY, etc.)
            target_id: Target ID
            target_name: Human-readable target name
            reason_code: Reason code
            reason_note: Optional reason note
            source_incident_id: Optional source incident ID
            founder_id: Founder user ID
            founder_email: Founder email
            mfa_verified: Whether MFA was verified
            is_reversible: Whether action is reversible

        Returns:
            Created FounderAction instance (with ID assigned via flush)
        """
        action = FounderAction(
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            reason_code=reason_code,
            reason_note=reason_note,
            source_incident_id=source_incident_id,
            founder_id=founder_id,
            founder_email=founder_email,
            mfa_verified=mfa_verified,
            is_reversible=is_reversible,
        )
        self._session.add(action)
        self._session.flush()  # Get ID before commit
        return action

    def mark_action_reversed(
        self,
        action_id: str,
        reversed_at: datetime,
        reversed_by_action_id: str,
    ) -> None:
        """
        Mark an original action as reversed.

        Args:
            action_id: ID of the action to mark as reversed
            reversed_at: Timestamp of reversal
            reversed_by_action_id: ID of the reversal action
        """
        self._session.execute(
            text(
                """
                UPDATE founder_actions
                SET is_active = false,
                    reversed_at = :now,
                    reversed_by_action_id = :reversal_id
                WHERE id = :action_id
            """
            ),
            {
                "now": reversed_at,
                "reversal_id": reversed_by_action_id,
                "action_id": action_id,
            },
        )

    def commit(self) -> None:
        """Commit the current transaction."""
        self._session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._session.rollback()


def get_founder_action_write_driver(session: Session) -> FounderActionWriteDriver:
    """Factory function to get FounderActionWriteDriver instance."""
    return FounderActionWriteDriver(session)


__all__ = [
    "FounderActionWriteDriver",
    "get_founder_action_write_driver",
]
