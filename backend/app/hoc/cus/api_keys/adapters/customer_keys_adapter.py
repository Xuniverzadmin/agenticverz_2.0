# Layer: L2 — Adapter
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L4)
# Role: Customer API keys boundary adapter (L2 → L4)
# Callers: guard.py (L2) — to be wired
# Allowed Imports: L4
# Forbidden Imports: L1, L2, L5, L6
# Reference: PIN-280, PIN-281 (L2 Promotion Governance - PHASE 1 Adapter Closure)
#
# GOVERNANCE NOTE:
# This adapter is TRANSLATION ONLY. It enforces:
# - Tenant scoping (customer can only see their own API keys)
# - Customer-safe schema (no full key value exposed)
# - Key status management (freeze/unfreeze)

"""
Customer Keys Adapter (L2)

This adapter sits between L2 (guard.py API) and L4 (services).

L2 (Guard API) → L4 (KeysReadService/KeysWriteService)

The adapter:
1. Receives API requests with tenant context
2. Enforces tenant isolation
3. Transforms to customer-safe schema (prefix only, no full key)
4. Delegates to L4 services (no L6 access)

Reference: PIN-280 (L2 Promotion Governance), PIN-281 (PHASE 1 Adapter Closure)
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Session

# L5 engine imports (migrated to HOC per SWEEP-03)
from app.hoc.cus.api_keys.L5_engines.keys_engine import (
    get_keys_read_engine as get_keys_read_service,
    get_keys_write_engine as get_keys_write_service,
)

# =============================================================================
# Customer-Safe DTOs (No Full Key Value)
# =============================================================================


class CustomerKeyInfo(BaseModel):
    """Customer-safe API key information."""

    id: str
    name: str
    prefix: str  # First 8 chars only, never full key
    status: str  # active, frozen
    created_at: str
    last_seen_at: Optional[str] = None
    requests_today: int
    spend_today_cents: int
    # No full key value exposed


class CustomerKeyListResponse(BaseModel):
    """Customer key list response."""

    items: List[CustomerKeyInfo]
    total: int


class CustomerKeyAction(BaseModel):
    """Result of a key action (freeze/unfreeze)."""

    id: str
    name: str
    status: str
    message: str


# =============================================================================
# Adapter Class
# =============================================================================


class CustomerKeysAdapter:
    """
    Boundary adapter for customer API key operations.

    This class provides the ONLY interface that L2 (guard.py) may use
    to access API key functionality. It enforces tenant isolation and
    transforms data to customer-safe schemas.

    PIN-280 Rule: Adapter Is Translation Only + Tenant Scoping
    PIN-281 Rule: Adapter imports L4 only (no L6 direct access)
    """

    def __init__(self, session: Session):
        """Initialize adapter with database session."""
        self._session = session
        self._read_service = get_keys_read_service(session)
        self._write_service = get_keys_write_service(session)

    def list_keys(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> CustomerKeyListResponse:
        """
        List API keys for a customer.

        Enforces tenant isolation - customer can only see their own keys.

        Args:
            tenant_id: Customer's tenant ID (REQUIRED, enforced)
            limit: Page size
            offset: Pagination offset

        Returns:
            CustomerKeyListResponse with customer-safe key info
        """
        # L2 → L4 delegation
        keys, total = self._read_service.list_keys(tenant_id, limit, offset)

        # Get today's start for usage stats
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        items = []
        for key in keys:
            # Get today's usage for this key via L4 service
            requests_today, spend_today = self._read_service.get_key_usage_today(key.id, today_start)

            # Determine status
            status = "frozen" if getattr(key, "is_frozen", False) else "active"

            items.append(
                CustomerKeyInfo(
                    id=key.id,
                    name=key.name or f"Key {key.id[:8]}",
                    prefix=key.key_hash[:8] if hasattr(key, "key_hash") and key.key_hash else key.id[:8],
                    status=status,
                    created_at=key.created_at.isoformat() if key.created_at else "",
                    last_seen_at=key.last_used_at.isoformat() if getattr(key, "last_used_at", None) else None,
                    requests_today=requests_today,
                    spend_today_cents=int(spend_today),
                )
            )

        return CustomerKeyListResponse(
            items=items,
            total=total,
        )

    def get_key(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[CustomerKeyInfo]:
        """
        Get API key detail.

        Enforces tenant isolation - returns None if key belongs to different tenant.

        Args:
            key_id: API Key ID
            tenant_id: Customer's tenant ID (REQUIRED, enforced)

        Returns:
            CustomerKeyInfo if found and authorized, None otherwise
        """
        # L2 → L4 delegation
        key = self._read_service.get_key(key_id, tenant_id)

        if key is None:
            return None

        # Get today's usage via L4 service
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        requests_today, spend_today = self._read_service.get_key_usage_today(key.id, today_start)

        status = "frozen" if getattr(key, "is_frozen", False) else "active"

        return CustomerKeyInfo(
            id=key.id,
            name=key.name or f"Key {key.id[:8]}",
            prefix=key.key_hash[:8] if hasattr(key, "key_hash") and key.key_hash else key.id[:8],
            status=status,
            created_at=key.created_at.isoformat() if key.created_at else "",
            last_seen_at=key.last_used_at.isoformat() if getattr(key, "last_used_at", None) else None,
            requests_today=requests_today,
            spend_today_cents=int(spend_today),
        )

    def freeze_key(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[CustomerKeyAction]:
        """
        Freeze an API key.

        Args:
            key_id: API Key ID
            tenant_id: Customer's tenant ID (REQUIRED, enforced)

        Returns:
            CustomerKeyAction if found and authorized, None otherwise
        """
        # L2 → L4 delegation for read
        key = self._read_service.get_key(key_id, tenant_id)

        if key is None:
            return None

        # Check if already frozen
        if getattr(key, "is_frozen", False):
            return CustomerKeyAction(
                id=key.id,
                name=key.name or f"Key {key.id[:8]}",
                status="frozen",
                message="Key is already frozen",
            )

        # L2 → L4 delegation for write
        key = self._write_service.freeze_key(key)

        return CustomerKeyAction(
            id=key.id,
            name=key.name or f"Key {key.id[:8]}",
            status="frozen",
            message="Key has been frozen. All requests using this key will be blocked.",
        )

    def unfreeze_key(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[CustomerKeyAction]:
        """
        Unfreeze an API key.

        Args:
            key_id: API Key ID
            tenant_id: Customer's tenant ID (REQUIRED, enforced)

        Returns:
            CustomerKeyAction if found and authorized, None otherwise
        """
        # L2 → L4 delegation for read
        key = self._read_service.get_key(key_id, tenant_id)

        if key is None:
            return None

        # Check if not frozen
        if not getattr(key, "is_frozen", False):
            return CustomerKeyAction(
                id=key.id,
                name=key.name or f"Key {key.id[:8]}",
                status="active",
                message="Key is not frozen",
            )

        # L2 → L4 delegation for write
        key = self._write_service.unfreeze_key(key)

        return CustomerKeyAction(
            id=key.id,
            name=key.name or f"Key {key.id[:8]}",
            status="active",
            message="Key has been unfrozen. Requests will now be processed normally.",
        )


# =============================================================================
# Factory
# =============================================================================


def get_customer_keys_adapter(session: Session) -> CustomerKeysAdapter:
    """
    Get a CustomerKeysAdapter instance.

    Args:
        session: Database session

    Returns:
        CustomerKeysAdapter instance
    """
    return CustomerKeysAdapter(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CustomerKeysAdapter",
    "get_customer_keys_adapter",
    # DTOs for L2 convenience
    "CustomerKeyInfo",
    "CustomerKeyListResponse",
    "CustomerKeyAction",
]
