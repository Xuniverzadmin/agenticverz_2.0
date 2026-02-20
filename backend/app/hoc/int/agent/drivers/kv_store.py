# Layer: L6 — Driver
# KV Store Skill (M11)
# Redis-backed key-value operations with idempotency support
# capability_id: CAP-016

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

import redis.asyncio as redis
from pydantic import BaseModel

from app.schemas.skill import KVStoreInput, KVStoreOutput
from .registry import skill

logger = logging.getLogger("nova.skills.kv_store")

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
KEY_PREFIX = "aos"
DEFAULT_TTL = 3600  # 1 hour
IDEMPOTENCY_TTL = 86400  # 24 hours


class KVStoreConfig(BaseModel):
    """Configuration schema for kv_store skill."""

    allow_external: bool = True
    redis_url: Optional[str] = None
    key_prefix: str = KEY_PREFIX
    default_ttl: int = DEFAULT_TTL


@skill(
    "kv_store",
    input_schema=KVStoreInput,
    output_schema=KVStoreOutput,
    tags=["storage", "redis", "kv"],
    default_config={"allow_external": True, "key_prefix": KEY_PREFIX, "default_ttl": DEFAULT_TTL},
)
class KVStoreSkill:
    """Redis KV Store skill with idempotency support.

    Features:
    - GET, SET, DELETE, EXISTS, TTL, INCR, DECR, EXPIRE operations
    - Namespace isolation for multi-tenant safety
    - Idempotency support for SET/DELETE operations
    - Configurable TTL with defaults
    - External call control (can stub for testing)

    Environment Variables:
    - REDIS_URL: Redis connection URL (supports TLS via rediss://)

    Usage in workflow:
        {
            "skill": "kv_store",
            "params": {
                "operation": "set",
                "namespace": "workflow_123",
                "key": "status",
                "value": {"state": "running"},
                "ttl_seconds": 3600
            }
        }
    """

    VERSION = "1.0.0"
    DESCRIPTION = "Redis key-value store with namespace isolation and idempotency"

    def __init__(
        self,
        *,
        allow_external: bool = True,
        redis_url: Optional[str] = None,
        key_prefix: str = KEY_PREFIX,
        default_ttl: int = DEFAULT_TTL,
    ):
        self.allow_external = allow_external
        self.redis_url = redis_url or REDIS_URL
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
        return self._client

    def _make_key(self, namespace: str, key: str) -> str:
        """Build full key with prefix and namespace."""
        return f"{self.key_prefix}:{namespace}:{key}"

    def _make_idempotency_key(self, idempotency_key: str) -> str:
        """Build idempotency key."""
        return f"{self.key_prefix}:idem:{idempotency_key}"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute KV operation.

        Args:
            params: Dict with operation, key, value, ttl_seconds, namespace, idempotency_key

        Returns:
            Structured result with operation outcome
        """
        operation = params.get("operation", "get")
        key = params.get("key", "")
        value = params.get("value")
        ttl_seconds = params.get("ttl_seconds")
        namespace = params.get("namespace", "default")
        idempotency_key = params.get("idempotency_key")

        started_at = datetime.now(timezone.utc)
        start_time = time.time()
        full_key = self._make_key(namespace, key)

        logger.info("kv_store_execution_start", extra={"skill": "kv_store", "operation": operation, "key": full_key})

        # Check stub mode
        if not self.allow_external:
            duration = time.time() - start_time
            return self._stubbed_response(operation, key, started_at, duration)

        # Check idempotency for mutating operations
        if idempotency_key and operation in ("set", "delete"):
            cached = await self._check_idempotency(idempotency_key)
            if cached:
                logger.info("kv_store_idempotency_hit", extra={"idempotency_key": idempotency_key})
                return {**cached, "from_cache": True}

        try:
            client = await self._get_client()
            result = await self._execute_operation(client, operation, full_key, key, value, ttl_seconds, namespace)

            duration = time.time() - start_time
            completed_at = datetime.now(timezone.utc)

            response = {
                "skill": "kv_store",
                "skill_version": self.VERSION,
                "status": "ok",
                "duration_seconds": round(duration, 3),
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "operation": operation,
                "key": key,
                **result,
            }

            # Store idempotency result for mutating operations
            if idempotency_key and operation in ("set", "delete"):
                await self._store_idempotency(idempotency_key, response)

            logger.info(
                "kv_store_execution_end",
                extra={"skill": "kv_store", "operation": operation, "key": full_key, "duration": duration},
            )

            return response

        except redis.RedisError as e:
            duration = time.time() - start_time
            logger.error("kv_store_redis_error", extra={"error": str(e), "key": full_key})
            return {
                "skill": "kv_store",
                "skill_version": self.VERSION,
                "status": "error",
                "error": f"Redis error: {str(e)[:200]}",
                "duration_seconds": round(duration, 3),
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "operation": operation,
                "key": key,
            }

    async def _execute_operation(
        self,
        client: redis.Redis,
        operation: str,
        full_key: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int],
        namespace: str,
    ) -> Dict[str, Any]:
        """Execute the specific KV operation."""

        if operation == "get":
            raw = await client.get(full_key)
            if raw is None:
                return {"value": None, "exists": False}
            try:
                return {"value": json.loads(raw), "exists": True}
            except json.JSONDecodeError:
                return {"value": raw, "exists": True}

        elif operation == "set":
            serialized = json.dumps(value) if not isinstance(value, str) else value
            ttl = ttl_seconds or self.default_ttl
            await client.set(full_key, serialized, ex=ttl)
            return {"value": value, "ttl_remaining": ttl}

        elif operation == "delete":
            deleted = await client.delete(full_key)
            return {"value": None, "exists": deleted > 0}

        elif operation == "exists":
            exists = await client.exists(full_key)
            return {"exists": exists > 0}

        elif operation == "ttl":
            ttl = await client.ttl(full_key)
            return {"ttl_remaining": ttl if ttl >= 0 else None, "exists": ttl != -2}

        elif operation == "incr":
            new_value = await client.incr(full_key)
            if ttl_seconds:
                await client.expire(full_key, ttl_seconds)
            return {"value": new_value}

        elif operation == "decr":
            new_value = await client.decr(full_key)
            if ttl_seconds:
                await client.expire(full_key, ttl_seconds)
            return {"value": new_value}

        elif operation == "expire":
            ttl = ttl_seconds or self.default_ttl
            result = await client.expire(full_key, ttl)
            return {"ttl_remaining": ttl if result else None, "exists": bool(result)}

        else:
            return {"error": f"Unknown operation: {operation}"}

    async def _check_idempotency(self, idempotency_key: str) -> Optional[Dict]:
        """Check if operation was already executed."""
        try:
            client = await self._get_client()
            idem_key = self._make_idempotency_key(idempotency_key)
            cached = await client.get(idem_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Idempotency check failed: {e}")
        return None

    async def _store_idempotency(self, idempotency_key: str, result: Dict):
        """Store operation result for idempotency."""
        try:
            client = await self._get_client()
            idem_key = self._make_idempotency_key(idempotency_key)
            await client.set(idem_key, json.dumps(result), ex=IDEMPOTENCY_TTL)
        except Exception as e:
            logger.warning(f"Idempotency store failed: {e}")

    def _stubbed_response(self, operation: str, key: str, started_at: datetime, duration: float) -> Dict:
        """Return stubbed response when external calls disabled."""
        return {
            "skill": "kv_store",
            "skill_version": self.VERSION,
            "status": "stubbed",
            "duration_seconds": round(duration, 3),
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "key": key,
            "value": {"stubbed": True},
            "error": None,
        }

    @classmethod
    def get_input_schema(cls) -> Type[BaseModel]:
        return KVStoreInput

    @classmethod
    def get_output_schema(cls) -> Type[BaseModel]:
        return KVStoreOutput
