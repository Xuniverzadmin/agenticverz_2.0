# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Location: hoc/cus/api_keys/L5_engines/keys_engine.py
# Temporal:
#   Trigger: api
#   Execution: sync (DB reads/writes via driver)
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: APIKey, ProxyCall (via driver)
#   Writes: APIKey (via driver)
# Role: API Keys domain engine - business logic for key operations
# Callers: customer_keys_adapter.py (L3), runtime, gateway — NOT L2
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-281, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
#
# PHASE 2.5B EXTRACTION (2026-01-24):
# This engine was created from keys_service.py to enforce L5/L6 separation.
# All DB operations are now delegated to keys_driver.py (L6).
# This engine contains only business logic (validation, decisions).
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.
#
# PRODUCT SCOPE NOTE:
# Marked system-wide because engines serve runtime/gateway (not just console).
# The facade (api_keys_facade.py) is ai-console because it's customer-facing only.
#
# GOVERNANCE NOTE:
# This L4 engine provides READ and WRITE operations for the Keys domain.
# L2 APIs MUST NOT call this directly — use APIKeysFacade instead.
# Engines are operational primitives for L3 adapters and runtime layers.

"""
Keys Engine (L4 Domain Logic)

This engine provides business logic for API key operations.
All DB access is delegated to KeysDriver (L6).

L3 (Adapter) → L4 (this engine) → L6 (Driver) → DB

Responsibilities:
- Validate key operations
- Freeze/unfreeze key decisions
- Delegate persistence to driver
- No direct exposure to L2
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional, Tuple

from app.hoc.cus.api_keys.L6_drivers.keys_driver import (
    KeysDriver,
    KeySnapshot,
    KeyUsageSnapshot,
    get_keys_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session


class KeysReadEngine:
    """
    L4 engine for API key read operations.

    Provides tenant-scoped, bounded reads for the Keys domain.
    All DB access is delegated to KeysDriver.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._driver = get_keys_driver(session)

    def list_keys(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[KeySnapshot], int]:
        """
        List API keys for a tenant.

        Args:
            tenant_id: Tenant ID (required, enforces isolation)
            limit: Page size
            offset: Pagination offset

        Returns:
            Tuple of (keys list as snapshots, total count)
        """
        keys = self._driver.fetch_keys(tenant_id, limit=limit, offset=offset)
        total = self._driver.count_keys(tenant_id)
        return keys, total

    def get_key(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[KeySnapshot]:
        """
        Get a single API key by ID with tenant isolation.

        Args:
            key_id: API Key ID
            tenant_id: Tenant ID (required, enforces isolation)

        Returns:
            KeySnapshot if found and belongs to tenant, None otherwise
        """
        return self._driver.fetch_key_by_id(key_id, tenant_id)

    def get_key_usage_today(
        self,
        key_id: str,
        today_start: datetime,
    ) -> KeyUsageSnapshot:
        """
        Get today's usage for an API key.

        Args:
            key_id: API Key ID
            today_start: Start of today (UTC)

        Returns:
            KeyUsageSnapshot with request count and spend
        """
        return self._driver.fetch_key_usage(key_id, today_start)


class KeysWriteEngine:
    """
    L4 engine for API key write operations.

    Provides tenant-scoped mutations for the Keys domain.
    All DB access is delegated to KeysDriver.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._driver = get_keys_driver(session)

    def freeze_key(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[KeySnapshot]:
        """
        Freeze an API key.

        Business logic:
        - Validates key exists and belongs to tenant
        - Sets frozen timestamp
        - Delegates persistence to driver

        Args:
            key_id: API Key ID
            tenant_id: Tenant ID (required, enforces isolation)

        Returns:
            Updated KeySnapshot, or None if key not found
        """
        # Fetch key for update (need raw model for mutation)
        key = self._driver.fetch_key_for_update(key_id, tenant_id)
        if key is None:
            return None

        # Business logic: set freeze timestamp
        frozen_at = datetime.now(timezone.utc)

        # Delegate persistence to driver
        return self._driver.update_key_frozen(key, frozen_at)

    def unfreeze_key(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[KeySnapshot]:
        """
        Unfreeze an API key.

        Business logic:
        - Validates key exists and belongs to tenant
        - Clears frozen state
        - Delegates persistence to driver

        Args:
            key_id: API Key ID
            tenant_id: Tenant ID (required, enforces isolation)

        Returns:
            Updated KeySnapshot, or None if key not found
        """
        # Fetch key for update (need raw model for mutation)
        key = self._driver.fetch_key_for_update(key_id, tenant_id)
        if key is None:
            return None

        # Delegate persistence to driver
        return self._driver.update_key_unfrozen(key)


# =============================================================================
# Factory Functions
# =============================================================================


def get_keys_read_engine(session: Session) -> KeysReadEngine:
    """Factory function to get KeysReadEngine instance."""
    return KeysReadEngine(session)


def get_keys_write_engine(session: Session) -> KeysWriteEngine:
    """Factory function to get KeysWriteEngine instance."""
    return KeysWriteEngine(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "KeysReadEngine",
    "KeysWriteEngine",
    "get_keys_read_engine",
    "get_keys_write_engine",
    # Re-export snapshots for convenience
    "KeySnapshot",
    "KeyUsageSnapshot",
]
