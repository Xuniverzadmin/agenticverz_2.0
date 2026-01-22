# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async (DB reads)
# Role: API Keys domain facade - unified entry point for API key operations
# Callers: L2 api-keys API (aos_api_key.py)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Connectivity Domain - Customer Console v1 Constitution
#
"""
API Keys Domain Facade (L4)

Unified facade for API key management operations.

Provides:
- List API keys (O2)
- Get API key detail (O3)

API keys are used for:
- SDK authentication
- Programmatic access to AOS APIs
- RBAC-controlled permissions
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import APIKey


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
    """

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

        # Base query - exclude synthetic keys from customer view
        stmt = (
            select(APIKey)
            .where(APIKey.tenant_id == tenant_id)
            .where(APIKey.is_synthetic == False)  # noqa: E712
            .order_by(APIKey.created_at.desc())
        )

        if status is not None:
            stmt = stmt.where(APIKey.status == status)
            filters_applied["status"] = status

        # Count total
        count_stmt = (
            select(func.count(APIKey.id))
            .where(APIKey.tenant_id == tenant_id)
            .where(APIKey.is_synthetic == False)  # noqa: E712
        )
        if status is not None:
            count_stmt = count_stmt.where(APIKey.status == status)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        keys = result.scalars().all()

        items = [
            APIKeySummaryResult(
                key_id=key.id,
                name=key.name,
                prefix=key.key_prefix,
                status=key.status.upper(),
                created_at=key.created_at,
                last_used_at=key.last_used_at,
                expires_at=key.expires_at,
                total_requests=key.total_requests,
            )
            for key in keys
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
        stmt = (
            select(APIKey)
            .where(APIKey.id == key_id)
            .where(APIKey.tenant_id == tenant_id)
            .where(APIKey.is_synthetic == False)  # noqa: E712
        )

        result = await session.execute(stmt)
        key = result.scalar_one_or_none()

        if key is None:
            return None

        # Parse JSON fields
        permissions = json.loads(key.permissions_json) if key.permissions_json else None
        allowed_workers = (
            json.loads(key.allowed_workers_json) if key.allowed_workers_json else None
        )

        return APIKeyDetailResult(
            key_id=key.id,
            name=key.name,
            prefix=key.key_prefix,
            status=key.status.upper(),
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            total_requests=key.total_requests,
            permissions=permissions,
            allowed_workers=allowed_workers,
            rate_limit_rpm=key.rate_limit_rpm,
            max_concurrent_runs=key.max_concurrent_runs,
            revoked_at=key.revoked_at,
            revoked_reason=key.revoked_reason,
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
