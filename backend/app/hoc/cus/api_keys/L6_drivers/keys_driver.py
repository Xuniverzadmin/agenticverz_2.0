# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: Keys Driver - Pure data access for API key engine operations
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: APIKey, ProxyCall
#   Writes: APIKey (freeze, unfreeze, create, revoke)
# Database:
#   Scope: domain (api_keys)
#   Models: APIKey, ProxyCall
# Callers: keys_engine.py (L5)
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
#
# PHASE 2.5B EXTRACTION (2026-01-24):
# This driver was extracted from keys_service.py to enforce L5/L6 separation.
# All sqlalchemy/sqlmodel runtime imports and model imports are now here (L6).
# The engine (L5) delegates to this driver for data access.

"""
Keys Driver (L6 Data Access)

This driver contains all database queries and mutations for the keys engine.
It returns snapshot dataclasses to the engine (L4) for business logic.

ARCHITECTURAL RULE:
- This driver ONLY performs data access
- NO business logic (no validation, no freeze decisions)
- Returns raw query results as typed snapshots
- Accepts pre-computed values from engine for mutations
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlmodel import Session

# L7 model imports (allowed in L6)
from app.models.killswitch import ProxyCall
from app.models.tenant import APIKey


# =============================================================================
# Snapshot Dataclasses (Driver Output)
# =============================================================================


@dataclass
class KeySnapshot:
    """API key snapshot for engine operations."""

    id: str
    tenant_id: str
    name: str
    key_prefix: str
    status: str
    is_frozen: bool
    frozen_at: Optional[datetime]
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    total_requests: int


@dataclass
class KeyUsageSnapshot:
    """Key usage statistics from DB."""

    request_count: int
    spend_cents: int


# =============================================================================
# Driver Implementation
# =============================================================================


class KeysDriver:
    """
    Keys Driver - Pure data access layer.

    All methods execute DB queries/mutations and return snapshot dataclasses.
    No business logic or validation decisions.
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    # =========================================================================
    # READ Operations
    # =========================================================================

    def fetch_keys(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[KeySnapshot]:
        """Fetch API keys for a tenant."""
        stmt = (
            select(APIKey)
            .where(APIKey.tenant_id == tenant_id)
            .order_by(desc(APIKey.created_at))
            .offset(offset)
            .limit(limit)
        )
        rows = self._session.exec(stmt).all()
        keys = [row[0] if hasattr(row, "__getitem__") else row for row in rows]

        return [
            KeySnapshot(
                id=key.id,
                tenant_id=key.tenant_id,
                name=key.name,
                key_prefix=key.key_prefix,
                status=key.status,
                is_frozen=key.is_frozen,
                frozen_at=key.frozen_at,
                created_at=key.created_at,
                last_used_at=key.last_used_at,
                expires_at=key.expires_at,
                total_requests=key.total_requests,
            )
            for key in keys
        ]

    def count_keys(self, tenant_id: str) -> int:
        """Count API keys for a tenant."""
        stmt = select(func.count(APIKey.id)).where(APIKey.tenant_id == tenant_id)
        result = self._session.exec(stmt).first()
        return result[0] if result else 0

    def fetch_key_by_id(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[KeySnapshot]:
        """Fetch a single API key by ID with tenant isolation."""
        stmt = select(APIKey).where(
            and_(
                APIKey.id == key_id,
                APIKey.tenant_id == tenant_id,
            )
        )
        row = self._session.exec(stmt).first()

        if not row:
            return None

        key = row[0] if hasattr(row, "__getitem__") else row

        return KeySnapshot(
            id=key.id,
            tenant_id=key.tenant_id,
            name=key.name,
            key_prefix=key.key_prefix,
            status=key.status,
            is_frozen=key.is_frozen,
            frozen_at=key.frozen_at,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            total_requests=key.total_requests,
        )

    def fetch_key_usage(
        self,
        key_id: str,
        since: datetime,
    ) -> KeyUsageSnapshot:
        """Fetch usage statistics for an API key since a given time."""
        stmt = select(
            func.count(ProxyCall.id),
            func.coalesce(func.sum(ProxyCall.cost_cents), 0),
        ).where(
            and_(
                ProxyCall.api_key_id == key_id,
                ProxyCall.created_at >= since,
            )
        )
        row = self._session.exec(stmt).first()

        if row:
            return KeyUsageSnapshot(
                request_count=row[0] or 0,
                spend_cents=row[1] or 0,
            )
        return KeyUsageSnapshot(request_count=0, spend_cents=0)

    # =========================================================================
    # WRITE Operations
    # =========================================================================

    def fetch_key_for_update(
        self,
        key_id: str,
        tenant_id: str,
    ) -> Optional[APIKey]:
        """Fetch raw APIKey model for update operations."""
        stmt = select(APIKey).where(
            and_(
                APIKey.id == key_id,
                APIKey.tenant_id == tenant_id,
            )
        )
        row = self._session.exec(stmt).first()
        return row[0] if row and hasattr(row, "__getitem__") else row

    def update_key_frozen(
        self,
        key: APIKey,
        frozen_at: datetime,
    ) -> KeySnapshot:
        """Update key to frozen state."""
        key.is_frozen = True
        key.frozen_at = frozen_at
        self._session.add(key)
        self._session.flush()  # Get generated data, NO COMMIT — L4 owns transaction
        self._session.refresh(key)

        return KeySnapshot(
            id=key.id,
            tenant_id=key.tenant_id,
            name=key.name,
            key_prefix=key.key_prefix,
            status=key.status,
            is_frozen=key.is_frozen,
            frozen_at=key.frozen_at,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            total_requests=key.total_requests,
        )

    def update_key_unfrozen(
        self,
        key: APIKey,
    ) -> KeySnapshot:
        """Update key to unfrozen state."""
        key.is_frozen = False
        key.frozen_at = None
        self._session.add(key)
        self._session.flush()  # Get generated data, NO COMMIT — L4 owns transaction
        self._session.refresh(key)

        return KeySnapshot(
            id=key.id,
            tenant_id=key.tenant_id,
            name=key.name,
            key_prefix=key.key_prefix,
            status=key.status,
            is_frozen=key.is_frozen,
            frozen_at=key.frozen_at,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            total_requests=key.total_requests,
        )


# =============================================================================
# Factory Function
# =============================================================================


def get_keys_driver(session: Session) -> KeysDriver:
    """Factory function to get KeysDriver instance."""
    return KeysDriver(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Driver
    "KeysDriver",
    "get_keys_driver",
    "get_keys_read_driver",
    "get_keys_write_driver",
    # Snapshots
    "KeySnapshot",
    "KeyUsageSnapshot",
]

# Backward compatibility aliases (legacy names from app.services.keys_driver)
get_keys_read_driver = get_keys_driver
get_keys_write_driver = get_keys_driver
