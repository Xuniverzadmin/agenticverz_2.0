# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Location: hoc/cus/account/L5_engines/user_write_engine.py
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L6 driver)
# Lifecycle:
#   Emits: USER_CREATED, USER_UPDATED
#   Subscribes: none
# Data Access:
#   Reads: User (via driver)
#   Writes: User (via driver)
# Role: User write operations (L5 engine over L6 driver)
# Callers: api/onboarding.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-250, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
#
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.
#
# GOVERNANCE NOTE:
# This L5 engine delegates ALL database operations to UserWriteDriver (L6).
# NO direct database access - only driver calls.
# Phase 2 extraction: DB operations moved to drivers/user_write_driver.py
#
# EXTRACTION STATUS: COMPLETE (2026-01-23)

"""
User Write Engine (L5)

DB write operations for User management.
Delegates to UserWriteDriver (L6) for all database access.

L2 (API) → L4 (this service) → L6 (UserWriteDriver)

Responsibilities:
- Delegate to L6 driver for data access
- Maintain backward compatibility for callers

Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
"""

from typing import TYPE_CHECKING, Dict, Optional

# L6 driver import (allowed)
from app.hoc.cus.account.L6_drivers.user_write_driver import (
    UserWriteDriver,
    get_user_write_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session
    from app.models.tenant import User


class UserWriteService:
    """
    DB write operations for User management.

    Delegates all operations to UserWriteDriver (L6).
    NO DIRECT DB ACCESS - driver calls only.
    """

    def __init__(self, session: "Session"):
        self._driver = get_user_write_driver(session)

    def create_user(
        self,
        email: str,
        clerk_user_id: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        status: str = "active",
    ) -> "User":
        """Delegate to driver."""
        return self._driver.create_user(
            email=email,
            clerk_user_id=clerk_user_id,
            name=name,
            avatar_url=avatar_url,
            status=status,
        )

    def update_user_login(self, user: "User") -> "User":
        """Delegate to driver."""
        return self._driver.update_user_login(user=user)

    def user_to_dict(self, user: "User") -> Dict:
        """Delegate to driver."""
        return self._driver.user_to_dict(user=user)
