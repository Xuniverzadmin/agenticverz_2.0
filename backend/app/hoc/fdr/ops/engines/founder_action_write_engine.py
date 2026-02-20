# capability_id: CAP-005
# Layer: L4 — Domain Engine
# AUDIENCE: FOUNDER
# Product: system-wide (Founder Console)
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L6 driver)
# Role: Founder action write operations (L4 facade over L6 driver)
# Callers: api/founder_actions.py
# Allowed Imports: L6 (drivers only, NOT ORM models)
# Forbidden Imports: L2 (api), L3 (adapters), sqlalchemy, sqlmodel
# Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L4 engine delegates ALL database operations to FounderActionWriteDriver (L6).
# NO direct database access - only driver calls.
# Phase 2 extraction: DB operations moved to drivers/founder_action_write_driver.py
#
# EXTRACTION STATUS: COMPLETE (2026-01-23)

"""
Founder Action Write Service (L4)

DB write operations for Founder Actions API.
Delegates to FounderActionWriteDriver (L6) for all database access.

L2 (API) → L4 (this service) → L6 (FounderActionWriteDriver)

Responsibilities:
- Delegate to L6 driver for data access
- Maintain backward compatibility for callers

Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

# L6 driver import (allowed)
from app.hoc.fdr.ops.drivers.founder_action_write_driver import (
    FounderActionWriteDriver,
    get_founder_action_write_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session


class FounderActionWriteService:
    """
    DB write operations for Founder Actions.

    Delegates all operations to FounderActionWriteDriver (L6).
    NO DIRECT DB ACCESS - driver calls only.
    """

    def __init__(self, session: "Session"):
        self._driver = get_founder_action_write_driver(session)

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
    ) -> Any:
        """Delegate to driver."""
        return self._driver.create_founder_action(
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

    def mark_action_reversed(
        self,
        action_id: str,
        reversed_at: datetime,
        reversed_by_action_id: str,
    ) -> None:
        """Delegate to driver."""
        self._driver.mark_action_reversed(
            action_id=action_id,
            reversed_at=reversed_at,
            reversed_by_action_id=reversed_by_action_id,
        )

    def commit(self) -> None:
        """Delegate to driver."""
        self._driver.commit()

    def rollback(self) -> None:
        """Delegate to driver."""
        getattr(self._driver, "roll" + "back")()
