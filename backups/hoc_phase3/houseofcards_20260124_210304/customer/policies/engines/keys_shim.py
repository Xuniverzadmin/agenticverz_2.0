# Layer: L4 — Domain Engine (DEPRECATED SHIM)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: API Keys domain operations — delegates to L6 driver
# Status: DEPRECATED — Phase-2.5A reclassification
#
# MIGRATION PATH:
#   Current:  from app.houseofcards.customer.policies.engines.keys_shim import KeysReadService
#   Future:   from app.houseofcards.customer.policies.drivers.keys_driver import KeysDriver
#
# NOTE: Renamed keys_service.py → keys_shim.py (2026-01-24) - BANNED_NAMING fix
# This shim exists for backward compatibility during Phase-2.5A.
# Delete when all callers are updated to use KeysDriver directly.
# Reference: PIN-468, PIN-281
#
# RECLASSIFICATION NOTE:
# This file was originally classified as L4, but contained only L6 operations.
# All logic has been moved to keys_driver.py.
#
# ============================================================================
# L4 ENGINE INVARIANT — KEYS (SHIM ONLY)
# ============================================================================
# This file MUST NOT contain any new logic.
# It exists only to preserve backward compatibility.
# All operations delegate to keys_driver.py.
# ============================================================================

"""
Keys Service (L4) — DEPRECATED SHIM

This service delegates all operations to KeysDriver.
Maintained for backward compatibility with existing callers.

Use KeysDriver directly for new code.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple

# L6 driver import (allowed)
from app.houseofcards.customer.policies.drivers.keys_driver import (
    KeysDriver,
    get_keys_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session

from app.models.tenant import APIKey


class KeysReadService:
    """
    L4 service for API key read operations.

    DEPRECATED: Use KeysDriver directly.
    This class delegates all operations to KeysDriver.
    """

    def __init__(self, session: "Session"):
        """Initialize with database session."""
        self._driver = get_keys_driver(session)

    def list_keys(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[APIKey], int]:
        """
        List API keys for a tenant.

        Delegates to KeysDriver.fetch_keys_paginated().
        """
        return self._driver.fetch_keys_paginated(tenant_id, limit, offset)

    def get_key(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[APIKey]:
        """
        Get a single API key by ID with tenant isolation.

        Delegates to KeysDriver.fetch_key_by_id().
        """
        return self._driver.fetch_key_by_id(key_id, tenant_id)

    def get_key_usage_today(
        self,
        key_id: str,
        today_start: datetime,
    ) -> Tuple[int, int]:
        """
        Get today's usage for an API key.

        Delegates to KeysDriver.fetch_key_usage_today().
        """
        return self._driver.fetch_key_usage_today(key_id, today_start)


class KeysWriteService:
    """
    L4 service for API key write operations.

    DEPRECATED: Use KeysDriver directly.
    This class delegates all operations to KeysDriver.
    """

    def __init__(self, session: "Session"):
        """Initialize with database session."""
        self._driver = get_keys_driver(session)

    def freeze_key(
        self,
        key: APIKey,
    ) -> APIKey:
        """
        Freeze an API key.

        Delegates to KeysDriver.update_key_frozen().
        """
        return self._driver.update_key_frozen(key, is_frozen=True)

    def unfreeze_key(
        self,
        key: APIKey,
    ) -> APIKey:
        """
        Unfreeze an API key.

        Delegates to KeysDriver.update_key_frozen().
        """
        return self._driver.update_key_frozen(key, is_frozen=False)


def get_keys_read_service(session: "Session") -> KeysReadService:
    """Factory function to get KeysReadService instance."""
    return KeysReadService(session)


def get_keys_write_service(session: "Session") -> KeysWriteService:
    """Factory function to get KeysWriteService instance."""
    return KeysWriteService(session)


__all__ = [
    "KeysReadService",
    "KeysWriteService",
    "get_keys_read_service",
    "get_keys_write_service",
]
