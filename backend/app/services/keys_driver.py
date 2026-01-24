# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (DB reads/writes)
# Role: API Keys data access driver
# Callers: customer_keys_adapter.py (L3)
# Allowed Imports: ORM models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468 (Phase 2 Step 2 - L4/L6 Segregation)
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for API Keys.
# NO business logic - only DB operations.
#
# RECLASSIFICATION: 2026-01-23
# Previously: keys_service.py (mislabeled as L4 engine)
# Reason: 0 decisions, 100% persistence = pure driver

"""
Keys Driver (L6)

Pure database operations for API Keys domain.

L3 (Adapter) → L6 (this driver)

Responsibilities:
- Query API keys with tenant isolation
- Freeze/unfreeze keys (persistence only)
- Get key usage statistics
- NO business logic (L4 responsibility)

Reference: PIN-468 (Phase 2 Step 2)
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlmodel import Session

from app.models.killswitch import ProxyCall
from app.models.tenant import APIKey


class KeysReadDriver:
    """
    L6 driver for API key read operations.

    Pure database access - no business logic.
    """

    def __init__(self, session: Session):
        self._session = session

    def list_keys(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[APIKey], int]:
        """
        List API keys for a tenant.

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

        count_stmt = select(func.count(APIKey.id)).where(APIKey.tenant_id == tenant_id)
        count_row = self._session.exec(count_stmt).first()
        total = count_row[0] if count_row else 0

        return keys, total

    def get_key(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[APIKey]:
        """
        Get a single API key by ID with tenant isolation.

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

    def get_key_usage_today(
        self,
        key_id: str,
        today_start: datetime,
    ) -> Tuple[int, int]:
        """
        Get today's usage for an API key.

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


class KeysWriteDriver:
    """
    L6 driver for API key write operations.

    Pure database access - no business logic.
    """

    def __init__(self, session: Session):
        self._session = session

    def freeze_key(self, key: APIKey) -> APIKey:
        """
        Freeze an API key and persist.

        Args:
            key: APIKey to freeze

        Returns:
            Updated APIKey
        """
        key.is_frozen = True
        key.frozen_at = datetime.now(timezone.utc)
        self._session.add(key)
        self._session.commit()
        self._session.refresh(key)
        return key

    def unfreeze_key(self, key: APIKey) -> APIKey:
        """
        Unfreeze an API key and persist.

        Args:
            key: APIKey to unfreeze

        Returns:
            Updated APIKey
        """
        key.is_frozen = False
        key.frozen_at = None
        self._session.add(key)
        self._session.commit()
        self._session.refresh(key)
        return key


def get_keys_read_driver(session: Session) -> KeysReadDriver:
    """Factory function to get KeysReadDriver instance."""
    return KeysReadDriver(session)


def get_keys_write_driver(session: Session) -> KeysWriteDriver:
    """Factory function to get KeysWriteDriver instance."""
    return KeysWriteDriver(session)


# Backward compatibility aliases (DEPRECATED - remove after migration)
KeysReadService = KeysReadDriver
KeysWriteService = KeysWriteDriver
get_keys_read_service = get_keys_read_driver
get_keys_write_service = get_keys_write_driver


__all__ = [
    "KeysReadDriver",
    "KeysWriteDriver",
    "get_keys_read_driver",
    "get_keys_write_driver",
    # Deprecated aliases
    "KeysReadService",
    "KeysWriteService",
    "get_keys_read_service",
    "get_keys_write_service",
]
