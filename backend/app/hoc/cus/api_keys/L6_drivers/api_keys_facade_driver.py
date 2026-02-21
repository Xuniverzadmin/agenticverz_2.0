# capability_id: CAP-006
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: API Keys Facade Driver - Pure data access for API key queries
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: APIKey
#   Writes: none (read-only projection)
# Database:
#   Scope: domain (api_keys)
#   Models: APIKey
# Callers: api_keys_facade.py (L5)
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470
#
# PHASE 2.5B EXTRACTION (2026-01-24):
# This driver was extracted from api_keys_facade.py to enforce L5/L6 separation.
# All sqlalchemy runtime imports and model imports are now here (L6).
# The facade (L5) delegates to this driver for data access.

"""
API Keys Facade Driver (L6 Data Access)

This driver contains all database queries for the API keys facade.
It returns snapshot dataclasses to the facade (L4) for business logic composition.

ARCHITECTURAL RULE:
- This driver ONLY performs data access
- NO business logic (no status decisions, no permission checks)
- Returns raw query results as typed snapshots
- The facade composes business results from these snapshots
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# L7 model imports (allowed in L6)
from app.models.tenant import APIKey


# =============================================================================
# Snapshot Dataclasses (Driver Output)
# =============================================================================


@dataclass
class APIKeySnapshot:
    """Raw API key data from DB for list view."""

    id: str
    name: str
    key_prefix: str
    status: str
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    total_requests: int
    is_synthetic: bool


@dataclass
class APIKeyDetailSnapshot:
    """Detailed API key data from DB."""

    id: str
    name: str
    key_prefix: str
    status: str
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    total_requests: int
    permissions_json: Optional[str]
    allowed_workers_json: Optional[str]
    rate_limit_rpm: Optional[int]
    max_concurrent_runs: Optional[int]
    revoked_at: Optional[datetime]
    revoked_reason: Optional[str]


# =============================================================================
# Driver Implementation
# =============================================================================


class APIKeysFacadeDriver:
    """
    API Keys Facade Driver - Pure data access layer.

    All methods execute DB queries and return snapshot dataclasses.
    No business logic or status decisions.
    """

    async def fetch_api_keys(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[APIKeySnapshot]:
        """Fetch API keys for tenant. Excludes synthetic keys."""
        stmt = (
            select(APIKey)
            .where(APIKey.tenant_id == tenant_id)
            .where(APIKey.is_synthetic == False)  # noqa: E712
            .order_by(APIKey.created_at.desc(), APIKey.id.desc())
        )

        if status is not None:
            stmt = stmt.where(APIKey.status == status)

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        keys = result.scalars().all()

        return [
            APIKeySnapshot(
                id=key.id,
                name=key.name,
                key_prefix=key.key_prefix,
                status=key.status,
                created_at=key.created_at,
                last_used_at=key.last_used_at,
                expires_at=key.expires_at,
                total_requests=key.total_requests,
                is_synthetic=key.is_synthetic,
            )
            for key in keys
        ]

    async def count_api_keys(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: Optional[str] = None,
    ) -> int:
        """Count API keys for tenant. Excludes synthetic keys."""
        stmt = (
            select(func.count(APIKey.id))
            .where(APIKey.tenant_id == tenant_id)
            .where(APIKey.is_synthetic == False)  # noqa: E712
        )

        if status is not None:
            stmt = stmt.where(APIKey.status == status)

        result = await session.execute(stmt)
        return result.scalar() or 0

    async def fetch_api_key_by_id(
        self,
        session: AsyncSession,
        tenant_id: str,
        key_id: str,
    ) -> Optional[APIKeyDetailSnapshot]:
        """Fetch API key detail by ID. Tenant isolation enforced."""
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

        return APIKeyDetailSnapshot(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            status=key.status,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            total_requests=key.total_requests,
            permissions_json=key.permissions_json,
            allowed_workers_json=key.allowed_workers_json,
            rate_limit_rpm=key.rate_limit_rpm,
            max_concurrent_runs=key.max_concurrent_runs,
            revoked_at=key.revoked_at,
            revoked_reason=key.revoked_reason,
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Driver
    "APIKeysFacadeDriver",
    # Snapshots
    "APIKeySnapshot",
    "APIKeyDetailSnapshot",
]
