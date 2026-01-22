# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (DB reads/writes)
# Role: API Keys domain operations (L4)
# Callers: customer_keys_adapter.py (L3), runtime, gateway — NOT L2
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-281 (L3 Adapter Closure - PHASE 1)
#
# PRODUCT SCOPE NOTE:
# Marked system-wide because engines serve runtime/gateway (not just console).
# The facade (api_keys_facade.py) is ai-console because it's customer-facing only.
# See api_keys/__init__.py for full domain contract.
#
# GOVERNANCE NOTE:
# This L4 service provides READ and WRITE operations for the Keys domain.
# L2 APIs MUST NOT call this directly — use APIKeysFacade instead.
# Engines are operational primitives for L3 adapters and runtime layers.

"""
Keys Service (L4)

This service provides all operations for the API Keys domain.
It sits between L3 (CustomerKeysAdapter) and L6 (Database).

L3 (Adapter) → L4 (this service) → L6 (Database)

Responsibilities:
- Query API keys with tenant isolation
- Freeze/unfreeze keys
- Get key usage statistics
- No direct exposure to L2

Reference: PIN-281 (L3 Adapter Closure - PHASE 1)
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlmodel import Session

# L6 imports (allowed)
from app.models.killswitch import ProxyCall
from app.models.tenant import APIKey


class KeysReadService:
    """
    L4 service for API key read operations.

    Provides tenant-scoped, bounded reads for the Keys domain.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
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
        # Query keys with tenant isolation
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


class KeysWriteService:
    """
    L4 service for API key write operations.

    Provides tenant-scoped mutations for the Keys domain.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    def freeze_key(
        self,
        key: APIKey,
    ) -> APIKey:
        """
        Freeze an API key.

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

    def unfreeze_key(
        self,
        key: APIKey,
    ) -> APIKey:
        """
        Unfreeze an API key.

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


def get_keys_read_service(session: Session) -> KeysReadService:
    """Factory function to get KeysReadService instance."""
    return KeysReadService(session)


def get_keys_write_service(session: Session) -> KeysWriteService:
    """Factory function to get KeysWriteService instance."""
    return KeysWriteService(session)


__all__ = [
    "KeysReadService",
    "KeysWriteService",
    "get_keys_read_service",
    "get_keys_write_service",
]
