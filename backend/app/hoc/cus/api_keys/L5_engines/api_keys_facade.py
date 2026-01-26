# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async (DB reads via driver)
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: APIKey (via driver)
#   Writes: none (read-only facade)
# Role: API Keys domain engine - unified entry point for API key operations
# Location: hoc/cus/api_keys/L5_engines/api_keys_facade.py
# Callers: L2 api-keys API (aos_api_key.py)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, Connectivity Domain - Customer Console v1 Constitution
#
# PHASE 2.5B EXTRACTION (2026-01-24):
# All DB operations extracted to api_keys_facade_driver.py (L6).
# This engine now delegates to driver for data access and composes business results.
#
# PHASE 3 MIGRATION (2026-01-24):
# Moved from facades/ to L5_engines/ - this is business logic, not API organization.

"""
API Keys Domain Engine (L5)

Unified facade for API key management operations.

Provides:
- List API keys (O2)
- Get API key detail (O3)

API keys are used for:
- SDK authentication
- Programmatic access to AOS APIs
- RBAC-controlled permissions

All DB access is delegated to APIKeysFacadeDriver (L6).
This facade only contains business logic composition.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from app.hoc.cus.api_keys.L6_drivers.api_keys_facade_driver import (
    APIKeysFacadeDriver,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class APIKeySummaryResult:
    """API key summary for list view."""

    key_id: str
    name: str
    prefix: str  # First 12 chars for identification (aos_xxxxxxxx)
    status: str  # ACTIVE, REVOKED, EXPIRED
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    total_requests: int


@dataclass
class APIKeysListResult:
    """API keys list response."""

    items: list[APIKeySummaryResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class APIKeyDetailResult:
    """API key detail response."""

    key_id: str
    name: str
    prefix: str
    status: str
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    total_requests: int
    # Permissions
    permissions: Optional[list[str]]
    allowed_workers: Optional[list[str]]
    # Rate limits
    rate_limit_rpm: Optional[int]
    max_concurrent_runs: Optional[int]
    # Revocation info (if revoked)
    revoked_at: Optional[datetime]
    revoked_reason: Optional[str]


# =============================================================================
# API Keys Facade
# =============================================================================


class APIKeysFacade:
    """
    Unified facade for API key management.

    Provides:
    - List API keys (O2)
    - Get API key detail (O3)

    All operations are tenant-scoped for isolation.
    Synthetic keys are excluded from customer view.

    All DB access is delegated to APIKeysFacadeDriver (L6).
    """

    def __init__(self) -> None:
        """Initialize the facade with its driver."""
        self._driver = APIKeysFacadeDriver()

    async def list_api_keys(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> APIKeysListResult:
        """List API keys for the tenant. Excludes synthetic keys."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

        if status is not None:
            filters_applied["status"] = status

        # Fetch data from driver
        key_snapshots = await self._driver.fetch_api_keys(
            session, tenant_id, status=status, limit=limit, offset=offset
        )
        total = await self._driver.count_api_keys(session, tenant_id, status=status)

        # Compose business result
        items = [
            APIKeySummaryResult(
                key_id=snap.id,
                name=snap.name,
                prefix=snap.key_prefix,
                status=snap.status.upper(),
                created_at=snap.created_at,
                last_used_at=snap.last_used_at,
                expires_at=snap.expires_at,
                total_requests=snap.total_requests,
            )
            for snap in key_snapshots
        ]

        return APIKeysListResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    async def get_api_key_detail(
        self,
        session: AsyncSession,
        tenant_id: str,
        key_id: str,
    ) -> Optional[APIKeyDetailResult]:
        """Get API key detail. Tenant isolation enforced."""
        # Fetch data from driver
        snap = await self._driver.fetch_api_key_by_id(session, tenant_id, key_id)

        if snap is None:
            return None

        # Parse JSON fields (business logic)
        permissions = json.loads(snap.permissions_json) if snap.permissions_json else None
        allowed_workers = json.loads(snap.allowed_workers_json) if snap.allowed_workers_json else None

        # Compose business result
        return APIKeyDetailResult(
            key_id=snap.id,
            name=snap.name,
            prefix=snap.key_prefix,
            status=snap.status.upper(),
            created_at=snap.created_at,
            last_used_at=snap.last_used_at,
            expires_at=snap.expires_at,
            total_requests=snap.total_requests,
            permissions=permissions,
            allowed_workers=allowed_workers,
            rate_limit_rpm=snap.rate_limit_rpm,
            max_concurrent_runs=snap.max_concurrent_runs,
            revoked_at=snap.revoked_at,
            revoked_reason=snap.revoked_reason,
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_facade_instance: APIKeysFacade | None = None


def get_api_keys_facade() -> APIKeysFacade:
    """Get the singleton APIKeysFacade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = APIKeysFacade()
    return _facade_instance


__all__ = [
    # Facade
    "APIKeysFacade",
    "get_api_keys_facade",
    # Result types
    "APIKeySummaryResult",
    "APIKeysListResult",
    "APIKeyDetailResult",
]
