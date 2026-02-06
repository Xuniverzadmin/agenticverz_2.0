# Layer: L6 — Domain Driver
# NOTE: Renamed idempotency.py → idempotency_driver.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api/worker (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Redis (idempotency keys)
#   Writes: Redis (idempotency keys, delete)
# Database:
#   Scope: domain (logs)
#   Models: none (Redis-backed)
# Role: Trace idempotency enforcement (Redis + Lua scripts)
# Authority: Idempotency state mutation (NEW/DUPLICATE/CONFLICT)
# Callers: trace store, workers
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470, EXECUTION_SEMANTIC_CONTRACT.md (Guarantee 2: Idempotent Trace Emission)

"""
Redis Idempotency Store for AOS Traces

M8 Deliverable: Atomic idempotency enforcement using Redis + Lua scripts.

Features:
- Atomic check-and-set with Lua scripts
- Configurable TTL per key
- Conflict detection with hash comparison
- Async Redis support
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class IdempotencyResult(Enum):
    """Result of idempotency check."""

    NEW = "new"  # First time, lock acquired
    DUPLICATE = "duplicate"  # Same hash, safe to replay
    CONFLICT = "conflict"  # Different hash, conflict


@dataclass
class IdempotencyResponse:
    """Response from idempotency check."""

    result: IdempotencyResult
    stored_hash: str
    stored_trace_id: str

    @property
    def is_new(self) -> bool:
        return self.result == IdempotencyResult.NEW

    @property
    def is_duplicate(self) -> bool:
        return self.result == IdempotencyResult.DUPLICATE

    @property
    def is_conflict(self) -> bool:
        return self.result == IdempotencyResult.CONFLICT


# Load Lua script
_LUA_SCRIPT_PATH = Path(__file__).parent / "idempotency.lua"
_LUA_SCRIPT: Optional[str] = None


def _load_lua_script() -> str:
    """Load Lua script from file."""
    global _LUA_SCRIPT
    if _LUA_SCRIPT is None:
        if _LUA_SCRIPT_PATH.exists():
            _LUA_SCRIPT = _LUA_SCRIPT_PATH.read_text()
        else:
            # Inline fallback
            # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant.
            # Lua script requires tenant_id to be passed in; empty string preserved for backwards compat
            # but should never be used for production queries.
            _LUA_SCRIPT = """
local key = KEYS[1]
local request_hash = ARGV[1]
local ttl = tonumber(ARGV[2]) or 86400
local tenant_id = ARGV[3] or ""
local trace_id = ARGV[4] or ""

local existing = redis.call("HGETALL", key)

if #existing == 0 then
    redis.call("HSET", key,
        "hash", request_hash,
        "tenant_id", tenant_id,
        "trace_id", trace_id,
        "created_at", redis.call("TIME")[1],
        "status", "pending"
    )
    redis.call("EXPIRE", key, ttl)
    return {"new", request_hash, ""}
end

local stored_hash = ""
local stored_trace_id = ""
for i = 1, #existing, 2 do
    if existing[i] == "hash" then
        stored_hash = existing[i + 1]
    elseif existing[i] == "trace_id" then
        stored_trace_id = existing[i + 1]
    end
end

if stored_hash == request_hash then
    return {"duplicate", stored_hash, stored_trace_id}
else
    return {"conflict", stored_hash, stored_trace_id}
end
"""
    return _LUA_SCRIPT


def canonical_json(obj: Any) -> str:
    """Produce canonical JSON (sorted keys, compact format)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def hash_request(data: Dict[str, Any]) -> str:
    """Hash request data for idempotency comparison."""
    canonical = canonical_json(data)
    return hashlib.sha256(canonical.encode()).hexdigest()


