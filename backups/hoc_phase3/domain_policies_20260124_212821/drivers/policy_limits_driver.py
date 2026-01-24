# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: Data access for policy limits CRUD operations
# Callers: policy_limits_service.py (L4 engine)
# Allowed Imports: ORM models, sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, POLICIES_DOMAIN_LOCK.md
#
# EXTRACTION STATUS: Phase-2.5A (2026-01-24)
# - Created from policy_limits_service.py extraction
# - All DB operations moved here
# - Engine contains ONLY decision logic
#
# ============================================================================
# L6 DRIVER INVARIANT — POLICY LIMITS (LOCKED)
# ============================================================================
# This file MUST contain ONLY data access operations.
# No business logic, no validation, no decisions.
# Any violation is a Phase-2.5 regression.
# ============================================================================

"""
Policy Limits Driver

Pure data access for policy limits table.
No business logic - only DB operations.

Authority: LIMIT_PERSISTENCE
Tables: limits, limit_integrity
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.models.policy_control_plane import Limit, LimitIntegrity


class PolicyLimitsDriver:
    """
    Data access driver for policy limits.

    INVARIANTS (L6):
    - No business branching
    - No validation
    - No cross-domain calls
    - Pure persistence operations only
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_limit_by_id(
        self,
        tenant_id: str,
        limit_id: str,
    ) -> Optional["Limit"]:
        """
        Fetch a limit by ID with tenant scope.

        Args:
            tenant_id: Tenant scope
            limit_id: Limit to fetch

        Returns:
            Limit if found, None otherwise
        """
        from app.models.policy_control_plane import Limit

        stmt = select(Limit).where(
            Limit.id == limit_id,
            Limit.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def add_limit(self, limit: "Limit") -> None:
        """
        Add a limit to the session.

        Args:
            limit: Limit to add
        """
        self._session.add(limit)

    def add_integrity(self, integrity: "LimitIntegrity") -> None:
        """
        Add an integrity record to the session.

        Args:
            integrity: Integrity record to add
        """
        self._session.add(integrity)

    async def flush(self) -> None:
        """Flush pending changes without committing."""
        await self._session.flush()


def get_policy_limits_driver(session: AsyncSession) -> PolicyLimitsDriver:
    """Factory function for PolicyLimitsDriver."""
    return PolicyLimitsDriver(session)
