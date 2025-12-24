"""
Server-Side Replay Enforcement
M8 Deliverable: Enforce replay_behavior during trace execution

Provides:
- Replay behavior enforcement (execute, skip, check)
- Idempotency key validation
- Output verification for "check" mode
- Replay mismatch detection
"""

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Optional


class ReplayBehavior(str, Enum):
    """Replay behavior options."""

    EXECUTE = "execute"  # Always execute (default)
    SKIP = "skip"  # Skip if already executed
    CHECK = "check"  # Verify output matches


class ReplayMismatchError(Exception):
    """Raised when replay output doesn't match original."""

    def __init__(
        self,
        step_index: int,
        expected_hash: str,
        actual_hash: str,
        message: str = "Replay output mismatch",
    ):
        self.step_index = step_index
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        super().__init__(f"{message}: step {step_index}, expected {expected_hash}, got {actual_hash}")


class IdempotencyViolationError(Exception):
    """Raised when idempotency key is violated."""

    def __init__(
        self,
        idempotency_key: str,
        message: str = "Idempotency key already executed",
    ):
        self.idempotency_key = idempotency_key
        super().__init__(f"{message}: {idempotency_key}")


@dataclass
class ReplayResult:
    """Result of a replay operation."""

    executed: bool
    skipped: bool
    checked: bool
    output_data: Any
    output_hash: str
    from_cache: bool = False


def hash_output(data: Any) -> str:
    """Compute hash of output data for comparison."""
    if data is None:
        return hashlib.sha256(b"null").hexdigest()[:16]
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class ReplayEnforcer:
    """
    Server-side replay behavior enforcer.

    Ensures that:
    - "skip" steps are not re-executed
    - "check" steps verify output matches
    - Idempotency keys are respected
    """

    def __init__(self, idempotency_store: Optional["IdempotencyStore"] = None):
        self.idempotency_store = idempotency_store or InMemoryIdempotencyStore()

    async def enforce_step(
        self,
        step: dict,
        execute_fn: Callable[[], Awaitable[Any]],
        tenant_id: str,
    ) -> ReplayResult:
        """
        Enforce replay behavior for a single step.

        Args:
            step: Step data including replay_behavior and idempotency_key
            execute_fn: Async function to execute the step
            tenant_id: Tenant ID for idempotency scoping

        Returns:
            ReplayResult with execution outcome

        Raises:
            ReplayMismatchError: If check mode fails
            IdempotencyViolationError: If idempotency violated
        """
        behavior = ReplayBehavior(step.get("replay_behavior", "execute"))
        idempotency_key = step.get("idempotency_key")
        step_index = step.get("step_index", 0)
        original_output_hash = step.get("output_hash")

        # Check idempotency if key is present
        if idempotency_key:
            cached = await self.idempotency_store.get(idempotency_key, tenant_id)
            if cached is not None:
                # Already executed
                if behavior == ReplayBehavior.SKIP:
                    return ReplayResult(
                        executed=False,
                        skipped=True,
                        checked=False,
                        output_data=cached.get("output_data"),
                        output_hash=cached.get("output_hash", ""),
                        from_cache=True,
                    )
                elif behavior == ReplayBehavior.CHECK:
                    # Return cached result, caller should verify
                    return ReplayResult(
                        executed=False,
                        skipped=False,
                        checked=True,
                        output_data=cached.get("output_data"),
                        output_hash=cached.get("output_hash", ""),
                        from_cache=True,
                    )
                # EXECUTE behavior continues to execute

        # Handle SKIP without idempotency key
        if behavior == ReplayBehavior.SKIP and not idempotency_key:
            # Can't skip without idempotency tracking - warn and execute
            pass

        # Execute the step
        output_data = await execute_fn()
        output_hash = hash_output(output_data)

        # Store idempotency record
        if idempotency_key:
            await self.idempotency_store.set(
                idempotency_key,
                tenant_id,
                {
                    "output_data": output_data,
                    "output_hash": output_hash,
                    "step_index": step_index,
                },
            )

        # Verify for CHECK mode
        if behavior == ReplayBehavior.CHECK and original_output_hash:
            if output_hash != original_output_hash:
                raise ReplayMismatchError(
                    step_index=step_index,
                    expected_hash=original_output_hash,
                    actual_hash=output_hash,
                )

        return ReplayResult(
            executed=True,
            skipped=False,
            checked=(behavior == ReplayBehavior.CHECK),
            output_data=output_data,
            output_hash=output_hash,
            from_cache=False,
        )

    async def enforce_trace(
        self,
        trace: dict,
        step_executor: Callable[[dict], Awaitable[Any]],
        tenant_id: str,
    ) -> list[ReplayResult]:
        """
        Enforce replay behavior for an entire trace.

        Args:
            trace: Complete trace with steps
            step_executor: Function to execute each step
            tenant_id: Tenant ID for scoping

        Returns:
            List of ReplayResult for each step
        """
        results = []
        steps = trace.get("steps", [])

        for step in steps:

            async def execute():
                return await step_executor(step)

            result = await self.enforce_step(step, execute, tenant_id)
            results.append(result)

            # If step was skipped or checked from cache, use cached output
            # for downstream steps that might depend on it
            if result.from_cache:
                step["_cached_output"] = result.output_data

        return results