class RedisIdempotencyStore:
    """
    Redis-backed idempotency store with Lua script for atomicity.

    Usage:
        store = RedisIdempotencyStore(redis_client)
        response = await store.check("my-key", request_data, tenant_id="acme")

        if response.is_new:
            # Process request
            await store.mark_completed("my-key", trace_id)
        elif response.is_duplicate:
            # Return cached response
            pass
        elif response.is_conflict:
            # Reject with 409 Conflict
            raise HTTPException(409, "Idempotency conflict")
    """

    def __init__(
        self,
        redis_client: Any,
        key_prefix: str = "idem",
        default_ttl: int = 86400,  # 24 hours
    ):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self._script_sha: Optional[str] = None

    def _make_key(self, idempotency_key: str, tenant_id: str = "default") -> str:
        """Construct Redis key."""
        return f"{self.key_prefix}:{tenant_id}:{idempotency_key}"

    async def _ensure_script_loaded(self) -> str:
        """Ensure Lua script is loaded in Redis."""
        if self._script_sha is None:
            script = _load_lua_script()
            self._script_sha = await self.redis.script_load(script)
        return self._script_sha

    async def check(
        self,
        idempotency_key: str,
        request_data: Dict[str, Any],
        tenant_id: str = "default",
        trace_id: str = "",
        ttl: Optional[int] = None,
    ) -> IdempotencyResponse:
        """
        Check idempotency key atomically.

        Args:
            idempotency_key: Client-provided idempotency key
            request_data: Request data to hash
            tenant_id: Tenant for isolation
            trace_id: Associated trace ID
            ttl: TTL in seconds (default: 24h)

        Returns:
            IdempotencyResponse with result type
        """
        key = self._make_key(idempotency_key, tenant_id)
        request_hash = hash_request(request_data)
        ttl = ttl or self.default_ttl

        try:
            script_sha = await self._ensure_script_loaded()
            result = await self.redis.evalsha(
                script_sha,
                1,  # Number of keys
                key,
                request_hash,
                str(ttl),
                tenant_id,
                trace_id,
            )

            result_type = IdempotencyResult(result[0].decode() if isinstance(result[0], bytes) else result[0])
            stored_hash = result[1].decode() if isinstance(result[1], bytes) else result[1]
            stored_trace_id = result[2].decode() if isinstance(result[2], bytes) else result[2]

            return IdempotencyResponse(result=result_type, stored_hash=stored_hash, stored_trace_id=stored_trace_id)

        except Exception as e:
            logger.error(f"Redis idempotency check failed: {e}")
            # Fallback: allow through (fail open for availability)
            return IdempotencyResponse(result=IdempotencyResult.NEW, stored_hash=request_hash, stored_trace_id="")

    async def mark_completed(
        self,
        idempotency_key: str,
        trace_id: str,
        tenant_id: str = "default",
        response_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark idempotency key as completed with trace result."""
        key = self._make_key(idempotency_key, tenant_id)

        try:
            await self.redis.hset(
                key,
                mapping={
                    "status": "completed",
                    "trace_id": trace_id,
                    "response_hash": hash_request(response_data) if response_data else "",
                },
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mark idempotency key completed: {e}")
            return False

    async def mark_failed(self, idempotency_key: str, tenant_id: str = "default", error: str = "") -> bool:
        """Mark idempotency key as failed (allows retry)."""
        key = self._make_key(idempotency_key, tenant_id)

        try:
            await self.redis.hset(
                key,
                mapping={
                    "status": "failed",
                    "error": error[:500],  # Truncate error
                },
            )
            # Reduce TTL to allow faster retry
            await self.redis.expire(key, 300)  # 5 minutes
            return True
        except Exception as e:
            logger.error(f"Failed to mark idempotency key failed: {e}")
            return False

    async def delete(self, idempotency_key: str, tenant_id: str = "default") -> bool:
        """Delete idempotency key (admin operation)."""
        key = self._make_key(idempotency_key, tenant_id)
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete idempotency key: {e}")
            return False

    async def get_status(self, idempotency_key: str, tenant_id: str = "default") -> Optional[Dict[str, str]]:
        """Get current status of idempotency key."""
        key = self._make_key(idempotency_key, tenant_id)
        try:
            data = await self.redis.hgetall(key)
            if not data:
                return None
            return {
                k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()
            }
        except Exception as e:
            logger.error(f"Failed to get idempotency status: {e}")
            return None


class InMemoryIdempotencyStore:
    """
    In-memory idempotency store for testing and development.

    Not suitable for production (no persistence, no distributed support).
    """

    def __init__(self, default_ttl: int = 86400):
        self._store: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def _make_key(self, idempotency_key: str, tenant_id: str = "default") -> str:
        return f"{tenant_id}:{idempotency_key}"

    async def check(
        self,
        idempotency_key: str,
        request_data: Dict[str, Any],
        tenant_id: str = "default",
        trace_id: str = "",
        ttl: Optional[int] = None,
    ) -> IdempotencyResponse:
        key = self._make_key(idempotency_key, tenant_id)
        request_hash = hash_request(request_data)

        if key not in self._store:
            self._store[key] = {"hash": request_hash, "tenant_id": tenant_id, "trace_id": trace_id, "status": "pending"}
            return IdempotencyResponse(result=IdempotencyResult.NEW, stored_hash=request_hash, stored_trace_id="")

        stored = self._store[key]
        if stored["hash"] == request_hash:
            return IdempotencyResponse(
                result=IdempotencyResult.DUPLICATE,
                stored_hash=stored["hash"],
                stored_trace_id=stored.get("trace_id", ""),
            )

        return IdempotencyResponse(
            result=IdempotencyResult.CONFLICT, stored_hash=stored["hash"], stored_trace_id=stored.get("trace_id", "")
        )

    async def mark_completed(
        self,
        idempotency_key: str,
        trace_id: str,
        tenant_id: str = "default",
        response_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        key = self._make_key(idempotency_key, tenant_id)
        if key in self._store:
            self._store[key]["status"] = "completed"
            self._store[key]["trace_id"] = trace_id
        return True

    async def mark_failed(self, idempotency_key: str, tenant_id: str = "default", error: str = "") -> bool:
        key = self._make_key(idempotency_key, tenant_id)
        if key in self._store:
            self._store[key]["status"] = "failed"
            self._store[key]["error"] = error
        return True

    async def delete(self, idempotency_key: str, tenant_id: str = "default") -> bool:
        key = self._make_key(idempotency_key, tenant_id)
        self._store.pop(key, None)
        return True

    async def get_status(self, idempotency_key: str, tenant_id: str = "default") -> Optional[Dict[str, str]]:
        key = self._make_key(idempotency_key, tenant_id)
        return self._store.get(key)


# Factory function
_idempotency_store: Optional[Any] = None


async def get_idempotency_store() -> Any:
    """Get or create idempotency store based on environment."""
    global _idempotency_store

    if _idempotency_store is not None:
        return _idempotency_store

    redis_url = os.getenv("REDIS_URL", "")

    if redis_url:
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(redis_url, decode_responses=False)
            await client.ping()
            _idempotency_store = RedisIdempotencyStore(client)
            logger.info(f"Using Redis idempotency store: {redis_url}")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory store: {e}")
            _idempotency_store = InMemoryIdempotencyStore()
    else:
        logger.info("REDIS_URL not set, using in-memory idempotency store")
        _idempotency_store = InMemoryIdempotencyStore()

    return _idempotency_store
