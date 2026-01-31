# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: User
#   Writes: User (create, update)
# Database:
#   Scope: domain (account)
#   Models: User
# Role: Data access for user write operations
# Callers: user_write_engine.py (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for user writes.
# NO business logic - only DB operations.
#
# EXTRACTION STATUS: RECLASSIFIED (2026-01-23)

"""
User Write Driver (L6)

Pure database write operations for User management.

L4 (UserWriteService) → L6 (this driver)

Responsibilities:
- Create user records
- Update user login timestamps
- Convert user to dict (DTO transformation)
- NO business logic (L4 responsibility)

Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
"""

from typing import Dict, Optional

from sqlmodel import Session

from app.hoc.hoc_spine.services.time import utc_now
from app.models.tenant import User


class UserWriteDriver:
    """
    L6 driver for user write operations.

    Pure database access - no business logic.
    """

    def __init__(self, session: Session):
        self._session = session

    def create_user(
        self,
        email: str,
        clerk_user_id: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        status: str = "active",
    ) -> User:
        """
        Create a new user and persist.

        Args:
            email: User email
            clerk_user_id: External auth provider ID
            name: User display name
            avatar_url: User avatar URL
            status: User status (default: active)

        Returns:
            Created User instance
        """
        user = User(
            email=email,
            name=name,
            avatar_url=avatar_url,
            clerk_user_id=clerk_user_id,
            status=status,
        )
        self._session.add(user)
        self._session.flush()  # Get generated ID, NO COMMIT — L4 owns transaction
        self._session.refresh(user)
        return user

    def update_user_login(self, user: User) -> User:
        """
        Update user's last_login_at timestamp and persist.

        Args:
            user: The user to update

        Returns:
            Updated User instance
        """
        now = utc_now()
        user.last_login_at = now
        user.updated_at = now
        self._session.add(user)
        self._session.flush()  # Get updated data, NO COMMIT — L4 owns transaction
        self._session.refresh(user)
        return user

    def user_to_dict(self, user: User) -> Dict:
        """
        Convert user to dict for response.

        Note: This is a helper to avoid DetachedInstanceError when
        session closes. Pure DTO transformation.
        """
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "default_tenant_id": user.default_tenant_id,
            "status": user.status,
        }


def get_user_write_driver(session: Session) -> UserWriteDriver:
    """Factory function to get UserWriteDriver instance."""
    return UserWriteDriver(session)


__all__ = [
    "UserWriteDriver",
    "get_user_write_driver",
]
