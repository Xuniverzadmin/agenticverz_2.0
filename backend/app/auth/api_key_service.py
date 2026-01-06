# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: API key validation service for machine authentication
# Callers: AuthGateway
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-306 (Capability Registry), CAP-006 (Authentication)
# capability_id: CAP-006

"""
API Key Validation Service

Validates API keys against the database and returns key metadata.
Used by the AuthGateway for machine authentication flow.

INVARIANTS:
1. Keys are validated by hash comparison (never plaintext storage)
2. Revoked/expired keys are rejected immediately
3. Key usage is recorded for audit trail
4. Scopes are extracted from key permissions
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("nova.auth.api_key_service")


class ApiKeyService:
    """
    API key validation and lookup service.

    Validates keys against the database and returns metadata
    for the AuthGateway to create MachineCapabilityContext.

    Usage:
        service = ApiKeyService()
        key_info = await service.validate_key("aos_xxxxx")

        if key_info:
            # key_info contains: key_id, tenant_id, scopes, rate_limit
            pass
    """

    def __init__(self, engine=None):
        """
        Initialize API key service.

        Args:
            engine: SQLAlchemy engine (lazy-loaded if not provided)
        """
        self._engine = engine

    def _get_engine(self):
        """Get or create database engine."""
        if self._engine is None:
            from ..db import engine

            self._engine = engine
        return self._engine

    async def validate_key(self, api_key: str) -> Optional[dict]:
        """
        Validate an API key and return its metadata.

        Args:
            api_key: The full API key string (e.g., "aos_xxxxx")

        Returns:
            Dictionary with key metadata if valid:
            {
                "key_id": str,
                "key_name": str,
                "tenant_id": str,
                "scopes": list[str],
                "rate_limit": int,
                "revoked": bool,
            }
            Returns None if key is invalid or not found.
        """
        if not api_key:
            return None

        # Hash the key for lookup
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        try:
            # Run database query
            return await self._lookup_key_by_hash(key_hash)
        except Exception as e:
            logger.error(f"API key lookup failed: {e}")
            return None

    async def _lookup_key_by_hash(self, key_hash: str) -> Optional[dict]:
        """
        Look up API key by its hash.

        This is an async wrapper around the synchronous database query.
        In production, this should use an async database session.
        """
        import asyncio

        # Run sync DB operation in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_lookup_key, key_hash)

    def _sync_lookup_key(self, key_hash: str) -> Optional[dict]:
        """
        Synchronous key lookup.

        Called from thread pool by async wrapper.
        """
        from sqlmodel import Session, select

        from ..models.tenant import APIKey

        engine = self._get_engine()

        with Session(engine) as session:
            # Find key by hash
            statement = select(APIKey).where(APIKey.key_hash == key_hash)
            api_key = session.exec(statement).first()

            if api_key is None:
                return None

            # Check validity
            if not api_key.is_valid():
                return {
                    "key_id": api_key.id,
                    "key_name": api_key.name,
                    "tenant_id": api_key.tenant_id,
                    "scopes": [],
                    "rate_limit": 0,
                    "revoked": True,
                }

            # Parse scopes from permissions JSON
            scopes = self._parse_scopes(api_key.permissions_json)

            # Get rate limit (per-key override or default)
            rate_limit = api_key.rate_limit_rpm or 1000

            # Record usage
            api_key.record_usage()
            session.add(api_key)
            session.commit()

            return {
                "key_id": api_key.id,
                "key_name": api_key.name,
                "tenant_id": api_key.tenant_id,
                "scopes": scopes,
                "rate_limit": rate_limit,
                "revoked": False,
            }

    def _parse_scopes(self, permissions_json: Optional[str]) -> list[str]:
        """
        Parse scopes from permissions JSON.

        Permissions are stored as JSON array: ["run:*", "read:*"]
        If None or invalid, return default full access scope.
        """
        if not permissions_json:
            return ["*"]  # Default full access

        try:
            scopes = json.loads(permissions_json)
            if isinstance(scopes, list):
                return scopes
            return ["*"]
        except json.JSONDecodeError:
            return ["*"]

    async def revoke_key(self, key_id: str, reason: str = "") -> bool:
        """
        Revoke an API key.

        Args:
            key_id: The key ID to revoke
            reason: Reason for revocation (for audit)

        Returns:
            True if key was revoked, False if not found.
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_revoke_key, key_id, reason)

    def _sync_revoke_key(self, key_id: str, reason: str) -> bool:
        """Synchronous key revocation."""
        from sqlmodel import Session, select

        from ..models.tenant import APIKey

        engine = self._get_engine()

        with Session(engine) as session:
            statement = select(APIKey).where(APIKey.id == key_id)
            api_key = session.exec(statement).first()

            if api_key is None:
                return False

            api_key.status = "revoked"
            api_key.revoked_at = datetime.utcnow()
            api_key.revoked_reason = reason[:255] if reason else None

            session.add(api_key)
            session.commit()

            logger.info(f"API key revoked: {api_key.key_prefix}... reason={reason}")
            return True

    async def get_key_info(self, key_id: str) -> Optional[dict]:
        """
        Get information about a specific key by ID.

        Used for admin/audit purposes.
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_get_key_info, key_id)

    def _sync_get_key_info(self, key_id: str) -> Optional[dict]:
        """Synchronous key info lookup."""
        from sqlmodel import Session, select

        from ..models.tenant import APIKey

        engine = self._get_engine()

        with Session(engine) as session:
            statement = select(APIKey).where(APIKey.id == key_id)
            api_key = session.exec(statement).first()

            if api_key is None:
                return None

            return {
                "key_id": api_key.id,
                "key_name": api_key.name,
                "key_prefix": api_key.key_prefix,
                "tenant_id": api_key.tenant_id,
                "user_id": api_key.user_id,
                "status": api_key.status,
                "scopes": self._parse_scopes(api_key.permissions_json),
                "rate_limit": api_key.rate_limit_rpm,
                "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
                "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                "total_requests": api_key.total_requests,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "revoked_at": api_key.revoked_at.isoformat() if api_key.revoked_at else None,
            }


# Singleton instance
_api_key_service: Optional[ApiKeyService] = None


def get_api_key_service() -> ApiKeyService:
    """Get or create the API key service singleton."""
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = ApiKeyService()
    return _api_key_service
