# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (DB reads/writes)
# Role: API Keys data access operations
# Callers: keys_service.py (L4 shim), customer_keys_adapter.py (L3)
# Allowed Imports: ORM models, sqlalchemy, sqlmodel
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, PIN-281 (L3 Adapter Closure)
#
# EXTRACTION STATUS: Phase-2.5A (2026-01-24)
# - RECLASSIFIED from keys_service.py (was labeled L4, is actually L6)
# - No business logic present — pure data access
#
# ============================================================================
# L6 DRIVER INVARIANT — API KEYS (LOCKED)
# ============================================================================
# This file MUST contain ONLY data access operations.
# No business logic, no validation, no decisions.
# Any violation is a Phase-2.5 regression.
# ============================================================================

"""
Keys Driver (L6)

Pure data access for API keys.
No business logic - only DB operations.

Authority: KEY_PERSISTENCE
Tables: api_keys, proxy_calls (read-only for usage)
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlmodel import Session

from app.models.killswitch import ProxyCall
from app.models.tenant import APIKey


class KeysDriver:
    """
    L6 driver for API key data access.

    INVARIANTS (L6):
    - No business branching
    - No validation
    - No cross-domain calls
    - Pure persistence operations only
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    def fetch_keys_paginated(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[APIKey], int]:
        """
        Fetch API keys for a tenant with pagination.

        Args:
            tenant_id: Tenant ID (required, enforces isolation)
            limit: Page size
            offset: Pagination offset

        Returns:
            Tuple of (keys list, total count)
        """
        stmt = (
            select(APIKey)
            .where(APIKey.tenant_id == tenant_id)
            .order_by(desc(APIKey.created_at))
            .offset(offset)
            .limit(limit)
        )
        rows = self._session.exec(stmt).all()
        keys = [row[0] if hasattr(row, "__getitem__") else row for row in rows]

        # Get total count
        count_stmt = select(func.count(APIKey.id)).where(APIKey.tenant_id == tenant_id)
        count_row = self._session.exec(count_stmt).first()
        total = count_row[0] if count_row else 0

        return keys, total

    def fetch_key_by_id(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[APIKey]:
        """
        Fetch a single API key by ID with tenant isolation.

        Args:
            key_id: API Key ID
            tenant_id: Tenant ID (required, enforces isolation)

        Returns:
            APIKey if found and belongs to tenant, None otherwise
        """
        stmt = select(APIKey).where(
            and_(
                APIKey.id == key_id,
                APIKey.tenant_id == tenant_id,
            )
        )
        row = self._session.exec(stmt).first()
        return row[0] if row else None

    def fetch_key_usage_today(
        self,
        key_id: str,
        today_start: datetime,
    ) -> Tuple[int, int]:
        """
        Fetch today's usage for an API key.

        Args:
            key_id: API Key ID
            today_start: Start of today (UTC)

        Returns:
            Tuple of (request_count, spend_cents)
        """
        stmt = select(
            func.count(ProxyCall.id),
            func.coalesce(func.sum(ProxyCall.cost_cents), 0),
        ).where(
            and_(
                ProxyCall.api_key_id == key_id,
                ProxyCall.created_at >= today_start,
            )
        )
        row = self._session.exec(stmt).first()
        if row:
            return row[0] or 0, row[1] or 0
        return 0, 0

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    def update_key_frozen(
        self,
        key: APIKey,
        is_frozen: bool,
    ) -> APIKey:
        """
        Update the frozen status of an API key.

        Args:
            key: APIKey to update
            is_frozen: True to freeze, False to unfreeze

        Returns:
            Updated APIKey
        """
        key.is_frozen = is_frozen
        key.frozen_at = datetime.now(timezone.utc) if is_frozen else None
        self._session.add(key)
        self._session.commit()
        self._session.refresh(key)
        return key


def get_keys_driver(session: Session) -> KeysDriver:
    """Factory function for KeysDriver."""
    return KeysDriver(session)


__all__ = [
    "KeysDriver",
    "get_keys_driver",
]
