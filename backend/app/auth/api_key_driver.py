# Layer: L6 — Driver
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: engine-call
#   Execution: sync
# Role: Data access for API key validation
# Callers: ApiKeyEngine (L4)
# Allowed Imports: sqlalchemy, sqlmodel, app.models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md, PIN-306

"""API Key Driver

L6 driver for API key data access.

Pure persistence - no business logic.
Returns raw facts: key data, validity status, usage counts.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.db import engine as default_engine
from app.models.tenant import APIKey


@dataclass(frozen=True)
class KeyRow:
    """Immutable API key data for validation."""

    id: str
    name: str
    key_prefix: str
    tenant_id: str
    user_id: Optional[str]
    status: str
    permissions_json: Optional[str]
    rate_limit_rpm: Optional[int]
    is_valid: bool
    created_at: Optional[datetime]
    last_used_at: Optional[datetime]
    total_requests: int
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    revoked_reason: Optional[str]


class ApiKeyDriver:
    """L6 driver for API key data access.

    Pure persistence - no business logic.
    Returns raw facts for engine to interpret.
    """

    def __init__(self, engine=None):
        """Initialize driver with database engine.

        Args:
            engine: SQLAlchemy engine (uses default if not provided)
        """
        self._engine = engine or default_engine

    # =========================================================================
    # FETCH OPERATIONS
    # =========================================================================

    def fetch_key_by_hash(self, key_hash: str) -> Optional[KeyRow]:
        """Fetch API key by its hash.

        Args:
            key_hash: SHA256 hash of the API key

        Returns:
            KeyRow if found, None otherwise
        """
        with Session(self._engine) as session:
            statement = select(APIKey).where(APIKey.key_hash == key_hash)
            api_key = session.exec(statement).first()

            if api_key is None:
                return None

            return KeyRow(
                id=str(api_key.id),
                name=api_key.name,
                key_prefix=api_key.key_prefix,
                tenant_id=api_key.tenant_id,
                user_id=api_key.user_id,
                status=api_key.status,
                permissions_json=api_key.permissions_json,
                rate_limit_rpm=api_key.rate_limit_rpm,
                is_valid=api_key.is_valid(),
                created_at=api_key.created_at,
                last_used_at=api_key.last_used_at,
                total_requests=api_key.total_requests or 0,
                expires_at=api_key.expires_at,
                revoked_at=api_key.revoked_at,
                revoked_reason=api_key.revoked_reason,
            )

    def fetch_key_by_id(self, key_id: str) -> Optional[KeyRow]:
        """Fetch API key by ID.

        Args:
            key_id: The key ID

        Returns:
            KeyRow if found, None otherwise
        """
        with Session(self._engine) as session:
            statement = select(APIKey).where(APIKey.id == key_id)
            api_key = session.exec(statement).first()

            if api_key is None:
                return None

            return KeyRow(
                id=str(api_key.id),
                name=api_key.name,
                key_prefix=api_key.key_prefix,
                tenant_id=api_key.tenant_id,
                user_id=api_key.user_id,
                status=api_key.status,
                permissions_json=api_key.permissions_json,
                rate_limit_rpm=api_key.rate_limit_rpm,
                is_valid=api_key.is_valid(),
                created_at=api_key.created_at,
                last_used_at=api_key.last_used_at,
                total_requests=api_key.total_requests or 0,
                expires_at=api_key.expires_at,
                revoked_at=api_key.revoked_at,
                revoked_reason=api_key.revoked_reason,
            )

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    def record_usage(self, key_hash: str) -> bool:
        """Record API key usage.

        Args:
            key_hash: SHA256 hash of the API key

        Returns:
            True if recorded, False if key not found
        """
        with Session(self._engine) as session:
            statement = select(APIKey).where(APIKey.key_hash == key_hash)
            api_key = session.exec(statement).first()

            if api_key is None:
                return False

            api_key.record_usage()
            session.add(api_key)
            session.commit()
            return True

    def revoke_key(self, key_id: str, reason: str) -> bool:
        """Revoke an API key.

        Args:
            key_id: The key ID to revoke
            reason: Reason for revocation

        Returns:
            True if revoked, False if key not found
        """
        with Session(self._engine) as session:
            statement = select(APIKey).where(APIKey.id == key_id)
            api_key = session.exec(statement).first()

            if api_key is None:
                return False

            api_key.status = "revoked"
            api_key.revoked_at = datetime.utcnow()
            api_key.revoked_reason = reason[:255] if reason else None

            session.add(api_key)
            session.commit()
            return True


# Factory function
def get_api_key_driver(engine=None) -> ApiKeyDriver:
    """Get driver instance.

    Args:
        engine: Optional SQLAlchemy engine

    Returns:
        ApiKeyDriver instance
    """
    return ApiKeyDriver(engine=engine)
