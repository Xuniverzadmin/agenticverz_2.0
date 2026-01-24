# Layer: L4 — Domain Engine
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: API key validation engine for machine authentication
# Callers: AuthGateway
# Allowed Imports: L6 drivers (via injection)
# Forbidden Imports: sqlalchemy, sqlmodel, app.models
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md, PIN-306, CAP-006

"""API Key Validation Engine

L4 engine for API key validation decisions.

Decides: Key validity, scope parsing, rate limit defaults
Delegates: All data access to ApiKeyDriver

INVARIANTS:
1. Keys are validated by hash comparison (never plaintext storage)
2. Revoked/expired keys are rejected immediately
3. Key usage is recorded for audit trail
4. Scopes are extracted from key permissions
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import TYPE_CHECKING, Optional

from app.auth.api_key_driver import ApiKeyDriver, get_api_key_driver

if TYPE_CHECKING:
    pass

logger = logging.getLogger("nova.auth.api_key_engine")


class ApiKeyEngine:
    """L4 engine for API key validation decisions.

    Decides: Key validity, scope parsing, rate limit defaults
    Delegates: All data access to ApiKeyDriver

    Usage:
        engine = ApiKeyEngine()
        key_info = await engine.validate_key("aos_xxxxx")

        if key_info:
            # key_info contains: key_id, tenant_id, scopes, rate_limit
            pass
    """

    # Default rate limit if not specified per-key
    DEFAULT_RATE_LIMIT_RPM = 1000

    # Default scope if no permissions specified
    DEFAULT_SCOPE = ["*"]

    def __init__(self, driver: Optional[ApiKeyDriver] = None):
        """Initialize engine with driver.

        Args:
            driver: ApiKeyDriver instance (lazy-created if not provided)
        """
        self._driver = driver

    def _get_driver(self) -> ApiKeyDriver:
        """Get or create driver."""
        if self._driver is None:
            self._driver = get_api_key_driver()
        return self._driver

    # =========================================================================
    # KEY VALIDATION
    # =========================================================================

    async def validate_key(self, api_key: str) -> Optional[dict]:
        """Validate an API key and return its metadata.

        DECISION LOGIC:
        1. Hash the key for lookup
        2. Fetch key data from driver
        3. Check validity (revoked, expired)
        4. Parse scopes from permissions
        5. Apply rate limit defaults
        6. Record usage

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
            # Run sync driver operation in thread pool
            loop = asyncio.get_event_loop()
            key_row = await loop.run_in_executor(
                None, self._get_driver().fetch_key_by_hash, key_hash
            )

            if key_row is None:
                return None

            # DECISION: Check validity
            if not key_row.is_valid:
                return {
                    "key_id": key_row.id,
                    "key_name": key_row.name,
                    "tenant_id": key_row.tenant_id,
                    "scopes": [],
                    "rate_limit": 0,
                    "revoked": True,
                }

            # DECISION: Parse scopes
            scopes = self._parse_scopes(key_row.permissions_json)

            # DECISION: Apply rate limit defaults
            rate_limit = key_row.rate_limit_rpm or self.DEFAULT_RATE_LIMIT_RPM

            # Record usage
            await loop.run_in_executor(
                None, self._get_driver().record_usage, key_hash
            )

            return {
                "key_id": key_row.id,
                "key_name": key_row.name,
                "tenant_id": key_row.tenant_id,
                "scopes": scopes,
                "rate_limit": rate_limit,
                "revoked": False,
            }

        except Exception as e:
            logger.error(f"API key lookup failed: {e}")
            return None

    def _parse_scopes(self, permissions_json: Optional[str]) -> list[str]:
        """Parse scopes from permissions JSON.

        DECISION LOGIC:
        - Permissions stored as JSON array: ["run:*", "read:*"]
        - If None or invalid, return default full access scope

        Args:
            permissions_json: JSON string of permissions

        Returns:
            List of scope strings
        """
        if not permissions_json:
            return self.DEFAULT_SCOPE

        try:
            scopes = json.loads(permissions_json)
            if isinstance(scopes, list):
                return scopes
            return self.DEFAULT_SCOPE
        except json.JSONDecodeError:
            return self.DEFAULT_SCOPE

    # =========================================================================
    # KEY REVOCATION
    # =========================================================================

    async def revoke_key(self, key_id: str, reason: str = "") -> bool:
        """Revoke an API key.

        Args:
            key_id: The key ID to revoke
            reason: Reason for revocation (for audit)

        Returns:
            True if key was revoked, False if not found.
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._get_driver().revoke_key, key_id, reason
        )

        if result:
            logger.info(f"API key revoked: {key_id} reason={reason}")

        return result

    # =========================================================================
    # KEY INFO
    # =========================================================================

    async def get_key_info(self, key_id: str) -> Optional[dict]:
        """Get information about a specific key by ID.

        Used for admin/audit purposes.

        Args:
            key_id: The key ID

        Returns:
            Key info dict or None if not found
        """
        loop = asyncio.get_event_loop()
        key_row = await loop.run_in_executor(
            None, self._get_driver().fetch_key_by_id, key_id
        )

        if key_row is None:
            return None

        return {
            "key_id": key_row.id,
            "key_name": key_row.name,
            "key_prefix": key_row.key_prefix,
            "tenant_id": key_row.tenant_id,
            "user_id": key_row.user_id,
            "status": key_row.status,
            "scopes": self._parse_scopes(key_row.permissions_json),
            "rate_limit": key_row.rate_limit_rpm,
            "created_at": key_row.created_at.isoformat() if key_row.created_at else None,
            "last_used_at": key_row.last_used_at.isoformat() if key_row.last_used_at else None,
            "total_requests": key_row.total_requests,
            "expires_at": key_row.expires_at.isoformat() if key_row.expires_at else None,
            "revoked_at": key_row.revoked_at.isoformat() if key_row.revoked_at else None,
        }


# Singleton instance
_api_key_engine: Optional[ApiKeyEngine] = None


def get_api_key_engine() -> ApiKeyEngine:
    """Get or create the API key engine singleton."""
    global _api_key_engine
    if _api_key_engine is None:
        _api_key_engine = ApiKeyEngine()
    return _api_key_engine


# Backward compatibility aliases
ApiKeyService = ApiKeyEngine
get_api_key_service = get_api_key_engine
