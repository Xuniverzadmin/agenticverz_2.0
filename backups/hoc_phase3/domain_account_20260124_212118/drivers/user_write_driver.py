# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Data access for user write operations
# Callers: user engines (L4)
# Allowed Imports: ORM models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
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

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlmodel import Session

from app.models.tenant import User


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


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
        self._session.commit()
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
        self._session.commit()
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
