# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: DB write delegation for User management (Phase 2B extraction)
# Callers: api/onboarding.py
# Allowed Imports: L6 (models, db)
# Forbidden Imports: L2 (api), L3 (adapters)
# Reference: PIN-250 Phase 2B Batch 1

"""
User Write Service - DB write operations for User management.

Phase 2B Batch 1: Extracted from api/onboarding.py.

Constraints (enforced by PIN-250):
- Write-only: No policy logic
- No cross-service calls
- No domain refactoring
- Call-path relocation only
"""

from typing import Dict, Optional

from sqlmodel import Session

from app.houseofcards.customer.general.utils.time import utc_now
from app.models.tenant import User


class UserWriteService:
    """
    DB write operations for User management.

    Write-only facade. No policy logic, no branching beyond DB operations.
    """

    def __init__(self, session: Session):
        self.session = session

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
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_user_login(self, user: User) -> User:
        """
        Update user's last_login_at timestamp and persist.

        Args:
            user: The user to update

        Returns:
            Updated User instance
        """
        user.last_login_at = utc_now()
        user.updated_at = utc_now()
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def user_to_dict(self, user: User) -> Dict:
        """
        Convert user to dict for response.

        Note: This is a helper to avoid DetachedInstanceError when
        session closes. Extracted from onboarding.py.
        """
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "default_tenant_id": user.default_tenant_id,
            "status": user.status,
        }
