# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Redis-backed session revocation store
# Callers: AuthGateway
# Allowed Imports: (none - leaf module)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-306 (Capability Registry), CAP-006 (Authentication)
# capability_id: CAP-006

"""
Session Revocation Store

Redis-backed store for tracking revoked sessions.
When a user logs out or their session is invalidated,
the session ID is added to this store.

The gateway checks this store on every human request
to ensure revoked sessions cannot be used.

INVARIANTS:
1. Session revocation is immediate (no caching delay)
2. Missing Redis = sessions NOT revoked (fail-open for availability)
3. Session IDs expire from Redis after TTL (default: 7 days)
4. This is advisory only - Redis loss doesn't break auth
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger("nova.auth.session_store")

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_REVOCATION_TTL = int(os.getenv("SESSION_REVOCATION_TTL", str(7 * 24 * 3600)))  # 7 days
SESSION_REVOCATION_PREFIX = "session:revoked:"


class SessionStore:
    """
    Redis-backed session revocation store.

    Tracks revoked sessions to prevent replay of stolen tokens.

    Usage:
        store = SessionStore()
        await store.revoke(session_id)

        # In gateway:
        if await store.is_revoked(session_id):
            return error_session_revoked()
    """

    def __init__(self, redis_url: str = REDIS_URL):
        """
        Initialize session store.

        Args:
            redis_url: Redis connection URL
        """
        self._redis_url = redis_url
        self._redis: Optional["Redis"] = None

    async def _get_redis(self) -> Optional["Redis"]:
        """Get or create Redis connection."""
        if self._redis is not None:
            return self._redis

        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._redis.ping()
            return self._redis
        except ImportError:
            logger.warning("redis package not installed, session revocation disabled")
            return None
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, session revocation disabled")
            return None

    async def is_revoked(self, session_id: str) -> bool:
        """
        Check if a session has been revoked.

        Args:
            session_id: The session ID to check

        Returns:
            True if session is revoked, False otherwise.
            Returns False if Redis is unavailable (fail-open).
        """
        if not session_id:
            return False

        redis = await self._get_redis()
        if redis is None:
            # Fail-open: if Redis is unavailable, assume not revoked
            return False

        try:
            key = f"{SESSION_REVOCATION_PREFIX}{session_id}"
            result = await redis.exists(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Redis check failed: {e}, assuming not revoked")
            return False

    async def revoke(
        self,
        session_id: str,
        ttl: int = SESSION_REVOCATION_TTL,
    ) -> bool:
        """
        Revoke a session.

        Args:
            session_id: The session ID to revoke
            ttl: Time-to-live in seconds (default: 7 days)

        Returns:
            True if revocation was recorded, False if Redis unavailable.
        """
        if not session_id:
            return False

        redis = await self._get_redis()
        if redis is None:
            logger.error("Cannot revoke session: Redis unavailable")
            return False

        try:
            key = f"{SESSION_REVOCATION_PREFIX}{session_id}"
            await redis.setex(key, ttl, "1")
            logger.info(f"Session revoked: {session_id[:8]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke session: {e}")
            return False

    async def unrevoke(self, session_id: str) -> bool:
        """
        Remove session from revocation list.

        Use with caution - typically only for admin operations.

        Args:
            session_id: The session ID to unrevoke

        Returns:
            True if removed, False if Redis unavailable or key not found.
        """
        if not session_id:
            return False

        redis = await self._get_redis()
        if redis is None:
            return False

        try:
            key = f"{SESSION_REVOCATION_PREFIX}{session_id}"
            result = await redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to unrevoke session: {e}")
            return False

    async def revoke_all_for_user(
        self,
        user_id: str,
        session_ids: list[str],
    ) -> int:
        """
        Revoke all sessions for a user.

        Used when a user's account is compromised or
        when they request "log out everywhere".

        Args:
            user_id: The user ID (for logging)
            session_ids: List of session IDs to revoke

        Returns:
            Number of sessions successfully revoked.
        """
        revoked_count = 0
        for session_id in session_ids:
            if await self.revoke(session_id):
                revoked_count += 1

        logger.info(f"Revoked {revoked_count}/{len(session_ids)} sessions for user {user_id}")
        return revoked_count

    async def close(self):
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


# Singleton instance
_session_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """Get or create the session store singleton."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