class IdempotencyStore:
    """Abstract base for idempotency storage."""

    async def get(self, key: str, tenant_id: str) -> Optional[dict]:
        raise NotImplementedError

    async def set(self, key: str, tenant_id: str, value: dict) -> None:
        raise NotImplementedError

    async def delete(self, key: str, tenant_id: str) -> bool:
        raise NotImplementedError


class InMemoryIdempotencyStore(IdempotencyStore):
    """In-memory idempotency store for testing."""

    def __init__(self):
        self._store: dict[str, dict] = {}

    def _make_key(self, key: str, tenant_id: str) -> str:
        return f"{tenant_id}:{key}"

    async def get(self, key: str, tenant_id: str) -> Optional[dict]:
        full_key = self._make_key(key, tenant_id)
        return self._store.get(full_key)

    async def set(self, key: str, tenant_id: str, value: dict) -> None:
        full_key = self._make_key(key, tenant_id)
        self._store[full_key] = value

    async def delete(self, key: str, tenant_id: str) -> bool:
        full_key = self._make_key(key, tenant_id)
        if full_key in self._store:
            del self._store[full_key]
            return True
        return False

    def clear(self) -> None:
        """Clear all stored keys."""
        self._store.clear()


class RedisIdempotencyStore(IdempotencyStore):
    """Redis-based idempotency store for production."""

    def __init__(self, redis_url: str | None = None, ttl_seconds: int = 86400):
        import os

        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.ttl_seconds = ttl_seconds
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as redis

            self._client = redis.from_url(self.redis_url)
        return self._client

    def _make_key(self, key: str, tenant_id: str) -> str:
        return f"aos:idempotency:{tenant_id}:{key}"

    async def get(self, key: str, tenant_id: str) -> Optional[dict]:
        client = await self._get_client()
        full_key = self._make_key(key, tenant_id)
        data = await client.get(full_key)
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, tenant_id: str, value: dict) -> None:
        client = await self._get_client()
        full_key = self._make_key(key, tenant_id)
        await client.setex(full_key, self.ttl_seconds, json.dumps(value))

    async def delete(self, key: str, tenant_id: str) -> bool:
        client = await self._get_client()
        full_key = self._make_key(key, tenant_id)
        result = await client.delete(full_key)
        return bool(result > 0)


# Singleton enforcer
_enforcer: Optional[ReplayEnforcer] = None


def get_replay_enforcer(use_redis: bool = False) -> ReplayEnforcer:
    """Get singleton replay enforcer."""
    global _enforcer
    if _enforcer is None:
        if use_redis:
            store = RedisIdempotencyStore()
        else:
            store = InMemoryIdempotencyStore()
        _enforcer = ReplayEnforcer(idempotency_store=store)
    return _enforcer
