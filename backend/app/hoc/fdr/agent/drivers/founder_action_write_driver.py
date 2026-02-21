# capability_id: CAP-005
# Layer: L4 — Domain Engine
# Product: system-wide (Founder Console)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: DB write delegation for Founder Actions API (Phase 2B extraction)
# Callers: api/founder_actions.py
# Allowed Imports: L6 (models, db)
# Forbidden Imports: L2 (api), L3 (adapters)
# Reference: PIN-250 Phase 2B Batch 3

"""
Founder Action Write Service - DB write operations for Founder Actions API.

Phase 2B Batch 3: Extracted from api/founder_actions.py.

Constraints (enforced by PIN-250):
- Write-only: No policy logic
- No cross-service calls
- No domain refactoring
- Call-path relocation only
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlmodel import Session

from app.models.tenant import FounderAction


class FounderActionWriteService:
    """
    DB write operations for Founder Actions.

    Write-only facade. No policy logic, no branching beyond DB operations.
    """

    def __init__(self, session: Session):
        self.session = session

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
        self.session.add(action)
        self.session.flush()  # Get ID before commit
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
        self.session.execute(
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
        self.session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.session.rollback()
